"""This script contains classes to help import animations."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp


def set_flags_and_timing(kfc, exp_fcurves, start_frame=None, stop_frame=None):
    # fill in the non-trivial values
    kfc.flags = 8  # active
    kfc.flags |= get_flags_from_fcurves(exp_fcurves)
    kfc.frequency = 1.0
    kfc.phase = 0.0
    if not start_frame and not stop_frame:
        start_frame, stop_frame = exp_fcurves[0].range()
    kfc.start_time = start_frame / Animation.fps
    kfc.stop_time = stop_frame / Animation.fps


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


class Animation:

    fps = 30

    def __init__(self, parent):
        self.nif_export = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.texture_animation = TextureAnimation(parent)
        self.fps = bpy.context.scene.render.fps

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

    @staticmethod
    def iter_frame_key(fcurves, mathutils_class):
        """
        Iterator that yields a tuple of frame and key for all fcurves.
        Assumes the fcurves are sampled at the same time and all have the same amount of keys
        Return the key in the desired mathutils_class
        """
        for point in zip(*[fcu.keyframe_points for fcu in fcurves]):
            frame = point[0].co[0]
            key = [k.co[1] for k in point]
            yield frame, mathutils_class(key)

    def export_keyframes(self, parent_block, b_obj=None, bone=None):
        """
        If called on b_obj=None and bone=None it should save an empty controller.
        If called on an b_obj = type(armature), it expects a bone too.
        If called on an object, with bone=None, it exports object level animation.
        """

        # sometimes we need to export an empty keyframe... 
        scale_curve = []
        quat_curve = []
        euler_curve = []
        trans_curve = []

        exp_fcurves = []

        # just for more detailed error reporting later on
        bonestr = ""

        # we have either skeletal or object animation
        if b_obj and b_obj.animation_data and b_obj.animation_data.action:
            action = b_obj.animation_data.action

            # skeletal animation - with bone correction & coordinate corrections
            if bone and bone.name in action.groups:
                # get bind matrix for bone or object
                bind_matrix = self.nif_export.objecthelper.get_object_bind(bone)
                exp_fcurves = action.groups[bone.name].channels
                # just for more detailed error reporting later on
                bonestr = " in bone " + bone.name
            # object level animation - no coordinate corrections
            elif not bone:
                # raise error on any objects parented to bones
                if b_obj.parent and b_obj.parent_type == "BONE":
                    raise nif_utils.NifError(
                       "{} is parented to a bone AND has animations."
                       "The nif format does not support this!".format(b_obj.name))

                # we have either a root object (Scene Root), in which case we take the coordinates without modification
                # or a generic object parented to an empty = node
                # objects may have an offset from their parent that is not apparent in the user input (ie. UI values and keyframes)
                # we want to export matrix_local, and the keyframes are in matrix_basis, so do:
                # matrix_local = matrix_parent_inverse * matrix_basis
                bind_matrix = b_obj.matrix_parent_inverse
                exp_fcurves = [fcu for fcu in action.fcurves if
                               fcu.data_path in ("rotation_quaternion", "rotation_euler", "location", "scale")]
            # decompose the bind matrix
            if exp_fcurves:
                bind_scale, bind_rot, bind_trans = nif_utils.decompose_srt(bind_matrix)
                bind_rot = bind_rot.to_4x4()
            start_frame, stop_frame = action.frame_range

        # we are supposed to export an empty controller
        else:
            # only set frame range
            start_frame = bpy.context.scene.frame_start
            stop_frame = bpy.context.scene.frame_end

        if NifOp.props.animation == 'GEOM_NIF' and self.nif_export.version < 0x0A020000:
            # keyframe controllers are not present in geometry only files
            # for more recent versions, the controller and interpolators are
            # present, only the data is not present (see further on)
            return

        # add a KeyframeController block, and refer to this block in the
        # parent's time controller
        if self.nif_export.version < 0x0A020000:
            kfc = self.nif_export.objecthelper.create_block("NiKeyframeController", exp_fcurves)
        else:
            kfc = self.nif_export.objecthelper.create_block("NiTransformController", exp_fcurves)
            kfi = self.nif_export.objecthelper.create_block("NiTransformInterpolator", exp_fcurves)
            # link interpolator from the controller
            kfc.interpolator = kfi
            # set interpolator default data
            kfi.scale, kfi.rotation, kfi.translation = \
                parent_block.get_transform().get_scale_quat_translation()

        # if parent is a node, attach controller to that node
        if isinstance(parent_block, NifFormat.NiNode):
            parent_block.add_controller(kfc)
        # else ControllerSequence, so create a link
        elif isinstance(parent_block, NifFormat.NiControllerSequence):
            controlled_block = parent_block.add_controlled_block()
            if self.nif_export.version < 0x0A020000:
                # older versions need the actual controller blocks
                controlled_block.target_name = armature.get_bone_name_for_nif(bone.name)
                controlled_block.controller = kfc
                # erase reference to target node
                kfc.target = None
            else:
                # newer versions need the interpolator blocks
                controlled_block.interpolator = kfi
        else:
            raise nif_utils.NifError("Unsupported KeyframeController parent!")

        # fill in the non-trivial values
        set_flags_and_timing(kfc, exp_fcurves, start_frame, stop_frame)

        if NifOp.props.animation == 'GEOM_NIF':
            # keyframe data is not present in geometry files
            return

        # get the desired fcurves for each data type from exp_fcurves
        quaternions = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("quaternion")]
        translations = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("location")]
        eulers = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("euler")]
        scales = [fcu for fcu in exp_fcurves if fcu.data_path.endswith("scale")]

        # go over all fcurves collected above and transform and store all keys
        if scales:
            # just use the first scale curve and assume even scale over all curves
            for frame, scale in self.iter_frame_key(scales, mathutils.Vector):
                scale_curve.append((frame, scale[0]))

        if quaternions:
            if len(quaternions) != 4:
                raise nif_utils.NifError("Incomplete ROT key set {} for action {}".format(bonestr, action.name))
            else:
                for frame, quat in self.iter_frame_key(quaternions, mathutils.Quaternion):
                    quat = armature.export_keymat(bind_rot, quat.to_matrix().to_4x4(), bone).to_quaternion()
                    quat_curve.append((frame, quat))

        if eulers:
            if len(eulers) != 3:
                raise nif_utils.NifError("Incomplete Euler key set {} for action {}".format(bonestr, action.name))
            else:
                for frame, euler in self.iter_frame_key(eulers, mathutils.Euler):
                    keymat = armature.export_keymat(bind_rot, euler.to_matrix().to_4x4(), bone)
                    euler = keymat.to_euler("XYZ", euler)
                    euler_curve.append((frame, euler))

        if translations:
            if len(translations) != 3:
                raise nif_utils.NifError("Incomplete LOC key set{} for action {}".format(bonestr, action.name))
            else:
                for frame, trans in self.iter_frame_key(translations, mathutils.Vector):
                    keymat = armature.export_keymat(bind_rot, mathutils.Matrix.Translation(trans), bone)
                    trans = keymat.to_translation() + bind_trans
                    trans_curve.append((frame, trans))

        # finally we can export the data calculated above
        if (max(len(quat_curve), len(euler_curve), len(trans_curve), len(scale_curve)) <= 1
                and self.nif_export.version >= 0x0A020000):
            # only add data if number of keys is > 1
            # (see importer comments with import_kf_root: a single frame
            # keyframe denotes an interpolator without further data)
            # insufficient keys, so set the data and we're done!
            if trans_curve:
                trans = trans_curve[0][1]
                kfi.translation.x = trans[0]
                kfi.translation.y = trans[1]
                kfi.translation.z = trans[2]
            if quat_curve:
                quat = quat_curve[0][1]
                kfi.rotation.x = quat.x
                kfi.rotation.y = quat.y
                kfi.rotation.z = quat.z
                kfi.rotation.w = quat.w
            elif euler_curve:
                quat = euler_curve[0][1].to_quaternion()
                kfi.rotation.x = quat.x
                kfi.rotation.y = quat.y
                kfi.rotation.z = quat.z
                kfi.rotation.w = quat.w
            # ignore scale for now...
            kfi.scale = 1.0
            # done!
            return

        # add the keyframe data
        if self.nif_export.version < 0x0A020000:
            kfd = self.nif_export.objecthelper.create_block("NiKeyframeData", exp_fcurves)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.nif_export.objecthelper.create_block("NiTransformData", exp_fcurves)
            kfi.data = kfd

        # TODO [animation] support other interpolation modes, get interpolation from blender?
        #                  probably requires additional data like tangents and stuff

        # save all nif keys
        if euler_curve:
            kfd.rotation_type = NifFormat.KeyType.XYZ_ROTATION_KEY
            kfd.num_rotation_keys = 1  # *NOT* len(frames) this crashes the engine!
            for i, coord in enumerate(kfd.xyz_rotations):
                coord.num_keys = len(euler_curve)
                coord.interpolation = NifFormat.KeyType.LINEAR_KEY
                coord.keys.update_size()
                for key, (frame, euler) in zip(coord.keys, euler_curve):
                    key.time = frame / self.fps
                    key.value = euler[i]
        elif quat_curve:
            kfd.rotation_type = NifFormat.KeyType.LINEAR_KEY
            kfd.num_rotation_keys = len(quat_curve)
            kfd.quaternion_keys.update_size()
            for key, (frame, quat) in zip(kfd.quaternion_keys, quat_curve):
                key.time = frame / self.fps
                key.value.w = quat.w
                key.value.x = quat.x
                key.value.y = quat.y
                key.value.z = quat.z

        kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.translations.num_keys = len(trans_curve)
        kfd.translations.keys.update_size()
        for key, (frame, trans) in zip(kfd.translations.keys, trans_curve):
            key.time = frame / self.fps
            key.value.x, key.value.y, key.value.z = trans

        kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.scales.num_keys = len(scale_curve)
        kfd.scales.keys.update_size()
        for key, (frame, scale) in zip(kfd.scales.keys, scale_curve):
            key.time = frame / self.fps
            key.value = scale

    def export_text_keys(self, block_parent, ):
        """Parse the animation groups buffer and write an extra string
        data block, and attach it to an existing block (typically, the root
        of the nif tree)."""
        if NifOp.props.animation == 'GEOM_NIF':
            # animation group extra data is not present in geometry only files
            return
        if "Anim" not in bpy.data.texts:
            return
        animtxt = bpy.data.texts["Anim"]
        NifLog.info("Exporting animation groups")
        # -> get animation groups information

        # parse the anim text descriptor

        # the format is:
        # frame/string1[/string2[.../stringN]]

        # example:
        # 001/Idle: Start/Idle: Stop/Idle2: Start/Idle2: Loop Start
        # 051/Idle2: Stop/Idle3: Start
        # 101/Idle3: Loop Start/Idle3: Stop

        slist = animtxt.asLines()
        flist = []
        dlist = []
        for s in slist:
            # ignore empty lines
            if not s:
                continue
            # parse line
            t = s.split('/')
            if len(t) < 2:
                raise nif_utils.NifError("Syntax error in Anim buffer ('{}')".format(s))
            f = int(t[0])
            if (f < bpy.context.scene.frame_start) or (f > bpy.context.scene.frame_end):
                NifLog.warn("Frame in animation buffer out of range ({0} not between [{1}, {2}])".format(
                    str(f), str(bpy.context.scene.frame_start), str(bpy.context.scene.frame_end)))
            d = t[1].strip()
            for i in range(2, len(t)):
                d = d + '\r\n' + t[i].strip()
            # print 'frame %d'%f + ' -> \'%s\''%d # debug
            flist.append(f)
            dlist.append(d)

        # -> now comes the real export

        # add a NiTextKeyExtraData block, and refer to this block in the
        # parent node (we choose the root block)
        textextra = self.nif_export.objecthelper.create_block("NiTextKeyExtraData", animtxt)
        block_parent.add_extra_data(textextra)

        # create a text key for each frame descriptor
        textextra.num_text_keys = len(flist)
        textextra.text_keys.update_size()
        for i, key in enumerate(textextra.text_keys):
            key.time = flist[i] / self.fps
            key.value = dlist[i]

        return textextra


class TextureAnimation:

    def __init__(self, parent):
        self.nif_export = parent

    def export_flip_controller(self, fliptxt, texture, target, target_tex):
        # TODO [animation] port code to use native Blender texture flipping system
        #
        # export a NiFlipController
        #
        # fliptxt is a blender text object containing the flip definitions
        # texture is the texture object in blender ( texture is used to checked for pack and mipmap flags )
        # target is the NiTexturingProperty
        # target_tex is the texture to flip ( 0 = base texture, 4 = glow texture )
        #
        # returns exported NiFlipController
        #
        tlist = fliptxt.asLines()

        # create a NiFlipController
        flip = self.nif_export.objecthelper.create_block("NiFlipController", fliptxt)
        target.add_controller(flip)

        # fill in NiFlipController's values
        flip.flags = 8  # active
        flip.frequency = 1.0
        flip.start_time = (bpy.context.scene.frame_start - 1) * bpy.context.scene.render.fps
        flip.stop_time = (bpy.context.scene.frame_end - bpy.context.scene.frame_start) * bpy.context.scene.render.fps
        flip.texture_slot = target_tex
        count = 0
        for t in tlist:
            if len(t) == 0:
                continue  # skip empty lines
            # create a NiSourceTexture for each flip
            tex = self.nif_export.texturehelper.texture_writer.export_source_texture(texture, t)
            flip.num_sources += 1
            flip.sources.update_size()
            flip.sources[flip.num_sources - 1] = tex
            count += 1
        if count < 2:
            raise nif_utils.NifError(
                "Error in Texture Flip buffer '{}': must define at least two textures".format(fliptxt.name))
        flip.delta = (flip.stop_time - flip.start_time) / count


class MaterialAnimation:

    def __init__(self, parent):
        self.nif_export = parent
        self.fps = bpy.context.scene.render.fps

    def export_material_controllers(self, b_material, n_geom):
        """Export material animation data for given geometry."""

        if NifOp.props.animation == 'GEOM_NIF':
            # geometry only: don't write controllers
            return

        # check if the material holds an animation
        if b_material and not (b_material.animation_data and b_material.animation_data.action):
            return

        # find the nif material property to attach alpha & color controllers to
        n_matprop = nif_utils.find_property(n_geom, NifFormat.NiMaterialProperty)
        if not n_matprop:
            raise ValueError("Bug!! must add material property before exporting alpha controller")
        colors = (("alpha", None),
                  ("niftools.ambient_color", NifFormat.TargetColor.TC_AMBIENT),
                  ("diffuse_color", NifFormat.TargetColor.TC_DIFFUSE),
                  ("specular_color", NifFormat.TargetColor.TC_SPECULAR))
        # the actual export
        for b_dtype, n_dtype in colors:
            self.export_material_alpha_color_controller(b_material, n_matprop, b_dtype, n_dtype)
        self.export_material_uv_controller(b_material, n_geom)

    def export_material_alpha_color_controller(self, b_material, n_matprop, b_dtype, n_dtype):
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
        n_key_data = self.nif_export.objecthelper.create_block(keydata, fcurves)
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
            n_mat_ctrl = self.nif_export.objecthelper.create_block(controller, fcurves)
            n_mat_ipol = self.nif_export.objecthelper.create_block(interpolator, fcurves)
            n_mat_ctrl.interpolator = n_mat_ipol

            set_flags_and_timing(n_mat_ctrl, fcurves)
            # set target color only for color controller
            if n_dtype:
                n_mat_ctrl.set_target_color(n_dtype)
            n_mat_ctrl.data = n_key_data
            n_mat_ipol.data = n_key_data
            # attach block to material property
            n_matprop.add_controller(n_mat_ctrl)

    def export_material_uv_controller(self, b_material, n_geom):
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
                # NifLog.info("Exporting {0} as NiUVData".format(b_curve))
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
        # if uv data is present
        # then add the controller so it is exported
        if fcurves[0].keyframe_points:
            n_uv_ctrl = NifFormat.NiUVController()
            set_flags_and_timing(n_uv_ctrl, fcurves)
            n_uv_ctrl.data = n_uv_data
            # attach block to geometry
            n_geom.add_controller(n_uv_ctrl)


class ObjectAnimation:

    def __init__(self, parent):
        self.nif_export = parent

    def export_object_vis_controller(self, n_node, b_obj):
        """Export the visibility controller data."""

        if not b_obj.animation_data and not b_obj.animation_data.action:
            return
        # get the hide fcurve
        fcurves = [fcu for fcu in b_obj.animation_data.action.fcurves if "hide" in fcu.data_path]
        if not fcurves:
            return

        # TODO [animation] which sort of controller should be exported?
        #                  should this be driven by version number?
        #                  we probably don't want both at the same time
        # NiVisData = old style, NiBoolData = new style
        n_vis_data = self.nif_export.objecthelper.create_block("NiVisData", fcurves)
        n_bool_data = self.nif_export.objecthelper.create_block("NiBoolData", fcurves)

        # we just leave interpolation at constant
        n_bool_data.data.interpolation = NifFormat.KeyType.CONST_KEY
        n_vis_data.num_keys = len(fcurves[0].keyframe_points)
        n_vis_data.keys.update_size()
        n_bool_data.data.num_keys = len(fcurves[0].keyframe_points)
        n_bool_data.data.keys.update_size()
        for b_point, n_vis_key, n_bool_key in zip(fcurves[0].keyframe_points, n_vis_data.keys, n_bool_data.data.keys):
            # add each point of the curve
            b_frame, b_value = b_point.co
            n_vis_key.arg = n_bool_data.data.interpolation  # n_vis_data has no interpolation stored
            n_vis_key.time = b_frame / bpy.context.scene.render.fps
            n_vis_key.value = b_value
            n_bool_key.arg = n_bool_data.data.interpolation
            n_bool_key.time = n_vis_key.time
            n_bool_key.value = n_vis_key.value
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if fcurves[0].keyframe_points:
            n_vis_ctrl = self.nif_export.objecthelper.create_block("NiVisController", fcurves)
            n_vis_ipol = self.nif_export.objecthelper.create_block("NiBoolInterpolator", fcurves)
            set_flags_and_timing(n_vis_ctrl, fcurves)
            n_vis_ctrl.interpolator = n_vis_ipol
            n_vis_ctrl.data = n_vis_data
            n_vis_ipol.data = n_bool_data
            # attach block to node
            n_node.add_controller(n_vis_ctrl)
