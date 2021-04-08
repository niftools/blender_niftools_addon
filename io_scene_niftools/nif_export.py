"""This script exports Netimmerse and Gamebryo .nif files from Blender."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2007, NIF File Format Library and Tools contributors.
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


import os.path

import bpy
import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_export.animation.transform import TransformAnimation
from io_scene_niftools.modules.nif_export.constraint import Constraint
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.object import Object
from io_scene_niftools.modules.nif_export import scene
from io_scene_niftools.modules.nif_export.property.object import ObjectProperty
from io_scene_niftools.nif_common import NifCommon
from io_scene_niftools.utils import math, consts
from io_scene_niftools.utils.singleton import NifOp, EGMData, NifData
from io_scene_niftools.utils.logging import NifLog, NifError


# main export class


class NifExport(NifCommon):

    # TODO: - Expose via properties

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.transform_anim = TransformAnimation()
        self.constrainthelper = Constraint()
        self.objecthelper = Object()
        self.exportable_objects = []
        self.root_objects = []

    def execute(self):
        """Main export function."""
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        NifLog.info(f"Exporting {NifOp.props.filepath}")

        # extract directory, base name, extension
        directory = os.path.dirname(NifOp.props.filepath)
        filebase, fileext = os.path.splitext(os.path.basename(NifOp.props.filepath))

        block_store.block_to_obj = {}  # clear out previous iteration

        try:  # catch export errors

            # find all objects that do not have a parent
            self.exportable_objects, self.root_objects = self.objecthelper.get_export_objects()
            if not self.exportable_objects:
                NifLog.warn("No objects can be exported!")
                return {'FINISHED'}

            for b_obj in self.exportable_objects:
                # armatures should not be in rest position
                if b_obj.type == 'ARMATURE':
                    b_obj.data.pose_position = 'POSE'

                elif b_obj.type == 'MESH':
                    if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                        for b_mod in b_obj.modifiers:
                            if b_mod.type == 'ARMATURE' and b_mod.use_bone_envelopes:
                                raise NifError(f"'{b_obj.name}': Cannot export envelope skinning. If you have vertex groups, turn off envelopes.\n"
                                               f"If you don't have vertex groups, select the bones one by one press W to "
                                               f"convert their envelopes to vertex weights, and turn off envelopes.")

                # check for non-uniform transforms
                scale = b_obj.matrix_local.to_scale()
                if abs(scale.x - scale.y) > NifOp.props.epsilon or abs(scale.y - scale.z) > NifOp.props.epsilon:
                    NifLog.warn(f"Non-uniform scaling not supported.\n"
                                f"Workaround: apply size and rotation (CTRL-A) on '{b_obj.name}'.")

            b_armature = math.get_armature()
            # some scenes may not have an armature, so nothing to do here
            if b_armature:
                math.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)

            prefix = "x" if bpy.context.scene.niftools_scene.game in ('MORROWIND', ) else ""
            NifLog.info("Exporting")
            if NifOp.props.animation == 'ALL_NIF':
                NifLog.info("Exporting geometry and animation")
            elif NifOp.props.animation == 'GEOM_NIF':
                # for morrowind: everything except keyframe controllers
                NifLog.info("Exporting geometry only")

            # find nif version to write

            self.version, data = scene.get_version_data()
            NifData.init(data)

            # export the actual root node (the name is fixed later to avoid confusing the exporter with duplicate names)
            root_block = self.objecthelper.export_root_node(self.root_objects, filebase)

            # post-processing:
            # ----------------

            NifLog.info("Checking controllers")
            if bpy.context.scene.niftools_scene.game == 'MORROWIND':
                # animations without keyframe animations crash the TESCS
                # if we are in that situation, add a trivial keyframe animation
                has_keyframecontrollers = False
                for block in block_store.block_to_obj:
                    if isinstance(block, NifFormat.NiKeyframeController):
                        has_keyframecontrollers = True
                        break
                if (not has_keyframecontrollers) and (not NifOp.props.bs_animation_node):
                    NifLog.info("Defining dummy keyframe controller")
                    # add a trivial keyframe controller on the scene root
                    self.transform_anim.create_controller(root_block, root_block.name)

                if NifOp.props.bs_animation_node:
                    for block in block_store.block_to_obj:
                        if isinstance(block, NifFormat.NiNode):
                            # if any of the shape children has a controller or if the ninode has a controller convert its type
                            if block.controller or any(child.controller for child in block.children if isinstance(child, NifFormat.NiGeometry)):
                                new_block = NifFormat.NiBSAnimationNode().deepcopy(block)
                                # have to change flags to 42 to make it work
                                new_block.flags = 42
                                root_block.replace_global_node(block, new_block)
                                if root_block is block:
                                    root_block = new_block

            # oblivion skeleton export: check that all bones have a transform controller and transform interpolator
            if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') and filebase.lower() in ('skeleton', 'skeletonbeast'):

                # TODO [armature] Extract out to armature animation
                # here comes everything that is Oblivion skeleton export specific
                NifLog.info("Adding controllers and interpolators for skeleton")
                # note: block_store.block_to_obj changes during iteration, so need list copy
                for n_block in list(block_store.block_to_obj.keys()):
                    if isinstance(n_block, NifFormat.NiNode) and n_block.name.decode() == "Bip01":
                        for n_bone in n_block.tree(block_type=NifFormat.NiNode):
                            n_kfc, n_kfi = self.transform_anim.create_controller(n_bone, n_bone.name.decode())
                            # todo [anim] use self.nif_export.animationhelper.set_flags_and_timing
                            n_kfc.flags = 12
                            n_kfc.frequency = 1.0
                            n_kfc.phase = 0.0
                            n_kfc.start_time = consts.FLOAT_MAX
                            n_kfc.stop_time = consts.FLOAT_MIN
            else:
                # here comes everything that should be exported EXCEPT for Oblivion skeleton exports
                # export animation groups (not for skeleton.nif export!)
                # anim_textextra = self.animation_helper.export_text_keys(b_action)
                pass

            # bhkConvexVerticesShape of children of bhkListShapes need an extra bhkConvexTransformShape (see issue #3308638, reported by Koniption)
            # note: block_store.block_to_obj changes during iteration, so need list copy
            for block in list(block_store.block_to_obj.keys()):
                if isinstance(block, NifFormat.bhkListShape):
                    for i, sub_shape in enumerate(block.sub_shapes):
                        if isinstance(sub_shape, NifFormat.bhkConvexVerticesShape):
                            coltf = block_store.create_block("bhkConvexTransformShape")
                            coltf.material = sub_shape.material
                            coltf.unknown_float_1 = 0.1
                            unk_8 = coltf.unknown_8_bytes
                            unk_8[0] = 96
                            unk_8[1] = 120
                            unk_8[2] = 53
                            unk_8[3] = 19
                            unk_8[4] = 24
                            unk_8[5] = 9
                            unk_8[6] = 253
                            unk_8[7] = 4
                            coltf.transform.set_identity()
                            coltf.shape = sub_shape
                            block.sub_shapes[i] = coltf

            # export constraints
            for b_obj in self.exportable_objects:
                if b_obj.constraints:
                    self.constrainthelper.export_constraints(b_obj, root_block)

            object_prop = ObjectProperty()
            object_prop.export_root_node_properties(root_block)

            # FIXME:
            """
            if self.EXPORT_FLATTENSKIN:
                # (warning: trouble if armatures parent other armatures or
                # if bones parent geometries, or if object is animated)
                # flatten skins
                skelroots = set()
                affectedbones = []
                for block in block_store.block_to_obj:
                    if isinstance(block, NifFormat.NiGeometry) and block.is_skin():
                        NifLog.info("Flattening skin on geometry {0}".format(block.name))
                        affectedbones.extend(block.flatten_skin())
                        skelroots.add(block.skin_instance.skeleton_root)
                # remove NiNodes that do not affect skin
                for skelroot in skelroots:
                    NifLog.info("Removing unused NiNodes in '{0}'".format(skelroot.name))
                    skelrootchildren = [child for child in skelroot.children
                                        if ((not isinstance(child,
                                                            NifFormat.NiNode))
                                            or (child in affectedbones))]
                    skelroot.num_children = len(skelrootchildren)
                    skelroot.children.update_size()
                    for i, child in enumerate(skelrootchildren):
                        skelroot.children[i] = child
            """

            # apply scale
            data.roots = [root_block]
            scale_correction = bpy.context.scene.niftools_scene.scale_correction
            if abs(scale_correction) > NifOp.props.epsilon:
                self.apply_scale(data, round(1 / NifOp.props.scale_correction))
                # also scale egm
                if EGMData.data:
                    EGMData.data.apply_scale(1 / scale_correction)

            # generate mopps (must be done after applying scale!)
            if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                for block in block_store.block_to_obj:
                    if isinstance(block, NifFormat.bhkMoppBvTreeShape):
                        NifLog.info("Generating mopp...")
                        block.update_mopp()
                        # print "=== DEBUG: MOPP TREE ==="
                        # block.parse_mopp(verbose = True)
                        # print "=== END OF MOPP TREE ==="
                        # warn about mopps on non-static objects
                        if any(sub_shape.layer != 1 for sub_shape in block.shape.sub_shapes):
                            NifLog.warn("Mopps for non-static objects may not function correctly in-game. You may wish to use simple primitives for collision.")

            # export nif file:
            # ----------------
            if bpy.context.scene.niftools_scene.game == 'EMPIRE_EARTH_II':
                ext = ".nifcache"
            else:
                ext = ".nif"
            NifLog.info(f"Writing {ext} file")

            # make sure we have the right file extension
            if fileext.lower() != ext:
                NifLog.warn(f"Changing extension from {fileext} to {ext} on output file")
            niffile = os.path.join(directory, prefix + filebase + ext)

            data.roots = [root_block]
            # todo [export] I believe this is redundant and setting modification only is the current way?
            data.neosteam = (bpy.context.scene.niftools_scene.game == 'NEOSTEAM')
            if bpy.context.scene.niftools_scene.game == 'NEOSTEAM':
                data.modification = "neosteam"
            elif bpy.context.scene.niftools_scene.game == 'ATLANTICA':
                data.modification = "ndoors"
            elif bpy.context.scene.niftools_scene.game == 'HOWLING_SWORD':
                data.modification = "jmihs1"

            with open(niffile, "wb") as stream:
                data.write(stream)

            # export egm file:
            # -----------------
            if EGMData.data:
                ext = ".egm"
                NifLog.info(f"Writing {ext} file")

                egmfile = os.path.join(directory, filebase + ext)
                with open(egmfile, "wb") as stream:
                    EGMData.data.write(stream)

            # save exported file (this is used by the test suite)
            self.root_blocks = [root_block]

        except NifError:
            return {'CANCELLED'}

        NifLog.info("Finished")
        return {'FINISHED'}
