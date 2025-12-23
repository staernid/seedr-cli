import sys
from .core import SeedrClient
from .utils import format_size, sanitize_filename
from seedrcc.models import Folder, File, Torrent

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

def cmd_list(args, core: SeedrClient):
    """Handle the 'list' command."""
    usage = core.get_memory_bandwidth()
    print(f"\033[1mStorage:\033[0m {format_size(usage.space_used)} / {format_size(usage.space_max)}")
    print("\033[1mTree:\033[0m")
    contents = core.list_contents()
    children = []
    children.extend(contents.folders)
    children.extend(contents.files)
    children.extend(contents.torrents)
    
    for i, child in enumerate(children):
        enumerate_tree(core, child, "", i == len(children) - 1, max_depth=args.depth)

def cmd_fetch(args, core: SeedrClient):
    """Handle the 'fetch' command."""
    print(f"[*] Fetching ID: {args.id}")
    
    # 1. Try as file first
    try:
        result = core.fetch_file(args.id)
        if hasattr(result, 'url') and result.url:
            print(f"\n\033[1;32mType:\033[0m File")
            print(f"\033[1;32mName:\033[0m {result.name}")
            print(f"\033[1;32mURL:\033[0m  {result.url}")
            print(f"\nTo download:")
            base_name = sanitize_filename(result.name)
            print(f"wget '{result.url}' -O '{base_name}'")
            return
    except Exception:
        pass
    
    # 2. Try as folder (archive)
    try:
        folder_info = core.list_contents(args.id)
        if folder_info:
            print(f"[*] ID {args.id} identified as folder: {folder_info.name or 'Root'}")
            archive_result = core.create_archive(args.id)
            if archive_result.result:
                name = folder_info.name if folder_info.name else f"folder_{args.id}"
                print(f"\n\033[1;32mType:\033[0m Folder (Archive)")
                print(f"\033[1;32mName:\033[0m {name}.zip")
                print(f"\033[1;32mURL:\033[0m  {archive_result.archive_url}")
                print(f"\nTo download:")
                safe_name = sanitize_filename(name)
                print(f"wget '{archive_result.archive_url}' -O '{safe_name}.zip'")
                return
    except Exception:
        pass

    print(f"\033[1;31mError:\033[0m Could not fetch item with ID {args.id} (tried as file and folder)")

def cmd_delete(args, core: SeedrClient):
    """Handle the 'delete' command."""
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
            item_type = None

    found_type, found_name = core.find_item_by_id(target_id)
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

    if item_type:
        try:
            method = getattr(core, f"delete_{item_type}")
            method(target_id)
            print(f"\033[1;32mSuccessfully deleted {item_type} {target_id}\033[0m")
            return
        except Exception as e:
            if args.identifier in ["file", "folder", "torrent"]:
                print(f"\033[1;31mError:\033[0m {e}")
                return

    success = False
    for t in ["folder", "file", "torrent"]:
        try:
            getattr(core, f"delete_{t}")(target_id)
            print(f"\033[1;32mSuccessfully deleted as {t} {target_id}\033[0m")
            success = True
            break
        except:
            continue
    
    if not success:
        print(f"\033[1;31mError:\033[0m Could not find or delete item with ID {target_id}")

def cmd_add(args, core: SeedrClient):
    """Handle the 'add' command."""
    print(f"[*] Target: {args.torrent}")
    core.add_torrent(args.torrent)
    print("\n\033[1;32mSuccessfully added torrent\033[0m")
