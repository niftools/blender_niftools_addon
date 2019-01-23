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

from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp
import math

correction_local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
correction_local_inv = correction_local.inverted()
correction_global = mathutils.Euler((math.radians(-90), math.radians(-90), 0)).to_matrix().to_4x4()

### also useful for export  

def get_bind_matrix(bone):
    """
    Get a nif armature-space matrix from a blender bone matrix.
    """
    bind = correction_global.inverted() *  correction_local.inverted() * bone.matrix_local *  correction_local
    if bone.parent:
        p_bind_restored = correction_global.inverted() *  correction_local.inverted() * bone.parent.matrix_local *  correction_local
        bind = p_bind_restored.inverted() * bind
    return bind

def export_keymat(rest_rot, key_matrix):
    key_matrix = correction_local_inv * key_matrix * correction_local
    return rest_rot * key_matrix
    
class AnimationHelper():
    
    def __init__(self, parent):
        self.nif_export = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.texture_animation = TextureAnimation(parent)
    
    def get_flags_from_extend(self, cyclic):
        if cyclic:
            return 0
        else:
            return 4 # 0b100

    
    def export_keyframes(self, arm, bone, parent_block):
        print("export_keyframes",bone.name)
        action = arm.animation_data.action
        if not action:
            return
        if bone.name in action.groups:
            action_group = action.groups[bone.name]
        else:
            action_group = None
        self.fps = bpy.context.scene.render.fps
        if NifOp.props.animation == 'GEOM_NIF' and self.nif_export.version < 0x0A020000:
            # keyframe controllers are not present in geometry only files
            # for more recent versions, the controller and interpolators are
            # present, only the data is not present (see further on)
            return
    
        # make sure the parent is of the right type
        assert(isinstance(parent_block, NifFormat.NiNode))
    
        # add a keyframecontroller block, and refer to this block in the
        # parent's time controller
        if self.nif_export.version < 0x0A020000:
            kfc = self.nif_export.objecthelper.create_block("NiKeyframeController", action_group)
        else:
            kfc = self.nif_export.objecthelper.create_block("NiTransformController", action_group)
            kfi = self.nif_export.objecthelper.create_block("NiTransformInterpolator", action_group)
            # link interpolator from the controller
            kfc.interpolator = kfi
            # set interpolator default data
            scale, quat, trans = \
                parent_block.get_transform().get_scale_quat_translation()
            kfi.translation.x = trans.x
            kfi.translation.y = trans.y
            kfi.translation.z = trans.z
            kfi.rotation.x = quat.x
            kfi.rotation.y = quat.y
            kfi.rotation.z = quat.z
            kfi.rotation.w = quat.w
            kfi.scale = scale
    
        parent_block.add_controller(kfc)
    
        # determine cycle mode for this controller
        # this is stored in the blender ipo curves
        # while we're at it, we also determine the
        # start and stop frames
        extend = None
        
        #TODO: or use the extent of each fcurve - fcu.range()?
        start_frame, stop_frame = action.frame_range
        cyclic = False
        #see if there are cyclic extrapolation modifiers on the fcurves
        if action_group:
            for fcu in action_group.channels:
                for mod in fcu.modifiers:
                    if mod.type == "CYCLES":
                        cyclic = True
                        break
        else:
            start_frame = bpy.context.scene.frame_start
            stop_frame = bpy.context.scene.frame_end
    
        # fill in the non-trivial values
        kfc.flags = 8 # active
        kfc.flags |= self.get_flags_from_extend(cyclic)
        kfc.frequency = 1.0
        kfc.phase = 0.0
        kfc.start_time = start_frame / self.fps
        kfc.stop_time = stop_frame / self.fps
    
        if NifOp.props.animation == 'GEOM_NIF':
            # keyframe data is not present in geometry files
            return
    
        # -> get keyframe information
    
        # some calculations
        bind_matrix = get_bind_matrix(bone)
        bind_scale, bind_rot, bind_trans = nif_utils.decompose_srt(bind_matrix)
        bind_rot = bind_rot.to_4x4()
    
        #just create a dummy euler so we can make all following eulers compatible to each other
        euler = mathutils.Euler((0.0, math.radians(45.0), 0.0), 'XYZ')
        
        # sometimes we need to export an empty keyframe... 
        scale_curve = []
        quat_curve = []
        euler_curve = []
        trans_curve = []
        if action_group:
            quaternions = [fcu for fcu in action_group.channels if fcu.data_path.endswith("quaternion")]
            translations = [fcu for fcu in action_group.channels if fcu.data_path.endswith("location")]
            eulers = [fcu for fcu in action_group.channels if fcu.data_path.endswith("euler")]
            scales = [fcu for fcu in action_group.channels if fcu.data_path.endswith("scale")]
            # merge the animation curves into a rotation vector and translation vector curve
            
            #scales
            if scales:
                num_keys = len(scales[0].keyframe_points)
                for i in range(num_keys):
                    frame = scales[0].keyframe_points[i].co[0]
                    scale = scales[0].keyframe_points[i].co[1]
                    scale_curve.append( (frame, scale) )
            
            #quaternions
            if quaternions:
                if len(quaternions) != 4:
                    raise nif_utils.NifError("Incomplete ROT key set in bone "+bone.name+" for action "+action.name)
                else:
                    num_keys = len(quaternions[0].keyframe_points)
                    for i in range(num_keys):
                        frame = quaternions[0].keyframe_points[i].co[0]
                        quat = export_keymat(bind_rot, mathutils.Quaternion([fcurve.keyframe_points[i].co[1] for fcurve in quaternions]).to_matrix().to_4x4()).to_quaternion()
                        quat_curve.append( (frame, quat) )
                    
            #eulers
            if eulers:
                if len(eulers) != 3:
                    raise nif_utils.NifError("Incomplete Euler key set in bone "+bone.name+" for action "+action.name)
                else:
                    num_keys = len(eulers[0].keyframe_points)
                    for i in range(num_keys):
                        frame = eulers[0].keyframe_points[i].co[0]
                        # important: make new euler compatible to the previous euler in to_euler()
                        euler = export_keymat(bind_rot, mathutils.Euler([fcurve.keyframe_points[i].co[1] for fcurve in eulers]).to_matrix().to_4x4() ).to_euler("XYZ", euler)
                        euler_curve.append( (frame, euler) )
                        
            #translations
            if translations:
                if len(translations) != 3:
                    raise nif_utils.NifError("Incomplete LOC key set in bone "+bone.name+" for action "+action.name)
                else:
                    num_keys = len(translations[0].keyframe_points)
                    for i in range(num_keys):
                        frame = translations[0].keyframe_points[i].co[0]
                        trans = export_keymat(bind_rot, mathutils.Matrix.Translation( [fcurve.keyframe_points[i].co[1] for fcurve in translations] ) ).to_translation() + bind_trans
                        trans_curve.append( (frame, trans) )
        # # -> now comes the real export
    
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
            kfd = self.nif_export.objecthelper.create_block("NiKeyframeData", action_group)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.nif_export.objecthelper.create_block("NiTransformData", action_group)
            kfi.data = kfd
    
        if euler_curve:
            kfd.rotation_type = NifFormat.KeyType.XYZ_ROTATION_KEY
            kfd.num_rotation_keys = 1 # *NOT* len(frames) this crashes the engine!
            for i, coord in enumerate(kfd.xyz_rotations):
                coord.num_keys = len(euler_curve)
                # XXX todo: quadratic interpolation?
                coord.interpolation = NifFormat.KeyType.LINEAR_KEY
                coord.keys.update_size()
                for key, (frame, euler) in zip(coord.keys, euler_curve):
                    key.time = frame / self.fps
                    key.value = euler[i]
        elif quat_curve:
            # XXX todo: quadratic interpolation?
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
            

    def export_anim_groups(self, animtxt, block_parent):
        """Parse the animation groups buffer and write an extra string
        data block, and attach it to an existing block (typically, the root
        of the nif tree)."""
        if NifOp.props.animation == 'GEOM_NIF':
            # animation group extra data is not present in geometry only files
            return

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
            if (len(t) < 2):
                raise nif_utils.NifError("Syntax error in Anim buffer ('%s')" % s)
            f = int(t[0])
            if ((f < bpy.context.scene.frame_start) or (f > bpy.context.scene.frame_end)):
                NifLog.warn("Frame in animation buffer out of range ({0} not between [{1}, {2}])".format(str(f), str(bpy.context.scene.frame_start), str(bpy.context.scene.frame_end)))
            d = t[1].strip(' ')
            for i in range(2, len(t)):
                d = d + '\r\n' + t[i].strip(' ')
            #print 'frame %d'%f + ' -> \'%s\''%d # debug
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
            key.time = bpy.context.scene.render.fps * (flist[i]-1)
            key.value = dlist[i]

        return textextra
    
    
class TextureAnimation():
    
    def __init__(self, parent):
        self.nif_export = parent
    
    def export_flip_controller(self, fliptxt, texture, target, target_tex):
        ## TODO:port code to use native Blender texture flipping system
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
        flip.flags = 8 # active
        flip.frequency = 1.0
        flip.start_time = (bpy.context.scene.frame_start - 1) * bpy.context.scene.render.fps
        flip.stop_time = (bpy.context.scene.frame_end - bpy.context.scene.frame_start ) * bpy.context.scene.render.fps
        flip.texture_slot = target_tex
        count = 0
        for t in tlist:
            if len( t ) == 0: continue  # skip empty lines
            # create a NiSourceTexture for each flip
            tex = self.nif_export.texturehelper.texture_writer.export_source_texture(texture, t)
            flip.num_sources += 1
            flip.sources.update_size()
            flip.sources[flip.num_sources-1] = tex
            count += 1
        if count < 2:
            raise nif_utils.NifError(
                "Error in Texture Flip buffer '%s':"
                " must define at least two textures"
                %fliptxt.name)
        flip.delta = (flip.stop_time - flip.start_time) / count

class MaterialAnimation():
    
    def __init__(self, parent):
        self.nif_export = parent
    

    def export_material_controllers(self, b_material, n_geom):
        """Export material animation data for given geometry."""
        # XXX todo: port to blender 2.5x+ interface
        # XXX Blender.Ipo channel constants are replaced by FCurve.data_path?
        return

        if NifOp.props.animation == 'GEOM_NIF':
            # geometry only: don't write controllers
            return

        self.export_material_alpha_controller(b_material, n_geom)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_MIRR, Blender.Ipo.MA_MIRG, Blender.Ipo.MA_MIRB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_R, Blender.Ipo.MA_G, Blender.Ipo.MA_B),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_SPECR, Blender.Ipo.MA_SPECG, Blender.Ipo.MA_SPECB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_SPECULAR)
        self.export_material_uv_controller(b_material, n_geom)


    
    def export_material_alpha_controller(self, b_material, n_geom):
        """Export the material alpha controller data."""
        b_ipo = b_material.animation_data
        if not b_ipo:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_ipo[Blender.Ipo.MA_ALPHA]
        if not b_curve:
            return
        n_floatdata = self.nif_export.objecthelper.create_block("NiFloatData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        n_floatdata.data.num_keys = len(b_curve.bezierPoints)
        n_floatdata.data.interpolation = self.get_n_curve_from_b_curve(
            b_curve.interpolation)
        n_floatdata.data.keys.update_size()
        for b_point, n_key in zip(b_curve.bezierPoints, n_floatdata.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_key.arg = n_floatdata.data.interpolation
            n_key.time = (b_time - 1) * bpy.context.scene.render.fps
            n_key.value = b_value
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_alphactrl = self.nif_export.objecthelper.create_block("NiAlphaController", b_ipo)
            n_alphaipol = self.nif_export.objecthelper.create_block("NiFloatInterpolator", b_ipo)
            n_alphactrl.interpolator = n_alphaipol
            n_alphactrl.flags = 8 # active
            n_alphactrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_alphactrl.frequency = 1.0
            n_alphactrl.start_time = min(n_times)
            n_alphactrl.stop_time = max(n_times)
            n_alphactrl.data = n_floatdata
            n_alphaipol.data = n_floatdata
            # attach block to geometry
            n_matprop = nif_utils.find_property(n_geom,
                                           NifFormat.NiMaterialProperty)
            if not n_matprop:
                raise ValueError(
                    "bug!! must add material property"
                    " before exporting alpha controller")
            n_matprop.add_controller(n_alphactrl)

    def export_material_color_controller(
        self, b_material, b_channels, n_geom, n_target_color):
        """Export the material color controller data."""
        b_ipo = b_material.animation_data
        if not b_ipo:
            return
        # get the material color curves and translate it into nif data
        b_curves = [b_ipo[b_channel] for b_channel in b_channels]
        if not all(b_curves):
            return
        n_posdata = self.nif_export.objecthelper.create_block("NiPosData", b_curves)
        # and also to have common reference times for all curves
        b_times = set()
        for b_curve in b_curves:
            b_times |= set(b_point.pt[0] for b_point in b_curve.bezierPoints)
        # track all nif times: used later in start time and end time
        n_times = []
        n_posdata.data.num_keys = len(b_times)
        n_posdata.data.interpolation = self.get_n_curve_from_b_curve(
            b_curves[0].interpolation)
        n_posdata.data.keys.update_size()
        for b_time, n_key in zip(sorted(b_times), n_posdata.data.keys):
            # add each point of the curves
            n_key.arg = n_posdata.data.interpolation
            n_key.time = (b_time - 1) * bpy.context.scene.render.fps
            n_key.value.x = b_curves[0][b_time]
            n_key.value.y = b_curves[1][b_time]
            n_key.value.z = b_curves[2][b_time]
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_matcolor_ctrl = self.nif_export.objecthelper.create_block(
                "NiMaterialColorController", b_ipo)
            n_matcolor_ipol = self.nif_export.objecthelper.create_block(
                "NiPoint3Interpolator", b_ipo)
            n_matcolor_ctrl.interpolator = n_matcolor_ipol
            n_matcolor_ctrl.flags = 8 # active
            n_matcolor_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_matcolor_ctrl.set_target_color(n_target_color)
            n_matcolor_ctrl.frequency = 1.0
            n_matcolor_ctrl.start_time = min(n_times)
            n_matcolor_ctrl.stop_time = max(n_times)
            n_matcolor_ctrl.data = n_posdata
            n_matcolor_ipol.data = n_posdata
            # attach block to geometry
            n_matprop = nif_utils.find_property(n_geom,
                                           NifFormat.NiMaterialProperty)
            if not n_matprop:
                raise ValueError(
                    "bug!! must add material property"
                    " before exporting material color controller")
            n_matprop.add_controller(n_matcolor_ctrl)

    def export_material_uv_controller(self, b_material, n_geom):
        """Export the material UV controller data."""
        # get the material ipo
        b_ipo = b_material.ipo
        if not b_ipo:
            return
        # get the uv curves and translate them into nif data
        n_uvdata = NifFormat.NiUVData()
        n_times = [] # track all times (used later in start time and end time)
        b_channels = (Blender.Ipo.MA_OFSX, Blender.Ipo.MA_OFSY,
                      Blender.Ipo.MA_SIZEX, Blender.Ipo.MA_SIZEY)
        for b_channel, n_uvgroup in zip(b_channels, n_uvdata.uv_groups):
            b_curve = b_ipo[b_channel]
            if b_curve:
                NifLog.info("Exporting {0} as NiUVData".format(b_curve))
                n_uvgroup.num_keys = len(b_curve.bezierPoints)
                n_uvgroup.interpolation = self.get_n_curve_from_b_curve(
                    b_curve.interpolation)
                n_uvgroup.keys.update_size()
                for b_point, n_key in zip(b_curve.bezierPoints, n_uvgroup.keys):
                    # add each point of the curve
                    b_time, b_value = b_point.pt
                    if b_channel in (Blender.Ipo.MA_OFSX, Blender.Ipo.MA_OFSY):
                        # offsets are negated in blender
                        b_value = -b_value
                    n_key.arg = n_uvgroup.interpolation
                    n_key.time = (b_time - 1) * bpy.context.scene.render.fps
                    n_key.value = b_value
                    # track time
                    n_times.append(n_key.time)
                # save extend mode to export later
                b_curve_extend = b_curve.extend
        # if uv data is present (we check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_uvctrl = NifFormat.NiUVController()
            n_uvctrl.flags = 8 # active
            n_uvctrl.flags |= self.get_flags_from_extend(b_curve_extend)
            n_uvctrl.frequency = 1.0
            n_uvctrl.start_time = min(n_times)
            n_uvctrl.stop_time = max(n_times)
            n_uvctrl.data = n_uvdata
            # attach block to geometry
            n_geom.add_controller(n_uvctrl)
            
            
class ObjectAnimation():
        
    def __init__(self, parent):
        self.nif_export = parent
    
    def export_object_vis_controller(self, b_obj, n_node):
        """Export the material alpha controller data."""
        b_ipo = b_obj.ipo
        if not b_ipo:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_ipo[Blender.Ipo.OB_LAYER]
        if not b_curve:
            return
        # NiVisData = old style, NiBoolData = new style
        n_vis_data = self.nif_export.objecthelper.create_block("NiVisData", b_curve)
        n_bool_data = self.nif_export.objecthelper.create_block("NiBoolData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        # we just leave interpolation at constant
        n_bool_data.data.interpolation = NifFormat.KeyType.CONST_KEY
        #n_bool_data.data.interpolation = self.get_n_curve_from_b_curve(
        #    b_curve.interpolation)
        n_vis_data.num_keys = len(b_curve.bezierPoints)
        n_bool_data.data.num_keys = len(b_curve.bezierPoints)
        n_vis_data.keys.update_size()
        n_bool_data.data.keys.update_size()
        visible_layer = 2 ** (min(bpy.context.scene.getLayers()) - 1)
        for b_point, n_vis_key, n_bool_key in zip(
            b_curve.bezierPoints, n_vis_data.keys, n_bool_data.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_vis_key.arg = n_bool_data.data.interpolation # n_vis_data has no interpolation stored
            n_vis_key.time = (b_time - 1) * bpy.context.scene.render.fps
            n_vis_key.value = 1 if (int(b_value + 0.01) & visible_layer) else 0
            n_bool_key.arg = n_bool_data.data.interpolation
            n_bool_key.time = n_vis_key.time
            n_bool_key.value = n_vis_key.value
            # track time
            n_times.append(n_vis_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_vis_ctrl = self.nif_export.objecthelper.create_block("NiVisController", b_ipo)
            n_vis_ipol = self.nif_export.objecthelper.create_block("NiBoolInterpolator", b_ipo)
            n_vis_ctrl.interpolator = n_vis_ipol
            n_vis_ctrl.flags = 8 # active
            n_vis_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_vis_ctrl.frequency = 1.0
            n_vis_ctrl.start_time = min(n_times)
            n_vis_ctrl.stop_time = max(n_times)
            n_vis_ctrl.data = n_vis_data
            n_vis_ipol.data = n_bool_data
            # attach block to node
            n_node.add_controller(n_vis_ctrl)




