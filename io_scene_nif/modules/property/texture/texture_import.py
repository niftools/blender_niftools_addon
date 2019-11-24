"""This script contains helper methods to import textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2012, NIF File Format Library and Tools contributors.
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


from pyffi.formats.nif import NifFormat
from io_scene_nif.utility.nif_logging import NifLog


class Texture():

    def __init__(self, parent):
        self.nif_import = parent
        self.textureloader = None
        self.used_slots = []
        self.b_mat = None
        self.reset_textures()
        self.reset_texture_flags()

    def reset_textures(self):
        self.bump_map = None
        self.dark_map = None
        self.decal_map = None
        self.detail_map = None
        self.diffuse_map = None
        self.env_map = None
        self.gloss_map = None
        self.glow_map = None
        self.normal_map = None
        self.reflection_map = None
        self.unknown_2_map = None

    def reset_texture_flags(self):
        self.has_bumptex = False
        self.has_darktex = False
        self.has_decaltex = False
        self.has_detailtex = False
        self.has_diffusetex = False
        self.has_envtex = False
        self.has_glosstex = False
        self.has_glowtex = False
        self.has_normaltex = False
        self.has_reftex = False
        self.has_unk2tex = False

    def set_texture_loader(self, textureloader):
        self.textureloader = textureloader

    def import_nitextureprop_textures(self, b_mat, n_textureDesc):
        if n_textureDesc.has_base_texture:
            self.has_diffusetex = True
            self.diffuse_map = self.import_image_texture(b_mat,
                                                         n_textureDesc.base_texture)

        if n_textureDesc.has_bump_map_texture:
            self.has_bumptex = True
            self.bump_map = self.import_image_texture(b_mat,
                                                      n_textureDesc.base_texture)

        if n_textureDesc.has_normal_texture:
            self.has_normaltex = True
            self.normal_map = self.import_image_texture(b_mat,
                                                        n_textureDesc.bump_map_texture)

        if n_textureDesc.has_gloss_texture:
            self.has_glosstex = True
            self.gloss_map = self.import_image_texture(b_mat,
                                                       n_textureDesc.glow_texture)

        if n_textureDesc.has_glow_texture:
            self.has_glowtex = True
            self.glow_map = self.import_image_texture(b_mat,
                                                      n_textureDesc.normal_map_texture)

        if n_textureDesc.has_dark_texture:
            self.has_darktex = True
            self.dark_map = self.import_image_texture(b_mat,
                                                      n_textureDesc.base_texture)

        if n_textureDesc.has_detail_texture:
            self.has_detailtex = True
            self.detail_map = self.import_image_texture(b_mat,
                                                        n_textureDesc.base_texture)

    def import_texture_extra_shader(self, b_mat, n_texture_prop, extra_datas):
        # extra texture shader slots
        for shader_tex_desc in n_texture_prop.shader_textures:

            if not shader_tex_desc.is_used:
                continue

            # it is used, figure out the slot it is used for
            for extra in extra_datas:
                if extra.integer_data == shader_tex_desc.map_index:
                    shader_name = extra.name
                    break
            else:
                NifLog.warn("No slot for shader texture {0}.".format(
                    shader_tex_desc.texture_data.source.file_name))
                continue
            try:
                extra_shader_index = (
                    self.nif_import.EXTRA_SHADER_TEXTURES.index(shader_name))
            except ValueError:
                # shader_name not in self.EXTRA_SHADER_TEXTURES
                NifLog.warn("No slot for shader texture {0}.".format(
                    shader_tex_desc.texture_data.source.file_name))
                continue

            self.import_shader_by_type(shader_tex_desc, extra_shader_index)

    def import_shader_by_type(self, b_mat, shader_tex_desc, extra_shader_index):
        if extra_shader_index == 0:
            # EnvironmentMapIndex
            if shader_tex_desc.texture_data.source.file_name.lower().startswith(
                    "rrt_engine_env_map"):
                # sid meier's railroads: env map generated by engine
                # we can skip this
                NifLog.info(
                    "Skipping environment map texture. Env Map is generated by Engine")
            envTexDesc = shader_tex_desc.texture_data
            self.has_envtex = True
            self.env_map = self.import_image_texture(b_mat, envTexDesc)

        elif extra_shader_index == 1:
            # NormalMapIndex
            bumpTexDesc = shader_tex_desc.texture_data
            self.has_bumptex = True
            self.bump_map = self.import_image_texture(b_mat, bumpTexDesc)

        elif extra_shader_index == 2:
            # SpecularIntensityIndex
            glossTexDesc = shader_tex_desc.texture_data
            self.has_glosstex = True
            self.gloss_map = self.import_image_texture(b_mat, glossTexDesc)

        elif extra_shader_index == 3:
            # EnvironmentIntensityIndex (this is reflection)
            refTexDesc = shader_tex_desc.texture_data
            self.has_reftex = True
            self.reflection_map = self.reflection_map = self.import_image_texture(
                b_mat, refTexDesc)

        elif extra_shader_index == 4:
            # LightCubeMapIndex
            if shader_tex_desc.texture_data.source.file_name.lower().startswith(
                    "rrt_cube_light_map"):
                # sid meier's railroads: light map generated by engine
                # we can skip this
                NifLog.info("Ignoring Env Map as generated by Engine")
            NifLog.warn("Skipping light cube texture.")

        elif extra_shader_index == 5:
            # ShadowTextureIndex
            NifLog.warn("Skipping shadow texture.")

        else:
            NifLog.warn("Unknown texture type found in extra_shader_index")

    def import_bsshaderproperty(self, b_mat, bsShaderProperty):
        self.reset_textures()
        ImageTexFile = bsShaderProperty.texture_set.textures[0].decode()
        if ImageTexFile:
            self.has_diffusetex = True
            self.diffuse_map = self.import_image_texture(b_mat, ImageTexFile)

        ImageTexFile = bsShaderProperty.texture_set.textures[1].decode()
        if ImageTexFile:
            self.has_normaltex = True
            self.normal_map = self.import_image_texture(b_mat, ImageTexFile)

        ImageTexFile = bsShaderProperty.texture_set.textures[2].decode()
        if ImageTexFile:
            self.has_glowtex = True
            self.glow_map = self.import_image_texture(b_mat, ImageTexFile)

        ImageTexFile = bsShaderProperty.texture_set.textures[3].decode()
        if ImageTexFile:
            self.has_detailtex = True
            self.detail_map = self.import_image_texture(b_mat, ImageTexFile)

        if len(bsShaderProperty.texture_set.textures) > 6:
            ImageTexFile = bsShaderProperty.texture_set.textures[6].decode()
            if ImageTexFile:
                self.has_decaltex = True
                self.decal_map = self.import_image_texture(b_mat, ImageTexFile)

            ImageTexFile = bsShaderProperty.texture_set.textures[7].decode()
            if ImageTexFile:
                self.has_glosstex = True
                self.gloss_map = self.import_image_texture(b_mat, ImageTexFile)
        if hasattr(bsShaderProperty, 'texture_clamp_mode'):
            self.b_mat = self.import_clamp(b_mat, bsShaderProperty)
        if hasattr(bsShaderProperty, 'uv_offset'):
            self.b_mat = self.import_uv_offset(b_mat, bsShaderProperty)
        if hasattr(bsShaderProperty, 'uv_scale'):
            self.b_mat = self.import_uv_scale(b_mat, bsShaderProperty)

    def import_bseffectshaderproperty(self, b_mat, bsEffectShaderProperty):
        self.reset_textures()
        ImageTexFile = bsEffectShaderProperty.source_texture.decode()
        if ImageTexFile:
            self.has_diffusetex = True
            self.diffuse_map = self.import_image_texture(b_mat, ImageTexFile)
        ImageTexFile = bsEffectShaderProperty.greyscale_texture.decode()
        if ImageTexFile:
            self.has_glowtex = True
            self.glow_map = self.import_image_texture(b_mat, ImageTexFile)

        if hasattr(bsEffectShaderProperty, 'uv_offset'):
            self.b_mat = self.import_uv_offset(b_mat, bsEffectShaderProperty)
        if hasattr(bsEffectShaderProperty, 'uv_scale'):
            self.b_mat = self.import_uv_scale(b_mat, bsEffectShaderProperty)

        self.b_mat = self.import_texture_game_properties(b_mat, bsEffectShaderProperty)

    def import_texture_effect(self, b_mat, textureEffect):
        ImageTexFile = textureEffect
        self.has_envtex = True
        self.env_map = self.import_image_texture(b_mat, ImageTexFile)

    def import_clamp(self, b_mat, ShaderProperty):
        clamp = ShaderProperty.texture_clamp_mode
        for texslot in b_mat.texture_slots:
            if texslot:
                if clamp == 3:
                    texslot.texture.image.use_clamp_x = False
                    texslot.texture.image.use_clamp_y = False
                if clamp == 2:
                    texslot.texture.image.use_clamp_x = False
                    texslot.texture.image.use_clamp_y = True
                if clamp == 1:
                    texslot.texture.image.use_clamp_x = True
                    texslot.texture.image.use_clamp_y = False
                if clamp == 0:
                    texslot.texture.image.use_clamp_x = True
                    texslot.texture.image.use_clamp_y = True

    def import_uv_offset(self, b_mat, ShaderProperty):
        for texslot in b_mat.texture_slots:
            if texslot:
                texslot.offset.x = ShaderProperty.uv_offset.u
                texslot.offset.y = ShaderProperty.uv_offset.v

    def import_uv_scale(self, b_mat, ShaderProperty):
        for texslot in b_mat.texture_slots:
            if texslot:
                texslot.scale.x = ShaderProperty.uv_scale.u
                texslot.scale.y = ShaderProperty.uv_scale.v

    def import_texture_game_properties(self, b_mat, ShaderProperty):
        for texslot in b_mat.texture_slots:
            if texslot:
                texslot.texture.image.use_animation = True
                texslot.texture.image.fps = ShaderProperty.controller.frequency
                texslot.texture.image.frame_start = ShaderProperty.controller.start_time
                texslot.texture.image.frame_end = ShaderProperty.controller.stop_time

    def create_texture_slot(self, b_mat, image_texture):
        b_mat_texslot = b_mat.texture_slots.add()
        try:
            b_mat_texslot.texture = self.textureloader.import_texture_source(image_texture.source)
        except:
            b_mat_texslot.texture = self.textureloader.import_texture_source(image_texture)
        b_mat_texslot.use = True

        # Influence mapping

        # Mapping
        b_mat_texslot.texture_coords = 'UV'
        try:
            b_mat_texslot.uv_layer = self.get_uv_layer_name(image_texture.uv_set)
        except:
            b_mat_texslot.uv_layer = self.get_uv_layer_name(0)

        return b_mat_texslot

    def import_image_texture(self, b_mat, n_textureDesc):

        image_texture = n_textureDesc

        b_mat_texslot = self.create_texture_slot(b_mat, image_texture)

        # Influence mapping
        if self.has_bumptex:
            b_mat_texslot.texture.use_normal_map = False  # causes artifacts otherwise.
        if self.has_normaltex:
            b_mat_texslot.texture.use_normal_map = True  # causes artifacts otherwise.
        if self.has_glowtex or self.has_glosstex or self.has_decaltex:
            b_mat_texslot.texture.use_alpha = False

        # Influence
        if (self.nif_import.ni_alpha_prop):
            b_mat_texslot.use_map_alpha = True

        if self.has_diffusetex or self.has_darktex or self.has_detailtex or self.has_reftex or self.has_envtex:
            b_mat_texslot.use_map_color_diffuse = True
        if self.has_bumptex or self.has_normaltex or self.has_glowtex or self.has_glosstex:
            b_mat_texslot.use_map_color_diffuse = False
        if self.has_bumptex or self.has_normaltex:
            b_mat_texslot.use_map_normal = True
            b_mat_texslot.use_map_alpha = False
        if self.has_glowtex or self.has_reftex:
            b_mat_texslot.use_map_emit = True
        if self.has_glosstex:
            b_mat_texslot.use_map_specular = True
            b_mat_texslot.use_map_color_spec = True
        if self.has_reftex:
            b_mat_texslot.use_map_mirror = True

        # Blend mode
        if hasattr(n_textureDesc, "apply_mode"):
            b_mat_texslot.blend_type = self.get_b_blend_type_from_n_apply_mode(
                n_textureDesc.apply_mode)
        elif self.has_envtex:
            b_mat_texslot.blend_type = 'ADD'
        else:
            b_mat_texslot.blend_type = "MIX"

        self.reset_texture_flags()
        return b_mat_texslot

    def get_b_blend_type_from_n_apply_mode(self, n_apply_mode):
        # TODO: - Check out n_apply_modes
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
            NifLog.warn("Unknown apply mode ({0}) in material, using blend type 'MIX'".format(n_apply_mode))
            return "MIX"

    def get_uv_layer_name(self, uvset):
        return str(uvset)

    def get_used_textslots(self, b_mat):
        self.used_slots = [b_texslot for b_texslot in b_mat.texture_slots if b_texslot is not None]
        return self.used_slots

    def has_base_texture(self, b_mat):
        return self.diffuse_map

    def has_bumpmap_texture(self, b_mat):
        return self.bump_map

    def has_dark_texture(self, b_mat):
        return self.dark_map

    def has_decal_map_texture(self, b_mat):
        return self.decal_map

    def has_detail_map_texture(self, b_mat):
        return self.detail_map

    def has_env_map_texture(self, b_mat):
        return self.env_map

    def has_gloss_map_texture(self, b_mat):
        return self.gloss_map

    def has_glow_texture(self, b_mat):
        return self.glow_map

    def has_normalmap_texture(self, b_mat):
        return self.normal_map

    def has_reflection_map_texture(self, b_mat):
        return self.reflection_map

    def has_unknown_2_map_texture(self, b_mat):
        return self.unknown_2_map
