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
from generated.formats.nif.versions import get_game

from io_scene_niftools.utils.logging import NifLog


def import_version_info(data):
    scene = bpy.context.scene.niftools_scene
    nif_version = data.version
    user_version = data.user_version
    user_version_2 = data.bs_header.bs_version if hasattr(data, "bs_header") else 0

    # filter possible games by nif version
    possible_games = get_game(data)
    if len(possible_games) == 1:
        scene.game = possible_games[0]._name_
    elif len(possible_games) > 1:
        scene.game = possible_games[0]._name_
        # todo[version] - check if this nif's version is marked as default for any of the possible games and use that
        NifLog.warn(f"Game set to '{possible_games[0]}', but multiple games qualified")
    scene.nif_version = nif_version
    scene.user_version = user_version
    scene.user_version_2 = user_version_2
