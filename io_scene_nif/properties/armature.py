'''Nif Format Properties, stores custom nif properties for armature settings'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2014, NIF File Format Library and Tools contributors.
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

from bpy.types import PropertyGroup
from bpy.props import (PointerProperty,
                       CollectionProperty,
                       IntProperty,
                       StringProperty,
                       FloatProperty,
                       )

class BoneProperty(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Bone.niftools_bone = PointerProperty(
                        name='Niftools Bone Property',
                        description='Additional bone properties used by the Nif File Format',
                        type = cls,
                        )
        cls.boneflags = IntProperty(
                        name='Bone Flag',
                        default = 0
                        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Bone.niftools_bone


class BsInventoryMarker(PropertyGroup):

    name  = StringProperty(
                    name = (''),
                    default = 'INV'
                    )

    bs_inv_x = IntProperty(
                    name = "Inv X value",
                    description = "Position of object in inventory on the x axis.",
                    default = 0)

    bs_inv_y = IntProperty(
                    name = "Inv Y value",
                    description = "Position of object in inventory on the y axis.",
                    default = 0)

    bs_inv_z = IntProperty(
                    name = "Inv Z value",
                    description = "Position of object in inventory on the z axis.",
                    default = 0)

    bs_inv_zoom = FloatProperty(
                    name = "Inv zoom value",
                    description = "Inventory object Zoom level.",
                    default = 1)

    @classmethod
    def register(cls):
        bpy.types.Object.niftools_bs_invmarker = \
            CollectionProperty(type=BsInventoryMarker)
            
    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools_bs_invmarker

