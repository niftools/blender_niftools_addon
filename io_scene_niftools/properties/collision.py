"""Nif User Interface, custom nif properties store for collisions settings"""

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
                       IntProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       )
from bpy.types import PropertyGroup

from generated.formats.nif import classes as NifClasses

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


def game_specific_col_layer_items(self, context):
    """Items for collision layers based on the currently selected game"""
    if context is None:
        current_game = bpy.context.scene.niftools_scene.game
    else:
        current_game = context.scene.niftools_scene.game
    col_layer_format = None
    if current_game in ("OBLIVION", "OBLIVION_KF"):
        col_layer_format = NifClasses.OblivionLayer
    elif current_game == "FALLOUT_3":
        col_layer_format = NifClasses.Fallout3Layer
    elif current_game in ("SKYRIM" , "SKYRIM_SE", "FALLOUT_4"):
        col_layer_format = NifClasses.SkyrimLayer
    if col_layer_format is None:
        return []
    else:
        return [(str(member.value), member.name, "", member.value) for member in col_layer_format]

class CollisionProperty(PropertyGroup):
    """Group of Havok related properties, which gets attached to objects through a property pointer."""

    motion_system: EnumProperty(
        name='Motion System',
        description='Havok Motion System settings for bhkRigidBody(t)',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.HkMotionType)],
        # default = 'MO_SYS_FIXED',

    )

    collision_layer: EnumProperty(
        name='Collision layer',
        description='Collision layer string (game-specific)',
        items=game_specific_col_layer_items,
    )

    penetration_depth: FloatProperty(
        name='Penetration Depth',
        description='The maximum allowed penetration for this object.',
        default=0.15
    )

    deactivator_type: EnumProperty(
        name='Deactivator Type',
        description='Motion deactivation setting',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.HkDeactivatorType)],
    )

    solver_deactivation: EnumProperty(
        name='Solver Deactivation',
        description='Motion deactivation setting',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.HkSolverDeactivation)],
    )

    quality_type: EnumProperty(
        name='Quality Type',
        description='Determines quality of motion',
        items=[(member.name, member.name, "", i) for i, member in enumerate(NifClasses.HkQualityType)],
        # default = 'MO_QUAL_FIXED',
    )

    col_filter: IntProperty(
        name='Col Filter',
        description='Flags for bhkRigidBody(t)',
        default=0
    )

    max_linear_velocity: FloatProperty(
        name='Max Linear Velocity',
        description='Linear velocity limit for bhkRigidBody(t)',
        default=0
    )

    max_angular_velocity: FloatProperty(
        name='Max Angular Velocity',
        description='Angular velocity limit for bhkRigidBody(t)',
        default=0
    )

    export_bhklist: BoolProperty(
        name='Export BHKList',
        description='None',
        default=False
    )

    use_blender_properties: BoolProperty(
        name='Use Blender Properties',
        description='Whether or not to export collision settings via blender properties',
        default=False,
    )


CLASSES = [
    CollisionProperty
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Object.nifcollision = bpy.props.PointerProperty(type=CollisionProperty)


def unregister():
    del bpy.types.Object.nifcollision

    unregister_classes(CLASSES, __name__)
