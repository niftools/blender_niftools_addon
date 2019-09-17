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
from io_scene_nif.utility.nif_logging import NifLog

class Object:
    # this will have to deal with all naming issues
    def __init__(self, parent):
        self.nif_import = parent
    
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
                    for k, v in self.nif_import.prn_dict.items():
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

    def create_b_obj(self, n_block, b_obj_data, name=""):
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
        self.store_longname(b_obj, n_name)
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
                    verts.append( (x,y,z) )
        faces = [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]]
        return self.mesh_from_data(b_name, verts, faces)

    def store_longname(self, b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            NifLog.debug("Stored long name for {0}".format(b_obj.name))
   
    def import_range_lod_data(self, n_node, b_obj, b_children):
        """ Import LOD ranges and mark b_obj as a LOD node """
        if isinstance(n_node, NifFormat.NiLODNode):
            b_obj["type"] = "NiLODNode"
            range_data = n_node
            # where lodlevels are stored is determined by version number
            # need more examples - just a guess here
            if not range_data.lod_levels:
                range_data = n_node.lod_level_data
            # can't just take b_obj.children because the order doesn't match
            for lod_level, b_child in zip(range_data.lod_levels, b_children):
                b_child["near_extent"] = lod_level.near_extent
                b_child["far_extent"] = lod_level.far_extent

    def import_billboard(self, n_node, b_obj):
        """ Import a NiBillboardNode """
        if isinstance(n_node, NifFormat.NiBillboardNode) and not isinstance(b_obj, bpy.types.Bone):
            # find camera object
            for obj in bpy.context.scene.objects:
                if obj.type == 'CAMERA':
                    b_obj_camera = obj
                    break
            # none exists, create one
            else:
                b_obj_camera_data = bpy.data.cameras.new("Camera")
                b_obj_camera = self.create_b_obj(None, b_obj_camera_data)
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
    
    def get_skin_deformation_from_partition(self, n_geom):
        """ Workaround because pyffi does not support this skinning method """

        # todo [pyffi] integrate this into pyffi!!!
        #              so that NiGeometry.get_skin_deformation() deals with this as intended

        # mostly a copy from pyffi...
        skininst = n_geom.skin_instance
        skindata = skininst.data
        skinpartition = skininst.skin_partition
        skelroot = skininst.skeleton_root
        vertices = [ NifFormat.Vector3() for i in range(n_geom.data.num_vertices) ]
        # ignore normals for now, not needed for import
        sumweights = [ 0.0 for i in range(n_geom.data.num_vertices) ]
        skin_offset = skindata.get_transform()
        # store one transform per bone
        bone_transforms = []
        for i, bone_block in enumerate(skininst.bones):
            bonedata = skindata.bone_list[i]
            bone_offset = bonedata.get_transform()
            bone_matrix = bone_block.get_transform(skelroot)
            transform = bone_offset * bone_matrix * skin_offset
            bone_transforms.append(transform)
        # now the actual unique bit
        for block in skinpartition.skin_partition_blocks:
            # create all vgroups for this block's bones
            block_bone_transforms = [bone_transforms[i] for i in block.bones]

            # go over each vert in this block
            for vert_index, vertex_weights, bone_indices in zip(block.vertex_map,
                                                                block.vertex_weights,
                                                                block.bone_indices):
                # skip verts that were already processed in an earlier block
                if sumweights[vert_index] != 0:
                    continue
                # go over all 4 weight / bone pairs and transform this vert
                for weight, b_i in zip(vertex_weights, bone_indices):
                    if weight > 0:
                        transform = block_bone_transforms[b_i]
                        vertices[vert_index] += weight * (n_geom.data.vertices[vert_index] * transform)
                        sumweights[vert_index] += weight
        for i, s in enumerate(sumweights):
            if abs(s - 1.0) > 0.01: 
                print( "vertex %i has weights not summing to one: %i" % (i, sumweights[i]))
            
        return vertices

    def apply_skin_deformation(self, n_data):
        """ Process all geometries in NIF tree to apply their skin """
        # get all geometries with skin
        n_geoms = [g for g in n_data.get_global_iterator() if isinstance(g, NifFormat.NiGeometry) and g.is_skin()]
        # make sure that each skin is applied only once to avoid distortions when a model is referred to twice
        for n_geom in set(n_geoms):
            NifLog.info('Applying skin deformation on geometry {0}'.format(n_geom.name))
            skininst = n_geom.skin_instance
            skindata = skininst.data
            if skindata.has_vertex_weights:
                vertices = n_geom.get_skin_deformation()[0]
            else:
                NifLog.info("PYFFI does not support this type of skinning, so here's a workaround...")
                vertices = self.get_skin_deformation_from_partition(n_geom)
            # finally we can actually set the data
            for vold, vnew in zip(n_geom.data.vertices, vertices):
                vold.x = vnew.x
                vold.y = vnew.y
                vold.z = vnew.z

                