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


from io_scene_nif.modules.nif_export.geometry import mesh
from io_scene_nif.modules.nif_export.animation.material import MaterialAnimation
from io_scene_nif.modules.nif_export.animation.morph import MorphAnimation
from io_scene_nif.modules.nif_export.block_registry import block_store
from io_scene_nif.modules.nif_export.property.material import MaterialProp
from io_scene_nif.modules.nif_export.property.object import ObjectProperty
from io_scene_nif.modules.nif_export.property.shader import BSShaderProperty
from io_scene_nif.modules.nif_export.property.texture.types.nitextureprop import NiTextureProp
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_math import NifError
from io_scene_nif.utils.util_global import NifOp, NifData
from io_scene_nif.utils.util_logging import NifLog

# TODO [scene][property][ui] Expose these either through the scene or as ui properties
VERTEX_RESOLUTION = 1000
NORMAL_RESOLUTION = 100


class Mesh:

    def __init__(self):
        self.texture_helper = NiTextureProp.get()
        self.bss_helper = BSShaderProperty()
        self.object_property = ObjectProperty()
        self.material_property = MaterialProp()
        self.material_anim = MaterialAnimation()
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
        NifLog.info("Exporting {0}".format(b_obj))

        assert (b_obj.type == 'MESH')

        # get mesh from b_obj
        b_mesh = b_obj.data  # get mesh data

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not b_obj.data.vertices:
            # do not export anything
            NifLog.warn("{0} has no vertices, skipped.".format(b_obj))
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

        # is mesh double sided?
        # todo [mesh/material] detect from material settings!
        mesh_doublesided = True

        # vertex color check
        mesh_hasvcol = b_mesh.vertex_colors

        # Non-textured materials, vertex colors are used to color the mesh
        # Textured materials, they represent lighting details

        # let's now export one trishape for every mesh material
        # TODO [material] needs refactoring - move material, texture, etc. to separate function
        for materialIndex, b_mat in enumerate(mesh_materials):

            b_ambient_prop = False
            b_diffuse_prop = False
            b_spec_prop = False
            b_emissive_prop = False
            b_gloss_prop = False
            b_alpha_prop = False
            b_emit_prop = False

            # todo [material/texture] reimplement for node materials
            # # use the texture properties as preference
            # for b_slot in self.texture_helper.get_used_textslots(b_mat):
            #     # replace with texture helper queries
            #     b_ambient_prop |= b_slot.use_map_ambient
            #     b_diffuse_prop |= b_slot.use_map_color_diffuse
            #     b_spec_prop |= b_slot.use_map_color_spec
            #     b_emissive_prop |= b_slot.use_map_emit
            #     b_gloss_prop |= b_slot.use_map_hardness
            #     b_alpha_prop |= b_slot.use_map_alpha
            #     b_emit_prop |= b_slot.use_map_emit

            # -> first, extract valuable info from our b_obj

            mesh_texture_alpha = False  # texture has transparency

            mesh_uv_layers = []  # uv layers used by this material
            mesh_hasalpha = False  # mesh has transparency
            mesh_haswire = False  # mesh rendered as wireframe
            mesh_hasspec = False  # mesh specular property

            mesh_hasnormals = False
            if b_mat is not None:
                mesh_hasnormals = True  # for proper lighting
                if (NifOp.props.game == 'SKYRIM') and (b_mat.niftools_shader.bslsp_shaderobjtype == 'Skin Tint'):
                    mesh_hasnormals = False  # for proper lighting

                # ambient mat
                mesh_mat_ambient_color = b_mat.niftools.ambient_color
                # diffuse mat
                mesh_mat_diffuse_color = b_mat.diffuse_color
                # emissive mat
                mesh_mat_emissive_color = b_mat.niftools.emissive_color
                # mesh_mat_emitmulti = b_mat.emit
                mesh_mat_emitmulti = b_mat.niftools.emissive_color
                # specular mat
                mesh_mat_specular_color = b_mat.specular_color

                eps = NifOp.props.epsilon
                if (mesh_mat_specular_color.r > eps) or (mesh_mat_specular_color.g > eps) or (mesh_mat_specular_color.b > eps):
                    mesh_hasspec = b_spec_prop

                # gloss mat 'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_gloss = b_mat.specular_intensity

                # alpha mat
                # todo [material] check for transparent node in node tree
                mesh_hasalpha = b_alpha_prop
                mesh_mat_transparency = 1
                if b_mat.blend_method != "OPAQUE":
                    mesh_hasalpha = True
                elif mesh_hasvcol:
                    mesh_hasalpha = True
                elif b_mat.animation_data and 'Alpha' in b_mat.animation_data.action.fcurves:
                    mesh_hasalpha = True

                # wire mat
                # mesh_haswire = (b_mat.type == 'WIRE')
                # todo [material] find alternative
                mesh_haswire = False

            # list of body part (name, index, vertices) in this mesh
            bodypartgroups = []
            for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
                vertex_group = b_obj.vertex_groups.get(bodypartgroupname)
                vertices_list = set()
                if vertex_group:
                    for b_vert in b_mesh.vertices:
                        for b_groupname in b_vert.groups:
                            if b_groupname.group == vertex_group.index:
                                vertices_list.add(b_vert.index)
                    NifLog.debug("Found body part {0}".format(bodypartgroupname))
                    bodypartgroups.append([bodypartgroupname, getattr(NifFormat.BSDismemberBodyPartType, bodypartgroupname), vertices_list])

            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

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
                    trishape.name = trishape.name.decode() + ":%i" % materialIndex
                else:
                    trishape.name = block_store.get_full_name(trishape)

            self.set_mesh_flags(b_obj, trishape)

            # extra shader for Sid Meier's Railroads
            if NifOp.props.game == 'SID_MEIER_S_RAILROADS':
                trishape.has_shader = True
                trishape.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                trishape.unknown_integer = -1  # default

            # if we have an animation of a blender mesh
            # an intermediate NiNode has been created which holds this b_obj's transform
            # the trishape itself then needs identity transform (default)
            if trishape_name is not None:
                # only export the bind matrix on trishapes that were not animated
                util_math.set_object_matrix(b_obj, trishape)

            # add textures
            if NifOp.props.game == 'FALLOUT_3':
                if b_mat:
                    bsshader = self.bss_helper.export_bs_shader_property(b_mat)

                    block_store.register_block(bsshader)
                    trishape.add_property(bsshader)
            elif NifOp.props.game == 'SKYRIM':
                if b_mat:
                    bsshader = self.bss_helper.export_bs_shader_property(b_mat)

                    block_store.register_block(bsshader)
                    num_props = trishape.num_properties
                    trishape.num_properties = num_props + 1
                    trishape.bs_properties.update_size()
                    trishape.bs_properties[num_props] = bsshader

            else:
                if NifOp.props.game in self.texture_helper.USED_EXTRA_SHADER_TEXTURES:
                    # sid meier's railroad and civ4: set shader slots in extra data
                    self.texture_helper.add_shader_integer_extra_datas(trishape)

                if b_mat:
                    n_nitextureprop = self.texture_helper.export_texturing_property(
                        flags=0x0001,  # standard
                        # TODO [object][texture][material] Move out and break dependency
                        applymode=self.texture_helper.get_n_apply_mode_from_b_blend_type('MIX'),
                        b_mat=b_mat)

                    block_store.register_block(n_nitextureprop)
                    trishape.add_property(n_nitextureprop)

            # add texture effect block (must be added as preceding child of the trishape)
            if n_parent:
                # todo [texture] detect effect and move out
                # ref_mtex = self.texture_helper.b_ref_slot
                ref_mtex = False
                if NifOp.props.game == 'MORROWIND' and ref_mtex:
                    # create a new parent block for this shape
                    extra_node = block_store.create_block("NiNode", ref_mtex)
                    n_parent.add_child(extra_node)
                    # set default values for this ninode
                    extra_node.rotation.set_identity()
                    extra_node.scale = 1.0
                    extra_node.flags = 0x000C  # morrowind
                    # create texture effect block and parent the texture effect and trishape to it
                    texeff = self.texture_helper.export_texture_effect(ref_mtex)
                    extra_node.add_child(texeff)
                    extra_node.add_child(trishape)
                    extra_node.add_effect(texeff)
                else:
                    # refer to this block in the parent's children list
                    n_parent.add_child(trishape)

            if mesh_hasalpha:
                # add NiTriShape's alpha propery refer to the alpha property in the trishape block
                trishape.add_property(self.object_property.export_alpha_property(b_mat))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.add_property(self.object_property.export_wireframe_property(flags=1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.add_property(self.object_property.export_stencil_property())

            if b_mat and not (NifOp.props.game == 'SKYRIM'):
                # add NiTriShape's specular property
                # but NOT for sid meier's railroads and other extra shader
                # games (they use specularity even without this property)
                if mesh_hasspec and (NifOp.props.game not in self.texture_helper.USED_EXTRA_SHADER_TEXTURES):
                    # refer to the specular property in the trishape block
                    trishape.add_property(self.object_property.export_specular_property(flags=0x0001))

                # add NiTriShape's material property
                trimatprop = self.material_property.export_material_property(
                    name=block_store.get_full_name(b_mat),
                    flags=0x0001,
                    # TODO: - standard flag, check? material and texture properties in morrowind style nifs had a flag
                    ambient=mesh_mat_ambient_color,
                    diffuse=mesh_mat_diffuse_color,
                    specular=mesh_mat_specular_color,
                    emissive=mesh_mat_emissive_color,
                    gloss=mesh_mat_gloss,
                    alpha=mesh_mat_transparency,
                    emitmulti=mesh_mat_emitmulti)

                block_store.register_block(trimatprop)

                # refer to the material property in the trishape block
                trishape.add_property(trimatprop)

                # material animation
                self.material_anim.export_material(b_mat, trishape)

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
                        NifLog.warn("No UV map for texture associated with poly {0} of selected mesh '{1}'.".format(str(poly.index), b_mesh.name))

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
                        # iterate only over vertices with the same vertex index and check if they have the same uvs, normals and colors
                        for j in vertmap[vertex_index]:
                            # TODO use function to do comparison
                            if mesh_uv_layers:
                                num_uvs_layers = len(mesh_uv_layers)
                                if max(abs(vertquad[1][uv_layer][0] - vertquad_list[j][1][uv_layer][0]) for uv_layer in range(num_uvs_layers)) > NifOp.props.epsilon:
                                    continue
                                if max(abs(vertquad[1][uv_layer][1] - vertquad_list[j][1][uv_layer][1]) for uv_layer in range(num_uvs_layers)) > NifOp.props.epsilon:
                                    continue
                            if mesh_hasnormals:
                                if abs(vertquad[2][0] - vertquad_list[j][2][0]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[2][1] - vertquad_list[j][2][1]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[2][2] - vertquad_list[j][2][2]) > NifOp.props.epsilon:
                                    continue
                            if mesh_hasvcol:
                                if abs(vertquad[3][0] - vertquad_list[j][3][0]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][1] - vertquad_list[j][3][1]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][2] - vertquad_list[j][3][2]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][3] - vertquad_list[j][3][3]) > NifOp.props.epsilon:
                                    continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise util_math.NifError("Too many vertices. Decimate your mesh and try again.")

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
                    if NifOp.props.game not in ('FALLOUT_3', 'SKYRIM') or not bodypartgroups:
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
                self.select_unweighted_vertices(b_mesh, b_obj, polygons_without_bodypart)

            if len(trilist) > 65535:
                raise util_math.NifError("Too many polygons. Decimate your mesh and try again.")
            if len(vertlist) == 0:
                continue  # m_4444x: skip 'empty' material indices

            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = block_store.create_block("NiTriShapeData", b_obj)
            else:
                tridata = block_store.create_block("NiTriStripsData", b_obj)
            trishape.data = tridata

            # flags
            if b_obj.niftools.consistency_flags in NifFormat.ConsistencyType._enumkeys:
                cf_index = NifFormat.ConsistencyType._enumkeys.index(b_obj.niftools.consistency_flags)
                tridata.consistency_flags = NifFormat.ConsistencyType._enumvalues[cf_index]
            else:
                tridata.consistency_flags = NifFormat.ConsistencyType.CT_STATIC
                NifLog.warn("{0} has no consistency type set using default CT_STATIC.".format(b_obj))

            # data
            tridata.num_vertices = len(vertlist)
            tridata.has_vertices = True
            tridata.vertices.update_size()
            for i, v in enumerate(tridata.vertices):
                v.x = vertlist[i][0]
                v.y = vertlist[i][1]
                v.z = vertlist[i][2]
            tridata.update_center_radius()

            if mesh_hasnormals:
                tridata.has_normals = True
                tridata.normals.update_size()
                for i, v in enumerate(tridata.normals):
                    v.x = normlist[i][0]
                    v.y = normlist[i][1]
                    v.z = normlist[i][2]

            if mesh_hasvcol:
                tridata.has_vertex_colors = True
                tridata.vertex_colors.update_size()
                for i, v in enumerate(tridata.vertex_colors):
                    v.r = vcollist[i][0]
                    v.g = vcollist[i][1]
                    v.b = vcollist[i][2]
                    v.a = vcollist[i][3]

            if mesh_uv_layers:
                tridata.num_uv_sets = len(mesh_uv_layers)
                tridata.bs_num_uv_sets = len(mesh_uv_layers)
                if NifOp.props.game == 'FALLOUT_3':
                    if len(mesh_uv_layers) > 1:
                        raise util_math.NifError("Fallout 3 does not support multiple UV layers")
                tridata.has_uv = True
                tridata.uv_sets.update_size()
                for j, uv_layer in enumerate(mesh_uv_layers):
                    for i, uv in enumerate(tridata.uv_sets[j]):
                        if len(uvlist[i]) == 0:
                            continue  # skip non-uv textures
                        uv.u = uvlist[i][j][0]
                        uv.v = 1.0 - uvlist[i][j][1]  # opengl standard

            # set triangles stitch strips for civ4
            tridata.set_triangles(trilist, stitchstrips=NifOp.props.stitch_strips)

            # update tangent space (as binary extra data only for Oblivion)
            # for extra shader texture games, only export it if those textures are actually exported
            # (civ4 seems to be consistent with not using tangent space on non shadered nifs)
            if mesh_uv_layers and mesh_hasnormals:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') or (NifOp.props.game in self.texture_helper.USED_EXTRA_SHADER_TEXTURES):
                    trishape.update_tangent_space(as_extra=(NifOp.props.game == 'OBLIVION'))

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
                    skininst, skindata = self.create_skin_inst_data(b_obj, n_root_name)
                    trishape.skin_instance = skininst

                    # Vertex weights,  find weights and normalization factors
                    vert_list = {}
                    vert_norm = {}
                    unassigned_verts = []

                    for bone_group in boneinfluences:
                        b_list_weight = []
                        b_vert_group = b_obj.vertex_groups[bone_group]

                        for b_vert in b_obj.data.vertices:
                            if len(b_vert.groups) == 0:  # check vert has weight_groups
                                unassigned_verts.append(b_vert)
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

                    self.select_unassigned_vertices(unassigned_verts)

                    # for each bone, first we get the bone block then we get the vertex weights and then we add it to the NiSkinData
                    # note: allocate memory for faster performance
                    vert_added = [False for _ in range(len(vertlist))]
                    for b_bone_name in boneinfluences:
                        # find bone in exported blocks
                        full_bone_name = block_store.get_full_name(b_obj_armature.data.bones[b_bone_name])
                        bone_block = self.get_bone_block(full_bone_name)

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
                            maximize_bone_sharing=(NifOp.props.game in ('FALLOUT_3', 'SKYRIM')))

                        # warn on bad config settings
                        if NifOp.props.game == 'OBLIVION':
                            if NifOp.props.pad_bones:
                                NifLog.warn("Using padbones on Oblivion export. Disable the pad bones option to get higher quality skin partitions.")
                        if NifOp.props.game in ('OBLIVION', 'FALLOUT_3'):
                            if NifOp.props.max_bones_per_partition < 18:
                                NifLog.warn("Using less than 18 bones per partition on Oblivion/Fallout 3 export."
                                            "Set it to 18 to get higher quality skin partitions.")
                        if NifOp.props.game in 'SKYRIM':
                            if NifOp.props.max_bones_per_partition < 24:
                                NifLog.warn("Using less than 24 bones per partition on Skyrim export."
                                            "Set it to 24 to get higher quality skin partitions.")
                        if lostweight > NifOp.props.epsilon:
                            NifLog.warn("Lost {0} in vertex weights while creating a skin partition for Blender object '{1}' (nif block '{2}')".format(
                                str(lostweight), b_obj.name, trishape.name))

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

    def get_bone_block(self, bone_name):
        """For a bone name, return the corresponding nif node from the blocks that have already been exported"""
        bone_block = None
        for block in block_store.block_to_obj:
            if isinstance(block, NifFormat.NiNode):
                if block.name.decode() == bone_name:
                    if not bone_block:
                        bone_block = block
                    else:
                        raise util_math.NifError("Multiple bones with name '{0}': probably you have multiple armatures. "
                                                 "Please parent all meshes to a single armature and try again".format(bone_name))
        if not bone_block:
            raise util_math.NifError("Bone '{0}' not found.".format(bone))
        return bone_block

    def create_skin_inst_data(self, b_obj, n_root_name):
        if NifOp.props.game in ('FALLOUT_3', 'SKYRIM') and bodypartgroups:
            skininst = block_store.create_block("BSDismemberSkinInstance", b_obj)
        else:
            skininst = block_store.create_block("NiSkinInstance", b_obj)
        for block in block_store.block_to_obj:
            if isinstance(block, NifFormat.NiNode):
                if block.name.decode() == n_root_name:
                    skininst.skeleton_root = block
                    break
        else:
            raise util_math.NifError("Skeleton root '%s' not found." % n_root_name)

        # create skinning data and link it
        skindata = block_store.create_block("NiSkinData", b_obj)
        skininst.data = skindata

        skindata.has_vertex_weights = True
        # fix geometry rest pose: transform relative to skeleton root
        skindata.set_transform(util_math.get_object_matrix(b_obj).get_inverse())
        return skininst, skindata

    # TODO [object][flags] Move up to object
    def set_mesh_flags(self, b_obj, trishape):
        # use blender flags
        if (b_obj.type == 'MESH') and (b_obj.niftools.flags != 0):
            trishape.flags = b_obj.niftools.flags
        # fall back to defaults
        else:
            if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                trishape.flags = 0x000E

            elif NifOp.props.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                trishape.flags = 0x0010
            elif NifOp.props.game in ('EMPIRE_EARTH_II',):
                trishape.flags = 0x0016
            elif NifOp.props.game in ('DIVINITY_2',):
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
    def select_unassigned_vertices(self, unassigned_verts):
        # vertices must be assigned at least one vertex group lets be nice and display them for the user
        if len(unassigned_verts) > 0:
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

            raise util_math.NifError("Cannot export mesh with unweighted vertices. "
                                     "The unweighted vertices have been selected in the mesh so they can easily be identified.")


    def select_unweighted_vertices(self, b_mesh, b_obj, polygons_without_bodypart):
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
        raise NifError("Some polygons of {0} not assigned to any body part."
                       "The unassigned polygons have been selected in the mesh so they can easily be identified.".format(b_obj))

    def smooth_mesh_seams(self, b_objs):
        """ Finds vertices that are shared between all blender objects and averages their normals"""
        # get shared vertices
        NifLog.info("Smoothing seams between objects...")
        vdict = {}
        for b_obj in [b_obj for b_obj in b_objs if b_obj.type == 'MESH']:
            b_mesh = b_obj.data
            # for vertex in b_mesh.vertices:
            #    vertex.sel = False
            for poly in b_mesh.polygons:
                for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    pv_index = b_mesh.loops[loop_index].vertex_index
                    vertex = b_mesh.vertices[pv_index]
                    vertex_vec = vertex.co
                    vkey = (int(vertex_vec[0] * mesh.VERTEX_RESOLUTION),
                            int(vertex_vec[1] * mesh.VERTEX_RESOLUTION),
                            int(vertex_vec[2] * mesh.VERTEX_RESOLUTION))
                    try:
                        vdict[vkey].append((vertex, poly, b_mesh))
                    except KeyError:
                        vdict[vkey] = [(vertex, poly, b_mesh)]

        # set normals on shared vertices
        nv = 0
        for vlist in vdict.values():
            if len(vlist) <= 1:
                continue  # not shared

            meshes = set([b_mesh for vertex, poly, b_mesh in vlist])
            if len(meshes) <= 1:
                continue  # not shared

            # take average of all face normals of polygons that have this vertex
            norm = mathutils.Vector()
            for vertex, poly, b_mesh in vlist:
                norm += poly.normal
            norm.normalize()
            # remove outliers (fixes better bodies issue) first calculate fitness of each face
            fitlist = [poly.normal.dot(norm)
                       for vertex, poly, b_mesh in vlist]
            bestfit = max(fitlist)
            # recalculate normals only taking into account
            # well-fitting polygons
            norm = mathutils.Vector()
            for (vertex, poly, b_mesh), fit in zip(vlist, fitlist):
                if fit >= bestfit - 0.2:
                    norm += poly.normal
            norm.normalize()
            # save normal of this vertex
            for vertex, poly, b_mesh in vlist:
                vertex.normal = norm
                # vertex.sel = True
            nv += 1

        NifLog.info("Fixed normals on {0} vertices.".format(str(nv)))
