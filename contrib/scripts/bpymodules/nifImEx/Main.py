import Blender
from Blender import Draw
import Defaults, Config, Read

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()

def __init__():
    _GUI_ELEMENTS = {}
    _WINDOW_SIZE = Blender.Window.GetAreaSize()

def gui():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    #W = _WINDOW_SIZE[0]
    H = _WINDOW_SIZE[1]
    #Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)
    _GUI_ELEMENTS["CONFIG"]     = Draw.PushButton('configure',  100, 50, H-75, 100, 20)
    #_GUI_ELEMENTS["TOOLS"]      = Draw.PushButton('tools',      110, 50, WH-100, 100, 20)
    _GUI_ELEMENTS["IMPORT"]     = Draw.PushButton('import',     120, 50, H-100, 100, 20)
    _GUI_ELEMENTS["EXPORT"]     = Draw.PushButton('export',     130, 50, H-125, 100, 20)
    _GUI_ELEMENTS["CLOSE"]      = Draw.PushButton('close',      140, 50, H-250, 100, 20)
    Draw.Redraw(1)


def buttonEvent(evt):
    """
    Event handler for buttons
    """
    if evt == 140:
        close()
    elif evt == 100:
        close()
        reload(Config)
        Config.open()
    elif evt == 120:
        close()
        reload(Read)
        Read.open()
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
    Opens the main GUI
    """
    Draw.Register(gui, event, buttonEvent)
    

def close():
    """
    Closes the main GUI
    """
    Draw.Redraw(1)
    Draw.Exit()
    
    