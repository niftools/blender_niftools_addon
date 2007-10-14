# common functions for the nif import and export scripts

__version__ = "2.1.14"
__requiredpyffiversion__ = "0.4.5"
__requiredblenderversion__ = "245"

# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------

# imports

import Blender
from Blender import Draw, Registry
import sys, os

# nif config class
# note: keep every instance of this class in a global variable
# (otherwise gui elements might go out of skope which will crash
# Blender)

class NifConfig:
    # class global constants
    CONFIG_NAME = "nifscripts" # name of the config file
    TARGET_IMPORT = 0          # config target value when importing
    TARGET_EXPORT = 1          # config target value when exporting
    # the DEFAULTS dict defines the valid config variables, default values,
    # and their type
    # IMPORTANT: don't start dictionary keys with an underscore
    # the Registry module doesn't like that, apparently
    DEFAULTS = dict(
        IMPORT_FILE = Blender.sys.join(Blender.sys.dirname(Blender.sys.progname), "import.nif"),
        EXPORT_FILE = Blender.sys.join(Blender.sys.dirname(Blender.sys.progname), "export.nif"),
        REALIGN_BONES = True,
        IMPORT_ANIMATION = True,
        IMPORT_SCALE_CORRECTION = 0.1,
        EXPORT_SCALE_CORRECTION = 10.0, # 1/import scale correction
        IMPORT_TEXTURE_PATH = [],
        EXPORT_FLATTENSKIN = False,
        EXPORT_VERSION = 'Oblivion',
        EPSILON = 0.005, # used for checking equality with floats
        VERBOSITY = 0,   # verbosity level, determines how much debug output will be generated
        IMPORT_SKELETON = False, # import file as skeleton
        EXPORT_ANIMATION = 0, # export everything (1=geometry only, 2=animation only)
        EXPORT_FORCEDDS = False, # force dds extension on texture files
        EXPORT_SKINPARTITION = True, # generate skin partition
        EXPORT_BONESPERVERTEX = 4,
        EXPORT_BONESPERPARTITION = 18,
        EXPORT_PADBONES = False,
        EXPORT_STRIPIFY = True,
        EXPORT_STITCHSTRIPS = False,
        EXPORT_SMOOTHOBJECTSEAMS = False,
        IMPORT_SENDBONESTOBINDPOS = True,
        IMPORT_APPLYSKINDEFORM = True,
        EXPORT_BHKLISTSHAPE = False,
        EXPORT_MOPP = True,
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

        # load configuration
        self.load()

        # clears the console window
        if sys.platform in ('linux-i386','linux2'):
            os.system("clear")
        elif sys.platform in ('win32','dos','ms-dos'):
            os.system("cls")

        # print scripts info
        print 'Blender NIF Scripts %s (running on Blender %s, PyFFI %s)'%(__version__, __blenderversion__, __pyffiversion__)

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
        """
        Load the configuration stored in the Blender registry and checks
        configuration for incompatible values.
        """
        # copy defaults
        self.config = dict(**self.DEFAULTS)
        # read configuration
        savedconfig = Blender.Registry.GetKey(self.CONFIG_NAME, True)
        # hacks for renaming keys
        try:
            self.config["IMPORT_TEXTURE_PATH"] = savedconfig["TEXTURE_SEARCH_PATH"]
        except:
            pass
        try:
            self.config["IMPORT_FILE"] = Blender.sys.join(savedconfig["NIF_IMPORT_PATH"], savedconfig["NIF_IMPORT_FILE"])
        except:
            pass
        try:
            self.config["EXPORT_FILE"] = savedconfig["NIF_EXPORT_FILE"]
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

    def guiDraw(self):
        """Draw config GUI."""
        H = Blender.Window.GetAreaSize()[1]-40

        # common options
        self.guiElements["SCALE_CORRECTION"] = Draw.Slider(
            "Scale Correction:  ",
            self.eventId("SCALE_CORRECTION"),
            50, H, 390, 20,
            self.config["EXPORT_SCALE_CORRECTION"],
            0.01, 100, 0, "scale", self.updateScale)
        H -= 30

        # import-only options
        if self.target == self.TARGET_IMPORT:
            self.guiElements["TEXPATH_ITEM"]   = Draw.String(
                "Tex Paths:  ",
                self.eventId("TEXPATH_ITEM"),
                50, H, 300, 20,
                self.texpathCurrent, 290)
            self.guiElements["TEXPATH_PREV"]   = Draw.PushButton(
                '<',
                self.eventId("TEXPATH_PREV"),
                350, H, 20, 20)
            self.guiElements["TEXPATH_NEXT"]   = Draw.PushButton(
                '>',
                self.eventId("TEXPATH_NEXT"),
                370, H, 20, 20)
            self.guiElements["TEXPATH_REMOVE"] = Draw.PushButton(
                'X',
                self.eventId("TEXPATH_REMOVE"),
                390, H, 20, 20)
            self.guiElements["TEXPATH_ADD"]    = Draw.PushButton(
                '...',
                self.eventId("TEXPATH_ADD"),
                410, H, 30, 20)
            H -= 30

            self.guiElements["IMPORT_ANIMATION"] = Draw.Toggle(
                "Import Animation",
                self.eventId("IMPORT_ANIMATION"),
                50, H, 390, 20,
                self.config["IMPORT_ANIMATION"])
            H -= 30

            self.guiElements["REALIGN_BONES"] = Draw.Toggle(
                "Realign Bones",
                self.eventId("REALIGN_BONES"),
                50, H, 390, 20,
                self.config["REALIGN_BONES"])
            H -= 20
            self.guiElements["IMPORT_SENDBONESTOBINDPOS"] = Draw.Toggle(
                "Send Bones To Bind Position",
                self.eventId("IMPORT_SENDBONESTOBINDPOS"),
                50, H, 390, 20,
                self.config["IMPORT_SENDBONESTOBINDPOS"])
            H -= 20
            self.guiElements["IMPORT_APPLYSKINDEFORM"] = Draw.Toggle(
                "Apply Skin Deformation",
                self.eventId("IMPORT_APPLYSKINDEFORM"),
                50, H, 390, 20,
                self.config["IMPORT_APPLYSKINDEFORM"])
            H -= 30
            
            self.guiElements["IMPORT_SKELETON"] = Draw.Toggle(
                "Import Skeleton Only + Parent Selected",
                self.eventId("IMPORT_SKELETON"),
                50, H, 390, 20,
                self.config["IMPORT_SKELETON"])
            H -= 30

        # export-only options
        if self.target == self.TARGET_EXPORT:
            self.guiElements["EXPORT_ANIMATION_0"] = Draw.Toggle(
                "Export Geometry + Animation (.nif)",
                self.eventId("EXPORT_ANIMATION_0"),
                50, H, 390, 20, self.config["EXPORT_ANIMATION"] == 0)
            self.guiElements["EXPORT_ANIMATION_1"] = Draw.Toggle(
                "Export Geometry Only (.nif)",
                self.eventId("EXPORT_ANIMATION_1"),
                50, H-20, 390, 20,
                self.config["EXPORT_ANIMATION"] == 1)
            self.guiElements["EXPORT_ANIMATION_2"] = Draw.Toggle(
                "Export Animation Only (.kf) - MORROWIND ONLY FOR NOW",
                self.eventId("EXPORT_ANIMATION_2"),
                50, H-40, 390, 20,
                self.config["EXPORT_ANIMATION"] == 2)
            H -= 70

            self.guiElements["EXPORT_FORCEDDS"] = Draw.Toggle(
                "Force DDS Extension",
                self.eventId("EXPORT_FORCEDDS"),
                50, H, 390, 20,
                self.config["EXPORT_FORCEDDS"])
            H -= 30

            self.guiElements["EXPORT_STRIPIFY"] = Draw.Toggle(
                "Stripify Geometries",
                self.eventId("EXPORT_STRIPIFY"),
                50, H, 195, 20,
                self.config["EXPORT_STRIPIFY"])
            self.guiElements["EXPORT_STITCHSTRIPS"] = Draw.Toggle(
                "Stitch Strips",
                self.eventId("EXPORT_STITCHSTRIPS"),
                245, H, 195, 20,
                self.config["EXPORT_STITCHSTRIPS"])
            H -= 30

            self.guiElements["EXPORT_SMOOTHOBJECTSEAMS"] = Draw.Toggle(
                "Smoothen Inter-Object Seams",
                self.eventId("EXPORT_SMOOTHOBJECTSEAMS"),
                50, H, 390, 20,
                self.config["EXPORT_SMOOTHOBJECTSEAMS"])
            H -= 30

            self.guiElements["EXPORT_FLATTENSKIN"] = Draw.Toggle(
                "Flatten Skin", self.eventId("EXPORT_FLATTENSKIN"),
                50, H, 390, 20,
                self.config["EXPORT_FLATTENSKIN"])
            self.guiElements["EXPORT_SKINPARTITION"] = Draw.Toggle(
                "Export Skin Partition",
                self.eventId("EXPORT_SKINPARTITION"),
                50, H-20, 130, 20,
                self.config["EXPORT_SKINPARTITION"])
            self.guiElements["EXPORT_PADBONES"] = Draw.Toggle(
                "Pad & Sort Bones",
                self.eventId("EXPORT_PADBONES"),
                180, H-20, 130, 20,
                self.config["EXPORT_PADBONES"])
            self.guiElements["EXPORT_BONESPERPARTITION"] = Draw.Number(
                "Max Bones", self.eventId("EXPORT_BONESPERPARTITION"),
                310, H-20, 130, 20,
                self.config["EXPORT_BONESPERPARTITION"],
                4, 18, "maximum number of bones per partition", self.updateBonesPerPartition)
            # the value 4 does for all games, so let's not let user change it
            #self.guiElements["EXPORT_BONESPERVERTEX"] = Draw.Number("Max Bones Per Vertex", self.eventId("EXPORT_BONESPERVERTEX"), 50, H-65, 390, 20, self.config["EXPORT_BONESPERVERTEX"], 2, 8)
            H -= 50

            self.guiElements["EXPORT_BHKLISTSHAPE"] = Draw.Toggle(
                "Use bhkListShape",
                self.eventId("EXPORT_BHKLISTSHAPE"),
                50, H, 195, 20,
                self.config["EXPORT_BHKLISTSHAPE"])
            self.guiElements["EXPORT_MOPP"] = Draw.Toggle(
                "Export Mopp (EXPERIMENTAL)",
                self.eventId("EXPORT_MOPP"),
                245, H, 195, 20,
                self.config["EXPORT_MOPP"])
            H -= 30

            #self.guiElements["NIF_EXPORT_PATH"]        = Draw.String("",       self.eventId("NIF_EXPORT_PATH"),     50, H-100, 390, 20, self.config["NIF_EXPORT_PATH"],        390, "export path")
            #self.guiElements["BROWSE_EXPORT_PATH"]     = Draw.PushButton('...',self.eventId("BROWSE_EXPORT_PATH"), 440, H-100,  30, 20)
            
            games_list = sorted(NifFormat.games.keys())
            versions_list = sorted(NifFormat.versions.keys(), key=lambda x: NifFormat.versions[x])
            V = 50
            HH = H
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
            H = HH - 20 - 20*min(MAXJ, max(len(NifFormat.versions), len(NifFormat.games)))
            H -= 30 # leave some space

        self.guiElements["OK"]     = Draw.PushButton(
            'Ok',
            self.eventId("OK"),
            50,  H, 100, 20)
        self.guiElements["CANCEL"] = Draw.PushButton(
            'Cancel',
            self.eventId("CANCEL"),
            180, H, 100, 20)

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
        elif evName == "REALIGN_BONES":
            self.config["REALIGN_BONES"] = not self.config["REALIGN_BONES"]
        elif evName == "IMPORT_ANIMATION":
            self.config["IMPORT_ANIMATION"] = not self.config["IMPORT_ANIMATION"]
        elif evName == "IMPORT_SKELETON":
            self.config["IMPORT_SKELETON"] = not self.config["IMPORT_SKELETON"]
        elif evName == "IMPORT_SENDBONESTOBINDPOS":
            self.config["IMPORT_SENDBONESTOBINDPOS"] = not self.config["IMPORT_SENDBONESTOBINDPOS"]
        elif evName == "IMPORT_APPLYSKINDEFORM":
            self.config["IMPORT_APPLYSKINDEFORM"] = not self.config["IMPORT_APPLYSKINDEFORM"]
        elif evName[:5] == "GAME_":
            self.config["EXPORT_VERSION"] = evName[5:]
            # set default settings per game
            if self.config["EXPORT_VERSION"] == "Morrowind":
                self.config["EXPORT_STRIPIFY"] = False
                self.config["EXPORT_STITCHSTRIPS"] = False
                self.config["EXPORT_ANIMATION"] = 1
                self.config["EXPORT_FLATTENSKIN"] = False
                self.config["EXPORT_SKINPARTITION"] = False
                self.config["EXPORT_PADBONES"] = False
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_MOPP"] = False
            if self.config["EXPORT_VERSION"] == "Freedom Force vs. the 3rd Reich":
                self.config["EXPORT_STRIPIFY"] = False
                self.config["EXPORT_STITCHSTRIPS"] = False
                self.config["EXPORT_ANIMATION"] = 1
                self.config["EXPORT_FLATTENSKIN"] = False
                self.config["EXPORT_BONESPERPARTITION"] = 4
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = True
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_MOPP"] = False
            elif self.config["EXPORT_VERSION"] == "Civilization IV":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_ANIMATION"] = 1
                self.config["EXPORT_FLATTENSKIN"] = False
                self.config["EXPORT_BONESPERPARTITION"] = 4
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = False
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_MOPP"] = False
            elif self.config["EXPORT_VERSION"] == "Oblivion":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_ANIMATION"] = 1
                self.config["EXPORT_FLATTENSKIN"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = False
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_MOPP"] = False
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
