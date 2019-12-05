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

from io_scene_nif.modules.animation.transform_import import TransformAnimation
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class Animation:

    def __init__(self):
        self.object_animation = ObjectAnimation(self)
        self.material_animation = MaterialAnimation(self)
        self.transform = TransformAnimation(self)
        # set a dummy here, update via set_frames_per_second
        self.fps = 30

    @staticmethod
    def get_b_interp_from_n_interp(n_ipol):
        if n_ipol in (NifFormat.KeyType.LINEAR_KEY, NifFormat.KeyType.XYZ_ROTATION_KEY):
            return "LINEAR"
        elif n_ipol == NifFormat.KeyType.QUADRATIC_KEY:
            return "BEZIER"
        elif n_ipol == 0:
            # guessing, not documented in nif.xml
            return "CONSTANT"
        # NifLog.warn("Unsupported interpolation mode ({0}) in nif, using quadratic/bezier.".format(n_ipol))
        return "BEZIER"

    @staticmethod
    def create_action(b_obj, action_name):
        """ Create or retrieve action and set it as active on the object. """
        # could probably skip this test and create always
        if not b_obj.animation_data:
            b_obj.animation_data_create()
        if action_name in bpy.data.actions:
            b_action = bpy.data.actions[action_name]
        else:
            b_action = bpy.data.actions.new(action_name)
        # set as active action on object
        b_obj.animation_data.action = b_action
        return b_action

    def create_fcurves(self, action, dtype, drange, flags=None, bonename=None):
        """ Create fcurves in action for desired conditions. """
        # armature pose bone animation
        if bonename:
            fcurves = [
                action.fcurves.new(data_path='pose.bones["' + bonename + '"].' + dtype, index=i, action_group=bonename)
                for i in drange]
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
        frame = round(t * self.fps)
        for fcurve, k in zip(fcurves, key):
            fcurve.keyframe_points.insert(frame, k).interpolation = interp

    # import animation groups
    def import_text_keys(self, n_block):
        """Stores the text keys that define animation start and end in a text
        buffer, so that they can be re-exported. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""

        if isinstance(n_block, NifFormat.NiControllerSequence):
            txk = n_block.text_keys
        else:
            txk = n_block.find(block_type=NifFormat.NiTextKeyExtraData)
        if txk:
            # get animation text buffer, and clear it if it already exists
            name = "Anim"
            if name in bpy.data.texts:
                animtxt = bpy.data.texts[name]
                animtxt.clear()
            else:
                animtxt = bpy.data.texts.new(name)

            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = round(key.time * self.fps)
                animtxt.write('%i/%s\n' % (frame, newkey))

            # set start and end frames
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = frame

    def set_frames_per_second(self, roots):
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
                    # skip bsplines without basis data (eg bowidle.kf in
                    # Oblivion)
                    continue
                key_times.extend(
                    point * (kfi.stop_time - kfi.start_time)
                    / (kfi.basis_data.num_control_points - 2)
                    for point in range(kfi.basis_data.num_control_points - 2))
            for uv_data in root.tree(block_type=NifFormat.NiUVData):
                for uv_group in uv_data.uv_groups:
                    key_times.extend(key.time for key in uv_group.keys)
        fps = self.fps
        # not animated, return a reasonable default
        if not key_times:
            return
        # calculate FPS
        key_times = sorted(set(key_times))
        lowest_diff = sum(abs(int(time * fps + 0.5) - (time * fps))
                          for time in key_times)
        # for test_fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 24, 25, 30, 35]:
            diff = sum(abs(int(time * test_fps + 0.5) - (time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        NifLog.info("Animation estimated at %i frames per second." % fps)
        self.fps = fps
        bpy.context.scene.render.fps = fps
        bpy.context.scene.frame_set(0)


class ObjectAnimation:

    def __init__(self, parent):
        self.animationhelper = parent

    def import_object_vis_controller(self, n_node, b_obj):
        """Import vis controller for blender object."""

        n_vis_ctrl = nif_utils.find_controller(n_node, NifFormat.NiVisController)
        if not (n_vis_ctrl and n_vis_ctrl.data):
            return
        NifLog.info("Importing vis controller")

        b_obj_action = self.animationhelper.create_action(b_obj, b_obj.name + "-Anim")

        fcurves = self.animationhelper.create_fcurves(b_obj_action, "hide", (0,), n_vis_ctrl.flags)
        for key in n_vis_ctrl.data.keys:
            self.animationhelper.add_key(fcurves, key.time, (key.value,), "CONSTANT")

    def import_morph_controller(self, n_node, b_obj, v_map):
        """Import NiGeomMorpherController as shape keys for blender object."""

        n_morphCtrl = nif_utils.find_controller(n_node, NifFormat.NiGeomMorpherController)
        if n_morphCtrl:
            b_mesh = b_obj.data
            morphData = n_morphCtrl.data
            if morphData.num_morphs:
                b_obj_action = self.animationhelper.create_action(b_obj, b_obj.name + "-Morphs")
                fps = bpy.context.scene.render.fps
                # get name for base key
                keyname = morphData.morphs[0].frame_name.decode()
                if not keyname:
                    keyname = 'Base'

                # insert base key at frame 1, using relative keys
                sk_basis = b_obj.shape_key_add(keyname)

                # get base vectors and import all morphs
                baseverts = morphData.morphs[0].vectors

                for idxMorph in range(1, morphData.num_morphs):
                    # get name for key
                    keyname = morphData.morphs[idxMorph].frame_name.decode()
                    if not keyname:
                        keyname = 'Key %i' % idxMorph
                    NifLog.info("Inserting key '{0}'".format(keyname))
                    # get vectors
                    morph_verts = morphData.morphs[idxMorph].vectors
                    self.morph_mesh(b_mesh, baseverts, morph_verts, v_map)
                    shape_key = b_obj.shape_key_add(keyname, from_mix=False)

                    # first find the keys
                    # older versions store keys in the morphData
                    morph_data = morphData.morphs[idxMorph]
                    # newer versions store keys in the controller
                    if not morph_data.keys:
                        try:
                            if n_morphCtrl.interpolators:
                                morph_data = n_morphCtrl.interpolators[idxMorph].data.data
                            elif n_morphCtrl.interpolator_weights:
                                morph_data = n_morphCtrl.interpolator_weights[idxMorph].interpolator.data.data
                        except KeyError:
                            NifLog.info("Unsupported interpolator '{0}'".format(type(n_morphCtrl.interpolator_weights[idxMorph].interpolator)))
                            continue
                    # TODO [animation] can we create the fcurve manually - does not seem to work here?
                    # as b_obj.data.shape_keys.animation_data is read-only

                    # FYI shape_key = b_mesh.shape_keys.key_blocks[-1]
                    # set keyframes
                    for key in morph_data.keys:
                        shape_key.value = key.value
                        shape_key.keyframe_insert(data_path="value", frame=round(key.time * fps))

                    # fcurves = (b_obj.data.shape_keys.animation_data.action.fcurves[-1], )
                    # # set extrapolation to fcurves
                    # self.nif_import.animation_helper.set_extrapolation(n_morphCtrl.flags, fcurves)
                    # # get the interpolation mode
                    # interp = self.nif_import.animation_helper.get_b_interp_from_n_interp( morph_data.interpolation)
                    # TODO [animation] set interpolation once low level access works


class MaterialAnimation:

    def __init__(self, parent):
        self.animationhelper = parent

    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not NifOp.props.animation:
            return
        n_material = nif_utils.find_property(n_geom, NifFormat.NiMaterialProperty)
        if n_material:
            self.import_material_alpha_controller(b_material, n_material)
            for b_channel, n_target_color in (("niftools.ambient_color", NifFormat.TargetColor.TC_AMBIENT),
                                              ("diffuse_color", NifFormat.TargetColor.TC_DIFFUSE),
                                              ("specular_color", NifFormat.TargetColor.TC_SPECULAR)):
                self.import_material_color_controller(b_material, n_material, b_channel, n_target_color)

        self.import_material_uv_controller(b_material, n_geom)

    def import_material_alpha_controller(self, b_material, n_material):
        # find alpha controller
        n_alphactrl = nif_utils.find_controller(n_material, NifFormat.NiAlphaController)
        if not (n_alphactrl and n_alphactrl.data):
            return
        NifLog.info("Importing alpha controller")

        b_mat_action = self.animationhelper.create_action(b_material, "MaterialAction")
        fcurves = self.animationhelper.create_fcurves(b_mat_action, "alpha", (0,), n_alphactrl.flags)
        interp = self.animationhelper.get_b_interp_from_n_interp(n_alphactrl.data.data.interpolation)
        for key in n_alphactrl.data.data.keys:
            self.animationhelper.add_key(fcurves, key.time, (key.value,), interp)

    def import_material_color_controller(self, b_material, n_material, b_channel, n_target_color):
        # find material color controller with matching target color
        for ctrl in n_material.get_controllers():
            if isinstance(ctrl, NifFormat.NiMaterialColorController):
                if ctrl.get_target_color() == n_target_color:
                    n_matcolor_ctrl = ctrl
                    break
        else:
            return
        NifLog.info("Importing material color controller for target color {0} into blender channel {0}".format(n_target_color, b_channel))

        # import data as curves
        b_mat_action = self.animationhelper.create_action(b_material, "MaterialAction")

        fcurves = self.animationhelper.create_fcurves(b_mat_action, b_channel, range(3), n_matcolor_ctrl.flags)
        interp = self.animationhelper.get_b_interp_from_n_interp(n_matcolor_ctrl.data.data.interpolation)
        for key in n_matcolor_ctrl.data.data.keys:
            self.animationhelper.add_key(fcurves, key.time, key.value.as_list(), interp)

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom, NifFormat.NiUVController)
        if not (n_ctrl and n_ctrl.data):
            return
        NifLog.info("Importing UV controller")

        b_mat_action = self.animationhelper.create_action(b_material, "MaterialAction")

        dtypes = ("offset", 0), ("offset", 1), ("scale", 0), ("scale", 1)
        for n_uvgroup, (data_path, array_ind) in zip(n_ctrl.data.uv_groups, dtypes):
            if n_uvgroup.keys:
                interp = self.animationhelper.get_b_interp_from_n_interp(n_uvgroup.interpolation)
                # in blender, UV offset is stored per n_texture slot
                # so we have to repeat the import for each used tex slot
                for i, texture_slot in enumerate(b_material.texture_slots):
                    if texture_slot:
                        fcurves = self.animationhelper.create_fcurves(b_mat_action, "texture_slots[" + str(i) + "]." + data_path, (array_ind,), n_ctrl.flags)
                        for key in n_uvgroup.keys:
                            if "offset" in data_path:
                                self.animationhelper.add_key(fcurves, key.time, (-key.value,), interp)
                            else:
                                self.animationhelper.add_key(fcurves, key.time, (key.value,), interp)

