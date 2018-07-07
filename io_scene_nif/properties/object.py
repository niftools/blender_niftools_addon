""" Nif User Interface, custom nif properties for objects"""

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
                       StringProperty,
                       IntProperty,
                       EnumProperty,
                       CollectionProperty,
                       FloatProperty
                       )
from bpy.types import PropertyGroup
from pyffi.formats.nif import NifFormat


class ExtraData(PropertyGroup):
    name = StringProperty()
    data = StringProperty()
    sub_class = StringProperty()


#     def __new__(self, name, data, sub_class):
#         self.name = name
#         self.data = data
#         self.sub_class = sub_class


class BSXFlags:
    # type = NifFormat.BSXFlags()
    #     data = {}

    def __init__(self):
        self.name = "BSXFlag"


class ExtraDataStore(PropertyGroup):
    @classmethod
    def register(cls):
        cls.extra_data = CollectionProperty(
            name="Extra Data",
            description="Used to store all the Extra data",
            type=ExtraData
        )

        cls.extra_data_index = IntProperty()

    @classmethod
    def unregister(cls):
        del cls.extra_data
        del cls.extra_data_index


class ObjectProperty(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools = PointerProperty(
            name='Niftools Object Property',
            description='Additional object properties used by the Nif File Format',
            type=cls,
        )

        cls.rootnode = EnumProperty(
            name='Nif Root Node',
            description='Type of property used to display meshes.',
            items=(
                ('NiNode', 'NiNode', "", 0),
                ('BSFadeNode', 'BSFadeNode', "", 1)),
            default='NiNode',
        )

        cls.bsnumuvset = IntProperty(
            name='BS Num UV Set',
            default=0
        )

        cls.longname = StringProperty(
            name='Nif Long Name'
        )

        cls.consistency_flags = EnumProperty(
            name='Consistency Flag',
            description='Controls animation type',
            items=[(item, item, "", i) for i, item in enumerate(NifFormat.ConsistencyType._enumkeys)],
            # default = 'SHADER_DEFAULT'
        )

        cls.objectflags = IntProperty(
            name='Object Flag',
            description='Controls animation and collision',
            default=0
        )

        cls.bsxflags = IntProperty(
            name='BSX Flags',
            description='Controls animation and collision',
            default=0  # 2 = Bit 1, enable collision
        )

        cls.upb = StringProperty(
            name='UPB',
            description='Commands for an optimizer?',
            default=''
        )

        cls.extra_data_store = PointerProperty(
            name="Extra Data",
            description="Used to store all the Extra data",
            type=ExtraDataStore,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools


class BsInventoryMarker(PropertyGroup):

    @classmethod
    def register(cls):
        bpy.types.Object.niftools_bs_invmarker = CollectionProperty(type=BsInventoryMarker)

        cls.name = StringProperty(
            name="",
            default='INV'
        )

        cls.bs_inv_x = IntProperty(
            name="Inv X value",
            description="Position of object in inventory on the x axis.",
            default=0
        )

        cls.bs_inv_y = IntProperty(
            name="Inv Y value",
            description="Position of object in inventory on the y axis.",
            default=0
        )

        cls.bs_inv_z = IntProperty(
            name="Inv Z value",
            description="Position of object in inventory on the z axis.",
            default=0
        )

        cls.bs_inv_zoom = FloatProperty(
            name="Inv Zoom Value",
            description="Inventory object Zoom level.",
            default=1
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools_bs_invmarker
