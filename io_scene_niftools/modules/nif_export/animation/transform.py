"""This script contains classes to help export blender bone or object level transform(ation) animations into NIF controllers."""

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

from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_export.animation import Animation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifError, NifLog


class TransformAnimation(Animation):

    def __init__(self):
        super().__init__()

    @staticmethod
    def iter_frame_key(fcurves, mathutilclass):
        """
        Iterator that yields a tuple of frame and key for all fcurves.
        Assumes the fcurves are sampled at the same time and all have the same amount of keys
        Return the key in the desired MathutilsClass
        """
        for point in zip(*[fcu.keyframe_points for fcu in fcurves]):
            frame = point[0].co[0]
            key = [k.co[1] for k in point]
            yield frame, mathutilclass(key)

    def export_kf_root(self, b_armature=None):
        # todo [anim] export them properly, in the right tree to begin with
        # find all nodes and relevant controllers
        # node_kfctrls = self.get_controllers( root_block.tree() )

        # morrowind
        if bpy.context.scene.niftools_scene.game in ('MORROWIND', 'FREEDOM_FORCE'):
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

        # skyrim
        elif bpy.context.scene.niftools_scene.game in ('SKYRIM'):

            if b_armature:
                NifLog.info(f"Skyrim: Exporting animation on the skeleton: {b_armature.name}")
                b_action = self.get_active_action(b_armature)
                kf_root = block_store.create_block("NiControllerSequence")
                targetname = "Scene Root"
                for bone in b_armature.data.bones:
                    self.export_transforms(kf_root,b_armature,b_action,bone)

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

            else:
                NifError("Cannot export animation without skeleton")

        # oblivion
        elif bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'CIVILIZATION_IV', 'ZOO_TYCOON_2', 'FREEDOM_FORCE_VS_THE_3RD_REICH'):
            # TODO [animation] allow for object kf only

            # create kf root header
            kf_root = block_store.create_block("NiControllerSequence")
            targetname = "Scene Root"

            # per-node animation
            if b_armature:
                b_action = self.get_active_action(b_armature)
                for b_bone in b_armature.data.bones:
                    self.export_transforms(kf_root, b_armature, b_action, b_bone)
                # quick hack to set correct target name
                if "Bip01" in b_armature.data.bones:
                    targetname = "Bip01"
                elif "Bip02" in b_armature.data.bones:
                    targetname = "Bip02"

            # per-object animation
            else:
                for b_obj in bpy.data.objects:
                    b_action = self.get_active_action(b_obj)
                    self.export_transforms(kf_root, b_obj, b_action)

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
            raise NifError(f"Keyframe export for '{bpy.context.scene.niftools_scene.game}' is not supported.\nOnly Morrowind, Oblivion, Skyrim, Fallout 3, Civilization IV,"
                                     " Zoo Tycoon 2, Freedom Force, and Freedom Force vs. the 3rd Reich keyframes are supported.")
        return kf_root

    def export_transforms(self, parent_block, b_obj, b_action, bone=None):
        """
        If bone == None, object level animation is exported.
        If a bone is given, skeletal animation is exported.
        """

        # b_action may be None, then nothing is done.
        if not b_action:
            return

        # blender object must exist
        assert b_obj
        # if a bone is given, b_obj must be an armature
        if bone:
            assert type(b_obj.data) == bpy.types.Armature

        # just for more detailed error reporting later on
        bonestr = ""

        # skeletal animation - with bone correction & coordinate corrections
        if bone and bone.name in b_action.groups:
            # get bind matrix for bone or object
            bind_matrix = math.get_object_bind(bone)
            exp_fcurves = b_action.groups[bone.name].channels
            # just for more detailed error reporting later on
            bonestr = " in bone " + bone.name
            target_name = block_store.get_full_name(bone)
            priority = bone.niftools.priority

        # object level animation - no coordinate corrections
        elif not bone:

            # raise error on any objects parented to bones
            if b_obj.parent and b_obj.parent_type == "BONE":
                raise NifError("{} is parented to a bone AND has animations. The nif format does not support this!".format(b_obj.name))

            target_name = block_store.get_full_name(b_obj)
            priority = 0

            # we have either a root object (Scene Root), in which case we take the coordinates without modification
            # or a generic object parented to an empty = node
            # objects may have an offset from their parent that is not apparent in the user input (ie. UI values and keyframes)
            # we want to export matrix_local, and the keyframes are in matrix_basis, so do:
            # matrix_local = matrix_parent_inverse * matrix_basis
            bind_matrix = b_obj.matrix_parent_inverse
            exp_fcurves = [fcu for fcu in b_action.fcurves if fcu.data_path in ("rotation_quaternion", "rotation_euler", "location", "scale")]

        else:
            # bone isn't keyframed in this action, nothing to do here
            return

        # decompose the bind matrix
        bind_scale, bind_rot, bind_trans = math.decompose_srt(bind_matrix)
        n_kfc, n_kfi = self.create_controller(parent_block, target_name, priority)

        # fill in the non-trivial values
        start_frame, stop_frame = b_action.frame_range
        self.set_flags_and_timing(n_kfc, exp_fcurves, start_frame, stop_frame)

        # get the desired fcurves for each data type from exp_fcurves
        quaternions = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("quaternion")]
        translations = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("location")]
        eulers = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("euler")]
        scales = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("scale")]

        # ensure that those groups that are present have all their fcurves
        for fcus, num_fcus in ((quaternions, 4), (eulers, 3), (translations, 3), (scales, 3)):
            if fcus and len(fcus) != num_fcus:
                raise NifError("Incomplete key set {} for action {}. Ensure that if a bone is keyframed for a property, all channels are keyframed.".format(bonestr, b_action.name))

        # go over all fcurves collected above and transform and store all their keys
        quat_curve = []
        euler_curve = []
        trans_curve = []
        scale_curve = []
        for frame, quat in self.iter_frame_key(quaternions, mathutils.Quaternion):
            quat = math.export_keymat(bind_rot, quat.to_matrix().to_4x4(), bone).to_quaternion()
            quat_curve.append((frame, quat))

        for frame, euler in self.iter_frame_key(eulers, mathutils.Euler):
            keymat = math.export_keymat(bind_rot, euler.to_matrix().to_4x4(), bone)
            euler = keymat.to_euler("XYZ", euler)
            euler_curve.append((frame, euler))

        for frame, trans in self.iter_frame_key(translations, mathutils.Vector):
            keymat = math.export_keymat(bind_rot, mathutils.Matrix.Translation(trans), bone)
            trans = keymat.to_translation() + bind_trans
            trans_curve.append((frame, trans))

        for frame, scale in self.iter_frame_key(scales, mathutils.Vector):
            # just use the first scale curve and assume even scale over all curves
            scale_curve.append((frame, scale[0]))

        if n_kfi:
            if max(len(c) for c in (quat_curve, euler_curve, trans_curve, scale_curve)) > 1:
                # number of frames is > 1, so add transform data
                n_kfd = block_store.create_block("NiTransformData", exp_fcurves)
                n_kfi.data = n_kfd
            else:
                # only add data if number of keys is > 1
                # (see importer comments with import_kf_root: a single frame
                # keyframe denotes an interpolator without further data)
                # insufficient keys, so set the data and we're done!
                if trans_curve:
                    trans = trans_curve[0][1]
                    n_kfi.translation.x, n_kfi.translation.y, n_kfi.translation.z = trans

                if quat_curve:
                    quat = quat_curve[0][1]
                elif euler_curve:
                    quat = euler_curve[0][1].to_quaternion()

                if quat_curve or euler_curve:
                    n_kfi.rotation.x = quat.x
                    n_kfi.rotation.y = quat.y
                    n_kfi.rotation.z = quat.z
                    n_kfi.rotation.w = quat.w
                # ignore scale for now...
                n_kfi.scale = 1.0
                # no need to add any keys, done
                return

        else:
            # add the keyframe data
            n_kfd = block_store.create_block("NiKeyframeData", exp_fcurves)
            n_kfc.data = n_kfd

        # TODO [animation] support other interpolation modes, get interpolation from blender?
        #                  probably requires additional data like tangents and stuff

        # finally we can export the data calculated above
        if euler_curve:
            n_kfd.rotation_type = NifFormat.KeyType.XYZ_ROTATION_KEY
            n_kfd.num_rotation_keys = 1  # *NOT* len(frames) this crashes the engine!
            for i, coord in enumerate(n_kfd.xyz_rotations):
                coord.num_keys = len(euler_curve)
                coord.interpolation = NifFormat.KeyType.LINEAR_KEY
                coord.keys.update_size()
                for key, (frame, euler) in zip(coord.keys, euler_curve):
                    key.time = frame / self.fps
                    key.value = euler[i]
        elif quat_curve:
            n_kfd.rotation_type = NifFormat.KeyType.QUADRATIC_KEY
            n_kfd.num_rotation_keys = len(quat_curve)
            n_kfd.quaternion_keys.update_size()
            for key, (frame, quat) in zip(n_kfd.quaternion_keys, quat_curve):
                key.time = frame / self.fps
                key.value.w = quat.w
                key.value.x = quat.x
                key.value.y = quat.y
                key.value.z = quat.z

        n_kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
        n_kfd.translations.num_keys = len(trans_curve)
        n_kfd.translations.keys.update_size()
        for key, (frame, trans) in zip(n_kfd.translations.keys, trans_curve):
            key.time = frame / self.fps
            key.value.x, key.value.y, key.value.z = trans

        n_kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
        n_kfd.scales.num_keys = len(scale_curve)
        n_kfd.scales.keys.update_size()
        for key, (frame, scale) in zip(n_kfd.scales.keys, scale_curve):
            key.time = frame / self.fps
            key.value = scale

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
                NifLog.warn(f"Marker out of animated range ({f} not between [{f0}, {f1}])")

            key.time = f / self.fps
            key.value = marker.name.replace('/', '\r\n')

        return n_text_extra
