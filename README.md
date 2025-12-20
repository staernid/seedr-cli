# Seedr CLI

A modern, unix-like CLI for managing your Seedr.cc account.

## Installation

Ensure you have `uv` installed, then:

```bash
uv sync
```

## Usage

### List Contents
Show your files and folders in a tree view.
```bash
uv run python main.py list
```

### Fetch a File
Get the download URL for a file by its ID.
```bash
uv run python main.py fetch <FILE_ID>
```

### Delete an Item
Delete a file, folder, or torrent.
```bash
uv run python main.py delete <type: file|folder|torrent> <ID>
```

### Add a Torrent (Placeholder)
```bash
uv run python main.py add "magnet:..."
```

### Help
```bash
uv run python main.py help
```
