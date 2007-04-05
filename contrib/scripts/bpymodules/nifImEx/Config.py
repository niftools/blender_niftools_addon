import Blender
from Blender import Draw, BGL, Registry

import Defaults as _DEF

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()

# Configuration
_CONFIG = {}
_CONFIG_NAME = "NIFSCRIPTS"

def __init__():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    global _CONFIG
    _GUI_ELEMENTS = {}
    _WINDOW_SIZE = Blender.Window.GetAreaSize()
    _CONFIG = {}
    clean()

def gui():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    global _CONFIG
    # These are to save me some typing
    #W = _WINDOW_SIZE[0]
    H = _WINDOW_SIZE[1]
    E = {}
    # Draw.String(name, event, x, y, width, height, initial, length, tooltip=None) 
    E["_NIF_IMPORT_PATH"]       = Draw.String("",          150,  50, H- 75, 350, 20, _CONFIG["_NIF_IMPORT_PATH"],        350, "export path")
    E["_BROWSE_IMPORT_PATH"]    = Draw.PushButton('browse',155, 410, H- 75, 100, 20)
    E["_NIF_EXPORT_PATH"]       = Draw.String("",          160,  50, H-100, 350, 20, _CONFIG["_NIF_EXPORT_PATH"],        350, "import path")
    E["_BROWSE_EXPORT_PATH"]    = Draw.PushButton('browse',165, 410, H-100, 100, 20)
    E["_BASE_TEXTURE_FOLDER"]   = Draw.String("",          170,  50, H-125, 350, 20, _CONFIG["_BASE_TEXTURE_FOLDER"],    350, "import path")
    E["_BROWSE_TEXBASE"]        = Draw.PushButton('browse',175, 410, H-125, 100, 20)
    E["_TEXTURE_SEARCH_PATH"]   = Draw.String("",          180,  50, H-150, 350, 20, _CONFIG["_TEXTURE_SEARCH_PATH"][0], 350, "texture search path")
    E["_TEXPATH_ITEM"]          = Draw.String("",          190,  50, H-170, 350, 20, "" , 290)
    E["_TEXPATH_PREV"]          = Draw.PushButton('<',     200, 340, H-170,  20, 20)
    E["_TEXPATH_NEXT"]          = Draw.PushButton('>',     210, 360, H-170,  20, 20)
    E["_TEXPATH_REMOVE"]        = Draw.PushButton('X',     230, 380, H-170,  20, 20)
    E["_BROWSE_TEXPATH"]        = Draw.PushButton('browse',235, 410, H-170, 100, 20)
    E["_REALIGN_BONES"]         = Draw.Toggle(" ",         240,  50, H-200,  20, 20, _CONFIG["_REALIGN_BONES"])
    # To draw text on the screen I have to position its start point first
    BGL.glRasterPos2i( 75, H-195)
    Draw.Text("try to realign bones")
    
    E["CANCEL"]                 = Draw.PushButton('cancel',250,  50, H-225, 100, 20)
    E["OK"]                     = Draw.PushButton('ok',    260,  50, H-250, 100, 20)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(idEvent):
    """
    Event handler for buttons
    """
    print  "buttonEvent(idEvent=%i)"%(idEvent)
    if idEvent == 260:
        save()
        exit()
    elif  idEvent == 250:
        exit()
    elif  idEvent == 240:
        _CONFIG["_REALIGN_BONES"] = (not _CONFIG["_REALIGN_BONES"])
    else:
        None
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
    Closes the config GUI
    """
    Draw.Exit()
    reload(Main)
    Main.open()

def save():
    """
    Saves the current configuration
    """
    global _CONFIG
    global _CONFIG_NAME
    #for key in _CONFIG.keys():
    #    print key, _CONFIG[key], "\n"
    Registry.SetKey(_CONFIG_NAME, _CONFIG, True)
    
def clean():
    """
    Checks saved configuration for incompatible values
    """
    # There's still some trouble with this.
    # For some reason the default values seem to drive even though the config has been properly saved.
    global _CONFIG
    global _CONFIG_NAME
    reload(_DEF)
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
    storedConf = Registry.GetKey(_CONFIG_NAME, True)
    cleanConf = {}
    for key in _CONFIG.keys():
        try:
            cleanConf[key] = storedConf[key]
            #print  "-", key, _CONFIG[key], cleanConf[key], "/n"
        except:
            cleanConf[key] = _CONFIG[key]
            #print  "!", key, _CONFIG[key], storedConf[key], "/n"
    print cleanConf
    Registry.SetKey(_CONFIG_NAME, cleanConf, True)