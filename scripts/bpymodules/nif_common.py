"""Common functions for the Blender nif import and export scripts."""

__version__ = "2.5.0"
__requiredpyffiversion__ = "2.0.4"
__requiredblenderversion__ = "245"

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2009, NIF File Format Library and Tools
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

# utility functions
    
def cmp_versions(version1, version2):
    """Compare version strings."""
    def version_intlist(version):
        """Convert version string to list of integers."""
        return [int(x) for x in version.__str__().split(".")]
    return cmp(version_intlist(version1), version_intlist(version2))

# things to do on import and export

# check Blender version

import Blender
__blenderversion__ = Blender.Get('version')

if cmp_versions(__blenderversion__, __requiredblenderversion__) == -1:
    print("""--------------------------
ERROR\nThis script requires Blender %s or higher.
It seems that you have an older version installed (%s).
Get a newer version at http://www.blender.org/
--------------------------"""%(__requiredblenderversion__, __blenderversion__))
    Blender.Draw.PupMenu("ERROR%t|Blender outdated, check console for details")
    raise ImportError

# check if PyFFI is installed and import NifFormat

try:
    from pyffi import __version__ as __pyffiversion__
except ImportError:
    print("""--------------------------
ERROR\nThis script requires the Python File Format Interface (PyFFI).
Make sure that PyFFI resides in your Python path or in your Blender scripts folder.
If you do not have it: http://pyffi.sourceforge.net/
--------------------------""")
    Blender.Draw.PupMenu("ERROR%t|PyFFI not found, check console for details")
    raise

# check PyFFI version

if cmp_versions(__pyffiversion__, __requiredpyffiversion__) == -1:
    print("""--------------------------
ERROR\nThis script requires Python File Format Interface %s or higher.
It seems that you have an older version installed (%s).
Get a newer version at http://pyffi.sourceforge.net/
--------------------------"""%(__requiredpyffiversion__, __pyffiversion__))
    Blender.Draw.PupMenu("ERROR%t|PyFFI outdated, check console for details")
    raise ImportError

# import PyFFI format classes

from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat

# other imports

from Blender import Draw, Registry
import logging
import sys
import os

def init_loggers():
    """Set up loggers."""
    niftoolslogger = logging.getLogger("niftools")
    niftoolslogger.setLevel(logging.WARNING)
    pyffilogger = logging.getLogger("pyffi")
    pyffilogger.setLevel(logging.WARNING)
    loghandler = logging.StreamHandler()
    loghandler.setLevel(logging.DEBUG)
    logformatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
    loghandler.setFormatter(logformatter)
    niftoolslogger.addHandler(loghandler)
    pyffilogger.addHandler(loghandler)

# set up the loggers: call it as a function to avoid polluting namespace
init_loggers()

class NifImportExport:
    """Abstract base class for import and export. Contains utility functions
    that are commonly used in both import and export."""

    EXTRA_SHADER_TEXTURES = [
        "EnvironmentMapIndex",
        "NormalMapIndex",
        "SpecularIntensityIndex",
        "EnvironmentIntensityIndex",
        "LightCubeMapIndex",
        "ShadowTextureIndex"]
    """Names (ordered by default index) of shader texture slots for
    Sid Meier's Railroads and similar games.
    """

    USED_EXTRA_SHADER_TEXTURES = {
        "Sid Meier's Railroads": (3, 0, 4, 1, 5, 2),
        "Civilization IV": (3, 0, 1, 2)}
    """The default ordering of the extra data blocks for different games."""

    progress_bar = 0
    """Level of the progress bar."""

    def msg_progress(self, message, progbar=None):
        """Message wrapper for the Blender progress bar."""
        # update progress bar level
        if progbar is None:
            if self.progress_bar > 0.89:
                # reset progress bar
                self.progress_bar = 0
                Blender.Window.DrawProgressBar(0, message)
            self.progress_bar += 0.1
        else:
            self.progress_bar = progbar
        # draw the progress bar
        Blender.Window.DrawProgressBar(self.progress_bar, message)

    def get_bone_name_for_blender(self, name):
        """Convert a bone name to a name that can be used by Blender: turns
        'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

        @param name: The bone name as in the nif file.
        @type name: C{str}
        @return: Bone name in Blender convention.
        @rtype: C{str}
        """
        if name.startswith("Bip01 L "):
            return "Bip01 " + name[8:] + ".L"
        elif name.startswith("Bip01 R "):
            return "Bip01 " + name[8:] + ".R"
        return name

    def get_bone_name_for_nif(self, name):
        """Convert a bone name to a name that can be used by the nif file:
        turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

        @param name: The bone name as in Blender.
        @type name: C{str}
        @return: Bone name in nif convention.
        @rtype: C{str}
        """
        if name.startswith("Bip01 "):
            if name.endswith(".L"):
                return "Bip01 L " + name[6:-2]
            elif name.endswith(".R"):
                return "Bip01 R " + name[6:-2]
        return name

    def get_extend_from_flags(self, flags):
        if flags & 6 == 4: # 0b100
            return Blender.IpoCurve.ExtendTypes.CONST
        elif flags & 6 == 0: # 0b000
            return Blender.IpoCurve.ExtendTypes.CYCLIC

        self.logger.warning(
            "Unsupported cycle mode in nif, using clamped.")
        return Blender.IpoCurve.ExtendTypes.CONST

    def get_flags_from_extend(self, extend):
        if extend == Blender.IpoCurve.ExtendTypes.CONST:
            return 4 # 0b100
        elif extend == Blender.IpoCurve.ExtendTypes.CYCLIC:
            return 0

        self.logger.warning(
            "Unsupported extend type in blend, using clamped.")
        return 4

class NifConfig:
    """Class which handles configuration of nif import and export in Blender.

    Important: keep every instance of this class in a global variable
    (otherwise gui elements might go out of skope which will crash
    Blender)."""
    # class global constants
    WELCOME_MESSAGE = 'Blender NIF Scripts %s (running on Blender %s, PyFFI %s)'%(__version__, __blenderversion__, __pyffiversion__)
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
        IMPORT_REALIGN_BONES = 1, # 0 = no, 1 = tail, 2 = tail+rotation
        IMPORT_ANIMATION = True,
        IMPORT_SCALE_CORRECTION = 0.1,
        EXPORT_SCALE_CORRECTION = 10.0, # 1/import scale correction
        IMPORT_TEXTURE_PATH = [],
        EXPORT_FLATTENSKIN = False,
        EXPORT_VERSION = 'Oblivion',
        EPSILON = 0.005, # used for checking equality with floats
        LOG_LEVEL = logging.WARNING, # log level
        IMPORT_SKELETON = 0, # 0 = normal import, 1 = import file as skeleton, 2 = import mesh and attach to skeleton
        IMPORT_KEYFRAMEFILE = '', # keyframe file for animations
        IMPORT_EGMFILE = '', # FaceGen EGM file for morphs
        IMPORT_EGMANIM = True, # create FaceGen EGM animation curves
        IMPORT_EGMANIMSCALE = 1.0, # scale of FaceGen EGM animation curves
        EXPORT_ANIMATION = 0, # export everything (1=geometry only, 2=animation only)
        EXPORT_ANIMSEQUENCENAME = '', # sequence name of the kf file
        EXPORT_FORCEDDS = True, # force dds extension on texture files
        EXPORT_SKINPARTITION = True, # generate skin partition
        EXPORT_BONESPERVERTEX = 4,
        EXPORT_BONESPERPARTITION = 18,
        EXPORT_PADBONES = False,
        EXPORT_STRIPIFY = True,
        EXPORT_STITCHSTRIPS = False,
        EXPORT_SMOOTHOBJECTSEAMS = True,
        IMPORT_MERGESKELETONROOTS = True,
        IMPORT_SENDGEOMETRIESTOBINDPOS = True,
        IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS = True,
        IMPORT_SENDBONESTOBINDPOS = True,
        IMPORT_APPLYSKINDEFORM = False,
        IMPORT_EXTRANODES = True,
        EXPORT_BHKLISTSHAPE = False,
        EXPORT_OB_BSXFLAGS = 2,
        EXPORT_OB_MASS = 10.0,
        EXPORT_OB_SOLID = True,
        EXPORT_OB_MOTIONSYSTEM = 7, # MO_SYS_FIXED
        EXPORT_OB_UNKNOWNBYTE1 = 1,
        EXPORT_OB_UNKNOWNBYTE2 = 1,
        EXPORT_OB_QUALITYTYPE = 1, # MO_QUAL_FIXED
        EXPORT_OB_WIND = 0,
        EXPORT_OB_LAYER = 1, # static
        EXPORT_OB_MATERIAL = 9, # wood
        EXPORT_OB_MALLEABLECONSTRAINT = False, # use malleable constraint for ragdoll and hinge
        EXPORT_OB_PRN = "NONE", # determines bone where to attach weapon
        EXPORT_FO3_SF_ZBUF = True, # use these shader flags?
        EXPORT_FO3_SF_SMAP = False,
        EXPORT_FO3_SF_SFRU = False,
        EXPORT_FO3_SF_WINDOW_ENVMAP = False,
        EXPORT_FO3_SF_EMPT = True,
        EXPORT_FO3_SF_UN31 = True,
        EXPORT_FO3_FADENODE = False,
        EXPORT_FO3_SHADER_TYPE = 1, # shader_default
        EXPORT_FO3_BODYPARTS = True,
        EXPORT_MW_NIFXNIFKF = False,
        EXPORT_EXTRA_SHADER_TEXTURES = True,
        PROFILE = '', # name of file where Python profiler dumps the profile; set to empty string to turn off profiling
        IMPORT_EXPORTEMBEDDEDTEXTURES = False,
        EXPORT_OPTIMIZE_MATERIALS = True,
        IMPORT_COMBINESHAPES = True)

    def __init__(self):
        """Initialize and load configuration."""
        # clears the console window
        if sys.platform in ('linux-i386','linux2'):
            os.system("clear")
        elif sys.platform in ('win32','dos','ms-dos'):
            os.system("cls")

        # print scripts info
        print self.WELCOME_MESSAGE

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
        configuration for incompatible values.
        """
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
               self.config["IMPORT_REALIGN_BONES"] = 1
            elif self.config["IMPORT_REALIGN_BONES"] == False:
               self.config["IMPORT_REALIGN_BONES"] = 0
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
        # special case: set log level here
        self.updateLogLevel("LOG_LEVEL", self.config["LOG_LEVEL"])

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

    def drawFileBrowse(self, text, event_name_prefix, val = None):
        """Create elements to select a file.

        Registers events PREFIX_ITEM, PREFIX_REMOVE, PREFIX_ADD."""
        if val is None:
            val = self.config[event_name_prefix]
        self.guiElements["%s_ITEM"%event_name_prefix]   = Draw.String(
            text,
            self.eventId("%s_ITEM"%event_name_prefix),
            self.xPos, self.yPos, self.XCOLUMNSKIP-50, self.YLINESKIP,
            val, 255)
        self.guiElements["%s_REMOVE"%event_name_prefix] = Draw.PushButton(
            'X',
            self.eventId("%s_REMOVE"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-50, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_ADD"%event_name_prefix]    = Draw.PushButton(
            '...',
            self.eventId("%s_ADD"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-30, self.yPos, 30, self.YLINESKIP)
        self.yPos -= self.YLINESKIP

    def drawString(self, text, event_name, max_length, callback, val = None,
                   num_items = 1, item = 0):
        """Create elements to input a string."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.String(
            text,
            self.eventId(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val,
            max_length,
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
        self.drawLabel(
            text = self.WELCOME_MESSAGE,
            event_name = "LABEL_WELCOME_MESSAGE")
        self.drawYSep()

        self.drawNumber(
            text = "Log Level",
            event_name = "LOG_LEVEL",
            min_val = 0, max_val = 99,
            callback = self.updateLogLevel,
            num_items = 4, item = 0)
        self.drawPushButton(
            text = "Warn",
            event_name = "LOG_LEVEL_WARN",
            num_items = 4, item = 1)
        self.drawPushButton(
            text = "Info",
            event_name = "LOG_LEVEL_INFO",
            num_items = 4, item = 2)
        self.drawPushButton(
            text = "Debug",
            event_name = "LOG_LEVEL_DEBUG",
            num_items = 4, item = 3)
        self.drawYSep()

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
                text = "Import Extra Nodes",
                event_name = "IMPORT_EXTRANODES")
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

            self.drawToggle(
                text = "Save Embedded Textures As DDS",
                event_name = "IMPORT_EXPORTEMBEDDEDTEXTURES")
            self.drawYSep()

            self.drawToggle(
                text = "Combine Multi-Material Shapes Into Single Mesh",
                event_name = "IMPORT_COMBINESHAPES")
            self.drawYSep()

            self.drawLabel(
                text = "Keyframe File:",
                event_name = "IMPORT_KEYFRAMEFILE_TEXT")
            self.drawFileBrowse(
                text = "",
                event_name_prefix = "IMPORT_KEYFRAMEFILE")
            self.drawYSep()

            self.drawLabel(
                text = "FaceGen EGM File:",
                event_name = "IMPORT_EGMFILE_TEXT")
            self.drawFileBrowse(
                text = "",
                event_name_prefix = "IMPORT_EGMFILE")
            self.drawToggle(
                text="Animate",
                event_name="IMPORT_EGMANIM",
                num_items=2, item=0)
            self.drawSlider(
                text="Scale:  ",
                event_name="IMPORT_EGMANIMSCALE",
                val=self.config["IMPORT_EGMANIMSCALE"],
                min_val=0.01, max_val=100.0,
                callback=self.updateEgmAnimScale,
                num_items=2, item=1)
            self.drawYSep()

            self.drawPushButton(
                text = "Restore Default Settings",
                event_name = "IMPORT_SETTINGS_DEFAULT")
            self.drawYSep()

            self.drawLabel(
                text = "... and if skinning fails with default settings:",
                event_name = "IMPORT_SETTINGS_SKINNING_TEXT")
            self.drawPushButton(
                text = "Use The Force Luke",
                event_name = "IMPORT_SETTINGS_SKINNING")
            self.drawYSep()

        # export-only options
        if self.target == self.TARGET_EXPORT:
            self.drawToggle(
                text = "Export Geometry + Animation (.nif)",
                event_name = "EXPORT_ANIMATION_0",
                val = ((self.config["EXPORT_ANIMATION"] == 0)
                       or self.config["EXPORT_MW_NIFXNIFKF"]))
            self.drawToggle(
                text = "Export Geometry Only (.nif)",
                event_name = "EXPORT_ANIMATION_1",
                val = ((self.config["EXPORT_ANIMATION"] == 1)
                       or self.config["EXPORT_MW_NIFXNIFKF"]))
            self.drawToggle(
                text = "Export Animation Only (.kf)",
                event_name = "EXPORT_ANIMATION_2",
                val = ((self.config["EXPORT_ANIMATION"] == 2)
                       or self.config["EXPORT_MW_NIFXNIFKF"]))
            self.drawYSep()

            self.drawString(
                text = "Anim Seq Name: ",
                event_name = "EXPORT_ANIMSEQUENCENAME",
                max_length = 128,
                callback = self.updateAnimSequenceName)
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

            self.drawToggle(
                text = "Combine Materials to Increase Performance",
                event_name = "EXPORT_OPTIMIZE_MATERIALS")
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

        # advanced import settings
        if self.target == self.TARGET_IMPORT:
            self.drawNextColumn()

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
                text="Merge Skeleton Roots",
                event_name="IMPORT_MERGESKELETONROOTS")
            self.drawToggle(
                text="Send Geometries To Bind Position",
                event_name="IMPORT_SENDGEOMETRIESTOBINDPOS")
            self.drawToggle(
                text="Send Detached Geometries To Node Position",
                event_name="IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS")
            self.drawToggle(
                text="Send Bones To Bind Position",
                event_name="IMPORT_SENDBONESTOBINDPOS")
            self.drawToggle(
                text = "Apply Skin Deformation",
                event_name = "IMPORT_APPLYSKINDEFORM")
            self.drawYSep()

        # export-only options for oblivion/fallout 3

        if (self.target == self.TARGET_EXPORT
            and self.config["EXPORT_VERSION"] in ("Oblivion", "Fallout 3")):
            self.drawNextColumn()
            
            self.drawLabel(
                text = "Collision Options",
                event_name = "EXPORT_OB_COLLISIONHTML")
            self.drawPushButton(
                text = "Static",
                event_name = "EXPORT_OB_RIGIDBODY_STATIC",
                num_items = 5, item = 0)
            self.drawPushButton(
                text = "Anim Static",
                event_name = "EXPORT_OB_RIGIDBODY_ANIMATED",
                num_items = 5, item = 1)
            self.drawPushButton(
                text = "Clutter",
                event_name = "EXPORT_OB_RIGIDBODY_CLUTTER",
                num_items = 5, item = 2)
            self.drawPushButton(
                text = "Weapon",
                event_name = "EXPORT_OB_RIGIDBODY_WEAPON",
                num_items = 5, item = 3)
            self.drawPushButton(
                text = "Creature",
                event_name = "EXPORT_OB_RIGIDBODY_CREATURE",
                num_items = 5, item = 4)
            self.drawToggle(
                text = "Stone",
                event_name = "EXPORT_OB_MATERIAL_STONE",
                val = self.config["EXPORT_OB_MATERIAL"] == 0,
                num_items = 6, item = 0)
            self.drawToggle(
                text = "Cloth",
                event_name = "EXPORT_OB_MATERIAL_CLOTH",
                val = self.config["EXPORT_OB_MATERIAL"] == 1,
                num_items = 6, item = 1)
            self.drawToggle(
                text = "Glass",
                event_name = "EXPORT_OB_MATERIAL_GLASS",
                val = self.config["EXPORT_OB_MATERIAL"] == 3,
                num_items = 6, item = 2)
            self.drawToggle(
                text = "Metal",
                event_name = "EXPORT_OB_MATERIAL_METAL",
                val = self.config["EXPORT_OB_MATERIAL"] == 5,
                num_items = 6, item = 3)
            self.drawToggle(
                text = "Skin",
                event_name = "EXPORT_OB_MATERIAL_SKIN",
                val = self.config["EXPORT_OB_MATERIAL"] == 7,
                num_items = 6, item = 4)
            self.drawToggle(
                text = "Wood",
                event_name = "EXPORT_OB_MATERIAL_WOOD",
                val = self.config["EXPORT_OB_MATERIAL"] == 9,
                num_items = 6, item = 5)
            self.drawNumber(
                text = "Material:  ",
                event_name = "EXPORT_OB_MATERIAL",
                min_val = 0, max_val = 30,
                callback = self.updateObMaterial)
            self.drawNumber(
                text = "BSX Flags:  ",
                event_name = "EXPORT_OB_BSXFLAGS",
                min_val = 0, max_val = 63,
                callback = self.updateObBSXFlags,
                num_items = 2, item = 0)
            self.drawSlider(
                text = "Mass:  ",
                event_name = "EXPORT_OB_MASS",
                min_val = 0.1, max_val = 1500.0,
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
            self.drawYSep()

            self.drawToggle(
                text = "Use bhkListShape",
                event_name = "EXPORT_BHKLISTSHAPE",
                num_items = 2, item = 0)
            self.drawToggle(
                text = "Use bhkMalleableConstraint",
                event_name = "EXPORT_OB_MALLEABLECONSTRAINT",
                num_items = 2, item = 1)
            self.drawYSep()

            self.drawLabel(
                text = "Weapon Body Location",
                event_name = "LABEL_WEAPON_LOCATION")
            self.drawToggle(
                text = "None",
                val = self.config["EXPORT_OB_PRN"] == "NONE",
                event_name = "EXPORT_OB_PRN_NONE",
                num_items = 7, item = 0)
            self.drawToggle(
                text = "Back",
                val = self.config["EXPORT_OB_PRN"] == "BACK",
                event_name = "EXPORT_OB_PRN_BACK",
                num_items = 7, item = 1)
            self.drawToggle(
                text = "Side",
                val = self.config["EXPORT_OB_PRN"] == "SIDE",
                event_name = "EXPORT_OB_PRN_SIDE",
                num_items = 7, item = 2)
            self.drawToggle(
                text = "Quiver",
                val = self.config["EXPORT_OB_PRN"] == "QUIVER",
                event_name = "EXPORT_OB_PRN_QUIVER",
                num_items = 7, item = 3)
            self.drawToggle(
                text = "Shield",
                val = self.config["EXPORT_OB_PRN"] == "SHIELD",
                event_name = "EXPORT_OB_PRN_SHIELD",
                num_items = 7, item = 4)
            self.drawToggle(
                text = "Helm",
                val = self.config["EXPORT_OB_PRN"] == "HELM",
                event_name = "EXPORT_OB_PRN_HELM",
                num_items = 7, item = 5)
            self.drawToggle(
                text = "Ring",
                val = self.config["EXPORT_OB_PRN"] == "RING",
                event_name = "EXPORT_OB_PRN_RING",
                num_items = 7, item = 6)
            self.drawYSep()

        # export-only options for morrowind
        if (self.target == self.TARGET_EXPORT
            and self.config["EXPORT_VERSION"] == "Morrowind"):
            self.drawNextColumn()

            self.drawToggle(
                text = "Export nif + xnif + kf",
                event_name = "EXPORT_MW_NIFXNIFKF")

        # export-only options for civ4 and rrt
        if (self.target == self.TARGET_EXPORT
            and (self.config["EXPORT_VERSION"]
                 in NifImportExport.USED_EXTRA_SHADER_TEXTURES)):
            self.drawNextColumn()

            self.drawToggle(
                text = "Export Extra Shader Textures",
                event_name = "EXPORT_EXTRA_SHADER_TEXTURES")

        # export-only options for fallout 3
        if (self.target == self.TARGET_EXPORT
            and self.config["EXPORT_VERSION"] == "Fallout 3"):
            self.drawNextColumn()

            self.drawLabel(
                text = "Shader Options",
                event_name = "LABEL_FO3_SHADER_OPTIONS")
            self.drawPushButton(
                text = "Default",
                event_name = "EXPORT_FO3_SHADER_OPTION_DEFAULT",
                num_items = 3, item = 0)
            self.drawPushButton(
                text = "Skin",
                event_name = "EXPORT_FO3_SHADER_OPTION_SKIN",
                num_items = 3, item = 1)
            self.drawPushButton(
                text = "Cloth",
                event_name = "EXPORT_FO3_SHADER_OPTION_CLOTH",
                num_items = 3, item = 2)
            self.drawToggle(
                text = "Default Type",
                val = self.config["EXPORT_FO3_SHADER_TYPE"] == 1,
                event_name = "EXPORT_FO3_SHADER_TYPE_DEFAULT",
                num_items = 2, item = 0)
            self.drawToggle(
                text = "Skin Type",
                val = self.config["EXPORT_FO3_SHADER_TYPE"] == 14,
                event_name = "EXPORT_FO3_SHADER_TYPE_SKIN",
                num_items = 2, item = 1)
            self.drawToggle(
                text = "Z Buffer",
                event_name = "EXPORT_FO3_SF_ZBUF",
                num_items = 3, item = 0)
            self.drawToggle(
                text = "Shadow Map",
                event_name = "EXPORT_FO3_SF_SMAP",
                num_items = 3, item = 1)
            self.drawToggle(
                text = "Shadow Frustum",
                event_name = "EXPORT_FO3_SF_SFRU",
                num_items = 3, item = 2)
            self.drawToggle(
                text = "Window Envmap",
                event_name = "EXPORT_FO3_SF_WINDOW_ENVMAP",
                num_items = 3, item = 0)
            self.drawToggle(
                text = "Empty",
                event_name = "EXPORT_FO3_SF_EMPT",
                num_items = 3, item = 1)
            self.drawToggle(
                text = "Unknown 31",
                event_name = "EXPORT_FO3_SF_UN31",
                num_items = 3, item = 2)
            self.drawYSep()

            self.drawToggle(
                text = "Use BSFadeNode Root",
                event_name = "EXPORT_FO3_FADENODE")
            self.drawYSep()

            self.drawToggle(
                text = "Export Dismember Body Parts",
                event_name = "EXPORT_FO3_BODYPARTS")
            self.drawYSep()

        # is this needed?
        #Draw.Redraw(1)

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

        elif evName == "IMPORT_KEYFRAMEFILE_ADD":
            kffile = self.config["IMPORT_KEYFRAMEFILE"]
            if not kffile:
                kffile = Blender.sys.dirname(self.config["IMPORT_FILE"])
            # browse and add keyframe file
            Blender.Window.FileSelector(
                self.selectKeyframeFile, "Select Keyframe File", kffile)
            self.config["IMPORT_ANIMATION"] = True
        elif evName == "IMPORT_KEYFRAMEFILE_REMOVE":
            self.config["IMPORT_KEYFRAMEFILE"] = ''
            self.config["IMPORT_ANIMATION"] = False

        elif evName == "IMPORT_EGMFILE_ADD":
            egmfile = self.config["IMPORT_EGMFILE"]
            if not egmfile:
                egmfile = self.config["IMPORT_FILE"][:-3] + "egm"
            # browse and add egm file
            Blender.Window.FileSelector(
                self.selectEgmFile, "Select FaceGen EGM File", egmfile)
        elif evName == "IMPORT_EGMFILE_REMOVE":
            self.config["IMPORT_EGMFILE"] = ''

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
        elif evName == "IMPORT_MERGESKELETONROOTS":
            self.config["IMPORT_MERGESKELETONROOTS"] = not self.config["IMPORT_MERGESKELETONROOTS"]
        elif evName == "IMPORT_SENDGEOMETRIESTOBINDPOS":
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = not self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"]
        elif evName == "IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS":
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = not self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"]
        elif evName == "IMPORT_SENDBONESTOBINDPOS":
            self.config["IMPORT_SENDBONESTOBINDPOS"] = not self.config["IMPORT_SENDBONESTOBINDPOS"]
        elif evName == "IMPORT_APPLYSKINDEFORM":
            self.config["IMPORT_APPLYSKINDEFORM"] = not self.config["IMPORT_APPLYSKINDEFORM"]
        elif evName == "IMPORT_EXTRANODES":
            self.config["IMPORT_EXTRANODES"] = not self.config["IMPORT_EXTRANODES"]
        elif evName == "IMPORT_EXPORTEMBEDDEDTEXTURES":
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = not self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"]
        elif evName == "IMPORT_COMBINESHAPES":
            self.config["IMPORT_COMBINESHAPES"] = not self.config["IMPORT_COMBINESHAPES"]
        elif evName == "IMPORT_EGMANIM":
            self.config["IMPORT_EGMANIM"] = not self.config["IMPORT_EGMANIM"]
        elif evName == "IMPORT_SETTINGS_DEFAULT":
            self.config["IMPORT_ANIMATION"] = True
            self.config["IMPORT_SKELETON"] = 0
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = False
            self.config["IMPORT_COMBINESHAPES"] = True
            self.config["IMPORT_REALIGN_BONES"] = 1
            self.config["IMPORT_MERGESKELETONROOTS"] = True
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = True
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = True
            self.config["IMPORT_SENDBONESTOBINDPOS"] = True
            self.config["IMPORT_APPLYSKINDEFORM"] = False
            self.config["IMPORT_EXTRANODES"] = True
            self.config["IMPORT_EGMFILE"] = ''
            self.config["IMPORT_EGMANIM"] = True
            self.config["IMPORT_EGMANIMSCALE"] = 1.0
        elif evName == "IMPORT_SETTINGS_SKINNING":
            self.config["IMPORT_ANIMATION"] = True
            self.config["IMPORT_SKELETON"] = 0
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = False
            self.config["IMPORT_COMBINESHAPES"] = True
            self.config["IMPORT_REALIGN_BONES"] = 1
            self.config["IMPORT_MERGESKELETONROOTS"] = True
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = False
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = False
            self.config["IMPORT_SENDBONESTOBINDPOS"] = False
            self.config["IMPORT_APPLYSKINDEFORM"] = True
            self.config["IMPORT_EXTRANODES"] = True
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
            self.config["EXPORT_MW_NIFXNIFKF"] = False
            self.config["EXPORT_EXTRA_SHADER_TEXTURES"] = True
            # set default settings per game
            if self.config["EXPORT_VERSION"] == "Morrowind":
                pass # fail-safe settings work
            if self.config["EXPORT_VERSION"] == "Freedom Force vs. the 3rd Reich":
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = True
            elif self.config["EXPORT_VERSION"] == "Civilization IV":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
            elif self.config["EXPORT_VERSION"] in ("Oblivion", "Fallout 3"):
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_FLATTENSKIN"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
                # oblivion specific settings
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_OB_MATERIAL"] = 9 # wood
                self.config["EXPORT_OB_MALLEABLECONSTRAINT"] = False
                # rigid body: static
                self.config["EXPORT_OB_BSXFLAGS"] = 2
                self.config["EXPORT_OB_MASS"] = 1000.0
                self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # MO_SYS_FIXED
                self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
                self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
                self.config["EXPORT_OB_QUALITYTYPE"] = 1 # MO_QUAL_FIXED
                self.config["EXPORT_OB_WIND"] = 0
                self.config["EXPORT_OB_LAYER"] = 1 # static
                # shader options
                self.config["EXPORT_FO3_SHADER_TYPE"] = 1
                self.config["EXPORT_FO3_SF_ZBUF"] = True
                self.config["EXPORT_FO3_SF_SMAP"] = False
                self.config["EXPORT_FO3_SF_SFRU"] = False
                self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
                self.config["EXPORT_FO3_SF_EMPT"] = True
                self.config["EXPORT_FO3_SF_UN31"] = True
                # body parts
                self.config["EXPORT_FO3_BODYPARTS"] = True
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
             elif value == 1:
                 # enable flattening skin for 'geometry only' exports
                 # in oblivion and fallout 3
                 if self.config["EXPORT_VERSION"] in ("Oblivion", "Fallout 3"):
                     self.config["EXPORT_FLATTENSKIN"] = True
        elif evName == "EXPORT_SKINPARTITION":
            self.config["EXPORT_SKINPARTITION"] = not self.config["EXPORT_SKINPARTITION"]
        elif evName == "EXPORT_PADBONES":
            self.config["EXPORT_PADBONES"] = not self.config["EXPORT_PADBONES"]
            if self.config["EXPORT_PADBONES"]: # bones are padded
                self.config["EXPORT_BONESPERPARTITION"] = 4 # force 4 bones per partition
        elif evName == "EXPORT_BHKLISTSHAPE":
            self.config["EXPORT_BHKLISTSHAPE"] = not self.config["EXPORT_BHKLISTSHAPE"]
        elif evName == "EXPORT_OB_MALLEABLECONSTRAINT":
            self.config["EXPORT_OB_MALLEABLECONSTRAINT"] = not self.config["EXPORT_OB_MALLEABLECONSTRAINT"]
        elif evName == "EXPORT_OB_SOLID":
            self.config["EXPORT_OB_SOLID"] = True
        elif evName == "EXPORT_OB_HOLLOW":
            self.config["EXPORT_OB_SOLID"] = False
        elif evName == "EXPORT_OB_RIGIDBODY_STATIC":
            self.config["EXPORT_OB_MATERIAL"] = 0 # stone
            self.config["EXPORT_OB_BSXFLAGS"] = 2 # havok
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # MO_SYS_FIXED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
            self.config["EXPORT_OB_QUALITYTYPE"] = 1 # MO_QUAL_FIXED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 1 # static
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_ANIMATED": # see fencedoor01.nif
            self.config["EXPORT_OB_MATERIAL"] = 0 # stone
            self.config["EXPORT_OB_BSXFLAGS"] = 11 # havok + anim + unknown
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 6 # MO_SYS_KEYFRAMED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 2 # MO_QUAL_KEYFRAMED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 2 # OL_ANIM_STATIC
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_CLUTTER":
            self.config["EXPORT_OB_BSXFLAGS"] = 3 # anim + havok
            self.config["EXPORT_OB_MASS"] = 10.0 # typical
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 4 # MO_SYS_BOX
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 3 # MO_QUAL_DEBRIS
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 4 # clutter
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_WEAPON":
            self.config["EXPORT_OB_MATERIAL"] = 5 # metal
            self.config["EXPORT_OB_BSXFLAGS"] = 3 # anim + havok
            self.config["EXPORT_OB_MASS"] = 25.0 # typical
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 4 # MO_SYS_BOX
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 3 # MO_QUAL_DEBRIS
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 5 # weapin
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "SIDE"
        elif evName == "EXPORT_OB_RIGIDBODY_CREATURE":
            self.config["EXPORT_OB_MATERIAL"] = 7 # skin
            self.config["EXPORT_OB_BSXFLAGS"] = 7 # anim + havok + skeleton
            self.config["EXPORT_OB_MASS"] = 600.0 # single person's weight in Oblivion
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 6 # MO_SYS_KEYFRAMED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 2 # MO_QUAL_KEYFRAMED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 8 # biped
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_MATERIAL_STONE":
            self.config["EXPORT_OB_MATERIAL"] = 0
        elif evName == "EXPORT_OB_MATERIAL_CLOTH":
            self.config["EXPORT_OB_MATERIAL"] = 1
        elif evName == "EXPORT_OB_MATERIAL_GLASS":
            self.config["EXPORT_OB_MATERIAL"] = 3
        elif evName == "EXPORT_OB_MATERIAL_METAL":
            self.config["EXPORT_OB_MATERIAL"] = 5
        elif evName == "EXPORT_OB_MATERIAL_SKIN":
            self.config["EXPORT_OB_MATERIAL"] = 7
        elif evName == "EXPORT_OB_MATERIAL_WOOD":
            self.config["EXPORT_OB_MATERIAL"] = 9
        elif evName[:14] == "EXPORT_OB_PRN_":
            self.config["EXPORT_OB_PRN"] = evName[14:]
        elif evName == "EXPORT_OPTIMIZE_MATERIALS":
            self.config["EXPORT_OPTIMIZE_MATERIALS"] = not self.config["EXPORT_OPTIMIZE_MATERIALS"]
        elif evName == "LOG_LEVEL_WARN":
            self.updateLogLevel(evName, logging.WARNING)
        elif evName == "LOG_LEVEL_INFO":
            self.updateLogLevel(evName, logging.INFO)
        elif evName == "LOG_LEVEL_DEBUG":
            self.updateLogLevel(evName, logging.DEBUG)
        elif evName == "EXPORT_FO3_FADENODE":
            self.config["EXPORT_FO3_FADENODE"] = not self.config["EXPORT_FO3_FADENODE"]
        elif evName.startswith("EXPORT_FO3_SF_"):
            self.config[evName] = not self.config[evName]
        elif evName == "EXPORT_FO3_SHADER_TYPE_DEFAULT":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
        elif evName == "EXPORT_FO3_SHADER_TYPE_SKIN":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 14
        elif evName == "EXPORT_FO3_SHADER_OPTION_DEFAULT":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = False
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_SHADER_OPTION_SKIN":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 14
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = True
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = True
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_SHADER_OPTION_CLOTH":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = True
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_BODYPARTS":
            self.config["EXPORT_FO3_BODYPARTS"] = not self.config["EXPORT_FO3_BODYPARTS"]
        elif evName == "EXPORT_MW_NIFXNIFKF":
            self.config["EXPORT_MW_NIFXNIFKF"] = not self.config["EXPORT_MW_NIFXNIFKF"]
        elif evName == "EXPORT_EXTRA_SHADER_TEXTURES":
            self.config["EXPORT_EXTRA_SHADER_TEXTURES"] = not self.config["EXPORT_EXTRA_SHADER_TEXTURES"]
        Draw.Redraw(1)

    def guiEvent(self, evt, val):
        """Event handler for GUI elements."""

        if evt == Draw.ESCKEY:
            self.callback = None
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

    def selectKeyframeFile(self, keyframefile):
        if keyframefile == '' or not Blender.sys.exists(keyframefile):
            Draw.PupMenu('No file selected or file does not exist%t|Ok')
        else:
            self.config["IMPORT_KEYFRAMEFILE"] = keyframefile

    def selectEgmFile(self, egmfile):
        if egmfile == '' or not Blender.sys.exists(egmfile):
            Draw.PupMenu('No file selected or file does not exist%t|Ok')
        else:
            self.config["IMPORT_EGMFILE"] = egmfile

    def updateLogLevel(self, evt, val):
        self.config["LOG_LEVEL"] = val
        logging.getLogger("niftools").setLevel(val)
        logging.getLogger("pyffi").setLevel(val)

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

    def updateAnimSequenceName(self, evt, val):
        self.config["EXPORT_ANIMSEQUENCENAME"] = val

    def updateEgmAnimScale(self, evt, val):
        self.config["IMPORT_EGMANIMSCALE"] = val
