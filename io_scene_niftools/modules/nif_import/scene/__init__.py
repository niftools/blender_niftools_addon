"""This script contains classes to help import nif header information."""

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
from pyffi.formats.nif import NifFormat
from io_scene_niftools.properties.scene import _game_to_enum
from io_scene_niftools.utils.logging import NifLog


def import_version_info(data):
    scene = bpy.context.scene.niftools_scene
    nif_version = data._version_value_._value
    user_version = data._user_version_value_._value
    user_version_2 = data._user_version_2_value_._value

    # filter possible games by nif version
    possible_games = []
    for game, versions in NifFormat.games.items():
        if game != '?':
            if nif_version in versions:
                game_enum = _game_to_enum(game)
                # go to next game if user version for this game does not match defined
                if game_enum in scene.USER_VERSION:
                    if scene.USER_VERSION[game_enum] != user_version:
                        continue
                # or user version in scene is not 0 when this game has no associated user version
                elif user_version != 0:
                    continue
                # same checks for user version 2
                if game_enum in scene.USER_VERSION_2:
                    if scene.USER_VERSION_2[game_enum] != user_version_2:
                        continue
                elif user_version_2 != 0:
                    continue
                # passed all checks, add to possible games list
                possible_games.append(game_enum)
    if len(possible_games) == 1:
        scene.game = possible_games[0]
    elif len(possible_games) > 1:
        scene.game = possible_games[0]
        # todo[version] - check if this nif's version is marked as default for any of the possible games and use that
        NifLog.warn(f"Game set to '{possible_games[0]}', but multiple games qualified")
    scene.nif_version = nif_version
    scene.user_version = user_version
    scene.user_version_2 = user_version_2
