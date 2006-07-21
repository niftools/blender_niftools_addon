import Blender
from Defaults import *
from Blender import BGL
from Blender import Draw
from Blender import Registry

# Configuration
global CONFIG
CONFIG = {
    "NIF_IMPORT_PATH" : NIF_IMPORT_PATH, \
    "NIF_EXPORT_PATH" : NIF_EXPORT_PATH, \
    "TEXTURE_SEARCH_PATH" : TEXTURE_SEARCH_PATH, \
    "REALIGN_BONES" : REALIGN_BONES, \
    "IMPORT_SCALE_CORRECTION" : IMPORT_SCALE_CORRECTION, \
    "EXPORT_SCALE_CORRECTION" : EXPORT_SCALE_CORRECTION, \
    "BASE_TEXTURE_FOLDER" : BASE_TEXTURE_FOLDER, \
    "EXPORT_TEXTURE_PATH" : EXPORT_TEXTURE_PATH, \
    "CONVERT_DDS" : CONVERT_DDS} \
            
# All UI elements are kept in this dictionary to make sure they never go out of scope
global ELEMENTS
ELEMENTS = {}

def DrawGui():
    global ELEMENTS
    global CONFIG
    #Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)
    ELEMENTS["NIF_EXPORT_PATH"] = Draw.String('', 1, 70, 100, 350, 20, CONFIG["NIF_EXPORT_PATH"], 350)
    ELEMENTS["TEXTURE_SEARCH_PATH"] = Draw.String('', 2, 70, 75, 350, 20, CONFIG["TEXTURE_SEARCH_PATH"], 350)
    ELEMENTS["CLOSE"] = Draw.PushButton('close', 100, 70, 50, 100, 20)
    print "ok so far"

#def Event(idEvent, valEvent):
#    print idEvent, valEvent
#    Draw.Redraw(1)

def ButtonEvent(idEvent):
    print idEvent
    if idEvent == 100:
        Close()
    else:
        Draw.Redraw(1)

def Open():
    """
    Opens the configuration GUI
    """
    #Draw.Register(gui, event, buttonEvent)
    Cleanup()
    Draw.Register(DrawGui, None, ButtonEvent)
    

def Close():
    """
    Closes the configuration GUI
    """
    Draw.Redraw(1)
    Draw.Exit()

def Load():
    """
    Loads the current configuration
    """
    print "ok so far"

def Save():
    """
    Saves the current configuration
    """
    print "ok so far"
    
def Prompt():
    """
    Prompts user to save settings
    """
    print "ok so far"

def Validate():
    """
    Checks user imput for incongruous values
    """
    print "ok so far"
    
def Cleanup():
    """
    Checks saved configuration for incongruous values
    """
    global CONFIG
    obsolete = []
    KeyName = "NIF_TOOLKIT_CONFIG"
    try:
        StoredConf = Registry.GetKey(KeyName, True)
        CleanedConf = {}
        for key in CONFIG.keys():
            print key
            try:
                CleanedConf[key] = StoredConf[key]
            except:
                CleanedConf[key] = CONFIG[key]
        Registry.SetKey(KeyName, CleanedConf, True)
    except KeyError:
        Registry.SetKey(KeyName, CONFIG, True)
    
            
    print "ok so far"
