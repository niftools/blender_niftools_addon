import os
# This "module" holds all the fallback values for the script configuration. This
# makes sure the configuration will never be invalid
_NIF_IMPORT_PATH = r"%s\Bethesda\Oblivion\Data\Meshes" % (os.getenv("ProgramFiles"))
# The 'r' before the string definition sets this as "raw". This means that escape
# sequences (those preceded by '\' won't be interpreted. Handy to set paths in
# Win32, and let's face it, almost all the script users will be Win32 users.
_NIF_EXPORT_PATH = r"%s\Bethesda\Oblivion\Data\Meshes" % (os.getenv("ProgramFiles"))
# These next two are selected in the import and export screens, not in the config
_NIF_IMPORT_FILE = ""
_NIF_EXPORT_FILE = "export.nif"
_REALIGN_BONES = True
_IMPORT_SCALE_CORRECTION = 0.1
_EXPORT_SCALE_CORRECTION = 1.0 / _IMPORT_SCALE_CORRECTION
_BASE_TEXTURE_FOLDER = r"%s\Bethesda\Oblivion\Data\Textures" % (os.getenv("ProgramFiles"))
_TEXTURE_SEARCH_PATH = []
_TEXTURE_SEARCH_PATH.append(_BASE_TEXTURE_FOLDER)
_EXPORT_VERSION = '20.0.0.5'
_EXPORT_TEXTURE_PATH = "R"
# (R)elative to NIF,
# (F)ull,
# (N)one (strip folders),
# Relative to (B)ase texture folder
_NIF_VERSIONS = { \
    '4.0.0.2' : 0x04000002,\
    '4.1.0.12': 0x0401000C,\
    '4.2.0.2' : 0x04020002,\
    '4.2.1.0' : 0x04020100,\
    '4.2.2.0' : 0x04020200,\
    '10.0.1.0': 0x0A000100,\
    '10.1.0.0': 0x0A010000,\
    '10.2.0.0': 0x0A020000,\
    '20.0.0.4': 0x14000004}
_EPSILON = 0.005 # used for checking equality with floats
_VERBOSE = True # enables debug output


_CONVERT_DDS = True
# Not really implemented yet... might have to call a command line tool. Hence..
# _CONVERTER_COMMAND_LINE = ... using wildcards for filenames and such.
