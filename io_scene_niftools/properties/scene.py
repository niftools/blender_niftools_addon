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
from bpy.props import PointerProperty, IntProperty
from bpy.types import PropertyGroup
from pyffi.formats.nif import NifFormat


def _game_to_enum(game):
    symbols = ":,'\" +-*!?;./="
    table = str.maketrans(symbols, "_" * len(symbols))
    enum = game.upper().translate(table).replace("__", "_")
    return enum


# noinspection PyUnusedLocal
def update_version_from_game(self, context):
    """Updates the Scene panel's numerical version fields if its game value has been changed"""
    self.nif_version = self.VERSION.get(self.game, 0)
    self.user_version = self.USER_VERSION.get(self.game, 0)
    self.user_version_2 = self.USER_VERSION_2.get(self.game, 0)


class Scene(PropertyGroup):

    nif_version: IntProperty(
        name='Nif Version',
        default=0
    )

    user_version: IntProperty(
        name='User Version',
        default=0
    )

    user_version_2: IntProperty(
        name='User Version 2',
        default=0
    )

    #: For which game to export.
    game: bpy.props.EnumProperty(
        items=[
            (_game_to_enum(game), game, "Export for " + game)
            for game in sorted(
                [x for x in NifFormat.games.keys() if x != '?'])
        ],
        name="Game",
        description="For which game to export.",
        default='OBLIVION',
        update=update_version_from_game)

    # Number of nif units per blender unit.
    scale_correction_import: bpy.props.FloatProperty(
        name="Scale Correction Import",
        description="Changes the size of mesh to fit onto Blender's default grid.",
        default=0.1,
        min=0.01, max=100.0, precision=3)

    # Number of blender units per nif unit.
    scale_correction_export: bpy.props.FloatProperty(
        name="Scale Correction Export",
        description="Changes the size of mesh from Blender default to nif default.",
        default=10.0,
        min=0.01, max=100.0, precision=2)

    #: Map game enum to nif version.
    VERSION = {
        _game_to_enum(game): versions[-1]
        for game, versions in NifFormat.games.items() if game != '?'
    }

    USER_VERSION = {
        'OBLIVION': 11,
        'FALLOUT_3': 11,
        'SKYRIM': 12,
        'DIVINITY_2': 131072
    }

    USER_VERSION_2 = {
        'OBLIVION': 11,
        'FALLOUT_3': 34,
        'SKYRIM': 83
    }
