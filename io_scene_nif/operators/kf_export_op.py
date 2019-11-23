"""Blender Nif Plugin Main Export operators, function called through Export Menu"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2019, NIF File Format Library and Tools contributors.
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
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from pyffi.formats.nif import NifFormat

from io_scene_nif import kf_export
from .nif_common_op import NifOperatorCommon


def _game_to_enum(game):
    symbols = ":,'\" +-*!?;./="
    table = str.maketrans(symbols, "_" * len(symbols))
    enum = game.upper().translate(table).replace("__", "_")
    return enum


class KfExportOperator(Operator, ExportHelper, NifOperatorCommon):
    """Operator for saving a kf file."""

    #: Name of function for calling the kf export operators.
    bl_idname = "export_scene.kf"

    #: How the kf export operators is labelled in the user interface.
    bl_label = "Export KF"

    #: Number of blender units per nif unit.
    scale_correction_export = bpy.props.FloatProperty(
        name="Scale Correction Export",
        description="Changes size of mesh from Blender default to nif default.",
        default=1.0,
        min=0.01, max=100.0, precision=2)

    #: For which game to export.
    game = bpy.props.EnumProperty(
        items=[
            (_game_to_enum(game), game, "Export for " + game)
            # implementation note: reversed makes it show alphabetically
            # (at least with the current blender)
            for game in reversed(sorted(
                [x for x in NifFormat.games.keys() if x != '?']))
        ],
        name="Game",
        description="For which game to export.",
        default='OBLIVION')

    #: Use BSAnimationNode (for Morrowind).
    bs_animation_node = bpy.props.BoolProperty(
        name="Use NiBSAnimationNode",
        description="Use NiBSAnimationNode (for Morrowind).",
        default=False)

    #: Map game enum to nif version.
    version = {
        _game_to_enum(game): versions[-1]
        for game, versions in NifFormat.games.items() if game != '?'
    }

    def execute(self, context):
        """Execute the export operators: first constructs a
        :class:`~io_scene_nif.nif_export.NifExport` instance and then
        calls its :meth:`~io_scene_nif.nif_export.NifExport.execute`
        method.
        """
        return kf_export.KfExport(self, context).execute()
