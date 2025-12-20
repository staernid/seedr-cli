import os
import re
from seedrcc import Token

TOKEN_FILE = os.path.expanduser("~/.seedr_token.txt")

def save_token(token: Token) -> None:
    """Save token to TOKEN_FILE in JSON format."""
    with open(TOKEN_FILE, "w") as f:
        f.write(token.to_json())

def load_token() -> Token | None:
    """Load token from TOKEN_FILE if it exists."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return Token.from_json(f.read())
    return None

def sanitize_filename(name: str) -> str:
    """Sanitize filename for saving."""
    # Keep alphanumerics, spaces, dots, hyphens, underscores
    clean = re.sub(r'[^\w\s.-]', '', name)
    # Replace multiple spaces with single
    clean = re.sub(r'\s+', ' ', clean)
    # Strip leading/trailing whitespace and replace spaces with underscores
    return clean.strip().replace(' ', '_')

def format_size(size: int) -> str:
    """Convert bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"