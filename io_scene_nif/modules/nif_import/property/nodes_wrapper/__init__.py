"""This script contains helper methods to managing importing texture into specific slots."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided
#   with the distribution.
#
# * Neither the name of the NIF File Format Library and Tools
#   project nor the names of its contributors may be used to endorse
#   or promote products derived from this software without specific
#   prior written permission.
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

from io_scene_nif.modules.nif_import.geometry.vertex import Vertex
from io_scene_nif.modules.nif_import.property.texture.loader import TextureLoader
from io_scene_nif.utils.util_logging import NifLog
from io_scene_nif.utils.util_nodes import nodes_iterate

# dictionary of texture files, to reuse textures
DICT_TEXTURES = {}

# TODO [property][texture] Move IMPORT_EMBEDDED_TEXTURES as a import property
IMPORT_EMBEDDED_TEXTURES = False

"""Names (ordered by default index) of shader texture slots for Sid Meier's Railroads and similar games."""
EXTRA_SHADER_TEXTURES = [
    "EnvironmentMapIndex",
    "NormalMapIndex",
    "SpecularIntensityIndex",
    "EnvironmentIntensityIndex",
    "LightCubeMapIndex",
    "ShadowTextureIndex"]


class NodesWrapper:

    def __init__(self):
        self.texture_loader = TextureLoader()
        self.tree = None
        self.b_mat = None
        self.output = None
        self.diffuse_pass = None
        self.diffuse_shader = None
        # raw texture nodes
        self.diffuse_texture = None

    def get_material_from_props(self, n_block, props):
        for prop in props:
            if prop.name:
                name = prop.name.decode()
                if name and name in bpy.data.materials:
                    self.b_mat = bpy.data.materials[name]
                    NifLog.debug(f"Retrieved already imported material {self.b_mat.name} from name {name}")
                else:
                    self.b_mat = bpy.data.materials.new(name)
                    NifLog.debug(f"Created material {name} to store properties in {self.b_mat.name}")
                break
        else:
            # bs shaders often have no name, so generate one from mesh name
            name = n_block.name.decode() + "_nt_mat"
            self.b_mat = bpy.data.materials.new(name)
            NifLog.debug(f"Created material {name} to store properties in {self.b_mat.name}")

        # do initial settings for the material here
        self.clear_default_nodes()
        return self.b_mat

    def set_uv_map(self, b_texture_node, uv_index=0, reflective=False):
        """Attaches a vector node describing the desired coordinate transforms to the texture node's UV input."""
        if reflective:
            uv = self.tree.nodes.new('ShaderNodeTexCoord')
            self.tree.links.new(uv.outputs[6], b_texture_node.inputs[0])
        # use supplied UV maps for everything else, if present
        else:
            uv = self.tree.nodes.new('ShaderNodeUVMap')
            uv.name = "TexCoordIndex" + str(uv_index)
            uv.uv_map = f"UV{uv_index}"
            self.tree.links.new(uv.outputs[0], b_texture_node.inputs[0])
            # todo [texture/anim] if present in nifs, support it and move to anim sys
            # if tex_transform or tex_anim:
            #     transform = tree.nodes.new('ShaderNodeMapping')
            #     # todo [texture] negate V coordinate
            #     if tex_transform:
            #         matrix_4x4 = mathutils.Matrix(tex_transform)
            #         transform.scale = matrix_4x4.to_scale()
            #         transform.rotation = matrix_4x4.to_euler()
            #         transform.translation = matrix_4x4.to_translation()
            #         transform.name = "TextureTransform" + str(i)
            #     if tex_anim:
            #         for j, dtype in enumerate(("offsetu", "offsetv")):
            #             for key in tex_anim[dtype]:
            #                 transform.translation[j] = key[1]
            #                 # note that since we are dealing with UV coordinates, V has to be negated
            #                 if j == 1: transform.translation[j] *= -1
            #                 transform.keyframe_insert("translation", index=j, frame=int(key[0] * fps))
            #     tree.links.new(uv.outputs[0], transform.inputs[0])
            #     tree.links.new(transform.outputs[0], tex.inputs[0])

    def clear_default_nodes(self):
        self.b_mat.use_backface_culling = True
        self.b_mat.use_nodes = True
        self.tree = self.b_mat.node_tree
        # bpy.context.view_layer.update()
        # self.tree.update()
        # clear default nodes
        for node in self.tree.nodes:
            self.tree.nodes.remove(node)
        # self.tree.update()
        # bpy.context.view_layer.update()

        self.output = self.tree.nodes.new('ShaderNodeOutputMaterial')

        # shaders
        self.diffuse_shader = self.tree.nodes.new('ShaderNodeBsdfDiffuse')

        # image passes
        self.diffuse_pass = None

        # raw texture nodes
        self.diffuse_texture = None

    def connect_to_pass(self, b_node_pass, b_texture_node, texture_type="Detail"):
        """Connect to an image premixing pass"""
        # connect if the pass has been established, ie. the base texture already exists
        if b_node_pass:
            rgb_mixer = self.tree.nodes.new('ShaderNodeMixRGB')
            # these textures are overlaid onto the base
            if texture_type in ("Detail", "Reflect"):
                rgb_mixer.inputs[0].default_value = 1
                rgb_mixer.blend_type = "OVERLAY"
            # these textures use their alpha channel as a mask over the input pass
            elif texture_type == "Decal":
                self.tree.links.new(b_texture_node.outputs[1], rgb_mixer.inputs[0])
            self.tree.links.new(b_node_pass.outputs[0], rgb_mixer.inputs[1])
            self.tree.links.new(b_texture_node.outputs[0], rgb_mixer.inputs[2])
            return rgb_mixer
        return b_texture_node

    def connect_vertex_colors_to_pass(self, ):
        # if ob.data.vertex_colors:
        vcol = self.tree.nodes.new('ShaderNodeVertexColor')
        vcol.layer_name = "RGBA"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, vcol, texture_type="Detail")

    def connect_to_output(self):

        if self.diffuse_pass:
            try:
                self.tree.links.new(self.diffuse_pass.outputs[0], self.diffuse_shader.inputs[0])
            except:
                print("bug, happens in successive runs over same b_mat")
        # transparency
        if self.b_mat.blend_method == "OPAQUE":
            self.tree.links.new(self.diffuse_shader.outputs[0], self.output.inputs[0])
        else:
            transp = self.tree.nodes.new('ShaderNodeBsdfTransparent')
            alpha_mixer = self.tree.nodes.new('ShaderNodeMixShader')
            #
            # if textures and ob.data.vertex_colors:
            #     vcol = tree.nodes.new('ShaderNodeAttribute')
            #     vcol.attribute_name = "AAA"
            #     mixAAA = tree.nodes.new('ShaderNodeMixRGB')
            #     mixAAA.inputs[0].default_value = 1
            #     mixAAA.blend_type = "MULTIPLY"
            #     tree.links.new(textures[0].outputs[1], mixAAA.inputs[1])
            #     tree.links.new(vcol.outputs[0], mixAAA.inputs[2])
            #     tree.links.new(mixAAA.outputs[0], alpha_mixer.inputs[0])
            if self.diffuse_texture:
                # print("self.diffuse_texture", self.diffuse_texture)
                try:
                    self.tree.links.new(self.diffuse_texture.outputs[1], alpha_mixer.inputs[0])
                except:
                    print("Bug in tex sys setting alpha channel, happens in successive runs?")
            # elif ob.data.vertex_colors:
            #     vcol = tree.nodes.new('ShaderNodeAttribute')
            #     vcol.attribute_name = "AAA"
            #     tree.links.new(vcol.outputs[0], alpha_mixer.inputs[0])

            self.tree.links.new(transp.outputs[0], alpha_mixer.inputs[1])
            self.tree.links.new(self.diffuse_shader.outputs[0], alpha_mixer.inputs[2])
            self.tree.links.new(alpha_mixer.outputs[0], self.output.inputs[0])

        nodes_iterate(self.tree, self.output)

    def create_texture_slot(self, n_tex_desc):
        # todo [texture] refactor this to separate code paths?
        # when processing a NiTextureProperty
        if isinstance(n_tex_desc, NifFormat.TexDesc):
            b_texture_node = self.texture_loader.import_texture_source(n_tex_desc.source, self.b_mat.node_tree)
            uv_layer_index = n_tex_desc.uv_set
        # when processing a BS shader property - n_tex_desc is a bare string
        else:
            b_texture_node = self.texture_loader.import_texture_source(n_tex_desc, self.b_mat.node_tree)
            uv_layer_index = 0
        # todo [texture] pass info about reflective coordinates
        # UV mapping
        self.set_uv_map(b_texture_node, uv_index=uv_layer_index, reflective=False)

        # todo [texture] support clamping and interpolation settings
        return b_texture_node

    def link_base_node(self, b_texture_node):
        self.diffuse_texture = b_texture_node
        b_texture_node.label = "Base"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, b_texture_node)

    def link_bump_map_node(self, b_texture_node):
        b_texture_node.label = "Bump Map"
        # # Influence mapping
        # b_texture_node.texture.use_normal_map = False  # causes artifacts otherwise.
        #
        # # Influence
        # # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # # if self.nif_import.ni_alpha_prop:
        # #     b_texture_node.use_map_alpha = True
        #
        # b_texture_node.use_map_color_diffuse = False
        # b_texture_node.use_map_normal = True
        # b_texture_node.use_map_alpha = False

    def link_normal_node(self, b_texture_node):
        b_texture_node.label = "Normal"
        # # Influence mapping
        # b_texture_node.texture.use_normal_map = True  # causes artifacts otherwise.
        #
        # # Influence
        # # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # # if self.nif_import.ni_alpha_prop:
        # #     b_texture_node.use_map_alpha = True
        #
        # b_texture_node.use_map_color_diffuse = False
        # b_texture_node.use_map_normal = True
        # b_texture_node.use_map_alpha = False

    def link_glow_node(self, b_texture_node):
        b_texture_node.label = "Glow"
        # # Influence mapping
        # b_texture_node.texture.use_alpha = False
        #
        # # Influence
        # # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # # if self.nif_import.ni_alpha_prop:
        # #     b_texture_node.use_map_alpha = True
        #
        # b_texture_node.use_map_color_diffuse = False
        # b_texture_node.use_map_emit = True

    def link_gloss_node(self, b_texture_node):
        b_texture_node.label = "Gloss"
        # # Influence mapping
        # b_texture_node.texture.use_alpha = False
        #
        # # Influence
        # # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # # if self.nif_import.ni_alpha_prop:
        # #     b_texture_node.use_map_alpha = True
        #
        # b_texture_node.use_map_color_diffuse = False
        # b_texture_node.use_map_specular = True
        # b_texture_node.use_map_color_spec = True

    def link_decal_0_node(self, b_texture_node):
        b_texture_node.label = "Decal 0"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, b_texture_node, texture_type="Decal")

    def link_decal_1_node(self, b_texture_node):
        b_texture_node.label = "Decal 1"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, b_texture_node, texture_type="Decal")

    def link_decal_2_node(self, b_texture_node):
        b_texture_node.label = "Decal2"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, b_texture_node, texture_type="Decal")

    def link_detail_node(self, b_texture_node):
        b_texture_node.label = "Detail"
        self.diffuse_pass = self.connect_to_pass(self.diffuse_pass, b_texture_node, texture_type="Detail")

    def link_dark_node(self, b_texture_node):
        # todo [texture] implement
        pass

    def link_reflection_node(self, b_texture_node):
        # Influence mapping

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_texture_node.use_map_alpha = True

        b_texture_node.use_map_color_diffuse = True
        b_texture_node.use_map_emit = True
        b_texture_node.use_map_mirror = True

    def link_environment_node(self, b_texture_node):
        # Influence mapping

        # Influence
        # TODO [property][texture][flag][alpha] Figure out if this texture has alpha
        # if self.nif_import.ni_alpha_prop:
        #     b_texture_node.use_map_alpha = True

        b_texture_node.use_map_color_diffuse = True
        b_texture_node.blend_type = 'ADD'

    @staticmethod
    def get_b_blend_type_from_n_apply_mode(n_apply_mode):
        # TODO [material] Check out n_apply_modes
        if n_apply_mode == NifFormat.ApplyMode.APPLY_MODULATE:
            return "MIX"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_REPLACE:
            return "COLOR"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_DECAL:
            return "OVERLAY"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT:
            return "LIGHTEN"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT2:  # used by Oblivion for parallax
            return "MULTIPLY"
        else:
            NifLog.warn("Unknown apply mode (%i) in material, using blend type 'MIX'".format(n_apply_mode))
            return "MIX"
