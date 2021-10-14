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
from io_scene_niftools.utils.blocks import safe_decode
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.singleton import NifOp, NifData


class Armature:

    def __init__(self):
        self.transform_anim = TransformAnimation()
        # to get access to the nif bone in object mode
        self.name_to_block = {}
        self.skinned = False
        self.n_armature = None

    def store_pose_matrix(self, n_node, armature_space_pose_store, n_root):
        """Stores the nif armature space matrix of a node tree"""
        # check that n_block is indeed a bone
        if not self.is_bone(n_node):
            return None
        NifLog.debug(f"Storing pose matrix for {n_node.name}")
        # calculate the transform relative to root, ie. turn nif local into nif armature space
        armature_space_pose_store[n_node] = n_node.get_transform(n_root)
        # move down the hierarchy
        for n_child in n_node.children:
            self.store_pose_matrix(n_child, armature_space_pose_store, n_root)

    def get_skinned_geometries(self, n_root):
        """Yield all children in n_root's tree that have skinning"""
        # search for all NiTriShape or NiTriStrips blocks...
        for n_block in n_root.tree(block_type=NifFormat.NiTriBasedGeom):
            # yes, we found one, does it have skinning?
            if n_block.is_skin():
                yield n_block

    def get_skin_bind(self, n_bone, geom, n_root):
        """Get armature space bind matrix for skin partition bone's inverse bind matrix"""
        # get the bind pose from the skin data
        # NiSkinData stores the inverse bind (=rest) pose for each bone, in armature space
        # todo [armature] not sure if the skin instance transform is in there as well as the parent node's transform
        return n_bone.get_transform().get_inverse(fast=False) * geom.get_transform(n_root)

    def import_pose(self, n_armature):
        """Process all geometries' skin instances to reconstruct a bind pose from their inverse bind matrices"""
        # improved from pyffi's send_bones_to_bind_position
        NifLog.debug(f"Calculating pose for {n_armature.name}")
        armature_space_bind_store = {}
        armature_space_pose_store = {}
        # store the original pose matrix for all nodes
        self.store_pose_matrix(n_armature, armature_space_pose_store, n_armature)

        # prioritize geometries that have most nodes in their skin instance
        geoms = sorted(self.get_skinned_geometries(n_armature), key=lambda g: g.skin_instance.num_bones, reverse=True)
        NifLog.debug(f"Found {len(geoms)} skinned geometries")
        for geom in geoms:
            NifLog.debug(f"Checking skin of {geom.name}")
            skininst = geom.skin_instance
            skindata = skininst.data
            for bonenode, bonedata in zip(skininst.bones, skindata.bone_list):
                # bonenode can be None; see pyffi issue #3114079
                if not bonenode:
                    continue
                # make sure all bone data of shared bones coincides
                # see if the bone has been used by a previous skin instance
                if bonenode in armature_space_bind_store:
                    # get the bind pose that has been stored
                    diff = armature_space_bind_store[bonenode] - self.get_skin_bind(bonedata, geom, n_armature)
                    if diff.sup_norm() > 1e-3:
                        NifLog.debug(
                            f"The bind position of mesh {geom.name} differs from previous meshes. "
                            f"Bone {bonenode.name} will be sent to a position matching only one of these")
                else:
                    # new bone - add it now
                    NifLog.debug(f"Found bind position data for {bonenode.name}")
                    armature_space_bind_store[bonenode] = self.get_skin_bind(bonedata, geom, n_armature)
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
            block_store.store_longname(b_bone, safe_decode(n_block.name))
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

    @staticmethod
    def argmax(values):
        """Return the index of the max value in values"""
        return max(zip(values, range(len(values))))[1]

    def get_forward_axis(self, n_bone, axis_indices):
        """Helper function to get the forward axis of a bone"""
        # check that n_block is indeed a bone
        if not self.is_bone(n_bone):
            return None
        trans = n_bone.translation.as_tuple()
        trans_abs = tuple(abs(v) for v in trans)
        # get the index of the coordinate with the biggest absolute value
        max_coord_ind = self.argmax(trans_abs)
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

    def check_for_skin(self, n_root):
        """Checks all tri geometry for skinning, sets self.skinned accordingly"""
        # set these here once per run
        self.n_armature = None
        self.skinned = False
        for n_block in self.get_skinned_geometries(n_root):
            self.skinned = True
            NifLog.debug(f"{n_block.name} has skinning.")
            # one is enough to require an armature, so stop
            return
        NifLog.debug(f"Found no skinned geometries.")

    def is_bone(self, ni_block):
        """Tests a NiNode to see if it has been marked as a bone."""
        if isinstance(ni_block, NifFormat.NiNode):
            return self.skinned

    def is_armature_root(self, n_block):
        """Tests a block to see if it's an armature."""
        if isinstance(n_block, NifFormat.NiNode):
            # we have skinning and are waiting for a suitable start node of the tree
            if self.skinned and not self.n_armature:
                # now store it as the nif armature's root
                self.n_armature = n_block
                return True
