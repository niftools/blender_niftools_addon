"""Nif Operators, nif specific operators to update nif properties"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2014, NIF File Format Library and Tools contributors.
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
from io_scene_niftools.utils.decorators import register_modules, unregister_modules
from io_scene_niftools.operators import object, geometry, nif_import_op, nif_export_op, kf_import_op, egm_import_op  # kf_export_op


# noinspection PyUnusedLocal
def menu_func_import(self, context):
    self.layout.operator(nif_import_op.NifImportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")
    self.layout.operator(kf_import_op.KfImportOperator.bl_idname, text="NetImmerse/Gamebryo (.kf)")
    self.layout.operator(egm_import_op.EgmImportOperator.bl_idname, text="NetImmerse/Gamebryo (.egm)")
    # TODO [general] get default path from config registry
    # default_path = bpy.data.filename.replace(".blend", ".nif")
    # ).filepath = default_path


# noinspection PyUnusedLocal
def menu_func_export(self, context):
    self.layout.operator(nif_export_op.NifExportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")
    # self.layout.operator(operators.kf_export_op.KfExportOperator.bl_idname, text="NetImmerse/Gamebryo (.kf)")


MODS = [object, geometry, nif_import_op, nif_export_op, kf_import_op, egm_import_op]


def register():
    register_modules(MODS, __name__)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    unregister_modules(MODS, __name__)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
