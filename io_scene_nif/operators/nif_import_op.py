'''Blender Nif Plugin Main Import operators, function called through Import Menu'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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
from bpy_extras.io_utils import ImportHelper

from .nif_common_op import NifOperatorCommon

from io_scene_nif import nif_import

class NifImportOperator(bpy.types.Operator, ImportHelper, NifOperatorCommon):
    """Operator for loading a nif file."""

    #: Name of function for calling the nif export operators.
    bl_idname = "import_scene.nif"

    #: How the nif import operators is labelled in the user interface.
    bl_label = "Import NIF"

    #: Number of nif units per blender unit.
    scale_correction_import = bpy.props.FloatProperty(
        name="Scale Correction Import",
        description="Changes size of mesh to fit onto Blender's default grid.",
        default=1.0,
        min=0.01, max=100.0, precision=2)

    # Whether or not to import the header information into the scene
    override_scene_info = bpy.props.BoolProperty(
        name="Override Scene Information",
        description="This will overwrite any previously stored scene information with the Nif header info.",
        default=True)

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
        default=False)

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

    #: Re-align Tail bones on import
    import_realign_bones = bpy.props.EnumProperty(
        items=(
            ("1", "Re-Align Tail Bone", "Re-Aligns bone tail on import."),
            ("2", "Re-Align Tail Bone + Roll", "Re-Align tail bone + roll"),
            ),
        name="Align",
        description="Re-align or Re-Align+Roll",
        default="1")


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
        name="Process",
        description="Parts of nif to be imported.",
        default="EVERYTHING")

    #: Import multi-material shapes as a single mesh.
    combine_shapes = bpy.props.BoolProperty(
        name="Combine Shapes",
        description="Import multi-material shapes as a single mesh.",
        default=False)
    
    #: Merge vertices that have identical location and normal values.
    combine_vertices = bpy.props.BoolProperty(
        name="Combine Vertices",
        description="Merge vertices that have identical location and normal values.",
        default=False)
    

    def execute(self, context):
        """Execute the import operators: first constructs a
        :class:`~io_scene_nif.nif_import.NifImport` instance and then
        calls its :meth:`~io_scene_nif.nif_import.NifImport.execute`
        method.
        """
        
        # setup the viewport for preferred viewing settings
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        for area in bpy.context.window.screen.areas:
            if area.type =='VIEW_3D':
                area.spaces[0].viewport_shade = 'MATERIAL'
                area.spaces[0].show_backface_culling = True
        
        return nif_import.NifImport(self, context).execute()
    
