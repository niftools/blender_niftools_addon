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
from bisect import bisect_left
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.utility.nif_global import NifOp

### TODO [animation/util] interpolate() should perhaps be moved to utils?
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


def create_fcurves(action, dtype, drange, bonename = None):
    """
    Create fcurves in action for desired conditions.
    """
    # armature pose bone animation
    if bonename:
        return [action.fcurves.new(data_path = 'pose.bones["'+bonename+'"].'+dtype, index = i, action_group = bonename) for i in drange]
    else:
        # Object animation (non-skeletal)
        # any() is intended here, as the fcurve should be lumped into the "LocRotScale" action_group if it is any of the given subtypes. It can never be all at once.
        # nb. "rotation" catches both rotation_euler and rotation_quaternion
        if any(subtype in dtype for subtype in ("rotation", "location", "scale")):
            action_group = "LocRotScale"
        # Non-transformaing animations (eg. visibility or material anims) use no action groups
        else:
            action_group = ""
        return [action.fcurves.new(data_path = dtype, index = i, action_group = action_group) for i in drange]
        
    
def get_interp_mode(kf_element, ):
    """
    Get an appropriate interpolation mode for blender's fcurves from the KF interpolation mode
    """
    
    ### TODO [animation] join / make compatible with get_b_interp_from_n_interp?
    
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
        #set a dummy here, update via set_frames_per_second
        self.fps = 30
    
    def get_b_interp_from_n_interp(self, n_ipol):
        if n_ipol == NifFormat.KeyType.LINEAR_KEY:
            return "LINEAR"
        elif n_ipol == NifFormat.KeyType.QUADRATIC_KEY:
            return "BEZIER"
        elif n_ipol == 0:
            # guessing, not documented in nif.xml
            return "CONSTANT"
        NifLog.warn("Unsupported interpolation mode ({0}) in nif, using quadratic/bezier.".format(n_ipol))
        return "BEZIER"
        
    def create_action(self, b_obj, action_name):
        #could probably skip this test and create always
        if not b_obj.animation_data:
            b_obj.animation_data_create()
        if action_name in bpy.data.actions:
            b_action = bpy.data.actions[action_name]
        else:
            b_action = bpy.data.actions.new( action_name )
        #set as active action on object
        b_obj.animation_data.action = b_action
        return b_action
    
    # TODO [animation]: Is there a better way to this than return a string,
    #                   since handling requires different code per type?
    def get_extend_from_flags(self, flags):
        if flags & 6 == 4: # 0b100
            return "CONST"
        elif flags & 6 == 0: # 0b000
            return "CYCLIC"

        NifLog.warn("Unsupported cycle mode in nif, using clamped.")
        return "CONST"
    
    def set_extrapolation(self, flags, fcurves):
        f_curve_extend_type = self.get_extend_from_flags(flags)
        if f_curve_extend_type == "CONST":
            for fcurve in fcurves:
                fcurve.extrapolation = 'CONSTANT'
        elif f_curve_extend_type == "CYCLIC":
            for fcurve in fcurves:
                fcurve.modifiers.new('CYCLES')
        else:
            for fcurve in fcurves:
                fcurve.extrapolation = 'CONSTANT'
    
    
    def add_key(self, fcurves, t, key, interp):
        """
        Add a key (len=n) to a set of fcurves (len=n) at the given frame. Set the key's interpolation to interp.
        """
        frame = round(t * self.fps)
        for fcurve, k in zip(fcurves, key):
            fcurve.keyframe_points.insert(frame, k).interpolation = interp
        
    def import_kf_standalone(self, kf_root, b_armature_obj, bind_data):
        """
        Import a kf animation. Needs a suitable armature in blender scene.
        """

        NifLog.info("Importing KF tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise nif_utils.NifError("non-Oblivion .kf import not supported")

        # import text keys
        self.import_text_keys(kf_root)
        
        self.create_action(b_armature_obj, kf_root.name.decode() )
        # go over all controlled blocks (NiKeyframeController)
        for controlledblock in kf_root.controlled_blocks:
            # nb: this yielded just an empty bytestring
            # nodename = controlledblock.get_node_name()
            kfc = controlledblock.controller
            bone_name = armature.get_bone_name_for_blender( controlledblock.target_name )
            if bone_name in bind_data:
                niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans = bind_data[bone_name]
                self.armature_animation.import_keyframe_controller(kfc, b_armature_obj, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans)
    
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
            for uvdata in root.tree(block_type=NifFormat.NiUVData):
                for uvgroup in uvdata.uv_groups:
                    key_times.extend(key.time for key in uvgroup.keys)
        fps = self.fps
        # not animated, return a reasonable default
        if not key_times:
            return
        # calculate FPS
        key_times = sorted(set(key_times))
        lowest_diff = sum(abs(int(time * fps + 0.5) - (time * fps))
                          for time in key_times)
        # for test_fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 24, 25, 35]:
            diff = sum(abs(int(time * test_fps + 0.5)-(time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        NifLog.info("Animation estimated at %i frames per second." % fps)
        self.fps = fps
        bpy.context.scene.render.fps = fps
        bpy.context.scene.frame_set(0)
    
    def import_object_animation(self, niBlock, b_obj):
        """
        Load animation attached to (Scene Root) object.
        Becomes the object level animation of the object.
        """
        
        # TODO: remove code duplication with import_keyframe_controller
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

        #get the interpolation modes
        interp_rot = get_interp_mode(kfd)
        interp_loc = get_interp_mode(kfd.translations)
        interp_scale = get_interp_mode(kfd.scales)
        
        b_obj_action = self.create_action(b_obj, b_obj.name + "-Anim" )

        if kfd.scales.keys:
            NifLog.debug('Scale keys...')
            fcurves = create_fcurves(b_obj_action, "scale", range(3))
            for key in kfd.scales.keys:
                v = (key.value, key.value, key.value)
                self.add_key(fcurves, key.time, v, interp_scale)
            
        # detect the type of rotation keys
        if kfd.rotation_type == 4:
            NifLog.debug('Rotation keys...(eulers)')
            b_obj.rotation_mode = "XYZ"
            #Eulers are a bit different here, we can import them regardless of their timing
            #because they need no correction math in object space
            fcurves = create_fcurves(b_obj_action, "rotation_euler", range(3))
            keys = (kfd.xyz_rotations[0].keys, kfd.xyz_rotations[1].keys, kfd.xyz_rotations[2].keys)
            for fcu, keys_dim in zip(fcurves, keys):
                for key in keys_dim:
                    self.add_key((fcu, ), key.time, (key.value,), interp_rot)
        # uses quaternions
        elif kfd.quaternion_keys:
            NifLog.debug('Rotation keys...(quaternions)')
            b_obj.rotation_mode = "QUATERNION"
            fcurves = create_fcurves(b_obj_action, "rotation_quaternion", range(4))
            for key in kfd.quaternion_keys:
                v = (key.value.w, key.value.x, key.value.y, key.value.z)
                self.add_key(fcurves, key.time, v, interp_rot)

        if kfd.translations.keys:
            NifLog.debug('Translation keys...')
            fcurves = create_fcurves(b_obj_action, "location", range(3))
            for key in kfd.translations.keys:
                v = (key.value.x, key.value.y, key.value.z)
                self.add_key(fcurves, key.time, v, interp_rot)

class ObjectAnimation():
    
    def __init__(self, parent):
        self.nif_import = parent
     
    def import_object_vis_controller(self, n_node, b_obj ):
        """Import vis controller for blender object."""
        
        n_vis_ctrl = nif_utils.find_controller(n_node, NifFormat.NiVisController)
        if not(n_vis_ctrl and n_vis_ctrl.data):
            return
        NifLog.info("Importing vis controller")
        
        b_obj_action = self.nif_import.animationhelper.create_action( b_obj, b_obj.name + "-Anim")

        fcurves = create_fcurves(b_obj_action, "hide", (0,))
        for key in n_vis_ctrl.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value, ), "CONSTANT")
        #get extrapolation from flags and set it to fcurves
        self.nif_import.animationhelper.set_extrapolation(n_vis_ctrl.flags, fcurves)

    def import_mesh_controllers(self, n_node, b_obj ):
        """Import mesh controller for blender object."""
        
        morphCtrl = nif_utils.find_controller(n_node, NifFormat.NiGeomMorpherController)
        if morphCtrl:
            b_mesh = b_obj.data
            morphData = morphCtrl.data
            if morphData.num_morphs:
                fps = bpy.context.scene.render.fps
                # insert base key at frame 1, using relative keys
                b_mesh.insertKey(1, 'relative')
                # get name for base key
                keyname = morphData.morphs[0].frame_name
                if not keyname:
                    keyname = 'Base'
                # set name for base key
                b_mesh.key.blocks[0].name = keyname
                # get base vectors and import all morphs
                baseverts = morphData.morphs[0].vectors
                b_ipo = Blender.Ipo.New('Key' , 'KeyIpo')
                b_mesh.key.ipo = b_ipo
                for idxMorph in range(1, morphData.num_morphs):
                    # get name for key
                    keyname = morphData.morphs[idxMorph].frame_name
                    if not keyname:
                        keyname = 'Key %i' % idxMorph
                    NifLog.info("Inserting key '{0}'".format(keyname))
                    # get vectors
                    morphverts = morphData.morphs[idxMorph].vectors
                    # for each vertex calculate the key position from base
                    # pos + delta offset
                    assert(len(baseverts) == len(morphverts) == len(v_map))
                    for bv, mv, b_v_index in zip(baseverts, morphverts, v_map):
                        base = mathutils.Vector(bv.x, bv.y, bv.z)
                        delta = mathutils.Vector(mv.x, mv.y, mv.z)
                        v = base + delta
                        if applytransform:
                            v *= transform
                        b_mesh.vertices[b_v_index].co[0] = v.x
                        b_mesh.vertices[b_v_index].co[1] = v.y
                        b_mesh.vertices[b_v_index].co[2] = v.z
                    # update the mesh and insert key
                    b_mesh.insertKey(idxMorph, 'relative')
                    # set name for key
                    b_mesh.key.blocks[idxMorph].name = keyname
                    # set up the ipo key curve
                    try:
                        b_curve = b_ipo.addCurve(keyname)
                    except ValueError:
                        # this happens when two keys have the same name
                        # an instance of this is in fallout 3
                        # meshes/characters/_male/skeleton.nif HeadAnims:0
                        NifLog.warn("Skipped duplicate of key '{0}'".format(keyname))
                    # no idea how to set up the bezier triples -> switching
                    # to linear instead
                    b_curve.interpolation = Blender.IpoCurve.InterpTypes.LINEAR
                    # select extrapolation
                    b_curve.extend = self.get_extend_from_flags(morphCtrl.flags)
                    # set up the curve's control points
                    # first find the keys
                    # older versions store keys in the morphData
                    morphkeys = morphData.morphs[idxMorph].keys
                    # newer versions store keys in the controller
                    if (not morphkeys) and morphCtrl.interpolators:
                        morphkeys = morphCtrl.interpolators[idxMorph].data.data.keys
                    for key in morphkeys:
                        x = key.value
                        frame = 1 + int(key.time * fps + 0.5)
                        b_curve.addBezier((frame, x))
                    # finally: return to base position
                    for bv, b_v_index in zip(baseverts, v_map):
                        base = mathutils.Vector(bv.x, bv.y, bv.z)
                        if applytransform:
                            base *= transform
                        b_mesh.vertices[b_v_index].co[0] = base.x
                        b_mesh.vertices[b_v_index].co[1] = base.y
                        b_mesh.vertices[b_v_index].co[2] = base.z
    
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
            b_channel="niftools.ambient_color",
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.import_material_color_controller(
            b_material=b_material,
            b_channel="diffuse_color",
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.import_material_color_controller(
            b_material=b_material,
            b_channel="specular_color",
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
        
        b_mat_action = self.nif_import.animationhelper.create_action( b_material, "MaterialAction")
        fcurves = create_fcurves(b_mat_action, "alpha", (0,))
        interp = self.nif_import.animationhelper.get_b_interp_from_n_interp( n_alphactrl.data.data.interpolation)
        self.nif_import.animationhelper.set_extrapolation(n_alphactrl.flags, fcurves)
        for key in n_alphactrl.data.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value, ), interp)

    def import_material_color_controller(
        self, b_material, b_channel, n_geom, n_target_color):
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
        NifLog.info("Importing material color controller for target color {0} into blender channel {0}".format(n_target_color, b_channel))
        # import data as curves
        b_mat_action = self.nif_import.animationhelper.create_action( b_material, "MaterialAction")
        
        fcurves = create_fcurves(b_mat_action, b_channel, range(3))
        interp = self.nif_import.animationhelper.get_b_interp_from_n_interp( n_matcolor_ctrl.data.data.interpolation)
        self.nif_import.animationhelper.set_extrapolation(n_matcolor_ctrl.flags, fcurves)
        for key in n_matcolor_ctrl.data.data.keys:
            self.nif_import.animationhelper.add_key(fcurves, key.time, key.value.as_list(), interp)

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom,
                                      NifFormat.NiUVController)
        if not(n_ctrl and n_ctrl.data):
            return
        NifLog.info("Importing UV controller")
        
        b_mat_action = self.nif_import.animationhelper.create_action( b_material, "MaterialAction")
        
        dtypes = ("offset", 0), ("offset", 1), ("scale", 0), ("scale", 1)
        for n_uvgroup, (data_path, array_ind) in zip(n_ctrl.data.uv_groups, dtypes):
            if n_uvgroup.keys:
                interp = self.nif_import.animationhelper.get_b_interp_from_n_interp( n_uvgroup.interpolation )
                #in blender, UV offset is stored per texture slot
                #so we have to repeat the import for each used tex slot
                for i, texture_slot in enumerate(b_material.texture_slots):
                    if texture_slot:
                        fcurves = create_fcurves(b_mat_action, "texture_slots["+str(i)+"]."+data_path, (array_ind,) )
                        for key in n_uvgroup.keys:
                            if "offset" in data_path:
                                self.nif_import.animationhelper.add_key(fcurves, key.time, (-key.value, ), interp)
                            else:
                                self.nif_import.animationhelper.add_key(fcurves, key.time, (key.value, ), interp)
                        self.nif_import.animationhelper.set_extrapolation( n_ctrl.flags, fcurves)
                            

class ArmatureAnimation():
    
    def __init__(self, parent):
        self.nif_import = parent
    
    def import_keyframe_controller(self, kfc, b_armature_obj, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans):
        if kfc:
            b_action = b_armature_obj.animation_data.action
            # old style: data directly on controller
            kfd = kfc.data
            # new style: data via interpolator
            kfi = kfc.interpolator
            
            translations = []
            scales = []
            rotations = []
            eulers = []

            #TODO: test interpolators
            # B-spline curve import
            if isinstance(kfi, NifFormat.NiBSplineInterpolator):
                times = list(kfi.get_times())
                
                translations = zip( times, list(kfi.get_translations()) )
                scales = zip( times, list(kfi.get_scales()) )
                rotations = zip( times, list(kfi.get_rotations()) )
                
                #TODO: get these from interpolator?
                interp_rot = "LINEAR"
                interp_loc = "LINEAR"
                interp_scale = "LINEAR"
                return
            # next is a quick hack to make the new transform
            # interpolator work as if it is an old style keyframe data
            # block parented directly on the controller
            if isinstance(kfi, NifFormat.NiTransformInterpolator):
                kfd = kfi.data
                # for now, in this case, ignore interpolator
                kfi = None
            if isinstance(kfd, NifFormat.NiKeyframeData):
                interp_rot = get_interp_mode(kfd)
                interp_loc = get_interp_mode(kfd.translations)
                interp_scale = get_interp_mode(kfd.scales)
                if kfd.rotation_type == 4:
                    b_armature_obj.pose.bones[bone_name].rotation_mode = "XYZ"
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
                    
            if eulers:
                NifLog.debug('Rotation keys...(euler)')
                fcurves = create_fcurves(b_action, "rotation_euler", range(3), bone_name)
                for t, val in eulers:
                    euler = mathutils.Euler( val )
                    key = armature.import_keymat(niBone_bind_rot_inv, euler.to_matrix().to_4x4() ).to_euler()
                    self.nif_import.animationhelper.add_key(fcurves, t, key, interp_rot)
            elif rotations:
                NifLog.debug('Rotation keys...(quaternions)')
                fcurves = create_fcurves(b_action, "rotation_quaternion", range(4), bone_name)
                for t, val in rotations:
                    quat = mathutils.Quaternion([val.w, val.x, val.y, val.z])
                    key = armature.import_keymat(niBone_bind_rot_inv, quat.to_matrix().to_4x4() ).to_quaternion()
                    self.nif_import.animationhelper.add_key(fcurves, t, key, interp_rot)
            
            if scales:
                NifLog.debug('Scale keys...')
                fcurves = create_fcurves(b_action, "scale", range(3), bone_name)
                for t, val in scales:
                    key = (val, val, val)
                    self.nif_import.animationhelper.add_key(fcurves, t, key, interp_scale)
                        
            if translations:
                NifLog.debug('Translation keys...')
                fcurves = create_fcurves(b_action, "location", range(3), bone_name)
                for t, val in translations:
                    vec = mathutils.Vector([val.x, val.y, val.z])
                    key = armature.import_keymat(niBone_bind_rot_inv, mathutils.Matrix.Translation(vec - niBone_bind_trans)).to_translation()
                    self.nif_import.animationhelper.add_key(fcurves, t, key, interp_loc)
            #get extrapolation from kfc and set it to fcurves
            if any( (eulers, rotations, scales, translations) ):
                self.nif_import.animationhelper.set_extrapolation(kfc.flags, b_action.groups[bone_name].channels)
           
    def import_bone_animation(self, n_block, b_armature_obj, bone_name):
        """
        Imports an animation contained in the NIF itself.
        """
        if NifOp.props.animation:
            NifLog.debug('Importing animation for bone %s'.format(bone_name))

            bone_bm = nif_utils.import_matrix(n_block) # base pose
            niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = nif_utils.decompose_srt(bone_bm)
            niBone_bind_rot_inv = niBone_bind_rot.to_4x4().inverted()
            kfc = nif_utils.find_controller(n_block, NifFormat.NiKeyframeController)
                                       
            self.import_keyframe_controller(kfc, b_armature_obj, bone_name, niBone_bind_scale, niBone_bind_rot_inv, niBone_bind_trans)