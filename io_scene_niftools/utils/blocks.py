""" Nif Utilities, stores common code that is used across the code base"""

def safe_decode(b: bytes) -> str:
    try:
        return b.decode()
    except UnicodeDecodeError:
        return b.decode("shift-jis", errors="surrogateescape")