"""This script contains helper methods to export objects."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules import armature
from io_scene_nif.modules.geometry.mesh.mesh_export import Mesh
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.modules.object.object_types import lod_export
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class Object:

    def __init__(self, parent):
        self.nif_export = parent
        self.mesh_helper = Mesh(parent=parent)

    def export_root_node(self, filebase):
        """ Exports a nif's root node; use blender root if there is only one, else create a meta root """
        # TODO [collsion] detect root collision -> root collision node (can be mesh or empty)
        #     self.nif_export.collisionhelper.export_collision(b_obj, n_parent)
        #     return None  # done; stop here

        # there is only one root object so that will be our final root
        if len(self.nif_export.root_objects) == 1:
            n_root = self.export_node(self.nif_export.root_objects[0], None)
        # there is more than one root object so we create a meta root
        else:
            n_root = self.create_ninode()
            n_root.name = "Scene Root"
            for b_obj in self.nif_export.root_objects:
                self.export_node(b_obj, n_root)
        # making root block a fade node
        root_type = self.nif_export.root_objects[0].niftools.rootnode
        if NifOp.props.game in ('FALLOUT_3', 'SKYRIM') and root_type == 'BSFadeNode':
            NifLog.info("Making root block a BSFadeNode")
            fade_root_block = NifFormat.BSFadeNode().deepcopy(n_root)
            fade_root_block.replace_global_node(n_root, fade_root_block)
            n_root = fade_root_block
        # various extra datas
        self.export_bsxflags_upb(n_root)
        self.export_weapon_location(n_root)
        self.export_inventory_marker(n_root)
        self.export_furniture_marker(n_root, filebase)
        return n_root

    # TODO [object][property] Move to object property
    def export_inventory_marker(self, n_root):
        if NifOp.props.game in ('SKYRIM',):
            for root_object in self.nif_export.root_objects:
                if root_object.niftools_bs_invmarker:
                    for extra_item in n_root.extra_data_list:
                        if isinstance(extra_item, NifFormat.BSInvMarker):
                            raise nif_utils.NifError("Multiple Items have Inventory marker data only one item may contain this data")
                    else:
                        n_extra_list = NifFormat.BSInvMarker()
                        n_extra_list.name = root_object.niftools_bs_invmarker[0].name.encode()
                        n_extra_list.rotation_x = root_object.niftools_bs_invmarker[0].bs_inv_x
                        n_extra_list.rotation_y = root_object.niftools_bs_invmarker[0].bs_inv_y
                        n_extra_list.rotation_z = root_object.niftools_bs_invmarker[0].bs_inv_z
                        n_extra_list.zoom = root_object.niftools_bs_invmarker[0].bs_inv_zoom
                        n_root.add_extra_data(n_extra_list)

    # TODO [object][type] Move to new object type
    def export_furniture_marker(self, n_root, filebase):
        # oblivion and Fallout 3 furniture markers
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') and filebase[:15].lower() == 'furnituremarker':
            # exporting a furniture marker for Oblivion/FO3
            try:
                furniturenumber = int(filebase[15:])
            except ValueError:
                raise nif_utils.NifError("Furniture marker has invalid number ({0}).\n"
                                         "Name your file 'furnituremarkerxx.nif' where xx is a number between 00 and 19.".format(filebase[
                                                                                                                            15:]))

            # create furniture marker block
            furnmark = block_store.create_block("BSFurnitureMarker")
            furnmark.name = "FRN"
            furnmark.num_positions = 1
            furnmark.positions.update_size()
            furnmark.positions[0].position_ref_1 = furniturenumber
            furnmark.positions[0].position_ref_2 = furniturenumber

            # create extra string data sgoKeep
            sgokeep = block_store.create_block("NiStringExtraData")
            sgokeep.name = "UPB"  # user property buffer
            sgokeep.string_data = "sgoKeep=1 ExportSel = Yes"  # Unyielding = 0, sgoKeep=1ExportSel = Yes

            # add extra blocks
            n_root.add_extra_data(furnmark)
            n_root.add_extra_data(sgokeep)

    # TODO [object][property] Move to object property
    def export_bsxflags_upb(self, root_block):
        # TODO [object][property] Fixme
        NifLog.info("Checking collision")
        # activate oblivion/Fallout 3 collision and physics
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            b_obj = self.nif_export.collisionhelper.has_collision()
            if b_obj:
                # enable collision
                bsx = block_store.create_block("BSXFlags")
                bsx.name = 'BSX'
                bsx.integer_data = b_obj.niftools.bsxflags
                root_block.add_extra_data(bsx)

                # many Oblivion nifs have a UPB, but export is disabled as
                # they do not seem to affect anything in the game
                if b_obj.niftools.upb:
                    upb = block_store.create_block("NiStringExtraData")
                    upb.name = 'UPB'
                    if b_obj.niftools.upb == '':
                        upb.string_data = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                    else:
                        upb.string_data = b_obj.niftools.upb.encode()
                    root_block.add_extra_data(upb)

    # TODO [object][property] Move to new object type
    def export_weapon_location(self, n_root):
        # export weapon location
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            b_obj = self.nif_export.root_objects[0]
            loc = b_obj.niftools.prn_location
            if loc != "NONE":
                # add string extra data
                prn = block_store.create_block("NiStringExtraData")
                prn.name = 'Prn'
                prn.string_data = self.nif_export.prn_dict[loc]
                n_root.add_extra_data(prn)

    # TODO [collision] Move to collision
    def update_rigid_bodies(self):
        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            n_rigid_bodies = [n_rigid_body for n_rigid_body in block_store.block_to_obj if isinstance(n_rigid_body, NifFormat.bhkRigidBody)]
            # update rigid body center of gravity and mass
            if self.nif_export.IGNORE_BLENDER_PHYSICS:
                # we are not using blender properties to set the mass
                # so calculate mass automatically first calculate distribution of mass
                total_mass = 0
                for n_block in n_rigid_bodies:
                    n_block.update_mass_center_inertia(solid=self.nif_export.EXPORT_OB_SOLID)
                    total_mass += n_block.mass

                # to avoid zero division error later (if mass is zero then this does not matter anyway)
                if total_mass == 0:
                    total_mass = 1

                # now update the mass ensuring that total mass is EXPORT_OB_MASS
                for n_block in n_rigid_bodies:
                    mass = self.nif_export.EXPORT_OB_MASS * n_block.mass / total_mass
                    # lower bound on mass
                    if mass < 0.0001:
                        mass = 0.05
                    n_block.update_mass_center_inertia(mass=mass, solid=self.nif_export.EXPORT_OB_SOLID)
            else:
                # using blender properties, so n_block.mass *should* have been set properly
                for n_block in n_rigid_bodies:
                    # lower bound on mass
                    if n_block.mass < 0.0001:
                        n_block.mass = 0.05
                    n_block.update_mass_center_inertia(mass=n_block.mass, solid=self.nif_export.EXPORT_OB_SOLID)

    def set_node_flags(self, b_obj, n_node):
        # default node flags
        b_obj_type = b_obj.type
        if b_obj_type in self.nif_export.export_types:
            if b_obj_type is 'EMPTY' and b_obj.niftools.objectflags != 0:
                n_node.flags = b_obj.niftools.objectflags
            if b_obj_type is 'MESH' and b_obj.niftools.objectflags != 0:
                n_node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags != 0:
                n_node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags == 0 and b_obj.parent is None:
                n_node.flags = b_obj.niftools.objectflags
            else:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    n_node.flags = 0x000E
                elif NifOp.props.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                    n_node.flags = 0x0010
                elif NifOp.props.game is 'EMPIRE_EARTH_II':
                    n_node.flags = 0x0002
                elif NifOp.props.game is 'DIVINITY_2':
                    n_node.flags = 0x0310
                else:
                    n_node.flags = 0x000C  # morrowind

    def export_node(self, b_obj, n_parent):
        """Export a mesh/armature/empty object b_obj as child of n_parent.
        Export also all children of b_obj.

        :param n_parent:
        :param b_obj:
        """

        if not b_obj:
            return None

        b_obj_type = b_obj.type
        b_obj_anim_data = b_obj.animation_data  # get animation data
        b_obj_children = b_obj.children
        has_anim = True if b_obj_anim_data and b_obj_anim_data.action and b_obj_anim_data.action.fcurves else False

        # can we export this b_obj?
        if b_obj_type not in self.nif_export.export_types:
            return None
        if b_obj_type == 'MESH' and b_obj.name.lower().startswith('bsbound'):
            # add a bounding box
            self.nif_export.collisionhelper.export_bounding_box(b_obj, n_parent, bsbound=True)
            return None  # done; stop here

        elif b_obj_type == 'MESH' and b_obj.name.lower().startswith("bounding box"):
            # Morrowind bounding box
            self.nif_export.collisionhelper.export_bounding_box(b_obj, n_parent, bsbound=False)
            return None  # done; stop here

        elif b_obj_type == 'MESH':
            # -> mesh data.
            # If this has children or animations or more than one material it gets wrapped in a purpose made NiNode.
            is_collision = b_obj.game.use_collision_bounds
            has_children = len(b_obj_children) > 0
            is_multimaterial = len(set([f.material_index for f in b_obj.data.polygons])) > 1

            # determine if object tracks camera
            # nb normally, imported models will have tracking constraints on their parent empty
            # but users may create track_to constraints directly on objects, so keep it for now
            has_track = self.has_track(b_obj)

            if is_collision:
                self.nif_export.collisionhelper.export_collision(b_obj, n_parent)
                return None  # done; stop here
            elif has_anim or has_children or is_multimaterial or has_track:
                # create a ninode as parent of this mesh for the hierarchy to work out
                node = self.create_ninode(b_obj)
            else:
                # don't create intermediate ninode for this guy
                return self.mesh_helper.export_tri_shapes(b_obj, n_parent, b_obj.name)

            # set transform on trishapes rather than on NiNode for skinned meshes this fixes an issue with clothing slots
            if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                if b_obj_anim_data:
                    # mesh with armature parent should not have animation!
                    NifLog.warn("Mesh {0} is skinned but also has object animation. "
                                "The nif format does not support this, ignoring object animation.".format(b_obj.name))
                    has_anim = False

        else:
            # -> everything else (empty/armature) is a (more or less regular) node
            node = self.create_ninode(b_obj)

        # make it child of its parent in the nif, if it has one
        if n_parent:
            n_parent.add_child(node)

        # and fill in this node's non-trivial values
        node.name = self.get_full_name(b_obj)
        self.set_node_flags(b_obj, node)
        self.set_object_matrix(b_obj, node)

        # export object animation
        if has_anim:
            self.nif_export.animationhelper.transform.export_transforms(node, b_obj)
            self.nif_export.animationhelper.obj_anim.export_visibility(node, b_obj)
        # if it is a mesh, export the mesh as trishape children of this ninode
        if b_obj.type == 'MESH':
            return self.mesh_helper.export_tri_shapes(b_obj, node)
        # if it is an armature, export the bones as ninode children of this ninode
        elif b_obj.type == 'ARMATURE':
            self.nif_export.armaturehelper.export_bones(b_obj, node)

        # export all children of this b_obj as children of this NiNode
        self.export_children(b_obj, node)

        return node

    def export_children(self, b_parent, n_parent):
        """Export all children of blender object b_parent as children of n_parent."""
        # loop over all obj's children
        for b_child in b_parent.children:
            # special case: objects parented to armature bones - find the nif parent bone
            if b_parent.type == 'ARMATURE' and b_child.parent_bone != "":
                parent_bone = b_parent.data.bones[b_child.parent_bone]
                assert (parent_bone in block_store.block_to_obj.values())
                for n_parent, obj in block_store.block_to_obj.items():
                    if obj == parent_bone:
                        break
            self.nif_export.objecthelper.export_node(b_child, n_parent)

    def create_ninode(self, b_obj=None):
        """Essentially a wrapper around create_block() that creates nodes of the right type"""
        # when no b_obj is passed, it means we create a root node
        if not b_obj:
            return block_store.create_block("NiNode")

        # get node type - some are stored as custom property of the b_obj
        try:
            n_node_type = b_obj["type"]
        except KeyError:
            n_node_type = "NiNode"

        # ...others by presence of constraints
        if self.has_track(b_obj):
            n_node_type = "NiBillboardNode"

        # now create the node
        n_node = block_store.create_block(n_node_type, b_obj)

        # customize the node data, depending on type
        if n_node_type == "NiLODNode":
            lod_export.export_range_lod_data(n_node, b_obj)

        return n_node

    def get_unique_name(self, b_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object.

        :param b_name: Name of object as in blender.
        :type b_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        unique_name = "unnamed"
        if b_name:
            unique_name = b_name
        # blender bone naming -> nif bone naming
        unique_name = armature.get_bone_name_for_nif(unique_name)
        return unique_name

    def get_full_name(self, b_obj):
        """Returns the original imported name if present, or the name by which
        the object was exported already.
        """
        longname = ""
        if b_obj:
            try:
                longname = b_obj.niftools.longname
            except:
                pass
            if not longname:
                longname = self.get_unique_name(b_obj.name)
        return longname

    def set_object_matrix(self, b_obj, block):
        """Set a blender object's transform matrix to a NIF object's transformation matrix in rest pose."""
        block.set_transform(self.get_object_matrix(b_obj))

    def get_object_matrix(self, b_obj):
        """Get a blender object's matrix as NifFormat.Matrix44"""
        return self.mathutils_to_nifformat_matrix(self.get_object_bind(b_obj))

    def set_b_matrix_to_n_block(self, b_matrix, block):
        """Set a blender matrix to a NIF object's transformation matrix in rest pose."""
        # TODO [object] maybe favor this over the above two methods for more flexibility and transparency?
        block.set_transform(self.mathutils_to_nifformat_matrix(b_matrix))

    def mathutils_to_nifformat_matrix(self, b_matrix):
        """Convert a blender matrix to a NifFormat.Matrix44"""
        # transpose to swap columns for rows so we can use pyffi's set_rows() directly
        # instead of setting every single value manually
        n_matrix = NifFormat.Matrix44()
        n_matrix.set_rows(*b_matrix.transposed())
        return n_matrix

    def get_object_bind(self, b_obj):
        """Get the bind matrix of a blender object.

        Returns the final NIF matrix for the given blender object.
        Blender space and axes order are corrected for the NIF.
        Returns a 4x4 mathutils.Matrix()
        """

        if isinstance(b_obj, bpy.types.Bone):
            return armature.get_bind_matrix(b_obj)

        elif isinstance(b_obj, bpy.types.Object):

            # TODO [armature] Move to armaturehelper
            # if there is a bone parent then the object is parented then get the matrix relative to the bone parent head
            if b_obj.parent_bone:
                # get parent bone
                parent_bone = b_obj.parent.data.bones[b_obj.parent_bone]

                # undo what was done on import
                mpi = armature.nif_bind_to_blender_bind(b_obj.matrix_parent_inverse).inverted()
                mpi.translation.y -= parent_bone.length
                return mpi.inverted() * b_obj.matrix_basis
            # just get the local matrix
            else:
                return b_obj.matrix_local
        # Nonetype, maybe other weird stuff
        return mathutils.Matrix()

    def has_track(self, b_obj):
        """ Determine if this b_obj has a track_to constraint """
        # bones do not have constraints
        if not isinstance(b_obj, bpy.types.Bone):
            for constr in b_obj.constraints:
                if constr.type == 'TRACK_TO':
                    return True


