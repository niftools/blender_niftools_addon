"""This script imports Netimmerse/Gamebryo nif files to Blender."""

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


import bpy
import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat

from io_scene_nif.io.egm import EGMFile
from io_scene_nif.io.nif import NifFile
from io_scene_nif.modules import armature
from io_scene_nif.modules.animation.animation_import import Animation
from io_scene_nif.modules.animation.object_import import ObjectAnimation
from io_scene_nif.modules.animation.transform_import import TransformAnimation
from io_scene_nif.modules.armature.armature_import import Armature
from io_scene_nif.modules.collision.collision_import import Collision
from io_scene_nif.modules.constraint.constraint_import import Constraint
from io_scene_nif.modules.geometry.vertex.skin_import import VertexGroup
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.modules.object.object_import import Object
from io_scene_nif.modules.object.object_types.type_import import NiTypes
from io_scene_nif.modules.scene import scene_import

from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp, EGMData, NifData
from io_scene_nif.utility.util_logging import NifLog


class NifImport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

    def execute(self):
        """Main import function."""
        self.load_files()

        # find and store this list now of selected objects as creating new objects adds them to the selection list
        self.SELECTED_OBJECTS = bpy.context.selected_objects[:]

        # Helper systems
        self.armaturehelper = Armature()
        self.collisionhelper = Collision()
        self.constrainthelper = Constraint()
        self.objecthelper = Object()
        self.object_anim = ObjectAnimation()
        self.transform_anim = TransformAnimation()

        # catch nif import errors
        try:
            # check that one armature is selected in 'import geometry + parent
            # to armature' mode
            if NifOp.props.skeleton == "GEOMETRY_ONLY":
                if len(NifCommon.SELECTED_OBJECTS) != 1 or NifCommon.SELECTED_OBJECTS[0].type != 'ARMATURE':
                    raise nif_utils.NifError("You must select exactly one armature in 'Import Geometry Only + Parent To Selected Armature' mode.")

            # the axes used for bone correction depend on the nif version
            armature.set_bone_orientation(NifOp.props.axis_forward, NifOp.props.axis_up)

            NifLog.info("Importing data")
            # calculate and set frames per second
            if NifOp.props.animation:
                Animation.set_frames_per_second(NifData.data.roots)

            # merge skeleton roots and transform geometry into the rest pose
            if NifOp.props.merge_skeleton_roots:
                pyffi.spells.nif.fix.SpellMergeSkeletonRoots(data=NifData.data).recurse()
            if NifOp.props.send_geoms_to_bind_pos:
                pyffi.spells.nif.fix.SpellSendGeometriesToBindPosition(data=NifData.data).recurse()
            if NifOp.props.send_detached_geoms_to_node_pos:
                pyffi.spells.nif.fix.SpellSendDetachedGeometriesToNodePosition(data=NifData.data).recurse()
            if NifOp.props.send_bones_to_bind_position:
                pyffi.spells.nif.fix.SpellSendBonesToBindPosition(data=NifData.data).recurse()
            if NifOp.props.apply_skin_deformation:
                VertexGroup.apply_skin_deformation(NifData.data)

            # scale tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = NifOp.props.scale_correction_import
            pyffi.spells.nif.fix.SpellScale(data=NifData.data, toaster=toaster).recurse()

            # import all root blocks
            for block in NifData.data.roots:
                root = block
                # root hack for corrupt better bodies meshes and remove geometry from better bodies on skeleton import
                for b in (b for b in block.tree() if isinstance(b, NifFormat.NiGeometry) and b.is_skin()):
                    # check if root belongs to the children list of the skeleton root (can only happen for better bodies meshes)
                    if root in [c for c in b.skin_instance.skeleton_root.children]:
                        # fix parenting and update transform accordingly
                        b.skin_instance.data.set_transform(root.get_transform() * b.skin_instance.data.get_transform())
                        b.skin_instance.skeleton_root = root
                        # delete non-skeleton nodes if we're importing skeleton only
                        if NifOp.props.skeleton == "SKELETON_ONLY":
                            nonbip_children = (child for child in root.children if child.name[:6] != 'Bip01 ')
                            for child in nonbip_children:
                                root.remove_child(child)

                # import this root block
                NifLog.debug("Root block: {0}".format(root.get_global_display()))
                self.import_root(root)
        finally:
            # clear progress bar
            NifLog.info("Finished")

        return {'FINISHED'}

    def load_files(self):
        NifData.init(NifFile.load_nif(NifOp.props.filepath))
        if NifOp.props.override_scene_info:
            scene_import.import_version_info(NifData.data)
        egm_path = NifOp.props.egm_file

        if egm_path:
            EGMData.init(EGMFile.load_egm(egm_path))
            # scale the data
            EGMData.data.apply_scale(NifOp.props.scale_correction_import)
        else:
            EGMData.init(None)

    def import_root(self, root_block):
        """Main import function."""
        # check that this is not a kf file
        if isinstance(root_block, (NifFormat.NiSequence, NifFormat.NiSequenceStreamHelper)):
            raise nif_utils.NifError("Use the KF import operator to load KF files.")

        # divinity 2: handle CStreamableAssetData
        if isinstance(root_block, NifFormat.CStreamableAssetData):
            root_block = root_block.root

        # sets the root block parent to None, so that when crawling back the script won't barf
        root_block._parent = None

        # set the block parent through the tree, to ensure I can always move backward
        self.set_parents(root_block)

        # mark armature nodes and bones
        self.armaturehelper.mark_armatures_bones(root_block)

        # import the keyframe notes
        # if NifOp.props.animation:
        #     self.animationhelper.import_text_keys(root_block)

        # read the NIF tree
        if isinstance(root_block, (NifFormat.NiNode, NifFormat.NiTriBasedGeom)):
            b_obj = self.import_branch(root_block)
            self.objecthelper.import_extra_datas(root_block, b_obj)

            # now all havok objects are imported, so we are ready to import the havok constraints
            self.constrainthelper.import_bhk_constraints()

            # parent selected meshes to imported skeleton
            if NifOp.props.skeleton == "SKELETON_ONLY":
                # update parenting & armature modifier
                for child in bpy.context.selected_objects:
                    if isinstance(child, bpy.types.Object) and not isinstance(child.data, bpy.types.Armature):
                        child.parent = b_obj
                        for mod in child.modifiers:
                            if mod.type == "ARMATURE":
                                mod.object = b_obj

        elif isinstance(root_block, NifFormat.NiCamera):
            NifLog.warn('Skipped NiCamera root')

        elif isinstance(root_block, NifFormat.NiPhysXProp):
            NifLog.warn('Skipped NiPhysXProp root')

        else:
            NifLog.warn("Skipped unsupported root block type '{0}' (corrupted nif?).".format(root_block.__class__))

    def import_branch(self, n_block, b_armature=None, n_armature=None):
        """Read the content of the current NIF tree branch to Blender recursively.

        :param n_block: The nif block to import.
        :param b_armature: The blender armature for the current branch.
        :param n_armature: The corresponding nif block for the armature for  the current branch.
        """
        if not n_block:
            return None

        # start with no grouping
        geom_group = []
        NifLog.info("Importing data for block '{0}'".format(n_block.name.decode()))
        if isinstance(n_block, NifFormat.NiTriBasedGeom) and NifOp.props.skeleton != "SKELETON_ONLY":
            return self.objecthelper.import_geometry_object(b_armature, n_block)

        elif isinstance(n_block, NifFormat.NiNode):
            # import object
            if self.armaturehelper.is_armature_root(n_block):
                # all bones in the tree are also imported by import_armature
                if NifOp.props.skeleton != "GEOMETRY_ONLY":
                    b_obj = self.armaturehelper.import_armature(n_block)
                else:
                    n_name = block_store.import_name(n_block)
                    b_obj = armature.get_armature()
                    NifLog.info("Merging nif tree '{0}' with armature '{1}'".format(n_name, b_obj.name))
                    if n_name != b_obj.name:
                        NifLog.warn("Using Nif block '{0}' as armature '{1}' but names do not match".format(n_name, b_obj.name))
                b_armature = b_obj
                n_armature = n_block

            elif self.armaturehelper.is_bone(n_block):
                # bones have already been imported during import_armature
                b_obj = b_armature.data.bones[block_store.import_name(n_block)]
                # TODO [object] flags, shouldn't be treated any different than object flags.
                b_obj.niftools.boneflags = n_block.flags

            else:
                # this may be a grouping node
                geom_group = Object.is_grouping_node(n_block)

                # if importing animation, remove children that have morph controllers from geometry group
                if NifOp.props.animation:
                    for child in geom_group:
                        if nif_utils.find_controller(child, NifFormat.NiGeomMorpherController):
                            geom_group.remove(child)

                # import geometry/empty
                if not geom_group or not NifOp.props.combine_shapes or len(geom_group) > 16:
                    # no grouping node, or too many materials to group the geometry into a single mesh
                    # so import it as an empty
                    b_obj = NiTypes.import_empty(n_block)

                    geom_group = []
                else:
                    b_obj = self.objecthelper.import_group_geometry(b_armature, geom_group, n_block)

            # find children that aren't part of the geometry group
            b_children = []
            n_children = [child for child in n_block.children if child not in geom_group]
            for n_child in n_children:
                b_child = self.import_branch(n_child, b_armature=b_armature, n_armature=n_armature)
                if b_child and isinstance(b_child, bpy.types.Object):
                    b_children.append(b_child)

            # import collision objects & bounding box
            if NifOp.props.skeleton != "SKELETON_ONLY":
                b_children.extend(self.collisionhelper.import_collision(n_block))
                b_children.extend(self.collisionhelper.import_bounding_box(n_block))

            # set bind pose for children
            self.objecthelper.set_object_bind(b_obj, b_children, b_armature)

            # import extra node data, such as node type
            self.objecthelper.import_root_collision(n_block, b_obj)
            NiTypes.import_billboard(n_block, b_obj)
            NiTypes.import_range_lod_data(n_block, b_obj, b_children)

            # set object transform, this must be done after all children objects have been parented to b_obj
            if isinstance(b_obj, bpy.types.Object):
                # note: bones and this object's children already have their matrix set
                b_obj.matrix_local = nif_utils.import_matrix(n_block)

                # import object level animations (non-skeletal)
                if NifOp.props.animation:
                    # self.animationhelper.import_text_keys(n_block)
                    self.transform_anim.import_transforms(n_block, b_obj)
                    self.object_anim.import_visibility(n_block, b_obj)

            return b_obj

        # all else is currently discarded
        return None

    def set_parents(self, n_block):
        """Set the parent block recursively through the tree, to allow
        crawling back as needed."""
        if isinstance(n_block, NifFormat.NiNode):
            # list of non-null children
            children = [child for child in n_block.children if child]
            for child in children:
                child._parent = n_block
                self.set_parents(child)
