"""This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.animation.animation_export import Animation
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.modules.property import texture
from io_scene_nif.modules.property.texture.texture_writer import TextureWriter
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog


class Texture:
    # Default ordering of Extra data blocks for different games
    USED_EXTRA_SHADER_TEXTURES = {
        'SID_MEIER_S_RAILROADS': (3, 0, 4, 1, 5, 2),
        'CIVILIZATION_IV': (3, 0, 1, 2)
    }

    def __init__(self):
        self.animation_helper = Animation(parent=self)
        self.dict_mesh_uvlayers = []
        self.texture_writer = TextureWriter()

        self.base_mtex = None
        self.glow_mtex = None
        self.bump_mtex = None
        self.normal_mtex = None
        self.gloss_mtex = None
        self.dark_mtex = None
        self.detail_mtex = None
        self.ref_mtex = None

    @staticmethod
    def get_uv_layers(b_mat):
        used_uvlayers = set()
        texture_slots = texture.get_used_textslots(b_mat)
        for slot in texture_slots:
            used_uvlayers.add(slot.uv_layer)
        return used_uvlayers

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

    def export_texturing_property(self, flags=0x0001, applymode=None, b_mat=None, b_obj=None):
        """Export texturing property."""

        self.determine_texture_types(b_obj, b_mat)

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

        if self.base_mtex:
            texprop.has_base_texture = True
            self.texture_writer.export_tex_desc(texdesc=texprop.base_texture,
                                                uvlayers=self.dict_mesh_uvlayers,
                                                b_mat_texslot=self.base_mtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.texture.name)
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.animation_helper.texture.export_flip_controller(fliptxt, self.base_mtex.texture, texprop, 0)

        if self.glow_mtex:
            texprop.has_glow_texture = True
            self.texture_writer.export_tex_desc(texdesc=texprop.glow_texture,
                                                uvlayers=self.dict_mesh_uvlayers,
                                                b_mat_texslot=self.glow_mtex)

        if self.bump_mtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_bump_map_texture = True
                self.texture_writer.export_tex_desc(texdesc=texprop.bump_map_texture,
                                                    uvlayers=self.dict_mesh_uvlayers,
                                                    b_mat_texslot=self.bump_mtex)
                texprop.bump_map_luma_scale = 1.0
                texprop.bump_map_luma_offset = 0.0
                texprop.bump_map_matrix.m_11 = 1.0
                texprop.bump_map_matrix.m_12 = 0.0
                texprop.bump_map_matrix.m_21 = 0.0
                texprop.bump_map_matrix.m_22 = 1.0

        if self.normal_mtex:
            shadertexdesc = texprop.shader_textures[1]
            shadertexdesc.is_used = True
            shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.normal_mtex.texture)

        if self.gloss_mtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_gloss_texture = True
                self.texture_writer.export_tex_desc(texdesc=texprop.gloss_texture,
                                                    uvlayers=self.dict_mesh_uvlayers,
                                                    b_mat_texslot=self.gloss_mtex)
            else:
                shadertexdesc = texprop.shader_textures[2]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.gloss_mtex.texture)

        if self.dark_mtex:
            texprop.has_dark_texture = True
            self.texture_writer.export_tex_desc(texdesc=texprop.dark_texture,
                                                uvlayers=self.dict_mesh_uvlayers,
                                                b_mat_texslot=self.dark_mtex)

        if self.detail_mtex:
            texprop.has_detail_texture = True
            self.texture_writer.export_tex_desc(texdesc=texprop.detail_texture,
                                                uvlayers=self.dict_mesh_uvlayers,
                                                b_mat_texslot=self.detail_mtex)

        if self.ref_mtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                NifLog.warn("Cannot export reflection texture for this game.")
                # tex_prop.hasRefTexture = True
                # self.export_tex_desc(texdesc=tex_prop.refTexture, uvlayers=uvlayers, mtex=refmtex)
            else:
                shadertexdesc = texprop.shader_textures[3]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = TextureWriter.export_source_texture(n_texture=self.ref_mtex.texture)

    def export_texture_shader_effect(self, tex_prop):
        # export extra shader textures
        if NifOp.props.game == 'SID_MEIER_S_RAILROADS':
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

        elif NifOp.props.game == 'CIVILIZATION_IV':
            # some textures end up in the shader texture list there are 4 slots available, so set them up
            tex_prop.num_shader_textures = 4
            tex_prop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(tex_prop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex

    def export_texture_effect(self, b_mat_texslot=None):
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
        if b_mat_texslot:
            texeff.source_texture = TextureWriter.export_source_texture(b_mat_texslot.texture)
            if NifOp.props.game == 'MORROWIND':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return block_store.register_block(texeff)

    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[NifOp.props.game]:
            shader_name = texture.EXTRA_SHADER_TEXTURES[shaderindex]
            trishape.add_integer_extra_data(shader_name, shaderindex)

    def determine_texture_types(self, b_obj, b_mat):

        used_slots = texture.get_used_textslots(b_mat)
        self.base_mtex = None
        self.bump_mtex = None
        self.dark_mtex = None
        self.detail_mtex = None
        self.gloss_mtex = None
        self.glow_mtex = None
        self.normal_mtex = None
        self.ref_mtex = None

        for b_mat_texslot in used_slots:
            # check REFL-mapped textures (used for "NiTextureEffect" materials)
            if b_mat_texslot.texture_coords == 'REFLECTION':
                if not b_mat_texslot.use_map_color_diffuse:
                    # it should map to colour
                    raise nif_utils.NifError("Non-COL-mapped reflection texture in mesh '%s', material '%s', these cannot be exported to NIF.\n"
                                             "Either delete all non-COL-mapped reflection textures, or in the Shading Panel, under Material Buttons, set texture 'Map To' to 'COL'." % (b_obj.name, b_mat.name))
                if b_mat_texslot.blend_type != 'ADD':
                    # it should have "ADD" blending mode
                    NifLog.warn("Reflection texture should have blending mode 'Add' on texture in mesh '{0}', material '{1}').".format(b_obj.name, b_mat.name))
                # an envmap image should have an empty... don't care
                self.ref_mtex = b_mat_texslot

            # check UV-mapped textures
            elif b_mat_texslot.texture_coords == 'UV':

                # update set of uv layers that must be exported
                if b_mat_texslot.uv_layer not in self.dict_mesh_uvlayers:
                    self.dict_mesh_uvlayers.append(b_mat_texslot.uv_layer)

                # glow tex
                if b_mat_texslot.use_map_emit:
                    # multi-check
                    if self.glow_mtex:
                        raise nif_utils.NifError("Multiple emissive textures in mesh '{0}', material '{1}''.\n"
                                                 "Make sure there is only one texture set as Influence > emit".format(b_obj.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    self.glow_mtex = b_mat_texslot

                # specular
                elif b_mat_texslot.use_map_specular or b_mat_texslot.use_map_color_spec:
                    # multi-check
                    if self.gloss_mtex:
                        raise nif_utils.NifError("Multiple specular gloss textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > specular".format(b_obj.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    # got the gloss map
                    self.gloss_mtex = b_mat_texslot

                # bump map
                elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map is False:
                    # multi-check
                    if self.bump_mtex:
                        raise nif_utils.NifError("Multiple bump/normal texture in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".format(b_obj.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    self.bump_mtex = b_mat_texslot

                # normal map
                elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map:
                    # multi-check
                    if self.normal_mtex:
                        raise nif_utils.NifError("Multiple bump/normal textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".format(b_obj.name, b_mat.name))
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.normal_mtex = b_mat_texslot

                # darken
                elif b_mat_texslot.use_map_color_diffuse and b_mat_texslot.blend_type == 'DARKEN':

                    if self.dark_mtex:
                        raise nif_utils.NifError("Multiple Darken textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Blend Type > Dark".format(b_obj.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    # got the dark map
                    self.dark_mtex = b_mat_texslot

                # diffuse
                elif b_mat_texslot.use_map_color_diffuse:
                    if self.base_mtex:
                        raise nif_utils.NifError("Multiple Diffuse textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Diffuse > color".format(b_obj.name, b_mat.name))

                    self.base_mtex = b_mat_texslot

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                        '''
                        # in this case, Blender replaces the texture transparant parts with the underlying material color...
                        # in NIF, material alpha is multiplied with texture alpha channel...
                        # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                        # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                        # but...
    
                        if mesh_mat_transparency > NifOp.props.epsilon:
                            raise nif_utils.NifError(
                                "Cannot export this type of"
                                " transparency in material '%s': "
                                " instead, try to set alpha to 0.0"
                                " and to use the 'Var' slider"
                                " in the 'Map To' tab under the"
                                " material buttons."
                                %b_mat.name)
                        if (b_mat.animation_data and b_mat.animation_data.action.fcurves['Alpha']):
                            raise nif_utils.NifError(
                                "Cannot export animation for"
                                " this type of transparency"
                                " in material '%s':"
                                " remove alpha animation,"
                                " or turn off MapTo.ALPHA,"
                                " and try again."
                                %b_mat.name)
    
                        mesh_mat_transparency = b_mat_texslot.varfac # we must use the "Var" value
                        '''

                # detail
                elif b_mat_texslot.use_map_color_diffuse:
                    if self.detail_mtex:
                        raise nif_utils.NifError("Multiple detail textures in mesh '{0}', material '{1}'.\n" 
                                                 "Make sure there is only one texture with Influence Diffuse > color".format(b_obj.name, b_mat.name))
                    # extra diffuse consider as detail texture

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.detail_mtex = b_mat_texslot

                # reflection
                elif b_mat_texslot.use_map_mirror or b_mat_texslot.use_map_raymir:
                    # multi-check
                    if self.glow_mtex:
                        raise nif_utils.NifError("Multiple reflection textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > Mirror/Ray Mirror".format(b_obj.name, b_mat.name))
                    # got the reflection map
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.ref_mtex = b_mat_texslot

                # unsupported map
                else:
                    raise nif_utils.NifError("Do not know how to export texture '{0}', in mesh '{1}', material '{2}'.\n"
                                             "Either delete it, or if this texture is to be your base texture.\n"
                                             "Go to the Shading Panel Material Buttons, and set texture 'Map To' to 'COL'.".format(b_mat_texslot.texture.name, b_obj.name, b_mat.name))

            # nif only support UV-mapped textures
            else:
                NifLog.warn("Non-UV texture in mesh '{0}', material '{1}'.\nEither delete all non-UV textures or "
                            "create a UV map for every texture associated with selected object and run the script again.".format(b_obj.name, b_mat.name))


def has_diffuse_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.diffusetextures

    for b_mat_texslot in texture.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_color_diffuse:
            self.diffusetextures.append(b_mat_texslot)
    return self.diffusetextures


def has_glow_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.glowtextures

    for b_mat_texslot in texture.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_emit:
            self.glowtextures.append(b_mat_texslot)
    return self.glowtextures


def has_bumpmap_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.bumpmaptextures

    for b_mat_texslot in texture.get_used_textslots(b_mat):
        if b_mat_texslot.use:
            if b_mat_texslot.texture.use_normal_map is False and b_mat_texslot.use_map_color_diffuse is False:
                self.bumpmaptextures.append(b_mat_texslot)
    return self.bumpmaptextures


def has_gloss_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.glosstextures

    for b_mat_texslot in texture.get_used_textslots(b_mat):
        if b_mat_texslot.use and b_mat_texslot.use_map_color_spec:
            self.glosstextures.append(b_mat_texslot)
    return self.glosstextures


def has_normalmap_textures(self, b_mat):
    if self.b_mat == b_mat:
        return self.normalmaptextures

    for b_mat_texslot in texture.get_used_textslots(b_mat):
        if b_mat_texslot.use:
            if b_mat_texslot.use_map_color_diffuse is False and b_mat_texslot.texture.use_normal_map and b_mat_texslot.use_map_normal:
                self.normalmaptextures.append(b_mat_texslot)
    return self.normalmaptextures
