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
import mathutils

from bisect import bisect_left

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


# TODO [animation][util] interpolate() should perhaps be moved to utils?
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


class Animation:

    def __init__(self, parent):
        self.nif_import = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.armature_animation = ArmatureAnimation(parent)
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
        self.nif_import = parent

    def import_object_vis_controller(self, n_node, b_obj):
        """Import vis controller for blender object."""

        n_vis_ctrl = nif_utils.find_controller(n_node, NifFormat.NiVisController)
        if not (n_vis_ctrl and n_vis_ctrl.data):
            return
        NifLog.info("Importing vis controller")

        b_obj_action = self.nif_import.animationhelper.create_action(b_obj, b_obj.name + "-Anim")

        fcurves = self.nif_import.animationhelper.create_fcurves(b_obj_action, "hide", (0,), n_vis_ctrl.flags)
        for key in n_vis_ctrl.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value,), "CONSTANT")

    def morph_mesh(self, b_mesh, baseverts, morphverts, v_map):
        """Transform a mesh to be in the shape given by morphverts."""
        # for each vertex calculate the key position from base
        # pos + delta offset
        # length check disabled
        # as sometimes, oddly, the morph has more vertices...
        # assert(len(baseverts) == len(morphverts) == len(v_map))
        for bv, mv, b_v_index in zip(baseverts, morphverts, v_map):
            # pyffi vector3
            v = bv + mv
            # if applytransform:
            # v *= transform
            b_mesh.vertices[b_v_index].co = v.as_tuple()

    def import_morph_controller(self, n_node, b_obj, v_map):
        """Import NiGeomMorpherController as shape keys for blender object."""

        n_morphCtrl = nif_utils.find_controller(n_node, NifFormat.NiGeomMorpherController)
        if n_morphCtrl:
            b_mesh = b_obj.data
            morphData = n_morphCtrl.data
            if morphData.num_morphs:
                b_obj_action = self.nif_import.animationhelper.create_action(b_obj, b_obj.name + "-Morphs")
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
                    # self.nif_import.animationhelper.set_extrapolation(n_morphCtrl.flags, fcurves)
                    # # get the interpolation mode
                    # interp = self.nif_import.animationhelper.get_b_interp_from_n_interp( morph_data.interpolation)
                    # TODO [animation] set interpolation once low level access works

    def import_egm_morphs(self, egm_data, b_obj, v_map, n_verts):
        """Import all EGM morphs as shape keys for blender object."""
        # TODO [morph][egm] if there is an egm, the assumption is that there is only one mesh in the nif
        b_mesh = b_obj.data
        sym_morphs = [list(morph.get_relative_vertices()) for morph in egm_data.sym_morphs]
        asym_morphs = [list(morph.get_relative_vertices()) for morph in egm_data.asym_morphs]

        # insert base key at frame 1, using absolute keys
        sk_basis = b_obj.shape_key_add("Basis")
        b_mesh.shape_keys.use_relative = False

        morphs = ([(morph, "EGM SYM %i" % i) for i, morph in enumerate(sym_morphs)] +
                  [(morph, "EGM ASYM %i" % i) for i, morph in enumerate(asym_morphs)])

        for morph_verts, key_name in morphs:
            # convert tuples into vector here so we can simply add in morph_mesh()
            morphvert_out = []
            for u in morph_verts:
                v = NifFormat.Vector3()
                v.x, v.y, v.z = u
                morphvert_out.append(v)
            self.morph_mesh(b_mesh, n_verts, morphvert_out, v_map)
            # TODO [animation] unused variable is it required
            shape_key = b_obj.shape_key_add(key_name, from_mix=False)


class MaterialAnimation:

    def __init__(self, parent):
        self.nif_import = parent

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

        b_mat_action = self.nif_import.animationhelper.create_action(b_material, "MaterialAction")
        fcurves = self.nif_import.animationhelper.create_fcurves(b_mat_action, "alpha", (0,), n_alphactrl.flags)
        interp = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_alphactrl.data.data.interpolation)
        for key in n_alphactrl.data.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value,), interp)

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
        b_mat_action = self.nif_import.animationhelper.create_action(b_material, "MaterialAction")

        fcurves = self.nif_import.animationhelper.create_fcurves(b_mat_action, b_channel, range(3), n_matcolor_ctrl.flags)
        interp = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_matcolor_ctrl.data.data.interpolation)
        for key in n_matcolor_ctrl.data.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, key.value.as_list(), interp)

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom, NifFormat.NiUVController)
        if not (n_ctrl and n_ctrl.data):
            return
        NifLog.info("Importing UV controller")

        b_mat_action = self.nif_import.animationhelper.create_action(b_material, "MaterialAction")

        dtypes = ("offset", 0), ("offset", 1), ("scale", 0), ("scale", 1)
        for n_uvgroup, (data_path, array_ind) in zip(n_ctrl.data.uv_groups, dtypes):
            if n_uvgroup.keys:
                interp = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_uvgroup.interpolation)
                # in blender, UV offset is stored per texture slot
                # so we have to repeat the import for each used tex slot
                for i, texture_slot in enumerate(b_material.texture_slots):
                    if texture_slot:
                        fcurves = self.nif_import.animationhelper.create_fcurves(b_mat_action, "texture_slots[" + str(i) + "]." + data_path, (array_ind,), n_ctrl.flags)
                        for key in n_uvgroup.keys:
                            if "offset" in data_path:
                                self.nif_import.animationhelper.add_key(fcurves, key.time, (-key.value,), interp)
                            else:
                                self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value,), interp)


class ArmatureAnimation:

    def __init__(self, parent):
        self.nif_import = parent

    def import_kf_standalone(self, kf_root, b_armature_obj, bind_data):
        """Import a kf animation. Needs a suitable armature in blender scene."""

        NifLog.info("Importing KF tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise nif_utils.NifError("non-Oblivion .kf import not supported")

        # import text keys
        self.nif_import.animationhelper.import_text_keys(kf_root)

        b_action = self.nif_import.animationhelper.create_action(b_armature_obj, kf_root.name.decode())
        # go over all controlled blocks (NiKeyframeController)
        for controlledblock in kf_root.controlled_blocks:
            # get bone name
            # ZT2 - old way is not supported by pyffi's get_node_name()
            n_name = controlledblock.target_name
            # fallout (node_name) & Loki (StringPalette)
            if not n_name:
                n_name = controlledblock.get_node_name()
            bone_name = armature.get_bone_name_for_blender(n_name)
            if bone_name not in b_armature_obj.data.bones:
                continue
            b_bone = b_armature_obj.data.bones[bone_name]
            # import bone priority
            b_bone.niftools.bonepriority = controlledblock.priority
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
            extend = self.nif_import.animationhelper.get_extend_from_cycle_type(kf_root.cycle_type)
            self.nif_import.animationhelper.set_extrapolation(extend, b_action.fcurves)

    # TODO [animation] Is scale param required or can be removed, not used
    def import_keyframe_controller(self, n_kfc, b_obj, bone_name=None, n_bone_bind_scale=None, n_bone_bind_rot_inv=None, n_bone_bind_trans=None):
        b_action = b_obj.animation_data.action

        if bone_name:
            b_obj = b_obj.pose.bones[bone_name]

        translations = []
        scales = []
        rotations = []
        eulers = []
        n_kfd = None

        # B-spline curve import
        if isinstance(n_kfc, NifFormat.NiBSplineInterpolator):
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

        # ZT2 - get extrapolation for every kfc
        if isinstance(n_kfc, NifFormat.NiKeyframeController):
            flags = n_kfc.flags
        # fallout, Loki - we set extrapolation according to the root NiControllerSequence.cycle_type
        else:
            flags = None
        if isinstance(n_kfd, NifFormat.NiKeyframeData):
            interp_rot = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_kfd.rotation_type)
            interp_loc = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_kfd.translations.interpolation)
            interp_scale = self.nif_import.animationhelper.get_b_interp_from_n_interp(n_kfd.scales.interpolation)
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

        if eulers:
            NifLog.debug('Rotation keys...(euler)')
            fcurves = self.nif_import.animationhelper.create_fcurves(b_action, "rotation_euler", range(3), flags, bone_name)
            for t, val in eulers:
                key = mathutils.Euler(val)
                if bone_name:
                    key = armature.import_keymat(n_bone_bind_rot_inv, key.to_matrix().to_4x4()).to_euler()
                self.nif_import.animationhelper.add_key(fcurves, t, key, interp_rot)
        elif rotations:
            NifLog.debug('Rotation keys...(quaternions)')
            fcurves = self.nif_import.animationhelper.create_fcurves(b_action, "rotation_quaternion", range(4), flags, bone_name)
            for t, val in rotations:
                key = mathutils.Quaternion([val.w, val.x, val.y, val.z])
                if bone_name:
                    key = armature.import_keymat(n_bone_bind_rot_inv, key.to_matrix().to_4x4()).to_quaternion()
                self.nif_import.animationhelper.add_key(fcurves, t, key, interp_rot)
        if translations:
            NifLog.debug('Translation keys...')
            fcurves = self.nif_import.animationhelper.create_fcurves(b_action, "location", range(3), flags, bone_name)
            for t, val in translations:
                key = mathutils.Vector([val.x, val.y, val.z])
                if bone_name:
                    key = armature.import_keymat(n_bone_bind_rot_inv,
                                                 mathutils.Matrix.Translation(key - n_bone_bind_trans)).to_translation()
                self.nif_import.animationhelper.add_key(fcurves, t, key, interp_loc)
        if scales:
            NifLog.debug('Scale keys...')
            fcurves = self.nif_import.animationhelper.create_fcurves(b_action, "scale", range(3), flags, bone_name)
            for t, val in scales:
                key = (val, val, val)
                self.nif_import.animationhelper.add_key(fcurves, t, key, interp_scale)

    def import_object_animation(self, n_block, b_obj):
        """Loads an animation attached to a nif block (non-skeletal). Becomes the object level animation of the blender object."""
        NifLog.debug('Importing animation for object %s'.format(b_obj.name))

        n_kfc = nif_utils.find_controller(n_block, NifFormat.NiKeyframeController)
        if n_kfc:
            self.nif_import.animationhelper.create_action(b_obj, b_obj.name + "-Anim")
            self.import_keyframe_controller(n_kfc, b_obj)

    def import_bone_animation(self, n_block, b_armature_obj, bone_name):
        """Loads an animation attached to a nif block (skeletal). Becomes the pose bone level animation of the blender object."""
        NifLog.debug('Importing animation for bone %s'.format(bone_name))

        n_kfc = nif_utils.find_controller(n_block, NifFormat.NiKeyframeController)
        if n_kfc:
            bone_bm = nif_utils.import_matrix(n_block)  # base pose
            n_bone_bind_scale, n_bone_bind_rot, n_bone_bind_trans = nif_utils.decompose_srt(bone_bm)
            niBone_bind_rot_inv = n_bone_bind_rot.to_4x4().inverted()
            self.import_keyframe_controller(n_kfc, b_armature_obj, bone_name, n_bone_bind_scale, niBone_bind_rot_inv, n_bone_bind_trans)
