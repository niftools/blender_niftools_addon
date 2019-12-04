"""This script contains classes to help export mesh animations."""

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
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.animation import animation_export
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class MeshAnimation:

    def __init__(self):
        self.fps = bpy.context.scene.render.fps

    def export_uv_controller(self, b_material, n_geom):
        """Export the material UV controller data."""

        # TODO [animation] This is also done in export material, should have higher level function.
        if NifOp.props.animation == 'GEOM_NIF':
            # geometry only: don't write controllers
            return

        # check if the material holds an animation
        if b_material and not (b_material.animation_data and b_material.animation_data.action):
            return

        # get fcurves - a bit more elaborate here so we can zip with the NiUVData later
        # nb. these are actually specific to the texture slot in blender
        # here we don't care and just take the first fcurve that matches
        fcurves = []
        for dp, ind in (("offset", 0), ("offset", 1), ("scale", 0), ("scale", 1)):
            for fcu in b_material.animation_data.action.fcurves:
                if dp in fcu.data_path and fcu.array_index == ind:
                    fcurves.append(fcu)
                    break
            else:
                fcurves.append(None)

        # continue if at least one fcurve exists
        if not any(fcurves):
            return

        # get the uv curves and translate them into nif data
        n_uv_data = NifFormat.NiUVData()
        for fcu, n_uv_group in zip(fcurves, n_uv_data.uv_groups):
            if fcu:
                NifLog.debug("Exporting {0} as NiUVData".format(fcu))
                n_uv_group.num_keys = len(fcu.keyframe_points)
                n_uv_group.interpolation = NifFormat.KeyType.LINEAR_KEY
                n_uv_group.keys.update_size()
                for b_point, n_key in zip(fcu.keyframe_points, n_uv_group.keys):
                    # add each point of the curve
                    b_frame, b_value = b_point.co
                    if "offset" in fcu.data_path:
                        # offsets are negated in blender
                        b_value = -b_value
                    n_key.arg = n_uv_group.interpolation
                    n_key.time = b_frame / self.fps
                    n_key.value = b_value

        # if uv data is present then add the controller so it is exported
        if fcurves[0].keyframe_points:
            n_uv_ctrl = NifFormat.NiUVController()
            animation_export.set_flags_and_timing(n_uv_ctrl, fcurves)
            n_uv_ctrl.data = n_uv_data
            # attach block to geometry
            n_geom.add_controller(n_uv_ctrl)
