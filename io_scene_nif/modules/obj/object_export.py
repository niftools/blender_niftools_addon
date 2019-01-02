"""This script contains helper methods to export objects."""

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
import mathutils
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature, obj
from io_scene_nif.modules.animation.animation_export import Animation
from io_scene_nif.modules.armature.armature_export import Armature
from io_scene_nif.modules.collision.collision_export import Collision
from io_scene_nif.modules.geometry.mesh.mesh_export import MeshHelper
from io_scene_nif.modules.obj import blocks
from io_scene_nif.modules.obj.blocks import BlockRegistry
from io_scene_nif.modules.obj.object_types import lod_export
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class ObjectHelper:

    def __init__(self):
        self.armature_helper = Armature()
        self.collison_helper = Collision()
        self.mesh_helper = MeshHelper()
        self.animation_helper = Animation()

    """Export a blender object ob of the type mesh, child of nif block
    parent_block, as NiTriShape and NiTriShapeData blocks, possibly
    along with some NiTexturingProperty, NiSourceTexture,
    NiMaterialProperty, and NiAlphaProperty blocks. We export one
    trishape block per mesh material. We also export vertex weights.

    The parameter trishape_name passes on the name for meshes that
    should be exported as a single mesh."""
    @staticmethod
    def create_ninode(b_obj=None):
        # trivial case first
        if not b_obj:
            return BlockRegistry.create_block("NiNode")

        # exporting an object, so first create node of correct type
        # TODO [object] rework to get node type from nif format based on custom value?
        try:
            n_node_type = b_obj.getProperty("Type").data
        except (RuntimeError, AttributeError, NameError):
            n_node_type = "NiNode"

        n_node = BlockRegistry.create_block(n_node_type, b_obj)
        # customize the node data, depending on type
        if n_node_type == "NiLODNode":
            lod_export.export_range_lod_data(n_node, b_obj)

        # return the node
        return n_node

    @staticmethod
    def get_exported_objects():
        """Return a list of exported objects."""
        exported_objects = []
        # iterating over blocks.DICT_BLOCKS.itervalues() will count some objects twice
        for b_obj in blocks.DICT_BLOCKS.values():
            # skip empty objects
            if b_obj is None:
                continue
            # detect doubles
            if b_obj in exported_objects:
                continue
            # append new object
            exported_objects.append(b_obj)
        # return the list of unique exported objects
        return exported_objects

    def export_node(self, b_obj, space, parent_block, node_name):
        """Export a mesh/armature/empty object b_obj as child of parent_block.
        Export also all children of b_obj.

        - space is 'none', 'worldspace', or 'localspace', and determines
          relative to what object the transformation should be stored.
        - parent_block is the parent nif block of the object (None for the
          root node)
        - for the root node, b_obj is None, and node_name is usually the base
          filename (either with or without extension)

        :param space:
        :param parent_block:
        :param b_obj:
        :param node_name: The name of the node to be exported.
        :type node_name: :class:`str`
        """
        # b_obj_type: determine the block type
        #          (None, 'MESH', 'EMPTY' or 'ARMATURE')
        # b_obj_ipo:  object animation ipo
        # node:    contains new NifFormat.NiNode instance
        export_types = ('EMPTY', 'MESH', 'ARMATURE')
        if b_obj is None:
            selected_exportable_objects = [b_obj for b_obj in bpy.context.selected_objects if b_obj.type in export_types]
            if len(selected_exportable_objects) == 0:
                raise nif_utils.NifError("Selected objects ({0}) are not exportable.".format(str(bpy.context.selected_objects)))

            for root_object in [b_obj for b_obj in bpy.context.selected_objects if b_obj.type in export_types]:
                while root_object.parent:
                    root_object = root_object.parent

            # root node
            if root_object.type == 'ARMATURE':
                b_obj = root_object

            # root node
            if b_obj is None:
                assert parent_block is None  # debug
                node = self.create_ninode()
                b_obj_type = None
                b_obj_ipo = None
            else:
                b_obj_type = b_obj.type
                assert (b_obj_type in export_types)  # debug
                assert (parent_block is None)  # debug
                b_obj_ipo = b_obj.animation_data  # get animation data
                b_obj_children = b_obj.children
                node_name = b_obj.name

        elif b_obj.name != parent_block.name.decode() and b_obj.parent is not None:
            # -> empty, b_mesh, or armature
            b_obj_type = b_obj.type
            assert (b_obj_type in export_types)  # debug
            assert parent_block  # debug
            b_obj_ipo = b_obj.animation_data  # get animation data
            b_obj_children = b_obj.children

        elif b_obj.name != parent_block.name.decode() and b_obj.type != 'ARMATURE':
            # -> empty, b_mesh, or armature
            b_obj_type = b_obj.type
            assert b_obj_type in ['EMPTY', 'MESH']  # debug
            assert parent_block  # debug
            b_obj_ipo = b_obj.animation_data  # get animation data
            b_obj_children = b_obj.children

        else:
            return None

        # TODO [collision] Extract as collision check
        if node_name == 'RootCollisionNode':
            # -> root collision node (can be mesh or empty)
            # TODO [object] do we need to fix this stuff on export?
            # b_obj.draw_bounds_type = 'POLYHEDERON'
            # b_obj.draw_type = 'BOUNDS'
            # b_obj.show_wire = True
            self.collison_helper.export_collision(b_obj, parent_block)
            for child in b_obj.children:
                ObjectHelper.export_node(child, 'localspace', node, None)
            return None  # done; stop here

        elif b_obj_type == 'MESH' and b_obj.show_bounds and b_obj.name.lower().startswith('bsbound'):
            # add a bounding box
            self.collison_helper.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=True)
            return None  # done; stop here

        elif b_obj_type == 'MESH' and b_obj.show_bounds and b_obj.name.lower().startswith("bounding box"):
            # Morrowind bounding box
            self.collison_helper.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=False)
            return None  # done; stop here

        elif b_obj_type == 'MESH':
            # -> mesh data.
            # If this has children or animations or more than one material it gets wrapped in a purpose made NiNode.
            has_ipo = b_obj_ipo and len(b_obj_ipo.getCurves()) > 0
            has_children = len(b_obj_children) > 0
            is_multimaterial = len(set([f.material_index for f in b_obj.data.polygons])) > 1

            # determine if object tracks camera
            has_track = False
            for constr in b_obj.constraints:
                if constr.type == 'TRACK_TO':
                    has_track = True
                    break
                # does geom have priority value in NULL constraint?
                elif constr.name[:9].lower() == "priority:":
                    armature.DICT_BONE_PRIORITIES[armature.get_bone_name_for_nif(b_obj.name)] = int(constr.name[9:])

            is_collision = b_obj.game.use_collision_bounds
            if is_collision:
                self.collison_helper.export_collision(b_obj, parent_block)
                return None  # done; stop here
            elif has_ipo or has_children or is_multimaterial or has_track:
                # mesh ninode for the hierarchy to work out
                if not has_track:
                    node = BlockRegistry.create_block('NiNode', b_obj)
                else:
                    node = BlockRegistry.create_block('NiBillboardNode', b_obj)
            else:
                # don't create intermediate ninode for this guy
                self.mesh_helper.export_tri_shapes(b_obj, space, parent_block, node_name)
                # we didn't create a ninode, return nothing
                return None

        elif b_obj is not None:
            # -> everything else (empty/armature) is a regular node
            node = self.create_ninode(b_obj)
            # does node have priority value in NULL constraint?
            for constr in b_obj.constraints:
                if constr.name[:9].lower() == "priority:":
                    armature.DICT_BONE_PRIORITIES[armature.get_bone_name_for_nif(b_obj.name)] = int(constr.name[9:])

        # set transform on trishapes rather than on NiNode for skinned meshes
        # this fixes an issue with clothing slots
        if b_obj_type == 'MESH':
            if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                if b_obj_ipo:
                    # mesh with armature parent should not have animation!
                    NifLog.warn("Mesh {0} is skinned but also has object animation. "
                                "The nif format does not support this, ignoring object animation.".format(b_obj.name))
                    b_obj_ipo = None
                trishape_space = space
                space = 'none'
            else:
                trishape_space = 'none'

        # make it child of its parent in the nif, if it has one
        if parent_block:
            parent_block.add_child(node)

        # and fill in this node's non-trivial values
        node.name = get_full_name(node_name)

        # default node flags
        if b_obj_type in export_types:
            if b_obj_type is 'EMPTY' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            if b_obj_type is 'MESH' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags == 0 and b_obj.parent is None:
                node.flags = b_obj.niftools.objectflags
            else:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    node.flags = 0x000E
                elif NifOp.props.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                    node.flags = 0x0010
                elif NifOp.props.game is 'EMPIRE_EARTH_II':
                    node.flags = 0x0002
                elif NifOp.props.game is 'DIVINITY_2':
                    node.flags = 0x0310
                else:
                    node.flags = 0x000C  # morrowind

        set_object_matrix(b_obj, space, node)

        if b_obj:
            # export animation
            if b_obj_ipo:
                if any(b_obj_ipo[b_channel] for b_channel in (Ipo.OB_LOCX, Ipo.OB_ROTX, Ipo.OB_SCALEX)):
                    self.animation_helper.export_keyframes(b_obj_ipo, space, node)
                self.animation_helper.export_object_vis_controller(b_obj, node)
            # if it is a mesh, export the mesh as trishape children of this ninode
            if b_obj.type == 'MESH':
                # see definition of trishape_space above
                self.mesh_helper.export_tri_shapes(b_obj, trishape_space, node)

            # if it is an armature, export the bones as ninode children of this ninode
            elif b_obj.type == 'ARMATURE':
                self.armature_helper.export_bones(b_obj, node)

            # export all children of this empty/mesh/armature/bone object as children of this NiNode
            self.export_children(b_obj, node)

        return node

    def export_children(self, b_obj, parent_block):
        """Export all children of blender object b_obj as children of
        parent_block."""
        # loop over all obj's children
        for b_obj_child in b_obj.children:
            # is it a regular node?
            if b_obj_child.type in ['MESH', 'EMPTY', 'ARMATURE']:
                if b_obj.type != 'ARMATURE':
                    # not parented to an armature
                    # TODO [object] Should we use the return value
                    self.export_node(b_obj_child, 'localspace', parent_block, b_obj_child.name)
                else:
                    # this object is parented to an armature
                    # we should check whether it is really parented to the
                    # armature using vertex weights
                    # or whether it is parented to some bone of the armature
                    parent_bone_name = b_obj_child.parent_bone
                    if parent_bone_name == "":
                        self.export_node(b_obj_child, 'localspace', parent_block, b_obj_child.name)
                    else:
                        # we should parent the object to the bone instead of
                        # to the armature
                        # so let's find that bone!
                        nif_bone_name = get_full_name(parent_bone_name)
                        for bone_block in blocks.DICT_BLOCKS:
                            if isinstance(bone_block, NifFormat.NiNode) and bone_block.name.decode() == nif_bone_name:
                                # ok, we should parent to block
                                # instead of to parent_block
                                # two problems to resolve:
                                #   - blender bone matrix is not the exported
                                #     bone matrix!
                                #   - blender objects parented to bone have
                                #     extra translation along the Y axis
                                #     with length of the bone ("tail")
                                # this is handled in the get_object_srt function
                                self.export_node(b_obj_child, 'localspace', bone_block, b_obj_child.name)
                                break
                        else:
                            assert False  # BUG!


def rebuild_full_names():
    """Recovers the full object names from the text buffer and rebuilds
    the names dictionary."""
    # TODO [object] get objects to store their own names.
    try:
        namestxt = bpy.data.texts['FullNames']
    except KeyError:
        return
    for b_textline in namestxt.lines:
        line = b_textline.body
        if len(line) > 0:
            name, fullname = line.split(';')
            obj.DICT_NAMES[name] = fullname


def get_unique_name(b_name):
    """Returns an unique name for use in the NIF file, from the name of a
    Blender object.

    :param b_name: Name of object as in blender.
    :type b_name: :class:`str`

    """
    # TODO [object] Refactor and simplify this code.
    unique_name = "unnamed"
    if b_name:
        unique_name = b_name
    # blender bone naming -> nif bone naming
    unique_name = armature.get_bone_name_for_nif(unique_name)
    # ensure uniqueness
    if unique_name in obj.BLOCK_NAMES_LIST or unique_name in list(obj.DICT_NAMES.values()):
        unique_int = 0
        old_name = unique_name
        while unique_name in obj.BLOCK_NAMES_LIST or unique_name in list(obj.DICT_NAMES.values()):
            unique_name = "%s.%02d" % (old_name, unique_int)
            unique_int += 1
    obj.BLOCK_NAMES_LIST.append(unique_name)
    obj.DICT_NAMES[b_name] = unique_name
    return unique_name


def get_full_name(b_name):
    """Returns the original imported name if present, or the name by which
    the object was exported already.

    :param b_name:
    """
    # TODO [object] Refactor and simplify this code.
    try:
        return obj.DICT_NAMES[b_name]
    except KeyError:
        return get_unique_name(b_name)


def set_object_matrix(b_obj, space, block):
    """Set a block's transform matrix to an object's transformation matrix in rest pose."""
    # decompose
    n_scale, n_rot_mat33, n_trans_vec = get_object_srt(b_obj, space)

    # and fill in the values
    block.translation.x = n_trans_vec[0]
    block.translation.y = n_trans_vec[1]
    block.translation.z = n_trans_vec[2]
    block.rotation.m_11 = n_rot_mat33[0][0]
    block.rotation.m_21 = n_rot_mat33[0][1]
    block.rotation.m_31 = n_rot_mat33[0][2]
    block.rotation.m_12 = n_rot_mat33[1][0]
    block.rotation.m_22 = n_rot_mat33[1][1]
    block.rotation.m_32 = n_rot_mat33[1][2]
    block.rotation.m_13 = n_rot_mat33[2][0]
    block.rotation.m_23 = n_rot_mat33[2][1]
    block.rotation.m_33 = n_rot_mat33[2][2]
    block.velocity.x = 0.0
    block.velocity.y = 0.0
    block.velocity.z = 0.0
    block.scale = n_scale

    return n_scale, n_rot_mat33, n_trans_vec


def get_object_matrix(b_obj, space):
    """Get an object's matrix as NifFormat.Matrix44

    Note: for objects parented to bones, this will return the transform
    relative to the bone parent head in nif coordinates (that is, including
    the bone correction); this differs from getMatrix which
    returns the transform relative to the armature."""
    n_scale, n_rot_mat33, n_trans_vec = get_object_srt(b_obj, space)
    matrix = NifFormat.Matrix44()

    matrix.m_11 = n_rot_mat33[0][0] * n_scale
    matrix.m_21 = n_rot_mat33[0][1] * n_scale
    matrix.m_31 = n_rot_mat33[0][2] * n_scale
    matrix.m_12 = n_rot_mat33[1][0] * n_scale
    matrix.m_22 = n_rot_mat33[1][1] * n_scale
    matrix.m_32 = n_rot_mat33[1][2] * n_scale
    matrix.m_13 = n_rot_mat33[2][0] * n_scale
    matrix.m_23 = n_rot_mat33[2][1] * n_scale
    matrix.m_33 = n_rot_mat33[2][2] * n_scale
    matrix.m_14 = n_trans_vec[0]
    matrix.m_24 = n_trans_vec[1]
    matrix.m_34 = n_trans_vec[2]

    matrix.m_41 = 0.0
    matrix.m_42 = 0.0
    matrix.m_43 = 0.0
    matrix.m_44 = 1.0

    return matrix


def get_object_srt(b_obj, space='localspace'):
    """Find scale, rotation, and translation components of an object in
    the rest pose. Returns a triple (bs, br, bt), where bs
    is a scale float, br is a 3x3 rotation matrix, and bt is a
    translation vector. It should hold that

    ob.getMatrix(space) == bs * br * bt

    Note: for objects parented to bones, this will return the transform
    relative to the bone parent head including bone correction.

    space is either 'none' (gives identity transform) or 'localspace'"""
    # TODO [object] remove the space argument, always do local space
    # handle the trivial case first
    if space == 'none':
        return (1.0,
                mathutils.Matrix([[1, 0, 0],
                                  [0, 1, 0],
                                  [0, 0, 1]]),
                mathutils.Vector([0, 0, 0]))

    assert (space == 'localspace')

    # now write out spaces
    if isinstance(b_obj, bpy.types.Bone):
        # bones, get the rest matrix
        matrix = Armature.get_bone_rest_matrix(b_obj, 'BONESPACE')

    else:
        # TODO [armature] Move to armature module

        matrix = b_obj.matrix_local.copy()
        bone_parent_name = b_obj.parent_bone

        # if there is a bone parent then the object is parented then get the matrix relative to the bone parent head
        if bone_parent_name:
            # so v * O * T * B' = v * Z * B
            # where B' is the Blender bone matrix in armature
            # space, T is the bone tail translation, O is the object
            # matrix (relative to the head), and B is the nif bone matrix;
            # we wish to find Z

            # b_obj.getMatrix('localspace')
            # gets the object local transform matrix, relative
            # to the armature!! (not relative to the bone)
            # so at this point, matrix = O * T * B'
            # hence it must hold that matrix = Z * B,
            # or equivalently Z = matrix * B^{-1}

            # now, B' = X * B, so B^{-1} = B'^{-1} * X
            # hence Z = matrix * B'^{-1} * X

            # first multiply with inverse of the Blender bone matrix
            bone_parent = b_obj.parent.data.bones[bone_parent_name]
            boneinv = mathutils.Matrix(bone_parent.matrix['ARMATURESPACE'])
            boneinv.invert()
            matrix = matrix * boneinv
            # now multiply with the bone correction matrix X
            try:
                extra = mathutils.Matrix(Armature.get_bone_extra_matrix_inv(bone_parent_name))
                extra.invert()
                matrix = matrix * extra
            except KeyError:
                # no extra local transform
                pass

    try:
        return nif_utils.decompose_srt(matrix)
    except nif_utils.NifError:  # non-uniform scaling
        raise nif_utils.NifError("Non-uniform scaling on bone '%s' not supported. "
                                 "This could be a bug... No workaround. :( Post your blend!" % b_obj.name)
