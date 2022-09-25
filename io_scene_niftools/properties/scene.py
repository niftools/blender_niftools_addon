""" Nif User Interface, custom nif properties for objects"""

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


import bpy
from bpy.props import PointerProperty, IntProperty, EnumProperty, StringProperty, FloatProperty, CollectionProperty
from bpy.types import PropertyGroup

from generated.formats.nif.versions import games, set_game

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class DummyClass: pass

dummy_context = DummyClass()
dummy_context.bs_header = DummyClass()
game_version_map = {}
for game in games:
    dummy_context.version = 0
    dummy_context.user_version = 0
    dummy_context.bs_header.bs_version = 0
    set_game(dummy_context, game)
    game_version_map[game._name_] = (dummy_context.version, dummy_context.user_version, dummy_context.bs_header.bs_version)
game_version_map["NONE"] = (0, 0, 0)

# noinspection PyUnusedLocal
def update_version_from_game(self, context):
    """Updates the Scene panel's numerical version fields if its game value has been changed"""
    self.nif_version, self.user_version, self.user_version_2 = game_version_map[self.game]

class Scene(PropertyGroup):
    nif_version: IntProperty(
        name='Version',
        description="The Gamebryo Engine version used",
        default=0
    )

    user_version: IntProperty(
        name='User Version',
        description="Studio specific version, used to denote versioning from game to game",
        default=0
    )

    user_version_2: IntProperty(
        name='User Version 2',
        description="Studio specific version, used to denote versioning from game to game",
        default=0
    )

    # For which game to export.
    game: bpy.props.EnumProperty(
        items=[('NONE', 'NONE', 'No game selected')] + [
            (member._name_, member._value_, "Export for " + member._value_)
            for member in sorted(
                [member for member in games], key=lambda x: x._name_)
        ],
        name="Game",
        description="For which game to export",
        default='NONE',
        update=update_version_from_game)

    rootnode: EnumProperty(
        name='Root Node',
        description='Type of property used to display meshes',
        items=(
            ('NiNode', 'NiNode', "", 0),
            ('BSFadeNode', 'BSFadeNode', "", 1)),
        default='NiNode',
    )

    scale_correction: bpy.props.FloatProperty(
        name="Scale Correction",
        description="Changes size of mesh to fit onto Blender's default grid",
        default=0.1,
        min=0.001, max=100.0, precision=2)


CLASSES = [
    Scene
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Scene.niftools_scene = bpy.props.PointerProperty(type=Scene)


def unregister():
    del bpy.types.Scene.niftools_scene

    unregister_classes(CLASSES, __name__)
