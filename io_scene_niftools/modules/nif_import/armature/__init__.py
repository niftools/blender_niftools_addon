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
        self.pose_store = {}
        self.bind_store = {}
        self.skinned = False
        self.n_armature = None

    def store_pose_matrices(self, n_node, n_root):
        """Stores the nif armature space matrix of a node tree"""
        # check that n_block is indeed a bone
        if not self.is_bone(n_node):
            return None
        NifLog.debug(f"Storing pose matrix for {n_node.name}")
        # calculate the transform relative to root, ie. turn nif local into nif armature space
        self.pose_store[n_node] = n_node.get_transform(n_root)
        # move down the hierarchy
        for n_child in n_node.children:
            self.store_pose_matrices(n_child, n_root)

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

        # for ZT2 elephant, the skin transform is the inverse of the geom's armature space transform
        # this gives a straight rest pose for MW too
        # return n_bone.get_transform().get_inverse(fast=False) * geom.skin_instance.data.get_transform().get_inverse(fast=False)
        # however, this conflicts with send_geometries_to_bind_position for MW meshes, so stick to this now
        return n_bone.get_transform().get_inverse(fast=False) * geom.get_transform(n_root)

    def bones_iter(self, skin_instance):
        # might want to make sure that bone_list includes no dupes too to avoid breaking the first mesh
        for bonenode, bonedata in zip(skin_instance.bones, skin_instance.data.bone_list):
            # bonenode can be None; see pyffi issue #3114079
            if bonenode:
                yield bonenode, bonedata

    def store_bind_matrices(self, n_armature):
        """Process all geometries' skin instances to reconstruct a bind pose from their inverse bind matrices"""
        # improved from pyffi's send_geometries_to_bind_position & send_bones_to_bind_position
        NifLog.debug(f"Calculating bind for {n_armature.name}")
        # prioritize geometries that have most nodes in their skin instance
        geoms = sorted(self.get_skinned_geometries(n_armature), key=lambda g: g.skin_instance.num_bones, reverse=True)
        NifLog.debug(f"Found {len(geoms)} skinned geometries")
        for geom in geoms:
            NifLog.debug(f"Checking skin of {geom.name}")
            skininst = geom.skin_instance
            for bonenode, bonedata in self.bones_iter(skininst):
                # make sure all bone data of shared bones coincides
                # see if the bone has been used by a previous skin instance
                if bonenode in self.bind_store:
                    # get the bind pose that has been stored
                    diff = (bonedata.get_transform()
                            * self.bind_store[bonenode]
                            # * geom.skin_instance.data.get_transform())  use this if relative to skin instead of geom
                            * geom.get_transform(n_armature).get_inverse(fast=False))
                    # there is a difference between the two geometries' bind poses
                    if not diff.is_identity():
                        NifLog.debug(f"Fixing {geom.name} bind position")
                        # update the skin for all bones of the new geom
                        for bonenode, bonedata in self.bones_iter(skininst):
                            NifLog.debug(f"Transforming bind of {bonenode.name}")
                            bonedata.set_transform(diff.get_inverse(fast=False) * bonedata.get_transform())
                    # transforming verts helps with nifs where the skins differ, eg MW vampire or WLP2 Gastornis
                    for vert in geom.data.vertices:
                        newvert = vert * diff
                        vert.x = newvert.x
                        vert.y = newvert.y
                        vert.z = newvert.z
                    for norm in geom.data.normals:
                        newnorm = norm * diff.get_matrix_33()
                        norm.x = newnorm.x
                        norm.y = newnorm.y
                        norm.z = newnorm.z
                    break
            # store bind pose
            for bonenode, bonedata in self.bones_iter(skininst):
                NifLog.debug(f"Stored {geom.name} bind position")
                self.bind_store[bonenode] = self.get_skin_bind(bonedata, geom, n_armature)

        NifLog.debug("Storing non-skeletal bone poses")
        self.fix_pose(n_armature, n_armature)

    def fix_pose(self, n_node, n_root):
        """reposition non-skeletal bones to maintain their local orientation to their skeletal parents"""
        for n_child_node in n_node.children:
            # only process nodes
            if not isinstance(n_child_node, NifFormat.NiNode):
                continue
            if n_child_node not in self.bind_store and n_child_node in self.pose_store:
                NifLog.debug(f"Calculating bind pose for non-skeletal bone {n_child_node.name}")
                # get matrices for n_node (the parent) - fallback to getter if it is not in the store
                n_armature_pose = self.pose_store.get(n_node, n_node.get_transform(n_root))
                # get bind of parent node or pose if it has no bind pose
                n_armature_bind = self.bind_store.get(n_node, n_armature_pose)

                # the child must have a pose, no need for a fallback
                n_child_armature_pose = self.pose_store[n_child_node]
                # get the relative transform of n_child_node from pose * inverted parent pose
                n_child_local_pose = n_child_armature_pose * n_armature_pose.get_inverse(fast=False)
                # get object space transform by multiplying with bind of parent bone
                self.bind_store[n_child_node] = n_child_local_pose * n_armature_bind
            # move down the hierarchy
            self.fix_pose(n_child_node, n_root)

    def import_armature(self, n_armature):
        """Scans an armature hierarchy, and returns a whole armature.
        This is done outside the normal node tree scan to allow for positioning
        of the bones before skins are attached."""

        armature_name = block_store.import_name(n_armature)
        b_armature_data = bpy.data.armatures.new(armature_name)
        b_armature_data.display_type = 'STICK'

        # use heuristics to determine a suitable orientation, if requested
        if NifOp.props.guess_armature_orientation:
            forward, up = self.guess_orientation(n_armature)
        else:
            forward, up = (NifOp.props.armature_axis_forward, NifOp.props.armature_axis_up)
        # pass them to the matrix utility
        math.set_bone_orientation(forward, up)
        # store axis orientation for export
        b_armature_data.niftools.axis_forward = forward
        b_armature_data.niftools.axis_up = up
        b_armature_obj = Object.create_b_obj(n_armature, b_armature_data)
        b_armature_obj.show_in_front = True

        # store the original pose & bind matrices for all nodes
        self.pose_store = {}
        self.bind_store = {}
        self.store_pose_matrices(n_armature, n_armature)
        self.store_bind_matrices(n_armature)

        # make armature editable and create bones
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        for n_child in n_armature.children:
            self.import_bone_bind(n_child, b_armature_data, n_armature)
        self.fix_bone_lengths(b_armature_data)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # The armature has been created in editmode,
        # now we are ready to set the bone keyframes and store the bones' long names.
        if NifOp.props.animation:
            self.transform_anim.get_bind_data(b_armature_obj)

        for bone_name, b_bone in b_armature_obj.data.bones.items():
            n_block = self.name_to_block[bone_name]
            # the property is only available from object mode!
            block_store.store_longname(b_bone, safe_decode(n_block.name))
            if NifOp.props.animation:
                self.transform_anim.import_transforms(n_block, b_armature_obj, bone_name)

        # import pose
        for b_name, n_block in self.name_to_block.items():
            n_pose = self.pose_store[n_block]
            b_pose_bone = b_armature_obj.pose.bones[b_name]
            n_bind = math.nifformat_to_mathutils_matrix(n_pose)
            b_pose_bone.matrix = math.nif_bind_to_blender_bind(n_bind)
            # force update is required after each pbone to ensure the transforms are set properly in blender
            bpy.context.view_layer.update()

        return b_armature_obj

    def import_bone_bind(self, n_block, b_armature_data, n_armature, b_parent_bone=None):
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
        n_bind = math.nifformat_to_mathutils_matrix(self.bind_store.get(n_block, NifFormat.Matrix44()))
        # get transformation in blender's coordinate space
        b_bind = math.nif_bind_to_blender_bind(n_bind)

        # set the bone matrix - but set the tail first to prevent issues with zero-length bone
        b_edit_bone.tail = mathutils.Vector([0, 0, 1])
        b_edit_bone.matrix = b_bind
        # link to parent
        if b_parent_bone:
            b_edit_bone.parent = b_parent_bone
        # import and parent bone children
        for n_child in n_block.children:
            self.import_bone_bind(n_child, b_armature_data, n_armature, b_edit_bone)

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
        # force import of nodes as bones, even if no geometries are present
        if NifOp.props.process == "SKELETON_ONLY":
            self.skinned = True
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
