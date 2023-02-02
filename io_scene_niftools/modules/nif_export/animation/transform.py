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
from io_scene_niftools.utils import math, consts
from io_scene_niftools.utils.logging import NifError, NifLog

from io_scene_niftools.modules.nif_export import block_registry

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
        """Creates and returns a KF root block and exports controllers for objects and bones"""
        scene = bpy.context.scene
        game = scene.niftools_scene.game
        if game in ('MORROWIND', 'FREEDOM_FORCE'):
            kf_root = block_store.create_block("NiSequenceStreamHelper")
        elif game in (
                'SKYRIM', 'OBLIVION', 'FALLOUT_3', 'CIVILIZATION_IV', 'ZOO_TYCOON_2', 'FREEDOM_FORCE_VS_THE_3RD_REICH',
                'MEGAMI_TENSEI_IMAGINE'):
            kf_root = block_store.create_block("NiControllerSequence")
        else:
            raise NifError(f"Keyframe export for '{game}' is not supported.")

        anim_textextra = self.create_text_keys(kf_root)
        targetname = "Scene Root"

        # per-node animation
        if b_armature:
            b_action = self.get_active_action(b_armature)
            for b_bone in b_armature.data.bones:
                self.export_transforms(kf_root, b_armature, b_action, b_bone)
            if game in ('SKYRIM',):
                targetname = "NPC Root [Root]"
            else:
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

        self.export_text_keys(b_action, anim_textextra)

        kf_root.name = b_action.name
        kf_root.unknown_int_1 = 1
        kf_root.weight = 1.0
        kf_root.cycle_type = NifFormat.CycleType.CYCLE_CLAMP
        kf_root.frequency = 1.0

        if anim_textextra.num_text_keys > 0:
            kf_root.start_time = anim_textextra.text_keys[0].time
            kf_root.stop_time = anim_textextra.text_keys[anim_textextra.num_text_keys - 1].time
        else:
            kf_root.start_time = scene.frame_start / self.fps
            kf_root.stop_time = scene.frame_end / self.fps

        kf_root.target_name = targetname
        return kf_root


    def export_kfa_root(self, b_armature=None):
        """Creates and returns a KFA root block and exports controllers for objects and bones"""
        scene = bpy.context.scene
        game = scene.niftools_scene.game
        kfa_root = block_store.create_block("NiNode")

        anim_textextra = self.create_text_keys(kfa_root)
        targetname = "Scene Root"

        # mapping between bones name and id 
        bonename_dict = { "Bip01":0, "Bip01 Pelvis":1, "Bip01 Spine":2, "Bip01 Spine1":3, "Bip01 Spine2":4, "Bip01 Spine3":5, "Bip01 Neck":6, "Bip01 Neck1":7, "Bip01 Neck2":8, "Bip01 Neck3":9, "Bip01 Neck4":10, "Bip01 Head":11, "Bip01 Ponytail1":12, "Bip01 Ponytail11":13, "Bip01 Ponytail12":14, "Bip01 Ponytail13":15, "Bip01 Ponytail14":16, "Bip01 Ponytail2":17, "Bip01 Ponytail21":18, "Bip01 Ponytail22":19, "Bip01 Ponytail23":20, "Bip01 Ponytail24":21, "Bip01 L Clavicle":22, "Bip01 L UpperArm":23, "Bip01 L Forearm":34, "Bip01 L Hand":25, "Bip01 L Finger0":26, "Bip01 L Finger01":27, "Bip01 L Finger02":28, "Bip01 L Finger1":29, "Bip01 L Finger11":30, "Bip01 L Finger12":31, "Bip01 L Finger2":32, "Bip01 L Finger21":33, "Bip01 L Finger22":34, "Bip01 R Clavicle":35, "Bip01 R UpperArm":36, "Bip01 R Forearm":37, "Bip01 R Hand":38, "Bip01 R Finger0":39, "Bip01 R Finger01":40, "Bip01 R Finger02":41, "Bip01 R Finger1":42, "Bip01 R Finger11":43, "Bip01 R Finger12":44, "Bip01 R Finger2":45, "Bip01 R Finger21":46, "Bip01 R Finger22":47, "Bip01 L Thigh":48, "Bip01 L Calf":49, "Bip01 L HorseLink":50, "Bip01 L Foot":51, "Bip01 L Toe0":52, "Bip01 L Toe01":53, "Bip01 R Thigh":54, "Bip01 R Calf":55, "Bip01 R HorseLink":56, "Bip01 R Foot":57, "Bip01 R Toe0":58, "Bip01 R Toe01":59, "Bip01 Tail":60, "Bip01 Tail1":61, "Bip01 Tail2":62, "Bip01 Tail3":63, "Bip01 Tail4":64, "Bip01 L Shield":65, "Bip01 R Shield":66, "Bip01 L Held":67, "Bip01 R Held":68, "Bip01 L Belt":69, "Bip01 R Belt":70, "Bip01 L Back":71, "Bip01 R Back":72, "Bip01 Helm":73, "Bip01 Ext01":74, "Bip01 Ext02":75, "Bip01 Ext03":76, "Bip01 Ext04":77, "Bip01 Ext05":78, "Bip01 Ext06":79, "Bip01 Ext07":80, "Bip01 Ext08":81, "Bip01 Ext09":82, "Bip01 Ext10":83, "Bip01 Ext11":84, "Bip01 Ext12":85, "Bip01 Ext13":86, "Bip01 Ext14":87, "Bip01 Ext15":88, "Bip01 Ext16":89, "Bip01 Ext17":90, "Bip01 Ext18":91, "Bip01 Ext19":92, "Bip01 Ext20":93, "Bip01 L Finger3":94, "Bip01 L Finger31":95, "Bip01 L Finger32":96, "Bip01 L Finger4":97, "Bip01 L Finger41":98, "Bip01 L Finger42":99, "Bip01 R Finger3":100, "Bip01 R Finger31":101, "Bip01 R Finger32":102, "Bip01 R Finger4":103, "Bip01 R Finger41":104, "Bip01 R Finger42":105, "Bip01 L Toe02":106, "Bip01 L Toe03":107, "Bip01 L Toe1":108, "Bip01 L Toe11":109, "Bip01 L Toe12":110, "Bip01 L Toe2":111, "Bip01 L Toe21":112, "Bip01 L Toe22":113, "Bip01 R Toe02":114, "Bip01 R Toe03":115, "Bip01 R Toe1":116, "Bip01 R Toe11":117, "Bip01 R Toe12":118, "Bip01 R Toe2":119, "Bip01 R Toe21":120, "Bip01 R Toe22":121, "Bip01 L ForeTwist":122, "Bip01 L ForeTwist1":123, "Bip01 R ForeTwist":124, "Bip01 R ForeTwist1":125, "Bip01 EyeLids":126, "Bip01 L BicepTwist":127, "Bip01 R BicepTwist":128, "Bip01 L Pauldron":129, "Bip01 R Pauldron":130, "Bip01 Beard1":131, "Bip01 Beard2":132, "Bip01 FrontRobe1":133, "Bip01 FrontRobe2":134, "Bip01 BackRobe1":135, "Bip01 BackRobe2":136, "Bip01 C Cloak01":137, "Bip01 C Cloak02":138, "Bip01 C Cloak03":139, "Bip01 C Cloak04":140, "Bip01 C Cloak05":141, "Bip01 L Cloak01":142, "Bip01 L Cloak02":143, "Bip01 L Cloak03":144, "Bip01 L Cloak04":145, "Bip01 L Cloak05":146, "Bip01 R Cloak01":147, "Bip01 R Cloak02":148, "Bip01 R Cloak03":149, "Bip01 R Cloak04":150, "Bip01 R Cloak05":151, "Bip01 C CloakIKChain":152, "Bip01 L CloakIKChain":153, "Bip01 R CloakIKChain":154, "Bip01 L ThighTwist":155, "Bip01 R ThighTwist":156, "R Cloak Control01":157, "L Cloak Control01":158, "C Cloak Control01":159, "C Cloak Control02":160, "C Cloak Control03":161, "C Cloak Control04":162, "C Cloak Control05":163, "C Cloak Control06":164, "L Cloak Control02":165, "L Cloak Control03":166, "L Cloak Control04":167, "L Cloak Control05":168, "L Cloak Control06":169, "R Cloak Control02":170, "R Cloak Control03":171, "R Cloak Control04":172, "R Cloak Control05":173, "R Cloak Control06":174 }

        # per-node animation
        if b_armature:
            b_action = self.get_active_action(b_armature)
            # generate array of NiStringExtraData to indice the bones list used
            extraDataList = []
            data_nb=0
            for b_bone in b_armature.data.bones:
                # get bone name
                bone_name = block_registry.ExportBlockRegistry.get_bone_name_for_nif(b_bone.name)
                # retrieve the bone id from the bone name
                bone_id = bonename_dict.get(bone_name)

                if bone_id != None:
                    if (b_bone and b_bone.name in b_action.groups) or (not b_bone) :
                        # NiStringExtraData corresponding to bone  
                        extraData = block_store.create_block("NiStringExtraData")
                        extraData.name="NiStringED"+'%03d'%data_nb
                        extraData.string_data = str(bone_id)
                        extraDataList.append(extraData)
                        # Create and add the NiKeyframeController corresponding to the bone in the chained list
                        self.export_transforms(kfa_root, b_armature, b_action, b_bone)                      
                    data_nb = data_nb +1
                                   
            kfa_root.set_extra_datas(extraDataList)
                
            # quick hack to set correct target name
            if "Bip01" in b_armature.data.bones:
                targetname = "Bip01"
            elif "Bip02" in b_armature.data.bones:
                targetname = "Bip02"

        # per-object animation
        else:
            for b_obj in bpy.data.objects:
                b_action = self.get_active_action(b_obj)
                self.export_transforms(kfa_root, b_obj, b_action)

        #self.export_text_keys(b_action, anim_textextra)

        kfa_root.name = b_action.name
        kfa_root.unknown_int_1 = 1
        kfa_root.weight = 1.0
        kfa_root.cycle_type = NifFormat.CycleType.CYCLE_CLAMP
        kfa_root.frequency = 1.0

        if anim_textextra.num_text_keys > 0:
            kfa_root.start_time = anim_textextra.text_keys[0].time
            kfa_root.stop_time = anim_textextra.text_keys[anim_textextra.num_text_keys - 1].time
        else:
            kfa_root.start_time = scene.frame_start / self.fps
            kfa_root.stop_time = scene.frame_end / self.fps

        kfa_root.target_name = targetname
        return kfa_root


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
            # get bind matrix for bone
            bind_matrix = math.get_object_bind(bone)
            exp_fcurves = b_action.groups[bone.name].channels
            # just for more detailed error reporting later on
            bonestr = f" in bone {bone.name}"
            target_name = block_store.get_full_name(bone)
            priority = bone.niftools.priority

        # object level animation - no coordinate corrections
        elif not bone:

            # raise error on any objects parented to bones
            if b_obj.parent and b_obj.parent_type == "BONE":
                raise NifError(
                    f"{b_obj.name} is parented to a bone AND has animations. The nif format does not support this!")

            target_name = block_store.get_full_name(b_obj)
            priority = 0

            # we have either a root object (Scene Root), in which case we take the coordinates without modification
            # or a generic object parented to an empty = node
            # objects may have an offset from their parent that is not apparent in the user input (ie. UI values and keyframes)
            # we want to export matrix_local, and the keyframes are in matrix_basis, so do:
            # matrix_local = matrix_parent_inverse * matrix_basis
            bind_matrix = b_obj.matrix_parent_inverse
            exp_fcurves = [fcu for fcu in b_action.fcurves if
                           fcu.data_path in ("rotation_quaternion", "rotation_euler", "location", "scale")]

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
                raise NifError(
                    f"Incomplete key set {bonestr} for action {b_action.name}."
                    f"Ensure that if a bone is keyframed for a property, all channels are keyframed.")

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
            # set the default transforms of the interpolator as the bone's bind pose
            n_kfi.translation.x, n_kfi.translation.y, n_kfi.translation.z = bind_trans
            n_kfi.rotation.w, n_kfi.rotation.x, n_kfi.rotation.y, n_kfi.rotation.z = bind_rot.to_quaternion()
            n_kfi.scale = bind_scale

            if max(len(c) for c in (quat_curve, euler_curve, trans_curve, scale_curve)) > 0:
                # number of frames is > 0, so add transform data
                n_kfd = block_store.create_block("NiTransformData", exp_fcurves)
                n_kfi.data = n_kfd
            else:
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
        
            
    def create_text_keys(self, kf_root):
        """Create the text keys before filling in the data so that the extra data hierarchy is correct"""
        # add a NiTextKeyExtraData block
        n_text_extra = block_store.create_block("NiTextKeyExtraData", None)
        if isinstance(kf_root, NifFormat.NiControllerSequence):
            kf_root.text_keys = n_text_extra
        elif isinstance(kf_root, NifFormat.NiSequenceStreamHelper):
            kf_root.add_extra_data(n_text_extra)
        return n_text_extra

    def export_text_keys(self, b_action, n_text_extra):
        """Process b_action's pose markers and populate the extra string data block."""
        NifLog.info("Exporting animation groups")
        self.add_dummy_markers(b_action)
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

    def add_dummy_controllers(self):
        NifLog.info("Adding controllers and interpolators for skeleton")
        # note: block_store.block_to_obj changes during iteration, so need list copy
        for n_block in list(block_store.block_to_obj.keys()):
            if isinstance(n_block, NifFormat.NiNode) and n_block.name.decode() == "Bip01":
                for n_bone in n_block.tree(block_type=NifFormat.NiNode):
                    n_kfc, n_kfi = self.transform_anim.create_controller(n_bone, n_bone.name.decode())
                    # todo [anim] use self.nif_export.animationhelper.set_flags_and_timing
                    n_kfc.flags = 12
                    n_kfc.frequency = 1.0
                    n_kfc.phase = 0.0
                    n_kfc.start_time = consts.FLOAT_MAX
                    n_kfc.stop_time = consts.FLOAT_MIN
