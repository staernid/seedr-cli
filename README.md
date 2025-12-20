# Seedr CLI

A modern, unix-like CLI for managing your Seedr.cc account.

## Installation

To install `seedr-cli` globally so you can run it from anywhere:

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
seedr-cli list
```

### Fetch a File
Get the download URL for a file by its ID.
```bash
seedr-cli fetch <FILE_ID>
```

### Delete an Item
Delete a file, folder, or torrent.
```bash
seedr-cli delete <type: file|folder|torrent> <ID>
```

### Add a Torrent
```bash
seedr-cli add "magnet:..."
```

### Help
```bash
seedr-cli help
```
