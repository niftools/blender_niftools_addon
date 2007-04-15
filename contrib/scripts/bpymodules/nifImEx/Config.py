import Blender, os, sys
import Read, Write, Defaults
from Blender import Draw, BGL, Registry

if sys.platform in ('linux-i386','linux2'):
    os.system("clear")
elif sys.platform in ('win32','dos','ms-dos'):
    os.system("cls")

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()

# Configuration
_CONFIG = {}
_CONFIG_NAME = "nifscripts"

# Back target for exit
_BACK_TARGET = None

def __init__():
    global _GUI_ELEMENTS, _WINDOW_SIZE, _CONFIG
    reload(Defaults)
    _GUI_ELEMENTS = {}
    _WINDOW_SIZE = Blender.Window.GetAreaSize()
    _CONFIG = {}
    clean()

def gui():
    global _GUI_ELEMENTS, _WINDOW_SIZE, _CONFIG
    # These are to save me some typing
    #W = _WINDOW_SIZE[0]
    H = _WINDOW_SIZE[1]
    E = {}
    # IMPORTANT: Don't start dictionary keys with an underscore, the Registry module doesn't like that, apparently
    # Draw.String(name, event, x, y, width, height, initial, length, tooltip=None) 
    E["NIF_IMPORT_PATH"]        = Draw.String("",          150,  50, H- 75, 350, 20, _CONFIG["NIF_IMPORT_PATH"],        350, "export path")
    E["BROWSE_IMPORT_PATH"]     = Draw.PushButton('browse',155, 410, H- 75, 100, 20)
    E["NIF_EXPORT_PATH"]        = Draw.String("",          160,  50, H-100, 350, 20, _CONFIG["NIF_EXPORT_PATH"],        350, "import path")
    E["BROWSE_EXPORT_PATH"]     = Draw.PushButton('browse',165, 410, H-100, 100, 20)
    E["BASE_TEXTURE_FOLDER"]    = Draw.String("",          170,  50, H-125, 350, 20, _CONFIG["BASE_TEXTURE_FOLDER"],    350, "import path")
    E["BROWSE_TEXBASE"]         = Draw.PushButton('browse',175, 410, H-125, 100, 20)
    E["TEXTURE_SEARCH_PATH"]    = Draw.String("",          180,  50, H-150, 350, 20, _CONFIG["TEXTURE_SEARCH_PATH"], 350, "texture search path")
    E["TEXPATH_ITEM"]           = Draw.String("",          190,  50, H-170, 350, 20, "" , 290)
    E["TEXPATH_PREV"]           = Draw.PushButton('<',     200, 340, H-170,  20, 20)
    E["TEXPATH_NEXT"]           = Draw.PushButton('>',     210, 360, H-170,  20, 20)
    E["TEXPATH_REMOVE"]         = Draw.PushButton('X',     230, 380, H-170,  20, 20)
    E["BROWSE_TEXPATH"]         = Draw.PushButton('browse',235, 410, H-170, 100, 20)
    E["REALIGN_BONES"]          = Draw.Toggle(" ",         240,  50, H-200,  20, 20, _CONFIG["REALIGN_BONES"])
    # To draw text on the screen I have to position its start point first
    BGL.glRasterPos2i( 75, H-195)
    Draw.Text("try to realign bones")
    
    E["CANCEL"]                 = Draw.PushButton('cancel',250,  50, H-225, 100, 20)
    E["OK"]                     = Draw.PushButton('ok',    260,  50, H-250, 100, 20)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(evt):
    """
    Event handler for buttons
    """
    if evt == 260:
        save()
        exit()
    elif  evt == 250:
        exit()
    elif  evt == 240:
        _CONFIG["REALIGN_BONES"] = not _CONFIG["REALIGN_BONES"]
    else:
        None
    Draw.Redraw(1)

def event(evt, val):
    """
    Event handler for GUI elements
    """
    #print  "event(%i,%i)"%(arg1,arg2)
    if evt == Draw.ESCKEY:
        exit()

def open(back_target=None):
    """
    Opens the config GUI
    """
    # defines what script called the config screen
    global _BACK_TARGET
    _BACK_TARGET = back_target
    clean()
    Draw.Register(gui, event, buttonEvent)
    
def exit():
    """
    Closes the config GUI
    """
    global _BACK_TARGET
    Draw.Exit()
    if _BACK_TARGET == "Import":
        reload(Read)
        Read.open()
    elif _BACK_TARGET == "Export":
        reload(Write)
        Write.open()
    elif _BACK_TARGET == "Main":
        reload(Main)
        Main.open()


def save():
    """
    Saves the current configuration
    """
    global _CONFIG, _CONFIG_NAME
    print "datadir", Blender.Get('datadir'), "\n\n"
    print "--",_CONFIG_NAME, _CONFIG, "\n\n"
    Registry.SetKey(_CONFIG_NAME, _CONFIG, True)

def load():
    """
    Loads the stored configuration
    """
    global _CONFIG
    #_CONFIG = Blender.Registry.GetKey(_CONFIG_NAME, True)
    clean()

def clean():
    """
    Checks saved configuration for incompatible values
    """
    global _CONFIG, _CONFIG_NAME
    reload(Defaults)
    _CONFIG = {
        'NIF_IMPORT_PATH'          : Defaults._NIF_IMPORT_PATH, \
        'NIF_EXPORT_PATH'          : Defaults._NIF_EXPORT_PATH, \
        'NIF_IMPORT_FILE'          : Defaults._NIF_IMPORT_FILE, \
        'NIF_EXPORT_FILE'          : Defaults._NIF_EXPORT_FILE, \
        'TEXTURE_SEARCH_PATH'      : Defaults._TEXTURE_SEARCH_PATH, \
        'REALIGN_BONES'            : Defaults._REALIGN_BONES, \
        'IMPORT_SCALE_CORRECTION'  : Defaults._IMPORT_SCALE_CORRECTION, \
        'EXPORT_SCALE_CORRECTION'  : Defaults._EXPORT_SCALE_CORRECTION, \
        'BASE_TEXTURE_FOLDER'      : Defaults._BASE_TEXTURE_FOLDER, \
        'EXPORT_TEXTURE_PATH'      : Defaults._EXPORT_TEXTURE_PATH, \
        'NIF_VERSIONS'             : Defaults._NIF_VERSIONS, \
        'EPSILON'                  : Defaults._EPSILON, \
        'VERBOSE'                  : Defaults._VERBOSE}
    oldConfig = Blender.Registry.GetKey(_CONFIG_NAME, True)
    #print "oldConfig", oldConfig, "\n\n"
    newConfig = {}
    for key in _CONFIG.keys():
        try:
            newConfig[key] = oldConfig[key]
        except:
            newConfig[key] = _CONFIG[key]
    #print "newConfig", newConfig, "\n\n"
    _CONFIG = newConfig
    Blender.Registry.SetKey(_CONFIG_NAME, _CONFIG, True)

