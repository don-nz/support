import os
import re
import subprocess
from pathlib import Path



class WinREEnvironment:
    """Handles system environment detection and drive mapping in WinRE."""

    def __init__(self, target_drive="C:"):
        self.target_drive = target_drive.rstrip(":") + ":"
        self.win_dir = Path(f"{self.target_drive}\\Windows")
        self.srt_log = (
            self.win_dir / "System32" / "Logfiles" / "Srt" / "SrtTrail.txt"
        )

    def is_valid_windows_drive(self) -> bool:
        """Verifies if the designated drive contains a Windows installation."""
        return self.win_dir.exists() and (self.win_dir / "System32").exists()


class CommandRunner:
    """Executes system CLI tools and captures output safely."""

    @staticmethod
    def run(cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Execution Error: {str(e)}"


class DISMManager:
    """Encapsulates DISM operations for package management and repairs."""

    def __init__(self, env: WinREEnvironment):
        self.env = env

    def revert_pending_actions(self) -> str:
        cmd = f"dism /image:{self.env.target_drive}\\ /cleanup-image /revertpendingactions"
        return CommandRunner.run(cmd)

    def get_installed_packages(self) -> list[dict]:
        """Parses raw DISM table output into structured objects."""
        cmd = f"dism /image:{self.env.target_drive}\\ /get-packages /format:table"
        raw_output = CommandRunner.run(cmd)

        packages = []
        for line in raw_output.splitlines():
            if "Package_for_" in line or "RollupFix" in line:
                parts = re.split(r"\s{2,}", line.strip())
                if len(parts) >= 3:
                    packages.append(
                        {
                            "id": parts[0],
                            "state": parts[1],
                            "release_time": parts[2],
                        }
                    )
        return packages

    def remove_package(self, package_id: str) -> str:
        cmd = f"dism /image:{self.env.target_drive}\\ /remove-package /packagename:{package_id}"
        return CommandRunner.run(cmd)


class RepairApp:
    """Main application controller managing interactive CLI state."""

    def __init__(self):
        self.env = WinREEnvironment(target_drive="C:")
        self.dism = DISMManager(self.env)

    def display_menu(self):
        print("\n==========================================")
        print(f" WinRE Python Diagnostic Suite ")
        print(f" Target Drive: [{self.env.target_drive}]")
        print("==========================================")
        print("1. Change Target Drive Letter")
        print("2. Read SrtTrail.txt Log")
        print("3. Revert Pending DISM Actions")
        print("4. List Update Packages (Parsed)")
        print("5. Remove Specific Update Package")
        print("6. Run Offline SFC Repair Scan")
        print("7. Exit")
        print("==========================================")

    def run(self):
        while True:
            self.display_menu()
            choice = input("Select an option (1-7): ").strip()

            if choice == "1":
                drive = input(
                    "Enter Windows Drive Letter (e.g., C, D): "
                ).strip()
                self.env = WinREEnvironment(target_drive=drive)
                self.dism = DISMManager(self.env)
                if not self.env.is_valid_windows_drive():
                    print(
                        f"\n[!] Warning: {self.env.win_dir} not detected on drive {self.env.target_drive}"
                    )
                else:
                    print(
                        f"\n[+] Validated Windows installation at {self.env.win_dir}"
                    )

            elif choice == "2":
                if self.env.srt_log.exists():
                    print(f"\n--- Reading {self.env.srt_log} ---")
                    print(self.env.srt_log.read_text(errors="replace")[-2000:])
                else:
                    print(f"\n[!] Log file not found at {self.env.srt_log}")

            elif choice == "3":
                print("\nRunning DISM Revert Pending Actions...")
                print(self.dism.revert_pending_actions())

            elif choice == "4":
                print("\nFetching Installed Packages...")
                pkgs = self.dism.get_installed_packages()
                if not pkgs:
                    print(
                        "[!] No packages parsed or DISM output was empty."
                    )
                for idx, pkg in enumerate(pkgs, 1):
                    print(
                        f"[{idx}] {pkg['id']}\n    State: {pkg['state']} | Date: {pkg['release_time']}"
                    )

            elif choice == "5":
                pkgs = self.dism.get_installed_packages()
                if not pkgs:
                    print("[!] No packages available to display.")
                    continue
                for idx, pkg in enumerate(pkgs, 1):
                    print(f"[{idx}] {pkg['id']} ({pkg['state']})")

                selection = input(
                    "\nSelect package number to REMOVE (or 'cancel'): "
                ).strip()
                if selection.isdigit() and 1 <= int(selection) <= len(pkgs):
                    target_pkg = pkgs[int(selection) - 1]["id"]
                    print(f"\nRemoving package: {target_pkg}")
                    print(self.dism.remove_package(target_pkg))

            elif choice == "6":
                print("\nRunning Offline SFC Scan...")
                cmd = f"sfc /scannow /offbootdir={self.env.target_drive}\\ /offwindir={self.env.win_dir}"
                print(CommandRunner.run(cmd))

            elif choice == "7":
                print("Exiting Diagnostic Suite.")
                break


if __name__ == "__main__":
    app = RepairApp()
    app.run()
    