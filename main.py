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

def find_item_by_id(client, target_id):
    """Try to find an item by ID in the root contents to identify its type and name."""
    try:
        contents = client.list_contents()
        for f in contents.folders:
            if str(f.id) == str(target_id):
                return "folder", f.name
        for f in contents.files:
            if str(f.folder_file_id) == str(target_id):
                return "file", f.name
        for t in contents.torrents:
            if str(t.id) == str(target_id):
                return "torrent", t.name
    except:
        pass
    return None, None

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
        # Determine ID and Type based on arguments
        if args.identifier in ["file", "folder", "torrent"]:
            item_type = args.identifier
            target_id = args.id_if_type
            if not target_id:
                print(f"\033[1;31mError:\033[0m ID required when type is specified.")
                return
        else:
            target_id = args.identifier
            item_type = args.id_if_type
            if item_type and item_type not in ["file", "folder", "torrent"]:
                # Second argument provided but not a valid type, ignore it
                item_type = None

        item_name = None
        # Try to identify the item for better UX (resolve name even if type is known)
        found_type, found_name = find_item_by_id(client, target_id)
        
        if not item_type:
            item_type = found_type
        
        item_name = found_name

        display_type = item_type or "item"
        display_name = f" '{item_name}'" if item_name else ""
        
        print(f"[*] Deleting {display_type}{display_name} (ID: {target_id})")
        confirm = input(f"[?] Are you sure you want to delete this {display_type}? [y/N] ").lower()
        if confirm != 'y':
            print("[*] Aborted.")
            return

        # If we know the type (or think we do), try it first
        if item_type:
            try:
                method = getattr(client, f"delete_{item_type}")
                method(target_id)
                print(f"\033[1;32mSuccessfully deleted {item_type} {target_id}\033[0m")
                return
            except Exception as e:
                # If auto-detected, maybe it was wrong? Try fallback if so.
                if args.identifier in ["file", "folder", "torrent"]:
                    print(f"\033[1;31mError:\033[0m {e}")
                    return

        # Fallback/Unknown type: try all methods
        success = False
        for t in ["folder", "file", "torrent"]:
            try:
                getattr(client, f"delete_{t}")(target_id)
                print(f"\033[1;32mSuccessfully deleted as {t} {target_id}\033[0m")
                success = True
                break
            except:
                continue
        
        if not success:
            print(f"\033[1;31mError:\033[0m Could not find or delete item with ID {target_id}")

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
    delete_parser = subparsers.add_parser("delete", help="Delete a file, folder, or torrent (type optional)")
    delete_parser.add_argument("identifier", help="The ID of the item, or the type (file/folder/torrent)")
    delete_parser.add_argument("id_if_type", nargs="?", help="The ID of the item (if type was provided first)")
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