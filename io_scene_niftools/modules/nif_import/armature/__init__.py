"""Script to import/export all the skeleton related objects."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2012, NIF File Format Library and Tools contributors.
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

import os

import bpy
import mathutils

from pyffi.formats.nif import NifFormat

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_import.object.block_registry import block_store
from io_scene_niftools.modules.nif_export.block_registry import block_store as block_store_export
from io_scene_niftools.modules.nif_import.animation.transform import TransformAnimation
from io_scene_niftools.modules.nif_import.object import Object
from io_scene_niftools.utils import math
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.singleton import NifOp, NifData


class Armature:

    def __init__(self):
        self.transform_anim = TransformAnimation()
        # this is used to hold lists of bones for each armature during mark_armatures_bones
        self.dict_armatures = {}
        # to get access to the nif bone in object mode
        self.name_to_block = {}

    def store_pose_matrix(self, n_node, armature_space_pose_store, n_root):
        # check that n_block is indeed a bone
        if not self.is_bone(n_node):
            return None
        armature_space_pose_store[n_node] = n_node.get_transform(n_root)
        # move down the hierarchy
        for n_child in n_node.children:
            self.store_pose_matrix(n_child, armature_space_pose_store, n_root)

    def import_pose(self, n_armature):
        """Ported and adapted from pyffi send_bones_to_bind_position"""
        armature_space_bind_store = {}
        armature_space_pose_store = {}
        # check all bones and bone datas to see if a bind position exists
        bonelist = []
        # store the original pose matrix for all nodes
        for n_child in n_armature.children:
            self.store_pose_matrix(n_child, armature_space_pose_store, n_armature)

        # prioritize geometries that have most nodes in their skin instance
        for geom in sorted(n_armature.get_skinned_geometries(), key=lambda g: g.skin_instance.num_bones, reverse=True):
            skininst = geom.skin_instance
            skindata = skininst.data
            for bonenode, bonedata in zip(skininst.bones, skindata.bone_list):
                # bonenode can be None; see pyffi issue #3114079
                if not bonenode:
                    continue
                # make sure all bone data of shared bones coincides
                for othergeom, otherbonenode, otherbonedata in bonelist:
                    if bonenode is otherbonenode:
                        diff = ((otherbonedata.get_transform().get_inverse(fast=False)
                                 * othergeom.get_transform(n_armature))
                                -
                                (bonedata.get_transform().get_inverse(fast=False)
                                 * geom.get_transform(n_armature)))
                        if diff.sup_norm() > 1e-3:
                            NifLog.debug(
                                f"Geometries {geom.name} and {othergeom.name} do not share the same bind position."
                                f"bone {bonenode.name} will be sent to a position matching only one of these")
                        # break the loop
                        break
                else:
                    # the loop did not break, so the bone was not yet added
                    # add it now
                    NifLog.debug(f"Found bind position data for {bonenode.name}")
                    bonelist.append((geom, bonenode, bonedata))

        # get the bind pose from the skin data
        # NiSkinData stores the inverse bind (=rest) pose for each bone, in armature space
        for geom, bonenode, bonedata in bonelist:
            n_bind = (bonedata.get_transform().get_inverse(fast=False) * geom.get_transform(n_armature))
            armature_space_bind_store[bonenode] = n_bind

        NifLog.debug("Storing non-skeletal bone poses")
        self.fix_pose(n_armature, n_armature, armature_space_bind_store, armature_space_pose_store)
        return armature_space_bind_store, armature_space_pose_store

    def fix_pose(self, n_armature, n_node, armature_space_bind_store, armature_space_pose_store):
        """reposition non-skeletal bones to maintain their local orientation to their skeletal parents"""
        for n_child_node in n_node.children:
            # only process nodes
            if not isinstance(n_child_node, NifFormat.NiNode):
                continue
            if n_child_node not in armature_space_bind_store and n_child_node in armature_space_pose_store:
                NifLog.debug(f"Calculating bind pose for non-skeletal bone {n_child_node.name}")
                # get matrices for n_node (the parent) - fallback to getter if it is not in the store
                n_armature_pose = armature_space_pose_store.get(n_node, n_node.get_transform(n_armature))
                # get bind of parent node or pose if it has no bind pose
                n_armature_bind = armature_space_bind_store.get(n_node, n_armature_pose)

                # the child must have a pose, no need for a fallback
                n_child_armature_pose = armature_space_pose_store[n_child_node]
                # get the relative transform of n_child_node from pose * inverted parent pose
                n_child_local_pose = n_child_armature_pose * n_armature_pose.get_inverse(fast=False)
                # get object space transform by multiplying with bind of parent bone
                armature_space_bind_store[n_child_node] = n_child_local_pose * n_armature_bind

            self.fix_pose(n_armature, n_child_node, armature_space_bind_store, armature_space_pose_store)

    def import_armature(self, n_armature):
        """Scans an armature hierarchy, and returns a whole armature.
        This is done outside the normal node tree scan to allow for positioning
        of the bones before skins are attached."""

        armature_name = block_store.import_name(n_armature)
        b_armature_data = bpy.data.armatures.new(armature_name)
        b_armature_data.display_type = 'STICK'

        # use heuristics to determine a suitable orientation
        forward, up = self.guess_orientation(n_armature)
        # pass them to the matrix utility
        math.set_bone_orientation(forward, up)
        # store axis orientation for export
        b_armature_data.niftools.axis_forward = forward
        b_armature_data.niftools.axis_up = up
        b_armature_obj = Object.create_b_obj(n_armature, b_armature_data)
        b_armature_obj.show_in_front = True

        armature_space_bind_store, armature_space_pose_store = self.import_pose(n_armature)

        # make armature editable and create bones
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        for n_child in n_armature.children:
            self.import_bone_bind(n_child, armature_space_bind_store, b_armature_data, n_armature)
        self.fix_bone_lengths(b_armature_data)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # The armature has been created in editmode,
        # now we are ready to set the bone keyframes and store the bones' long names.
        if NifOp.props.animation:
            self.transform_anim.create_action(b_armature_obj, armature_name + "-Anim")

        for bone_name, b_bone in b_armature_obj.data.bones.items():
            n_block = self.name_to_block[bone_name]
            # the property is only available from object mode!
            block_store.store_longname(b_bone, n_block.name.decode())
            if NifOp.props.animation:
                self.transform_anim.import_transforms(n_block, b_armature_obj, bone_name)

        # import pose
        for b_name, n_block in self.name_to_block.items():
            n_pose = armature_space_pose_store[n_block]
            b_pose_bone = b_armature_obj.pose.bones[b_name]
            n_bind = mathutils.Matrix(n_pose.as_list()).transposed()
            b_pose_bone.matrix = math.nif_bind_to_blender_bind(n_bind)
            # force update is required to ensure the transforms are set properly in blender
            bpy.context.view_layer.update()

        return b_armature_obj

    def import_bone_bind(self, n_block, n_bind_store, b_armature_data, n_armature, b_parent_bone=None):
        """Adds a bone to the armature in edit mode."""
        # check that n_block is indeed a bone
        if not self.is_bone(n_block):
            return None
        # bone name
        bone_name = block_store.import_name(n_block)
        # create a new bone
        b_edit_bone = b_armature_data.edit_bones.new(bone_name)
        # store nif block for access from object mode
        self.name_to_block[b_edit_bone.name] = n_block
        # get the nif bone's armature space matrix (under the hood all bone space matrixes are multiplied together)
        n_bind = mathutils.Matrix(n_bind_store.get(n_block, NifFormat.Matrix44()).as_list()).transposed()
        # get transformation in blender's coordinate space
        b_bind = math.nif_bind_to_blender_bind(n_bind)

        # the following is a workaround because blender can no longer set matrices to bones directly
        tail, roll = bpy.types.Bone.AxisRollFromMatrix(b_bind.to_3x3())
        b_edit_bone.head = b_bind.to_translation()
        b_edit_bone.tail = tail + b_edit_bone.head
        b_edit_bone.roll = roll
        # link to parent
        if b_parent_bone:
            b_edit_bone.parent = b_parent_bone
        # import and parent bone children
        for n_child in n_block.children:
            self.import_bone_bind(n_child, n_bind_store, b_armature_data, n_armature, b_edit_bone)

    def guess_orientation(self, n_armature):
        """Analyze all bones' translations to see what the nif considers the 'forward' axis"""
        axis_indices = []
        ids = ["X", "Y", "Z", "-X", "-Y", "-Z"]
        for n_child in n_armature.children:
            self.get_forward_axis(n_child, axis_indices)
        # the forward index is the most common one from the list
        forward_ind = max(set(axis_indices), key=axis_indices.count)
        # move the up index one coordinate to the right, account for end of list
        up_ind = (forward_ind + 1) % len(ids)
        # return string identifiers
        return ids[forward_ind], ids[up_ind]

    def get_forward_axis(self, n_bone, axis_indices):
        """Helper function to get the forward axis of a bone"""
        # check that n_block is indeed a bone
        if not self.is_bone(n_bone):
            return None
        trans = n_bone.translation.as_tuple()
        trans_abs = tuple(abs(v) for v in trans)
        # do argmax
        max_coord_ind = max(zip(trans_abs, range(len(trans_abs))))[1]
        # now check the sign
        actual_value = trans[max_coord_ind]
        # handle sign accordingly so negative indices map to the negative identifiers in list
        if actual_value < 0:
            max_coord_ind += 3
        axis_indices.append(max_coord_ind)
        # move down the hierarchy
        for n_child in n_bone.children:
            self.get_forward_axis(n_child, axis_indices)

    @staticmethod
    def fix_bone_lengths(b_armature_data):
        """Sets all edit_bones to a suitable length."""
        for b_edit_bone in b_armature_data.edit_bones:
            # don't change root bones
            if b_edit_bone.parent:
                # take the desired length from the mean of all children's heads
                if b_edit_bone.children:
                    child_heads = mathutils.Vector()
                    for b_child in b_edit_bone.children:
                        child_heads += b_child.head
                    bone_length = (b_edit_bone.head - child_heads / len(b_edit_bone.children)).length
                    if bone_length < 0.01:
                        bone_length = 0.25
                # end of a chain
                else:
                    bone_length = b_edit_bone.parent.length
                b_edit_bone.length = bone_length

    def mark_armatures_bones(self, ni_block):
        """Mark armatures and bones by peeking into NiSkinInstance blocks."""
        # case where we import skeleton only,
        # or importing an Oblivion or Fallout 3 skeleton:
        # do all NiNode's as bones
        if NifOp.props.process == "SKELETON_ONLY" or \
                (NifData.data.version in (0x14000005, 0x14020007) and os.path.basename(NifOp.props.filepath).lower() in ('skeleton.nif', 'skeletonbeast.nif')):

            if not isinstance(ni_block, NifFormat.NiNode):
                raise io_scene_niftools.utils.logging.NifError("Cannot import skeleton: root is not a NiNode")

            # for morrowind, take the Bip01 node to be the skeleton root
            if NifData.data.version == 0x04000002:
                skelroot = ni_block.find(block_name='Bip01', block_type=NifFormat.NiNode)
                if not skelroot:
                    skelroot = ni_block
            else:
                skelroot = ni_block
            if skelroot not in self.dict_armatures:
                self.dict_armatures[skelroot] = []
            NifLog.info(f"Selecting node '{skelroot.name}' as skeleton root")
            # add bones
            self.populate_bone_tree(skelroot)
            return  # done!

        # attaching to selected armature -> first identify armature and bones
        elif NifOp.props.process == "GEOMETRY_ONLY" and not self.dict_armatures:
            b_armature_obj = bpy.context.selected_objects[0]
            skelroot = ni_block.find(block_name=b_armature_obj.name)
            if not skelroot:
                skelroot = ni_block
                # raise nif_utils.NifError(f"nif has no armature '{b_armature_obj.name}'")
            NifLog.debug(f"Identified '{skelroot.name}' as armature")
            self.dict_armatures[skelroot] = []
            for bone_name in b_armature_obj.data.bones.keys():
                # blender bone naming -> nif bone naming
                nif_bone_name = block_store_export.get_bone_name_for_nif(bone_name)
                # find a block with bone name
                bone_block = skelroot.find(block_name=nif_bone_name)
                # add it to the name list if there is a bone with that name
                if bone_block:
                    NifLog.info(f"Identified nif block '{nif_bone_name}' with bone '{bone_name}' in selected armature")
                    self.dict_armatures[skelroot].append(bone_block)
                    self.complete_bone_tree(bone_block, skelroot)

        # search for all NiTriShape or NiTriStrips blocks...
        if isinstance(ni_block, NifFormat.NiTriBasedGeom):
            # yes, we found one, get its skin instance
            if ni_block.is_skin():
                NifLog.debug(f"Skin found on block '{ni_block.name}'")
                # it has a skin instance, so get the skeleton root
                # which is an armature only if it's not a skinning influence
                # so mark the node to be imported as an armature
                skininst = ni_block.skin_instance
                skelroot = skininst.skeleton_root
                if NifOp.props.process == "EVERYTHING":
                    if skelroot not in self.dict_armatures:
                        self.dict_armatures[skelroot] = []
                        NifLog.debug(f"'{skelroot.name}' is an armature")
                elif NifOp.props.process == "GEOMETRY_ONLY":
                    if skelroot not in self.dict_armatures:
                        raise io_scene_niftools.utils.logging.NifError(f"Nif structure incompatible with '{b_armature_obj.name}' as armature: node '{ni_block.name}' has '{skelroot.name}' as armature")

                for boneBlock in skininst.bones:
                    # boneBlock can be None; see pyffi issue #3114079
                    if not boneBlock:
                        continue
                    if boneBlock not in self.dict_armatures[skelroot]:
                        self.dict_armatures[skelroot].append(boneBlock)
                        NifLog.debug(f"'{boneBlock.name}' is a bone of armature '{skelroot.name}'")
                    # now we "attach" the bone to the armature:
                    # we make sure all NiNodes from this bone all the way
                    # down to the armature NiNode are marked as bones
                    self.complete_bone_tree(boneBlock, skelroot)

                # mark all nodes as bones
                self.populate_bone_tree(skelroot)
        # continue down the tree
        for child in ni_block.get_refs():
            if not isinstance(child, NifFormat.NiAVObject):
                continue  # skip blocks that don't have transforms
            self.mark_armatures_bones(child)

    def populate_bone_tree(self, skelroot):
        """Add all of skelroot's bones to its dict_armatures list."""
        for bone in skelroot.tree():
            if bone is skelroot:
                continue
            if not isinstance(bone, NifFormat.NiNode):
                continue
            if isinstance(bone, NifFormat.NiLODNode):
                # LOD nodes are never bones
                continue
            if bone not in self.dict_armatures[skelroot]:
                self.dict_armatures[skelroot].append(bone)
                NifLog.debug(f"'{bone.name}' marked as extra bone of armature '{skelroot.name}'")

    def complete_bone_tree(self, bone, skelroot):
        """Make sure that the complete hierarchy from bone up to skelroot is marked in dict_armatures."""
        # we must already have marked both as a bone
        assert skelroot in self.dict_armatures  # debug
        assert bone in self.dict_armatures[skelroot]  # debug
        # get the node parent, this should be marked as an armature or as a bone
        boneparent = bone._parent
        if boneparent != skelroot:
            # parent is not the skeleton root
            if boneparent not in self.dict_armatures[skelroot]:
                # neither is it marked as a bone: so mark the parent as a bone
                self.dict_armatures[skelroot].append(boneparent)
                # store the coordinates for realignement autodetection 
                NifLog.debug(f"'{boneparent.name}' is a bone of armature '{skelroot.name}'")
            # now the parent is marked as a bone
            # recursion: complete the bone tree,
            # this time starting from the parent bone
            self.complete_bone_tree(boneparent, skelroot)

    def is_bone(self, ni_block):
        """Tests a NiNode to see if it has been marked as a bone."""
        if ni_block:
            for bones in self.dict_armatures.values():
                if ni_block in bones:
                    return True

    def is_armature_root(self, ni_block):
        """Tests a block to see if it's an armature."""
        if isinstance(ni_block, NifFormat.NiNode):
            return ni_block in self.dict_armatures
