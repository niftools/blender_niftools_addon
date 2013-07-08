"""This script contains classes to help import animations."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

import io_scene_nif.utility.nif_utils

class AnimationHelper():
    
    def __init__(self, parent):
        self.nif_common = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
    
    

    def import_kf_root(self, kf_root, root):
        """Merge kf into nif.

        *** Note: this function will eventually move to PyFFI. ***
        """

        self.info("Merging kf tree into nif tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise NifImportError("non-Oblivion .kf import not supported")

        # import text keys
        self.import_text_keys(kf_root)


        # go over all controlled blocks
        for controlledblock in kf_root.controlled_blocks:
            # get the name
            nodename = controlledblock.get_node_name()
            # match from nif tree?
            node = root.find(block_name = nodename)
            if not node:
                self.info(
                    "Animation for %s but no such node found in nif tree"
                    % nodename)
                continue
            # node found, now find the controller
            controllertype = controlledblock.get_controller_type()
            if not controllertype:
                self.info(
                    "Animation for %s without controller type, so skipping"
                    % nodename)
                continue
            controller = nif_utils.find_controller(node, getattr(NifFormat, controllertype))
            if not controller:
                self.info(
                    "Animation for %s with %s controller,"
                    " but no such controller type found"
                    " in corresponding node, so creating one"
                    % (nodename, controllertype))
                controller = getattr(NifFormat, controllertype)()
                # TODO set all the fields of this controller
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
                    self.nif_common.warning("ignored NaN in interpolator translation")
                else:
                    kfd.translations.num_keys = 1
                    kfd.translations.keys.update_size()
                    kfd.translations.keys[0].time = 0.0
                    kfd.translations.keys[0].value.x = kfi.translation.x
                    kfd.translations.keys[0].value.y = kfi.translation.y
                    kfd.translations.keys[0].value.z = kfi.translation.z
                # ignore scale, usually contains invalid data in interpolator

            # save priority for future reference
            # (priorities will be stored into the name of a NULL constraint on
            # bones, see import_armature function)
            self.nif_common.bone_priorities[nodename] = controlledblock.priority

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
            # TODO git rid of try-except block here
            try:
                bpy.data.texts["Anim"]
                animtxt.clear()
            except KeyError:
                animtxt = bpy.data.texts.new("Anim")

            frame = 1
            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = 1 + int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                animtxt.write('%i/%s\n'%(frame, newkey))

            # set start and end frames
            self.nif_common.context.scene.getRenderingContext().startFrame(1)
            self.nif_common.context.scene.getRenderingContext().endFrame(frame)

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
        # for fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 25, 35]:
            diff = sum(abs(int(time * test_fps + 0.5)-(time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        self.nif_common.info("Animation estimated at %i frames per second." % fps)
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
        self.nif_common.info("Animation")
        self.nif_common.info("Importing animation data for %s" % b_obj.name)
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        # create an Ipo for this object
        b_ipo = ObjectAnimation.get_object_ipo(b_obj)
        # get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys
        self.nif_common.debug('Scale keys...')
        for key in scales.keys:
            frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.SizeX = key.value
            b_obj.SizeY = key.value
            b_obj.SizeZ = key.value
            b_obj.insertIpoKey(Blender.Object.SIZE)

        # detect the type of rotation keys
        rotation_type = kfd.rotation_type
        if rotation_type == 4:
            # uses xyz rotation
            xkeys = kfd.xyz_rotations[0].keys
            ykeys = kfd.xyz_rotations[1].keys
            zkeys = kfd.xyz_rotations[2].keys
            self.nif_common.debug('Rotation keys...(euler)')
            for (xkey, ykey, zkey) in zip(xkeys, ykeys, zkeys):
                frame = 1+int(xkey.time * self.fps + 0.5) # time 0.0 is frame 1
                # XXX we assume xkey.time == ykey.time == zkey.time
                Blender.Set('curframe', frame)
                # both in radians, no conversion needed
                b_obj.RotX = xkey.value
                b_obj.RotY = ykey.value
                b_obj.RotZ = zkey.value
                b_obj.insertIpoKey(Blender.Object.ROT)
        else:
            # uses quaternions
            if kfd.quaternion_keys:
                self.nif_common.debug('Rotation keys...(quaternions)')
            for key in kfd.quaternion_keys:
                frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                rot = mathutils.Quaternion(key.value.w, key.value.x, key.value.y, key.value.z).toEuler()
                # Blender euler is in degrees, object RotXYZ is in radians
                b_obj.RotX = rot.x * self.D2R
                b_obj.RotY = rot.y * self.D2R
                b_obj.RotZ = rot.z * self.D2R
                b_obj.insertIpoKey(Blender.Object.ROT)

        if translations.keys:
            self.nif_common.debug('Translation keys...')
        for key in translations.keys:
            frame = 1+int(key.time * self.nif_common.fps + 0.5) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.LocX = key.value.x
            b_obj.LocY = key.value.y
            b_obj.LocZ = key.value.z
            b_obj.insertIpoKey(Blender.Object.LOC)

        Blender.Set('curframe', 1)


class ObjectAnimation():
    
    def __init__(self, parent):
        self.nif_common = parent
    
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
        self.info("importing vis controller")
        b_channel = "Layer"
        b_ipo = self.get_object_ipo(b_object)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = Blender.IpoCurve.InterpTypes.CONST
        b_curve.extend = self.nif_common.get_extend_from_flags(n_vis_ctrl.flags)
        for n_key in n_vis_ctrl.data.keys:
            b_curve[1 + n_key.time * self.fps] = (
                2 ** (n_key.value + max([1] + self.nif_common.context.scene.getLayers()) - 1))

class MaterialAnimation():
    
    def __init__(self, parent):
        self.nif_common = parent
    
    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not self.nif_common.properties.animation:
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
        self.nif_common.info("importing alpha controller")
        b_channel = "Alpha"
        b_ipo = self.get_material_ipo(b_material)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = self.nif_common.get_b_ipol_from_n_ipol(
            n_alphactrl.data.data.interpolation)
        b_curve.extend = self.nif_common.get_extend_from_flags(n_alphactrl.flags)
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
        self.info(
            "importing material color controller for target color %s"
            " into blender channels %s"
            % (n_target_color, b_channels))
        # import data as curves
        b_ipo = self.get_material_ipo(b_material)
        for i, b_channel in enumerate(b_channels):
            b_curve = b_ipo.addCurve(b_channel)
            b_curve.interpolation = self.nif_common.get_b_ipol_from_n_ipol(
                n_matcolor_ctrl.data.data.interpolation)
            b_curve.extend = self.nif_common.get_extend_from_flags(n_matcolor_ctrl.flags)
            for n_key in n_matcolor_ctrl.data.data.keys:
                b_curve[1 + n_key.time * self.fps] = n_key.value.as_list()[i]

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom,
                                      NifFormat.NiUVController)
        if not(n_ctrl and n_ctrl.data):
            return
        self.info("importing UV controller")
        b_channels = ("OfsX", "OfsY", "SizeX", "SizeY")
        for b_channel, n_uvgroup in zip(b_channels,
                                        n_ctrl.data.uv_groups):
            if n_uvgroup.keys:
                # create curve in material ipo
                b_ipo = self.get_material_ipo(b_material)
                b_curve = b_ipo.addCurve(b_channel)
                b_curve.interpolation = self.nif_common.get_b_ipol_from_n_ipol(
                    n_uvgroup.interpolation)
                b_curve.extend = self.nif_common.get_extend_from_flags(n_ctrl.flags)
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
