import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Enable ANSI colors in Windows CMD
os.system("")

# ---------------------------------------------------------------------------
# Path Configuration: Add embeddable Python / python_libs to sys.path
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

# Check for python_libs directory or embeddable site-packages
possible_lib_paths = [
    ROOT_DIR / "Python" / "Lib" / "site-packages",
    ROOT_DIR / "Python",
    SCRIPT_DIR / "python_libs",
]

for lib_path in possible_lib_paths:
    if lib_path.exists() and str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))

# ---------------------------------------------------------------------------
# Dynamic UI Library Imports (with ANSI Fallback)
# ---------------------------------------------------------------------------
HAS_RICH = False
HAS_QUESTIONARY = False

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    console = Console()
    HAS_RICH = True
    HAS_QUESTIONARY = True
except ImportError:
    pass

# ANSI Formatting Fallbacks
CLEAR = "\033[2J\033[H"
HEADER_BG = "\033[1;37;44m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"


class WinREDiagnostics:

    def __init__(self, target_drive: str = "C"):
        self.target_drive = target_drive.upper().rstrip(":\\") + ":"
        self.windir = Path(f"{self.target_drive}\\Windows")
        self.servicing_dir = self.windir / "Servicing" / "Packages"
        self.backup_dir = self.servicing_dir / "Corrupt_Backup"

    def verify_environment(self) -> bool:
        """Verifies that the target Windows directory exists."""
        return self.windir.exists()

    def validate_and_quarantine_manifests(self) -> int:
        """Scans servicing package XML files (.mum) and quarantines invalid ones."""
        if not self.servicing_dir.exists():
            msg = f"[!] Servicing directory does not exist: {self.servicing_dir}"
            if HAS_RICH:
                console.print(f"[bold yellow]{msg}[/bold yellow]")
            else:
                print(f"{YELLOW}{msg}{RESET}")
            return 0

        msg = f"[*] Scanning XML manifests in {self.servicing_dir}..."
        if HAS_RICH:
            console.print(f"[bold cyan]{msg}[/bold cyan]")
        else:
            print(f"{CYAN}{msg}{RESET}")

        corrupt_files = []

        for xml_file in self.servicing_dir.glob("*.mum"):
            try:
                ET.parse(xml_file)
            except (ET.ParseError, Exception) as e:
                err_msg = f"[!] Corrupt manifest detected: {xml_file.name} | Error: {e}"
                if HAS_RICH:
                    console.print(f"[bold red]{err_msg}[/bold red]")
                else:
                    print(f"{RED}{err_msg}{RESET}")
                corrupt_files.append(xml_file)

        if corrupt_files:
            q_msg = f"[!] Found {len(corrupt_files)} corrupted XML manifest(s). Quarantining..."
            if HAS_RICH:
                console.print(f"[bold yellow]{q_msg}[/bold yellow]")
            else:
                print(f"{YELLOW}{q_msg}{RESET}")

            self.backup_dir.mkdir(parents=True, exist_ok=True)

            for file_path in corrupt_files:
                dest = self.backup_dir / file_path.name
                try:
                    file_path.rename(dest)
                    print(f"    [->] Quarantined: {file_path.name}")
                except Exception as err:
                    fail_msg = f"    [x] Failed to move {file_path.name}: {err}"
                    if HAS_RICH:
                        console.print(f"[bold red]{fail_msg}[/bold red]")
                    else:
                        print(f"{RED}{fail_msg}{RESET}")
        else:
            ok_msg = "[+] All XML servicing manifests parsed successfully."
            if HAS_RICH:
                console.print(f"[bold green]{ok_msg}[/bold green]")
            else:
                print(f"{GREEN}{ok_msg}{RESET}")

        return len(corrupt_files)

    def run_dism_repair(self):
        """Executes offline DISM repair commands using WinRE binaries."""
        msg = "[*] Initiating offline DISM cleanup and repair..."
        if HAS_RICH:
            console.print(f"[bold cyan]{msg}[/bold cyan]")
        else:
            print(f"{CYAN}{msg}{RESET}")

        winre_dism = Path(r"X:\Sources\Recovery\Tools\dism.exe")
        dism_bin = (
            str(winre_dism)
            if winre_dism.exists()
            else f"{self.target_drive}\\Windows\\System32\\dism.exe"
        )

        cmd = [
            dism_bin,
            f"/Image:{self.target_drive}\\",
            "/Cleanup-Image",
            "/RevertPendingActions",
        ]

        print(f"[*] Executing: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
            print(result.stdout)
            if result.stderr:
                if HAS_RICH:
                    console.print(
                        f"[bold red][!] DISM Stderr: {result.stderr}[/bold red]"
                    )
                else:
                    print(f"{RED}[!] DISM Stderr: {result.stderr}{RESET}")
        except Exception as e:
            if HAS_RICH:
                console.print(
                    f"[bold red][x] Subprocess execution failed: {e}[/bold red]"
                )
            else:
                print(f"{RED}[x] Subprocess execution failed: {e}{RESET}")

    def run_sfc_scan(self):
        """Executes offline System File Checker (SFC) scan."""
        msg = "[*] Initiating offline System File Checker (SFC)..."
        if HAS_RICH:
            console.print(f"[bold cyan]{msg}[/bold cyan]")
        else:
            print(f"{CYAN}{msg}{RESET}")

        cmd = [
            "sfc",
            "/scannow",
            f"/offbootdir={self.target_drive}\\",
            f"/offwindir={self.windir}",
        ]

        print(f"[*] Executing: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )
            print(result.stdout)
            if result.stderr:
                if HAS_RICH:
                    console.print(
                        f"[bold red][!] SFC Stderr: {result.stderr}[/bold red]"
                    )
                else:
                    print(f"{RED}[!] SFC Stderr: {result.stderr}{RESET}")
        except Exception as e:
            if HAS_RICH:
                console.print(
                    f"[bold red][x] Subprocess execution failed: {e}[/bold red]"
                )
            else:
                print(f"{RED}[x] Subprocess execution failed: {e}{RESET}")


class WinRETuiApp:

    def __init__(self, target_drive: str = "C"):
        self.engine = WinREDiagnostics(target_drive=target_drive)

    def draw_header(self):
        os.system("cls" if os.name == "nt" else "clear")

        env_ok = self.engine.verify_environment()
        status_str = "VALID OS TARGET" if env_ok else "INVALID TARGET PATH"

        if HAS_RICH:
            table = Table(show_header=False, expand=True, box=None)
            table.add_column(justify="left")
            table.add_column(justify="right")

            status_style = "bold green" if env_ok else "bold red"
            table.add_row(
                f"[bold cyan]Target Partition:[/] [{self.engine.target_drive}\\]",
                f"[bold cyan]OS Status:[/] [{status_style}]{status_str}[/]",
            )

            console.print(
                Panel(
                    table,
                    title="[bold white on blue] WinRE Recovery & Diagnostic Suite v2.0 [/bold white on blue]",
                    border_style="blue",
                )
            )
        else:
            print(
                f"{HEADER_BG} WinRE Recovery & Diagnostic Suite v2.0 {' ' * 38}{RESET}"
            )
            env_color = GREEN if env_ok else RED
            print(
                f"{CYAN}Target Partition: [{self.engine.target_drive}\\]   |   OS Status: {env_color}{status_str}{RESET}"
            )
            print("─" * 80)

    def run(self):
        while True:
            self.draw_header()

            if not self.engine.verify_environment():
                err_msg = f"[!] Error: Could not locate Windows directory at {self.engine.windir}"
                hint_msg = f"[*] Try passing a different target drive (e.g., run_diag.cmd D)"
                if HAS_RICH:
                    console.print(f"[bold red]{err_msg}[/bold red]")
                    console.print(f"[bold yellow]{hint_msg}[/bold yellow]\n")
                else:
                    print(f"{RED}{err_msg}{RESET}")
                    print(f"{YELLOW}{hint_msg}{RESET}\n")

            options_map = {
                "Scan & Quarantine Corrupt XML Manifests": self.action_check_xml,
                "Execute Offline DISM Action Revert": self.action_dism,
                "Run Offline System File Checker (SFC)": self.action_sfc,
                "Run Full Diagnostic & Repair Pipeline": self.action_full_auto,
                "Exit Recovery Suite": self.action_exit,
            }

            if HAS_QUESTIONARY:
                choice = questionary.select(
                    "Select a diagnostic task:",
                    choices=list(options_map.keys()),
                ).ask()

                if choice is None:  # User hit Ctrl+C
                    self.action_exit()

                action = options_map[choice]
            else:
                print(f"{BOLD}Select a diagnostic option:{RESET}\n")
                for idx, label in enumerate(options_map.keys(), 1):
                    print(f"  {idx}. {label}")

                print("\n" + "─" * 80)
                raw_choice = input(
                    f"{BOLD}Enter choice (1-{len(options_map)}): {RESET}"
                ).strip()

                if (
                    raw_choice.isdigit()
                    and 1 <= int(raw_choice) <= len(options_map)
                ):
                    selected_label = list(options_map.keys())[
                        int(raw_choice) - 1
                    ]
                    action = options_map[selected_label]
                else:
                    continue

            print("\n==================================================")
            print(" Executing Selected Diagnostic Action")
            print("==================================================\n")

            action()

            if HAS_RICH:
                console.print(
                    "\n[bold green][+] Task complete.[/bold green] Press Enter to return to menu..."
                )
            else:
                print(
                    f"\n{GREEN}[+] Task complete.{RESET} Press Enter to return to menu..."
                )
            input()

    def action_check_xml(self):
        self.engine.validate_and_quarantine_manifests()

    def action_dism(self):
        self.engine.run_dism_repair()

    def action_sfc(self):
        self.engine.run_sfc_scan()

    def action_full_auto(self):
        print("--- Phase 1: Servicing Manifest Check ---")
        self.engine.validate_and_quarantine_manifests()

        print("\n--- Phase 2: DISM Offline Repair ---")
        self.engine.run_dism_repair()

        print("\n--- Phase 3: System File Checker ---")
        self.engine.run_sfc_scan()

    def action_exit(self):
        if HAS_RICH:
            console.print(
                "[bold yellow][*] Exiting WinRE Diagnostic Suite.[/bold yellow]"
            )
        else:
            print(f"\n{YELLOW}[*] Exiting WinRE Diagnostic Suite.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "C"
    app = WinRETuiApp(target_drive=target)
    app.run()