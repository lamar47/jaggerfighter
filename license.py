"""
core/license.py - Système de licence JaggerFighter
Gère les tiers Free / Pro / Team avec validation de clé.
"""

import hashlib
import json
import logging
import os
import platform
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LICENSE_FILE = Path.home() / ".jaggerfighter" / "license.json"
VALIDATION_URL = "https://api.jaggerfighter.io/v1/license/validate"  # Ton API future

# ─── Fonctionnalités par tier ────────────────────────────────────────────────

FEATURES = {
    "free": {
        "modules": ["nmap", "nikto", "gobuster", "hydra", "sqlmap", "harvester"],
        "cve_lookup": True,
        "cve_limit": 5,           # 5 req/30s (limite NVD sans clé)
        "report_html": True,
        "report_pdf": False,
        "report_json": True,
        "shodan": False,
        "burp_pro": False,
        "cloud_scans": False,
        "scheduled_scans": False,
        "multi_user": False,
        "max_targets": 1,
        "history_days": 7,
    },
    "pro": {
        "modules": ["nmap", "nikto", "gobuster", "hydra", "sqlmap", "harvester"],
        "cve_lookup": True,
        "cve_limit": 0,           # Illimité (clé NVD partagée)
        "report_html": True,
        "report_pdf": True,
        "report_json": True,
        "shodan": True,
        "burp_pro": True,
        "cloud_scans": False,
        "scheduled_scans": True,
        "multi_user": False,
        "max_targets": 10,
        "history_days": 90,
    },
    "team": {
        "modules": ["nmap", "nikto", "gobuster", "hydra", "sqlmap", "harvester"],
        "cve_lookup": True,
        "cve_limit": 0,
        "report_html": True,
        "report_pdf": True,
        "report_json": True,
        "shodan": True,
        "burp_pro": True,
        "cloud_scans": True,
        "scheduled_scans": True,
        "multi_user": True,
        "max_targets": 0,         # Illimité
        "history_days": 365,
    },
}

TIER_LABELS = {
    "free":  "Community (Gratuit)",
    "pro":   "Pro (~10$/mois)",
    "team":  "Team (~30$/mois)",
}

TIER_COLORS = {
    "free":  "dim",
    "pro":   "cyan",
    "team":  "gold1",
}


class License:
    """
    Gère la licence de l'utilisateur.

    Stocke localement dans ~/.jaggerfighter/license.json.
    Valide optionnellement en ligne au démarrage (avec cache 24h).
    """

    def __init__(self):
        self._tier = "free"
        self._key: Optional[str] = None
        self._email: Optional[str] = None
        self._expires: Optional[datetime] = None
        self._last_validated: Optional[datetime] = None
        self._load()

    # ─── Chargement / sauvegarde ─────────────────────────────────────────────

    def _load(self):
        """Charge la licence depuis le fichier local."""
        if not LICENSE_FILE.exists():
            return
        try:
            data = json.loads(LICENSE_FILE.read_text())
            self._key    = data.get("key")
            self._tier   = data.get("tier", "free")
            self._email  = data.get("email")
            expires_str  = data.get("expires")
            validated_str = data.get("last_validated")

            if expires_str:
                self._expires = datetime.fromisoformat(expires_str)
            if validated_str:
                self._last_validated = datetime.fromisoformat(validated_str)

            # Vérifie l'expiration locale
            if self._expires and datetime.now() > self._expires:
                logger.warning("Licence expirée — retour au tier Free")
                self._tier = "free"
                self._key  = None

        except Exception as e:
            logger.warning("Impossible de charger la licence : %s", e)

    def _save(self):
        """Sauvegarde la licence dans le fichier local."""
        LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key":            self._key,
            "tier":           self._tier,
            "email":          self._email,
            "expires":        self._expires.isoformat() if self._expires else None,
            "last_validated": datetime.now().isoformat(),
        }
        LICENSE_FILE.write_text(json.dumps(data, indent=2))

    # ─── Activation ──────────────────────────────────────────────────────────

    def activate(self, key: str) -> dict:
        """
        Active une clé de licence.
        Tente d'abord une validation en ligne, sinon valide localement.
        Retourne {"success": bool, "message": str, "tier": str}
        """
        key = key.strip().upper()

        if not self._is_valid_key_format(key):
            return {"success": False, "message": "Format de clé invalide. Format attendu : JFPRO-XXXX-XXXX-XXXX"}

        # Tentative de validation en ligne
        result = self._validate_online(key)
        if result["success"]:
            self._key    = key
            self._tier   = result["tier"]
            self._email  = result.get("email", "")
            self._expires = datetime.now() + timedelta(days=result.get("days_valid", 365))
            self._save()
            return {
                "success": True,
                "message": f"Licence {TIER_LABELS[self._tier]} activée !",
                "tier":    self._tier,
                "email":   self._email,
            }

        # Fallback : validation locale (utile hors ligne)
        local_tier = self._validate_locally(key)
        if local_tier:
            self._key    = key
            self._tier   = local_tier
            self._expires = datetime.now() + timedelta(days=365)
            self._save()
            return {
                "success": True,
                "message": f"Licence {TIER_LABELS[local_tier]} activée (mode hors ligne).",
                "tier":    local_tier,
            }

        return {"success": False, "message": "Clé invalide ou expirée. Vérifiez sur jaggerfighter.io"}

    def deactivate(self):
        """Supprime la licence et revient au tier Free."""
        self._tier    = "free"
        self._key     = None
        self._email   = None
        self._expires = None
        if LICENSE_FILE.exists():
            LICENSE_FILE.unlink()

    # ─── Validation ──────────────────────────────────────────────────────────

    def _validate_online(self, key: str) -> dict:
        """Valide la clé auprès de l'API JaggerFighter."""
        try:
            machine_id = self._get_machine_id()
            payload = json.dumps({"key": key, "machine_id": machine_id}).encode()
            req = urllib.request.Request(
                VALIDATION_URL,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "JaggerFighter/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception:
            # Si l'API est inaccessible, on ne bloque pas l'utilisateur
            return {"success": False, "message": "API inaccessible"}

    def _validate_locally(self, key: str) -> Optional[str]:
        """
        Validation locale basique par préfixe de clé.
        En production tu remplacerais ça par une signature cryptographique (HMAC/RSA).
        """
        prefixes = {
            "JFPRO-": "pro",
            "JFTEAM-": "team",
            "JFDEMO-": "pro",   # Clés démo pour tests
        }
        for prefix, tier in prefixes.items():
            if key.startswith(prefix) and len(key) >= 16:
                return tier
        return None

    def _is_valid_key_format(self, key: str) -> bool:
        """Vérifie le format basique : JFXXX-XXXX-XXXX-XXXX"""
        parts = key.split("-")
        return len(parts) >= 3 and parts[0].startswith("JF")

    def _get_machine_id(self) -> str:
        """Identifiant unique de la machine (pour éviter le partage de clé)."""
        raw = f"{platform.node()}{platform.machine()}{os.getuid() if hasattr(os, 'getuid') else 0}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # ─── Interface publique ──────────────────────────────────────────────────

    @property
    def tier(self) -> str:
        return self._tier

    @property
    def is_pro(self) -> bool:
        return self._tier in ("pro", "team")

    @property
    def is_team(self) -> bool:
        return self._tier == "team"

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def key(self) -> Optional[str]:
        return self._key

    @property
    def expires(self) -> Optional[datetime]:
        return self._expires

    def can(self, feature: str) -> bool:
        """Vérifie si la fonctionnalité est disponible pour le tier actuel."""
        tier_features = FEATURES.get(self._tier, FEATURES["free"])
        return bool(tier_features.get(feature, False))

    def get_feature(self, feature: str):
        """Retourne la valeur d'une fonctionnalité pour le tier actuel."""
        tier_features = FEATURES.get(self._tier, FEATURES["free"])
        return tier_features.get(feature)

    def status_dict(self) -> dict:
        """Résumé de la licence pour l'affichage."""
        return {
            "tier":    self._tier,
            "label":   TIER_LABELS.get(self._tier, "Unknown"),
            "email":   self._email or "—",
            "key":     f"{self._key[:12]}..." if self._key else "—",
            "expires": self._expires.strftime("%d/%m/%Y") if self._expires else "—",
            "features": FEATURES.get(self._tier, FEATURES["free"]),
        }


# Instance globale (singleton)
_license_instance: Optional[License] = None

def get_license() -> License:
    """Retourne l'instance globale de la licence."""
    global _license_instance
    if _license_instance is None:
        _license_instance = License()
    return _license_instance

# ╔══════════════════════════════════════════════════╗
#   ██╗      █████╗ ███╗   ███╗ █████╗ ██████╗
#   ██║     ██╔══██╗████╗ ████║██╔══██╗██╔══██╗
#   ██║     ███████║██╔████╔██║███████║██████╔╝
#   ██║     ██╔══██║██║╚██╔╝██║██╔══██║██╔══██╗
#   ███████╗██║  ██║██║ ╚═╝ ██║██║  ██║██║  ██║
#   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
#
#   JaggerFighter Pentest Suite
#   Developed by Lamar — github.com/lamar
#   Unauthorized use is illegal. Use responsibly.
# ╚══════════════════════════════════════════════════╝