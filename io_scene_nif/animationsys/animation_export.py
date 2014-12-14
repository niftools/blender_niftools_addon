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

import bpy
import mathutils

from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils

class AnimationHelper():
    
    def __init__(self, parent):
        self.nif_export = parent
        self.properties = parent.properties
        self.context = parent.context
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
        self.texture_animation = TextureAnimation(parent)
    
    # Export the animation of blender action as keyframe controller and
    # keyframe data. Extra quaternion is multiplied prior to keyframe
    # rotation, and dito for translation. These extra fields come in handy
    # when exporting bone action's, which are relative to the rest pose, so
    # we can pass the rest pose through these extra transformations.
    #
    # bind_matrix is the original Blender bind matrix (the B' matrix below)
    # extra_mat_inv is the inverse matrix which transforms the Blender bone matrix
    # to the NIF bone matrix (the inverse of the X matrix below)
    #
    # Explanation of extra transformations:
    # Final transformation matrix is vec * Rchannel * Tchannel * Rbind * Tbind
    # So we export:
    # [ SRchannel 0 ]    [ SRbind 0 ]   [ SRchannel * SRbind        0 ]
    # [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel * SRbind + Tbind 1 ]
    # or, in detail,
    # Stotal = Schannel * Sbind
    # Rtotal = Rchannel * Rbind
    # Ttotal = Tchannel * Sbind * Rbind + Tbind
    # We also need the conversion of the new bone matrix to the original matrix, say X,
    # B' = X * B
    # (with B' the Blender matrix and B the NIF matrix) because we need that
    # C' * B' = X * C * B
    # and therefore
    # C * B = inverse(X) * C' * B'
    # (we need to write out C * B, the NIF format stores total transformation in keyframes).
    # In detail:
    #          [ SRX 0 ]     [ SRC' 0 ]   [ SRB' 0 ]
    # inverse( [ TX  1 ] ) * [ TC'  1 ] * [ TB'  1 ] =
    # [ inverse(SRX)         0 ]   [ SRC' * SRB'         0 ]
    # [ -TX * inverse(SRX)   1 ] * [ TC' * SRB' + TB'    1 ] =
    # [ inverse(SRX) * SRC' * SRB'                       0 ]
    # [ (-TX * inverse(SRX) * SRC' + TC') * SRB' + TB'    1 ]
    # Hence
    # S = SC' * SB' / SX
    # R = inverse(RX) * RC' * RB'
    # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
    #
    # Finally, note that
    # - TX * inverse(RX) / SX = translation part of inverse(X)
    # inverse(RX) = rotation part of inverse(X)
    # 1 / SX = scale part of inverse(X)
    # so having inverse(X) around saves on calculations
    
    def get_flags_from_extend(self, extend):
        if extend == bpy.types.actionCurve.ExtendTypes.CONST:
            return 4 # 0b100
        elif extend == bpy.types.actionCurve.ExtendTypes.CYCLIC:
            return 0

        self.nif_export.warning(
            "Unsupported extend type in blend, using clamped.")
        return 4
    
    def export_keyframes(self, action, space, parent_block, bind_matrix = None,
                     extra_mat_inv = None):
    
    
        if self.properties.animation == 'GEOM_NIF' and self.nif_export.version < 0x0A020000:
            # keyframe controllers are not present in geometry only files
            # for more recent versions, the controller and interpolators are
            # present, only the data is not present (see further on)
            return
    
        # only localspace keyframes need to be exported
        assert(space == 'localspace')
    
        # make sure the parent is of the right type
        assert(isinstance(parent_block, NifFormat.NiNode))
    
        # add a keyframecontroller block, and refer to this block in the
        # parent's time controller
        if self.nif_export.version < 0x0A020000:
            kfc = self.nif_export.objecthelper.create_block("NiKeyframeController", action)
        else:
            kfc = self.nif_export.objecthelper.create_block("NiTransformController", action)
            kfi = self.nif_export.objecthelper.create_block("NiTransformInterpolator", action)
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
        # this is stored in the blender action curves
        # while we're at it, we also determine the
        # start and stop frames
        extend = None
        if action:
            start_frame = +1000000
            stop_frame = -1000000
            for curve in action:
                # get cycle mode
                if extend is None:
                    extend = curve.extend
                elif extend != curve.extend:
                    self.nif_export.warning(
                        "Inconsistent extend type in %s, will use %s."
                        % (action, extend))
                # get start and stop frames
                start_frame = min(
                    start_frame,
                    min(btriple.pt[0] for btriple in curve.bezierPoints))
                stop_frame = max(
                    stop_frame,
                    max(btriple.pt[0] for btriple in curve.bezierPoints))
        else:
            # dummy action
            # default extend, start, and end
            extend = bpy.actionCurve.ExtendTypes.CYCLIC
            start_frame = self.context.scene.frame_start
            stop_frame = self.context.scene.frame_end
    
        # fill in the non-trivial values
        kfc.flags = 8 # active
        kfc.flags |= self.get_flags_from_extend(extend)
        kfc.frequency = 1.0
        kfc.phase = 0.0
        kfc.start_time = (start_frame - 1) * self.context.scene.render.fps
        kfc.stop_time = (stop_frame - 1) * self.context.scene.render.fps
    
        if self.properties.animation == 'GEOM_NIF':
            # keyframe data is not present in geometry files
            return
    
        # -> get keyframe information
    
        # some calculations
        if bind_matrix:
            bind_scale, bind_rot, bind_trans = nif_utils.decompose_srt(bind_matrix)
            bind_quat = bind_rot.toQuat()
        else:
            bind_scale = 1.0
            bind_rot = mathutils.Matrix([[1,0,0],[0,1,0],[0,0,1]])
            bind_quat = mathutils.Quaternion(1,0,0,0)
            bind_trans = mathutils.Vector()
        if extra_mat_inv:
            extra_scale_inv, extra_rot_inv, extra_trans_inv = \
                nif_utils.decompose_srt(extra_mat_inv)
            extra_quat_inv = extra_rot_inv.toQuat()
        else:
            extra_scale_inv = 1.0
            extra_rot_inv = mathutils.Matrix([[1,0,0],[0,1,0],[0,0,1]])
            extra_quat_inv = mathutils.Quaternion(1,0,0,0)
            extra_trans_inv = mathutils.Vector()
    
        # sometimes we need to export an empty keyframe... this will take care of that
        if (action == None):
            scale_curve = {}
            rot_curve = {}
            trans_curve = {}
        # the usual case comes now...
        else:
            # merge the animation curves into a rotation vector and translation vector curve
            scale_curve = {}
            rot_curve = {}
            trans_curve = {}
            # the following code makes these assumptions
            assert(action.PO_SCALEX == action.OB_SCALEX)
            assert(action.PO_LOCX == action.OB_LOCX)
            # check validity of curves
            for curvecollection in (
                (action.PO_SCALEX, action.PO_SCALEY, action.PO_SCALEZ),
                (action.PO_LOCX, action.PO_LOCY, action.PO_LOCZ),
                (action.PO_QUATX, action.PO_QUATY, action.PO_QUATZ, action.PO_QUATW),
                (action.OB_ROTX, action.OB_ROTY, action.OB_ROTZ)):
                # skip invalid curves
                try:
                    action[curvecollection[0]]
                except KeyError:
                    continue
                # check that if any curve is defined in the collection
                # then all curves are defined in the collection
                if (any(action[curve] for curve in curvecollection)
                    and not all(action[curve] for curve in curvecollection)):
                    keytype = {action.PO_SCALEX: "SCALE",
                               action.PO_LOCX: "LOC",
                               action.PO_QUATX: "ROT",
                               action.OB_ROTX: "ROT"}
                    raise nif_utils.NifError(
                        "missing curves in %s; insert %s key at frame 1"
                        " and try again"
                        % (action, keytype[curvecollection[0]]))
            # go over all curves
            action_curves = list(action.curveConsts.values())
            for curve in action_curves:
                # skip empty curves
                if action[curve] is None:
                    continue
                # non-empty curve: go over all frames of the curve
                for btriple in action[curve].bezierPoints:
                    frame = btriple.pt[0]
                    if (frame < self.context.scene.frame_start) or (frame > self.context.scene.frame_end):
                        continue
                    # PO_SCALEX == OB_SCALEX, so this does both pose and object
                    # scale
                    if curve in (action.PO_SCALEX, action.PO_SCALEY, action.PO_SCALEZ):
                        # support only uniform scaling... take the mean
                        scale_curve[frame] = (action[action.PO_SCALEX][frame]
                                              + action[action.PO_SCALEY][frame]
                                              + action[action.PO_SCALEZ][frame]) / 3.0
                        # SC' * SB' / SX
                        scale_curve[frame] = \
                            scale_curve[frame] * bind_scale * extra_scale_inv
                    # object rotation
                    elif curve in (action.OB_ROTX, action.OB_ROTY, action.OB_ROTZ):
                        rot_curve[frame] = mathutils.Euler(
                            [10 * action[action.OB_ROTX][frame],
                             10 * action[action.OB_ROTY][frame],
                             10 * action[action.OB_ROTZ][frame]])
                        # use quat if we have bind matrix and/or extra matrix
                        # XXX maybe we should just stick with eulers??
                        if bind_matrix or extra_mat_inv:
                            rot_curve[frame] = rot_curve[frame].toQuat()
                            # beware, CrossQuats takes arguments in a counter-intuitive order:
                            # q1.to_matrix() * q2.to_matrix() == CrossQuats(q2, q1).to_matrix()
                            rot_curve[frame] = mathutils.CrossQuats(mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # pose rotation
                    elif curve in (action.PO_QUATX, action.PO_QUATY,
                                   action.PO_QUATZ, action.PO_QUATW):
                        rot_curve[frame] = mathutils.Quaternion()
                        rot_curve[frame].x = action[action.PO_QUATX][frame]
                        rot_curve[frame].y = action[action.PO_QUATY][frame]
                        rot_curve[frame].z = action[action.PO_QUATZ][frame]
                        rot_curve[frame].w = action[action.PO_QUATW][frame]
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.to_matrix() * q2.to_matrix() == CrossQuats(q2, q1).to_matrix()
                        rot_curve[frame] = mathutils.CrossQuats(mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # PO_LOCX == OB_LOCX, so this does both pose and object
                    # location
                    elif curve in (action.PO_LOCX, action.PO_LOCY, action.PO_LOCZ):
                        trans_curve[frame] = mathutils.Vector(
                            [action[action.PO_LOCX][frame],
                             action[action.PO_LOCY][frame],
                             action[action.PO_LOCZ][frame]])
                        # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
                        trans_curve[frame] *= bind_scale
                        trans_curve[frame] *= bind_rot
                        trans_curve[frame] += bind_trans
                        # we need RC' and SC'
                        if action.OB_ROTX in action_curves and action[action.OB_ROTX]:
                            rot_c = mathutils.Euler(
                                [10 * action[action.OB_ROTX][frame],
                                 10 * action[action.OB_ROTY][frame],
                                 10 * action[action.OB_ROTZ][frame]]).to_matrix()
                        elif action.PO_QUATX in action_curves and action[action.PO_QUATX]:
                            rot_c = mathutils.Quaternion()
                            rot_c.x = action[action.PO_QUATX][frame]
                            rot_c.y = action[action.PO_QUATY][frame]
                            rot_c.z = action[action.PO_QUATZ][frame]
                            rot_c.w = action[action.PO_QUATW][frame]
                            rot_c = rot_c.to_matrix()
                        else:
                            rot_c = mathutils.Matrix([[1,0,0],[0,1,0],[0,0,1]])
                        # note, PO_SCALEX == OB_SCALEX, so this does both
                        if action[action.PO_SCALEX]:
                            # support only uniform scaling... take the mean
                            scale_c = (action[action.PO_SCALEX][frame]
                                       + action[action.PO_SCALEY][frame]
                                       + action[action.PO_SCALEZ][frame]) / 3.0
                        else:
                            scale_c = 1.0
                        trans_curve[frame] += \
                            extra_trans_inv * rot_c * bind_rot * \
                            scale_c * bind_scale
    
        # -> now comes the real export
    
        if (max(len(rot_curve), len(trans_curve), len(scale_curve)) <= 1
            and self.nif_export.version >= 0x0A020000):
            # only add data if number of keys is > 1
            # (see importer comments with import_kf_root: a single frame
            # keyframe denotes an interpolator without further data)
            # insufficient keys, so set the data and we're done!
            if trans_curve:
                trans = list(trans_curve.values())[0]
                kfi.translation.x = trans[0]
                kfi.translation.y = trans[1]
                kfi.translation.z = trans[2]
            if rot_curve:
                rot = list(rot_curve.values())[0]
                # XXX blender weirdness... Euler() is a function!!
                if isinstance(rot, mathutils.Euler().__class__):
                    rot = rot.toQuat()
                kfi.rotation.x = rot.x
                kfi.rotation.y = rot.y
                kfi.rotation.z = rot.z
                kfi.rotation.w = rot.w
            # ignore scale for now...
            kfi.scale = 1.0
            # done!
            return
    
        # add the keyframe data
        if self.nif_export.version < 0x0A020000:
            kfd = self.nif_export.objecthelper.create_block("NiKeyframeData", action)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.nif_export.objecthelper.create_block("NiTransformData", action)
            kfi.data = kfd
    
        frames = list(rot_curve.keys())
        frames.sort()
        # XXX blender weirdness... Euler() is a function!!
        if (frames
            and isinstance(list(rot_curve.values())[0],
                           mathutils.Euler().__class__)):
            # eulers
            kfd.rotation_type = NifFormat.KeyType.XYZ_ROTATION_KEY
            kfd.num_rotation_keys = 1 # *NOT* len(frames) this crashes the engine!
            kfd.xyz_rotations[0].num_keys = len(frames)
            kfd.xyz_rotations[1].num_keys = len(frames)
            kfd.xyz_rotations[2].num_keys = len(frames)
            # XXX todo: quadratic interpolation?
            kfd.xyz_rotations[0].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[1].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[2].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[0].keys.update_size()
            kfd.xyz_rotations[1].keys.update_size()
            kfd.xyz_rotations[2].keys.update_size()
            for i, frame in enumerate(frames):
                # XXX todo: speed up by not recalculating stuff
                rot_frame_x = kfd.xyz_rotations[0].keys[i]
                rot_frame_y = kfd.xyz_rotations[1].keys[i]
                rot_frame_z = kfd.xyz_rotations[2].keys[i]
                rot_frame_x.time = (frame - 1) * self.context.scene.render.fps
                rot_frame_y.time = (frame - 1) * self.context.scene.render.fps
                rot_frame_z.time = (frame - 1) * self.context.scene.render.fps
                rot_frame_x.value = rot_curve[frame].x * 3.14159265358979323846 / 180.0
                rot_frame_y.value = rot_curve[frame].y * 3.14159265358979323846 / 180.0
                rot_frame_z.value = rot_curve[frame].z * 3.14159265358979323846 / 180.0
        else:
            # quaternions
            # XXX todo: quadratic interpolation?
            kfd.rotation_type = NifFormat.KeyType.LINEAR_KEY
            kfd.num_rotation_keys = len(frames)
            kfd.quaternion_keys.update_size()
            for i, frame in enumerate(frames):
                rot_frame = kfd.quaternion_keys[i]
                rot_frame.time = (frame - 1) * self.context.scene.render.fps
                rot_frame.value.w = rot_curve[frame].w
                rot_frame.value.x = rot_curve[frame].x
                rot_frame.value.y = rot_curve[frame].y
                rot_frame.value.z = rot_curve[frame].z
    
        frames = list(trans_curve.keys())
        frames.sort()
        kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.translations.num_keys = len(frames)
        kfd.translations.keys.update_size()
        for i, frame in enumerate(frames):
            trans_frame = kfd.translations.keys[i]
            trans_frame.time = (frame - 1) * self.context.scene.render.fps
            trans_frame.value.x = trans_curve[frame][0]
            trans_frame.value.y = trans_curve[frame][1]
            trans_frame.value.z = trans_curve[frame][2]
    
        frames = list(scale_curve.keys())
        frames.sort()
        kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.scales.num_keys = len(frames)
        kfd.scales.keys.update_size()
        for i, frame in enumerate(frames):
            scale_frame = kfd.scales.keys[i]
            scale_frame.time = (frame - 1) * self.context.scene.render.fps
            scale_frame.value = scale_curve[frame]
            

    def export_anim_groups(self, animtxt, block_parent):
        """Parse the animation groups buffer and write an extra string
        data block, and attach it to an existing block (typically, the root
        of the nif tree)."""
        if self.properties.animation == 'GEOM_NIF':
            # animation group extra data is not present in geometry only files
            return

        self.nif_export.info("Exporting animation groups")
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
            if ((f < self.context.scene.frame_start) or (f > self.context.scene.frame_end)):
                self.warning("frame in animation buffer out of range "
                                 "(%i not in [%i, %i])"
                                 % (f, self.context.scene.frame_start, self.context.scene.frame_end))
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
            key.time = self.context.scene.render.fps * (flist[i]-1)
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
        flip.start_time = (self.context.scene.frame_start - 1) * self.context.scene.render.fps
        flip.stop_time = (self.context.scene.frame_end - self.context.scene.frame_start ) * self.context.scene.render.fps
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
        # XXX Blender.action channel constants are replaced by FCurve.data_path?
        return

        if self.properties.animation == 'GEOM_NIF':
            # geometry only: don't write controllers
            return

        self.export_material_alpha_controller(b_material, n_geom)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.action.MA_MIRR, Blender.action.MA_MIRG, Blender.action.MA_MIRB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.action.MA_R, Blender.action.MA_G, Blender.action.MA_B),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.action.MA_SPECR, Blender.action.MA_SPECG, Blender.action.MA_SPECB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_SPECULAR)
        self.export_material_uv_controller(b_material, n_geom)


    
    def export_material_alpha_controller(self, b_material, n_geom):
        """Export the material alpha controller data."""
        b_action = b_material.animation_data
        if not b_action:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_action[Blender.action.MA_ALPHA]
        if not b_curve:
            return
        n_floatdata = self.nif_export.objecthelper.create_block("NiFloatData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        n_floatdata.data.num_keys = len(b_curve.bezierPoints)
        n_floatdata.data.interpolation = self.get_n_actionl_from_b_actionl(
            b_curve.interpolation)
        n_floatdata.data.keys.update_size()
        for b_point, n_key in zip(b_curve.bezierPoints, n_floatdata.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_key.arg = n_floatdata.data.interpolation
            n_key.time = (b_time - 1) * self.context.scene.render.fps
            n_key.value = b_value
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_alphactrl = self.nif_export.objecthelper.create_block("NiAlphaController", b_action)
            n_alphaactionl = self.nif_export.objecthelper.create_block("NiFloatInterpolator", b_action)
            n_alphactrl.interpolator = n_alphaactionl
            n_alphactrl.flags = 8 # active
            n_alphactrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_alphactrl.frequency = 1.0
            n_alphactrl.start_time = min(n_times)
            n_alphactrl.stop_time = max(n_times)
            n_alphactrl.data = n_floatdata
            n_alphaactionl.data = n_floatdata
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
        b_action = b_material.animation_data
        if not b_action:
            return
        # get the material color curves and translate it into nif data
        b_curves = [b_action[b_channel] for b_channel in b_channels]
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
        n_posdata.data.interpolation = self.get_n_actionl_from_b_actionl(
            b_curves[0].interpolation)
        n_posdata.data.keys.update_size()
        for b_time, n_key in zip(sorted(b_times), n_posdata.data.keys):
            # add each point of the curves
            n_key.arg = n_posdata.data.interpolation
            n_key.time = (b_time - 1) * self.context.scene.render.fps
            n_key.value.x = b_curves[0][b_time]
            n_key.value.y = b_curves[1][b_time]
            n_key.value.z = b_curves[2][b_time]
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_matcolor_ctrl = self.nif_export.objecthelper.create_block(
                "NiMaterialColorController", b_action)
            n_matcolor_actionl = self.nif_export.objecthelper.create_block(
                "NiPoint3Interpolator", b_action)
            n_matcolor_ctrl.interpolator = n_matcolor_actionl
            n_matcolor_ctrl.flags = 8 # active
            n_matcolor_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_matcolor_ctrl.set_target_color(n_target_color)
            n_matcolor_ctrl.frequency = 1.0
            n_matcolor_ctrl.start_time = min(n_times)
            n_matcolor_ctrl.stop_time = max(n_times)
            n_matcolor_ctrl.data = n_posdata
            n_matcolor_actionl.data = n_posdata
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
        # get the material action
        b_action = b_material.action
        if not b_action:
            return
        # get the uv curves and translate them into nif data
        n_uvdata = NifFormat.NiUVData()
        n_times = [] # track all times (used later in start time and end time)
        b_channels = (Blender.action.MA_OFSX, Blender.action.MA_OFSY,
                      Blender.action.MA_SIZEX, Blender.action.MA_SIZEY)
        for b_channel, n_uvgroup in zip(b_channels, n_uvdata.uv_groups):
            b_curve = b_action[b_channel]
            if b_curve:
                self.info("Exporting %s as NiUVData" % b_curve)
                n_uvgroup.num_keys = len(b_curve.bezierPoints)
                n_uvgroup.interpolation = self.get_n_actionl_from_b_actionl(
                    b_curve.interpolation)
                n_uvgroup.keys.update_size()
                for b_point, n_key in zip(b_curve.bezierPoints, n_uvgroup.keys):
                    # add each point of the curve
                    b_time, b_value = b_point.pt
                    if b_channel in (Blender.action.MA_OFSX, Blender.action.MA_OFSY):
                        # offsets are negated in blender
                        b_value = -b_value
                    n_key.arg = n_uvgroup.interpolation
                    n_key.time = (b_time - 1) * self.context.scene.render.fps
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
        self.context = parent.context
    
    def export_object_vis_controller(self, b_obj, n_node):
        """Export the material alpha controller data."""
        b_action = b_obj.action
        if not b_action:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_action[Blender.action.OB_LAYER]
        if not b_curve:
            return
        # NiVisData = old style, NiBoolData = new style
        n_vis_data = self.nif_export.objecthelper.create_block("NiVisData", b_curve)
        n_bool_data = self.nif_export.objecthelper.create_block("NiBoolData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        # we just leave interpolation at constant
        n_bool_data.data.interpolation = NifFormat.KeyType.CONST_KEY
        #n_bool_data.data.interpolation = self.get_n_actionl_from_b_actionl(
        #    b_curve.interpolation)
        n_vis_data.num_keys = len(b_curve.bezierPoints)
        n_bool_data.data.num_keys = len(b_curve.bezierPoints)
        n_vis_data.keys.update_size()
        n_bool_data.data.keys.update_size()
        visible_layer = 2 ** (min(self.context.scene.getLayers()) - 1)
        for b_point, n_vis_key, n_bool_key in zip(
            b_curve.bezierPoints, n_vis_data.keys, n_bool_data.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_vis_key.arg = n_bool_data.data.interpolation # n_vis_data has no interpolation stored
            n_vis_key.time = (b_time - 1) * self.context.scene.render.fps
            n_vis_key.value = 1 if (int(b_value + 0.01) & visible_layer) else 0
            n_bool_key.arg = n_bool_data.data.interpolation
            n_bool_key.time = n_vis_key.time
            n_bool_key.value = n_vis_key.value
            # track time
            n_times.append(n_vis_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_vis_ctrl = self.nif_export.objecthelper.create_block("NiVisController", b_action)
            n_vis_actionl = self.nif_export.objecthelper.create_block("NiBoolInterpolator", b_action)
            n_vis_ctrl.interpolator = n_vis_actionl
            n_vis_ctrl.flags = 8 # active
            n_vis_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_vis_ctrl.frequency = 1.0
            n_vis_ctrl.start_time = min(n_times)
            n_vis_ctrl.stop_time = max(n_times)
            n_vis_ctrl.data = n_vis_data
            n_vis_actionl.data = n_bool_data
            # attach block to node
            n_node.add_controller(n_vis_ctrl)




