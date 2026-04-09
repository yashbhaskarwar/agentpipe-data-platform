import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

def _check_env() -> None:
    """Fail fast if ANTHROPIC_API_KEY is missing."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY is not set.\n"
            "Add it to your .env file:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...\n"
        )
        sys.exit(1)

def _print_banner() -> None:
    print(
        "\n"
        "╔══════════════════════════════════════════╗\n"
        "║         AgentPipe — CLI Interface        ║\n"
        "╚══════════════════════════════════════════╝\n"
    )

def main() -> None:
    _check_env()
    _print_banner()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        print(f"You entered: {user_input}")

if __name__ == "__main__":
    main()