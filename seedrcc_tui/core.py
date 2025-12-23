from seedrcc import Seedr
from seedrcc.models import Folder, File, Torrent
from .utils import load_token, save_token, format_size, sanitize_filename

class SeedrClient:
    def __init__(self):
        self._client = None

    def get_client(self, interactive=True):
        """Authenticate and return a Seedr client."""
        if self._client:
            return self._client
        
        token = load_token()
        if token:
            self._client = Seedr(token=token, on_token_refresh=save_token)
            return self._client
        
        if not interactive:
            raise Exception("Authentication required. Please run in interactive mode first.")

        # Device flow authentication
        codes = Seedr.get_device_code()
        print(f"[*] Authentication required.")
        print(f"[*] Please go to: {codes.verification_url}")
        print(f"[*] Enter code: {codes.user_code}")
        input("[?] Press Enter after authorizing...")
        
        client = Seedr.from_device_code(codes.device_code, on_token_refresh=save_token)
        save_token(client.token)
        self._client = client
        return client

    def list_contents(self, folder_id=None):
        client = self.get_client()
        return client.list_contents(folder_id)

    def get_memory_bandwidth(self):
        client = self.get_client()
        return client.get_memory_bandwidth()

    def fetch_file(self, file_id):
        client = self.get_client()
        return client.fetch_file(file_id)

    def create_archive(self, folder_id):
        client = self.get_client()
        return client.create_archive(folder_id)

    def delete_folder(self, folder_id):
        client = self.get_client()
        return client.delete_folder(folder_id)

    def delete_file(self, file_id):
        client = self.get_client()
        return client.delete_file(file_id)

    def delete_torrent(self, torrent_id):
        client = self.get_client()
        return client.delete_torrent(torrent_id)

    def add_torrent(self, torrent):
        client = self.get_client()
        return client.add_torrent(torrent)

    def find_item_by_id(self, target_id):
        """Try to find an item by ID in the root contents to identify its type and name."""
        try:
            contents = self.list_contents()
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
