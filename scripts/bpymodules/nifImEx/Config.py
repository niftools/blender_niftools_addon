__version__ = "2.1.5"
__requiredpyffiversion__ = "0.4.4"

import Blender

import sys, os

import Read, Write, Defaults
from Blender import Draw, BGL, Registry
from math import log
from copy import deepcopy
from PyFFI.NIF import NifFormat

# check PyFFI version
from PyFFI import __version__ as PyFFIVersion
if PyFFIVersion < __requiredpyffiversion__:
    err = """--------------------------
ERROR\nThis script requires Python File Format Interface %s or higher.
It seems that you have an older version installed (%s).
Get a newer version at http://pyffi.sourceforge.net/
--------------------------"""%(__requiredpyffiversion__, PyFFIVersion)
    print err
    Blender.Draw.PupMenu("ERROR%t|PyFFI outdated, check console for details")
    raise ImportError

# clears the console window
if sys.platform in ('linux-i386','linux2'):
    os.system("clear")
elif sys.platform in ('win32','dos','ms-dos'):
    os.system("cls")

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}

# To avoid confusion with event ID handling I register them all in a list
_GUI_EVENTS = []

# Configuration
_CONFIG = {}
# Old configuration for cancel button
_CONFIG_NAME = "nifscripts"

# Back target for exit
_BACK_TARGET = None

# Texture search path item index
_IDX_TEXPATH = 0

def __init__():
    global _GUI_ELEMENTS, _WINDOW_SIZE, _CONFIG
    _GUI_ELEMENTS.clear()
    _CONFIG.clear()
    load()

def setImportPath(nifImportPath):
    global _CONFIG
    nifImportPath = Blender.sys.dirname(nifImportPath)
    if nifImportPath == '' or not Blender.sys.exists(nifImportPath):
        Draw.PupMenu('No path selected or path does not exist%t|Ok')
    else:
        _CONFIG["NIF_IMPORT_PATH"] = nifImportPath

def setExportPath(nifExportPath):
    global _CONFIG
    nifExportPath = Blender.sys.dirname(nifExportPath)
    if nifExportPath == '' or not Blender.sys.exists(nifExportPath):
        Draw.PupMenu('No path selected or path does not exist%t|Ok')
    else:
        _CONFIG["NIF_EXPORT_PATH"] = nifExportPath

def setTextureBase(textureBaseFolder):
    global _CONFIG
    textureBaseFolder = Blender.sys.dirname(textureBaseFolder)
    if textureBaseFolder == '' or not Blender.sys.exists(textureBaseFolder):
        Draw.PupMenu('No path selected or path does not exist%t|Ok')
    else:
        _CONFIG["BASE_TEXTURE_FOLDER"] = textureBaseFolder
        
def addTexturePath(nifTexturePath):
    global _CONFIG, _IDX_TEXPATH
    nifTexturePath = Blender.sys.dirname(nifTexturePath)
    if nifTexturePath == '' or not Blender.sys.exists(nifTexturePath):
        Draw.PupMenu('No path selected or path does not exist%t|Ok')
    else:
        if nifTexturePath not in _CONFIG["TEXTURE_SEARCH_PATH"]:
            _CONFIG["TEXTURE_SEARCH_PATH"].append(nifTexturePath)
        _IDX_TEXPATH = _CONFIG["TEXTURE_SEARCH_PATH"].index(nifTexturePath)

def updateScale(evt, val):
    _CONFIG["EXPORT_SCALE_CORRECTION"] = val
    _CONFIG["IMPORT_SCALE_CORRECTION"] = 1.0 / _CONFIG["EXPORT_SCALE_CORRECTION"]

def updateBonesPerPartition(evt, val):
    _CONFIG["EXPORT_BONESPERPARTITION"] = val

def addEvent(evName = "NO_NAME"):
    global _GUI_EVENTS
    eventId = len(_GUI_EVENTS)
    if eventId >= 16383:
        raise "Maximum number of events exceeded"
        return None
    _GUI_EVENTS.append(evName)
    return eventId


def guiText(str = "", xpos = 0, ypos = 0):
    # To draw text on the screen I have to position its start point first
    BGL.glRasterPos2i( xpos, ypos)
    Draw.Text(str)


def drawGUI():
    global _GUI_ELEMENTS, _CONFIG, _IDX_TEXPATH, _GUI_EVENTS
    del _GUI_EVENTS[:]

    # These are to save me some typing
    #W = _WINDOW_SIZE[0]
    H = Blender.Window.GetAreaSize()[1]
    # dictionary of GUI elements
    E = {}
    
    texpathString = ""
    texpathItemString = ""
    if len(_CONFIG["TEXTURE_SEARCH_PATH"]) > 0:
        texpathString = ";".join(_CONFIG["TEXTURE_SEARCH_PATH"])
        if not _IDX_TEXPATH in xrange(len(_CONFIG["TEXTURE_SEARCH_PATH"])):
            _IDX_TEXPATH = 0
        texpathItemString = _CONFIG["TEXTURE_SEARCH_PATH"][_IDX_TEXPATH]
    
    
    # IMPORTANT: Don't start dictionary keys with an underscore, the Registry module doesn't like that, apparently
    # Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)

    H -= 20

    # common options
    guiText("Scale correction", 50, H)
    E["SCALE_CORRECTION"] = Draw.Slider("", addEvent("SCALE_CORRECTION"), 50, H-25, 390, 20, _CONFIG["EXPORT_SCALE_CORRECTION"], 0.01, 100, 0, "scale", updateScale)

    H -= 60

    # import-only options
    if _BACK_TARGET == "Import":
        H += 125 # TODO shift values below...
        
        #E["NIF_IMPORT_PATH"]        = Draw.String("",       addEvent("NIF_IMPORT_PATH"),     50, H- 75, 390, 20, _CONFIG["NIF_IMPORT_PATH"],        390, "import path")
        #E["BROWSE_IMPORT_PATH"]     = Draw.PushButton('...',addEvent("BROWSE_IMPORT_PATH"), 440, H- 75,  30, 20)
        #E["BASE_TEXTURE_FOLDER"]    = Draw.String("",       addEvent("BASE_TEXTURE_FOLDER"), 50, H-125, 390, 20, _CONFIG["BASE_TEXTURE_FOLDER"],    390, "base texture folder")
        #E["BROWSE_TEXBASE"]         = Draw.PushButton('...',addEvent("BROWSE_TEXBASE"),     440, H-125,  30, 20)
        guiText("texture search path", 75, H-125)
        E["TEXTURE_SEARCH_PATH"]    = Draw.String("",       addEvent("TEXTURE_SEARCH_PATH"), 50, H-150, 390, 20, texpathString,                     390, "texture search path")
        E["BROWSE_TEXPATH"]         = Draw.PushButton('...',addEvent("BROWSE_TEXPATH"),     440, H-150,  30, 20)
        E["TEXPATH_ITEM"]           = Draw.String("",       addEvent("TEXPATH_ITEM"),        50, H-170, 360, 20, texpathItemString,                 290)
        E["TEXPATH_PREV"]           = Draw.PushButton('<',  addEvent("TEXPATH_PREV"),       410, H-170,  20, 20)
        E["TEXPATH_NEXT"]           = Draw.PushButton('>',  addEvent("TEXPATH_NEXT"),       430, H-170,  20, 20)
        E["TEXPATH_REMOVE"]         = Draw.PushButton('X',  addEvent("TEXPATH_REMOVE"),     450, H-170,  20, 20)
        E["REALIGN_BONES"]          = Draw.Toggle(" ",      addEvent("REALIGN_BONES"),       50, H-200,  20, 20, _CONFIG["REALIGN_BONES"])
        guiText("try to realign bones", 75, H-195)
        E["IMPORT_ANIMATION"]       = Draw.Toggle(" ",      addEvent("IMPORT_ANIMATION"),    50, H-220,  20, 20, _CONFIG["IMPORT_ANIMATION"])
        guiText("import animation (if present)", 75, H-215)
        E["IMPORT_SKELETON"]       = Draw.Toggle("Import Skeleton Only + Parent Selected", addEvent("IMPORT_SKELETON"), 50, H-250, 390, 20, _CONFIG["IMPORT_SKELETON"])
        E["IMPORT_SENDBONESTOBINDPOS"] = Draw.Toggle("Send Bones To Bind Position", addEvent("IMPORT_SENDBONESTOBINDPOS"), 50, H-270, 390, 20, _CONFIG["IMPORT_SENDBONESTOBINDPOS"])
        E["IMPORT_APPLYSKINDEFORM"] = Draw.Toggle("Apply Skin Deformation", addEvent("IMPORT_APPLYSKINDEFORM"), 50, H-290, 390, 20, _CONFIG["IMPORT_APPLYSKINDEFORM"])

        H -= 335
        E["BACK"]                     = Draw.PushButton('back',    addEvent("BACK"),  50, H-25, 100, 20)

    # export-only options
    if _BACK_TARGET == "Export":
        E["EXPORT_ANIMATION_0"] = Draw.Toggle("Export Geometry + Animation (.nif)", addEvent("EXPORT_ANIMATION_0"), 50, H, 390, 20, _CONFIG["EXPORT_ANIMATION"] == 0)
        E["EXPORT_ANIMATION_1"] = Draw.Toggle("Export Geometry Only (.nif)",        addEvent("EXPORT_ANIMATION_1"), 50, H-20, 390, 20, _CONFIG["EXPORT_ANIMATION"] == 1)
        E["EXPORT_ANIMATION_2"] = Draw.Toggle("Export Animation Only (.kf) - MORROWIND ONLY FOR NOW",        addEvent("EXPORT_ANIMATION_2"), 50, H-40, 390, 20, _CONFIG["EXPORT_ANIMATION"] == 2)
        H -= 70

        E["EXPORT_FLATTENSKIN"] = Draw.Toggle("Flatten Skin", addEvent("EXPORT_FLATTENSKIN"), 50, H, 390, 20, _CONFIG["EXPORT_FLATTENSKIN"])
        H -= 30

        E["EXPORT_STRIPIFY"] = Draw.Toggle("Stripify Geometries", addEvent("EXPORT_STRIPIFY"), 50, H, 390, 20, _CONFIG["EXPORT_STRIPIFY"])
        E["EXPORT_STITCHSTRIPS"] = Draw.Toggle("Stitch Strips", addEvent("EXPORT_STITCHSTRIPS"), 50, H-20, 390, 20, _CONFIG["EXPORT_STITCHSTRIPS"])
        H -= 50

        E["EXPORT_SKINPARTITION"] = Draw.Toggle("Export Skin Partition", addEvent("EXPORT_SKINPARTITION"), 50, H, 390, 20, _CONFIG["EXPORT_SKINPARTITION"])
        E["EXPORT_BONESPERPARTITION"] = Draw.Number("Max Bones Per Partition", addEvent("EXPORT_BONESPERPARTITION"), 50, H-20, 390, 20, _CONFIG["EXPORT_BONESPERPARTITION"], 4, 18, "maximum number of bones per partition", updateBonesPerPartition)
        # the value 4 does for all games, so let's not let user change it
        #E["EXPORT_BONESPERVERTEX"] = Draw.Number("Max Bones Per Vertex", addEvent("EXPORT_BONESPERVERTEX"), 50, H-65, 390, 20, _CONFIG["EXPORT_BONESPERVERTEX"], 2, 8)
        H -= 50

        E["EXPORT_BHKLISTSHAPE"] = Draw.Toggle("Use Collision List (bhkListShape)", addEvent("EXPORT_BHKLISTSHAPE"), 50, H, 390, 20, _CONFIG["EXPORT_BHKLISTSHAPE"])
        E["EXPORT_MOPP"] = Draw.Toggle("Export Collision Mopp (EXPERIMENTAL)", addEvent("EXPORT_MOPP"), 50, H-20, 390, 20, _CONFIG["EXPORT_MOPP"])
        H -= 50

        #E["NIF_EXPORT_PATH"]        = Draw.String("",       addEvent("NIF_EXPORT_PATH"),     50, H-100, 390, 20, _CONFIG["NIF_EXPORT_PATH"],        390, "export path")
        #E["BROWSE_EXPORT_PATH"]     = Draw.PushButton('...',addEvent("BROWSE_EXPORT_PATH"), 440, H-100,  30, 20)
        
        games_list = sorted(NifFormat.games.keys())
        versions_list = sorted(NifFormat.versions.keys(), key=lambda x: NifFormat.versions[x])
        guiText("Game or NIF version", 50, H)
        H -= 30
        V = 50
        HH = H
        j = 0
        MAXJ = 7
        for i, game in enumerate(games_list):
            if j >= MAXJ:
                H = HH
                j = 0
                V += 150
            state = (_CONFIG["EXPORT_VERSION"] == game)
            E["GAME_%s"%game.upper()] = Draw.Toggle(game, addEvent("GAME_%s"%game), V, H-j*20, 150, 20, state)
            j += 1
        j = 0
        V += 160
        for i, version in enumerate(versions_list):
            if j >= MAXJ:
                H = HH
                j = 0
                V += 70
            state = (_CONFIG["EXPORT_VERSION"] == version)
            E["VERSION_%s"%version] = Draw.Toggle(version, addEvent("VERSION_%s"%version), V, H-j*20, 70, 20, state)
            j += 1
        H = HH - 20 - 20*min(MAXJ, max(len(NifFormat.versions), len(NifFormat.games)))
        H -= 20 # leave some space
        E["CANCEL"]                 = Draw.PushButton('cancel',addEvent("CANCEL"),  50, H, 100, 20)
        E["OK"]                     = Draw.PushButton('ok',    addEvent("OK"),  50, H-25, 100, 20)

    # Sets the GUI elements to a global var to avoid them going out of scope (causes segfaults)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(evt):
    """
    Event handler for buttons
    """
    global _GUI_EVENTS, _CONFIG, _IDX_TEXPATH

    try:
        evName = _GUI_EVENTS[evt]
    except IndexError:
        evName = None

    if evName in  ["OK", "BACK"]:
        save()
        exitGUI()
    elif evName == "CANCEL":
        Draw.Exit()
        return
    elif evName == "REALIGN_BONES":
        _CONFIG["REALIGN_BONES"] = not _CONFIG["REALIGN_BONES"]
    elif evName == "IMPORT_ANIMATION":
        _CONFIG["IMPORT_ANIMATION"] = not _CONFIG["IMPORT_ANIMATION"]
    elif evName == "IMPORT_SKELETON":
        _CONFIG["IMPORT_SKELETON"] = not _CONFIG["IMPORT_SKELETON"]
    elif evName == "IMPORT_SENDBONESTOBINDPOS":
        _CONFIG["IMPORT_SENDBONESTOBINDPOS"] = not _CONFIG["IMPORT_SENDBONESTOBINDPOS"]
    elif evName == "IMPORT_APPLYSKINDEFORM":
        _CONFIG["IMPORT_APPLYSKINDEFORM"] = not _CONFIG["IMPORT_APPLYSKINDEFORM"]
    elif evName == "BROWSE_IMPORT_PATH":
        # browse import path
        print _CONFIG["NIF_IMPORT_PATH"]
        Blender.Window.FileSelector(setImportPath, "set import path", _CONFIG["NIF_IMPORT_PATH"])
    elif evName == "BROWSE_EXPORT_PATH":
        # browse import path
        Blender.Window.FileSelector(setExportPath, "set export path", _CONFIG["NIF_EXPORT_PATH"])
    elif evName == "BROWSE_TEXBASE":
        # browse and add texture search path
        Blender.Window.FileSelector(setTextureBase, "set texture base folder")
    elif evName == "BROWSE_TEXPATH":
        # browse and add texture search path
        Blender.Window.FileSelector(addTexturePath, "add texture search path")
    elif evName == "TEXPATH_NEXT":
        if _IDX_TEXPATH < (len(_CONFIG["TEXTURE_SEARCH_PATH"])-1):
            _IDX_TEXPATH += 1
    elif evName == "TEXPATH_PREV":
        if _IDX_TEXPATH > 0:
            _IDX_TEXPATH -= 1
    elif evName == "TEXPATH_REMOVE":
        if _IDX_TEXPATH in xrange(len(_CONFIG["TEXTURE_SEARCH_PATH"])):
            del _CONFIG["TEXTURE_SEARCH_PATH"][_IDX_TEXPATH]
        if _IDX_TEXPATH > 0:
            _IDX_TEXPATH-=1
    elif evName[:5] == "GAME_":
        _CONFIG["EXPORT_VERSION"] = evName[5:]
    elif evName[:8] == "VERSION_":
        _CONFIG["EXPORT_VERSION"] = evName[8:]
    elif evName == "EXPORT_FLATTENSKIN":
        _CONFIG["EXPORT_FLATTENSKIN"] = not _CONFIG["EXPORT_FLATTENSKIN"]
        if _CONFIG["EXPORT_FLATTENSKIN"]: # if skin is flattened
            _CONFIG["EXPORT_ANIMATION"] = 1 # force geometry only
    elif evName == "EXPORT_STRIPIFY":
        _CONFIG["EXPORT_STRIPIFY"] = not _CONFIG["EXPORT_STRIPIFY"]
    elif evName == "EXPORT_STITCHSTRIPS":
        _CONFIG["EXPORT_STITCHSTRIPS"] = not _CONFIG["EXPORT_STITCHSTRIPS"]
    elif evName[:17] == "EXPORT_ANIMATION_":
         value = int(evName[17:])
         _CONFIG["EXPORT_ANIMATION"] = value
         if value == 0 or value == 2: # if animation is exported
             _CONFIG["EXPORT_FLATTENSKIN"] = False # disable flattening skin
    elif evName == "EXPORT_SKINPARTITION":
        _CONFIG["EXPORT_SKINPARTITION"] = not _CONFIG["EXPORT_SKINPARTITION"]
    elif evName == "EXPORT_BHKLISTSHAPE":
        _CONFIG["EXPORT_BHKLISTSHAPE"] = not _CONFIG["EXPORT_BHKLISTSHAPE"]
    elif evName == "EXPORT_MOPP":
        _CONFIG["EXPORT_MOPP"] = not _CONFIG["EXPORT_MOPP"]
    Draw.Redraw(1)

def event(evt, val):
    """
    Event handler for GUI elements
    """
    global _CONFIG, _BACK_TARGET

    if evt == Draw.ESCKEY:
        save()
        if _BACK_TARGET == "Import":
            exitGUI()
        else:
            Draw.Exit()
            return
    elif evt == Draw.RETKEY:
        save()
        exitGUI()

    Draw.Redraw(1)

def openGUI(back_target=None):
    """
    Opens the config GUI
    """
    # defines what script called the config screen
    global _BACK_TARGET
    _BACK_TARGET = back_target
    load()
    Draw.Register(drawGUI, event, buttonEvent)
    
def exitGUI():
    """
    Closes the config GUI
    """
    Draw.Exit()
    if _BACK_TARGET == "Import":
        Read.openGUI()
    elif _BACK_TARGET == "Export":
        if not _CONFIG["PROFILE"]:
            Write.export_nif(_CONFIG["NIF_EXPORT_FILE"])
        else:
            import cProfile
            import pstats
            prof = cProfile.Profile()
            prof.runctx('Write.export_nif(_CONFIG["NIF_EXPORT_FILE"])', locals(), globals())
            prof.dump_stats(_CONFIG["PROFILE"])
            stats = pstats.Stats(_CONFIG["PROFILE"])
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats()

def save():
    """
    Saves the current configuration
    """
    global _CONFIG, _CONFIG_NAME
    #print "datadir", Blender.Get('datadir'), "\n\n"
    #print "--",_CONFIG_NAME, _CONFIG, "\n\n"
    Registry.SetKey(_CONFIG_NAME, _CONFIG, True)
    load()
    

def load():
    """
    Loads the stored configuration and checks saved configuration for incompatible values
    """
    # both loads and cleans up the configuration from the registry
    global _CONFIG, _CONFIG_NAME
    reload(Defaults)
    _CONFIG = {}
    for key in dir(Defaults):
        if key[:5] == "_CFG_":
            _CONFIG[key[5:]] = getattr(Defaults, key)
    oldConfig = Blender.Registry.GetKey(_CONFIG_NAME, True)
    #print "oldConfig", oldConfig, "\n\n"
    newConfig = {}
    for key, val in _CONFIG.iteritems():
        try:
            if type(oldConfig[key]) == type(val):
                newConfig[key] = oldConfig[key]
            else:
                newConfig[key] = val
        except KeyError:
            newConfig[key] = val
        except TypeError:
            newConfig[key] = val
    #print "newConfig", newConfig, "\n\n"
    _CONFIG = newConfig
    Blender.Registry.SetKey(_CONFIG_NAME, _CONFIG, True)

