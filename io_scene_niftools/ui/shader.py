"""Nif User Interface, connect custom properties from properties.py into Blenders UI"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2016, NIF File Format Library and Tools contributors.
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

from bpy.types import Panel

from generated.formats.nif import classes as NifClasses

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ShaderPanel(Panel):
    bl_label = "Niftools Shader Panel"
    bl_idname = "NIFTOOLS_PT_ShaderPanel"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        nif_obj_props = context.material.niftools_shader

        layout = self.layout
        row = layout.column()

        row.prop(nif_obj_props, "bs_shadertype")

        if nif_obj_props.bs_shadertype == 'BSShaderPPLightingProperty':
            row.prop(nif_obj_props, "bsspplp_shaderobjtype")

            for property_name in sorted([member.name for member in NifClasses.BSShaderFlags]):
                row.prop(nif_obj_props, property_name)

        elif nif_obj_props.bs_shadertype in ('BSLightingShaderProperty', 'BSEffectShaderProperty'):
            row.prop(nif_obj_props, "bslsp_shaderobjtype")

            for property_name in sorted([member.name for member in NifClasses.SkyrimShaderPropertyFlags1]):
                row.prop(nif_obj_props, property_name)
            for property_name in sorted([member.name for member in NifClasses.SkyrimShaderPropertyFlags2]):
                row.prop(nif_obj_props, property_name)


classes = [
    ShaderPanel
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
