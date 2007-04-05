import Blender
from Blender import Draw
from Blender import Registry

import Defaults as _DEF
reload(_DEF)

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()

# Configuration
_CONFIG = {
    "_NIF_IMPORT_PATH" : _DEF._NIF_IMPORT_PATH, \
    "_NIF_EXPORT_PATH" : _DEF._NIF_EXPORT_PATH, \
    "_TEXTURE_SEARCH_PATH" : _DEF._TEXTURE_SEARCH_PATH, \
    "_REALIGN_BONES" : _DEF._REALIGN_BONES, \
    "_IMPORT_SCALE_CORRECTION" : _DEF._IMPORT_SCALE_CORRECTION, \
    "_EXPORT_SCALE_CORRECTION" : _DEF._EXPORT_SCALE_CORRECTION, \
    "_BASE_TEXTURE_FOLDER" : _DEF._BASE_TEXTURE_FOLDER, \
    "_EXPORT_TEXTURE_PATH" : _DEF._EXPORT_TEXTURE_PATH, \
    "_CONVERT_DDS" : _DEF._CONVERT_DDS}
            

_CONFIG_NAME = "NIFSCRIPTS"

def __init__():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    global _CONFIG
    
    reload(_DEF)
    _GUI_ELEMENTS = {}
    _WINDOW_SIZE = Blender.Window.GetAreaSize()
    _CONFIG = {
        "_NIF_IMPORT_PATH"          : _DEF._NIF_IMPORT_PATH, \
        "_NIF_EXPORT_PATH"          : _DEF._NIF_EXPORT_PATH, \
        "_TEXTURE_SEARCH_PATH"      : _DEF._TEXTURE_SEARCH_PATH, \
        "_REALIGN_BONES"            : _DEF._REALIGN_BONES, \
        "_IMPORT_SCALE_CORRECTION"  : _DEF._IMPORT_SCALE_CORRECTION, \
        "_EXPORT_SCALE_CORRECTION"  : _DEF._EXPORT_SCALE_CORRECTION, \
        "_BASE_TEXTURE_FOLDER"      : _DEF._BASE_TEXTURE_FOLDER, \
        "_EXPORT_TEXTURE_PATH"      : _DEF._EXPORT_TEXTURE_PATH, \
        "_CONVERT_DDS"              : _DEF._CONVERT_DDS}
    clean()

def gui():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    WW = _WINDOW_SIZE[0]
    WH = _WINDOW_SIZE[1]
    #Draw.String(name, event, x, y, width, height, initial, length, tooltip=None) 
    #_GUI_ELEMENTS["_NIF_EXPORT_PATH"]       = Draw.String("", 150, 50, WH-75, 350, 20, String(_CONFIG["_NIF_EXPORT_PATH"]), 350, "import path")
    #_GUI_ELEMENTS["_TEXTURE_SEARCH_PATH"]   = Draw.String("", 160, 50, WH-100, 350, 20, String(_CONFIG["_TEXTURE_SEARCH_PATH"]), 350, "export path")
    _GUI_ELEMENTS["_NIF_EXPORT_PATH"]       = Draw.String("", 150, 50, WH-75, 350, 20, "1", 350, "import path")
    _GUI_ELEMENTS["_TEXTURE_SEARCH_PATH"]   = Draw.String("", 160, 50, WH-100, 350, 20, "2", 350, "export path")
    _GUI_ELEMENTS["_REALIGN_BONES"]     = Draw.Toggle("Realign Bones", 170, 50, WH-125, 55, 20, _CONFIG["_REALIGN_BONES"],"Tries to detect optimum bone alignment")
    _GUI_ELEMENTS["CANCEL"]             = Draw.PushButton('cancel',      130, 50, WH-225, 100, 20)
    _GUI_ELEMENTS["OK"]                 = Draw.PushButton('ok',      140, 50, WH-250, 100, 20)
    Draw.Redraw(1)

def buttonEvent(idEvent):
    """
    Event handler for buttons
    """
    print  "buttonEvent(idEvent=%i)"%(idEvent)
    if idEvent == 140:
        close()
    elif  idEvent == 130:
        exit()
    else:
        Draw.Redraw(1)
        
def event(arg1, arg2):
    """
    Event handler for GUI elements
    """
    #print  "event(%i,%i)"%(arg1,arg2)
    None

def open():
    """
    Opens the config GUI
    """
    clean()
    Draw.Register(gui, event, buttonEvent)
    
def exit():
    """
    Closes the config GUI without saving
    """
    Draw.Redraw(1)
    Draw.Exit()
    import Main
    reload(Main)
    Main.open()

def close():
    """
    Saves and closes the config GUI
    """
    save()
    exit()


def save():
    """
    Saves the current configuration
    """
    Registry.SetKey(_CONFIG_NAME, _CONFIG, True)
    
def clean():
    """
    Checks saved configuration for incompatible values
    """
    global _CONFIG
    try:
        StoredConf = Registry.GetKey(_CONFIG_NAME, True)
        CleanedConf = {}
        for key in _CONFIG.keys():
            print "----", key, _CONFIG[key], "\n"
            try:
                CleanedConf[key] = StoredConf[key]
            except:
                CleanedConf[key] = _CONFIG[key]
        Registry.SetKey(_CONFIG_NAME, CleanedConf, True)
    except KeyError:
        Registry.SetKey(_CONFIG_NAME, _CONFIG, True)
