""" Nif User Interface, custom nif properties for materials"""

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
from bpy.props import (PointerProperty,
                       FloatVectorProperty,
                       IntProperty,
                       BoolProperty,
                       FloatProperty,
                       )
from bpy.types import PropertyGroup

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class Material(PropertyGroup):
    """Adds custom properties to material"""

    ambient_preview: BoolProperty(
        name='Ambient Preview', description='Allows a viewport preview of the ambient property', default=False)

    ambient_color: FloatVectorProperty(
        name='Ambient', subtype='COLOR', default=[1.0, 1.0, 1.0], min=0.0, max=1.0)

    emissive_preview: BoolProperty(
        name='Emissive Preview', description='Allows a viewport preview of the emissive property', default=False)

    emissive_color: FloatVectorProperty(
        name='Emissive', subtype='COLOR', default=[0.0, 0.0, 0.0], min=0.0, max=1.0)

    emissive_alpha: FloatVectorProperty(
        name='Alpha', subtype='COLOR', default=[0.0, 0.0, 0.0], min=0.0, max=1.0)

    lightingeffect1: FloatProperty(
        name='Lighting Effect 1',
        default=0.3
    )
    lightingeffect2: FloatProperty(
        name='Lighting Effect 2',
        default=2
    )


class AlphaFlags(PropertyGroup):
    """Adds custom properties to material"""

    alphaflag: IntProperty(
        name='Alpha Flag',
        default=0
    )

    textureflag: IntProperty(
        name='Texture Flag',
        default=0
    )

    materialflag: IntProperty(
        name='Material Flag',
        default=0
    )


CLASSES = [
    Material,
    AlphaFlags
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Material.niftools = bpy.props.PointerProperty(type=Material)
    bpy.types.Material.niftools_alpha = bpy.props.PointerProperty(type=AlphaFlags)


def unregister():
    del bpy.types.Material.niftools
    del bpy.types.Material.niftools_alpha

    unregister_classes(CLASSES, __name__)
