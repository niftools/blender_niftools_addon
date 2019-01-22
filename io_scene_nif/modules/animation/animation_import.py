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
import math
from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp



### todo: this should probably be moved to utils?
### or maybe use numpy - np.interp() is equivalent but probably way too much overhead for just that one function

from bisect import bisect_left
def interpolate(x_out, x_in, y_in):
    """
    sample (x_in I y_in) at x coordinates x_out
    """
    y_out = []
    intervals = zip(x_in, x_in[1:], y_in, y_in[1:])
    slopes = [(y2 - y1)/(x2 - x1) for x1, x2, y1, y2 in intervals]
    #if we had just one input, slope will be 0 for constant extrapolation
    if not slopes: slopes = [0,]
    for x in x_out:
        i = bisect_left(x_in, x) - 1
        #clamp to valid range
        i = max(min(i, len(slopes)-1), 0)
        y_out.append(y_in[i] + slopes[i] * (x - x_in[i]) )
    return y_out

### do all NIFs use the same coordinate system?
### this should probably be moved to utils
    
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

### also useful for export  

def get_armature():
    """
    Get an armature.
    If there is more than one armature in the scene and some armatures are selected, return the first of the selected armatures.
    """
    src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
    #do we have armatures?
    if src_armatures:
        #see if one of these is selected -> get only that one
        if len(src_armatures) > 1:
            sel_armatures = [ob for ob in src_armatures if ob.select]
            if sel_armatures:
                return sel_armatures[0]
        return src_armatures[0]

def get_keymat(rest_rot_inv, key_matrix):
    """
    Handles space conversions for imported keys
    """
    key_matrix = rest_rot_inv * key_matrix
    return correction_local * key_matrix * correction_local_inv
        
def get_bind_data(armature):
    """
    Get the required bind data of an armature.
    """
    if armature:
        bones_data = {}
        for bone in armature.data.bones:
            rest_scale, rest_rot, rest_trans = nif_utils.decompose_srt( get_bind_matrix(bone) )
            bones_data[bone.name] = (rest_scale, rest_rot.inverted().to_4x4(), rest_trans)
        return bones_data

def create_fcurves(action, bonename, dtype, dlen):
    """
    Create fcurves for bonename in action.
    """
    return [action.fcurves.new(data_path = 'pose.bones["'+bonename+'"].'+dtype, index = i, action_group = bonename) for i in range(dlen)]
    
def add_key(fcurves, t, fps, key, interp):
    """
    Add a key (len=n) to a set of fcurves (len=n) at the given frame. Set the key's interpolation to interp.
    """
    frame = round(t * fps)
    for fcurve, k in zip(fcurves, key):
        fcurve.keyframe_points.insert(frame, k).interpolation = interp
    
def get_interp_mode(kf_element, ):
    """
    Get an appropriate interpolation mode for blender's fcurves from the KF interpolation mode
    """
    
    #TODO: join / make compatible with nif_common.get_b_curve_from_n_curve?
    
    #rotation mode interpolation
    if isinstance(kf_element, NifFormat.NiKeyframeData):
        if kf_element.rotation_type in (NifFormat.KeyType.LINEAR_KEY, NifFormat.KeyType.XYZ_ROTATION_KEY):
            return "LINEAR"
        else:
            return "QUAD"
    #scale or translation 
    else:
        if kf_element.interpolation == NifFormat.KeyType.LINEAR_KEY:
            return "LINEAR"
        else:
            return "QUAD"
    
class AnimationHelper():
    
    def __init__(self, parent):
        self.nif_import = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.armature_animation = ArmatureAnimation(parent)
        self.fps = 30

 
    def import_kf_standalone(self, kf_root):
        """
        Import a kf animation. Needs a suitable armature in blender scene.
        """

        NifLog.info("Importing KF tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise nif_utils.NifError("non-Oblivion .kf import not supported")

        b_armature_object = get_armature()
        bind_data = get_bind_data(b_armature_object)
        if not bind_data:
            raise nif_utils.NifError("No armature was found in scene")
        
        # import text keys
        self.import_text_keys(kf_root)
        
        b_armature_object.animation_data_create()
        b_armature_action = bpy.data.actions.new( self.nif_import.get_bone_name_for_blender(kf_root.name) )
        b_armature_object.animation_data.action = b_armature_action
        # go over all controlled blocks (NiKeyframeController)
        for controlledblock in kf_root.controlled_blocks:
            # nb: this yielded just an empty bytestring
            # nodename = controlledblock.get_node_name()
            bone_name = self.nif_import.get_bone_name_for_blender( controlledblock.target_name )
            if bone_name in bind_data:
                niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans = bind_data[bone_name]
                
                kfc = controlledblock.controller
                self.armature_animation.import_keyframe_controller(kfc, b_armature_object, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans)
                

    def import_kf_root(self, kf_root, root):
        """Merge kf into nif.

        *** Note: this function will eventually move to PyFFI. ***
        """

        NifLog.info("Merging kf tree into nif tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise nif_utils.NifError("non-Oblivion .kf import not supported")

        # import text keys
        self.import_text_keys(kf_root)


        # go over all controlled blocks
        for controlledblock in kf_root.controlled_blocks:
            # get the name
            nodename = controlledblock.get_node_name()
            # match from nif tree?
            node = root.find(block_name = nodename)
            if not node:
                NifLog.info("Animation for {0} but no such node found in nif tree".format(nodename))
                continue
            # node found, now find the controller
            controllertype = controlledblock.get_controller_type().decode()
            if not controllertype:
                NifLog.info("Animation for {0} without controller type, so skipping".format(nodename))
                continue
            controller = nif_utils.find_controller(node, getattr(NifFormat, controllertype))
            if not controller:
                NifLog.info("No {1} Controller found in corresponding animation node {0}, creating one".format(controllertype, nodename))
                controller = getattr(NifFormat, controllertype)()
                # TODO:set all the fields of this controller
                node.add_controller(controller)
            # yes! attach interpolator
            controller.interpolator = controlledblock.interpolator
            # in case of a NiTransformInterpolator without a data block
            # we still must re-export the interpolator for Oblivion to
            # accept the file
            # so simply add dummy keyframe data for this one with just a single
            # key to flag the exporter to export the keyframe as interpolator
            # (i.e. length 1 keyframes are simply interpolators)
            if isinstance(controller.interpolator,
                          NifFormat.NiTransformInterpolator) \
                and controller.interpolator.data is None:
                # create data block
                kfi = controller.interpolator
                kfi.data = NifFormat.NiTransformData()
                # fill with info from interpolator
                kfd = controller.interpolator.data
                # copy rotation
                kfd.num_rotation_keys = 1
                kfd.rotation_type = NifFormat.KeyType.LINEAR_KEY
                kfd.quaternion_keys.update_size()
                kfd.quaternion_keys[0].time = 0.0
                kfd.quaternion_keys[0].value.x = kfi.rotation.x
                kfd.quaternion_keys[0].value.y = kfi.rotation.y
                kfd.quaternion_keys[0].value.z = kfi.rotation.z
                kfd.quaternion_keys[0].value.w = kfi.rotation.w
                # copy translation
                if kfi.translation.x < -1000000:
                    # invalid, happens in fallout 3, e.g. h2haim.kf
                    NifLog.warn("Ignored NaN in interpolator translation")
                else:
                    kfd.translations.num_keys = 1
                    kfd.translations.keys.update_size()
                    kfd.translations.keys[0].time = 0.0
                    kfd.translations.keys[0].value.x = kfi.translation.x
                    kfd.translations.keys[0].value.y = kfi.translation.y
                    kfd.translations.keys[0].value.z = kfi.translation.z
                # ignore scale, usually contains invalid data in interpolator

            # save priority for future reference
            # (priorities will be stored into the name of a TRANSFORM constraint on
            # bones, see import_armature function)
            # This name is a bytestring, not a string
            self.nif_import.dict_bone_priorities[nodename] = controlledblock.priority

        # DEBUG: save the file for manual inspection
        #niffile = open("C:\\test.nif", "wb")
        #NifFormat.write(niffile,
        #                version = 0x14000005, user_version = 11, roots = [root])
    
    
    # import animation groups
    def import_text_keys(self, niBlock):
        """Stores the text keys that define animation start and end in a text
        buffer, so that they can be re-exported. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""
        
        if isinstance(niBlock, NifFormat.NiControllerSequence):
            txk = niBlock.text_keys
        else:
            txk = niBlock.find(block_type=NifFormat.NiTextKeyExtraData)
        if txk:
            # get animation text buffer, and clear it if it already exists
            name = "Anim"
            if name in bpy.data.texts:
                animtxt = bpy.data.texts["Anim"]
                animtxt.clear()
            else:
                animtxt = bpy.data.texts.new("Anim")

            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = round(key.time * self.fps)
                animtxt.write('%i/%s\n'%(frame, newkey))

            # set start and end frames
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = frame

    def get_frames_per_second(self, roots):
        """Scan all blocks and return a reasonable number for FPS."""
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
            for uvdata in root.tree(block_type=NifFormat.NiUVData):
                for uvgroup in uvdata.uv_groups:
                    key_times.extend(key.time for key in uvgroup.keys)
        # not animated, return a reasonable default
        if not key_times:
            return 30
        # calculate FPS
        fps = 30
        lowest_diff = sum(abs(int(time * fps + 0.5) - (time * fps))
                          for time in key_times)
        # for test_fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 25, 35]:
            diff = sum(abs(int(time * test_fps + 0.5)-(time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        NifLog.info("Animation estimated at %i frames per second." % fps)
        return fps

    def store_animation_data(self, rootBlock):
        return
        # very slow, implement later
        """
        niBlockList = [block for block in rootBlock.tree() if isinstance(block, NifFormat.NiAVObject)]
        for niBlock in niBlockList:
            kfc = nif_utils.find_controller(niBlock, NifFormat.NiKeyframeController)
            if not kfc: continue
            kfd = kfc.data
            if not kfd: continue
            _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.translations.keys])
            _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.scales.keys])
            if kfd.rotation_type == 4:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.xyz_rotations.keys])
            else:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.quaternion_keys])

        # set the frames in the _ANIMATION_DATA list
        for key in _ANIMATION_DATA:
            # time 0 is frame 1
            key['frame'] = 1 + int(key['data'].time * self.fps + 0.5)

        # sort by frame, I need this later
        _ANIMATION_DATA.sort(lambda key1, key2: cmp(key1['frame'], key2['frame']))
        """

        
    def set_animation(self, niBlock, b_obj):
        """Load basic animation info for this object."""
        kfc = nif_utils.find_controller(niBlock, NifFormat.NiKeyframeController)
        if not kfc:
            # no animation data: do nothing
            return

        if kfc.interpolator:
            if isinstance(kfc.interpolator, NifFormat.NiBSplineInterpolator):
                kfd = None # not supported yet so avoids fatal error - should be kfc.interpolator.spline_data when spline data is figured out.
            else:
                kfd = kfc.interpolator.data
        else:
            kfd = kfc.data

        if not kfd:
            # no animation data: do nothing
            return

        # denote progress
        NifLog.info("Animation")
        NifLog.info("Importing animation data for {0}".format(b_obj.name))
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        # get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys

        #Create curve structure
        if b_obj.animation_data == None:
            b_obj.animation_data_create()
        b_obj_action = bpy.data.actions.new(str(b_obj.name) + "-Anim")
        b_obj.animation_data.action = b_obj_action

        NifLog.debug('Scale keys...')
        for key in scales.keys:
            frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
            bpy.context.scene.frame_set(frame)
            b_obj.scale = (key.value,key.value,key.value)
            b_obj.keyframe_insert('scale')

        # detect the type of rotation keys
        rotation_type = kfd.rotation_type
        if rotation_type == 4:
            # uses xyz rotation
            xkeys = kfd.xyz_rotations[0].keys
            ykeys = kfd.xyz_rotations[1].keys
            zkeys = kfd.xyz_rotations[2].keys
            NifLog.debug('Rotation keys...(euler)')
            for (xkey, ykey, zkey) in zip(xkeys, ykeys, zkeys):
                frame = 1+int(xkey.time * self.fps + 0.5) # time 0.0 is frame 1
                # XXX we assume xkey.time == ykey.time == zkey.time
                bpy.context.scene.frame_set(frame)
                # both in radians, no conversion needed
                b_obj.rotation_euler = (xkey.value, ykey.value, zkey.value)
                b_obj.keyframe_insert('rotation_euler')
        else:
            # uses quaternions
            if kfd.quaternion_keys:
                NifLog.debug('Rotation keys...(quaternions)')
            for key in kfd.quaternion_keys:
                frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                bpy.context.scene.frame_set(frame)
                #Blender euler is now in radians, not degrees
                rot = mathutils.Quaternion((key.value.w, key.value.x, key.value.y, key.value.z)).toEuler()
                b_obj.rotation_euler = (rot.x, rot.y, rot.z)
                b_obj.keyframe_insert('rotation_euler')

        if translations.keys:
            NifLog.debug('Translation keys...')
        for key in translations.keys:
            frame = 1+int(key.time * self.nif_import.fps + 0.5) # time 0.0 is frame 1
            bpy.context.scene.frame_set(frame)
            b_obj.location = (key.value.x, key.value.y, key.value.z)
            b_obj.keyframe_insert('location')

        bpy.context.scene.frame_set(1)


class ObjectAnimation():
    
    def __init__(self, parent):
        self.nif_import = parent
    
    def get_object_ipo(self, b_object):
        """Return existing object ipo data, or if none exists, create one
        and return that.
        """
        if not b_object.ipo:
            b_object.ipo = Blender.Ipo.New("Object", "Ipo")
        return b_object.ipo    
    
    def import_object_vis_controller(self, b_object, n_node):
        """Import vis controller for blender object."""
        n_vis_ctrl = nif_utils.find_controller(n_node, NifFormat.NiVisController)
        if not(n_vis_ctrl and n_vis_ctrl.data):
            return
        NifLog.info("Importing vis controller")
        b_channel = "Layer"
        b_ipo = self.get_object_ipo(b_object)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = Blender.IpoCurve.InterpTypes.CONST
        b_curve.extend = self.nif_import.get_extend_from_flags(n_vis_ctrl.flags)
        for n_key in n_vis_ctrl.data.keys:
            b_curve[1 + n_key.time * self.fps] = (
                2 ** (n_key.value + max([1] + bpy.context.scene.getLayers()) - 1))

class MaterialAnimation():
    
    def __init__(self, parent):
        self.nif_import = parent
    
    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not NifOp.props.animation:
            return

        self.import_material_alpha_controller(b_material, n_geom)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("MirR", "MirG", "MirB"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("R", "G", "B"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("SpecR", "SpecG", "SpecB"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_SPECULAR)
        self.import_material_uv_controller(b_material, n_geom)
        
    def import_material_alpha_controller(self, b_material, n_geom):
        # find alpha controller
        n_matprop = nif_utils.find_property(n_geom, NifFormat.NiMaterialProperty)
        if not n_matprop:
            return
        n_alphactrl = nif_utils.find_controller(n_matprop,
                                           NifFormat.NiAlphaController)
        if not(n_alphactrl and n_alphactrl.data):
            return
        NifLog.info("Importing alpha controller")
        b_channel = "Alpha"
        b_ipo = self.get_material_ipo(b_material)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = self.nif_import.get_b_curve_from_n_curve(
            n_alphactrl.data.data.interpolation)
        b_curve.extend = self.nif_import.get_extend_from_flags(n_alphactrl.flags)
        for n_key in n_alphactrl.data.data.keys:
            b_curve[1 + n_key.time * self.fps] = n_key.value

    def import_material_color_controller(
        self, b_material, b_channels, n_geom, n_target_color):
        # find material color controller with matching target color
        n_matprop = nif_utils.find_property(n_geom, NifFormat.NiMaterialProperty)
        if not n_matprop:
            return
        for ctrl in n_matprop.get_controllers():
            if isinstance(ctrl, NifFormat.NiMaterialColorController):
                if ctrl.get_target_color() == n_target_color:
                    n_matcolor_ctrl = ctrl
                    break
        else:
            return
        NifLog.info("Importing material color controller for target color {0} into blender channels {0}".format(n_target_color, b_channels))
        # import data as curves
        b_ipo = self.get_material_ipo(b_material)
        for i, b_channel in enumerate(b_channels):
            b_curve = b_ipo.addCurve(b_channel)
            b_curve.interpolation = self.nif_import.get_b_curve_from_n_curve(
                n_matcolor_ctrl.data.data.interpolation)
            b_curve.extend = self.nif_import.get_extend_from_flags(n_matcolor_ctrl.flags)
            for n_key in n_matcolor_ctrl.data.data.keys:
                b_curve[1 + n_key.time * self.fps] = n_key.value.as_list()[i]

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom,
                                      NifFormat.NiUVController)
        if not(n_ctrl and n_ctrl.data):
            return
        NifLog.info("Importing UV controller")
        b_channels = ("OfsX", "OfsY", "SizeX", "SizeY")
        for b_channel, n_uvgroup in zip(b_channels,
                                        n_ctrl.data.uv_groups):
            if n_uvgroup.keys:
                # create curve in material ipo
                b_ipo = self.get_material_ipo(b_material)
                b_curve = b_ipo.addCurve(b_channel)
                b_curve.interpolation = self.nif_import.get_b_curve_from_n_curve(
                    n_uvgroup.interpolation)
                b_curve.extend = self.nif_import.get_extend_from_flags(n_ctrl.flags)
                for n_key in n_uvgroup.keys:
                    if b_channel.startswith("Ofs"):
                        # offsets are negated
                        b_curve[1 + n_key.time * self.fps] = -n_key.value
                    else:
                        b_curve[1 + n_key.time * self.fps] = n_key.value    
    

    def get_material_ipo(self, b_material):
        """Return existing material ipo data, or if none exists, create one
        and return that.
        """
        if not b_material.ipo:
            b_material.ipo = Blender.Ipo.New("Material", "MatIpo")
        return b_material.ipo

class ArmatureAnimation():
    
    def __init__(self, parent):
        self.nif_import = parent
        self.fps = 30

    
    def import_keyframe_controller(self, kfc, b_armature_object, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans):
        b_armature_action = b_armature_object.animation_data.action
        # old style: data directly on controller
        kfd = kfc.data if kfc else None
        # new style: data via interpolator
        kfi = kfc.interpolator if kfc else None

        
        #TODO: test interpolators
        # B-spline curve import
        if isinstance(kfi, NifFormat.NiBSplineInterpolator):
            times = list(kfi.get_times())
            
            translations = zip( times, list(kfi.get_translations()) )
            scales = zip( times, list(kfi.get_scales()) )
            rotations = zip( times, list(kfi.get_rotations()) )
            eulers = []
            
            #TODO: get these from interpolator?
            interp_rot = "LINEAR"
            interp_loc = "LINEAR"
            interp_scale = "LINEAR"
        # next is a quick hack to make the new transform
        # interpolator work as if it is an old style keyframe data
        # block parented directly on the controller
        if isinstance(kfi, NifFormat.NiTransformInterpolator):
            kfd = kfi.data
            # for now, in this case, ignore interpolator
            kfi = None
        if isinstance(kfd, NifFormat.NiKeyframeData):
            translations = []
            scales = []
            rotations = []
            eulers = []
            
            interp_rot = get_interp_mode(kfd)
            interp_loc = get_interp_mode(kfd.translations)
            interp_scale = get_interp_mode(kfd.scales)
            if kfd.rotation_type == 4:
                b_armature_object.pose.bones[bone_name].rotation_mode = "XYZ"
                # uses xyz rotation
                if kfd.xyz_rotations[0].keys:
                    
                    #euler keys need not be sampled at the same time in KFs
                    #but we need complete key sets to do the space conversion
                    #so perform linear interpolation to import all keys properly
                    
                    #get all the keys' times
                    times_x = [key.time for key in kfd.xyz_rotations[0].keys]
                    times_y = [key.time for key in kfd.xyz_rotations[1].keys]
                    times_z = [key.time for key in kfd.xyz_rotations[2].keys]
                    #the unique time stamps we have to sample all curves at
                    times_all = sorted( set(times_x + times_y + times_z) )
                    #the actual resampling
                    x_r = interpolate(times_all, times_x, [key.value for key in kfd.xyz_rotations[0].keys])
                    y_r = interpolate(times_all, times_y, [key.value for key in kfd.xyz_rotations[1].keys])
                    z_r = interpolate(times_all, times_z, [key.value for key in kfd.xyz_rotations[2].keys])
                eulers = zip(times_all, zip(x_r, y_r, z_r) )
            else:
                rotations = [(key.time, key.value) for key in kfd.quaternion_keys]
        
            if kfd.scales.keys:
                scales = [(key.time, key.value) for key in kfd.scales.keys]
                
            if kfd.translations.keys:
                translations = [(key.time, key.value) for key in kfd.translations.keys]
                
        #todo: move frame conversion into function
        
        if eulers:
            NifLog.debug('Rotation keys...(euler)')
            fcurves = create_fcurves(b_armature_action, bone_name, "rotation_euler", 3)
            for t, val in eulers:
                euler = mathutils.Euler( val )
                key = get_keymat(niBone_bind_rot_inv, euler.to_matrix().to_4x4() ).to_euler()
                add_key(fcurves, t, self.fps, key, interp_rot)
        elif rotations:
            NifLog.debug('Rotation keys...(quaternions)')
            fcurves = create_fcurves(b_armature_action, bone_name, "rotation_quaternion", 4)
            for t, val in rotations:
                quat = mathutils.Quaternion([val.w, val.x, val.y, val.z])
                key = get_keymat(niBone_bind_rot_inv, quat.to_matrix().to_4x4() ).to_quaternion()
                add_key(fcurves, t, self.fps, key, interp_rot)
        
        if scales:
            NifLog.debug('Scale keys...')
            fcurves = create_fcurves(b_armature_action, bone_name, "scale", 3)
            for t, val in scales:
                key = (val, val, val)
                add_key(fcurves, t, self.fps, key, interp_scale)
                    
        if translations:
            NifLog.debug('Translation keys...')
            fcurves = create_fcurves(b_armature_action, bone_name, "location", 3)
            for t, val in translations:
                vec = mathutils.Vector([val.x, val.y, val.z])
                key = get_keymat(niBone_bind_rot_inv, mathutils.Matrix.Translation(vec - niBone_bind_trans)).to_translation()
                add_key(fcurves, t, self.fps, key, interp_loc)
        
        if kfc:
            #probably a superfluous check
            if bone_name in b_armature_action.groups:
                bone_fcurves = b_armature_action.groups[bone_name].channels
                f_curve_extend_type = self.nif_import.get_extend_from_flags(kfc.flags)
                if f_curve_extend_type == "CONST":
                    for fcurve in bone_fcurves:
                        fcurve.extrapolation = 'CONSTANT'
                elif f_curve_extend_type == "CYCLIC":
                    for fcurve in bone_fcurves:
                        fcurve.modifiers.new('CYCLES')
                else:
                    for fcurve in bone_fcurves:
                        fcurve.extrapolation = 'CONSTANT'        
        
    def import_armature_animation(self, b_armature):
		"""
		Imports an animation contained in the NIF itself.
		"""
        # create an action
        b_armature_object = bpy.data.objects[b_armature.name]
        b_armature_object.animation_data_create()
        b_armature_action = bpy.data.actions.new(str(b_armature.name) + "-kfAnim")
        b_armature_object.animation_data.action = b_armature_action
        # go through all armature pose bones
        NifLog.info('Importing Animations')
        for bone_name, b_posebone in b_armature.pose.bones.items():
            # denote progress
            NifLog.debug('Importing animation for bone %s'.format(bone_name))
            niBone = self.nif_import.dict_blocks[bone_name]

            bone_bm = nif_utils.import_matrix(niBone) # base pose
            niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = nif_utils.decompose_srt(bone_bm)
            niBone_bind_rot_inv = niBone_bind_rot.to_4x4().inverted()
            
            # get controller, interpolator, and data
            # note: the NiKeyframeController check also includes
            #       NiTransformController (see hierarchy!)
            kfc = nif_utils.find_controller(niBone, NifFormat.NiKeyframeController)
                                       
            self.import_keyframe_controller(kfc, b_armature_object, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans)
