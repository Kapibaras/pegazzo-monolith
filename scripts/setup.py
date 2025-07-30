import subprocess
import sys


class Colors:
    HEADER = "\033[95m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


commands = [
    "pipenv install --dev",
    "pre-commit install",
    "pipenv clean",
    "pre-commit clean",
]

TAB = "    "


def run_commands():
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 Running setup commands...{Colors.RESET}")
    for command in commands:
        print(f"{Colors.CYAN}{Colors.BOLD}> Running:{Colors.RESET} {command}")
        try:
            # Merge stdout and stderr so we don't get duplicate/mixed lines
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Stream output line by line with indentation
            for line in process.stdout:
                print(f"{TAB}{line.rstrip()}")

            process.wait()
            if process.returncode != 0:
                print(f"{TAB}{Colors.RED}❌ Command failed: {command}{Colors.RESET}")
                sys.exit(process.returncode)

        except Exception as e:
            print(f"{TAB}{Colors.RED}❌ An error occurred: {e}{Colors.RESET}")
            sys.exit(1)
    print(f"{Colors.GREEN}{Colors.BOLD}✅ The setup was executed successfully!{Colors.RESET}")


if __name__ == "__main__":
    run_commands()
