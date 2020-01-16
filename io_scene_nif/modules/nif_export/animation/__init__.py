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

from io_scene_nif.modules.nif_export.animation.material import MaterialAnimation
from io_scene_nif.modules.nif_export.animation.morph import MorphAnimation
from io_scene_nif.modules.nif_export.animation.object import ObjectAnimation
from io_scene_nif.modules.nif_export.animation.texture import TextureAnimation
from io_scene_nif.modules.nif_export.animation.transform import TransformAnimation
from io_scene_nif.modules.nif_import.object.block_registry import block_store
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog

FPS = 30


class Animation:

    def __init__(self, parent):
        self.nif_export = parent
        self.object = ObjectAnimation(self)
        self.material = MaterialAnimation(self)
        self.texture = TextureAnimation()
        self.transform = TransformAnimation(parent)
        self.morph = MorphAnimation(self)
        # todo [scene / anim] move to scene?
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
        
    def get_active_action(self, b_obj):
        # check if the blender object has a non-empty action assigned to it
        if b_obj:
            if b_obj.animation_data and b_obj.animation_data.action:
                b_action = b_obj.animation_data.action
                if b_action.fcurves:
                    return b_action

    def export_kf_root(self, b_armature = None):
        # todo [anim] export them properly, in the right tree to begin with
        # find all nodes and relevant controllers
        # node_kfctrls = self.get_controllers( root_block.tree() )

        # morrowind
        if NifOp.props.game in ('MORROWIND', 'FREEDOM_FORCE'):
            # create kf root header
            kf_root = block_store.create_block("NiSequenceStreamHelper")
            # kf_root.add_extra_data(anim_textextra)
            # # reparent controller tree
            # for node, ctrls in node_kfctrls.items():
            #     for ctrl in ctrls:
            #         # create node reference by name
            #         nodename_extra = block_store.create_block("NiStringExtraData")
            #         nodename_extra.bytes_remaining = len(node.name) + 4
            #         nodename_extra.string_data = node.name

            #         # break the controller chain
            #         ctrl.next_controller = None

            #         # add node reference and controller
            #         kf_root.add_extra_data(nodename_extra)
            #         kf_root.add_controller(ctrl)
            #         # wipe controller target
            #         ctrl.target = None

        # oblivion
        elif NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'CIVILIZATION_IV', 'ZOO_TYCOON_2', 'FREEDOM_FORCE_VS_THE_3RD_REICH'):
            # TODO [animation] allow for object kf only

            # create kf root header
            kf_root = block_store.create_block("NiControllerSequence")
            targetname = "Scene Root"

            # per-node animation
            if b_armature:
                b_action = self.get_active_action(b_armature)
                for b_bone in b_armature.data.bones:
                    self.transform.export_transforms(kf_root, b_armature, b_action, b_bone)
                # quick hack to set correct target name
                if "Bip01" in b_armature.data.bones:
                    targetname = "Bip01"
                elif "Bip02" in b_armature.data.bones:
                    targetname = "Bip02"

            # per-object animation
            else:
                for b_obj in bpy.data.objects:
                    b_action = self.get_active_action(b_obj)
                    self.transform.export_transforms(kf_root, b_obj, b_action)

            anim_textextra = self.export_text_keys(b_action)

            kf_root.name = b_action.name
            kf_root.unknown_int_1 = 1
            kf_root.weight = 1.0
            kf_root.text_keys = anim_textextra
            kf_root.cycle_type = NifFormat.CycleType.CYCLE_CLAMP
            kf_root.frequency = 1.0
            kf_root.start_time = bpy.context.scene.frame_start * bpy.context.scene.render.fps
            kf_root.stop_time = (bpy.context.scene.frame_end - bpy.context.scene.frame_start) * bpy.context.scene.render.fps

            kf_root.target_name = targetname
            kf_root.string_palette = NifFormat.NiStringPalette()
        
            # todo [anim] the following seems to be post-processing of morph controllers
            # this will probably end up as redundant after refactoring is done
            # keep it here for now
            # for node, ctrls in zip(iter(node_kfctrls.keys()), iter(node_kfctrls.values())):
                # # export a block for every interpolator in every controller
                # for ctrl in ctrls:
                    # # XXX add get_interpolators to pyffi interface
                    # if isinstance(ctrl, NifFormat.NiSingleInterpController):
                        # interpolators = [ctrl.interpolator]
                    # elif isinstance( ctrl, (NifFormat.NiGeomMorpherController, NifFormat.NiMorphWeightsController)):
                        # interpolators = ctrl.interpolators

                    # if isinstance(ctrl, NifFormat.NiGeomMorpherController):
                        # variable_2s = [morph.frame_name for morph in ctrl.data.morphs]
                    # else:
                        # variable_2s = [None for interpolator in interpolators]
                    # for interpolator, variable_2 in zip(interpolators, variable_2s):
                        # # create ControlledLink for each interpolator
                        # controlledblock = kf_root.add_controlled_block()
                        # if self.version < 0x0A020000:
                            # # older versions need the actual controller blocks
                            # controlledblock.target_name = node.name
                            # controlledblock.controller = ctrl
                            # # erase reference to target node
                            # ctrl.target = None
                        # else:
                            # # newer versions need the interpolator blocks
                            # controlledblock.interpolator = interpolator
                            
                        # # set palette, and node and controller type names, and variables
                        # controlledblock.string_palette = kf_root.string_palette
                        # controlledblock.set_node_name(node.name)
                        # controlledblock.set_controller_type(ctrl.__class__.__name__)
                        # if variable_2:
                            # controlledblock.set_variable_2(variable_2)
        else:
            raise nif_utils.NifError("Keyframe export for '%s' is not supported.\nOnly Morrowind, Oblivion, Fallout 3, Civilization IV,"
                                        " Zoo Tycoon 2, Freedom Force, and Freedom Force vs. the 3rd Reich keyframes are supported." % NifOp.props.game)
        return kf_root
    
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
                if NifOp.props.game == 'MORROWIND':
                    # morrowind: only keyframe controllers
                    if not isinstance(ctrl, NifFormat.NiKeyframeController):
                        continue
                if node not in node_kfctrls:
                    node_kfctrls[node] = []
                node_kfctrls[node].append(ctrl)
        return node_kfctrls
    
    def create_controller(self, parent_block, target_name, priority = 0):
        n_kfi = None
        n_kfc = None
        
        if NifOp.props.animation == 'GEOM_NIF' and NifOp.props.version < 0x0A020000:
            # keyframe controllers are not present in geometry only files
            # for more recent versions, the controller and interpolators are
            # present, only the data is not present (see further on)
            return n_kfc, n_kfi

        # add a KeyframeController block, and refer to this block in the
        # parent's time controller
        if NifOp.props.version < 0x0A020000:
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
            if self.nif_export.version < 0x0A020000:
                # older versions need the actual controller blocks
                controlled_block.target_name = target_name
                controlled_block.controller = n_kfc
                # erase reference to target node
                n_kfc.target = None
            else:
                # newer versions need the interpolator blocks
                controlled_block.interpolator = n_kfi
        else:
            raise nif_utils.NifError("Unsupported KeyframeController parent!")
        
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

        NifLog.warn("Unsupported interpolation mode ({0}) in blend, using quadratic/bezier.".format(b_ipol))
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
            for frame, text in zip(b_action.frame_range, ("Idle: Start/Idle: Loop Start", "Idle: Loop Stop/Idle: Stop") ):
                marker = b_action.pose_markers.new(text)
                marker.frame = frame

    def export_text_keys(self, b_action):
        """Process b_action's pose markers and return an extra string data block."""
        if NifOp.props.animation == 'GEOM_NIF':
            # animation group extra data is not present in geometry only files
            return
        NifLog.info("Exporting animation groups")

        self.add_dummy_markers(b_action)

        # add a NiTextKeyExtraData block
        n_text_extra = block_store.create_block("NiTextKeyExtraData", b_action.pose_markers)

        # create a text key for each frame descriptor
        n_text_extra.num_text_keys = len(b_action.pose_markers)
        n_text_extra.text_keys.update_size()
        f0, f1 = b_action.frame_range
        for key, marker in zip(n_text_extra.text_keys, b_action.pose_markers):
            f = marker.frame
            if (f < f0) or (f > f1):
                NifLog.warn("Marker out of animated range ({0} not between [{1}, {2}])".format(
                    f, f0, f1))

            key.time = f / self.fps
            key.value = marker.name.replace('/', '\r\n')

        return n_text_extra
