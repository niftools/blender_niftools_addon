''' Nif User Interface, connect custom properties from properties.py into Blenders UI'''

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
from bpy.types import Panel


class NifMatFlagPanel(Panel):
    bl_label = "Flag Panel"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        mat = context.material
        if mat is not None:
            if mat.use_nodes:
                if mat.active_node_material is not None:
                    return True
                return False
            return True
        return False

    def draw(self, context):
        matalpha = context.material.niftools_alpha

        layout = self.layout
        row = layout.column()

        row.prop(matalpha, "alphaflag")
        row.prop(matalpha, "materialflag")
        row.prop(matalpha, "textureflag")


class NifMatColorPanel(Panel):
    bl_label = "Material Color Panel"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        mat = context.material
        if mat is not None:
            if mat.use_nodes:
                if mat.active_node_material is not None:
                    return True
                return False
            return True
        return False

    def draw(self, context):
        mat = context.material.niftools

        layout = self.layout
        row = layout.column()
        col = row.column()
        col.prop(mat, "ambient_preview")
        col.prop(mat, "ambient_color", text="")
        col.prop(mat, "emissive_preview")
        col.prop(mat, "emissive_color", text="")
        col.prop(mat, "emissive_alpha")
        col.prop(mat, "lightingeffect1")
        col.prop(mat, "lightingeffect2")


def register():
    bpy.utils.register_class(NifMatColorPanel)
    bpy.types.MATERIAL_PT_shading.prepend(NifMatColorPanel)


def unregister():
    bpy.types.MATERIAL_PT_shading.remove(NifMatColorPanel)
    bpy.utils.unregister_class(NifMatColorPanel)
