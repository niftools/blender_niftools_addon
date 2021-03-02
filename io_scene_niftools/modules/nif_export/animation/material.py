"""This script contains classes to help export material animations."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_export.animation import Animation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


class MaterialAnimation(Animation):

    def __init__(self):
        super().__init__()

    def export_material(self, b_material, n_mat_prop):
        """Export material animations for given geometry."""

        if NifOp.props.animation == 'GEOM_NIF':
            # geometry only: don't write controllers
            return

        # check if the material holds an animation
        if not self.get_active_action(b_material):
            return
        
        self.export_material_controllers(b_material, n_mat_prop)
        # todo [material][animation] needs upgrade to new node api, also needs n_geom
        # self.export_uv_controller(b_material, n_geom)

    def export_material_controllers(self, b_material, n_mat_prop):
        """Export material animation data for given geometry."""

        if not n_mat_prop:
            raise ValueError("Bug!! must add material property before exporting alpha controller")
        colors = (("alpha", None),
                  ("niftools.ambient_color", NifFormat.TargetColor.TC_AMBIENT),
                  ("diffuse_color", NifFormat.TargetColor.TC_DIFFUSE),
                  ("specular_color", NifFormat.TargetColor.TC_SPECULAR))
        # the actual export
        for b_dtype, n_dtype in colors:
            self.export_material_alpha_color_controller(b_material, n_mat_prop, b_dtype, n_dtype)

    def export_material_alpha_color_controller(self, b_material, n_mat_prop, b_dtype, n_dtype):
        """Export the material alpha or color controller data."""

        # get fcurves
        fcurves = [fcu for fcu in b_material.animation_data.action.fcurves if b_dtype in fcu.data_path]
        if not fcurves:
            return

        # just set the names of the nif data types, main difference between alpha and color
        if b_dtype == "alpha":
            keydata = "NiFloatData"
            interpolator = "NiFloatInterpolator"
            controller = "NiAlphaController"
        else:
            keydata = "NiPosData"
            interpolator = "NiPoint3Interpolator"
            controller = "NiMaterialColorController"

        # create the key data
        n_key_data = block_store.create_block(keydata, fcurves)
        n_key_data.data.num_keys = len(fcurves[0].keyframe_points)
        n_key_data.data.interpolation = NifFormat.KeyType.LINEAR_KEY
        n_key_data.data.keys.update_size()

        # assumption: all curves have same amount of keys and are sampled at the same time
        for i, n_key in enumerate(n_key_data.data.keys):
            frame = fcurves[0].keyframe_points[i].co[0]
            # add each point of the curves
            n_key.arg = n_key_data.data.interpolation
            n_key.time = frame / self.fps
            if b_dtype == "alpha":
                n_key.value = fcurves[0].keyframe_points[i].co[1]
            else:
                n_key.value.x, n_key.value.y, n_key.value.z = [fcu.keyframe_points[i].co[1] for fcu in fcurves]
        # if key data is present
        # then add the controller so it is exported
        if fcurves[0].keyframe_points:
            n_mat_ctrl = block_store.create_block(controller, fcurves)
            n_mat_ipol = block_store.create_block(interpolator, fcurves)
            n_mat_ctrl.interpolator = n_mat_ipol

            self.set_flags_and_timing(n_mat_ctrl, fcurves)
            # set target color only for color controller
            if n_dtype:
                n_mat_ctrl.set_target_color(n_dtype)
            n_mat_ctrl.data = n_key_data
            n_mat_ipol.data = n_key_data
            # attach block to material property
            n_mat_prop.add_controller(n_mat_ctrl)

    def export_uv_controller(self, b_material, n_geom):
        """Export the material UV controller data."""

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
                NifLog.debug(f"Exporting {fcu} as NiUVData")
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
            self.set_flags_and_timing(n_uv_ctrl, fcurves)
            n_uv_ctrl.data = n_uv_data
            # attach block to geometry
            n_geom.add_controller(n_uv_ctrl)
