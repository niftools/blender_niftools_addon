"""This script contains classes to help import animations."""

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
import bpy

from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import import animation
from io_scene_niftools.utils.logging import NifLog

FPS = 30


class Animation:

    def __init__(self):
        self.show_pose_markers()

    @staticmethod
    def show_pose_markers():
        """Helper function to ensure that pose markers are shown"""
        for screen in bpy.data.screens:
            for area in screen.areas:
                for space in area.spaces:
                    if space.type == 'DOPESHEET_EDITOR':
                        space.show_pose_markers = True

    @staticmethod
    def get_b_interp_from_n_interp(n_ipol):
        if n_ipol in (NifFormat.KeyType.LINEAR_KEY, NifFormat.KeyType.XYZ_ROTATION_KEY):
            return "LINEAR"
        elif n_ipol == NifFormat.KeyType.QUADRATIC_KEY:
            return "BEZIER"
        elif n_ipol == 0:
            # guessing, not documented in nif.xml
            return "CONSTANT"
        # NifLog.warn(f"Unsupported interpolation mode ({n_ipol}) in nif, using quadratic/bezier.")
        return "BEZIER"

    @staticmethod
    def create_action(b_obj, action_name, retrieve=True):
        """ Create or retrieve action and set it as active on the object. """
        # could probably skip this test and create always
        if not b_obj.animation_data:
            b_obj.animation_data_create()
        if retrieve and action_name in bpy.data.actions:
            b_action = bpy.data.actions[action_name]
        else:
            b_action = bpy.data.actions.new(action_name)
        # set as active action on object
        b_obj.animation_data.action = b_action
        return b_action

    def create_fcurves(self, action, dtype, drange, flags=None, bonename=None, keyname=None):
        """ Create fcurves in action for desired conditions. """
        # armature pose bone animation
        if bonename:
            fcurves = [
                action.fcurves.new(data_path=f'pose.bones["{bonename}"].{dtype}', index=i, action_group=bonename)
                for i in drange]
        # shapekey pose bone animation
        elif keyname:
            fcurves = [
                action.fcurves.new(data_path=f'key_blocks["{keyname}"].{dtype}', index=0,)
            ]
        else:
            # Object animation (non-skeletal) is lumped into the "LocRotScale" action_group
            if dtype in ("rotation_euler", "rotation_quaternion", "location", "scale"):
                action_group = "LocRotScale"
            # Non-transformaing animations (eg. visibility or material anims) use no action groups
            else:
                action_group = ""
            fcurves = [action.fcurves.new(data_path=dtype, index=i, action_group=action_group) for i in drange]
        if flags:
            self.set_extrapolation(self.get_extend_from_flags(flags), fcurves)
        return fcurves

    @staticmethod
    def get_extend_from_flags(flags):
        if flags & 6 == 4:  # 0b100
            return "CONSTANT"
        elif flags & 6 == 0:  # 0b000
            return "CYCLIC"

        NifLog.warn("Unsupported cycle mode in nif, using clamped.")
        return "CONSTANT"

    @staticmethod
    def get_extend_from_cycle_type(cycle_type):
        return ("CYCLIC", "REVERSE", "CONSTANT")[cycle_type]

    @staticmethod
    def set_extrapolation(extend_type, fcurves):
        if extend_type == "CONSTANT":
            for fcurve in fcurves:
                fcurve.extrapolation = 'CONSTANT'
        elif extend_type == "CYCLIC":
            for fcurve in fcurves:
                fcurve.modifiers.new('CYCLES')
        # don't support reverse for now, not sure if it is even possible in blender
        else:
            NifLog.warn("Unsupported extrapolation mode, using clamped.")
            for fcurve in fcurves:
                fcurve.extrapolation = 'CONSTANT'

    def add_key(self, fcurves, t, key, interp):
        """
        Add a key (len=n) to a set of fcurves (len=n) at the given frame. Set the key's interpolation to interp.
        """
        frame = round(t * animation.FPS)
        for fcurve, k in zip(fcurves, key):
            fcurve.keyframe_points.insert(frame, k).interpolation = interp

    # import animation groups
    def import_text_keys(self, n_block, b_action):
        """Gets and imports a NiTextKeyExtraData"""
        if isinstance(n_block, NifFormat.NiControllerSequence):
            txk = n_block.text_keys
        else:
            txk = n_block.find(block_type=NifFormat.NiTextKeyExtraData)
        self.import_text_key_extra_data(txk, b_action)

    def import_text_key_extra_data(self, txk, b_action):
        """Stores the text keys as pose markers in a blender action."""
        if txk and b_action:
            for key in txk.text_keys:
                newkey = key.value.decode().replace('\r\n', '/').rstrip('/')
                frame = round(key.time * animation.FPS)
                marker = b_action.pose_markers.new(newkey)
                marker.frame = frame

    @staticmethod
    def set_frames_per_second(roots):
        """Scan all blocks and set a reasonable number for FPS to this class and the scene."""
        # find all key times
        key_times = []
        for root in roots:
            for kfd in root.tree(block_type=NifFormat.NiKeyframeData):
                key_times.extend(key.time for key in kfd.translations.keys)
                key_times.extend(key.time for key in kfd.scales.keys)
                key_times.extend(key.time for key in kfd.quaternion_keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[0].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[1].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[2].keys)

            for kfi in root.tree(block_type=NifFormat.NiBSplineInterpolator):
                if not kfi.basis_data:
                    # skip bsplines without basis data (eg bowidle.kf in Oblivion)
                    continue
                key_times.extend(
                    point * (kfi.stop_time - kfi.start_time)
                    / (kfi.basis_data.num_control_points - 2)
                    for point in range(kfi.basis_data.num_control_points - 2))

            for uv_data in root.tree(block_type=NifFormat.NiUVData):
                for uv_group in uv_data.uv_groups:
                    key_times.extend(key.time for key in uv_group.keys)

        # not animated, return a reasonable default
        if not key_times:
            return

        # calculate FPS
        key_times = sorted(set(key_times))
        fps = animation.FPS
        lowest_diff = sum(abs(int(time * fps + 0.5) - (time * fps)) for time in key_times)

        # for test_fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 24, 25, 30, 35]:
            diff = sum(abs(int(time * test_fps + 0.5) - (time * test_fps)) for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        NifLog.info(f"Animation estimated at {fps} frames per second.")
        animation.FPS = fps
        bpy.context.scene.render.fps = fps
        bpy.context.scene.frame_set(0)
