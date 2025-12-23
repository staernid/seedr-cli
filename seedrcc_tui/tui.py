from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Input, Button, DataTable
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import on
from .core import SeedrClient
from .utils import format_size, sanitize_filename
from seedrcc.models import Folder, File, Torrent

class AddTorrentModal(ModalScreen[str]):
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Add Torrent / Magnet Link", id="modal-title"),
            Input(placeholder="Magnet link or Torrent URL", id="torrent-input"),
            Horizontal(
                Button("Cancel", variant="error", id="cancel"),
                Button("Add", variant="success", id="add"),
                classes="modal-buttons"
            ),
            id="modal-container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(None)

    @on(Button.Pressed, "#add")
    def add(self):
        self.dismiss(self.query_one("#torrent-input", Input).value)

class SeedrItem(ListItem):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def compose(self) -> ComposeResult:
        icon = "📁" if isinstance(self.node, Folder) else "📄" if isinstance(self.node, File) else "🧲"
        size = format_size(getattr(self.node, 'size', 0))
        yield Horizontal(
            Label(f"{icon} {self.node.name}", classes="node-name"),
            Label(size, classes="node-size"),
            Label(f"ID: {getattr(self.node, 'id', getattr(self.node, 'folder_file_id', 'N/A'))}", classes="node-id"),
        )

class SeedrApp(App):
    TITLE = "Seedr TUI"
    CSS = """
    #main-container {
        padding: 1;
    }
    #storage-info {
        background: $accent;
        color: $text;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
        text-style: bold;
    }
    .node-name {
        width: 1fr;
    }
    .node-size {
        width: 15;
        text-align: right;
        color: $text-muted;
    }
    .node-id {
        width: 15;
        text-align: right;
        color: $text-disabled;
    }
    #modal-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
        align: center middle;
    }
    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .modal-buttons {
        margin-top: 1;
        align: center middle;
    }
    .modal-buttons Button {
        margin: 0 1;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("a", "add", "Add Torrent"),
        Binding("d", "delete", "Delete Selected"),
        Binding("f", "fetch", "Fetch Link"),
    ]

    def __init__(self, core: SeedrClient):
        super().__init__()
        self.core = core

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Storage Loading...", id="storage-info"),
            ListView(id="item-list"),
            id="main-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        storage_info = self.query_one("#storage-info", Static)
        item_list = self.query_one("#item-list", ListView)
        
        try:
            usage = self.core.get_memory_bandwidth()
            storage_info.update(f"Storage: {format_size(usage.space_used)} / {format_size(usage.space_max)}")
            
            contents = self.core.list_contents()
            item_list.clear()
            
            for folder in contents.folders:
                item_list.append(SeedrItem(folder))
            for file in contents.files:
                item_list.append(SeedrItem(file))
            for torrent in contents.torrents:
                item_list.append(SeedrItem(torrent))
                
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_refresh(self) -> None:
        self.refresh_list()

    async def action_add(self) -> None:
        def handle_add(torrent_url: str | None):
            if torrent_url:
                try:
                    self.core.add_torrent(torrent_url)
                    self.notify("Torrent added successfully")
                    self.refresh_list()
                except Exception as e:
                    self.notify(f"Error adding torrent: {e}", severity="error")

        self.push_screen(AddTorrentModal(), handle_add)

    async def action_fetch(self) -> None:
        item_list = self.query_one("#item-list", ListView)
        if item_list.highlighted_child:
            node = item_list.highlighted_child.node
            target_id = getattr(node, 'id', getattr(node, 'folder_file_id', None))
            if not target_id:
                return

            try:
                if isinstance(node, File):
                    result = self.core.fetch_file(target_id)
                    self.notify(f"Link: {result.url}", timeout=10)
                    # We could copy to clipboard if possible, but let's just show it
                elif isinstance(node, Folder):
                    result = self.core.create_archive(target_id)
                    self.notify(f"Archive Link: {result.archive_url}", timeout=10)
                else:
                    self.notify("Cannot fetch link for this item type", severity="warning")
            except Exception as e:
                self.notify(f"Error fetching: {e}", severity="error")

    async def action_delete(self) -> None:
        item_list = self.query_one("#item-list", ListView)
        if item_list.highlighted_child:
            node = item_list.highlighted_child.node
            try:
                if isinstance(node, Folder):
                    self.core.delete_folder(node.id)
                elif isinstance(node, File):
                    self.core.delete_file(node.folder_file_id)
                elif isinstance(node, Torrent):
                    self.core.delete_torrent(node.id)
                
                self.notify(f"Deleted: {node.name}")
                self.refresh_list()
            except Exception as e:
                self.notify(f"Error deleting: {e}", severity="error")

def run_tui(core: SeedrClient):
    app = SeedrApp(core)
    app.run()
