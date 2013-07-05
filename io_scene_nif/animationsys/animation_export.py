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

import mathutils

class AnimationHelper():
    
    def __init__(self, parent):
        self.nif_export = parent
        self.properties = parent.properties
        self.context = parent.context
        self.object_animation = ObjectAnimation(parent)
        self.material_animation = MaterialAnimation(parent)
    
    # Export the animation of blender Ipo as keyframe controller and
    # keyframe data. Extra quaternion is multiplied prior to keyframe
    # rotation, and dito for translation. These extra fields come in handy
    # when exporting bone ipo's, which are relative to the rest pose, so
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
        if extend == bpy.types.IpoCurve.ExtendTypes.CONST:
            return 4 # 0b100
        elif extend == bpy.types.IpoCurve.ExtendTypes.CYCLIC:
            return 0

        self.nif_export.warning(
            "Unsupported extend type in blend, using clamped.")
        return 4
    
    def export_keyframes(self, ipo, space, parent_block, bind_matrix = None,
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
            kfc = self.nif_export.create_block("NiKeyframeController", ipo)
        else:
            kfc = self.nif_export.create_block("NiTransformController", ipo)
            kfi = self.nif_export.create_block("NiTransformInterpolator", ipo)
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
        if ipo:
            start_frame = +1000000
            stop_frame = -1000000
            for curve in ipo:
                # get cycle mode
                if extend is None:
                    extend = curve.extend
                elif extend != curve.extend:
                    self.nif_export.warning(
                        "Inconsistent extend type in %s, will use %s."
                        % (ipo, extend))
                # get start and stop frames
                start_frame = min(
                    start_frame,
                    min(btriple.pt[0] for btriple in curve.bezierPoints))
                stop_frame = max(
                    stop_frame,
                    max(btriple.pt[0] for btriple in curve.bezierPoints))
        else:
            # dummy ipo
            # default extend, start, and end
            extend = bpy.IpoCurve.ExtendTypes.CYCLIC
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
        if (ipo == None):
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
            assert(Ipo.PO_SCALEX == Ipo.OB_SCALEX)
            assert(Ipo.PO_LOCX == Ipo.OB_LOCX)
            # check validity of curves
            for curvecollection in (
                (Ipo.PO_SCALEX, Ipo.PO_SCALEY, Ipo.PO_SCALEZ),
                (Ipo.PO_LOCX, Ipo.PO_LOCY, Ipo.PO_LOCZ),
                (Ipo.PO_QUATX, Ipo.PO_QUATY, Ipo.PO_QUATZ, Ipo.PO_QUATW),
                (Ipo.OB_ROTX, Ipo.OB_ROTY, Ipo.OB_ROTZ)):
                # skip invalid curves
                try:
                    ipo[curvecollection[0]]
                except KeyError:
                    continue
                # check that if any curve is defined in the collection
                # then all curves are defined in the collection
                if (any(ipo[curve] for curve in curvecollection)
                    and not all(ipo[curve] for curve in curvecollection)):
                    keytype = {Ipo.PO_SCALEX: "SCALE",
                               Ipo.PO_LOCX: "LOC",
                               Ipo.PO_QUATX: "ROT",
                               Ipo.OB_ROTX: "ROT"}
                    raise nif_utils.NifExportError(
                        "missing curves in %s; insert %s key at frame 1"
                        " and try again"
                        % (ipo, keytype[curvecollection[0]]))
            # go over all curves
            ipo_curves = list(ipo.curveConsts.values())
            for curve in ipo_curves:
                # skip empty curves
                if ipo[curve] is None:
                    continue
                # non-empty curve: go over all frames of the curve
                for btriple in ipo[curve].bezierPoints:
                    frame = btriple.pt[0]
                    if (frame < self.context.scene.frame_start) or (frame > self.context.scene.frame_end):
                        continue
                    # PO_SCALEX == OB_SCALEX, so this does both pose and object
                    # scale
                    if curve in (Ipo.PO_SCALEX, Ipo.PO_SCALEY, Ipo.PO_SCALEZ):
                        # support only uniform scaling... take the mean
                        scale_curve[frame] = (ipo[Ipo.PO_SCALEX][frame]
                                              + ipo[Ipo.PO_SCALEY][frame]
                                              + ipo[Ipo.PO_SCALEZ][frame]) / 3.0
                        # SC' * SB' / SX
                        scale_curve[frame] = \
                            scale_curve[frame] * bind_scale * extra_scale_inv
                    # object rotation
                    elif curve in (Ipo.OB_ROTX, Ipo.OB_ROTY, Ipo.OB_ROTZ):
                        rot_curve[frame] = mathutils.Euler(
                            [10 * ipo[Ipo.OB_ROTX][frame],
                             10 * ipo[Ipo.OB_ROTY][frame],
                             10 * ipo[Ipo.OB_ROTZ][frame]])
                        # use quat if we have bind matrix and/or extra matrix
                        # XXX maybe we should just stick with eulers??
                        if bind_matrix or extra_mat_inv:
                            rot_curve[frame] = rot_curve[frame].toQuat()
                            # beware, CrossQuats takes arguments in a counter-intuitive order:
                            # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                            rot_curve[frame] = mathutils.CrossQuats(mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # pose rotation
                    elif curve in (Ipo.PO_QUATX, Ipo.PO_QUATY,
                                   Ipo.PO_QUATZ, Ipo.PO_QUATW):
                        rot_curve[frame] = mathutils.Quaternion()
                        rot_curve[frame].x = ipo[Ipo.PO_QUATX][frame]
                        rot_curve[frame].y = ipo[Ipo.PO_QUATY][frame]
                        rot_curve[frame].z = ipo[Ipo.PO_QUATZ][frame]
                        rot_curve[frame].w = ipo[Ipo.PO_QUATW][frame]
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        rot_curve[frame] = mathutils.CrossQuats(mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # PO_LOCX == OB_LOCX, so this does both pose and object
                    # location
                    elif curve in (Ipo.PO_LOCX, Ipo.PO_LOCY, Ipo.PO_LOCZ):
                        trans_curve[frame] = mathutils.Vector(
                            [ipo[Ipo.PO_LOCX][frame],
                             ipo[Ipo.PO_LOCY][frame],
                             ipo[Ipo.PO_LOCZ][frame]])
                        # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
                        trans_curve[frame] *= bind_scale
                        trans_curve[frame] *= bind_rot
                        trans_curve[frame] += bind_trans
                        # we need RC' and SC'
                        if Ipo.OB_ROTX in ipo_curves and ipo[Ipo.OB_ROTX]:
                            rot_c = mathutils.Euler(
                                [10 * ipo[Ipo.OB_ROTX][frame],
                                 10 * ipo[Ipo.OB_ROTY][frame],
                                 10 * ipo[Ipo.OB_ROTZ][frame]]).toMatrix()
                        elif Ipo.PO_QUATX in ipo_curves and ipo[Ipo.PO_QUATX]:
                            rot_c = mathutils.Quaternion()
                            rot_c.x = ipo[Ipo.PO_QUATX][frame]
                            rot_c.y = ipo[Ipo.PO_QUATY][frame]
                            rot_c.z = ipo[Ipo.PO_QUATZ][frame]
                            rot_c.w = ipo[Ipo.PO_QUATW][frame]
                            rot_c = rot_c.toMatrix()
                        else:
                            rot_c = mathutils.Matrix([[1,0,0],[0,1,0],[0,0,1]])
                        # note, PO_SCALEX == OB_SCALEX, so this does both
                        if ipo[Ipo.PO_SCALEX]:
                            # support only uniform scaling... take the mean
                            scale_c = (ipo[Ipo.PO_SCALEX][frame]
                                       + ipo[Ipo.PO_SCALEY][frame]
                                       + ipo[Ipo.PO_SCALEZ][frame]) / 3.0
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
            kfd = self.nif_export.create_block("NiKeyframeData", ipo)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.nif_export.create_block("NiTransformData", ipo)
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
            
