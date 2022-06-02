""" Nif Utilities, stores common code that is used across the code base"""


def safe_decode(b: bytes, encodings=('ascii', 'utf8', 'latin1', 'shift-jis')) -> str:
    for encoding in encodings:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError:
            pass
    return b.decode("ascii", errors="surrogateescape")
