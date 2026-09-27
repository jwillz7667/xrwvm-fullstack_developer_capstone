"""Create local development secrets without printing or committing them."""
import os
import secrets
from pathlib import Path
path = Path(__file__).resolve().parent.parent / ".local-env"
if path.exists():
    print("Using existing .local-env")
else:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write("DJANGO_SECRET_KEY=" + secrets.token_urlsafe(64) + "\nSERVICE_KEY=" + secrets.token_urlsafe(48) + "\n")
    print("Created private .local-env")
