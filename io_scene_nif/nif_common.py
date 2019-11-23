"""Helper functions for nif import and export scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005, NIF File Format Library and Tools contributors.
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
import pyffi
from pyffi.formats.nif import NifFormat

from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class NifCommon:
    """Abstract base class for import and export. Contains utility functions
    that are commonly used in both import and export.
    """
    # used for weapon locations or attachments to a body
    prn_dict = {"BACK": "BackWeapon",
                "SIDE": "SideWeapon",
                "QUIVER": "Quiver",
                "SHIELD": "Bip01 L ForearmTwist",
                "HELM": "Bip01 Head",
                "RING": "Bip01 R Finger1"}

    # dictionary of materials, to reuse materials
    dict_materials = {}

    # dictionary of texture files, to reuse textures
    dict_textures = {}
    dict_mesh_uvlayers = []

    VERTEX_RESOLUTION = 1000
    NORMAL_RESOLUTION = 100

    EXTRA_SHADER_TEXTURES = [
        "EnvironmentMapIndex",
        "NormalMapIndex",
        "SpecularIntensityIndex",
        "EnvironmentIntensityIndex",
        "LightCubeMapIndex",
        "ShadowTextureIndex"]
    """Names (ordered by default index) of shader texture slots for
    Sid Meier's Railroads and similar games.
    """

    HAVOK_SCALE = 6.996

    def __init__(self, operator, context):
        """Common initialization functions for executing the import/export operators: """

        NifOp.init(operator, context)

        # print scripts info
        from . import bl_info
        niftools_ver = (".".join(str(i) for i in bl_info["version"]))

        NifLog.info("Executing - Niftools : Blender Nif Plugin v{0} (running on Blender {1}, PyFFI {2})".format(niftools_ver,
                                                                                                                bpy.app.version_string,
                                                                                                                pyffi.__version__))

        # find and store this list now of selected objects as creating new objects adds them to the selection list
        self.selected_objects = bpy.context.selected_objects[:]

    def get_n_apply_mode_from_b_blend_type(self, b_blend_type):
        if b_blend_type == "LIGHTEN":
            return NifFormat.ApplyMode.APPLY_HILIGHT
        elif b_blend_type == "MULTIPLY":
            return NifFormat.ApplyMode.APPLY_HILIGHT2
        elif b_blend_type == "MIX":
            return NifFormat.ApplyMode.APPLY_MODULATE

        NifLog.warn("Unsupported blend type ({0}) in material, using apply mode APPLY_MODULATE".format(b_blend_type))
        return NifFormat.ApplyMode.APPLY_MODULATE
