 # JaggerFighter — Documentation complète

> **Version** 1.0 | **Plateforme** Kali Linux | **Python** 3.10+

---

## Table des matières

1. [Installation](#installation)
2. [Démarrage rapide](#démarrage-rapide)
3. [Interface menu](#interface-menu)
4. [Commandes CLI](#commandes-cli)
5. [Modules détaillés](#modules-détaillés)
6. [Licence Pro](#licence-pro)
7. [Rapports](#rapports)
8. [Base de données](#base-de-données)
9. [Configuration](#configuration)
10. [Cas d'usage concrets](#cas-dusage-concrets)
11. [FAQ](#faq)

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/VOTRE_USER/jaggerfighter.git
cd jaggerfighter

# 2. Installer (nécessite root pour les outils système)
sudo bash install.sh

# 3. Lancer
jaggerfighter
# ou alias court :
jf
```

### Ce qu'installe install.sh

| Outil | Usage | Obligatoire |
|-------|-------|-------------|
| nmap | Scan de ports et services | Oui |
| nikto | Scanner de vulnérabilités web | Oui |
| gobuster | Énumération de répertoires | Oui |
| hydra | Brute force d'identifiants | Oui |
| sqlmap | Détection d'injections SQL | Oui |
| theharvester | Reconnaissance OSINT | Oui |
| weasyprint | Export PDF des rapports | Non (Pro) |

---

## Démarrage rapide

```bash
# Scan interactif — menu pour choisir les modules
jf -t 192.168.1.1

# Scan rapide (nmap + nikto + gobuster uniquement)
jf -t 192.168.1.1 --quick

# Scan complet d'un domaine
jf -t exemple.com

# Scan d'une application web
jf -t https://monapp.exemple.com
```

---

## Interface menu

Lancez `jaggerfighter` sans argument pour ouvrir le menu interactif :

```
┌─────────────────────────────────────┐
│  Menu principal                     │
│                                     │
│  1  Nouveau scan         Free+      │
│  2  Scan rapide          Free+      │
│  3  Historique           Free+      │
│  4  Générer un rapport   Free+      │
│  ─  ──────────────────────────────  │
│  5  Activer licence Pro  Pro        │
│  6  Statut de la licence Free+      │
│  ─  ──────────────────────────────  │
│  0  Quitter                         │
└─────────────────────────────────────┘
```

### Option 1 — Nouveau scan

1. Renseignez la cible (IP, domaine ou URL)
2. Sélectionnez les modules parmi la liste affichée
3. Confirmez — le scan démarre en temps réel
4. Le rapport est généré automatiquement à la fin

### Option 2 — Scan rapide

Identique à `--quick` : lance nmap + nikto + gobuster sans poser de question.
Idéal pour une première reconnaissance rapide.

### Option 3 — Historique

Affiche toutes les sessions passées avec leur score de risque et le nombre de findings.

### Option 4 — Générer un rapport

Recrée un rapport HTML/PDF/JSON depuis une session existante sans relancer le scan.

---

## Commandes CLI

### Syntaxe générale

```bash
jaggerfighter [OPTIONS]
```

### Options disponibles

| Option | Court | Description | Exemple |
|--------|-------|-------------|---------|
| `--target` | `-t` | Cible du scan | `-t 192.168.1.1` |
| `--quick` | | Scan rapide 3 modules | `--quick` |
| `--activate` | | Activer une clé Pro | `--activate JFPRO-XXXX-XXXX` |
| `--history` | | Lister les sessions | `--history` |
| `--report` | | Rapport d'une session | `--report abc12345` |
| `--status` | | Statut de la licence | `--status` |
| `--no-banner` | | Pas de bannière ASCII | `--no-banner` |

### Exemples complets

```bash
# Scan interactif (menu module)
jf -t 192.168.1.1

# Scan rapide sans interaction
jf -t 192.168.1.1 --quick

# Voir toutes les sessions passées
jf --history

# Régénérer le rapport de la session "abc12345"
jf --report abc12345

# Activer votre clé Pro
jf --activate JFPRO-ABCD-1234-EFGH

# Vérifier le statut de la licence
jf --status

# Scan sans bannière (utile dans un script)
jf -t 10.0.0.1 --quick --no-banner
```

---

## Modules détaillés

### nmap — Scan de ports et services

**Ce qu'il fait :**
- Découverte des ports ouverts (TCP/UDP)
- Identification des services et versions
- Détection du système d'exploitation (avec root)
- Enrichissement CVE automatique via l'API NVD

**Options dans config.yaml :**
```yaml
nmap:
  default_flags: "-sV -sC"     # -sV = versions, -sC = scripts par défaut
  timing: "T3"                  # T1=lent/discret, T3=normal, T5=agressif
  os_detection: false           # true nécessite root
  cve_enrichment: true
  cve_max_results: 3
```

**Findings générés :**
- `Port ouvert 22/tcp — ssh` → Sévérité MEDIUM
- `Port ouvert 23/tcp — telnet` → Sévérité HIGH (service non chiffré)
- `CVE-2021-41773 — Apache 2.4.49 (CVSS 9.8)` → Sévérité CRITICAL

**Exemple de sortie :**
```
nmap          Exécution : nmap -sV -sC -T3 -oX /tmp/nmap_192_168_1_1.xml 192.168.1.1
nmap          22/tcp  open  ssh     OpenSSH 8.4
nmap          80/tcp  open  http    Apache httpd 2.4.49
nmap          443/tcp open  https   nginx 1.18.0
HIGH  Port ouvert 23/tcp — telnet [192.168.1.1:23]
MED   Port ouvert 22/tcp — ssh [192.168.1.1:22]
CRIT  CVE-2021-41773 — Apache httpd 2.4.49 (CVSS 9.8) [192.168.1.1:80]
✓ Terminé en 18.3s — 4 finding(s)
```

---

### theHarvester — Reconnaissance OSINT

**Ce qu'il fait :**
- Collecte d'emails associés au domaine
- Découverte de sous-domaines
- Identification d'IPs publiques
- Sources : Google, Bing, crt.sh, DNSDumpster, URLScan

**Cible valide :** domaines uniquement (`exemple.com`, pas d'IP)

**Options :**
```yaml
harvester:
  sources: "google,bing,crtsh,dnsdumpster,urlscan"
  limit: 200
  dns_resolve: true    # Résout les sous-domaines trouvés
```

**Exemple de sortie :**
```
harvester     Reconnaissance OSINT sur : exemple.com
harvester     Sources : google,bing,crtsh,dnsdumpster,urlscan
MED   Email découvert : admin@exemple.com
LOW   Sous-domaine découvert : dev.exemple.com
LOW   Sous-domaine découvert : api.exemple.com
INFO  IP publique découverte : 185.23.45.67
✓ Terminé en 45.2s — 8 finding(s)
```

---

### nikto — Scanner de vulnérabilités web

**Ce qu'il fait :**
- Détection de configurations dangereuses du serveur web
- Fichiers sensibles exposés (`.env`, `.git`, backups)
- Versions de serveurs obsolètes avec CVE
- En-têtes de sécurité manquants
- Formulaires et pages d'admin par défaut

**Options :**
```yaml
nikto:
  tuning: "1234567890"    # Tous les types de tests
  max_time: "10m"         # Durée max du scan
```

**Tuning (combinaison possible) :**
```
1 = Fichiers/CGI intéressants
2 = Mauvaise configuration
3 = Divulgation d'information
4 = Injection (XSS/Script/HTML)
5 = Remote file retrieval (serveur)
6 = Déni de service
8 = Exécution de commande
9 = Injection SQL
0 = Upload de fichiers
```

**Exemple de sortie :**
```
HIGH  Apache/2.4.49 — Path traversal (CVE-2021-41773) [192.168.1.1]
HIGH  /.git/config accessible — fuite du code source [192.168.1.1]
MED   X-Frame-Options header manquant [192.168.1.1]
MED   /phpinfo.php accessible — divulgation d'information [192.168.1.1]
INFO  Server: Apache/2.4.49 — version exposée [192.168.1.1]
```

---

### gobuster — Énumération de répertoires

**Ce qu'il fait :**
- Découverte de répertoires et fichiers cachés
- Détection de panneaux d'administration
- Fichiers sensibles (`.env`, `.git`, backups, configs)
- Mode DNS pour sous-domaines (en option)

**Cible valide :** URL ou IP (préfixe `http://` ajouté automatiquement)

**Options :**
```yaml
gobuster:
  wordlist: "/usr/share/wordlists/dirb/common.txt"
  wordlist_big: "/usr/share/wordlists/dirb/big.txt"
  extensions: "php,html,txt,js,bak,old,sql,conf"
  threads: 30
```

**Chemins automatiquement classés CRITICAL :**
```
/.env              /.git/config       /wp-config.php
/config.php        /.htpasswd         /id_rsa
/dump.sql          /web.config        /appsettings.json
```

**Exemple de sortie :**
```
CRIT  Chemin découvert : /.env [200] [192.168.1.1]
CRIT  Chemin découvert : /.git/config [200] [192.168.1.1]
HIGH  Chemin découvert : /admin [200] [192.168.1.1]
HIGH  Chemin découvert : /backup.sql [200] [192.168.1.1]
MED   Chemin découvert : /phpmyadmin [403] [192.168.1.1]
```

---

### sqlmap — Injection SQL

**Ce qu'il fait :**
- Détection automatique de tous types d'injections SQL
- Types : boolean-based, time-based, error-based, union-based, stacked
- Énumération des bases de données si injectable
- Mode automatique non-interactif

**Cible valide :** URL avec paramètres (`http://site.com/page?id=1`)

**Options :**
```yaml
sqlmap:
  level: 2      # 1 (basique) → 5 (exhaustif)
  risk: 1       # 1 (sûr) → 3 (peut modifier la DB)
  threads: 4
```

**⚠ Avertissement :** Ne jamais utiliser `risk: 3` sur une cible de production — peut modifier des données.

**Exemple de sortie :**
```
sqlmap        Niveau : 2, Risque : 1
sqlmap        Parameter 'id' is vulnerable
CRIT  Injection SQL — paramètre 'id' [http://site.com/page?id=1]
CRIT  Base de données exposée : users_db
```

---

### hydra — Brute force

**Ce qu'il fait :**
- Attaque par dictionnaire sur SSH, FTP, RDP, MySQL, HTTP...
- Arrêt automatique au premier succès
- Supporte HTTP form (login web)

**Options requises (dans config ou via code) :**
```python
options = {
    "service": "ssh",
    "username": "admin",          # OU
    "userlist": "/path/to/users.txt",
    "password": "password123",    # OU
    "passlist": "/usr/share/wordlists/rockyou.txt",
}
```

**Services supportés :**
`ssh`, `ftp`, `telnet`, `smtp`, `pop3`, `imap`, `rdp`, `smb`, `mysql`, `postgres`, `mssql`, `vnc`, `http-get`, `http-post-form`

**Exemple de sortie :**
```
CRIT  Credential trouvé : admin@192.168.1.1 [ssh]
        Login : admin / Mot de passe : password123
```

---

## Licence Pro

### Tiers disponibles

| Fonctionnalité | Free | Pro (~10$/mois) | Team (~30$/mois) |
|----------------|------|-----------------|------------------|
| Nmap, Nikto, Gobuster, Hydra, SQLMap, theHarvester | ✓ | ✓ | ✓ |
| CVE lookup NVD | ✓ (5 req/30s) | ✓ (illimité) | ✓ (illimité) |
| Rapport HTML | ✓ | ✓ | ✓ |
| Rapport PDF | ✗ | ✓ | ✓ |
| Shodan API | ✗ | ✓ | ✓ |
| Burp Suite Pro (via cloud) | ✗ | ✓ | ✓ |
| Scans planifiés | ✗ | ✓ | ✓ |
| Multi-utilisateurs | ✗ | ✗ | ✓ |
| Cibles simultanées | 1 | 10 | Illimité |
| Historique | 7 jours | 90 jours | 1 an |

### Activer une licence

```bash
# Via CLI
jf --activate JFPRO-ABCD-1234-EFGH-5678

# Ou depuis le menu → option 5
jf
> 5
> Entrez votre clé : JFPRO-ABCD-1234-EFGH-5678
✓ Licence Pro activée !
```

La clé est stockée dans `~/.jaggerfighter/license.json` et validée automatiquement au démarrage.

### Acheter une licence

Rendez-vous sur **https://jaggerfighter.io/pro** — paiement sécurisé via Stripe.

---

## Rapports

### Formats disponibles

| Format | Free | Pro | Contenu |
|--------|------|-----|---------|
| HTML | ✓ | ✓ | Rapport interactif, findings cliquables, score de risque |
| JSON | ✓ | ✓ | Export brut de la session, intégrable dans d'autres outils |
| PDF | ✗ | ✓ | Version imprimable du rapport HTML |

### Structure du rapport HTML

- **En-tête** : cible, date, session ID, nombre de modules
- **Score de risque** : jauge 0-10 avec label (Minimal / Faible / Modéré / Élevé / Critique)
- **Compteurs** : CRITICAL / HIGH / MEDIUM / LOW / INFO
- **Modules** : statut et durée de chaque module
- **Findings** : liste triée par sévérité, cliquables pour voir description + recommandation + evidence

### Localisation des rapports

```
reports/output/
├── report_abc12345_20241215_143022.html
├── report_abc12345_20241215_143022.pdf   (Pro)
└── report_abc12345.json
```

### Générer un rapport depuis une session passée

```bash
# Via CLI
jf --report abc12345

# Via le menu → option 4
jf
> 4
> Session ID : abc12345
> Format : html
✓ Rapport généré
```

---

## Base de données

JaggerFighter stocke toutes les sessions dans `data/jaggerfighter.db` (SQLite).

### Commandes utiles

```bash
# Voir toutes les sessions
jf --history

# Rechercher dans les findings (via Python)
python3 -c "
from db.database import Database
db = Database()
# Trouver tous les findings critiques
findings = db.search_findings(severity='critical')
for f in findings:
    print(f['title'], f['host'])
"
```

### Statistiques globales

```bash
python3 -c "
from db.database import Database
db = Database()
print(db.get_stats())
"
# {'total_sessions': 12, 'total_findings': 347, 'critical': 8, 'high': 45}
```

---

## Configuration

Fichier : `config/config.yaml`

### Paramètres clés

```yaml
# Wordlist plus complète pour Gobuster
gobuster:
  wordlist: "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"
  threads: 50                  # Augmenter si la cible est rapide

# Scan Nmap plus agressif
nmap:
  default_flags: "-sV -sC -A"  # -A = OS + traceroute
  timing: "T4"                 # Plus rapide (peut déclencher IDS)

# Ajouter clé NVD pour CVE illimité (même en Free)
apis:
  nvd_api_key: "VOTRE-CLE-NVD" # Gratuit sur nvd.nist.gov/developers
```

---

## Cas d'usage concrets

### Pentest réseau interne

```bash
# 1. Scan de découverte rapide
jf -t 192.168.1.0/24 --quick

# 2. Scan complet d'une machine identifiée
jf -t 192.168.1.105

# 3. Sélectionner : nmap + nikto + gobuster + hydra
# 4. Rapport généré automatiquement dans reports/output/
```

### Audit d'une application web

```bash
# Scan web complet
jf -t https://monapp.exemple.com

# Sélectionner : nikto + gobuster + sqlmap
# Pour SQLMap, l'URL doit contenir des paramètres :
# Ex : https://monapp.exemple.com/page?id=1
```

### Reconnaissance OSINT d'un domaine

```bash
jf -t exemple.com

# Sélectionner uniquement : harvester
# Collecte emails, sous-domaines, IPs depuis sources publiques
```

### Utilisation programmatique (intégration dans un script)

```python
import asyncio
from core.orchestrator import Orchestrator
from core.nmap_module import NmapModule
from core.nikto_module import NiktoModule
from reports.generator import ReportGenerator

async def audit(target):
    orch = Orchestrator()
    orch.register_module(NmapModule)
    orch.register_module(NiktoModule)

    session = orch.new_session(target, name=f"Audit {target}")
    orch.on_progress(lambda mod, msg: print(f"[{mod}] {msg}"))

    results = await orch.run_all(parallel=False)

    gen = ReportGenerator()
    report = gen.generate_html(session)
    print(f"Rapport : {report}")
    return session

asyncio.run(audit("192.168.1.1"))
```

---

## FAQ

**Q : JaggerFighter fonctionne-t-il hors de Kali ?**
Oui, sur toute distribution Debian/Ubuntu. Les outils (`nmap`, `nikto`...) doivent être installés manuellement si `install.sh` ne les trouve pas.

**Q : Le scan Nmap nécessite-t-il root ?**
Le scan de base (`-sV -sC`) fonctionne sans root. La détection d'OS (`-O`) et certains scans SYN (`-sS`) nécessitent root.

**Q : Le CVE lookup fonctionne-t-il sans connexion internet ?**
Non, il interroge l'API NVD en ligne. Sans internet il est ignoré silencieusement.

**Q : Puis-je scanner n'importe quelle cible ?**
Non. JaggerFighter doit être utilisé uniquement sur des systèmes dont vous êtes propriétaire ou pour lesquels vous avez une autorisation écrite explicite. Scanner sans autorisation est illégal.

**Q : Où sont stockés les rapports ?**
Dans `reports/output/` par défaut. Configurable dans `config/config.yaml`.

**Q : La clé Pro fonctionne-t-elle sur plusieurs machines ?**
Par défaut, une clé Pro est liée à une machine. Contactez le support pour les licences multi-machines (tier Team).

---

> **Avertissement légal** : JaggerFighter est un outil de sécurité offensive réservé aux professionnels autorisés. Toute utilisation sur des systèmes sans autorisation explicite est illégale et punissable par la loi. Les auteurs déclinent toute responsabilité en cas d'usage illicite.



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