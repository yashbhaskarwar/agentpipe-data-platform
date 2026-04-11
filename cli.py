import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

def _check_env() -> None:
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

    from agent.agent import run_agent

    _print_banner()

    conversation_history: list = []

    print("Example queries to try:")
    print("  • What's the status of the ingestion pipeline?")
    print("  • Show me all failed runs in the last 7 days")
    print("  • Were there any data quality issues this week?")
    print("  • Trigger the transformation pipeline")
    print("  • Give me full details of run ID 5")
    print()

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

        if user_input.lower() == "reset":
            conversation_history = []
            print("[Conversation history cleared.]\n")
            continue

        if user_input.lower() == "history":
            import json
            print(json.dumps(conversation_history, indent=2, default=str))
            continue

        print("Agent: ", end="", flush=True)

        try:
            response, conversation_history = run_agent(
                user_message=user_input,
                conversation_history=conversation_history,
            )
            print(response)
        except Exception as exc:
            print(f"[Error: {exc}]")

if __name__ == "__main__":
    main()