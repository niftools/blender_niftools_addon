"""This script contains helper methods to import objects."""

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

from io_scene_niftools.modules.nif_import.geometry.mesh import Mesh
from io_scene_niftools.modules.nif_import.object.block_registry import block_store
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


class Object:

    def __init__(self):
        self.mesh = Mesh()

    @staticmethod
    def create_b_obj(n_block, b_obj_data, name=""):
        """Helper function to create a b_obj from b_obj_data, link it to the current scene, make it active and select it."""
        # get the actual nif name
        n_name = n_block.name.decode() if n_block else ""
        if name:
            n_name = name
        # let blender choose a name
        b_obj = bpy.data.objects.new(n_name, b_obj_data)
        # make the object visible and active
        bpy.context.scene.collection.objects.link(b_obj)
        bpy.context.view_layer.objects.active = b_obj
        block_store.store_longname(b_obj, n_name)
        b_obj.select_set(True)
        return b_obj

    @staticmethod
    def mesh_from_data(name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        return Object.create_b_obj(None, me, name)

    @staticmethod
    def box_from_extents(b_name, minx, maxx, miny, maxy, minz, maxz):
        verts = []
        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    verts.append((x, y, z))
        faces = [[0, 1, 3, 2], [6, 7, 5, 4], [0, 2, 6, 4], [3, 1, 5, 7], [4, 5, 1, 0], [7, 6, 2, 3]]
        return Object.mesh_from_data(b_name, verts, faces)

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
                mpi = math.nif_bind_to_blender_bind(b_child.matrix_parent_inverse).inverted()
                mpi.translation.y -= b_obj.length
                # essentially we mimic a transformed matrix_parent_inverse and delegate its transform
                # nb. matrix local is relative to the armature object, not the bone
                b_child.matrix_local = mpi @ b_child.matrix_basis
        else:
            raise RuntimeError(f"Unexpected object type {b_obj.__class__:s}")

    def create_mesh_object(self, n_block):
        ni_name = n_block.name.decode()
        # create mesh data
        b_mesh = bpy.data.meshes.new(ni_name)

        # create mesh object and link to data
        b_obj = self.create_b_obj(n_block, b_mesh)

        # Mesh hidden flag
        if n_block.flags & 1 == 1:
            b_obj.display_type = 'WIRE'  # hidden: wire
        else:
            b_obj.display_type = 'TEXTURED'  # not hidden: shaded

        return b_obj

    def import_geometry_object(self, b_armature, n_block):
        # it's a shape node and we're not importing skeleton only
        b_obj = self.create_mesh_object(n_block)
        b_obj.matrix_local = math.import_matrix(n_block)  # set transform matrix for the mesh
        self.mesh.import_mesh(n_block, b_obj)
        bpy.context.view_layer.objects.active = b_obj
        # store flags etc
        self.import_object_flags(n_block, b_obj)
        # skinning? add armature modifier
        if n_block.skin_instance:
            self.append_armature_modifier(b_obj, b_armature)
        return b_obj

    # TODO [object][property] Replace with object level property processing
    @staticmethod
    def import_object_flags(n_block, b_obj):
        """ Various settings in b_obj's niftools panel """
        b_obj.niftools.flags = n_block.flags

        if n_block.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
            cf_index = NifFormat.ConsistencyType._enumvalues.index(n_block.data.consistency_flags)
            b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]

    @staticmethod
    def append_armature_modifier(b_obj, b_armature):
        """Append an armature modifier for the object."""
        if b_obj and b_armature:
            armature_name = b_armature.name
            b_mod = b_obj.modifiers.new(armature_name, 'ARMATURE')
            b_mod.object = b_armature
            b_mod.use_bone_envelopes = False
            b_mod.use_vertex_groups = True
