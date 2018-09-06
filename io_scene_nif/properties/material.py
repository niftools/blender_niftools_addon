""" Nif User Interface, custom nif properties for materials"""

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
from bpy.props import (PointerProperty,
                       FloatVectorProperty,
                       IntProperty,
                       BoolProperty,
                       FloatProperty,
                       )
from bpy.types import PropertyGroup


class Material(PropertyGroup):
    """Adds custom properties to material"""

    @classmethod
    def register(cls):
        bpy.types.Material.niftools = PointerProperty(
            name='Niftools Materials',
            description='Additional material properties used by the Nif File Format',
            type=cls,
        )

        cls.ambient_preview = BoolProperty(
            name='Ambient Preview', description='Allows a viewport preview of the ambient property', default=False)

        cls.ambient_color = FloatVectorProperty(
            name='Ambient', subtype='COLOR', default=[1.0, 1.0, 1.0], min=0.0, max=1.0)

        cls.emissive_preview = BoolProperty(
            name='Emissive Preview', description='Allows a viewport preview of the emissive property', default=False)

        cls.emissive_color = FloatVectorProperty(
            name='Emissive', subtype='COLOR', default=[0.0, 0.0, 0.0], min=0.0, max=1.0)

        cls.emissive_alpha = FloatVectorProperty(
            name='Alpha', subtype='COLOR', default=[0.0, 0.0, 0.0], min=0.0, max=1.0)

        cls.lightingeffect1 = FloatProperty(
            name='Lighting Effect 1',
            default=0.3
        )
        cls.lightingeffect2 = FloatProperty(
            name='Lighting Effect 2',
            default=2
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Material.niftools


class AlphaFlags(PropertyGroup):
    """Adds custom properties to material"""

    @classmethod
    def register(cls):
        bpy.types.Material.niftools_alpha = PointerProperty(
            name='Niftools Material Alpha',
            description='Additional material properties used by the Nif File Format',
            type=cls,
        )

        cls.alphaflag = IntProperty(
            name='Alpha Flag',
            default=0
        )

        cls.textureflag = IntProperty(
            name='Texture Flag',
            default=0
        )

        cls.materialflag = IntProperty(
            name='Material Flag',
            default=0
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Material.niftools_alpha
