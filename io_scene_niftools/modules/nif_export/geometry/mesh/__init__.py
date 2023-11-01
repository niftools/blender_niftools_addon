"""This module contains helper methods to export Mesh information."""
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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
import bmesh
import mathutils
import numpy as np
import struct

from nifgen.formats.nif import classes as NifClasses

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.geometry import mesh
from io_scene_niftools.modules.nif_export.animation.morph import MorphAnimation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.property.object import ObjectProperty
from io_scene_niftools.modules.nif_export.property.texture.types.nitextureprop import NiTextureProp
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp, NifData
from io_scene_niftools.utils.logging import NifLog, NifError
from io_scene_niftools.modules.nif_export.geometry.mesh.skin_partition import update_skin_partition


class Mesh:

    def __init__(self):
        self.texture_helper = NiTextureProp.get()
        self.object_property = ObjectProperty()
        self.morph_anim = MorphAnimation()

    def export_tri_shapes(self, b_obj, n_parent, n_root, trishape_name=None):
        """
        Export a blender object ob of the type mesh, child of nif block
        n_parent, as NiTriShape and NiTriShapeData blocks, possibly
        along with some NiTexturingProperty, NiSourceTexture,
        NiMaterialProperty, and NiAlphaProperty blocks. We export one
        n_geom block per mesh material. We also export vertex weights.

        The parameter trishape_name passes on the name for meshes that
        should be exported as a single mesh.
        """
        NifLog.info(f"Exporting {b_obj}")

        assert (b_obj.type == 'MESH')

        # get mesh from b_obj, and evaluate the mesh with modifiers applied, too
        b_mesh = b_obj.data
        eval_mesh = self.get_evaluated_mesh(b_obj)

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not eval_mesh.vertices:
            # do not export anything
            NifLog.warn(f"{b_obj} has no vertices, skipped.")
            return

        # get the mesh's materials, this updates the mesh material list
        if not isinstance(n_parent, NifClasses.RootCollisionNode):
            mesh_materials = eval_mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_materials = []

        # if mesh has no materials, all face material indices should be 0, so fake one material in the material list
        if not mesh_materials:
            mesh_materials = [None]

        # vertex color check
        mesh_hasvcol = len(eval_mesh.vertex_colors) > 0 or len(eval_mesh.color_attributes) > 0
        # list of body part (name, index, vertices) in this mesh
        polygon_parts = self.get_polygon_parts(b_obj, eval_mesh)
        nif_scene = bpy.context.scene.niftools_scene
        game = nif_scene.game

        # Non-textured materials, vertex colors are used to color the mesh
        # Textured materials, they represent lighting details

        # let's now export one n_geom for every mesh material
        # TODO [material] needs refactoring - move material, texture, etc. to separate function
        for b_mat_index, b_mat in enumerate(mesh_materials):

            mesh_hasnormals = False
            if b_mat is not None:
                mesh_hasnormals = True  # for proper lighting
                if nif_scene.is_skyrim() and b_mat.niftools_shader.model_space_normals:
                    mesh_hasnormals = False  # for proper lighting

            # create a n_geom block
            if game in ("SKYRIM_SE",):
                n_geom = block_store.create_block("BSTriShape", b_obj)
            elif not NifOp.props.stripify:
                n_geom = block_store.create_block("NiTriShape", b_obj)
                n_geom.data = block_store.create_block("NiTriShapeData", b_obj)
            else:
                n_geom = block_store.create_block("NiTriStrips", b_obj)
                n_geom.data = block_store.create_block("NiTriStripsData", b_obj)

            # fill in the NiTriShape's non-trivial values
            if isinstance(n_parent, NifClasses.RootCollisionNode):
                n_geom.name = ""
            else:
                if not trishape_name:
                    if n_parent.name:
                        n_geom.name = "Tri " + n_parent.name
                    else:
                        n_geom.name = "Tri " + b_obj.name
                else:
                    n_geom.name = trishape_name

                # multimaterial meshes: add material index (Morrowind's child naming convention)
                if len(mesh_materials) > 1:
                    n_geom.name = f"{n_geom.name}: {b_mat_index}"
                else:
                    n_geom.name = block_store.get_full_name(n_geom)

            self.set_mesh_flags(b_obj, n_geom)

            # extra shader for Sid Meier's Railroads
            if game == 'SID_MEIER_S_RAILROADS':
                n_geom.has_shader = True
                n_geom.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                n_geom.unknown_integer = -1  # default

            # if we have an animation of a blender mesh
            # an intermediate NiNode has been created which holds this b_obj's transform
            # the n_geom itself then needs identity transform (default)
            if trishape_name is not None:
                # only export the bind matrix on trishapes that were not animated
                math.set_object_matrix(b_obj, n_geom)

            # check if there is a parent
            if n_parent:
                # add texture effect block (must be added as parent of the n_geom)
                n_parent = self.export_texture_effect(n_parent, b_mat)
                # refer to this mesh in the parent's children list
                n_parent.add_child(n_geom)

            self.object_property.export_properties(b_obj, b_mat, n_geom)

            b_uv_layers = eval_mesh.uv_layers
            # for each face in triangles, a body part index
            bodypartfacemap = []
            polygons_without_bodypart = []

            if eval_mesh.polygons:
                if b_uv_layers:
                    # if we have uv coordinates double check that we have uv data
                    if not eval_mesh.uv_layer_stencil:
                        NifLog.warn(f"No UV map for texture associated with selected mesh '{eval_mesh.name}'.")

            use_tangents = False
            if b_uv_layers and mesh_hasnormals:
                default_use_tangents = ('BULLY_SE',
                                        )
                if game in default_use_tangents or nif_scene.is_bs() or (game in self.texture_helper.USED_EXTRA_SHADER_TEXTURES):
                    use_tangents = True

            if nif_scene.is_fo3() or nif_scene.is_skyrim():
                if len(b_uv_layers) > 1:
                    raise NifError(f"{game} does not support multiple UV layers.")

            triangles, t_nif_to_blend, vertex_information, v_nif_to_blend = self.get_geom_data(b_mesh=eval_mesh,
                                                                             color=mesh_hasvcol,
                                                                             normal=mesh_hasnormals,
                                                                             uv=len(b_uv_layers) > 0,
                                                                             tangent=use_tangents,
                                                                             b_mat_index=b_mat_index)

            if len(vertex_information['POSITION']) == 0:
                continue  # m_4444x: skip 'empty' material indices
            if len(vertex_information['POSITION']) > 65535:
                raise NifError("Too many vertices. Decimate your mesh and try again.")
            if len(triangles) > 65535:
                raise NifError("Too many polygons. Decimate your mesh and try again.")

            vertex_map = [None for _ in range(len(eval_mesh.vertices))]
            for i, vertex_index in enumerate(v_nif_to_blend):
                if vertex_map[vertex_index] is None:
                    vertex_map[vertex_index] = [i]
                else:
                    vertex_map[vertex_index].append(i)

            if len(b_uv_layers) > 0:
                # adjustment of UV coordinates because of imprecision at larger sizes
                uv_array = vertex_information['UV']
                for layer_idx in range(len(b_uv_layers)):
                    for coord_idx in range(uv_array.shape[2]):
                        coord_min = np.min(uv_array[:, layer_idx, coord_idx])
                        coord_max = np.max(uv_array[:, layer_idx, coord_idx])
                        min_floor = np.floor(coord_min)
                        # UV coordinates must not be in the 0th UV square and must fit in one UV square
                        if min_floor != 0 and np.floor(coord_max) == min_floor:
                            uv_array[:, layer_idx, coord_idx] -= min_floor

            # add body part number
            if game not in ('FALLOUT_3', 'FALLOUT_NV', 'SKYRIM', 'SKYRIM_SE') or len(polygon_parts) == 0:
                # TODO: or not self.EXPORT_FO3_BODYPARTS):
                bodypartfacemap = np.zeros(len(triangles), dtype=int)
            else:
                bodypartfacemap = polygon_parts[t_nif_to_blend]
                polygon_indices_without_bodypart = np.arange(len(polygon_parts))[polygon_parts < 0]
                polygons_without_bodypart = [eval_mesh.polygons[i] for i in polygon_indices_without_bodypart]

            # check that there are no missing body part polygons
            if polygons_without_bodypart:
                self.select_unassigned_polygons(eval_mesh, b_obj, polygons_without_bodypart)

            self.set_geom_data(n_geom,
                               triangles,
                               vertex_information, b_uv_layers)

            # todo [mesh/object] use more sophisticated armature finding, also taking armature modifier into account
            # now export the vertex weights, if there are any
            if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                b_obj_armature = b_obj.parent
                vertgroups = {vertex_group.name for vertex_group in b_obj.vertex_groups}
                bone_names = set(b_obj_armature.data.bones.keys())
                # the vertgroups that correspond to bone_names are bones that influence the mesh
                boneinfluences = vertgroups & bone_names
                if boneinfluences:  # yes we have skinning!
                    # create new skinning instance block and link it
                    skininst, skindata = self.create_skin_inst_data(b_obj, b_obj_armature, polygon_parts)
                    n_geom.skin_instance = skininst

                    # Vertex weights,  find weights and normalization factors
                    vert_list = {}
                    vert_norm = {}
                    unweighted_vertices = []

                    for bone_group in boneinfluences:
                        b_list_weight = []
                        b_vert_group = b_obj.vertex_groups[bone_group]

                        for b_vert in eval_mesh.vertices:
                            if len(b_vert.groups) == 0:  # check vert has weight_groups
                                unweighted_vertices.append(b_vert.index)
                                continue

                            for g in b_vert.groups:
                                if b_vert_group.name in boneinfluences:
                                    if g.group == b_vert_group.index:
                                        b_list_weight.append((b_vert.index, g.weight))
                                        break

                        vert_list[bone_group] = b_list_weight

                        # create normalisation groupings
                        for v in vert_list[bone_group]:
                            if v[0] in vert_norm:
                                vert_norm[v[0]] += v[1]
                            else:
                                vert_norm[v[0]] = v[1]

                    self.select_unweighted_vertices(b_obj, unweighted_vertices)

                    # for each bone, get the vertex weights and add its n_node to the NiSkinData
                    for b_bone_name in boneinfluences:
                        # find vertex weights
                        vert_weights = {}
                        for v in vert_list[b_bone_name]:
                            # v[0] is the original vertex index
                            # v[1] is the weight

                            # vertex_map[v[0]] is the set of vertices (indices) to which v[0] was mapped
                            # so we simply export the same weight as the original vertex for each new vertex

                            # write the weights
                            # extra check for multi material meshes
                            if vertex_map[v[0]] and vert_norm[v[0]]:
                                for vert_index in vertex_map[v[0]]:
                                    vert_weights[vert_index] = v[1] / vert_norm[v[0]]
                        # add bone as influence, but only if there were actually any vertices influenced by the bone
                        if vert_weights:
                            # find bone in exported blocks
                            n_node = self.get_bone_block(b_obj_armature.data.bones[b_bone_name])
                            n_geom.add_bone(n_node, vert_weights)
                    del vert_weights

                    # update bind position skinning data
                    # n_geom.update_bind_position()
                    # override pyffi n_geom.update_bind_position with custom one that is relative to the nif root
                    self.update_bind_position(n_geom, n_root, b_obj_armature)

                    # calculate center and radius for each skin bone data block
                    n_geom.update_skin_center_radius()

                    self.export_skin_partition(b_obj, bodypartfacemap, triangles, n_geom)

            if isinstance(n_geom, NifClasses.NiTriBasedGeom):
                # fix data consistency type
                n_geom.data.consistency_flags = NifClasses.ConsistencyType[b_obj.niftools.consistency_flags]

            # export EGM or NiGeomMorpherController animation
            # shape keys are only present on the raw, unevaluated mesh
            self.morph_anim.export_morph(b_mesh, n_geom, vertex_map)
        return n_geom

    def get_geom_data(self, b_mesh, color, normal, uv, tangent, b_mat_index):
        """Converts the blender information in b_mesh to a triangles, a dictionary with vertex information and a
        mapping of the blender vertices to nif vertices.

        :param b_mesh: Blender Mesh object
        :type b_mesh: class:`bpy.types.Mesh`
        :param color: Whether to consider vertex colors
        :type color: bool
        :param normal: Whether to consider vertex normals
        :type normal: bool
        :param uv: Whether to consider UV coordinates
        :type uv: bool
        :param tangent: Whether to consider tangents and bitangents
        :type tangent: bool
        :param b_mat_index: Material index to filter on. -1 means no filtering
        :type b_mat_index: int

        :return: the triangles, triangle to polygon array, dict of vertex information and nif vertex to blender vertex array
        :rtype: tuple(np.ndarray, np.ndarray, dict(str, np.ndarray), np.ndarray)
        The dictionary can contain the following information:
        POSITION: position
        COLOR: vertex colors
        NORMAL: normal vectors per vertex
        UV: list of  UV coordinates per vertex per layer. vertex_dict['UV'][0][1] gives UV coordinates for the first vertex, second layer
        TANGENT: tangent vector per vertex
        BITANGENT: bitangent per vertex, always present if TANGENT is present

        NIF has one uv vertex, one normal, one color etc per vertex
        NIF uses the normal table for lighting.
        Smooth faces should use Blender's vertex normals,
        solid faces should use Blender's face normals.

        Blender's uv vertices and normals are per face.
        Blender supports per face vertex coloring.
        Blender loops, on the other hand, are much like nif vertices, and refer to one vertex associated with a polygon
        
        The algorithm merges loops with the same information (as long as they have the same original vertex) and
        triangulates the mesh without needing a triangulation modifier.
        """
        n_loops = len(b_mesh.loops)
        n_verts = len(b_mesh.vertices)
        n_tris = len(b_mesh.loop_triangles)

        if b_mat_index >= 0:
            loop_mat_indices = np.ones(n_loops, dtype=int) * -1
            for poly in b_mesh.polygons:
                loop_mat_indices[poly.loop_indices] = poly.material_index
            matl_to_loop = np.arange(n_loops, dtype=int)[loop_mat_indices == b_mat_index]
            del loop_mat_indices
        else:
            matl_to_loop = np.arange(n_loops, dtype=int)
        # for the loops without matl equivalent, use len(matl_to_loop) to exceed the length of the matl array
        loop_to_matl = np.ones(n_loops, dtype=int) * len(matl_to_loop)
        loop_to_matl[matl_to_loop] = np.arange(len(matl_to_loop), dtype=int)

        loop_hashes = np.zeros((len(matl_to_loop), 0), dtype=float)

        loop_to_vert = np.zeros(n_loops, dtype=int)
        b_mesh.loops.foreach_get('vertex_index', loop_to_vert)
        matl_to_vert = loop_to_vert[matl_to_loop]
        loop_hashes = np.concatenate((loop_hashes, matl_to_vert.reshape((-1,1))), axis=1)

        vert_positions = np.zeros((n_verts, 3), dtype=float)
        b_mesh.vertices.foreach_get('co', vert_positions.reshape((-1, 1)))
        loop_positions = vert_positions[matl_to_vert]
        del vert_positions
        loop_hashes = np.concatenate((loop_hashes, loop_positions), axis=1)

        if color:
            loop_colors = np.zeros((n_loops, 4), dtype=float)
            if b_mesh.vertex_colors:
                b_mesh.vertex_colors[0].data.foreach_get('color', loop_colors.reshape((-1, 1)))
            else:
                # vertex information of face corner (loop) information
                # byte or float color, but both will give float values
                color_attr = b_mesh.color_attributes[0]
                if color_attr.domain == 'CORNER':
                    color_attr.data.foreach_get('color', loop_colors.reshape((-1, 1)))
                else:
                    vert_colors = np.zeros((n_verts, 4), dtype=float)
                    color_attr.data.foreach_get('color', vert_colors.reshape((-1, 1)))
                    loop_colors[:] = vert_colors[loop_to_vert]
                    del vert_colors
            loop_colors = loop_colors[matl_to_loop]
            loop_hashes = np.concatenate((loop_hashes, loop_colors), axis=1)

        if normal:
            # calculate normals
            b_mesh.calc_normals_split()
            loop_normals = np.zeros((n_loops, 3), dtype=float)
            b_mesh.loops.foreach_get('normal', loop_normals.reshape((-1, 1)))
            # smooth = vertex normal, non-smooth = face normal)
            for poly in b_mesh.polygons:
                if not poly.use_smooth:
                    loop_normals[poly.loop_indices] = poly.normal
            loop_normals = loop_normals[matl_to_loop]
            loop_hashes = np.concatenate((loop_hashes, loop_normals), axis=1)

        if uv:
            uv_layers = []
            for layer in b_mesh.uv_layers:
                loop_uv = np.zeros((n_loops, 2), dtype=float)
                layer.data.foreach_get('uv', loop_uv.reshape((-1, 1)))
                loop_uv = loop_uv[matl_to_loop]
                uv_layers.append(loop_uv)
                loop_hashes = np.concatenate((loop_hashes, loop_uv), axis=1)
            loop_uvs = np.swapaxes(uv_layers, 0, 1)
            del uv_layers

        if tangent:
            b_mesh.calc_tangents(uvmap=b_mesh.uv_layers[0].name)
            loop_tangents = np.zeros((n_loops, 3), dtype=float)
            b_mesh.loops.foreach_get('tangent', loop_tangents.reshape((-1, 1)))
            loop_tangents = loop_tangents[matl_to_loop]
            if NifOp.props.sep_tangent_space:
                loop_hashes = np.concatenate((loop_hashes, loop_tangents), axis=1)

            bitangent_signs = np.zeros((n_loops, 1), dtype=float)
            b_mesh.loops.foreach_get('bitangent_sign', bitangent_signs)
            bitangent_signs = bitangent_signs[matl_to_loop]
            loop_bitangents = bitangent_signs * np.cross(loop_normals, loop_tangents)
            if NifOp.props.sep_tangent_space:
                loop_hashes = np.concatenate((loop_hashes, loop_bitangents), axis=1)
            del bitangent_signs

        # now remove duplicates
        # first exact (also sorts by blender vertex)
        loop_hashes, hash_to_matl, matl_to_hash = np.unique(loop_hashes, return_index=True, return_inverse=True, axis=0)
        hash_to_same_hash = np.arange(len(loop_hashes), dtype=int)
        hash_to_nif_vert = np.arange(len(loop_hashes), dtype=int)
        # then inexact (if epsilon is not 0)
        if NifOp.props.epsilon > 0:

            current_vert = -1
            max_nif_vert = -1
            for hash_index, loop_hash in enumerate(loop_hashes):
                if loop_hash[0] != current_vert:
                    current_vert = loop_hash[0]
                    current_hash_start = hash_index

                nif_vert_index = max_nif_vert + 1
                for comp_index in range(current_hash_start, hash_index):
                    comp_loop_hash = loop_hashes[comp_index]
                    if any(np.abs(comp_loop_hash - loop_hash) > NifOp.props.epsilon):
                        # this hash is different, but others may be the same
                        continue
                    else:
                        nif_vert_index = hash_to_nif_vert[comp_index]
                        hash_to_same_hash[hash_index] = comp_index
                        break
                hash_to_nif_vert[hash_index] = nif_vert_index
                max_nif_vert = max((nif_vert_index, max_nif_vert))

        # finally, use the mapping from blender to nif to create the triangles
        # first get the actual triangles in an array
        blend_triangles = np.zeros((n_tris, 3), dtype=int)
        b_mesh.loop_triangles.foreach_get('loops', blend_triangles.reshape((-1, 1)))
        tri_to_poly = np.zeros(n_tris, dtype=int)
        b_mesh.loop_triangles.foreach_get('polygon_index', tri_to_poly)
        # filter out the ones not in the specified material
        triangle_mats = np.zeros(n_tris, dtype=int)
        b_mesh.loop_triangles.foreach_get('material_index', triangle_mats)
        mattri_to_looptri = np.arange(n_tris, dtype=int)
        if b_mat_index >= 0:
            mattri_to_looptri = mattri_to_looptri[triangle_mats == b_mat_index]
        blend_triangles = blend_triangles[mattri_to_looptri]
        tri_to_poly = tri_to_poly[mattri_to_looptri]
        # go from loop indices to nif vertices
        # [TODO] possibly optimize later
        for i in range(len(blend_triangles)):
            blend_triangles[i] = hash_to_nif_vert[matl_to_hash[loop_to_matl[blend_triangles[i]]]]
        # sort the triangles on polygon index to keep the original order
        tri_sort = np.argsort(tri_to_poly, axis=0)
        tri_to_poly = tri_to_poly[tri_sort]
        blend_triangles = blend_triangles[tri_sort]

        # make the vertex data from the hash map
        nif_to_hash = np.unique(hash_to_same_hash, return_index=True)[1]
        nif_to_matl = hash_to_matl[nif_to_hash]
        data_dict = {
            'POSITION': loop_positions[nif_to_matl]
            }

        if color:
            data_dict['COLOR'] = loop_colors[nif_to_matl]
        if normal:
            data_dict['NORMAL'] = loop_normals[nif_to_matl]
        if uv:
            data_dict['UV'] = loop_uvs[nif_to_matl]
        if tangent:
            data_dict['TANGENT'] = loop_tangents[nif_to_matl]
            data_dict['BITANGENT'] = loop_bitangents[nif_to_matl]

        return blend_triangles, tri_to_poly, data_dict, loop_to_vert[matl_to_loop[nif_to_matl]]

    def set_geom_data(self, n_geom, triangles, vertex_information, b_uv_layers):
        if isinstance(n_geom, NifClasses.BSTriShape):
            self.set_bs_geom_data(n_geom, triangles, vertex_information, b_uv_layers)
        else:
            self.set_ni_geom_data(n_geom, triangles, vertex_information, b_uv_layers)

    def set_bs_geom_data(self, n_geom, triangles, vertex_information, b_uv_layers):
        """Sets the geometry data (triangles and flat lists of per-vertex data) to a BSGeometry block."""
        vertex_flags = n_geom.vertex_desc.vertex_attributes
        vertex_flags.vertex = True
        vertex_flags.u_vs = 'UV' in vertex_information
        vertex_flags.normals = 'NORMAL' in vertex_information
        vertex_flags.tangents = 'TANGENT' in vertex_information
        vertex_flags.vertex_colors = 'COLOR' in vertex_information
        n_geom.vertex_desc.vertex_attributes = vertex_flags
        vert_size = 0
        if vertex_flags.vertex:
            vert_size += 3
            vert_size += 1 # either unused W or bitangent X
        if vertex_flags.u_vs:
            vert_size += 1
        if vertex_flags.normals:
            vert_size += 1
        if vertex_flags.tangents:
            vert_size += 1
        if vertex_flags.vertex_colors:
            vert_size += 1
        n_geom.vertex_desc.vertex_data_size = vert_size

        n_geom.num_triangles = len(triangles)
        n_geom.num_vertices = len(vertex_information['POSITION'])
        # [TODO] maybe in future add function to generated code to use the calc attribute. For now, a copy of the xml.
        n_geom.data_size = ((n_geom.vertex_desc & 0xF) * n_geom.num_vertices * 4) + (n_geom.num_triangles * 6)

        n_geom.reset_field('vertex_data')
        for n_v, b_v in zip([data.vertex for data in n_geom.vertex_data], vertex_information['POSITION']):
            n_v.x, n_v.y, n_v.z = b_v
        if vertex_flags.u_vs:
            for n_uv, b_uv in zip([data.uv for data in n_geom.vertex_data], vertex_information['UV']):
                # NIF flips the texture V-coordinate (OpenGL standard)
                n_uv.u = b_uv[0][0]
                n_uv.v = 1.0 - b_uv[0][1]
        if vertex_flags.normals:
            for n_n, b_n in zip([data.normal for data in n_geom.vertex_data], vertex_information['NORMAL']):
                n_n.x, n_n.y, n_n.z = b_n
        if vertex_flags.tangents:
            # B_tan: +d(B_u), B_bit: +d(B_v) and N_tan: +d(N_v), N_bit: +d(N_u)
            # moreover, N_v = 1 - B_v, so d(B_v) = - d(N_v), therefore N_tan = -B_bit and N_bit = B_tan
            for n_t, b_t in zip([data.tangent for data in n_geom.vertex_data], vertex_information['BITANGENT']):
                n_t.x, n_t.y, n_t.z = -b_t
            for n_vert, b_b in zip(n_geom.vertex_data, vertex_information['TANGENT']):
                n_vert.bitangent_x, n_vert.bitangent_y, n_vert.bitangent_z = b_b
        if vertex_flags.vertex_colors:
            for n_c, b_c in zip([data.vertex_colors for data in n_geom.vertex_data], vertex_information['COLOR']):
                n_c.r, n_c.g, n_c.b, n_c.a = b_c

        n_geom.update_center_radius()

        n_geom.reset_field('triangles')
        for n_tri, b_tri in zip(n_geom.triangles, triangles):
            n_tri.v_1 = b_tri[0]
            n_tri.v_2 = b_tri[1]
            n_tri.v_3 = b_tri[2]

    def set_ni_geom_data(self, n_geom, triangles, vertex_information, b_uv_layers):
        """Sets the geometry data (triangles and flat lists of per-vertex data) to a BSGeometry block."""
        # coords
        n_geom.data.num_vertices = len(vertex_information['POSITION'])
        n_geom.data.has_vertices = True
        n_geom.data.reset_field("vertices")
        for n_v, b_v in zip(n_geom.data.vertices, vertex_information['POSITION']):
            n_v.x, n_v.y, n_v.z = b_v
        n_geom.data.update_center_radius()
        # normals
        n_geom.data.has_normals = 'NORMAL' in vertex_information
        if n_geom.data.has_normals:
            n_geom.data.reset_field("normals")
            for n_v, b_v in zip(n_geom.data.normals, vertex_information['NORMAL']):
                n_v.x, n_v.y, n_v.z = b_v
        # tangents
        if 'TANGENT' in vertex_information:
            tangents = vertex_information['TANGENT']
            bitangents = vertex_information['BITANGENT']
            # B_tan: +d(B_u), B_bit: +d(B_v) and N_tan: +d(N_v), N_bit: +d(N_u)
            # moreover, N_v = 1 - B_v, so d(B_v) = - d(N_v), therefore N_tan = -B_bit and N_bit = B_tan
            self.add_defined_tangents(n_geom,
                                      tangents=-bitangents,
                                      bitangents=tangents,
                                      as_extra_data=(bpy.context.scene.niftools_scene.game == 'OBLIVION'))  # as binary extra data only for Oblivion
        # vertex_colors
        n_geom.data.has_vertex_colors = 'COLOR' in vertex_information
        if n_geom.data.has_vertex_colors:
            n_geom.data.reset_field("vertex_colors")
            for n_v, b_v in zip(n_geom.data.vertex_colors, vertex_information['COLOR']):
                n_v.r, n_v.g, n_v.b, n_v.a = b_v
        # uv_sets
        if bpy.context.scene.niftools_scene.nif_version == 0x14020007 and bpy.context.scene.niftools_scene.user_version_2:
            data_flags = n_geom.data.bs_data_flags
        else:
            data_flags = n_geom.data.data_flags
        data_flags.has_uv = len(b_uv_layers) > 0
        if hasattr(data_flags, "num_uv_sets"):
            data_flags.num_uv_sets = len(b_uv_layers)
        else:
            if len(b_uv_layers) > 1:
                NifLog.warn(f"More than one UV layers for game that doesn't support it, only using first UV layer")
        if data_flags.has_uv:
            n_geom.data.reset_field("uv_sets")
            uv_coords = vertex_information['UV']
            for j, n_uv_set in enumerate(n_geom.data.uv_sets):
                for i, n_uv in enumerate(n_uv_set):
                    if len(uv_coords[i]) == 0:
                        continue  # skip non-uv textures
                    n_uv.u = uv_coords[i][j][0]
                    # NIF flips the texture V-coordinate (OpenGL standard)
                    n_uv.v = 1.0 - uv_coords[i][j][1]  # opengl standard
        # set triangles stitch strips for civ4
        n_geom.data.set_triangles(triangles, stitchstrips=NifOp.props.stitch_strips)

    def export_skin_partition(self, b_obj, bodypartfacemap, triangles, n_geom):
        """Attaches a skin partition to n_geom if needed"""
        game = bpy.context.scene.niftools_scene.game
        if NifData.data.version >= 0x04020100 and NifOp.props.skin_partition:
            NifLog.info("Creating skin partition")

            # warn on bad config settings
            if game == 'OBLIVION':
                if NifOp.props.pad_bones:
                    NifLog.warn(
                        "Using padbones on Oblivion export. Disable the pad bones option to get higher quality skin partitions.")

            # Skyrim Special Edition has a limit of 80 bones per partition, but export is not yet supported
            bones_per_partition_lut = {"OBLIVION": 18, "FALLOUT_3": 18, 'FALLOUT_NV': 18, "SKYRIM": 24}
            rec_bones = bones_per_partition_lut.get(game, None)
            if rec_bones is not None:
                if NifOp.props.max_bones_per_partition < rec_bones:
                    NifLog.warn(f"Using less than {rec_bones} bones per partition on {game} export."
                                f"Set it to {rec_bones} to get higher quality skin partitions.")
                elif NifOp.props.max_bones_per_partition > rec_bones:
                    NifLog.warn(f"Using more than {rec_bones} bones per partition on {game} export."
                                f"This may cause issues in-game.")

            part_order = [NifClasses.BSDismemberBodyPartType[face_map.name] for face_map in
                          b_obj.face_maps if face_map.name in NifClasses.BSDismemberBodyPartType.__members__]
            # override pyffi n_geom.update_skin_partition with custom one (that allows ordering)
            n_geom.update_skin_partition = update_skin_partition.__get__(n_geom)
            lostweight = n_geom.update_skin_partition(
                maxbonesperpartition=NifOp.props.max_bones_per_partition,
                maxbonespervertex=NifOp.props.max_bones_per_vertex,
                stripify=NifOp.props.stripify,
                stitchstrips=NifOp.props.stitch_strips,
                padbones=NifOp.props.pad_bones,
                triangles=triangles,
                trianglepartmap=bodypartfacemap,
                maximize_bone_sharing=(game in ('FALLOUT_3', 'FALLOUT_NV', 'SKYRIM')),
                part_sort_order=part_order)

            if lostweight > NifOp.props.epsilon:
                NifLog.warn(
                    f"Lost {lostweight:f} in vertex weights while creating a skin partition for Blender object '{b_obj.name}' (nif block '{n_geom.name}')")

    def update_bind_position(self, n_geom, n_root, b_obj_armature):
        """Transfer the Blender bind position to the nif bind position.
        Sets the NiSkinData overall transform to the inverse of the geometry transform
        relative to the skeleton root, and sets the NiSkinData of each bone to
        the inverse of the transpose of the bone transform relative to the skeleton root, corrected
        for the overall transform."""
        if not n_geom.is_skin():
            return

        # validate skin and set up quick links
        n_geom._validate_skin()
        skininst = n_geom.skin_instance
        skindata = skininst.data
        skelroot = skininst.skeleton_root

        # calculate overall offset (including the skeleton root transform) and use its inverse
        geomtransform = (n_geom.get_transform(skelroot) * skelroot.get_transform()).get_inverse(fast=False)
        skindata.set_transform(geomtransform)

        # for some nifs, somehow n_root is not set properly?!
        if not n_root:
            NifLog.warn(f"n_root was not set, bug")
            n_root = skelroot

        old_position = b_obj_armature.data.pose_position
        b_obj_armature.data.pose_position = 'POSE'

        # calculate bone offsets
        for i, bone in enumerate(skininst.bones):
            bone_name = block_store.block_to_obj[bone].name
            pose_bone = b_obj_armature.pose.bones[bone_name]
            n_bind = math.mathutils_to_nifformat_matrix(math.blender_bind_to_nif_bind(pose_bone.matrix))
            # todo [armature] figure out the correct transform that works universally
            # inverse skin bind in nif armature space, relative to root / geom??
            skindata.bone_list[i].set_transform((n_bind * geomtransform).get_inverse(fast=False))
            # this seems to be correct for skyrim heads, but breaks stuff like ZT2 elephant
            # skindata.bone_list[i].set_transform(bone.get_transform(n_root).get_inverse())

        b_obj_armature.data.pose_position = old_position

    def get_bone_block(self, b_bone):
        """For a blender bone, return the corresponding nif node from the blocks that have already been exported"""
        for n_block, b_obj in block_store.block_to_obj.items():
            if isinstance(n_block, NifClasses.NiNode) and b_bone == b_obj:
                return n_block
        raise NifError(f"Bone '{b_bone.name}' not found.")

    def get_polygon_parts(self, b_obj, b_mesh):
        """Returns the body part indices of the mesh polygons. -1 is either not assigned to a face map or not a valid
        body part"""
        index_group_map = {-1: -1}
        for bodypartgroupname in [member.name for member in NifClasses.BSDismemberBodyPartType]:
            face_map = b_obj.face_maps.get(bodypartgroupname)
            if face_map:
                index_group_map[face_map.index] = NifClasses.BSDismemberBodyPartType[bodypartgroupname]
        if len(index_group_map) <= 1:
            # there were no valid face maps
            return np.array([])
        bm = bmesh.new()
        bm.from_mesh(b_mesh)
        bm.faces.ensure_lookup_table()
        fm = bm.faces.layers.face_map.verify()
        polygon_parts = np.array([index_group_map.get(face[fm], -1) for face in bm.faces], dtype=int)
        bm.free()
        return polygon_parts

    def create_skin_inst_data(self, b_obj, b_obj_armature, polygon_parts):
        if bpy.context.scene.niftools_scene.game in ('FALLOUT_3', 'FALLOUT_NV', 'SKYRIM') and len(polygon_parts) > 0:
            skininst = block_store.create_block("BSDismemberSkinInstance", b_obj)
        else:
            skininst = block_store.create_block("NiSkinInstance", b_obj)

        # get skeleton root from custom property
        if b_obj.niftools.skeleton_root:
            n_root_name = b_obj.niftools.skeleton_root
        # or use the armature name
        else:
            n_root_name = block_store.get_full_name(b_obj_armature)
        # make sure that such a block exists, find it
        for block in block_store.block_to_obj:
            if isinstance(block, NifClasses.NiNode):
                if block.name == n_root_name:
                    skininst.skeleton_root = block
                    break
        else:
            raise NifError(f"Skeleton root '{n_root_name}' not found.")

        # create skinning data and link it
        skindata = block_store.create_block("NiSkinData", b_obj)
        skininst.data = skindata

        skindata.has_vertex_weights = True
        # fix geometry rest pose: transform relative to skeleton root
        skindata.set_transform(math.get_object_matrix(b_obj).get_inverse())
        return skininst, skindata

    # TODO [object][flags] Move up to object
    def set_mesh_flags(self, b_obj, trishape):
        # use blender flags
        if (b_obj.type == 'MESH') and (b_obj.niftools.flags != 0):
            trishape.flags = b_obj.niftools.flags
        # fall back to defaults
        else:
            if bpy.context.scene.niftools_scene.is_bs():
                trishape.flags = 0x000E

            elif bpy.context.scene.niftools_scene.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                trishape.flags = 0x0010
            elif bpy.context.scene.niftools_scene.game in ('EMPIRE_EARTH_II',):
                trishape.flags = 0x0016
            elif bpy.context.scene.niftools_scene.game in ('DIVINITY_2',):
                if trishape.name.lower[-3:] in ("med", "low"):
                    trishape.flags = 0x0014
                else:
                    trishape.flags = 0x0016
            else:
                # morrowind
                if b_obj.display_type != 'WIRE':  # not wire
                    trishape.flags = 0x0004  # use triangles as bounding box
                else:
                    trishape.flags = 0x0005  # use triangles as bounding box + hide

    # todo [mesh] join code paths for those two?
    def select_unweighted_vertices(self, b_obj, unweighted_vertices):
        # vertices must be assigned at least one vertex group lets be nice and display them for the user
        if len(unweighted_vertices) > 0:
            for b_scene_obj in bpy.context.scene.objects:
                b_scene_obj.select_set(False)

            bpy.context.view_layer.objects.active = b_obj

            # switch to edit mode to deselect everything in the mesh (not missing vertices or edges)
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.select_all(action='DESELECT')

            # select unweighted vertices - switch back to object mode to make per-vertex selection
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            for vert_index in unweighted_vertices:
                b_obj.data.vertices[vert_index].select = True

            # switch back to edit mode to make the selection visible and raise exception
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            raise NifError("Cannot export mesh with unweighted vertices. "
                           "The unweighted vertices have been selected in the mesh so they can easily be identified.")

    def select_unassigned_polygons(self, b_mesh, b_obj, polygons_without_bodypart):
        """Select any faces which are not weighted to a vertex group"""
        ngon_mesh = b_obj.data
        # make vertex: poly map of the untriangulated mesh
        vert_poly_dict = {i: set() for i in range(len(ngon_mesh.vertices))}
        for face in ngon_mesh.polygons:
            for vertex in face.vertices:
                vert_poly_dict[vertex].add(face.index)

        # translate the tris of polygons_without_bodypart to polygons (assuming vertex order does not change)
        ngons_without_bodypart = []
        for face in polygons_without_bodypart:
            poly_set = vert_poly_dict[face.vertices[0]]
            for vertex in face.vertices[1:]:
                poly_set = poly_set.intersection(vert_poly_dict[vertex])
                if len(poly_set) == 0:
                    break
            else:
                for poly in poly_set:
                    ngons_without_bodypart.append(poly)

        # switch to object mode so (de)selecting faces works
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # select mesh object
        for b_deselect_obj in bpy.context.scene.objects:
            b_deselect_obj.select_set(False)
        bpy.context.view_layer.objects.active = b_obj
        # switch to edit mode to deselect everything in the mesh (not missing vertices or edges)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.select_all(action='DESELECT')

        # switch back to object mode to make per-face selection
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for poly in ngons_without_bodypart:
            ngon_mesh.polygons[poly].select = True

        # select bad polygons switch to edit mode to select polygons
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # raise exception
        raise NifError(f"Some polygons of {b_obj.name} not assigned to any body part."
                       f"The unassigned polygons have been selected in the mesh so they can easily be identified.")

    def export_texture_effect(self, n_block, b_mat):
        # todo [texture] detect effect
        ref_mtex = False
        if ref_mtex:
            # create a new parent block for this shape
            extra_node = block_store.create_block("NiNode", ref_mtex)
            n_block.add_child(extra_node)
            # set default values for this ninode
            extra_node.rotation.set_identity()
            extra_node.scale = 1.0
            extra_node.flags = 0x000C  # morrowind
            # create texture effect block and parent the texture effect and n_geom to it
            texeff = self.texture_helper.export_texture_effect(ref_mtex)
            extra_node.add_child(texeff)
            extra_node.add_effect(texeff)
            return extra_node
        return n_block

    def get_evaluated_mesh(self, b_obj):
        # get the armature influencing this mesh, if it exists
        b_armature_obj = b_obj.find_armature()
        if b_armature_obj:
            old_position = b_armature_obj.data.pose_position
            b_armature_obj.data.pose_position = 'REST'

        # make a copy with all modifiers applied
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = b_obj.evaluated_get(dg)
        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
        if b_armature_obj:
            b_armature_obj.data.pose_position = old_position
        return eval_mesh

    def add_defined_tangents(self, n_geom, tangents, bitangents, as_extra_data):
        # check if size of tangents and bitangents is equal to num_vertices
        if not (len(tangents) == len(bitangents) == n_geom.data.num_vertices):
            raise NifError(f'Number of tangents or bitangents does not agree with number of vertices in {n_geom.name}')

        if as_extra_data:
            # if tangent space extra data already exists, use it
            # find possible extra data block
            extra_name = 'Tangent space (binormal & tangent vectors)'
            for extra in n_geom.get_extra_datas():
                if isinstance(extra, NifClasses.NiBinaryExtraData):
                    if extra.name == extra_name:
                        break
            else:
                # create a new block and link it
                extra = NifClasses.NiBinaryExtraData(NifData.data)
                extra.name = extra_name
                n_geom.add_extra_data(extra)
            # write the data
            extra.binary_data = np.concatenate((tangents, bitangents), axis=0).astype('<f').tobytes()
        else:
            # set tangent space flag
            n_geom.data.bs_data_flags.has_tangents = True
            n_geom.data.data_flags.nbt_method |= 1
            # XXX used to be 61440
            # XXX from Sid Meier's Railroad
            n_geom.data.reset_field("tangents")
            for n_v, b_v in zip(n_geom.data.tangents, tangents):
                n_v.x, n_v.y, n_v.z = b_v
            n_geom.data.reset_field("bitangents")
            for n_v, b_v in zip(n_geom.data.bitangents, bitangents):
                n_v.x, n_v.y, n_v.z = b_v
