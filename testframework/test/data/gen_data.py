from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create_data(n_data):
    n_data.version = 0x14000005
    n_data.user_version = 11
    n_data.user_version_2 = 11
    return n_data