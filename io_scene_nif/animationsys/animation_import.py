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
from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils


class AnimationHelper():

    def __init__(self, parent):
        self.nif_import = parent
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.armature_animation = ArmatureAnimation(parent)

    def import_kf_root(self, kf_root, root):
        """Merge kf into nif.

        *** Note: this function will eventually move to PyFFI. ***
        """

        self.info("Merging kf tree into nif tree")

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
            node = root.find(block_name=nodename)
            if not node:
                self.info("Animation for %s but no such node found in nif tree"
                          % nodename
                          )
                continue
            # node found, now find the controller
            controllertype = controlledblock.get_controller_type()
            if not controllertype:
                self.info("Animation for %s without controller type, so skipping"
                          % nodename
                          )
                continue
            controller = nif_utils.find_controller(node, getattr(NifFormat, controllertype))
            if not controller:
                self.info("Animation for %s with %s controller, but no such controller type found in corresponding node, so creating one"
                          % (nodename, controllertype)
                          )
                controller = getattr(NifFormat, controllertype)()
                # TODO: set all the fields of this controller
                node.add_controller(controller)
            # yes! attach interpolator
            controller.interpolator = controlledblock.interpolator
            # in case of a NiTransformInterpolator without a data block
            # we still must re-export the interpolator for Oblivion to
            # accept the file
            # so simply add dummy keyframe data for this one with just a single
            # key to flag the exporter to export the keyframe as interpolator
            # (i.e. length 1 keyframes are simply interpolators)
            if isinstance(controller.interpolator, NifFormat.NiTransformInterpolator) and controller.interpolator.data is None:
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
                    self.nif_import.warning("ignored NaN in interpolator translation")
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
            self.nif_import.dict_bone_priorities[nodename] = controlledblock.priority

        # DEBUG: save the file for manual inspection
        # niffile = open("C:\\test.nif", "wb")
        # NifFormat.write(niffile,
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
            # TODO: git rid of try-except block here
            try:
                bpy.data.texts["Anim"]
                animtxt.clear()
            except KeyError:
                animtxt = bpy.data.texts.new("Anim")

            frame = 1
            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = 1 + int(key.time * self.fps + 0.5)  # time 0.0 is frame 1
                animtxt.write('%i/%s\n' % (frame, newkey))

            # set start and end frames
            self.nif_import.context.scene.getRenderingContext().startFrame(1)
            self.nif_import.context.scene.getRenderingContext().endFrame(frame)

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
                    point * (kfi.stop_time - kfi.start_time) / (kfi.basis_data.num_control_points - 2)
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
            diff = sum(abs(int(time * test_fps + 0.5) - (time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        self.nif_import.info("Animation estimated at %i frames per second."
                             % fps
                             )
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
                kfd = None  # not supported yet so avoids fatal error - should be kfc.interpolator.spline_data when spline data is figured out.
            else:
                kfd = kfc.interpolator.data
        else:
            kfd = kfc.data

        if not kfd:
            # no animation data: do nothing
            return

        # denote progress
        self.nif_import.info("Animation")
        self.nif_import.info("Importing animation data for %s"
                             % b_obj.name
                             )
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        # create an Ipo for this object
        b_ipo = ObjectAnimation.get_object_ipo(b_obj)
        # get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys
        self.nif_import.debug('Scale keys...')
        for key in scales.keys:
            frame = 1 + int(key.time * self.fps + 0.5)  # time 0.0 is frame 1
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
            self.nif_import.debug('Rotation keys...(euler)')
            for (xkey, ykey, zkey) in zip(xkeys, ykeys, zkeys):
                frame = 1 + int(xkey.time * self.fps + 0.5)  # time 0.0 is frame 1
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
                self.nif_import.debug('Rotation keys...(quaternions)')
            for key in kfd.quaternion_keys:
                frame = 1 + int(key.time * self.fps + 0.5)  # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                rot = mathutils.Quaternion(key.value.w, key.value.x, key.value.y, key.value.z).toEuler()
                # Blender euler is in degrees, object RotXYZ is in radians
                b_obj.RotX = rot.x * self.D2R
                b_obj.RotY = rot.y * self.D2R
                b_obj.RotZ = rot.z * self.D2R
                b_obj.insertIpoKey(Blender.Object.ROT)

        if translations.keys:
            self.nif_import.debug('Translation keys...')
        for key in translations.keys:
            frame = 1 + int(key.time * self.nif_import.fps + 0.5)  # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.LocX = key.value.x
            b_obj.LocY = key.value.y
            b_obj.LocZ = key.value.z
            b_obj.insertIpoKey(Blender.Object.LOC)

        Blender.Set('curframe', 1)


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
        self.info("importing vis controller")
        b_channel = "Layer"
        b_ipo = self.get_object_ipo(b_object)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = Blender.IpoCurve.InterpTypes.CONST
        b_curve.extend = self.nif_import.get_extend_from_flags(n_vis_ctrl.flags)
        for n_key in n_vis_ctrl.data.keys:
            b_curve[1 + n_key.time * self.fps] = (
                2 ** (n_key.value + max([1] + self.nif_import.context.scene.getLayers()) - 1))


class MaterialAnimation():

    def __init__(self, parent):
        self.nif_import = parent

    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not self.nif_import.properties.animation:
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
        n_alphactrl = nif_utils.find_controller(n_matprop, NifFormat.NiAlphaController)
        if not(n_alphactrl and n_alphactrl.data):
            return
        self.nif_import.info("importing alpha controller")
        b_channel = "Alpha"
        b_ipo = self.get_material_ipo(b_material)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = self.nif_import.get_b_ipol_from_n_ipol(
            n_alphactrl.data.data.interpolation)
        b_curve.extend = self.nif_import.get_extend_from_flags(n_alphactrl.flags)
        for n_key in n_alphactrl.data.data.keys:
            b_curve[1 + n_key.time * self.fps] = n_key.value

    def import_material_color_controller(self, b_material, b_channels, n_geom, n_target_color):
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
        self.info("importing material color controller for target color %s into blender channels %s"
                  % (n_target_color, b_channels)
                  )
        # import data as curves
        b_ipo = self.get_material_ipo(b_material)
        for i, b_channel in enumerate(b_channels):
            b_curve = b_ipo.addCurve(b_channel)
            b_curve.interpolation = self.nif_import.get_b_ipol_from_n_ipol(
                n_matcolor_ctrl.data.data.interpolation)
            b_curve.extend = self.nif_import.get_extend_from_flags(n_matcolor_ctrl.flags)
            for n_key in n_matcolor_ctrl.data.data.keys:
                b_curve[1 + n_key.time * self.fps] = n_key.value.as_list()[i]

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = nif_utils.find_controller(n_geom, NifFormat.NiUVController)
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
                b_curve.interpolation = self.nif_import.get_b_ipol_from_n_ipol(
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

    def import_armature_animation(self, b_armature):
        # create an action
        action = bpy.data.actions.new(armature_name)
        bpy.types.NlaTrack.select = b_armature  # action.setActive(b_armature)
        # go through all armature pose bones
        # see http://www.elysiun.com/forum/viewtopic.php?t=58693
        self.nif_import.info('Importing Animations')
        for bone_name, b_posebone in b_armature.pose.bones.items():
            # denote progress
            self.nif_import.debug('Importing animation for bone %s'
                                  % bone_name
                                  )
            niBone = self.nif_import.dict_blocks[bone_name]

            # get bind matrix (NIF format stores full transformations in keyframes,
            # but Blender wants relative transformations, hence we need to know
            # the bind position for conversion). Since
            # [SRchannel 0]    [SRbind 0]   [SRchannel * SRbind         0]   [SRtotal 0]
            # [Tchannel  1] *  [Tbind  1] = [Tchannel  * SRbind + Tbind 1] = [Ttotal  1]
            # with
            # 'total' the transformations as stored in the NIF keyframes,
            # 'bind' the Blender bind pose, and
            # 'channel' the Blender IPO channel,
            # it follows that
            # Schannel = Stotal / Sbind
            # Rchannel = Rtotal * inverse(Rbind)
            # Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
            bone_bm = nif_utils.import_matrix(niBone)  # base pose
            niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = self.decompose_srt(bone_bm)
            niBone_bind_rot_inv = mathutils.Matrix(niBone_bind_rot)
            niBone_bind_rot_inv.invert()
            niBone_bind_quat_inv = niBone_bind_rot_inv.to_quaternion()
            # we also need the conversion of the original matrix to the
            # new bone matrix, say X,
            # B' = X * B
            # (with B' the Blender matrix and B the NIF matrix) because we
            # need that
            # C' * B' = X * C * B
            # and therefore
            # C' = X * C * B * inverse(B') = X * C * inverse(X),
            # where X = B' * inverse(B)
            #
            # In detail:
            # [SRX 0]   [SRC 0]            [SRX 0]
            # [TX  1] * [TC  1] * inverse( [TX  1] ) =
            # [SRX * SRC       0]   [inverse(SRX)         0]
            # [TX * SRC + TC   1] * [-TX * inverse(SRX)   1] =
            # [SRX * SRC * inverse(SRX)              0]
            # [(TX * SRC + TC - TX) * inverse(SRX)   1]
            # Hence
            # SC' = SX * SC / SX = SC
            # RC' = RX * RC * inverse(RX)
            # TC' = (TX * SC * RC + TC - TX) * inverse(RX) / SX
            extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = self.decompose_srt(self.nif_import.dict_bones_extra_matrix[niBone])
            extra_matrix_quat = extra_matrix_rot.to_quaternion()
            extra_matrix_rot_inv = mathutils.Matrix(extra_matrix_rot)
            extra_matrix_rot_inv.invert()
            extra_matrix_quat_inv = extra_matrix_rot_inv.to_quaternion()
            # now import everything
            # ##############################

            # get controller, interpolator, and data
            # note: the NiKeyframeController check also includes
            #       NiTransformController (see hierarchy!)
            kfc = nif_utils.find_controller(niBone, NifFormat.NiKeyframeController)
            # old style: data directly on controller
            kfd = kfc.data if kfc else None
            # new style: data via interpolator
            kfi = kfc.interpolator if kfc else None
            # next is a quick hack to make the new transform
            # interpolator work as if it is an old style keyframe data
            # block parented directly on the controller
            if isinstance(kfi, NifFormat.NiTransformInterpolator):
                kfd = kfi.data
                # for now, in this case, ignore interpolator
                kfi = None

            # B-spline curve import
            if isinstance(kfi, NifFormat.NiBSplineInterpolator):
                times = list(kfi.get_times())
                translations = list(kfi.get_translations())
                scales = list(kfi.get_scales())
                rotations = list(kfi.get_rotations())

                # if we have translation keys, we make a dictionary of
                # rot_keys and scale_keys, this makes the script work MUCH
                # faster in most cases
                if translations:
                    scale_keys_dict = {}
                    rot_keys_dict = {}

                # scales: ignore for now, implement later
                #         should come here
                scales = None

                # rotations
                if rotations:
                    self.nif_import.debug(
                        'Rotation keys...(bspline quaternions)')
                    for time, quat in zip(times, rotations):
                        frame = 1 + int(time * self.nif_import.fps + 0.5)
                        quat = mathutils.Quaternion(
                            [quat[0], quat[1], quat[2], quat[3]])
                        # beware, CrossQuats takes arguments in a
                        # counter-intuitive order:
                        # q1.to_matrix() * q2.to_matrix() == CrossQuats(q2, q1).to_matrix()
                        quatVal = CrossQuats(niBone_bind_quat_inv, quat)  # Rchannel = Rtotal * inverse(Rbind)
                        rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat)  # C' = X * C * inverse(X)
                        b_posebone.quat = rot
                        b_posebone.insertKey(b_armature, frame,
                                             [Blender.Object.Pose.ROT])
                        # fill optimizer dictionary
                        if translations:
                            rot_keys_dict[frame] = mathutils.Quaternion(rot)

                # translations
                if translations:
                    self.nif_import.debug('Translation keys...(bspline)')
                    for time, translation in zip(times, translations):
                        # time 0.0 is frame 1
                        frame = 1 + int(time * self.nif_import.fps + 0.5)
                        trans = mathutils.Vector(*translation)
                        locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (niBone_bind_scale)  # Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                        # the rotation matrix is needed at this frame (that's
                        # why the other keys are inserted first)
                        if rot_keys_dict:
                            try:
                                rot = rot_keys_dict[frame].to_matrix()
                            except KeyError:
                                # fall back on slow method
                                ipo = action.getChannelIpo(bone_name)
                                quat = mathutils.Quaternion()
                                quat.x = ipo.getCurve('QuatX').evaluate(frame)
                                quat.y = ipo.getCurve('QuatY').evaluate(frame)
                                quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                                quat.w = ipo.getCurve('QuatW').evaluate(frame)
                                rot = quat.to_matrix()
                        else:
                            rot = mathutils.Matrix([[1.0, 0.0, 0.0],
                                                    [0.0, 1.0, 0.0],
                                                    [0.0, 0.0, 1.0]])
                        # we also need the scale at this frame
                        if scale_keys_dict:
                            try:
                                sizeVal = scale_keys_dict[frame]
                            except KeyError:
                                ipo = action.getChannelIpo(bone_name)
                                if ipo.getCurve('SizeX'):
                                    sizeVal = ipo.getCurve('SizeX').evaluate(frame)  # assume uniform scale
                                else:
                                    sizeVal = 1.0
                        else:
                            sizeVal = 1.0
                        size = mathutils.Matrix([[sizeVal, 0.0, 0.0],
                                                 [0.0, sizeVal, 0.0],
                                                 [0.0, 0.0, sizeVal]])
                        # now we can do the final calculation
                        loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (extra_matrix_scale)  # C' = X * C * inverse(X)
                        b_posebone.loc = loc
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])

                # delete temporary dictionaries
                if translations:
                    del scale_keys_dict
                    del rot_keys_dict

            # NiKeyframeData and NiTransformData import
            elif isinstance(kfd, NifFormat.NiKeyframeData):

                translations = kfd.translations
                scales = kfd.scales
                # if we have translation keys, we make a dictionary of
                # rot_keys and scale_keys, this makes the script work MUCH
                # faster in most cases
                if translations:
                    scale_keys_dict = {}
                    rot_keys_dict = {}
                # add the keys

                # Scaling
                if scales.keys:
                    self.nif_import.debug('Scale keys...')
                for scaleKey in scales.keys:
                    # time 0.0 is frame 1
                    frame = 1 + int(scaleKey.time * self.nif_import.fps + 0.5)
                    sizeVal = scaleKey.value
                    size = sizeVal / niBone_bind_scale  # Schannel = Stotal / Sbind
                    b_posebone.size = mathutils.Vector(size, size, size)
                    b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE])  # this is very slow... :(
                    # fill optimizer dictionary
                    if translations:
                        scale_keys_dict[frame] = size

                # detect the type of rotation keys
                rotation_type = kfd.rotation_type

                # Euler Rotations
                if rotation_type == 4:
                    # uses xyz rotation
                    if kfd.xyz_rotations[0].keys:
                        self.nif_import.debug('Rotation keys...(euler)')
                    for xkey, ykey, zkey in zip(kfd.xyz_rotations[0].keys, kfd.xyz_rotations[1].keys, kfd.xyz_rotations[2].keys):
                        # time 0.0 is frame 1
                        # XXX it is assumed that all the keys have the
                        # XXX same times!!!
                        if (abs(xkey.time - ykey.time) > self.properties.epsilon or abs(xkey.time - zkey.time) > self.properties.epsilon):
                            self.nif_import.warning("xyz key times do not correspond, animation may not be correctly imported")
                        frame = 1 + int(xkey.time * self.nif_import.fps + 0.5)
                        euler = mathutils.Euler(
                            [xkey.value * 180.0 / math.pi,
                             ykey.value * 180.0 / math.pi,
                             zkey.value * 180.0 / math.pi])
                        quat = euler.toQuat()

                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.to_matrix() * q2.to_matrix() == CrossQuats(q2, q1).to_matrix()

                        quatVal = CrossQuats(niBone_bind_quat_inv, quat)  # Rchannel = Rtotal * inverse(Rbind)
                        rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat)  # C' = X * C * inverse(X)
                        b_posebone.quat = rot
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT])  # this is very slow... :(
                        # fill optimizer dictionary
                        if translations:
                            rot_keys_dict[frame] = mathutils.Quaternion(rot)

                # Quaternion Rotations
                else:
                    # TODO: take rotation type into account for interpolation
                    if kfd.quaternion_keys:
                        self.nif_import.debug('Rotation keys...(quaternions)')
                    quaternion_keys = kfd.quaternion_keys
                    for key in quaternion_keys:
                        frame = 1 + int(key.time * self.nif_import.fps + 0.5)
                        keyVal = key.value
                        quat = mathutils.Quaternion([keyVal.w, keyVal.x, keyVal.y, keyVal.z])
                        # beware, CrossQuats takes arguments in a
                        # counter-intuitive order:
                        # q1.to_matrix() * q2.to_matrix() == CrossQuats(q2, q1).to_matrix()
                        quatVal = CrossQuats(niBone_bind_quat_inv, quat)  # Rchannel = Rtotal * inverse(Rbind)
                        rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat)  # C' = X * C * inverse(X)
                        b_posebone.quat = rot
                        b_posebone.insertKey(b_armature, frame,
                                             [Blender.Object.Pose.ROT])
                        # fill optimizer dictionary
                        if translations:
                            rot_keys_dict[frame] = mathutils.Quaternion(rot)
                    # else:
                    #    print("Rotation keys...(unknown)" +
                    #          "WARNING: rotation animation data of type" +
                    #          " %i found, but this type is not yet supported; data has been skipped""" % rotation_type)

                # Translations
                if translations.keys:
                    self.nif_import.debug('Translation keys...')
                for key in translations.keys:
                    # time 0.0 is frame 1
                    frame = 1 + int(key.time * self.nif_import.fps + 0.5)
                    keyVal = key.value
                    trans = mathutils.Vector(keyVal.x, keyVal.y, keyVal.z)
                    locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (niBone_bind_scale)  # Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                    # the rotation matrix is needed at this frame (that's
                    # why the other keys are inserted first)
                    if rot_keys_dict:
                        try:
                            rot = rot_keys_dict[frame].to_matrix()
                        except KeyError:
                            # fall back on slow method
                            ipo = action.getChannelIpo(bone_name)
                            quat = mathutils.Quaternion()
                            quat.x = ipo.getCurve('QuatX').evaluate(frame)
                            quat.y = ipo.getCurve('QuatY').evaluate(frame)
                            quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                            quat.w = ipo.getCurve('QuatW').evaluate(frame)
                            rot = quat.to_matrix()
                    else:
                        rot = mathutils.Matrix([[1.0, 0.0, 0.0],
                                                [0.0, 1.0, 0.0],
                                                [0.0, 0.0, 1.0]])
                    # we also need the scale at this frame
                    if scale_keys_dict:
                        try:
                            sizeVal = scale_keys_dict[frame]
                        except KeyError:
                            ipo = action.getChannelIpo(bone_name)
                            if ipo.getCurve('SizeX'):
                                sizeVal = ipo.getCurve('SizeX').evaluate(frame)  # assume uniform scale
                            else:
                                sizeVal = 1.0
                    else:
                        sizeVal = 1.0
                    size = mathutils.Matrix([[sizeVal, 0.0, 0.0],
                                             [0.0, sizeVal, 0.0],
                                             [0.0, 0.0, sizeVal]])
                    # now we can do the final calculation
                    loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (extra_matrix_scale)  # C' = X * C * inverse(X)
                    b_posebone.loc = loc
                    b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
                if translations:
                    del scale_keys_dict
                    del rot_keys_dict
            # set extend mode for all ipo curves
            if kfc:
                try:
                    ipo = action.getChannelIpo(bone_name)
                except ValueError:
                    # no channel for bone_name
                    pass
                else:
                    for b_curve in ipo:
                        b_curve.extend = self.nif_import.get_extend_from_flags(kfc.flags)
