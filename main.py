import sys
import argparse
from seedrcc import Seedr
from seedrcc.models import Folder, File, Torrent
from utils import load_token, save_token, format_size, sanitize_filename

def get_client():
    """Authenticate and return a Seedr client."""
    token = load_token()
    if token:
        return Seedr(token=token, on_token_refresh=save_token)
    
    # Device flow authentication
    codes = Seedr.get_device_code()
    print(f"[*] Authentication required.")
    print(f"[*] Please go to: {codes.verification_url}")
    print(f"[*] Enter code: {codes.user_code}")
    input("[?] Press Enter after authorizing...")
    
    client = Seedr.from_device_code(codes.device_code, on_token_refresh=save_token)
    save_token(client.token)
    return client

def get_node_display(node):
    """Return a styled string representation of the node."""
    if isinstance(node, Folder):
        return f"\033[1;34m[DIR]\033[0m  {node.name:<40} ({format_size(node.size)}) [ID: {node.id}]"
    elif isinstance(node, File):
        return f"\033[1;32m[FILE]\033[0m {node.name:<40} ({format_size(node.size)}) [ID: {node.folder_file_id}]"
    elif isinstance(node, Torrent):
        return f"\033[1;33m[TOR]\033[0m  {node.name:<40} ({format_size(node.size)}) [ID: {node.id}]"
    return str(node)

def enumerate_tree(client, node, prefix: str = "", is_last: bool = True, depth: int = 0, max_depth: int = 2):
    """Recursively print the tree structure."""
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{get_node_display(node)}")

    if isinstance(node, Folder) and depth < max_depth:
        child_prefix = prefix + ("    " if is_last else "│   ")
        try:
            fetched = client.list_contents(str(node.id))
            children = []
            children.extend(fetched.folders)
            children.extend(fetched.files)
            children.extend(fetched.torrents)
            
            for i, child in enumerate(children):
                enumerate_tree(client, child, child_prefix, i == len(children) - 1, depth + 1, max_depth)
        except Exception as e:
            print(f"{child_prefix}└── \033[1;31m[Error: {e}]\033[0m")

def cmd_list(args):
    """Handle the 'list' command."""
    client = get_client()
    with client:
        usage = client.get_memory_bandwidth()
        print(f"\033[1mStorage:\033[0m {format_size(usage.space_used)} / {format_size(usage.space_max)}")
        print("\033[1mTree:\033[0m")
        contents = client.list_contents()
        # Seedr root is effectively a ListContentsResult which isn't a Folder but has similar properties
        # We can fake a root folder or just list its children
        children = []
        children.extend(contents.folders)
        children.extend(contents.files)
        children.extend(contents.torrents)
        
        for i, child in enumerate(children):
            enumerate_tree(client, child, "", i == len(children) - 1, max_depth=args.depth)

def cmd_fetch(args):
    """Handle the 'fetch' command."""
    client = get_client()
    with client:
        print(f"[*] Fetching file ID: {args.id}")
        try:
            result = client.fetch_file(args.id)
            print(f"\n\033[1;32mName:\033[0m {result.name}")
            print(f"\033[1;32mURL:\033[0m  {result.url}")
            print(f"\nTo download:")
            print(f"wget '{result.url}' -O '{sanitize_filename(result.name)}'")
        except Exception as e:
            print(f"\033[1;31mError:\033[0m {e}")

def cmd_delete(args):
    """Handle the 'delete' command."""
    client = get_client()
    with client:
        print(f"[*] Deleting {args.type} ID: {args.id}")
        confirm = input(f"[?] Are you sure you want to delete this {args.type}? [y/N] ").lower()
        if confirm != 'y':
            print("[*] Aborted.")
            return

        try:
            method_name = f"delete_{args.type}"
            if not hasattr(client, method_name):
                print(f"\033[1;31mError:\033[0m Unknown type '{args.type}'. Use: folder, file, or torrent.")
                return
            
            getattr(client, method_name)(args.id)
            print(f"\033[1;32mSuccessfully deleted {args.type} {args.id}\033[0m")
        except Exception as e:
            print(f"\033[1;31mError:\033[0m {e}")

def cmd_add(args):
    """Handle the 'add' command (placeholder)."""
    print(f"[*] Target: {args.torrent}")
    client = get_client()
    with client:
        client.add_torrent(args.torrent)
    print("\n\033[1;32mSuccessfully added torrent\033[0m")

def main():
    parser = argparse.ArgumentParser(
        description="Seedr CLI - Modern interface for Seedr.cc",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List contents of your Seedr account")
    list_parser.add_argument("-d", "--depth", type=int, default=1, help="Maximum recursion depth (default: 1)")
    list_parser.set_defaults(func=cmd_list)

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Get download link for a file")
    fetch_parser.add_argument("id", help="The ID of the file to fetch")
    fetch_parser.set_defaults(func=cmd_fetch)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a file, folder, or torrent")
    delete_parser.add_argument("type", choices=["file", "folder", "torrent"], help="Type of item to delete")
    delete_parser.add_argument("id", help="The ID of the item to delete")
    delete_parser.set_defaults(func=cmd_delete)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new torrent or magnet link")
    add_parser.add_argument("torrent", help="Magnet link or torrent URL")
    add_parser.set_defaults(func=cmd_add)

    # Help command (explicit)
    help_parser = subparsers.add_parser("help", help="Show this help message")

    args = parser.parse_args()

    if args.command == "help" or not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()