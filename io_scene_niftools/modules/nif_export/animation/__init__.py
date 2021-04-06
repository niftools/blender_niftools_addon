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
from abc import ABC

import bpy
from pyffi.formats.nif import NifFormat

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export import animation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils.singleton import NifOp, NifData
from io_scene_niftools.utils.logging import NifLog

# FPS = 30


class Animation(ABC):

    def __init__(self):
        self.fps = bpy.context.scene.render.fps

    def set_flags_and_timing(self, kfc, exp_fcurves, start_frame=None, stop_frame=None):
        # fill in the non-trivial values
        kfc.flags = 8  # active
        kfc.flags |= self.get_flags_from_fcurves(exp_fcurves)
        kfc.frequency = 1.0
        kfc.phase = 0.0
        if not start_frame and not stop_frame:
            start_frame, stop_frame = exp_fcurves[0].range()
        # todo [anim] this is a hack, move to scene
        kfc.start_time = start_frame / self.fps
        kfc.stop_time = stop_frame / self.fps

    @staticmethod
    def get_flags_from_fcurves(fcurves):
        # see if there are cyclic extrapolation modifiers on exp_fcurves
        cyclic = False
        for fcu in fcurves:
            # sometimes fcurves can include empty fcurves - see uv controller export
            if fcu:
                for mod in fcu.modifiers:
                    if mod.type == "CYCLES":
                        cyclic = True
                        break
        if cyclic:
            return 0
        else:
            return 4  # 0b100

    @staticmethod
    def get_active_action(b_obj):
        # check if the blender object has a non-empty action assigned to it
        if b_obj:
            if b_obj.animation_data and b_obj.animation_data.action:
                b_action = b_obj.animation_data.action
                if b_action.fcurves:
                    return b_action

    @staticmethod
    def get_controllers(nodes):
        """find all nodes and relevant controllers"""
        node_kfctrls = {}
        for node in nodes:
            if not isinstance(node, NifFormat.NiAVObject):
                continue
            # get list of all controllers for this node
            ctrls = node.get_controllers()
            for ctrl in ctrls:
                if bpy.context.scene.niftools_scene.game == 'MORROWIND':
                    # morrowind: only keyframe controllers
                    if not isinstance(ctrl, NifFormat.NiKeyframeController):
                        continue
                if node not in node_kfctrls:
                    node_kfctrls[node] = []
                node_kfctrls[node].append(ctrl)
        return node_kfctrls

    @staticmethod
    def create_controller(parent_block, target_name, priority=0):
        # todo[anim] - make independent of global NifData.data.version, and move check for NifOp.props.animation outside
        n_kfi = None
        n_kfc = None

        try:
            if NifOp.props.animation == 'GEOM_NIF' and NifData.data.version < 0x0A020000:
                # keyframe controllers are not present in geometry only files
                # for more recent versions, the controller and interpolators are
                # present, only the data is not present (see further on)
                return n_kfc, n_kfi
        except AttributeError:
            # kf export has no animation mode
            pass

        # add a KeyframeController block, and refer to this block in the
        # parent's time controller
        if NifData.data.version < 0x0A020000:
            n_kfc = block_store.create_block("NiKeyframeController", None)
        else:
            n_kfc = block_store.create_block("NiTransformController", None)
            n_kfi = block_store.create_block("NiTransformInterpolator", None)
            # link interpolator from the controller
            n_kfc.interpolator = n_kfi
        # if parent is a node, attach controller to that node
        if isinstance(parent_block, NifFormat.NiNode):
            parent_block.add_controller(n_kfc)
            if n_kfi:
                # set interpolator default data
                n_kfi.scale, n_kfi.rotation, n_kfi.translation = parent_block.get_transform().get_scale_quat_translation()

        # else ControllerSequence, so create a link
        elif isinstance(parent_block, NifFormat.NiControllerSequence):
            controlled_block = parent_block.add_controlled_block()
            controlled_block.priority = priority
            if NifData.data.version < 0x0A020000:
                # older versions need the actual controller blocks
                controlled_block.target_name = target_name
                controlled_block.controller = n_kfc
                # erase reference to target node
                n_kfc.target = None
            else:
                # newer versions need the interpolator blocks
                controlled_block.interpolator = n_kfi
                controlled_block.node_name = target_name
                controlled_block.controller_type = "NiTransformController"
        else:
            raise io_scene_niftools.utils.logging.NifError("Unsupported KeyframeController parent!")
        
        return n_kfc, n_kfi

    # todo [anim] currently not used, maybe reimplement this
    @staticmethod
    def get_n_interp_from_b_interp(b_ipol):
        if b_ipol == "LINEAR":
            return NifFormat.KeyType.LINEAR_KEY
        elif b_ipol == "BEZIER":
            return NifFormat.KeyType.QUADRATIC_KEY
        elif b_ipol == "CONSTANT":
            return NifFormat.KeyType.CONST_KEY

        NifLog.warn(f"Unsupported interpolation mode ({b_ipol}) in blend, using quadratic/bezier.")
        return NifFormat.KeyType.QUADRATIC_KEY
    
    def add_dummy_markers(self, b_action):
        # if we exported animations, but no animation groups are defined,
        # define a default animation group
        NifLog.info("Checking action pose markers.")
        if not b_action.pose_markers:
            # has_controllers = False
            # for block in block_store.block_to_obj:
            #     # has it a controller field?
            #     if isinstance(block, NifFormat.NiObjectNET):
            #         if block.controller:
            #             has_controllers = True
            #             break
            # if has_controllers:
            NifLog.info("Defining default action pose markers.")
            for frame, text in zip(b_action.frame_range, ("Idle: Start/Idle: Loop Start", "Idle: Loop Stop/Idle: Stop")):
                marker = b_action.pose_markers.new(text)
                marker.frame = frame
