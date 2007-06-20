import os, Blender

try:
    nifDataPath = Blender.sys.sep.join((os.getenv("ProgramFiles"), "Bethesda", "Oblivion", "Data", ""))
except TypeError:
    nifDataPath = ''

# This "module" holds all the fallback values for the script configuration. This
# makes sure the configuration will never be invalid
_NIF_IMPORT_PATH = "%sMeshes" % (nifDataPath)
# The 'r' before the string definition sets this as "raw". This means that escape
# sequences (those preceded by '\' won't be interpreted. Handy to set paths in
# Win32, and let's face it, almost all the script users will be Win32 users.
_NIF_EXPORT_PATH = "%sMeshes" % (nifDataPath)
# These next two are selected in the import and export screens, not in the config
_NIF_IMPORT_FILE = ""
_NIF_EXPORT_FILE = "export.nif"
_REALIGN_BONES = True
_IMPORT_ANIMATION = True
_IMPORT_SCALE_CORRECTION = 0.1
_EXPORT_SCALE_CORRECTION = 1.0 / _IMPORT_SCALE_CORRECTION
_BASE_TEXTURE_FOLDER = "%sTextures" % (nifDataPath)
_TEXTURE_SEARCH_PATH = [_BASE_TEXTURE_FOLDER]
_EXPORT_VERSION = '20.0.0.5'
_EXPORT_TEXTURE_PATH = "R"
# (R)elative to NIF,
# (F)ull,
# (N)one (strip folders),
# Relative to (B)ase texture folder
_EPSILON = 0.005 # used for checking equality with floats
_VERBOSE = True # enables debug output


# Not really implemented yet... might have to call a command line tool. Hence..
# _CONVERT_DDS = True
# _CONVERTER_COMMAND_LINE = ... using wildcards for filenames and such.
