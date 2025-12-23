# SeedrCC TUI

A modern, unix-like CLI and TUI for managing your Seedr.cc account.

## Installation

To install `seedrcc-tui` globally so you can run it from anywhere:

```bash
uv tool install .
```

If you are developing and want changes to reflect immediately:

```bash
uv tool install --editable .
```

## Usage

Once installed, you can use the command directly:

### List Contents
Show your files and folders in a tree view.
```bash
seedrcc-tui list
```

### Fetch a File
Get the download URL for a file by its ID.
```bash
seedrcc-tui fetch <FILE_ID>
```

### Delete an Item
Delete a file, folder, or torrent.
```bash
seedrcc-tui delete <type: file|folder|torrent> <ID>
```

### Add a Torrent
```bash
seedrcc-tui add "magnet:..."
```

### Help
```bash
seedrcc-tui help
```
