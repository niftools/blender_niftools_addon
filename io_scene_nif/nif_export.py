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

from io_scene_nif.modules import armature
from io_scene_nif.modules.animation.animation_export import Animation
from io_scene_nif.modules.armature.armature_export import Armature
from io_scene_nif.modules.collision.collision_export import Collision
from io_scene_nif.modules.constraint.constraint_export import Constraint
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.modules.object.object_export import Object
from io_scene_nif.modules.property.property_export import Property
from io_scene_nif.modules.scene import scene_export
from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp, EGMData
from io_scene_nif.utility.util_logging import NifLog


# main export class
class NifExport(NifCommon):

    IDENTITY44 = NifFormat.Matrix44()
    IDENTITY44.set_identity()
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38

    # TODO: - Expose via properties

    EXPORT_OPTIMIZE_MATERIALS = True
    IGNORE_BLENDER_PHYSICS = False

    EXPORT_BHKLISTSHAPE = False
    EXPORT_OB_MASS = 10.0
    EXPORT_OB_SOLID = True

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.collisionhelper = Collision(parent=self)
        self.armaturehelper = Armature(parent=self)
        self.animationhelper = Animation(parent=self)
        self.propertyhelper = Property(parent=self)
        self.constrainthelper = Constraint(parent=self)
        self.objecthelper = Object(parent=self)
        self.exportable_objects = []

    def execute(self):
        """Main export function."""
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        NifLog.info("Exporting {0}".format(NifOp.props.filepath))

        # TODO [animation[ Fix morrowind animation support
        '''
        if NifOp.props.animation == 'ALL_NIF_XNIF_XKF' and NifOp.props.game == 'MORROWIND':
            # if exporting in nif+xnif+kf mode, then first export
            # the nif with geometry + animation, which is done by:
            NifOp.props.animation = 'ALL_NIF'
        '''

        # extract directory, base name, extension
        directory = os.path.dirname(NifOp.props.filepath)
        filebase, fileext = os.path.splitext(os.path.basename(NifOp.props.filepath))

        block_store.block_to_obj = {}  # clear out previous iteration

        try:  # catch export errors

            # get the root object from selected object
            selected_objects = bpy.context.selected_objects
            # if none are selected, just get all of this scene's objects
            if not selected_objects:
                selected_objects = bpy.context.scene.objects

            # only export empties, meshes, and armatures
            self.exportable_objects = [b_obj for b_obj in selected_objects if b_obj.type in Object.export_types]
            if not self.exportable_objects:
                NifLog.warn("No objects can be exported!")
                return {'FINISHED'}
            NifLog.info("Exporting objects")
            # find all objects that do not have a parent
            self.root_objects = [b_obj for b_obj in self.exportable_objects if not b_obj.parent]

            for b_obj in self.exportable_objects:
                # armatures should not be in rest position
                if b_obj.type == 'ARMATURE':
                    b_obj.data.pose_position = 'POSE'

                elif b_obj.type == 'MESH':
                    if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                        for b_mod in b_obj.modifiers:
                            if b_mod.type == 'ARMATURE':
                                if b_mod.use_bone_envelopes:
                                    raise nif_utils.NifError("'%s': Cannot export envelope skinning. If you have vertex groups, turn off envelopes.\n"
                                                             "If you don't have vertex groups, select the bones one by one press W to "
                                                             "convert their envelopes to vertex weights, and turn off envelopes." % b_obj.name)

                # check for non-uniform transforms
                scale = b_obj.matrix_local.to_scale()
                if abs(scale.x - scale.y) > NifOp.props.epsilon or abs(scale.y - scale.z) > NifOp.props.epsilon:
                    NifLog.warn("Non-uniform scaling not supported.\n"
                                "Workaround: apply size and rotation (CTRL-A) on '%s'." % b_obj.name)

            b_armature = armature.get_armature()
            # some scenes may not have an armature, so nothing to do here
            if b_armature:
               armature.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)

            # smooth seams of objects
            if NifOp.props.smooth_object_seams:
                self.objecthelper.mesh_helper.smooth_mesh_seams(self.exportable_objects)

            prefix = ""
            NifLog.info("Exporting")
            if NifOp.props.animation == 'ALL_NIF':
                NifLog.info("Exporting geometry and animation")
            elif NifOp.props.animation == 'GEOM_NIF':
                # for morrowind: everything except keyframe controllers
                NifLog.info("Exporting geometry only")
            elif NifOp.props.animation == 'ANIM_KF':
                # for morrowind: only keyframe controllers
                NifLog.info("Exporting animation only (as .kf file)")
            elif NifOp.props.animation == 'ALL_NIF_XNIF_XKF':
                prefix = "x"
                NifLog.info("Exporting geometry and animation in xnif-style")

            # find nif version to write
            self.version, data = scene_export.get_version_data()

            # write external animation to a KF tree
            if NifOp.props.animation in ('ANIM_KF', 'ALL_NIF_XNIF_XKF'):
                NifLog.info("Creating keyframe tree")
                kf_root = self.animationhelper.export_kf_root(b_armature)

                # write kf (and xkf if asked)
                ext = ".kf"
                NifLog.info("Writing {0} file".format(prefix + ext))

                kffile = os.path.join(directory, prefix + filebase + ext)
                data.roots = [kf_root]
                data.neosteam = (NifOp.props.game == 'NEOSTEAM')
                with open(kffile, "wb") as stream:
                    data.write(stream)
                # if only anim, no need to do the time consuming nif export
                if NifOp.props.animation == 'ANIM_KF':
                    # clear progress bar
                    NifLog.info("Finished")
                    return {'FINISHED'}

            # export the actual root node (the name is fixed later to avoid confusing the exporter with duplicate names)
            root_block = self.objecthelper.export_root_node(self.root_objects, filebase)

            # post-processing:
            # ----------------

            NifLog.info("Checking controllers")
            if NifOp.props.game == 'MORROWIND':
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
                    self.animationhelper.create_controller(root_block, root_block.name)

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
            if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') and filebase.lower() in ('skeleton', 'skeletonbeast'):

                # TODO [armature] Extract out to armature animation
                # here comes everything that is Oblivion skeleton export specific
                NifLog.info("Adding controllers and interpolators for skeleton")
                # note: block_store.block_to_obj changes during iteration, so need list copy
                for n_block in list(block_store.block_to_obj.keys()):
                    if isinstance(n_block, NifFormat.NiNode) and n_block.name.decode() == "Bip01":
                        for n_bone in n_block.tree(block_type=NifFormat.NiNode):
                            n_kfc, n_kfi = self.animationhelper.create_controller(n_bone, n_bone.name.decode())
                            # todo [anim] use self.nif_export.animationhelper.set_flags_and_timing
                            n_kfc.flags = 12
                            n_kfc.frequency = 1.0
                            n_kfc.phase = 0.0
                            n_kfc.start_time = self.FLOAT_MAX
                            n_kfc.stop_time = self.FLOAT_MIN
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
                            coltf.unknown_8_bytes[0] = 96
                            coltf.unknown_8_bytes[1] = 120
                            coltf.unknown_8_bytes[2] = 53
                            coltf.unknown_8_bytes[3] = 19
                            coltf.unknown_8_bytes[4] = 24
                            coltf.unknown_8_bytes[5] = 9
                            coltf.unknown_8_bytes[6] = 253
                            coltf.unknown_8_bytes[7] = 4
                            coltf.transform.set_identity()
                            coltf.shape = sub_shape
                            block.sub_shapes[i] = coltf

            # export constraints
            for b_obj in self.exportable_objects:
                if b_obj.constraints:
                    self.constrainthelper.export_constraints(b_obj, root_block)

            # add vertex color and zbuffer properties for civ4 and railroads
            if NifOp.props.game in ('CIVILIZATION_IV', 'SID_MEIER_S_RAILROADS'):
                self.propertyhelper.object_property.export_vertex_color_property(root_block)
                self.propertyhelper.object_property.export_z_buffer_property(root_block)

            elif NifOp.props.game in ('EMPIRE_EARTH_II',):
                self.propertyhelper.object_property.export_vertex_color_property(root_block)
                self.propertyhelper.object_property.export_z_buffer_property(root_block, flags=15, function=1)

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
            if abs(NifOp.props.scale_correction_export) > NifOp.props.epsilon:
                NifLog.info("Applying scale correction {0}".format(str(NifOp.props.scale_correction_export)))
                data.roots = [root_block]
                toaster = pyffi.spells.nif.NifToaster()
                toaster.scale = NifOp.props.scale_correction_export
                pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()

                # also scale egm
                if EGMData.data:
                    EGMData.data.apply_scale(NifOp.props.scale_correction_export)

            # generate mopps (must be done after applying scale!)
            if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
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
            if NifOp.props.game == 'EMPIRE_EARTH_II':
                ext = ".nifcache"
            else:
                ext = ".nif"
            NifLog.info("Writing {0} file".format(ext))

            # make sure we have the right file extension
            if fileext.lower() != ext:
                NifLog.warn("Changing extension from {0} to {1} on output file".format(fileext, ext))
            niffile = os.path.join(directory, prefix + filebase + ext)

            data.roots = [root_block]
            # todo [export] I believe this is redundant and setting modification only is the current way?
            data.neosteam = (NifOp.props.game == 'NEOSTEAM')
            if NifOp.props.game == 'NEOSTEAM':
                data.modification = "neosteam"
            elif NifOp.props.game == 'ATLANTICA':
                data.modification = "ndoors"
            elif NifOp.props.game == 'HOWLING_SWORD':
                data.modification = "jmihs1"
            with open(niffile, "wb") as stream:
                data.write(stream)

            # export egm file:
            # -----------------
            if EGMData.data:
                ext = ".egm"
                NifLog.info("Writing {0} file".format(ext))

                egmfile = os.path.join(directory, filebase + ext)
                with open(egmfile, "wb") as stream:
                    EGMData.data.write(stream)
        finally:
            # clear progress bar
            NifLog.info("Finished")

        # save exported file (this is used by the test suite)
        self.root_blocks = [root_block]

        return {'FINISHED'}
