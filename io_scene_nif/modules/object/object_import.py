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

from io_scene_nif.modules import armature

class Object:
    # this will have to deal with all naming issues
    def __init__(self, parent):
        self.nif_import = parent
        # self.dict_names = {}
        # self.dict_blocks = {}
    
    def import_bsbound_data(self, root_block):
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.BSBound):
                self.nif_import.boundhelper.import_bounding_box(n_extra)
                    
    @staticmethod    
    def import_bsxflag_data(root_block):
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.BSXFlags):
                # get bsx flags so we can attach it to collision object
                bsxflags = n_extra.integer_data
                return bsxflags
        return 0

    @staticmethod
    def import_upbflag_data(root_block):
        # process extra data
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.NiStringExtraData):
                if n_extra.name.decode() == "UPB":
                    upbflags = n_extra.string_data.decode()
                    return upbflags
        return ''

    
    def create_b_obj(self, n_block, b_obj_data):
        """Helper function to create a b_obj from b_obj_data, link it to the current scene, make it active and select it."""
        # get the actual nif name
        n_name = n_block.name.decode() if n_block else ""
        # let blender choose a name
        b_obj = bpy.data.objects.new(n_name, b_obj_data)
        b_obj.select = True
        # make the object visible and active
        bpy.context.scene.objects.link(b_obj)
        bpy.context.scene.objects.active = b_obj
        self.store_longname(b_obj, n_name)
        self.map_names(b_obj, n_block)
        return b_obj
        
    def store_longname(self, b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            # NifLog.debug("Stored long name for {0}".format(b_obj.name))
   
    def map_names(self, b_obj, n_block):
        """Create mapping between nif and blender names"""
        # map nif block to blender short name
        self.nif_import.dict_names[n_block] = b_obj.name
        # map blender short name to nif block
        self.nif_import.dict_blocks[b_obj.name] = n_block
        
    def import_range_lod_data(self, n_node, b_obj):
        """ Import LOD ranges and mark b_obj as a LOD node """
        if isinstance(n_node, NifFormat.NiLODNode):
            b_obj["type"] = "NiLODNode"
            range_data = n_node
            # where lodlevels are stored is determined by version number
            # need more examples - just a guess here
            if not range_data.lod_levels:
                range_data = n_node.lod_level_data
            for lod_level, b_child in zip(range_data.lod_levels, b_obj.children):
                b_child["near_extent"] = lod_level.near_extent
                b_child["far_extent"] = lod_level.far_extent

    def import_billboard(self, n_node, b_obj):
        """ Import a NiBillboardNode """
        if isinstance(n_node, NifFormat.NiBillboardNode):
            # find camera object
            for obj in bpy.context.scene.objects:
                if obj.type == 'CAMERA':
                    b_obj_camera = obj
                    break
            # none exists, create one
            else:
                b_obj_camera_data = bpy.data.cameras.new("Camera")
                b_obj_camera = self.objecthelper.create_b_obj(None, b_obj_camera_data)
            # make b_obj track camera object
            constr = b_obj.constraints.new('TRACK_TO')
            constr.target = b_obj_camera
            constr.track_axis = 'TRACK_Z'
            constr.up_axis = 'UP_Y'

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
    
    def set_object_bind(self, b_obj, object_children, b_colliders, b_armature):
        # fix parentship
        if isinstance(b_obj, bpy.types.Object):
            # simple object parentship
            for (n_child, b_child) in object_children:
                b_child.parent = b_obj

        elif isinstance(b_obj, bpy.types.Bone):
            
            for b_collider in b_colliders:
                b_collider.parent = b_armature
                b_collider.parent_type = 'BONE'
                b_collider.parent_bone = b_obj.name
                
                # the capsule has been centered, now make it relative to bone head
                offset = b_collider.location.y - b_obj.length
                b_collider.matrix_basis = armature.nif_bind_to_blender_bind( mathutils.Matrix() )
                b_collider.location.y = offset
            
            # Mesh attached to bone (may be rigged or static)
            for n_child, b_child in object_children:
                b_child.parent = b_armature
                b_child.parent_type = 'BONE'
                b_child.parent_bone = b_obj.name

                # before we start, matrix_basis and matrix_parent_inverse are unity
                # this works even for arbitrary bone orientation
                # note that matrix_parent_inverse is a unity matrix on import, so could be simplified further with a constant
                mpi = armature.nif_bind_to_blender_bind(b_child.matrix_parent_inverse).inverted()
                mpi.translation.y -= b_obj.length
                # essentially we mimic a transformed matrix_parent_inverse and delegate its transform
                b_child.matrix_local = mpi * b_child.matrix_basis
        else:
            raise RuntimeError("Unexpected object type %s" % b_obj.__class__)
