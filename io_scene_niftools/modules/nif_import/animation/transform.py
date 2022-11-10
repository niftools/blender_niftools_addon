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

import bpy
import mathutils
import time

from functools import singledispatch
from bisect import bisect_left
from generated.formats.nif import classes as NifClasses

from io_scene_niftools.modules.nif_import.animation import Animation
from io_scene_niftools.modules.nif_import.object import block_registry
from io_scene_niftools.utils import math
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.consts import QUAT, EULER, LOC, SCALE


def as_b_quat(n_val):
    return mathutils.Quaternion([n_val.w, n_val.x, n_val.y, n_val.z])


def as_b_loc(n_val):
    return mathutils.Vector([n_val.x, n_val.y, n_val.z])


def as_b_scale(n_val):
    return n_val, n_val, n_val


def as_b_euler(n_val):
    return mathutils.Euler(n_val)


def correct_loc(key, n_bind_rot_inv, n_bind_trans):
    return math.import_keymat(n_bind_rot_inv, mathutils.Matrix.Translation(key - n_bind_trans)).to_translation()


def correct_quat(key, n_bind_rot_inv, n_bind_trans):
    return math.import_keymat(n_bind_rot_inv, key.to_matrix().to_4x4()).to_quaternion()


def correct_euler(key, n_bind_rot_inv, n_bind_trans):
    return math.import_keymat(n_bind_rot_inv, key.to_matrix().to_4x4()).to_euler()


def correct_scale(key, n_bind_rot_inv, n_bind_trans):
    return key


key_lut = {
    QUAT: (as_b_quat, correct_quat, 4),
    EULER: (as_b_euler, correct_euler, 3),
    LOC: (as_b_loc, correct_loc, 3),
    SCALE: (as_b_scale, correct_scale, 3),
}


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
        self.import_kf_root.register(NifClasses.NiControllerSequence, self.import_controller_sequence)
        self.import_kf_root.register(NifClasses.NiSequenceStreamHelper, self.import_sequence_stream_helper)
        self.import_kf_root.register(NifClasses.NiSequenceData, self.import_sequence_data)

    def get_bind_data(self, b_armature):
        """Get the required bind data of an armature. Used by standalone KF import and export. """
        self.bind_data = {}
        if b_armature:
            for b_bone in b_armature.data.bones:
                n_bind_scale, n_bind_rot, n_bind_trans = math.decompose_srt(math.get_object_bind(b_bone))
                self.bind_data[b_bone.name] = (n_bind_rot.inverted(), n_bind_trans)

    def get_target(self, b_armature_obj, n_name):
        """Gets a target for an anim controller"""
        b_name = block_registry.get_bone_name_for_blender(n_name)
        # if we have an armature, get the pose bone
        if b_armature_obj:
            if b_name in b_armature_obj.pose.bones:
                return b_armature_obj.pose.bones[b_name]
        # try to find the object for animation
        else:
            if b_name in bpy.data.objects:
                return bpy.data.objects[b_name]

    def import_kf_root(self, kf_root, b_armature_obj):
        """Base method to warn user that this root type is not supported"""
        NifLog.warn(f"Unknown KF root block found : {kf_root.name}")
        NifLog.warn(f"This type isn't currently supported: {type(kf_root)}")

    def import_generic_kf_root(self, kf_root):
        NifLog.debug(f'Importing {type(kf_root)}...')
        return kf_root.name

    def import_sequence_data(self, kf_root, b_armature_obj):
        b_action_name = self.import_generic_kf_root(kf_root)
        actions = set()
        for evaluator in kf_root.evaluators:
            b_target = self.get_target(b_armature_obj, evaluator.node_name)
            actions.add(self.import_keyframe_controller(evaluator, b_armature_obj, b_target, b_action_name))
        for b_action in actions:
            if b_action:
                self.import_text_keys(kf_root, b_action)
                if kf_root.cycle_type:
                    extend = self.get_extend_from_cycle_type(kf_root.cycle_type)
                    self.set_extrapolation(extend, b_action.fcurves)

    def import_sequence_stream_helper(self, kf_root, b_armature_obj):
        b_action_name = self.import_generic_kf_root(kf_root)
        actions = set()
        # import parallel trees of extra datas and keyframe controllers
        extra = kf_root.extra_data
        controller = kf_root.controller
        textkeys = None
        while extra and controller:
            # textkeys in the stack do not specify node names, import as markers
            while isinstance(extra, NifClasses.NiTextKeyExtraData):
                textkeys = extra
                extra = extra.next_extra_data

            # grabe the node name from string data
            if isinstance(extra, NifClasses.NiStringExtraData):
                b_target = self.get_target(b_armature_obj, extra.string_data)
                actions.add(self.import_keyframe_controller(controller, b_armature_obj, b_target, b_action_name))
            # grab next pair of extra and controller
            extra = extra.next_extra_data
            controller = controller.next_controller
        for b_action in actions:
            if b_action:
                self.import_text_key_extra_data(textkeys, b_action)

    def import_controller_sequence(self, kf_root, b_armature_obj):
        b_action_name = self.import_generic_kf_root(kf_root)
        actions = set()
        for controlledblock in kf_root.controlled_blocks:
            # get bone name
            # todo [pyffi] fixed get_node_name() is up, make release and clean up here
            # ZT2 - old way is not supported by pyffi's get_node_name()
            n_name = controlledblock.target_name
            # fallout (node_name) & Loki (StringPalette)
            if not n_name:
                n_name = controlledblock.get_node_name()
            b_target = self.get_target(b_armature_obj, n_name)
            # todo - temporarily disabled! should become a custom property on both object and pose bone, ideally
            # import bone priority
            # b_target.niftools.priority = controlledblock.priority
            # fallout, Loki
            kfc = controlledblock.interpolator
            if not kfc:
                # ZT2
                kfc = controlledblock.controller
            if kfc:
                actions.add(self.import_keyframe_controller(kfc, b_armature_obj, b_target, b_action_name))
        for b_action in actions:
            if b_action:
                self.import_text_keys(kf_root, b_action)
                # fallout: set global extrapolation mode here (older versions have extrapolation per controller)
                if kf_root.cycle_type:
                    extend = self.get_extend_from_cycle_type(kf_root.cycle_type)
                    self.set_extrapolation(extend, b_action.fcurves)

    def import_keyframe_controller(self, n_kfc, b_armature, b_target, b_action_name):
        """
        Imports a keyframe controller as fcurves in an action, which is created if necessary.
        n_kfc: some nif struct that has keyframe data, somewhere
        b_armature: either None or Object (blender armature)
        b_target: either Object or PoseBone
        b_action_name: name of the action that should be used; the actual imported name may differ due to suffixes
        """
        # the target may not exist in the scene, in which case it is None here
        if not b_target:
            return
        NifLog.debug(f'Importing keyframe controller for {b_target.name}')

        n_kfd = None
        # fallout, Loki - we set extrapolation according to the root NiControllerSequence.cycle_type
        flags = None
        n_bind_rot_inv = n_bind_trans = None

        # create or get the action
        if b_armature and isinstance(b_target, bpy.types.PoseBone):
            # action on armature, one per armature
            b_action = self.create_action(b_armature, b_action_name)
            if b_target.name in self.bind_data:
                n_bind_rot_inv, n_bind_trans = self.bind_data[b_target.name]
            bone_name = b_target.name
        else:
            # one action per object
            b_action = self.create_action(b_target, f"{b_action_name}_{b_target.name}")
            bone_name = None

        # B-spline curve import
        if isinstance(n_kfc, NifClasses.NiBSplineInterpolator):
            # Bsplines are Bezier curves
            interp = "BEZIER"
            if isinstance(n_kfc, NifClasses.NiBSplineCompFloatInterpolator):
                # used by WLP2 (tiger.kf), but only for non-LocRotScale data
                # eg. bone stretching - see controlledblock.get_variable_1()
                # do not support this for now, no good representation in Blender
                # pyffi lacks support for this, but the following gets float keys
                # keys = list(kfc._getCompKeys(kfc.offset, 1, kfc.bias, kfc.multiplier))
                return
            times = list(n_kfc.get_times())
            keys = list(n_kfc.get_translations())
            self.import_keys(LOC, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)
            keys = list(n_kfc.get_rotations())
            self.import_keys(QUAT, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)
            keys = list(n_kfc.get_scales())
            self.import_keys(SCALE, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)
        elif isinstance(n_kfc, NifClasses.NiMultiTargetTransformController):
            # not sure what this is used for
            return
        n_kfd = self.get_controller_data(n_kfc)
        # ZT2 - get extrapolation for every kfc
        if isinstance(n_kfc, NifClasses.NiKeyframeController):
            flags = n_kfc.flags
        if isinstance(n_kfd, NifClasses.NiKeyframeData):
            if n_kfd.rotation_type == 4:
                b_target.rotation_mode = "XYZ"
                # euler keys need not be sampled at the same time in KFs
                # but we need complete key sets to do the space conversion
                # so perform linear interpolation to import all keys properly

                # get all the times and keys for each coordinate
                times_keys = [self.get_keys_values(euler.keys) for euler in n_kfd.xyz_rotations]
                # the unique time stamps we have to sample all curves at
                times_all = sorted(set(times_keys[0][0] + times_keys[1][0] + times_keys[2][0]))
                # todo - this assumes that all three channels are keyframed, but it seems like this need not be the case
                # resample each coordinate for all times
                keys_res = [interpolate(times_all, times, keys) for times, keys in times_keys]
                # for eulers, the actual interpolation type is apparently stored per channel
                interp = self.get_b_interp_from_n_interp(n_kfd.xyz_rotations[0].interpolation)
                self.import_keys(EULER, b_action, bone_name, times_all, zip(*keys_res), flags, interp, n_bind_rot_inv, n_bind_trans)
            else:
                b_target.rotation_mode = "QUATERNION"
                times, keys = self.get_keys_values(n_kfd.quaternion_keys)
                interp = self.get_b_interp_from_n_interp(n_kfd.rotation_type)
                self.import_keys(QUAT, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)
            times, keys = self.get_keys_values(n_kfd.scales.keys)
            interp = self.get_b_interp_from_n_interp(n_kfd.scales.interpolation)
            self.import_keys(SCALE, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)

            times, keys = self.get_keys_values(n_kfd.translations.keys)
            interp = self.get_b_interp_from_n_interp(n_kfd.translations.interpolation)
            self.import_keys(LOC, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans)

        return b_action

    def import_keys(self, key_type, b_action, bone_name, times, keys, flags, interp, n_bind_rot_inv, n_bind_trans):
        """Imports key frames according to the specified key_type"""
        if not keys:
            return
        # look up conventions by key type
        key_func, key_corrector, key_dim = key_lut[key_type]
        NifLog.debug(f'{key_type} keys...')
        # convert nif keys to proper key type for blender
        keys = [key_func(val) for val in keys]
        # correct for bone space if target is an armature bone
        if bone_name:
            keys = [key_corrector(key, n_bind_rot_inv, n_bind_trans) for key in keys]
        self.add_keys(b_action, key_type, range(key_dim), flags, times, keys, interp, bone_name=bone_name)

    def import_transforms(self, n_block, b_obj, bone_name=None):
        """Loads an animation attached to a nif block."""
        # find keyframe controller
        n_kfc = math.find_controller(n_block, (NifClasses.NiKeyframeController, NifClasses.NiTransformController))
        if n_kfc:
            # skeletal animation
            if bone_name:
                p_bone = b_obj.pose.bones[bone_name]
                self.import_keyframe_controller(n_kfc, b_obj, p_bone, f"{b_obj.name}_Anim")
            # object-level animation
            else:
                self.import_keyframe_controller(n_kfc, None, b_obj, f"{b_obj.name}_Anim")

    def import_controller_manager(self, n_block, b_obj, b_armature):
        ctrlm = n_block.controller
        if ctrlm and isinstance(ctrlm, NifClasses.NiControllerManager):
            NifLog.debug(f'Importing NiControllerManager')
            if b_armature:
                self.get_bind_data(b_armature)
            for ctrl in ctrlm.controller_sequences:
                self.import_kf_root(ctrl, b_armature)

