import Blender
from Blender import Draw
import Defaults, Config

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()

def __init__():
    _GUI_ELEMENTS = {}
    _WINDOW_SIZE = Blender.Window.GetAreaSize()

def gui():
    global _GUI_ELEMENTS
    global _WINDOW_SIZE
    WW = _WINDOW_SIZE[0]
    WH = _WINDOW_SIZE[1]
    #Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)
    _GUI_ELEMENTS["CONFIG"]     = Draw.PushButton('configure',  100, 70, WH-75, 100, 20)
    #_GUI_ELEMENTS["TOOLS"]      = Draw.PushButton('tools',      110, 70, WH-100, 100, 20)
    _GUI_ELEMENTS["IMPORT"]     = Draw.PushButton('import',     120, 70, WH-100, 100, 20)
    _GUI_ELEMENTS["EXPORT"]     = Draw.PushButton('export',     130, 70, WH-125, 100, 20)
    _GUI_ELEMENTS["CLOSE"]      = Draw.PushButton('close',      140, 70, WH-250, 100, 20)
    Draw.Redraw(1)


def buttonEvent(idEvent):
    """
    Event handler for buttons
    """
    print  "buttonEvent(idEvent=%i)"%(idEvent)
    if idEvent == 140:
        close()
    elif idEvent == 100:
        close()
        reload(Config)
        Config.open()
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
    
    