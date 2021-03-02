"""This modules contains helper methods to export nitextureproperty type nodes"""

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

from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.property.texture import TextureSlotManager, TextureWriter
from io_scene_niftools.utils.logging import NifLog


class NiTextureProp(TextureSlotManager):

    # TODO Common for import/export
    """Names (ordered by default index) of shader texture slots for Sid Meier's Railroads and similar games."""
    EXTRA_SHADER_TEXTURES = [
        "EnvironmentMapIndex",
        "NormalMapIndex",
        "SpecularIntensityIndex",
        "EnvironmentIntensityIndex",
        "LightCubeMapIndex",
        "ShadowTextureIndex"]

    # Default ordering of Extra data blocks for different games
    USED_EXTRA_SHADER_TEXTURES = {
        'SID_MEIER_S_RAILROADS': (3, 0, 4, 1, 5, 2),
        'CIVILIZATION_IV': (3, 0, 1, 2)
    }

    __instance = None

    def __init__(self):
        """ Virtually private constructor. """
        if NiTextureProp.__instance:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            NiTextureProp.__instance = self

    @staticmethod
    def get():
        """ Static access method. """
        if not NiTextureProp.__instance:
            NiTextureProp()
        return NiTextureProp.__instance

    def export_texturing_property(self, flags=0x0001, applymode=None, b_mat=None):
        """Export texturing property."""

        self.determine_texture_types(b_mat)

        texprop = NifFormat.NiTexturingProperty()

        texprop.flags = flags
        texprop.apply_mode = applymode
        texprop.texture_count = 7

        self.export_texture_shader_effect(texprop)
        self.export_nitextureprop_tex_descs(texprop)

        # search for duplicate
        for n_block in block_store.block_to_obj:
            if isinstance(n_block, NifFormat.NiTexturingProperty) and n_block.get_hash() == texprop.get_hash():
                return n_block

        # no texturing property with given settings found, so use and register
        # the new one
        return texprop

    def export_nitextureprop_tex_descs(self, texprop):
        # go over all valid texture slots
        for slot_name, b_texture_node in self.slots.items():
            if b_texture_node:
                # get the field name used by nif xml for this texture
                field_name = f"{slot_name.lower().replace(' ', '_')}_texture"
                NifLog.debug(f"Activating {field_name} for {b_texture_node.name}")
                setattr(texprop, "has_"+field_name, True)
                # get the tex desc link
                texdesc = getattr(texprop, field_name)
                uv_index = self.get_uv_node(b_texture_node)
                # set uv index and source texture to the texdesc
                texdesc.uv_set = uv_index
                texdesc.source = TextureWriter.export_source_texture(b_texture_node)

        # TODO [animation] FIXME Heirarchy
        # self.texture_anim.export_flip_controller(fliptxt, self.base_mtex.texture, texprop, 0)

        # todo [texture] support extra shader textures again
        # if self.slots["Bump Map"]:
        #     if bpy.context.scene.niftools_scene.game not in self.USED_EXTRA_SHADER_TEXTURES:
        #         texprop.has_bump_map_texture = True
        #         self.texture_writer.export_tex_desc(texdesc=texprop.bump_map_texture,
        #                                             uv_set=uv_index,
        #                                             b_texture_node=self.slots["Bump Map"])
        #         texprop.bump_map_luma_scale = 1.0
        #         texprop.bump_map_luma_offset = 0.0
        #         texprop.bump_map_matrix.m_11 = 1.0
        #         texprop.bump_map_matrix.m_12 = 0.0
        #         texprop.bump_map_matrix.m_21 = 0.0
        #         texprop.bump_map_matrix.m_22 = 1.0
        #
        # if self.slots["Normal"]:
        #     shadertexdesc = texprop.shader_textures[1]
        #     shadertexdesc.is_used = True
        #     shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.slots["Bump Map"])
        #
        # if self.slots["Gloss"]:
        #     if bpy.context.scene.niftools_scene.game not in self.USED_EXTRA_SHADER_TEXTURES:
        #         texprop.has_gloss_texture = True
        #         self.texture_writer.export_tex_desc(texdesc=texprop.gloss_texture,
        #                                             uv_set=uv_index,
        #                                             b_texture_node=self.slots["Gloss"])
        #     else:
        #         shadertexdesc = texprop.shader_textures[2]
        #         shadertexdesc.is_used = True
        #         shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.slots["Gloss"])

        # if self.b_ref_slot:
        #     if bpy.context.scene.niftools_scene.game not in self.USED_EXTRA_SHADER_TEXTURES:
        #         NifLog.warn("Cannot export reflection texture for this game.")
        #         # tex_prop.hasRefTexture = True
        #         # self.export_tex_desc(texdesc=tex_prop.refTexture, uv_set=uv_set, mtex=refmtex)
        #     else:
        #         shadertexdesc = texprop.shader_textures[3]
        #         shadertexdesc.is_used = True
        #         shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.b_ref_slot.texture)

    def export_texture_effect(self, b_texture_node=None):
        """Export a texture effect block from material texture mtex (MTex, not Texture)."""
        texeff = NifFormat.NiTextureEffect()
        texeff.flags = 4
        texeff.rotation.set_identity()
        texeff.scale = 1.0
        texeff.model_projection_matrix.set_identity()
        texeff.texture_filtering = NifFormat.TexFilterMode.FILTER_TRILERP
        texeff.texture_clamping = NifFormat.TexClampMode.WRAP_S_WRAP_T
        texeff.texture_type = NifFormat.EffectType.EFFECT_ENVIRONMENT_MAP
        texeff.coordinate_generation_type = NifFormat.CoordGenType.CG_SPHERE_MAP
        if b_texture_node:
            texeff.source_texture = TextureWriter.export_source_texture(b_texture_node.texture)
            if bpy.context.scene.niftools_scene.game == 'MORROWIND':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return block_store.register_block(texeff)

    def export_texture_shader_effect(self, tex_prop):
        # disable
        return
        # export extra shader textures
        if bpy.context.scene.niftools_scene.game == 'SID_MEIER_S_RAILROADS':
            # sid meier's railroads:
            # some textures end up in the shader texture list there are 5 slots available, so set them up
            tex_prop.num_shader_textures = 5
            tex_prop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(tex_prop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex

            # some texture slots required by the engine
            shadertexdesc_envmap = tex_prop.shader_textures[0]
            shadertexdesc_envmap.is_used = True
            shadertexdesc_envmap.texture_data.source = TextureWriter.export_source_texture(filename="RRT_Engine_Env_map.dds")

            shadertexdesc_cubelightmap = tex_prop.shader_textures[4]
            shadertexdesc_cubelightmap.is_used = True
            shadertexdesc_cubelightmap.texture_data.source = TextureWriter.export_source_texture(filename="RRT_Cube_Light_map_128.dds")

        elif bpy.context.scene.niftools_scene.game == 'CIVILIZATION_IV':
            # some textures end up in the shader texture list there are 4 slots available, so set them up
            tex_prop.num_shader_textures = 4
            tex_prop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(tex_prop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex

    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[bpy.context.scene.niftools_scene.game]:
            shader_name = self.EXTRA_SHADER_TEXTURES[shaderindex]
            trishape.add_integer_extra_data(shader_name, shaderindex)

    @staticmethod
    def get_n_apply_mode_from_b_blend_type(b_blend_type):
        if b_blend_type == "LIGHTEN":
            return NifFormat.ApplyMode.APPLY_HILIGHT
        elif b_blend_type == "MULTIPLY":
            return NifFormat.ApplyMode.APPLY_HILIGHT2
        elif b_blend_type == "MIX":
            return NifFormat.ApplyMode.APPLY_MODULATE

        NifLog.warn("Unsupported blend type ({0}) in material, using apply mode APPLY_MODULATE".format(b_blend_type))
        return NifFormat.ApplyMode.APPLY_MODULATE
