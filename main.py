#!/usr/bin/env python3
"""
main.py - Point d'entrée principal de JaggerFighter
Interface menu interactive avec Rich. Lance : python main.py
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.rule import Rule

from core.orchestrator import Orchestrator
from core.license import get_license, TIER_COLORS, TIER_LABELS
from core.models import Severity
from core.nmap_module import NmapModule
from core.harvester_module import HarvesterModule
from core.nikto_module import NiktoModule
from core.gobuster_module import GobusterModule
from core.sqlmap_module import SQLMapModule
from core.hydra_module import HydraModule
from db.database import Database
from reports.generator import ReportGenerator

console = Console()

BANNER = r"""
     ██╗ █████╗  ██████╗  ██████╗ ███████╗██████╗
     ██║██╔══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
     ██║███████║██║  ███╗██║  ███╗█████╗  ██████╔╝
██   ██║██╔══██║██║   ██║██║   ██║██╔══╝  ██╔══██╗
╚█████╔╝██║  ██║╚██████╔╝╚██████╔╝███████╗██║  ██║
 ╚════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
███████╗██╗ ██████╗ ██╗  ██╗████████╗███████╗██████╗
██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝██╔════╝██╔══██╗
█████╗  ██║██║  ███╗███████║   ██║   █████╗  ██████╔╝
██╔══╝  ██║██║   ██║██╔══██║   ██║   ██╔══╝  ██╔══██╗
██║     ██║╚██████╔╝██║  ██║   ██║   ███████╗██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
"""

SEV_STYLE = {
    "critical": "bold red",
    "high":     "red",
    "medium":   "yellow",
    "low":      "blue",
    "info":     "dim",
}


# ─── Affichage bannière ─────────────────────────────────────────────────────

def show_banner():
    lic = get_license()
    tier_color = TIER_COLORS.get(lic.tier, "dim")
    tier_label = TIER_LABELS.get(lic.tier, "Free")

    console.print(f"[bold red]{BANNER}[/]")
    console.print(
        Panel(
            f"[bold white]Pentest Suite unifiée pour Kali Linux[/]\n"
            f"[dim]Nmap • Nikto • Gobuster • Hydra • SQLMap • theHarvester • CVE Lookup[/]\n\n"
            f"Tier : [{tier_color}]{tier_label}[/]"
            + (f"  |  [dim]{lic.email}[/]" if lic.email else "")
            + (f"\n[dim]⚠  Usage légal uniquement — sur systèmes autorisés[/]"),
            border_style="red",
            padding=(0, 2),
        )
    )


# ─── Menu principal ─────────────────────────────────────────────────────────

def show_main_menu() -> str:
    lic = get_license()
    console.print()
    console.print(Rule("[bold]Menu principal[/]", style="dim"))

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Num", style="bold cyan", width=4)
    table.add_column("Action", style="white")
    table.add_column("Tier", style="dim")

    table.add_row("1", "Nouveau scan",                "Free+")
    table.add_row("2", "Scan rapide (target en arg)", "Free+")
    table.add_row("3", "Historique des sessions",     "Free+")
    table.add_row("4", "Générer un rapport",          "Free+")
    table.add_row("─", "─" * 30,                      "")
    table.add_row("5", "Activer une licence Pro",     "Pro")
    table.add_row("6", "Statut de la licence",        "Free+")
    table.add_row("─", "─" * 30,                      "")
    table.add_row("0", "Quitter",                     "")

    console.print(table)
    return Prompt.ask("\n[bold cyan]Choix[/]", choices=["0","1","2","3","4","5","6"], default="1")


# ─── Sélection des modules ──────────────────────────────────────────────────

def select_modules(orch: Orchestrator) -> list[str]:
    lic = get_license()
    console.print()
    console.print(Rule("[bold]Sélection des modules[/]", style="dim"))

    modules = orch.list_modules()

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    table.add_column("#",         style="cyan",  width=4)
    table.add_column("Module",    style="white", width=14)
    table.add_column("Desc",      style="dim",   width=40)
    table.add_column("Dispo",     style="green", width=8)
    table.add_column("Tier",      style="dim",   width=8)

    for i, m in enumerate(modules, 1):
        available = "✓ Oui" if m["available"] else "[red]✗ Non[/]"
        tier_req = "Pro" if m["name"] in ("shodan",) else "Free"
        table.add_row(str(i), m["name"], m["description"][:40], available, tier_req)

    console.print(table)
    console.print("\n[dim]Entrez les numéros séparés par des virgules, ou 'all' pour tout[/]")
    raw = Prompt.ask("[bold cyan]Modules[/]", default="all")

    if raw.strip().lower() == "all":
        return [m["name"] for m in modules if m["available"]]

    selected = []
    for part in raw.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(modules) and modules[idx]["available"]:
                selected.append(modules[idx]["name"])
        except ValueError:
            pass

    return selected or [m["name"] for m in modules if m["available"]]


# ─── Scan principal ─────────────────────────────────────────────────────────

async def run_scan(target: str = "", quick: bool = False):
    lic = get_license()

    if not target:
        console.print()
        target = Prompt.ask("[bold cyan]Cible[/] (IP, domaine ou URL)")

    if not target:
        console.print("[red]✗ Cible vide.[/]")
        return

    # Initialise l'orchestrateur
    orch = Orchestrator()
    for ModClass in [NmapModule, HarvesterModule, NiktoModule,
                     GobusterModule, SQLMapModule, HydraModule]:
        orch.register_module(ModClass)

    # Sélection modules
    if quick:
        enabled = ["nmap", "nikto", "gobuster"]
        console.print(f"\n[dim]Mode rapide → modules : {', '.join(enabled)}[/]")
    else:
        enabled = select_modules(orch)

    if not enabled:
        console.print("[red]✗ Aucun module sélectionné.[/]")
        return

    # Confirmation
    console.print()
    console.print(Panel(
        f"[bold white]Cible    :[/] {target}\n"
        f"[bold white]Modules  :[/] {', '.join(enabled)}\n"
        f"[bold white]Licence  :[/] {TIER_LABELS.get(lic.tier)}",
        title="[bold]Récapitulatif du scan[/]",
        border_style="cyan",
    ))

    if not Confirm.ask("[bold yellow]Confirmer le scan ?[/]", default=True):
        return

    # Session
    db   = Database()
    gen  = ReportGenerator()
    session = orch.new_session(target)
    db.save_session(session)

    # Compteurs findings en temps réel
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0, "total": 0}

    def on_progress(mod, msg):
        console.print(f"  [dim cyan]{mod:12}[/] {msg}")

    def on_result(result):
        for f in result.findings:
            stats[f.severity.value] = stats.get(f.severity.value, 0) + 1
            stats["total"] += 1
            style = SEV_STYLE.get(f.severity.value, "white")
            sev   = f.severity.value.upper()[:4]
            host  = f" [{f.host}:{f.port}]" if f.host and f.port else (f" [{f.host}]" if f.host else "")
            console.print(f"  [{style}]{sev:4}[/]  {f.title[:65]}{host}")

    orch.on_progress(on_progress)
    orch.on_result(on_result)

    console.print()
    console.print(Rule("[bold green]Scan en cours[/]", style="green"))

    # Lance les modules
    for mod_name in enabled:
        console.print(f"\n[bold cyan]▶ {mod_name.upper()}[/]")
        try:
            result = await orch.run_module(mod_name, target)
            db.save_scan_result(session.session_id, result)

            if result.error_message:
                console.print(f"  [red]✗ Erreur : {result.error_message}[/]")
            else:
                dur = f"{result.duration:.1f}s" if result.duration else "—"
                console.print(f"  [green]✓ Terminé en {dur} — {len(result.findings)} finding(s)[/]")
        except Exception as e:
            console.print(f"  [red]✗ Exception : {e}[/]")

    # Rapport final
    console.print()
    console.print(Rule("[bold]Résultats[/]", style="dim"))
    risk = gen.calculate_risk_score(session)

    _print_risk_summary(risk, target, session.session_id)

    # Génère le rapport
    console.print()
    console.print("[dim]Génération du rapport...[/]")
    html_path = gen.generate_html(session)
    json_path = gen.generate_json(session)
    console.print(f"[green]✓ HTML : {html_path}[/]")
    console.print(f"[green]✓ JSON : {json_path}[/]")

    # PDF si Pro
    if lic.can("report_pdf"):
        pdf_path = gen.generate_pdf(session)
        if pdf_path:
            console.print(f"[green]✓ PDF  : {pdf_path}[/]")
    else:
        console.print("[dim]PDF disponible en tier Pro — jaggerfighter.io[/]")

    console.print()
    console.print(f"[bold green]Session ID : {session.session_id}[/]  [dim](utilisez --session {session.session_id} pour recharger)[/]")


def _print_risk_summary(risk: dict, target: str, session_id: str):
    score_color = "red" if risk["score"] >= 8 else "orange3" if risk["score"] >= 6 else "yellow" if risk["score"] >= 4 else "green"
    console.print(Panel(
        f"[bold white]Cible      :[/] {target}\n"
        f"[bold white]Session    :[/] {session_id}\n"
        f"[bold white]Score      :[/] [{score_color}]{risk['score']}/10 — {risk['label']}[/]\n\n"
        f"[bold red]CRITICAL : {risk['critical']:3}[/]   "
        f"[red]HIGH    : {risk['high']:3}[/]   "
        f"[yellow]MEDIUM  : {risk['medium']:3}[/]   "
        f"[blue]LOW     : {risk['low']:3}[/]   "
        f"[dim]INFO    : {risk['info']:3}[/]",
        title="[bold]Score de risque[/]",
        border_style=score_color,
    ))


# ─── Historique ─────────────────────────────────────────────────────────────

def show_history():
    db = Database()
    sessions = db.list_sessions()

    if not sessions:
        console.print("[dim]Aucune session enregistrée.[/]")
        return

    table = Table(title="Historique des sessions", box=box.ROUNDED)
    table.add_column("ID",       style="cyan",  width=10)
    table.add_column("Nom",      style="white", width=20)
    table.add_column("Cible",    style="white", width=22)
    table.add_column("Date",     style="dim",   width=12)
    table.add_column("Findings", style="red",   width=10, justify="right")

    for s in sessions:
        from datetime import datetime
        date = datetime.fromisoformat(s["created_at"]).strftime("%d/%m/%Y")
        table.add_row(s["session_id"], s["name"][:20], s["target"][:22], date, str(s["total_findings"]))

    console.print(table)

    stats = db.get_stats()
    console.print(f"\n[dim]Total : {stats.get('total_sessions', 0)} session(s), "
                  f"{stats.get('total_findings', 0)} finding(s) — "
                  f"{stats.get('critical', 0)} critiques[/]")


# ─── Rapport depuis session existante ───────────────────────────────────────

def generate_report_interactive():
    db  = Database()
    gen = ReportGenerator()
    sessions = db.list_sessions()

    if not sessions:
        console.print("[red]✗ Aucune session disponible.[/]")
        return

    show_history()
    session_id = Prompt.ask("\n[bold cyan]Session ID[/]")
    session = db.load_session(session_id)

    if not session:
        console.print(f"[red]✗ Session '{session_id}' introuvable.[/]")
        return

    fmt = Prompt.ask("[bold cyan]Format[/]", choices=["html", "json", "pdf", "all"], default="html")

    if fmt in ("html", "all"):
        p = gen.generate_html(session)
        console.print(f"[green]✓ HTML : {p}[/]")
    if fmt in ("json", "all"):
        p = gen.generate_json(session)
        console.print(f"[green]✓ JSON : {p}[/]")
    if fmt in ("pdf", "all"):
        lic = get_license()
        if lic.can("report_pdf"):
            p = gen.generate_pdf(session)
            if p: console.print(f"[green]✓ PDF : {p}[/]")
        else:
            console.print("[yellow]⚠ PDF disponible en tier Pro.[/]")


# ─── Gestion licence ────────────────────────────────────────────────────────

def activate_license():
    console.print()
    console.print(Panel(
        "[bold]Activer une licence JaggerFighter Pro[/]\n\n"
        "[dim]Obtenez votre clé sur : [bold cyan]https://jaggerfighter.io/pro[/]\n\n"
        "Tiers disponibles :\n"
        "  [cyan]Pro  (~10$/mois)[/] : CVE illimité, Shodan, Burp Pro, PDF\n"
        "  [gold1]Team (~30$/mois)[/] : Multi-user, cloud scans, API REST[/]",
        border_style="cyan",
    ))

    key = Prompt.ask("[bold cyan]Clé de licence[/]")
    if not key:
        return

    lic = get_license()
    result = lic.activate(key)

    if result["success"]:
        console.print(f"\n[bold green]✓ {result['message']}[/]")
    else:
        console.print(f"\n[bold red]✗ {result['message']}[/]")


def show_license_status():
    lic = get_license()
    status = lic.status_dict()
    tier_color = TIER_COLORS.get(lic.tier, "dim")
    features = status["features"]

    console.print()
    console.print(Panel(
        f"[bold white]Tier    :[/] [{tier_color}]{status['label']}[/]\n"
        f"[bold white]Clé     :[/] {status['key']}\n"
        f"[bold white]Email   :[/] {status['email']}\n"
        f"[bold white]Expire  :[/] {status['expires']}\n\n"
        f"[bold]Fonctionnalités :[/]\n"
        f"  CVE lookup     : {'[green]✓[/] (illimité)' if not features.get('cve_limit') else f'[yellow]✓[/] (limité {features[\"cve_limit\"]} req/30s)'}\n"
        f"  Rapport PDF    : {'[green]✓[/]' if features.get('report_pdf') else '[red]✗[/] — Pro requis'}\n"
        f"  Shodan API     : {'[green]✓[/]' if features.get('shodan') else '[red]✗[/] — Pro requis'}\n"
        f"  Scans planifiés: {'[green]✓[/]' if features.get('scheduled_scans') else '[red]✗[/] — Pro requis'}\n"
        f"  Multi-user     : {'[green]✓[/]' if features.get('multi_user') else '[red]✗[/] — Team requis'}",
        title="[bold]Statut de la licence[/]",
        border_style=tier_color,
    ))

    if not lic.is_pro:
        console.print(
            "\n[dim]Passez Pro sur [bold cyan]https://jaggerfighter.io/pro[/] "
            "pour débloquer CVE illimité, Shodan, PDF et plus.[/]"
        )


# ─── Point d'entrée ─────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="JaggerFighter — Pentest Suite unifiée pour Kali Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python main.py                          Menu interactif
  python main.py -t 192.168.1.1          Scan interactif sur cible
  python main.py -t 192.168.1.1 --quick  Scan rapide (nmap+nikto+gobuster)
  python main.py --activate JFPRO-XXXX   Activer une licence Pro
  python main.py --history               Voir l'historique
  python main.py --report SESSION_ID     Générer rapport d'une session
        """
    )
    p.add_argument("-t", "--target",   help="Cible (IP, domaine, URL)")
    p.add_argument("--quick",          action="store_true", help="Scan rapide (3 modules)")
    p.add_argument("--activate",       metavar="KEY",       help="Activer une clé de licence")
    p.add_argument("--history",        action="store_true", help="Afficher l'historique")
    p.add_argument("--report",         metavar="SESSION_ID",help="Générer rapport d'une session")
    p.add_argument("--status",         action="store_true", help="Afficher le statut de la licence")
    p.add_argument("--no-banner",      action="store_true", help="Pas de bannière ASCII")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.no_banner:
        show_banner()

    # ── Commandes directes (sans menu) ──────────────────────────────────────
    if args.activate:
        lic = get_license()
        result = lic.activate(args.activate)
        if result["success"]:
            console.print(f"[bold green]✓ {result['message']}[/]")
        else:
            console.print(f"[bold red]✗ {result['message']}[/]")
        return

    if args.history:
        show_history()
        return

    if args.status:
        show_license_status()
        return

    if args.report:
        db  = Database()
        gen = ReportGenerator()
        session = db.load_session(args.report)
        if session:
            p = gen.generate_html(session)
            console.print(f"[green]✓ Rapport : {p}[/]")
        else:
            console.print(f"[red]✗ Session '{args.report}' introuvable.[/]")
        return

    if args.target:
        asyncio.run(run_scan(args.target, quick=args.quick))
        return

    # ── Menu interactif ──────────────────────────────────────────────────────
    while True:
        try:
            choice = show_main_menu()
            if choice == "0":
                console.print("\n[dim]À bientôt — restez légal.[/]")
                break
            elif choice == "1":
                asyncio.run(run_scan())
            elif choice == "2":
                asyncio.run(run_scan(quick=True))
            elif choice == "3":
                show_history()
            elif choice == "4":
                generate_report_interactive()
            elif choice == "5":
                activate_license()
            elif choice == "6":
                show_license_status()
        except KeyboardInterrupt:
            console.print("\n\n[dim]Interruption — retour au menu.[/]")
            continue


if __name__ == "__main__":
    main()




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