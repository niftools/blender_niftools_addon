""" Nif User Interface, custom nif properties for shaders"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2012, NIF File Format Library and Tools contributors.
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
from bpy.props import (PointerProperty,
                       BoolProperty,
                       EnumProperty,
                       )
from bpy.types import PropertyGroup

from nifgen.formats.nif import classes as NifClasses

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ShaderProps(PropertyGroup):

    bs_shadertype: EnumProperty(
        name='Shader Type',
        description='Type of property used to display meshes',
        items=(
            ('None', 'None', "", 0),
            ('BSShaderProperty', 'BS Shader Property', "", 1),
            ('BSShaderPPLightingProperty', 'BS Shader PP Lighting Property', "", 2),
            ('BSLightingShaderProperty', 'BS Lighting Shader Property', "", 3),
            ('BSEffectShaderProperty', 'BS Effect Shader Property', "", 4)
        )
    )

    bsspplp_shaderobjtype: EnumProperty(
        name='BS Shader PP Lighting Object Type',
        description='Type of object linked to shader',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.BSShaderType)],
        default='SHADER_DEFAULT'
    )

    bslsp_shaderobjtype: EnumProperty(
        name='BS Lighting Shader Object Type',
        description='Type of object linked to shader',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.BSLightingShaderType)],
        # default = 'SHADER_DEFAULT'
    )


def prettify_prop_name(property_name):
    replacers = [('Hd', 'HD'), ('Lod', 'LOD')]
    prettified = ' '.join([word.capitalize() for word in property_name.split('_')])
    for original, replacement in replacers:
        prettified = prettified.replace(original, replacement)
    return prettified


annotations_dict = ShaderProps.__dict__.get('__annotations__', None)
if annotations_dict:
    for flag_field in (NifClasses.BSShaderFlags,
                       NifClasses.SkyrimShaderPropertyFlags1,
                       NifClasses.SkyrimShaderPropertyFlags2):
        for property_name in flag_field.__members__:
            if property_name not in annotations_dict:
                annotations_dict[property_name] = BoolProperty(name=prettify_prop_name(property_name))


CLASSES = [
    ShaderProps
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Material.niftools_shader = bpy.props.PointerProperty(type=ShaderProps)


def unregister():
    del bpy.types.Material.niftools_shader

    unregister_classes(CLASSES, __name__)
