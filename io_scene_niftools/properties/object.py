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

from generated.formats.nif import classes as NifClasses

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


prn_map = {"OBLIVION":   [("SideWeapon", ""),
                          ("BackWeapon", ""),
                          ("Bip01 L ForearmTwist", "Used for shields"),
                          ("Torch", ""),
                          ("Quiver", ""),
                          ("Bip01 Head", "Used for helmets"),
                          ("Bip01 R Finger1", "Used for rings")],
           "FALLOUT_3":  [("Weapon", ""),
                          ("Bip01 Head", "Used for helmets"),
                          ("Bip01 R Finger1", "")],
           "SKYRIM":     [("WeaponDagger", ""),
                          ("WeaponBack", ""),
                          ("WeaponBow", ""),
                          ("WeaponMace", ""),
                          ("SHIELD", ""),
                          ("WeaponStaff", ""),
                          ("WeaponSword", ""),
                          ("WeaponAxe", ""),
                          ("QUIVER", ""),
                          ("SHIELD", ""),
                          ("NPC Head [Head]", "Used for helmets"),
                          ("NPC R Finger10 [RF10]", "Used for rings")]
           }
prn_map["SKYRIM_SE"] = prn_map["SKYRIM"]


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


class BsInventoryMarker(PropertyGroup):
    name: StringProperty(
        name="",
        default='INV'
    )

    x: FloatProperty(
        name="X Rotation",
        description="Rotation of object in inventory around the x axis",
        default=0,
        subtype="ANGLE"
    )

    y: FloatProperty(
        name="Y Rotation",
        description="Rotation of object in inventory around the y axis",
        default=0,
        subtype="ANGLE"
    )

    z: FloatProperty(
        name="Z Rotation",
        description="Rotation of object in inventory around the z axis",
        default=0,
        subtype="ANGLE"
    )

    zoom: FloatProperty(
        name="Zoom",
        description="Inventory object Zoom level",
        default=1
    )


prn_versioned_arguments = {}
if bpy.app.version >= (3, 3, 0):
    prn_versioned_arguments['search'] = lambda self, context, edit_text: prn_map.get(context.scene.niftools_scene.game, [])

class ObjectProperty(PropertyGroup):

    nodetype: EnumProperty(
        name='Node Type',
        description='Type of node this empty represents',
        items=(
              ('NiNode', 'NiNode', "", 0),
              ('BSFadeNode', 'BSFadeNode', "", 1)),
        default='NiNode',
    )


    prn_location: StringProperty(
        name='Weapon Location',
        description='Attachment point of weapon, for Skyrim, FO3 & Oblivion',
        **prn_versioned_arguments,
    )

    longname: StringProperty(
        name='Nif Long Name'
    )

    consistency_flags: EnumProperty(
        name='Consistency Flag',
        description='Controls animation type',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.ConsistencyType)],
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

    skeleton_root: StringProperty(
        name='Skeleton Root',
        description="The bone that acts as the root of the SkinInstance",
    )

    bs_inv: bpy.props.CollectionProperty(type=BsInventoryMarker)


CLASSES = [
    BsInventoryMarker,
    ExtraData,
    ExtraDataStore,
    ObjectProperty,
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Object.niftools = bpy.props.PointerProperty(type=ObjectProperty)


def unregister():
    del bpy.types.Object.niftools

    unregister_classes(CLASSES, __name__)



