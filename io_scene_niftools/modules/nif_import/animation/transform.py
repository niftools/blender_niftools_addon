"""This script contains classes to help import NIF controllers as blender bone or object level transform(ation) animations."""

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

import mathutils

from functools import singledispatch
from bisect import bisect_left
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import.animation import Animation
from io_scene_niftools.modules.nif_import.object import block_registry
from io_scene_niftools.utils import math
from io_scene_niftools.utils.logging import NifLog


def interpolate(x_out, x_in, y_in):
    """
    sample (x_in I y_in) at x coordinates x_out
    """
    y_out = []
    intervals = zip(x_in, x_in[1:], y_in, y_in[1:])
    slopes = [(y2 - y1) / (x2 - x1) for x1, x2, y1, y2 in intervals]
    # if we had just one input, slope will be 0 for constant extrapolation
    if not slopes:
        slopes = [0, ]
    for x in x_out:
        i = bisect_left(x_in, x) - 1
        # clamp to valid range
        i = max(min(i, len(slopes) - 1), 0)
        y_out.append(y_in[i] + slopes[i] * (x - x_in[i]))
    return y_out


class TransformAnimation(Animation):

    def __init__(self):
        super().__init__()
        self.import_kf_root = singledispatch(self.import_kf_root)
        self.import_kf_root.register(NifFormat.NiControllerSequence, self.import_controller_sequence)
        self.import_kf_root.register(NifFormat.NiSequenceStreamHelper, self.import_sequence_stream_helper)

    def import_kf_root(self, kf_root, b_armature_obj, bind_data):
        """Base method to warn user that this root type is not supported"""
        NifLog.warn(f"Unknown KF root block found : {kf_root.name:s}")
        NifLog.warn(f"This type isn't currently supported: {type(kf_root)}")

    def import_sequence_stream_helper(self, kf_root, b_armature_obj, bind_data):
        NifLog.debug('Importing NiSequenceStreamHelper...')
        b_action = self.create_action(b_armature_obj, kf_root.name.decode(), retrieve=False)
        # import parallel trees of extra datas and keyframe controllers
        extra = kf_root.extra_data
        controller = kf_root.controller
        while extra and controller:
            # textkeys in the stack do not specify node names, import as markers
            while isinstance(extra, NifFormat.NiTextKeyExtraData):
                self.import_text_key_extra_data(extra, b_action)
                extra = extra.next_extra_data

            # grabe the node name from string data
            bone_name = None
            if isinstance(extra, NifFormat.NiStringExtraData):
                node_name = extra.string_data.decode()
                bone_name = block_registry.get_bone_name_for_blender(node_name)
            # import keyframe controller
            if bone_name in bind_data:
                niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans = bind_data[bone_name]
                self.import_keyframe_controller(controller, b_armature_obj, bone_name, niBone_bind_scale,
                                                    niBone_bind_rot_inv, niBone_bind_trans)
            # grab next pair of extra and controller
            extra = extra.next_extra_data
            controller = controller.next_controller

    def import_controller_sequence(self, kf_root, b_armature_obj, bind_data):
        NifLog.debug('Importing NiControllerSequence...')
        b_action = self.create_action(b_armature_obj, kf_root.name.decode())

        # import text keys
        self.import_text_keys(kf_root, b_action)

        # go over all controlled blocks (NiKeyframeController)
        for controlledblock in kf_root.controlled_blocks:
            # get bone name
            # todo [pyffi] fixed get_node_name() is up, make release and clean up here
            # ZT2 - old way is not supported by pyffi's get_node_name()
            n_name = controlledblock.target_name
            # fallout (node_name) & Loki (StringPalette)
            if not n_name:
                n_name = controlledblock.get_node_name()
            bone_name = block_registry.get_bone_name_for_blender(n_name)
            if bone_name not in b_armature_obj.data.bones:
                continue
            b_bone = b_armature_obj.data.bones[bone_name]
            # import bone priority
            b_bone.niftools.priority = controlledblock.priority
            # import animation
            if bone_name in bind_data:
                niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans = bind_data[bone_name]
                # ZT2
                kfc = controlledblock.controller
                # fallout, Loki
                if not kfc:
                    kfc = controlledblock.interpolator
                if kfc:
                    self.import_keyframe_controller(kfc, b_armature_obj, bone_name, niBone_bind_scale,
                                                    niBone_bind_rot_inv, niBone_bind_trans)
        # fallout: set global extrapolation mode here (older versions have extrapolation per controller)
        if kf_root.cycle_type:
            extend = self.get_extend_from_cycle_type(kf_root.cycle_type)
            self.set_extrapolation(extend, b_action.fcurves)

    # TODO [animation] Is scale param required or can be removed, not used
    def import_keyframe_controller(self, n_kfc, b_obj, bone_name=None, n_bone_bind_scale=None, n_bone_bind_rot_inv=None, n_bone_bind_trans=None):

        NifLog.debug('Importing keyframe controller for'+b_obj.name)

        b_action = b_obj.animation_data.action

        if bone_name:
            b_obj = b_obj.pose.bones[bone_name]

        translations = []
        scales = []
        rotations = []
        eulers = []
        n_kfd = None

        # transform controllers (dartgun.nif)
        if isinstance(n_kfc, NifFormat.NiTransformController):
            if n_kfc.interpolator:
                n_kfd = n_kfc.interpolator.data
        # B-spline curve import
        elif isinstance(n_kfc, NifFormat.NiBSplineInterpolator):
            # used by WLP2 (tiger.kf), but only for non-LocRotScale data
            # eg. bone stretching - see controlledblock.get_variable_1()
            # do not support this for now, no good representation in Blender
            if isinstance(n_kfc, NifFormat.NiBSplineCompFloatInterpolator):
                # pyffi lacks support for this, but the following gets float keys
                # keys = list(kfc._getCompKeys(kfc.offset, 1, kfc.bias, kfc.multiplier))
                return
            times = list(n_kfc.get_times())
            # just do these temp steps to avoid generating empty fcurves down the line
            trans_temp = [mathutils.Vector(tup) for tup in n_kfc.get_translations()]
            if trans_temp:
                translations = zip(times, trans_temp)
            rot_temp = [mathutils.Quaternion(tup) for tup in n_kfc.get_rotations()]
            if rot_temp:
                rotations = zip(times, rot_temp)
            scale_temp = list(n_kfc.get_scales())
            if scale_temp:
                scales = zip(times, scale_temp)
            # Bsplines are Bezier curves
            interp_rot = interp_loc = interp_scale = "BEZIER"
        else:
            # ZT2 & Fallout
            n_kfd = n_kfc.data
        if isinstance(n_kfd, NifFormat.NiKeyframeData):
            interp_rot = self.get_b_interp_from_n_interp(n_kfd.rotation_type)
            interp_loc = self.get_b_interp_from_n_interp(n_kfd.translations.interpolation)
            interp_scale = self.get_b_interp_from_n_interp(n_kfd.scales.interpolation)
            if n_kfd.rotation_type == 4:
                b_obj.rotation_mode = "XYZ"
                # uses xyz rotation
                if n_kfd.xyz_rotations[0].keys:
                    # euler keys need not be sampled at the same time in KFs
                    # but we need complete key sets to do the space conversion
                    # so perform linear interpolation to import all keys properly

                    # get all the keys' times
                    times_x = [key.time for key in n_kfd.xyz_rotations[0].keys]
                    times_y = [key.time for key in n_kfd.xyz_rotations[1].keys]
                    times_z = [key.time for key in n_kfd.xyz_rotations[2].keys]
                    # the unique time stamps we have to sample all curves at
                    times_all = sorted(set(times_x + times_y + times_z))
                    # the actual resampling
                    x_r = interpolate(times_all, times_x, [key.value for key in n_kfd.xyz_rotations[0].keys])
                    y_r = interpolate(times_all, times_y, [key.value for key in n_kfd.xyz_rotations[1].keys])
                    z_r = interpolate(times_all, times_z, [key.value for key in n_kfd.xyz_rotations[2].keys])
                eulers = zip(times_all, zip(x_r, y_r, z_r))
            else:
                b_obj.rotation_mode = "QUATERNION"
                rotations = [(key.time, key.value) for key in n_kfd.quaternion_keys]

            if n_kfd.scales.keys:
                scales = [(key.time, key.value) for key in n_kfd.scales.keys]

            if n_kfd.translations.keys:
                translations = [(key.time, key.value) for key in n_kfd.translations.keys]

        # ZT2 - get extrapolation for every kfc
        if isinstance(n_kfc, NifFormat.NiKeyframeController):
            flags = n_kfc.flags
        # fallout, Loki - we set extrapolation according to the root NiControllerSequence.cycle_type
        else:
            flags = None
        
        if eulers:
            NifLog.debug('Rotation keys..(euler)')
            fcurves = self.create_fcurves(b_action, "rotation_euler", range(3), flags, bone_name)
            for t, val in eulers:
                key = mathutils.Euler(val)
                if bone_name:
                    key = math.import_keymat(n_bone_bind_rot_inv, key.to_matrix().to_4x4()).to_euler()
                self.add_key(fcurves, t, key, interp_rot)
        elif rotations:
            NifLog.debug('Rotation keys...(quaternions)')
            fcurves = self.create_fcurves(b_action, "rotation_quaternion", range(4), flags, bone_name)
            for t, val in rotations:
                key = mathutils.Quaternion([val.w, val.x, val.y, val.z])
                if bone_name:
                    key = math.import_keymat(n_bone_bind_rot_inv, key.to_matrix().to_4x4()).to_quaternion()
                self.add_key(fcurves, t, key, interp_rot)
        if translations:
            NifLog.debug('Translation keys...')
            fcurves = self.create_fcurves(b_action, "location", range(3), flags, bone_name)
            for t, val in translations:
                key = mathutils.Vector([val.x, val.y, val.z])
                if bone_name:
                    key = math.import_keymat(n_bone_bind_rot_inv, mathutils.Matrix.Translation(key - n_bone_bind_trans)).to_translation()
                self.add_key(fcurves, t, key, interp_loc)
        if scales:
            NifLog.debug('Scale keys...')
            fcurves = self.create_fcurves(b_action, "scale", range(3), flags, bone_name)
            for t, val in scales:
                key = (val, val, val)
                self.add_key(fcurves, t, key, interp_scale)

    def import_transforms(self, n_block, b_obj, bone_name=None):
        """Loads an animation attached to a nif block."""
        # find keyframe controller
        n_kfc = math.find_controller(n_block, NifFormat.NiKeyframeController)
        # try again
        if not n_kfc:
            n_kfc = math.find_controller(n_block, NifFormat.NiTransformController)
        if n_kfc:
            # skeletal animation
            if bone_name:
                bone_bm = math.import_matrix(n_block)  # base pose
                n_bone_bind_scale, n_bone_bind_rot, n_bone_bind_trans = math.decompose_srt(bone_bm)
                self.import_keyframe_controller(n_kfc, b_obj, bone_name, n_bone_bind_scale, n_bone_bind_rot.inverted(), n_bone_bind_trans)
            # object-level animation
            else:
                self.create_action(b_obj, b_obj.name + "-Anim")
                self.import_keyframe_controller(n_kfc, b_obj)
