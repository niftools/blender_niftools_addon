"""Common functions for the Blender nif import and export scripts."""

__version__ = "2.2.2"
__requiredpyffiversion__ = "0.7.1"
__requiredblenderversion__ = "245"

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****

import Blender
from Blender import Draw, Registry
import sys, os

class NifConfig:
    """Class which handles configuration of nif import and export in Blender.

    Important: keep every instance of this class in a global variable
    (otherwise gui elements might go out of skope which will crash
    Blender)."""
    # class global constants
    CONFIG_NAME = "nifscripts" # name of the config file
    TARGET_IMPORT = 0          # config target value when importing
    TARGET_EXPORT = 1          # config target value when exporting
    # GUI stuff
    XORIGIN     = 50  # x coordinate of origin
    XCOLUMNSKIP = 390 # width of a column
    XCOLUMNSEP  = 10  # width of the column separator
    YORIGIN     = -40 # y coordinate of origin relative to Blender.Window.GetAreaSize()[1]
    YLINESKIP   = 20  # height of a line
    YLINESEP    = 10  # height of a line separator
    # the DEFAULTS dict defines the valid config variables, default values,
    # and their type
    # IMPORTANT: don't start dictionary keys with an underscore
    # the Registry module doesn't like that, apparently
    DEFAULTS = dict(
        IMPORT_FILE = Blender.sys.join(
            Blender.sys.dirname(Blender.sys.progname), "import.nif"),
        EXPORT_FILE = Blender.sys.join(
            Blender.sys.dirname(Blender.sys.progname), "export.nif"),
        IMPORT_REALIGN_BONES = 2, # 0 = no, 1 = tail, 2 = tail+rotation
        IMPORT_ANIMATION = True,
        IMPORT_SCALE_CORRECTION = 0.1,
        EXPORT_SCALE_CORRECTION = 10.0, # 1/import scale correction
        IMPORT_TEXTURE_PATH = [],
        EXPORT_FLATTENSKIN = False,
        EXPORT_VERSION = 'Oblivion',
        EPSILON = 0.005, # used for checking equality with floats
        VERBOSITY = 0,   # verbosity level, determines how much debug output will be generated
        IMPORT_SKELETON = 0, # 0 = normal import, 1 = import file as skeleton, 2 = import mesh and attach to skeleton
        EXPORT_ANIMATION = 0, # export everything (1=geometry only, 2=animation only)
        EXPORT_FORCEDDS = True, # force dds extension on texture files
        EXPORT_SKINPARTITION = True, # generate skin partition
        EXPORT_BONESPERVERTEX = 4,
        EXPORT_BONESPERPARTITION = 18,
        EXPORT_PADBONES = False,
        EXPORT_STRIPIFY = True,
        EXPORT_STITCHSTRIPS = False,
        EXPORT_SMOOTHOBJECTSEAMS = True,
        IMPORT_SENDBONESTOBINDPOS = True,
        IMPORT_APPLYSKINDEFORM = False,
        EXPORT_BHKLISTSHAPE = False,
        EXPORT_MOPP = False,
        EXPORT_OB_BSXFLAGS = 2,
        EXPORT_OB_MASS = 10.0,
        EXPORT_OB_SOLID = True,
        EXPORT_OB_MOTIONSYSTEM = 7, # keyframed
        EXPORT_OB_UNKNOWNBYTE1 = 1,
        EXPORT_OB_UNKNOWNBYTE2 = 1,
        EXPORT_OB_QUALITYTYPE = 1, # fixed
        EXPORT_OB_WIND = 0,
        EXPORT_OB_LAYER = 1, # static
        EXPORT_OB_MATERIAL = 9, # wood
        PROFILE = '') # name of file where Python profiler dumps the profile; set to empty string to turn off profiling

    def __init__(self):
        """Initialize and load configuration."""
        # initialize all instance variables
        self.guiElements = {} # dictionary of gui elements (buttons, strings, sliders, ...)
        self.guiEvents = []   # list of events
        self.guiEventIds = {} # dictionary of event ids
        self.config = {}      # configuration dictionary
        self.target = None    # import or export
        self.callback = None  # function to call when config gui is done
        self.texpathIndex = 0
        self.texpathCurrent = ''

        # reset GUI coordinates
        self.xPos = self.XORIGIN
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

        # load configuration
        self.load()

        # clears the console window
        if sys.platform in ('linux-i386','linux2'):
            os.system("clear")
        elif sys.platform in ('win32','dos','ms-dos'):
            os.system("cls")

        # print scripts info
        print('Blender NIF Scripts %s (running on Blender %s, PyFFI %s)'
              %(__version__, __blenderversion__, __pyffiversion__))

    def run(self, target, filename, callback):
        """Run the config gui."""
        self.target = target     # import or export
        self.callback = callback # function to call when config gui is done

        # save file name
        # (the key where to store the file name depends
        # on the target)
        if self.target == self.TARGET_IMPORT:
            self.config["IMPORT_FILE"] = filename
        elif self.target == self.TARGET_EXPORT:
            self.config["EXPORT_FILE"] = filename
        self.save()

        # prepare and run gui
        self.texpathIndex = 0
        self.updateTexpathCurrent()
        Draw.Register(self.guiDraw, self.guiEvent, self.guiButtonEvent)

    def save(self):
        """Save and validate configuration to Blender registry."""
        Registry.SetKey(self.CONFIG_NAME, self.config, True)
        self.load() # for validation

    def load(self):
        """Load the configuration stored in the Blender registry and checks
        configuration for incompatible values."""
        # copy defaults
        self.config = dict(**self.DEFAULTS)
        # read configuration
        savedconfig = Blender.Registry.GetKey(self.CONFIG_NAME, True)
        # port config keys from old versions to current version
        try:
            self.config["IMPORT_TEXTURE_PATH"] = savedconfig["TEXTURE_SEARCH_PATH"]
        except:
            pass
        try:
            self.config["IMPORT_FILE"] = Blender.sys.join(
                savedconfig["NIF_IMPORT_PATH"], savedconfig["NIF_IMPORT_FILE"])
        except:
            pass
        try:
            self.config["EXPORT_FILE"] = savedconfig["NIF_EXPORT_FILE"]
        except:
            pass
        try:
            self.config["IMPORT_REALIGN_BONES"] = savedconfig["REALIGN_BONES"]
        except:
            pass
        try:
            if self.config["IMPORT_REALIGN_BONES"] == True:
               self.config["IMPORT_REALIGN_BONES"] = 2
            elif self.config["IMPORT_REALIGN_BONES"] == False:
               self.config["IMPORT_REALIGN_BONES"] = 1
        except:
            pass
        try:
            if savedconfig["IMPORT_SKELETON"] == True:
                self.config["IMPORT_SKELETON"] = 1
            elif savedconfig["IMPORT_SKELETON"] == False:
                self.config["IMPORT_SKELETON"] = 0
        except:
            pass
        # merge configuration with defaults
        if savedconfig:
            for key, val in self.DEFAULTS.iteritems():
                try:
                    savedval = savedconfig[key]
                except KeyError:
                    pass
                else:
                    if isinstance(savedval, val.__class__):
                        self.config[key] = savedval
        # store configuration
        Blender.Registry.SetKey(self.CONFIG_NAME, self.config, True)

    def eventId(self, event_name):
        """Return event id from event name, and register event if it is new."""
        try:
            event_id = self.guiEventIds[event_name]
        except KeyError:
            event_id = len(self.guiEvents)
            self.guiEventIds[event_name] = event_id
            self.guiEvents.append(event_name)
        if  event_id >= 16383:
            raise RuntimeError("Maximum number of events exceeded")
        return event_id

    def drawYSep(self):
        """Vertical skip."""
        self.yPos -= self.YLINESEP

    def drawNextColumn(self):
        """Start a new column."""
        self.xPos += self.XCOLUMNSKIP + self.XCOLUMNSEP
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

    def drawSlider(
        self, text, event_name, min_val, max_val, callback, val = None,
        num_items = 1, item = 0):
        """Draw a slider."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Slider(
            text,
            self.eventId(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val, min_val, max_val,
            0, # realtime
            "", # tooltip,
            callback)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def drawLabel(self, text, event_name, num_items = 1, item = 0):
        """Draw a line of text."""
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Label(
            text,
            self.xPos + item*width, self.yPos, width, self.YLINESKIP)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def drawList(self, text, event_name_prefix, val):
        """Create elements to select a list of things.

        Registers events PREFIX_ITEM, PREFIX_PREV, PREFIX_NEXT, PREFIX_REMOVE
        and PREFIX_ADD."""
        self.guiElements["%s_ITEM"%event_name_prefix]   = Draw.String(
            text,
            self.eventId("%s_ITEM"%event_name_prefix),
            self.xPos, self.yPos, self.XCOLUMNSKIP-90, self.YLINESKIP,
            val, 255)
        self.guiElements["%s_PREV"%event_name_prefix]   = Draw.PushButton(
            '<',
            self.eventId("%s_PREV"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-90, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_NEXT"%event_name_prefix]   = Draw.PushButton(
            '>',
            self.eventId("%s_NEXT"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-70, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_REMOVE"%event_name_prefix] = Draw.PushButton(
            'X',
            self.eventId("%s_REMOVE"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-50, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_ADD"%event_name_prefix]    = Draw.PushButton(
            '...',
            self.eventId("%s_ADD"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-30, self.yPos, 30, self.YLINESKIP)
        self.yPos -= self.YLINESKIP

    def drawToggle(self, text, event_name, val = None, num_items = 1, item = 0):
        """Draw a toggle button."""
        if val == None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Toggle(
            text,
            self.eventId(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def drawPushButton(self, text, event_name, num_items = 1, item = 0):
        """Draw a push button."""
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.PushButton(
            text,
            self.eventId(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def drawNumber(
        self, text, event_name, min_val, max_val, callback, val = None,
        num_items = 1, item = 0):
        """Draw an input widget for numbers."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Number(
            text,
            self.eventId(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val,
            min_val, max_val,
            "", # tooltip
            callback)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def guiDraw(self):
        """Draw config GUI."""
        # reset position
        self.xPos = self.XORIGIN
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

        # common options
        self.drawSlider(
            text = "Scale Correction:  ",
            event_name = "SCALE_CORRECTION",
            val = self.config["EXPORT_SCALE_CORRECTION"],
            min_val = 0.01, max_val = 100.0,
            callback = self.updateScale)
        self.drawYSep()

        # import-only options
        if self.target == self.TARGET_IMPORT:
            self.drawLabel(
                text = "Texture Search Paths:",
                event_name = "TEXPATH_TEXT")
            self.drawList(
                text = "",
                event_name_prefix = "TEXPATH",
                val = self.texpathCurrent)
            self.drawYSep()

            self.drawToggle(
                text = "Import Animation",
                event_name = "IMPORT_ANIMATION")
            self.drawYSep()

            self.drawToggle(
                text = "Realign Bone Tail Only",
                event_name = "IMPORT_REALIGN_BONES_1",
                val = (self.config["IMPORT_REALIGN_BONES"] == 1),
                num_items = 2, item = 0)
            self.drawToggle(
                text = "Realign Bone Tail + Roll",
                event_name = "IMPORT_REALIGN_BONES_2",
                val = (self.config["IMPORT_REALIGN_BONES"] == 2),
                num_items = 2, item = 1)
            self.drawToggle(
                text = "Send Bones To Bind Position",
                event_name = "IMPORT_SENDBONESTOBINDPOS")
            self.drawToggle(
                text = "Apply Skin Deformation",
                event_name = "IMPORT_APPLYSKINDEFORM")
            self.drawYSep()
            
            self.drawToggle(
                text = "Import Skeleton Only + Parent Selected",
                event_name = "IMPORT_SKELETON_1",
                val = (self.config["IMPORT_SKELETON"] == 1))
            self.drawToggle(
                text = "Import Geometry Only + Parent To Selected Armature",
                event_name = "IMPORT_SKELETON_2",
                val = (self.config["IMPORT_SKELETON"] == 2))
            self.drawYSep()

        # export-only options
        if self.target == self.TARGET_EXPORT:
            self.drawToggle(
                text = "Export Geometry + Animation (.nif)",
                event_name = "EXPORT_ANIMATION_0",
                val = (self.config["EXPORT_ANIMATION"] == 0))
            self.drawToggle(
                text = "Export Geometry Only (.nif)",
                event_name = "EXPORT_ANIMATION_1",
                val = (self.config["EXPORT_ANIMATION"] == 1))
            self.drawToggle(
                text = "Export Animation Only (.kf) - MORROWIND ONLY FOR NOW",
                event_name = "EXPORT_ANIMATION_2",
                val = (self.config["EXPORT_ANIMATION"] == 2))
            self.drawYSep()

            self.drawToggle(
                text = "Force DDS Extension",
                event_name = "EXPORT_FORCEDDS")
            self.drawYSep()

            self.drawToggle(
                text = "Stripify Geometries",
                event_name = "EXPORT_STRIPIFY",
                num_items = 2, item = 0)
            self.drawToggle(
                text = "Stitch Strips",
                event_name = "EXPORT_STITCHSTRIPS",
                num_items = 2, item = 1)
            self.drawYSep()

            self.drawToggle(
                text = "Smoothen Inter-Object Seams",
                event_name = "EXPORT_SMOOTHOBJECTSEAMS")
            self.drawYSep()

            self.drawToggle(
                text = "Flatten Skin",
                event_name = "EXPORT_FLATTENSKIN")
            self.drawToggle(
                text = "Export Skin Partition",
                event_name = "EXPORT_SKINPARTITION",
                num_items = 3, item = 0)
            self.drawToggle(
                text = "Pad & Sort Bones",
                event_name = "EXPORT_PADBONES",
                num_items = 3, item = 1)
            self.drawNumber(
                text = "Max Bones",
                event_name = "EXPORT_BONESPERPARTITION",
                min_val = 4, max_val = 18,
                callback = self.updateBonesPerPartition,
                num_items = 3, item = 2)
            self.drawYSep()

            games_list = sorted(filter(lambda x: x != '?', NifFormat.games.keys()))
            versions_list = sorted(NifFormat.versions.keys(), key=lambda x: NifFormat.versions[x])
            V = self.xPos
            H = HH = self.yPos
            j = 0
            MAXJ = 7
            for i, game in enumerate(games_list):
                if j >= MAXJ:
                    H = HH
                    j = 0
                    V += 150
                state = (self.config["EXPORT_VERSION"] == game)
                self.guiElements["GAME_%s"%game.upper()] = Draw.Toggle(game, self.eventId("GAME_%s"%game), V, H-j*20, 150, 20, state)
                j += 1
            j = 0
            V += 160
            for i, version in enumerate(versions_list):
                if j >= MAXJ:
                    H = HH
                    j = 0
                    V += 70
                state = (self.config["EXPORT_VERSION"] == version)
                self.guiElements["VERSION_%s"%version] = Draw.Toggle(version, self.eventId("VERSION_%s"%version), V, H-j*20, 70, 20, state)
                j += 1
            self.yPos -= 20*min(MAXJ, max(len(NifFormat.versions), len(NifFormat.games)))
            self.drawYSep()
            
            if self.config["EXPORT_VERSION"] in games_list:
                self.guiElements["EXPORT_RESET"] = Draw.PushButton(
                    "Restore Default Settings For Selected Game",
                    self.eventId("GAME_%s"%self.config["EXPORT_VERSION"]),
                    self.xPos, self.yPos, self.XCOLUMNSKIP, self.YLINESKIP)
                self.yPos -= self.YLINESKIP
                self.drawYSep()
            
        self.drawPushButton(
            text = "Ok",
            event_name = "OK",
            num_items = 3, item = 0)
        # (item 1 is whitespace)
        self.drawPushButton(
            text = "Cancel",
            event_name = "CANCEL",
            num_items = 3, item = 2)

        # export-only options for oblivion
        if self.target == self.TARGET_EXPORT and self.config["EXPORT_VERSION"] == "Oblivion":
            self.drawNextColumn()
            
            self.drawLabel(
                text = "(see http://niftools.sourceforge.net/wiki/Blender/Collision)",
                event_name = "EXPORT_OB_COLLISIONHTML")
            self.drawYSep()

            self.drawToggle(
                text = "Use bhkListShape",
                event_name = "EXPORT_BHKLISTSHAPE")
            self.drawToggle(
                text = "Export Mopp (EXPERIMENTAL)",
                event_name = "EXPORT_MOPP")
            self.drawYSep()

            self.drawNumber(
                text = "Material:  ",
                event_name = "EXPORT_OB_MATERIAL",
                min_val = 0, max_val = 30,
                callback = self.updateObMaterial)
            self.drawYSep()

            self.drawLabel(
                text = "Rigid Body Settings",
                event_name = "EXPORT_OB_RIGIDBODY_LABEL",
                num_items = 3, item = 0)
            self.drawPushButton(
                text = "Static",
                event_name = "EXPORT_OB_RIGIDBODY_STATIC",
                num_items = 3, item = 1)
            self.drawPushButton(
                text = "Clutter",
                event_name = "EXPORT_OB_RIGIDBODY_CLUTTER",
                num_items = 3, item = 2)
            self.drawNumber(
                text = "BSX Flags:  ",
                event_name = "EXPORT_OB_BSXFLAGS",
                min_val = 2, max_val = 3,
                callback = self.updateObBSXFlags,
                num_items = 2, item = 0)
            self.drawSlider(
                text = "Mass:  ",
                event_name = "EXPORT_OB_MASS",
                min_val = 0.1, max_val = 150.0,
                callback = self.updateObMass,
                num_items = 2, item = 1)
            self.drawNumber(
                text = "Layer:  ",
                event_name = "EXPORT_OB_LAYER",
                min_val = 0, max_val = 57,
                callback = self.updateObLayer,
                num_items = 3, item = 0)
            self.drawNumber(
                text = "Motion System:  ",
                event_name = "EXPORT_OB_MOTIONSYSTEM",
                min_val = 0, max_val = 9,
                callback = self.updateObMotionSystem,
                num_items = 3, item = 1)
            self.drawNumber(
                text = "Quality Type:  ",
                event_name = "EXPORT_OB_QUALITYTYPE",
                min_val = 0, max_val = 8,
                callback = self.updateObQualityType,
                num_items = 3, item = 2)
            self.drawNumber(
                text = "Unk Byte 1:  ",
                event_name = "EXPORT_OB_UNKNOWNBYTE1",
                min_val = 1, max_val = 2,
                callback = self.updateObUnknownByte1,
                num_items = 3, item = 0)
            self.drawNumber(
                text = "Unk Byte 2:  ",
                event_name = "EXPORT_OB_UNKNOWNBYTE2",
                min_val = 1, max_val = 2,
                callback = self.updateObUnknownByte2,
                num_items = 3, item = 1)
            self.drawNumber(
                text = "Wind:  ",
                event_name = "EXPORT_OB_WIND",
                min_val = 0, max_val = 1,
                callback = self.updateObWind,
                num_items = 3, item = 2)
            self.drawToggle(
                text = "Solid",
                event_name = "EXPORT_OB_SOLID",
                num_items = 2, item = 0)
            self.drawToggle(
                text = "Hollow",
                event_name = "EXPORT_OB_HOLLOW",
                val = not self.config["EXPORT_OB_SOLID"],
                num_items = 2, item = 1)

        Draw.Redraw(1)

    def guiButtonEvent(self, evt):
        """Event handler for buttons."""
        try:
            evName = self.guiEvents[evt]
        except IndexError:
            evName = None

        if evName == "OK":
            self.save()
            self.guiExit()
        elif evName == "CANCEL":
            self.callback = None
            self.guiExit()
        elif evName == "TEXPATH_ADD":
            # browse and add texture search path
            Blender.Window.FileSelector(self.addTexturePath, "Add Texture Search Path")
        elif evName == "TEXPATH_NEXT":
            if self.texpathIndex < (len(self.config["IMPORT_TEXTURE_PATH"])-1):
                self.texpathIndex += 1
            self.updateTexpathCurrent()
        elif evName == "TEXPATH_PREV":
            if self.texpathIndex > 0:
                self.texpathIndex -= 1
            self.updateTexpathCurrent()
        elif evName == "TEXPATH_REMOVE":
            if self.texpathIndex < len(self.config["IMPORT_TEXTURE_PATH"]):
                del self.config["IMPORT_TEXTURE_PATH"][self.texpathIndex]
            if self.texpathIndex > 0:
                self.texpathIndex -= 1
            self.updateTexpathCurrent()
        elif evName == "IMPORT_REALIGN_BONES_1":
            if self.config["IMPORT_REALIGN_BONES"] == 1:
                self.config["IMPORT_REALIGN_BONES"] = 0
            else:
                self.config["IMPORT_REALIGN_BONES"] = 1
        elif evName == "IMPORT_REALIGN_BONES_2":
            if self.config["IMPORT_REALIGN_BONES"] == 2:
                self.config["IMPORT_REALIGN_BONES"] = 0
            else:
                self.config["IMPORT_REALIGN_BONES"] = 2
        elif evName == "IMPORT_ANIMATION":
            self.config["IMPORT_ANIMATION"] = not self.config["IMPORT_ANIMATION"]
        elif evName == "IMPORT_SKELETON_1":
            if self.config["IMPORT_SKELETON"] == 1:
                self.config["IMPORT_SKELETON"] = 0
            else:
                self.config["IMPORT_SKELETON"] = 1
        elif evName == "IMPORT_SKELETON_2":
            if self.config["IMPORT_SKELETON"] == 2:
                self.config["IMPORT_SKELETON"] = 0
            else:
                self.config["IMPORT_SKELETON"] = 2
        elif evName == "IMPORT_SENDBONESTOBINDPOS":
            self.config["IMPORT_SENDBONESTOBINDPOS"] = not self.config["IMPORT_SENDBONESTOBINDPOS"]
        elif evName == "IMPORT_APPLYSKINDEFORM":
            self.config["IMPORT_APPLYSKINDEFORM"] = not self.config["IMPORT_APPLYSKINDEFORM"]
        elif evName[:5] == "GAME_":
            self.config["EXPORT_VERSION"] = evName[5:]
            # settings that usually make sense, fail-safe
            self.config["EXPORT_FORCEDDS"] = True
            self.config["EXPORT_SMOOTHOBJECTSEAMS"] = True
            self.config["EXPORT_STRIPIFY"] = False
            self.config["EXPORT_STITCHSTRIPS"] = False
            self.config["EXPORT_ANIMATION"] = 1
            self.config["EXPORT_FLATTENSKIN"] = False
            self.config["EXPORT_SKINPARTITION"] = False
            self.config["EXPORT_BONESPERPARTITION"] = 4
            self.config["EXPORT_PADBONES"] = False
            self.config["EXPORT_OB_SOLID"] = True
            # set default settings per game
            if self.config["EXPORT_VERSION"] == "Morrowind":
                pass # fail-safe settings work
            if self.config["EXPORT_VERSION"] == "Freedom Force vs. the 3rd Reich":
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = True
            elif self.config["EXPORT_VERSION"] == "Civilization IV":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_SKINPARTITION"] = True
            elif self.config["EXPORT_VERSION"] == "Oblivion":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_FLATTENSKIN"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
                # oblivion specific settings
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_MOPP"] = False
                self.config["EXPORT_OB_MATERIAL"] = 9 # wood
                # rigid body: static
                self.config["EXPORT_OB_BSXFLAGS"] = 2
                self.config["EXPORT_OB_MASS"] = 10.0
                self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # keyframed
                self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
                self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
                self.config["EXPORT_OB_QUALITYTYPE"] = 1 # fixed
                self.config["EXPORT_OB_WIND"] = 0
                self.config["EXPORT_OB_LAYER"] = 1 # static
        elif evName[:8] == "VERSION_":
            self.config["EXPORT_VERSION"] = evName[8:]
        elif evName == "EXPORT_FLATTENSKIN":
            self.config["EXPORT_FLATTENSKIN"] = not self.config["EXPORT_FLATTENSKIN"]
            if self.config["EXPORT_FLATTENSKIN"]: # if skin is flattened
                self.config["EXPORT_ANIMATION"] = 1 # force geometry only
        elif evName == "EXPORT_FORCEDDS":
            self.config["EXPORT_FORCEDDS"] = not self.config["EXPORT_FORCEDDS"]
        elif evName == "EXPORT_STRIPIFY":
            self.config["EXPORT_STRIPIFY"] = not self.config["EXPORT_STRIPIFY"]
        elif evName == "EXPORT_STITCHSTRIPS":
            self.config["EXPORT_STITCHSTRIPS"] = not self.config["EXPORT_STITCHSTRIPS"]
        elif evName == "EXPORT_SMOOTHOBJECTSEAMS":
            self.config["EXPORT_SMOOTHOBJECTSEAMS"] = not self.config["EXPORT_SMOOTHOBJECTSEAMS"]
        elif evName[:17] == "EXPORT_ANIMATION_":
             value = int(evName[17:])
             self.config["EXPORT_ANIMATION"] = value
             if value == 0 or value == 2: # if animation is exported
                 self.config["EXPORT_FLATTENSKIN"] = False # disable flattening skin
        elif evName == "EXPORT_SKINPARTITION":
            self.config["EXPORT_SKINPARTITION"] = not self.config["EXPORT_SKINPARTITION"]
        elif evName == "EXPORT_PADBONES":
            self.config["EXPORT_PADBONES"] = not self.config["EXPORT_PADBONES"]
            if self.config["EXPORT_PADBONES"]: # bones are padded
                self.config["EXPORT_BONESPERPARTITION"] = 4 # force 4 bones per partition
        elif evName == "EXPORT_BHKLISTSHAPE":
            self.config["EXPORT_BHKLISTSHAPE"] = not self.config["EXPORT_BHKLISTSHAPE"]
        elif evName == "EXPORT_MOPP":
            self.config["EXPORT_MOPP"] = not self.config["EXPORT_MOPP"]
        elif evName == "EXPORT_OB_SOLID":
            self.config["EXPORT_OB_SOLID"] = True
        elif evName == "EXPORT_OB_HOLLOW":
            self.config["EXPORT_OB_SOLID"] = False
        elif evName == "EXPORT_OB_RIGIDBODY_STATIC":
            self.config["EXPORT_OB_BSXFLAGS"] = 2
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # keyframed
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
            self.config["EXPORT_OB_QUALITYTYPE"] = 1 # fixed
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 1 # static
            self.config["EXPORT_OB_SOLID"] = True
        elif evName == "EXPORT_OB_RIGIDBODY_CLUTTER":
            self.config["EXPORT_OB_BSXFLAGS"] = 3
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 4 # keyframed
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 3 # fixed
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 4 # clutter
            self.config["EXPORT_OB_SOLID"] = True
        Draw.Redraw(1)

    def guiEvent(self, evt, val):
        """Event handler for GUI elements."""

        if evt == Draw.ESCKEY:
            self.callback = None
            self.guiExit()
        elif evt == Draw.RETKEY:
            self.save()
            self.guiExit()

        Draw.Redraw(1)

    def guiExit(self):
        """Close config GUI and call callback function."""
        Draw.Exit()
        if not self.callback: return # no callback
        # pass on control to callback function
        if not self.config["PROFILE"]:
            # without profiling
            self.callback(**self.config)
        else:
            # with profiling
            import cProfile
            import pstats
            prof = cProfile.Profile()
            prof.runctx('self.callback(**self.config)', locals(), globals())
            prof.dump_stats(self.config["PROFILE"])
            stats = pstats.Stats(self.config["PROFILE"])
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats()

    def addTexturePath(self, texture_path):
        texture_path = Blender.sys.dirname(texture_path)
        if texture_path == '' or not Blender.sys.exists(texture_path):
            Draw.PupMenu('No path selected or path does not exist%t|Ok')
        else:
            if texture_path not in self.config["IMPORT_TEXTURE_PATH"]:
                self.config["IMPORT_TEXTURE_PATH"].append(texture_path)
            self.texpathIndex = self.config["IMPORT_TEXTURE_PATH"].index(texture_path)
        self.updateTexpathCurrent()

    def updateTexpathCurrent(self):
        """Update self.texpathCurrent string."""
        if self.config["IMPORT_TEXTURE_PATH"]:
            self.texpathCurrent = self.config["IMPORT_TEXTURE_PATH"][self.texpathIndex]
        else:
            self.texpathCurrent = ''

    def updateScale(self, evt, val):
        self.config["EXPORT_SCALE_CORRECTION"] = val
        self.config["IMPORT_SCALE_CORRECTION"] = 1.0 / self.config["EXPORT_SCALE_CORRECTION"]

    def updateBonesPerPartition(self, evt, val):
        self.config["EXPORT_BONESPERPARTITION"] = val
        self.config["EXPORT_PADBONES"] = False

    def updateObBSXFlags(self, evt, val):
        self.config["EXPORT_OB_BSXFLAGS"] = val

    def updateObMaterial(self, evt, val):
        self.config["EXPORT_OB_MATERIAL"] = val

    def updateObLayer(self, evt, val):
        self.config["EXPORT_OB_LAYER"] = val

    def updateObMass(self, evt, val):
        self.config["EXPORT_OB_MASS"] = val

    def updateObMotionSystem(self, evt, val):
        self.config["EXPORT_OB_MOTIONSYSTEM"] = val

    def updateObQualityType(self, evt, val):
        self.config["EXPORT_OB_QUALITYTYPE"] = val

    def updateObUnknownByte1(self, evt, val):
        self.config["EXPORT_OB_UNKNOWNBYTE1"] = val

    def updateObUnknownByte2(self, evt, val):
        self.config["EXPORT_OB_UNKNOWNBYTE2"] = val

    def updateObWind(self, evt, val):
        self.config["EXPORT_OB_WIND"] = val

# utility functions
    
def cmp_versions(version1, version2):
    """Compare version strings."""
    def version_intlist(version):
        """Convert version string to list of integers."""
        return [int(x) for x in version.__str__().split(".")]
    return cmp(version_intlist(version1), version_intlist(version2))

# things to do on import and export

# check Blender version

__blenderversion__ = Blender.Get('version')
if cmp_versions(__blenderversion__, __requiredblenderversion__) == -1:
    err = """--------------------------
ERROR\nThis script requires Blender %s or higher.
It seems that you have an older version installed (%s).
Get a newer version at http://www.blender.org/
--------------------------"""%(__requiredblenderversion__, __blenderversion__)
    print err
    Blender.Draw.PupMenu("ERROR%t|Blender outdated, check console for details")
    raise ImportError

# check if PyFFI is installed and import NifFormat

try:
    from PyFFI import __version__ as __pyffiversion__
    from PyFFI.NIF import NifFormat
except ImportError:
    err = """--------------------------
ERROR\nThis script requires the Python File Format Interface (PyFFI).
Make sure that PyFFI resides in your Python path or in your Blender scripts folder.
If you do not have it: http://pyffi.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|PyFFI not found, check console for details")
    raise

# check PyFFI version

if cmp_versions(__pyffiversion__, __requiredpyffiversion__) == -1:
    err = """--------------------------
ERROR\nThis script requires Python File Format Interface %s or higher.
It seems that you have an older version installed (%s).
Get a newer version at http://pyffi.sourceforge.net/
--------------------------"""%(__requiredpyffiversion__, __pyffiversion__)
    print err
    Blender.Draw.PupMenu("ERROR%t|PyFFI outdated, check console for details")
    raise ImportError
