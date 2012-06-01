'''Blender operators, functions called through menus'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2011, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper

import site
import pyffi
from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat

from . import export_nif, import_nif

class NifOperatorCommon:
    """Abstract base class for import and export user interface."""

    # filepath is created by ImportHelper/ExportHelper

    #: Default file name extension.
    filename_ext = ".nif"

    #: File name filter for file select dialog.
    filter_glob = bpy.props.StringProperty(
        default="*.nif;*.item;*.nifcache;*.jmi", options={'HIDDEN'})

    #: Level of verbosity on the console.
    log_level = bpy.props.EnumProperty(
        items=(
            ("DEBUG", "Debug",
             "Show all messages (only useful for debugging)."),
            ("INFO", "Info",
             "Show some informative messages, warnings, and errors."),
            ("WARNING", "Warning",
             "Only show warnings and errors."),
            ("ERROR", "Error",
             "Only show errors."),
            ("CRITICAL", "Critical",
             "Only show extremely critical errors."),
            ),
        name="Log Level",
        description="Level of verbosity on the console.",
        default="WARNING")

    #: Name of file where Python profiler dumps the profile.
    profile_path = bpy.props.StringProperty(
        name="Profile Path",
        description=
        "Name of file where Python profiler dumps the profile."
        " Set to empty string to turn off profiling.",
        maxlen=1024,
        default="",
        subtype="FILE_PATH",
        options={'HIDDEN'})

    #: Number of nif units per blender unit.
    scale_correction = bpy.props.FloatProperty(
        name="Scale Correction",
        description="Number of nif units per blender unit.",
        default=10.0,
        min=0.01, max=100.0, precision=2)

    #: Used for checking equality between floats.
    epsilon = bpy.props.FloatProperty(
        name="Epsilon",
        description="Used for checking equality between floats.",
        default=0.005,
        min=0.0, max=1.0, precision=5,
        options={'HIDDEN'})

class NifImportOperator(bpy.types.Operator, ImportHelper, NifOperatorCommon):
    """Operator for loading a nif file."""

    #: Name of function for calling the nif export operator.
    bl_idname = "import_scene.nif"

    #: How the nif import operator is labelled in the user interface.
    bl_label = "Import NIF"

    #: Keyframe file for animations.
    keyframe_file = bpy.props.StringProperty(
        name="Keyframe File",
        description="Keyframe file for animations.",
        maxlen=1024,
        default="",
        subtype="FILE_PATH")

    #: FaceGen EGM file for morphs.
    egm_file = bpy.props.StringProperty(
        name="FaceGen EGM File",
        description="FaceGen EGM file for morphs.",
        maxlen=1024,
        default="",
        subtype="FILE_PATH")

    #: Import animation.
    animation = bpy.props.BoolProperty(
        name="Animation",
        description="Import animation.",
        default=True)

    #: Merge skeleton roots.
    merge_skeleton_roots = bpy.props.BoolProperty(
        name="Merge Skeleton Roots",
        description="Merge skeleton roots.",
        default=False)

    #: Send all geometries to their bind position.
    send_geoms_to_bind_pos = bpy.props.BoolProperty(
        name="Send Geometries To Bind Position",
        description="Send all geometries to their bind position.",
        default=False)

    #: Send all detached geometries to the position of their parent node.
    send_detached_geoms_to_node_pos = bpy.props.BoolProperty(
        name="Send Detached Geometries To Node Position",
        description=
        "Send all detached geometries to the position of their parent node.",
        default=False)

    #: Send all bones to their bind position.
    send_bones_to_bind_position = bpy.props.BoolProperty(
        name="Send Bones To Bind Position",
        description="Send all bones to their bind position.",
        default=False)

    #: Apply skin deformation to all skinned geometries.
    apply_skin_deformation =  bpy.props.BoolProperty(
        name="Apply Skin Deformation",
        description="Apply skin deformation to all skinned geometries.",
        default=False)

    #: What should be imported.
    skeleton = bpy.props.EnumProperty(
        items=(
            ("EVERYTHING", "Everything",
             "Import everything."),
            ("SKELETON_ONLY", "Skeleton Only",
             "Import skeleton only and make it parent of selected geometry."),
            ("GEOMETRY_ONLY", "Geometry Only",
             "Import geometry only and parent them to selected skeleton."),
            ),
        name="What",
        description="What should be imported.",
        default="EVERYTHING")

    #: Import multi-material shapes as a single mesh.
    combine_shapes = bpy.props.BoolProperty(
        name="Combine Shapes",
        description="Import multi-material shapes as a single mesh.",
        default=False)

    def execute(self, context):
        """Execute the import operator: first constructs a
        :class:`~io_scene_nif.import_nif.NifImport` instance and then
        calls its :meth:`~io_scene_nif.import_nif.NifImport.execute`
        method.
        """
        
        #setup the viewport for preferred viewing settings
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        for area in bpy.context.window.screen.areas:
            if area.type =='VIEW_3D':
                area.spaces[0].viewport_shade = 'TEXTURED'
        
        from . import import_nif
        return import_nif.NifImport(self, context).execute()

def _game_to_enum(game):
    symbols = ":,'\" +-*!?;./="
    table = str.maketrans(symbols, "_" * len(symbols))
    enum = game.upper().translate(table).replace("__", "_")
    return enum

class NifExportOperator(bpy.types.Operator, ExportHelper, NifOperatorCommon):
    """Operator for saving a nif file."""

    #: Name of function for calling the nif export operator.
    bl_idname = "export_scene.nif"

    #: How the nif export operator is labelled in the user interface.
    bl_label = "Export NIF"

    #: For which game to export.
    game = bpy.props.EnumProperty(
        items=[
            (_game_to_enum(game), game, "Export for " + game)
            # implementation note: reversed makes it show alphabetically
            # (at least with the current blender)
            for game in reversed(sorted(
                [x for x in NifFormat.games.keys() if x != '?']))
            ],
        name="Game",
        description="For which game to export.",
        default='OBLIVION')

    #: How to export animation.
    animation = bpy.props.EnumProperty(
        items=[
            ('ALL_NIF', "All (nif)", "Geometry and animation to a single nif."),
            ('ALL_NIF_XNIF_XKF', "All (nif, xnif, xkf)", "Geometry and animation to a nif, xnif, and xkf (for Morrowind)."),
            ('GEOM_NIF', "Geometry only (nif)", "Only geometry to a single nif."),
            ('ANIM_KF', "Animation only (kf)", "Only animation to a single kf."),
            ],
        name="Animation",
        description="How to export animation.",
        default='ALL_NIF')

    #: Smoothen inter-object seams.
    smooth_object_seams = bpy.props.BoolProperty(
        name="Smoothen Inter-Object Seams",
        description="Smoothen inter-object seams.",
        default=True)

    #: Use BSAnimationNode (for Morrowind).
    bs_animation_node = bpy.props.BoolProperty(
        name="Use NiBSAnimationNode",
        description="Use NiBSAnimationNode (for Morrowind).",
        default=False)

    #: Stripify geometries. Deprecate? (Strips are slower than triangle shapes.)
    stripify = bpy.props.BoolProperty(
        name="Stripify Geometries",
        description="Stripify geometries.",
        default=False,
        options={'HIDDEN'})

    #: Stitch strips. Deprecate? (Strips are slower than triangle shapes.)
    stitch_strips = bpy.props.BoolProperty(
        name="Stitch Strips",
        description="Stitch strips.",
        default=True,
        options={'HIDDEN'})

    #: Flatten skin.
    flatten_skin = bpy.props.BoolProperty(
        name="Flatten Skin",
        description="Flatten skin.",
        default=False)

    #: Export skin partition.
    skin_partition = bpy.props.BoolProperty(
        name="Skin Partition",
        description="Export skin partition.",
        default=True)

    #: Pad and sort bones.
    pad_bones = bpy.props.BoolProperty(
        name="Pad & Sort Bones",
        description="Pad and sort bones.",
        default=False)

    #: Maximum number of bones per skin partition.
    max_bones_per_partition = bpy.props.IntProperty(
        name = "Max Bones Per Partition",
        description="Maximum number of bones per skin partition.",
        default=18, min=4, max=18)

    #: Maximum number of bones per vertex in skin partitions.
    max_bones_per_vertex = bpy.props.IntProperty(
        name = "Max Bones Per Vertex",
        description="Maximum number of bones per vertex in skin partitions.",
        default=4, min=1,
        options={'HIDDEN'})

    #: Pad and sort bones.
    force_dds = bpy.props.BoolProperty(
        name="Force DDS",
        description="Force texture .dds extension.",
        default=True)

    #: Map game enum to nif version.
    version = {
        _game_to_enum(game): versions[-1]
        for game, versions in NifFormat.games.items() if game != '?'
        }

    def execute(self, context):
        """Execute the export operator: first constructs a
        :class:`~io_scene_nif.export_nif.NifExport` instance and then
        calls its :meth:`~io_scene_nif.export_nif.NifExport.execute`
        method.
        """
        from . import export_nif
        return export_nif.NifExport(self, context).execute()