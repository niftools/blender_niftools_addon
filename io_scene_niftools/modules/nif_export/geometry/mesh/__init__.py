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
import mathutils

from pyffi.formats.nif import NifFormat

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.geometry import mesh
from io_scene_niftools.modules.nif_export.animation.morph import MorphAnimation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.property.object import ObjectProperty
from io_scene_niftools.modules.nif_export.property.texture.types.nitextureprop import NiTextureProp
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp, NifData
from io_scene_niftools.utils.logging import NifLog, NifError


class Mesh:

    def __init__(self):
        self.texture_helper = NiTextureProp.get()
        self.object_property = ObjectProperty()
        self.morph_anim = MorphAnimation()

    def export_tri_shapes(self, b_obj, n_parent, trishape_name=None):
        """
        Export a blender object ob of the type mesh, child of nif block
        n_parent, as NiTriShape and NiTriShapeData blocks, possibly
        along with some NiTexturingProperty, NiSourceTexture,
        NiMaterialProperty, and NiAlphaProperty blocks. We export one
        trishape block per mesh material. We also export vertex weights.

        The parameter trishape_name passes on the name for meshes that
        should be exported as a single mesh.
        """
        NifLog.info(f"Exporting {b_obj}")

        assert (b_obj.type == 'MESH')

        # get mesh from b_obj
        b_mesh = self.get_triangulated_mesh(b_obj)

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not b_mesh.vertices:
            # do not export anything
            NifLog.warn(f"{b_obj} has no vertices, skipped.")
            return

        # get the mesh's materials, this updates the mesh material list
        if not isinstance(n_parent, NifFormat.RootCollisionNode):
            mesh_materials = b_mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_materials = []

        # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
        if not mesh_materials:
            mesh_materials = [None]

        # vertex color check
        mesh_hasvcol = b_mesh.vertex_colors
        # list of body part (name, index, vertices) in this mesh
        bodypartgroups = self.get_body_part_groups(b_obj, b_mesh)

        # Non-textured materials, vertex colors are used to color the mesh
        # Textured materials, they represent lighting details

        # let's now export one trishape for every mesh material
        # TODO [material] needs refactoring - move material, texture, etc. to separate function
        for materialIndex, b_mat in enumerate(mesh_materials):

            mesh_hasnormals = False
            if b_mat is not None:
                mesh_hasnormals = True  # for proper lighting
                if (bpy.context.scene.niftools_scene.game == 'SKYRIM') and (b_mat.niftools_shader.bslsp_shaderobjtype == 'Skin Tint'):
                    mesh_hasnormals = False  # for proper lighting

            # create a trishape block
            if not NifOp.props.stripify:
                trishape = block_store.create_block("NiTriShape", b_obj)
            else:
                trishape = block_store.create_block("NiTriStrips", b_obj)

            # fill in the NiTriShape's non-trivial values
            if isinstance(n_parent, NifFormat.RootCollisionNode):
                trishape.name = ""
            else:
                if not trishape_name:
                    if n_parent.name:
                        trishape.name = "Tri " + n_parent.name.decode()
                    else:
                        trishape.name = "Tri " + b_obj.name.decode()
                else:
                    trishape.name = trishape_name

                # multimaterial meshes: add material index (Morrowind's child naming convention)
                if len(mesh_materials) > 1:
                    trishape.name = f"{trishape.name.decode()}: {materialIndex}"
                else:
                    trishape.name = block_store.get_full_name(trishape)

            self.set_mesh_flags(b_obj, trishape)

            # extra shader for Sid Meier's Railroads
            if bpy.context.scene.niftools_scene.game == 'SID_MEIER_S_RAILROADS':
                trishape.has_shader = True
                trishape.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                trishape.unknown_integer = -1  # default

            # if we have an animation of a blender mesh
            # an intermediate NiNode has been created which holds this b_obj's transform
            # the trishape itself then needs identity transform (default)
            if trishape_name is not None:
                # only export the bind matrix on trishapes that were not animated
                math.set_object_matrix(b_obj, trishape)

            # check if there is a parent
            if n_parent:
                # add texture effect block (must be added as parent of the trishape)
                n_parent = self.export_texture_effect(n_parent, b_mat)
                # refer to this mesh in the parent's children list
                n_parent.add_child(trishape)

            self.object_property.export_properties(b_obj, b_mat, trishape)

            # -> now comes the real export

            '''
                NIF has one uv vertex and one normal per vertex,
                per vert, vertex coloring.

                NIF uses the normal table for lighting.
                Smooth faces should use Blender's vertex normals,
                solid faces should use Blender's face normals.

                Blender's uv vertices and normals per face.
                Blender supports per face vertex coloring,
            '''

            # We now extract vertices, uv-vertices, normals, and
            # vertex colors from the mesh's face list. Some vertices must be duplicated.

            # The following algorithm extracts all unique quads(vert, uv-vert, normal, vcol),
            # produce lists of vertices, uv-vertices, normals, vertex colors, and face indices.

            mesh_uv_layers = b_mesh.uv_layers
            vertquad_list = []  # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [None for _ in range(len(b_mesh.vertices))]  # blender vertex -> nif vertices
            vertlist = []
            normlist = []
            vcollist = []
            uvlist = []
            trilist = []
            # for each face in trilist, a body part index
            bodypartfacemap = []
            polygons_without_bodypart = []
            for poly in b_mesh.polygons:

                # does the face belong to this trishape?
                if b_mat is not None and poly.material_index != materialIndex:
                    # we have a material but this face has another material, so skip
                    continue

                f_numverts = len(poly.vertices)
                if f_numverts < 3:
                    continue  # ignore degenerate polygons
                assert ((f_numverts == 3) or (f_numverts == 4))  # debug
                if mesh_uv_layers:
                    # if we have uv coordinates double check that we have uv data
                    if not b_mesh.uv_layer_stencil:
                        NifLog.warn(f"No UV map for texture associated with poly {poly.index:s} of selected mesh '{b_mesh.name}'.")

                # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
                f_index = [-1] * f_numverts
                for i, loop_index in enumerate(range(poly.loop_start, poly.loop_start + poly.loop_total)):

                    fv_index = b_mesh.loops[loop_index].vertex_index
                    vertex = b_mesh.vertices[fv_index]
                    vertex_index = vertex.index
                    fv = vertex.co

                    # smooth = vertex normal, non-smooth = face normal)
                    if mesh_hasnormals:
                        if poly.use_smooth:
                            fn = vertex.normal
                        else:
                            fn = poly.normal
                    else:
                        fn = None

                    fuv = [uv_layer.data[loop_index].uv for uv_layer in b_mesh.uv_layers]

                    # TODO [geomotry][mesh] Need to map b_verts -> n_verts
                    if mesh_hasvcol:
                        f_col = list(b_mesh.vertex_colors[0].data[loop_index].color)
                    else:
                        f_col = None

                    vertquad = (fv, fuv, fn, f_col)

                    # check for duplicate vertquad?
                    f_index[i] = len(vertquad_list)
                    if vertmap[vertex_index] is not None:
                        # iterate only over vertices with the same vertex index
                        for j in vertmap[vertex_index]:
                            # check if they have the same uvs, normals and colors
                            if self.is_new_face_corner_data(vertquad, vertquad_list[j]):
                                continue
                            # all tests passed: so yes, we already have a vert with the same face corner data!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise io_scene_niftools.utils.logging.NifError("Too many vertices. Decimate your mesh and try again.")

                    if f_index[i] == len(vertquad_list):
                        # first: add it to the vertex map
                        if not vertmap[vertex_index]:
                            vertmap[vertex_index] = []
                        vertmap[vertex_index].append(len(vertquad_list))
                        # new (vert, uv-vert, normal, vcol) quad: add it
                        vertquad_list.append(vertquad)

                        # add the vertex
                        vertlist.append(vertquad[0])
                        if mesh_hasnormals:
                            normlist.append(vertquad[2])
                        if mesh_hasvcol:
                            vcollist.append(vertquad[3])
                        if mesh_uv_layers:
                            uvlist.append(vertquad[1])

                # now add the (hopefully, convex) face, in triangles
                for i in range(f_numverts - 2):
                    if (b_obj.scale.x + b_obj.scale.y + b_obj.scale.z) > 0:
                        f_indexed = (f_index[0], f_index[1 + i], f_index[2 + i])
                    else:
                        f_indexed = (f_index[0], f_index[2 + i], f_index[1 + i])
                    trilist.append(f_indexed)

                    # add body part number
                    if bpy.context.scene.niftools_scene.game not in ('FALLOUT_3', 'SKYRIM') or not bodypartgroups:
                        # TODO: or not self.EXPORT_FO3_BODYPARTS):
                        bodypartfacemap.append(0)
                    else:
                        for bodypartname, bodypartindex, bodypartverts in bodypartgroups:
                            if set(b_vert_index for b_vert_index in poly.vertices) <= bodypartverts:
                                bodypartfacemap.append(bodypartindex)
                                break
                        else:
                            # this signals an error
                            polygons_without_bodypart.append(poly)

            # check that there are no missing body part polygons
            if polygons_without_bodypart:
                self.select_unassigned_polygons(b_mesh, b_obj, polygons_without_bodypart)

            if len(trilist) > 65535:
                raise io_scene_niftools.utils.logging.NifError("Too many polygons. Decimate your mesh and try again.")
            if len(vertlist) == 0:
                continue  # m_4444x: skip 'empty' material indices

            # add NiTriShape's data
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = block_store.create_block("NiTriShapeData", b_obj)
            else:
                tridata = block_store.create_block("NiTriStripsData", b_obj)
            trishape.data = tridata

            # data
            tridata.num_vertices = len(vertlist)
            tridata.has_vertices = True
            tridata.vertices.update_size()
            for i, v in enumerate(tridata.vertices):
                v.x, v.y, v.z = vertlist[i]
            tridata.update_center_radius()

            if mesh_hasnormals:
                tridata.has_normals = True
                tridata.normals.update_size()
                for i, v in enumerate(tridata.normals):
                    v.x, v.y, v.z = normlist[i]

            if mesh_hasvcol:
                tridata.has_vertex_colors = True
                tridata.vertex_colors.update_size()
                for i, v in enumerate(tridata.vertex_colors):
                    v.r, v.g, v.b, v.a = vcollist[i]

            if mesh_uv_layers:
                tridata.num_uv_sets = len(mesh_uv_layers)
                tridata.bs_num_uv_sets = len(mesh_uv_layers)
                if bpy.context.scene.niftools_scene.game == 'FALLOUT_3':
                    if len(mesh_uv_layers) > 1:
                        raise io_scene_niftools.utils.logging.NifError("Fallout 3 does not support multiple UV layers")
                tridata.has_uv = True
                tridata.uv_sets.update_size()
                for j, uv_layer in enumerate(mesh_uv_layers):
                    for i, uv in enumerate(tridata.uv_sets[j]):
                        if len(uvlist[i]) == 0:
                            continue  # skip non-uv textures
                        uv.u = uvlist[i][j][0]
                        # NIF flips the texture V-coordinate (OpenGL standard)
                        uv.v = 1.0 - uvlist[i][j][1]  # opengl standard

            # set triangles stitch strips for civ4
            tridata.set_triangles(trilist, stitchstrips=NifOp.props.stitch_strips)

            # update tangent space (as binary extra data only for Oblivion)
            # for extra shader texture games, only export it if those textures are actually exported
            # (civ4 seems to be consistent with not using tangent space on non shadered nifs)
            if mesh_uv_layers and mesh_hasnormals:
                if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') or (bpy.context.scene.niftools_scene.game in self.texture_helper.USED_EXTRA_SHADER_TEXTURES):
                    if bpy.context.scene.niftools_scene.game == 'SKYRIM':
                        tridata.bs_num_uv_sets = tridata.bs_num_uv_sets + 4096
                    trishape.update_tangent_space(as_extra=(bpy.context.scene.niftools_scene.game == 'OBLIVION'))

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
                    n_root_name = block_store.get_full_name(b_obj_armature)
                    skininst, skindata = self.create_skin_inst_data(b_obj, n_root_name, bodypartgroups)
                    trishape.skin_instance = skininst

                    # Vertex weights,  find weights and normalization factors
                    vert_list = {}
                    vert_norm = {}
                    unweighted_vertices = []

                    for bone_group in boneinfluences:
                        b_list_weight = []
                        b_vert_group = b_obj.vertex_groups[bone_group]

                        for b_vert in b_mesh.vertices:
                            if len(b_vert.groups) == 0:  # check vert has weight_groups
                                unweighted_vertices.append(b_vert)
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

                    self.select_unweighted_vertices(unweighted_vertices)

                    # for each bone, first we get the bone block then we get the vertex weights and then we add it to the NiSkinData
                    # note: allocate memory for faster performance
                    vert_added = [False for _ in range(len(vertlist))]
                    for b_bone_name in boneinfluences:
                        # find bone in exported blocks
                        bone_block = self.get_bone_block(b_obj_armature.data.bones[b_bone_name])

                        # find vertex weights
                        vert_weights = {}
                        for v in vert_list[b_bone_name]:
                            # v[0] is the original vertex index
                            # v[1] is the weight

                            # vertmap[v[0]] is the set of vertices (indices) to which v[0] was mapped
                            # so we simply export the same weight as the original vertex for each new vertex

                            # write the weights
                            # extra check for multi material meshes
                            if vertmap[v[0]] and vert_norm[v[0]]:
                                for vert_index in vertmap[v[0]]:
                                    vert_weights[vert_index] = v[1] / vert_norm[v[0]]
                                    vert_added[vert_index] = True
                        # add bone as influence, but only if there were actually any vertices influenced by the bone
                        if vert_weights:
                            trishape.add_bone(bone_block, vert_weights)

                    # update bind position skinning data
                    trishape.update_bind_position()

                    # calculate center and radius for each skin bone data block
                    trishape.update_skin_center_radius()

                    if NifData.data.version >= 0x04020100 and NifOp.props.skin_partition:
                        NifLog.info("Creating skin partition")
                        lostweight = trishape.update_skin_partition(
                            maxbonesperpartition=NifOp.props.max_bones_per_partition,
                            maxbonespervertex=NifOp.props.max_bones_per_vertex,
                            stripify=NifOp.props.stripify,
                            stitchstrips=NifOp.props.stitch_strips,
                            padbones=NifOp.props.pad_bones,
                            triangles=trilist,
                            trianglepartmap=bodypartfacemap,
                            maximize_bone_sharing=(bpy.context.scene.niftools_scene.game in ('FALLOUT_3', 'SKYRIM')))

                        # warn on bad config settings
                        if bpy.context.scene.niftools_scene.game == 'OBLIVION':
                            if NifOp.props.pad_bones:
                                NifLog.warn("Using padbones on Oblivion export. Disable the pad bones option to get higher quality skin partitions.")
                        if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3'):
                            if NifOp.props.max_bones_per_partition < 18:
                                NifLog.warn("Using less than 18 bones per partition on Oblivion/Fallout 3 export."
                                            "Set it to 18 to get higher quality skin partitions.")
                        if bpy.context.scene.niftools_scene.game in 'SKYRIM':
                            if NifOp.props.max_bones_per_partition < 24:
                                NifLog.warn("Using less than 24 bones per partition on Skyrim export."
                                            "Set it to 24 to get higher quality skin partitions.")
                        if lostweight > NifOp.props.epsilon:
                            NifLog.warn(f"Lost {lostweight:f} in vertex weights while creating a skin partition for Blender object '{b_obj.name}' (nif block '{trishape.name}')")

                    if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
                        partitions = skininst.partitions
                        b_obj_part_flags = b_obj.niftools_part_flags
                        for s_part in partitions:
                            s_part_index = NifFormat.BSDismemberBodyPartType._enumvalues.index(s_part.body_part)
                            s_part_name = NifFormat.BSDismemberBodyPartType._enumkeys[s_part_index]
                            for b_part in b_obj_part_flags:
                                if s_part_name == b_part.name:
                                    s_part.part_flag.pf_start_net_boneset = b_part.pf_startflag
                                    s_part.part_flag.pf_editor_visible = b_part.pf_editorflag

                    # clean up
                    del vert_weights
                    del vert_added

            # fix data consistency type
            tridata.consistency_flags = b_obj.niftools.consistency_flags

            # export EGM or NiGeomMorpherController animation
            self.morph_anim.export_morph(b_mesh, trishape, vertmap)
        return trishape

    def get_bone_block(self, b_bone):
        """For a blender bone, return the corresponding nif node from the blocks that have already been exported"""
        for n_block, b_obj in block_store.block_to_obj.items():
            if isinstance(n_block, NifFormat.NiNode) and b_bone == b_obj:
                return n_block
        raise io_scene_niftools.utils.logging.NifError(f"Bone '{b_bone.name}' not found.")

    def get_body_part_groups(self, b_obj, b_mesh):
        """Returns a set of vertices (no dupes) for each body part"""
        bodypartgroups = []
        for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
            vertex_group = b_obj.vertex_groups.get(bodypartgroupname)
            vertices_list = set()
            if vertex_group:
                for b_vert in b_mesh.vertices:
                    for b_groupname in b_vert.groups:
                        if b_groupname.group == vertex_group.index:
                            vertices_list.add(b_vert.index)
                NifLog.debug(f"Found body part {bodypartgroupname}")
                bodypartgroups.append(
                    [bodypartgroupname, getattr(NifFormat.BSDismemberBodyPartType, bodypartgroupname), vertices_list])
        return bodypartgroups

    def create_skin_inst_data(self, b_obj, n_root_name, bodypartgroups):
        if bpy.context.scene.niftools_scene.game in ('FALLOUT_3', 'SKYRIM') and bodypartgroups:
            skininst = block_store.create_block("BSDismemberSkinInstance", b_obj)
        else:
            skininst = block_store.create_block("NiSkinInstance", b_obj)
        for block in block_store.block_to_obj:
            if isinstance(block, NifFormat.NiNode):
                if block.name.decode() == n_root_name:
                    skininst.skeleton_root = block
                    break
        else:
            raise io_scene_niftools.utils.logging.NifError(f"Skeleton root '{n_root_name}' not found.")

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
            if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
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
    def select_unweighted_vertices(self, unweighted_vertices):
        # vertices must be assigned at least one vertex group lets be nice and display them for the user
        if len(unweighted_vertices) > 0:
            for b_scene_obj in bpy.context.scene.objects:
                b_scene_obj.select_set(False)

            b_obj = bpy.context.view_layer.objects.active
            b_obj.select_set(True)

            # switch to edit mode and raise exception
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            # clear all currently selected vertices
            bpy.ops.mesh.select_all(action='DESELECT')
            # select unweighted vertices
            bpy.ops.mesh.select_ungrouped(extend=False)

            raise io_scene_niftools.utils.logging.NifError("Cannot export mesh with unweighted vertices. "
                                     "The unweighted vertices have been selected in the mesh so they can easily be identified.")


    def select_unassigned_polygons(self, b_mesh, b_obj, polygons_without_bodypart):
        """Select any faces which are not weighted to a vertex group"""
        # select mesh object
        for b_deselect_obj in bpy.context.scene.objects:
            b_deselect_obj.select_set(False)
        bpy.context.view_layer.objects.active = b_obj
        b_obj.select_set(True)
        for face in b_mesh.polygons:
            face.select = False
        for face in polygons_without_bodypart:
            face.select = True

        # select bad polygons switch to edit mode to select polygons
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # raise exception
        raise NifError(f"Some polygons of {b_obj.name} not assigned to any body part."
                       f"The unassigned polygons have been selected in the mesh so they can easily be identified.")

    def is_new_face_corner_data(self, vertquad, v_quad_old):
        """Compares vert info to old vert info if relevant data is present"""
        # uvs
        if v_quad_old[1]:
            for i in range(2):
                if max(abs(vertquad[1][uv_index][i] - v_quad_old[1][uv_index][i]) for uv_index in
                       range(len(v_quad_old[1]))) > NifOp.props.epsilon:
                    return True
        # normals
        if v_quad_old[2]:
            for i in range(3):
                if abs(vertquad[2][i] - v_quad_old[2][i]) > NifOp.props.epsilon:
                    return True
        # vcols
        if v_quad_old[3]:
            for i in range(4):
                if abs(vertquad[3][i] - v_quad_old[3][i]) > NifOp.props.epsilon:
                    return True

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
            # create texture effect block and parent the texture effect and trishape to it
            texeff = self.texture_helper.export_texture_effect(ref_mtex)
            extra_node.add_child(texeff)
            extra_node.add_effect(texeff)
            return extra_node
        return n_block

    def get_triangulated_mesh(self, b_obj):
        # get the armature influencing this mesh, if it exists
        b_armature_obj = b_obj.find_armature()
        if b_armature_obj:
            for pbone in b_armature_obj.pose.bones:
                pbone.matrix_basis = mathutils.Matrix()

        # make sure the model has a triangulation modifier
        self.ensure_tri_modifier(b_obj)

        # make a copy with all modifiers applied
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = b_obj.evaluated_get(dg)
        return eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dg)

    def ensure_tri_modifier(self, b_obj):
        """Makes sure that ob has a triangulation modifier in its stack."""
        for mod in b_obj.modifiers:
            if mod.type in ('TRIANGULATE',):
                break
        else:
            b_obj.modifiers.new('Triangulate', 'TRIANGULATE')