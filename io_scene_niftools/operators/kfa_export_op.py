"""Blender Niftools Addon Main Export operators, function called through Export Menu"""

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
from bpy_extras.io_utils import ExportHelper

from io_scene_niftools.kfa_export import KfaExport
from io_scene_niftools.operators.common_op import CommonDevOperator, CommonScale, CommonKfa
from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class KfaExportOperator(Operator, ExportHelper, CommonDevOperator, CommonScale, CommonKfa):
    """Operator for saving a kfa file."""

    # Name of function for calling the kfa export operators.
    bl_idname = "export_scene.kfa"

    # How the kfa export operators is labelled in the user interface.
    bl_label = "Export KFA"

    def execute(self, context):
        """Execute the export operators: first constructs a
        :class:`~io_scene_niftools.nif_export.NifExport` instance and then
        calls its :meth:`~io_scene_niftools.nif_export.NifExport.execute`
        method.
        """
        return KfaExport(self, context).execute()


classes = [
    KfaExportOperator
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
