#!/bin/bash
# ════════════════════════════════════════════════════════════
#   JaggerFighter — Script d'installation pour Kali Linux
#   Usage : sudo bash install.sh
# ════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${RED}"
echo "     ██╗ █████╗  ██████╗  ██████╗ ███████╗██████╗ "
echo "     ██║██╔══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗"
echo "     ██║███████║██║  ███╗██║  ███╗█████╗  ██████╔╝"
echo "     ██║██╔══██║██║   ██║██║   ██║██╔══╝  ██╔══██╗"
echo " ██╗ ██║██║  ██║╚██████╔╝╚██████╔╝███████╗██║  ██║"
echo " ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${CYAN}Installation de JaggerFighter Pentest Suite${NC}"
echo "────────────────────────────────────────────"

# ── Vérification root ──────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[✗] Ce script doit être lancé en root : sudo bash install.sh${NC}"
    exit 1
fi

# ── Détection Kali ────────────────────────────────────────
if ! grep -qi "kali" /etc/os-release 2>/dev/null; then
    echo -e "${YELLOW}[⚠] Système non-Kali détecté. Le script est optimisé pour Kali Linux.${NC}"
    read -p "Continuer quand même ? (o/N) : " CONT
    [[ "$CONT" != "o" && "$CONT" != "O" ]] && exit 1
fi

step() { echo -e "\n${CYAN}[►] $1${NC}"; }
ok()   { echo -e "${GREEN}[✓] $1${NC}"; }
warn() { echo -e "${YELLOW}[⚠] $1${NC}"; }
fail() { echo -e "${RED}[✗] $1${NC}"; }

# ── Mise à jour apt ───────────────────────────────────────
step "Mise à jour des paquets apt"
apt-get update -qq
ok "apt à jour"

# ── Outils système ────────────────────────────────────────
step "Installation des outils de pentest"

TOOLS=(
    "nmap"
    "nikto"
    "gobuster"
    "hydra"
    "sqlmap"
    "theharvester"
    "python3"
    "python3-pip"
    "python3-venv"
)

for tool in "${TOOLS[@]}"; do
    if apt-get install -y -qq "$tool" 2>/dev/null; then
        ok "$tool installé"
    else
        warn "$tool : installation échouée (non critique)"
    fi
done

# ── Wordlists ─────────────────────────────────────────────
step "Vérification des wordlists"

if [ ! -f "/usr/share/wordlists/rockyou.txt" ]; then
    if [ -f "/usr/share/wordlists/rockyou.txt.gz" ]; then
        step "Décompression de rockyou.txt"
        gunzip /usr/share/wordlists/rockyou.txt.gz
        ok "rockyou.txt décompressé"
    else
        warn "rockyou.txt introuvable — Hydra fonctionnera avec une wordlist custom"
    fi
else
    ok "rockyou.txt présent"
fi

if [ ! -f "/usr/share/wordlists/dirb/common.txt" ]; then
    apt-get install -y -qq dirb 2>/dev/null || warn "dirb wordlists non installées"
else
    ok "wordlists dirb présentes"
fi

# ── Python venv ───────────────────────────────────────────
step "Création de l'environnement Python"

cd "$INSTALL_DIR"

if [ -d "venv" ]; then
    warn "venv existant — réutilisation"
else
    python3 -m venv venv
    ok "venv créé"
fi

source venv/bin/activate

# ── Dépendances Python ────────────────────────────────────
step "Installation des dépendances Python"

pip install --upgrade pip -q
pip install -r requirements.txt -q

ok "Dépendances Python installées"

# WeasyPrint (optionnel, pour PDF)
step "Installation de WeasyPrint (rapports PDF)"
if pip install weasyprint -q 2>/dev/null; then
    ok "WeasyPrint installé — rapports PDF disponibles"
else
    warn "WeasyPrint non installé — rapports PDF indisponibles (HTML OK)"
fi

# ── Dossiers ──────────────────────────────────────────────
step "Création des dossiers"
mkdir -p data reports/output
ok "Dossiers créés"

# ── Commande système ──────────────────────────────────────
step "Création de la commande 'jaggerfighter'"

cat > /usr/local/bin/jaggerfighter << SCRIPT
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python3 "$INSTALL_DIR/main.py" "\$@"
SCRIPT

chmod +x /usr/local/bin/jaggerfighter
ok "Commande 'jaggerfighter' disponible globalement"

# ── Alias bash ────────────────────────────────────────────
BASHRC="$HOME/.bashrc"
if ! grep -q "jaggerfighter" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# JaggerFighter Pentest Suite" >> "$BASHRC"
    echo "alias jf='jaggerfighter'" >> "$BASHRC"
    ok "Alias 'jf' ajouté dans ~/.bashrc"
fi

# ── Test final ────────────────────────────────────────────
step "Test de l'installation"

source venv/bin/activate
if python3 -c "from core.orchestrator import Orchestrator; print('Core OK')" 2>/dev/null; then
    ok "Core Python OK"
else
    fail "Erreur dans le core Python — vérifiez les logs"
fi

# ── Résumé ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ JaggerFighter installé avec succès !${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Lancement          : ${CYAN}jaggerfighter${NC} ou ${CYAN}jf${NC}"
echo -e "  Scan rapide        : ${CYAN}jf -t 192.168.1.1 --quick${NC}"
echo -e "  Activer licence Pro: ${CYAN}jf --activate VOTRE-CLE${NC}"
echo -e "  Documentation      : ${CYAN}docs/USAGE.md${NC}"
echo ""
echo -e "${YELLOW}  ⚠  Usage légal uniquement — sur systèmes autorisés${NC}"
echo ""




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