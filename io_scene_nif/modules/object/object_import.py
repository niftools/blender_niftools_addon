"""This script contains helper methods to export objects."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2016, NIF File Format Library and Tools contributors.
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
from pyffi.formats.nif import NifFormat

from io_scene_nif.modules import armature
from io_scene_nif.modules.object import PRN_DICT
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class Object:

    # TODO [property] Add delegate processing
    def import_extra_datas(self, root_block, b_obj):
        """ Only to be called on nif and blender root objects! """
        # store type of root node
        if isinstance(root_block, NifFormat.BSFadeNode):
            b_obj.niftools.rootnode = 'BSFadeNode'
        else:
            b_obj.niftools.rootnode = 'NiNode'
        # store its flags
        b_obj.niftools.objectflags = root_block.flags
        # store extra datas
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.NiStringExtraData):
                # weapon location or attachment position
                if n_extra.name.decode() == "Prn":
                    for k, v in PRN_DICT.items():
                        if v.lower() == n_extra.string_data.decode().lower():
                            b_obj.niftools.prn_location = k
                elif n_extra.name.decode() == "UPB":
                    b_obj.niftools.upb = n_extra.string_data.decode()
            elif isinstance(n_extra, NifFormat.BSXFlags):
                b_obj.niftools.bsxflags = n_extra.integer_data
            elif isinstance(n_extra, NifFormat.BSInvMarker):
                b_obj.niftools_bs_invmarker.add()
                b_obj.niftools_bs_invmarker[0].name = n_extra.name.decode()
                b_obj.niftools_bs_invmarker[0].bs_inv_x = n_extra.rotation_x
                b_obj.niftools_bs_invmarker[0].bs_inv_y = n_extra.rotation_y
                b_obj.niftools_bs_invmarker[0].bs_inv_z = n_extra.rotation_z
                b_obj.niftools_bs_invmarker[0].bs_inv_zoom = n_extra.zoom

    @staticmethod
    def create_b_obj(n_block, b_obj_data, name=""):
        """Helper function to create a b_obj from b_obj_data, link it to the current scene, make it active and select it."""
        # get the actual nif name
        n_name = n_block.name.decode() if n_block else ""
        if name:
            n_name = name
        # let blender choose a name
        b_obj = bpy.data.objects.new(n_name, b_obj_data)
        b_obj.select = True
        # make the object visible and active
        bpy.context.scene.objects.link(b_obj)
        bpy.context.scene.objects.active = b_obj
        Object.store_longname(b_obj, n_name)
        return b_obj

    def mesh_from_data(self, name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        return self.create_b_obj(None, me, name)

    def box_from_extents(self, b_name, minx, maxx, miny, maxy, minz, maxz):
        verts = []
        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    verts.append((x, y, z))
        faces = [[0, 1, 3, 2], [6, 7, 5, 4], [0, 2, 6, 4], [3, 1, 5, 7], [4, 5, 1, 0], [7, 6, 2, 3]]
        return self.mesh_from_data(b_name, verts, faces)

    @staticmethod
    def store_longname(b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            NifLog.debug("Stored long name for {0}".format(b_obj.name))

    def import_root_collision(self, n_node, b_obj):
        """ Import a RootCollisionNode """
        if isinstance(n_node, NifFormat.RootCollisionNode):
            b_obj.draw_type = 'BOUNDS'
            b_obj.show_wire = True
            b_obj.draw_bounds_type = 'BOX'
            b_obj.game.use_collision_bounds = True
            b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
            b_obj.niftools.objectflags = n_node.flags
            b_mesh = b_obj.data
            b_mesh.validate()
            b_mesh.update()

    def set_object_bind(self, b_obj, b_obj_children, b_armature):
        """ Sets up parent-child relationships for b_obj and all its children and corrects space for children of bones"""
        if isinstance(b_obj, bpy.types.Object):
            # simple object parentship, no space correction
            for b_child in b_obj_children:
                b_child.parent = b_obj

        elif isinstance(b_obj, bpy.types.Bone):
            # Mesh attached to bone (may be rigged or static) or a collider, needs bone space correction
            for b_child in b_obj_children:
                b_child.parent = b_armature
                b_child.parent_type = 'BONE'
                b_child.parent_bone = b_obj.name

                # this works even for arbitrary bone orientation
                # note that matrix_parent_inverse is a unity matrix on import, so could be simplified further with a constant
                mpi = armature.nif_bind_to_blender_bind(b_child.matrix_parent_inverse).inverted()
                mpi.translation.y -= b_obj.length
                # essentially we mimic a transformed matrix_parent_inverse and delegate its transform
                # nb. matrix local is relative to the armature object, not the bone
                b_child.matrix_local = mpi * b_child.matrix_basis
        else:
            raise RuntimeError("Unexpected object type %s" % b_obj.__class__)

    @staticmethod
    def is_grouping_node(n_block):
        """Determine whether node is grouping node.
        Returns the children which are grouped, or empty list if it is not a grouping node.
        """
        # combining shapes: disable grouping
        if not NifOp.props.combine_shapes:
            return []

        # check that it is a ninode
        if not isinstance(n_block, NifFormat.NiNode):
            return []

        # NiLODNodes are never grouping nodes (this ensures that they are imported as empties, with LODs as child meshes)
        if isinstance(n_block, NifFormat.NiLODNode):
            return []

        # root collision node: join everything
        if isinstance(n_block, NifFormat.RootCollisionNode):
            return [child for child in n_block.children if isinstance(child, NifFormat.NiTriBasedGeom)]

        # check that node has name
        node_name = n_block.name
        if not node_name:
            return []

        # strip "NonAccum" trailer, if present
        if node_name[-9:].lower() == " nonaccum":
            node_name = node_name[:-9]

        # get all geometry children
        return [child for child in n_block.children if (isinstance(child, NifFormat.NiTriBasedGeom) and child.name.find(node_name) != -1)]

    def create_mesh_object(self, n_block):
        ni_name = n_block.name.decode()
        # create mesh data
        b_mesh = bpy.data.meshes.new(ni_name)

        # create mesh object and link to data
        b_obj = self.create_b_obj(n_block, b_mesh)

        # Mesh hidden flag
        if n_block.flags & 1 == 1:
            b_obj.draw_type = 'WIRE'  # hidden: wire
        else:
            b_obj.draw_type = 'TEXTURED'  # not hidden: shaded

        return b_obj

    @staticmethod
    def import_name(n_block):
        """Get name of n_block, ready for blender but not necessarily unique.

        :param n_block: A named nif block.
        :type n_block: :class:`~pyffi.formats.nif.NifFormat.NiObjectNET`
        """
        if n_block is None:
            return ""

        NifLog.debug("Importing name for {0} block from {1}".format(n_block.__class__.__name__, n_block.name))

        n_name = n_block.name.decode()

        # if name is empty, create something non-empty
        if not n_name:
            n_name = "noname"
        n_name = armature.get_bone_name_for_blender(n_name)

        return n_name

    # TODO [object][property] Replace with object level property processing
    @staticmethod
    def import_object_flags(n_block, b_obj):
        """ Various settings in b_obj's niftools panel """
        b_obj.niftools.objectflags = n_block.flags

        if n_block.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
            cf_index = NifFormat.ConsistencyType._enumvalues.index(n_block.data.consistency_flags)
            b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]
