""" Nif User Interface, custom nif properties for objects"""

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
                       StringProperty,
                       IntProperty,
                       EnumProperty,
                       CollectionProperty,
                       FloatProperty
                       )
from bpy.types import PropertyGroup, Object

from pyffi.formats.nif import NifFormat

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


prn_array = [
            ["OBLIVION", "FALLOUT_3", "SKYRIM"],
            ["DAGGER", "SideWeapon", "Weapon", "WeaponDagger"],
            ["2HANDED", "BackWeapon", "Weapon", "WeaponBack"],
            ["BOW", "BackWeapon", None, "WeaponBow"],
            ["MACE", "SideWeapon", "Weapon", "WeaponMace"],
            ["SHIELD", "Bip01 L ForearmTwist", None, "SHIELD"],
            ["STAFF", "Torch", "Weapon", "WeaponStaff"],
            ["SWORD", "SideWeapon", "Weapon", "WeaponSword"],
            ["AXE", "SideWeapon", "Weapon", "WeaponAxe"],
            ["QUIVER", "Quiver", "Weapon", "QUIVER"],
            ["TORCH", "Torch", "Weapon", "SHIELD"],
            ["HELMET", "Bip01 Head", "Bip01 Head", "NPC Head [Head]"],
            ["RING", "Bip01 R Finger1", "Bip01 R Finger1", "NPC R Finger10 [RF10]"]
            ]
# PRN_DICT is a dict like so: dict['SLOT']['GAME']: 'Bone'
PRN_DICT = {}
for row in prn_array[1:]:
    PRN_DICT[row[0]] = dict(zip(prn_array[0], row[1:]))


class ExtraData(PropertyGroup):
    name: StringProperty()
    data: StringProperty()
    sub_class: StringProperty()


class BSXFlags:
    # type = NifFormat.BSXFlags()
    #     data = {}

    def __init__(self):
        self.name = "BSXFlag"


class ExtraDataStore(PropertyGroup):

    extra_data_index: IntProperty()
    extra_data: CollectionProperty(
        name="Extra Data",
        description="Used to store all the Extra data",
        type=ExtraData
    )


class ObjectProperty(PropertyGroup):

    rootnode: EnumProperty(
        name='Nif Root Node',
        description='Type of property used to display meshes.',
        items=(
            ('NiNode', 'NiNode', "", 0),
            ('BSFadeNode', 'BSFadeNode', "", 1)),
        default='NiNode',
    )

    prn_location: EnumProperty(
        name='Weapon Location',
        description='Attachment point of weapon, for Skyrim, FO3 & Oblivion',
        items=[(item, item, "", i) for i, item in enumerate(["NONE"] + list(PRN_DICT.keys()))],
        # default = 'NONE'
    )

    longname: StringProperty(
        name='Nif Long Name'
    )

    consistency_flags: EnumProperty(
        name='Consistency Flag',
        description='Controls animation type',
        items=[(item, item, "", i) for i, item in enumerate(NifFormat.ConsistencyType._enumkeys)],
        # default = 'SHADER_DEFAULT'
    )

    flags: IntProperty(
        name='Object Flag',
        description='Controls animation and collision',
        default=0
    )

    bsxflags: IntProperty(
        name='BSX Flags',
        description='Controls animation and collision',
        default=0  # 2 = Bit 1, enable collision
    )

    upb: StringProperty(
        name='UPB',
        description='Commands for an optimizer?',
        default=''
    )

    extra_data_store: PointerProperty(
        name="Extra Data",
        description="Used to store all the Extra data",
        type=ExtraDataStore,
    )


class BsInventoryMarker(PropertyGroup):

    name: StringProperty(
        name="",
        default='INV'
    )

    bs_inv_x: FloatProperty(
        name="Inv X value",
        description="Rotation of object in inventory around the x axis.",
        default=0,
        subtype = "ANGLE"
    )

    bs_inv_y: FloatProperty(
        name="Inv Y value",
        description="Rotation of object in inventory around the y axis.",
        default=0,
        subtype = "ANGLE"
    )

    bs_inv_z: FloatProperty(
        name="Inv Z value",
        description="Rotation of object in inventory around the z axis.",
        default=0,
        subtype = "ANGLE"
    )

    bs_inv_zoom: FloatProperty(
        name="Inv Zoom Value",
        description="Inventory object Zoom level.",
        default=1
    )


CLASSES = [
    ExtraData,
    ExtraDataStore,
    ObjectProperty,
    BsInventoryMarker
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Object.niftools = bpy.props.PointerProperty(type=ObjectProperty)
    bpy.types.Object.niftools_bs_invmarker = bpy.props.CollectionProperty(type=BsInventoryMarker)


def unregister():
    del bpy.types.Object.niftools
    del bpy.types.Object.niftools_bs_invmarker

    unregister_classes(CLASSES, __name__)



