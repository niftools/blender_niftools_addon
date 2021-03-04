"""Blender Niftools Addon Main Import operators, function called through Import Menu"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2015, NIF File Format Library and Tools contributors.
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
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper

from io_scene_niftools.nif_import import NifImport
from io_scene_niftools.operators.common_op import CommonDevOperator, CommonScale, CommonNif
from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class NifImportOperator(Operator, ImportHelper, CommonScale, CommonDevOperator, CommonNif):
    """Operator for loading a nif file."""

    # Name of function for calling the nif export operators.
    bl_idname = "import_scene.nif"

    # How the nif import operators is labelled in the user interface.
    bl_label = "Import NIF"

    # Whether or not to import the header information into the scene
    override_scene_info: bpy.props.BoolProperty(
        name="Override Scene Information",
        description="This will overwrite any previously stored scene information with the Nif header info.",
        default=True)

    # Import animation.
    animation: bpy.props.BoolProperty(
        name="Animation",
        description="Import animation.",
        default=False)

    # Merge skeleton roots.
    merge_skeleton_roots: bpy.props.BoolProperty(
        name="Merge Skeleton Roots",
        description="Merge skeleton roots.",
        default=False)

    # Send all geometries to their bind position.
    send_geoms_to_bind_pos: bpy.props.BoolProperty(
        name="Send Geometries To Bind Position",
        description="Send all geometries to their bind position.",
        default=False)

    # Send all detached geometries to the position of their parent node.
    send_detached_geoms_to_node_pos: bpy.props.BoolProperty(
        name="Send Detached Geometries To Node Position",
        description="Send all detached geometries to the position of their parent node.",
        default=False)

    # Apply skin deformation to all skinned geometries.
    apply_skin_deformation: bpy.props.BoolProperty(
        name="Apply Skin Deformation",
        description="Apply skin deformation to all skinned geometries.",
        default=False)

    # What should be imported.
    process: bpy.props.EnumProperty(
        items=(
            ("EVERYTHING", "Everything", "Import everything."),
            ("SKELETON_ONLY", "Skeleton Only", "Import skeleton only and make it parent of selected geometry."),
            ("GEOMETRY_ONLY", "Geometry Only", "Import geometry only and parent them to selected skeleton."),
        ),
        name="Process",
        description="Parts of nif to be imported.",
        default="EVERYTHING")

    use_custom_normals: bpy.props.BoolProperty(
        name="Use Custom Normals",
        description="Store NIF normals as custom normals.",
        default=True)

    combine_vertices: bpy.props.BoolProperty(
        name="Combine Vertices",
        description="Merge vertices that have identical location and normal values.",
        default=False)

    def draw(self, context):
        pass

    def execute(self, context):
        """Execute the import operators: first constructs a :class:`~io_scene_niftools.nif_import.NifImport` instance and then
        calls its :meth:`~io_scene_niftools.nif_import.NifImport.execute` method."""

        return NifImport(self, context).execute()


classes = [
    NifImportOperator
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
