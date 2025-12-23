import sys
import argparse
from seedrcc_tui.core import SeedrClient
from seedrcc_tui.cli import cmd_list, cmd_fetch, cmd_delete, cmd_add
from seedrcc_tui.tui import run_tui

def main():
    parser = argparse.ArgumentParser(
        description="SeedrCC TUI - Modern interface for Seedr.cc",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # Global flags
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in TUI mode")
    parser.add_argument("-n", "--non-interactive", action="store_true", help="Force non-interactive CLI mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List contents of your Seedr account")
    list_parser.add_argument("-d", "--depth", type=int, default=1, help="Maximum recursion depth (default: 1)")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Get download link for a file or folder (as zip)")
    fetch_parser.add_argument("id", help="The ID of the file or folder to fetch")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a file, folder, or torrent (type optional)")
    delete_parser.add_argument("identifier", help="The ID of the item, or the type (file/folder/torrent)")
    delete_parser.add_argument("id_if_type", nargs="?", help="The ID of the item (if type was provided first)")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new torrent or magnet link")
    add_parser.add_argument("torrent", help="Magnet link or torrent URL")

    # Help command
    subparsers.add_parser("help", help="Show this help message")

    args = parser.parse_args()

    # Core logic handler
    core = SeedrClient()

    # Determine mode:
    is_interactive = args.interactive
    force_non_interactive = args.non_interactive
    
    # If a command is given and -i is NOT given, we use CLI
    # If NO command is given, we use TUI (as default)
    
    if args.command == "help":
        parser.print_help()
        sys.exit(0)

    if args.command and not is_interactive:
        # CLI mode
        if args.command == "list":
            cmd_list(args, core)
        elif args.command == "fetch":
            cmd_fetch(args, core)
        elif args.command == "delete":
            cmd_delete(args, core)
        elif args.command == "add":
            cmd_add(args, core)
        else:
            parser.print_help()
    else:
        # Default mode (TUI) or forced TUI
        if force_non_interactive and not args.command:
            print("Error: No command provided for non-interactive mode.")
            parser.print_help()
            sys.exit(1)
        
        # Authenticate before starting TUI to avoid blocking TUI loop
        try:
            core.get_client(interactive=True)
        except Exception as e:
            print(f"Authentication failed: {e}")
            sys.exit(1)

        # Run TUI
        run_tui(core)

if __name__ == "__main__":
    main()