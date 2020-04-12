"""Blender Nif Plugin Main Import operators, function called through Import Menu"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2019, NIF File Format Library and Tools contributors.
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
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from io_scene_nif import kf_import
from .nif_common_op import NifOperatorCommon


class KfImportOperator(Operator, ImportHelper, NifOperatorCommon):
    """Operator for loading a kf file."""

    #: Name of function for calling the nif export operators.
    bl_idname = "import_scene.kf"

    #: How the nif import operators is labelled in the user interface.
    bl_label = "Import KF"

    #: Number of nif units per blender unit.
    scale_correction_import: bpy.props.FloatProperty(
        name="Scale Correction Import",
        description="Changes size of mesh to fit onto Blender's default grid.",
        default=1.0,
        min=0.01, max=100.0, precision=2)

    #: File name filter for file select dialog.
    filter_glob: bpy.props.StringProperty(
        default="*.kf", options={'HIDDEN'})

    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        """Execute the import operators: first constructs a
        :class:`~io_scene_nif.kf_import.KfImport` instance and then
        calls its :meth:`~io_scene_nif.kf_import.KfImport.execute`
        method.
        """

        return kf_import.KfImport(self, context).execute()
