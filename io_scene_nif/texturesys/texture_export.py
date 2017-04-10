"""This script contains helper methods to export textures."""

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

from pyffi.formats.nif import NifFormat

from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog

from io_scene_nif.texturesys.texture_writer import TextureWriter
from io_scene_nif.utility.nif_global import NifOp

class TextureHelper():
    
    #Default ordering of Extra data blocks for different games
    USED_EXTRA_SHADER_TEXTURES = {'SID_MEIER_S_RAILROADS': (3, 0, 4, 1, 5, 2),
                                  'CIVILIZATION_IV': (3, 0, 1, 2)}
    
    def __init__(self, parent):
        self.nif_export = parent
        self.texture_writer = TextureWriter(parent=self)
        
        self.basemtex=None
        self.glowmtex=None
        self.bumpmtex=None
        self.normalmtex=None
        self.glossmtex=None
        self.darkmtex=None
        self.detailmtex=None
        self.refmtex=None

#         mesh_base_mtex = None
#         mesh_glow_mtex = None
#         mesh_bump_mtex = None
#         mesh_normal_mtex = None
#         mesh_gloss_mtex = None
#         mesh_dark_mtex = None
#         mesh_detail_mtex = None
#         mesh_texeff_mtex = None
#         mesh_ref_mtex = None
    
    @staticmethod
    def get_used_textslots(b_mat):
        used_slots = []
        if b_mat is not None:
            used_slots = [b_texslot for b_texslot in b_mat.texture_slots if b_texslot is not None and b_texslot.use]
        return used_slots

    @staticmethod
    def get_uv_layers(b_mat):
        used_uvlayers = set()
        texture_slots = TextureHelper.get_used_textslots(b_mat)
        for slot in texture_slots:
            used_uvlayers.add(slot.uv_layer)
        return used_uvlayers

    def export_bs_shader_property(self, b_obj=None, b_mat=None):
        """Export a Bethesda shader property block."""
        self.determine_texture_types(b_obj, b_mat)
        
        # create new block
        if b_obj.niftools_shader.bs_shadertype == 'BSShaderPPLightingProperty':
            bsshader = NifFormat.BSShaderPPLightingProperty()
            # set shader options
            # TODO: FIXME:
            b_s_type = NifFormat.BSShaderType._enumkeys.index(b_obj.niftools_shader.bsspplp_shaderobjtype)
            bsshader.shader_type = NifFormat.BSShaderType._enumvalues[b_s_type]
            
            # Shader Flags
            if hasattr(bsshader, 'shader_flags'):
                self.export_shader_flags(b_obj, bsshader)
            
                        
        if b_obj.niftools_shader.bs_shadertype == 'BSLightingShaderProperty':
            bsshader = NifFormat.BSLightingShaderProperty()
            b_s_type = NifFormat.BSLightingShaderPropertyShaderType._enumkeys.index(b_obj.niftools_shader.bslsp_shaderobjtype)
            bsshader.shader_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues[b_s_type]
        
            # UV Offset
            if hasattr(bsshader, 'uv_offset'):
                self.export_uv_offset(bsshader)
                
            # UV Scale
            if hasattr(bsshader, 'uv_scale'):
                self.export_uv_scale(bsshader)
                
            # Texture Clamping mode
            if self.basemtex.texture.image.use_clamp_x == False:
                wrap_s = 2
            else:
                wrap_s = 0
            if self.basemtex.texture.image.use_clamp_y == False:
                wrap_t = 1
            else:
                wrap_t = 0
            bsshader.texture_clamp_mode = (wrap_s + wrap_t)
            
            # Diffuse color
            bsshader.skin_tint_color.r = b_mat.diffuse_color.r
            bsshader.skin_tint_color.g = b_mat.diffuse_color.g
            bsshader.skin_tint_color.b = b_mat.diffuse_color.b
            #b_mat.diffuse_intensity = 1.0

            bsshader.lighting_effect_1 = b_mat.niftools.lightingeffect1
            bsshader.lighting_effect_2 = b_mat.niftools.lightingeffect2

            
            # Emissive
            bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
            bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
            bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
            bsshader.emissive_multiple = b_mat.emit

            # gloss
            bsshader.glossiness = b_mat.specular_hardness

            # Specular color
            bsshader.specular_color.r = b_mat.specular_color.r
            bsshader.specular_color.g = b_mat.specular_color.g
            bsshader.specular_color.b = b_mat.specular_color.b
            bsshader.specular_strength = b_mat.specular_intensity

            # Alpha
            if b_mat.use_transparency == True: 
                bsshader.alpha = (1 - b_mat.alpha)
                
            # Shader Flags
            if hasattr(bsshader, 'shader_flags_1'):
                self.export_shader_flags(b_obj, bsshader)


        if b_obj.niftools_shader.bs_shadertype == 'BSEffectShaderProperty':
            bsshader = NifFormat.BSEffectShaderProperty()

            # Alpha
            if b_mat.use_transparency == True: 
                bsshader.alpha = (1 - b_mat.alpha)
            
            # clamp Mode
            bsshader.texture_clamp_mode = 65283

            # Emissive
            bsshader.emissive_color.r = b_mat.niftools.emissive_color.r
            bsshader.emissive_color.g = b_mat.niftools.emissive_color.g
            bsshader.emissive_color.b = b_mat.niftools.emissive_color.b
            bsshader.emissive_color.a = b_mat.niftools.emissive_alpha 
            bsshader.emissive_multiple = b_mat.emit

            # Shader Flags
            if hasattr(bsshader, 'shader_flags_1'):
                self.export_shader_flags(b_obj, bsshader)


        if b_obj.niftools_shader.bs_shadertype == 'None':
            raise nif_utils.NifError(
                        "Export version expected shader. "
                        "no shader applied to mesh '%s', "
                        " these cannot be exported to NIF."
                        " Set shader before exporting."
                        % b_obj)
        # set textures
        texset = NifFormat.BSShaderTextureSet()
        bsshader.texture_set = texset
        if self.basemtex:
            texset.textures[0] = self.texture_writer.export_texture_filename(self.basemtex.texture)
        if self.normalmtex:
            texset.textures[1] = self.texture_writer.export_texture_filename(self.normalmtex.texture)
        if self.glowmtex:
            texset.textures[2] = self.texture_writer.export_texture_filename(self.glowmtex.texture)
        if self.detailmtex:
            texset.textures[3] = self.texture_writer.export_texture_filename(self.detailmtex.texture)
        if b_obj.niftools_shader.bs_shadertype == 'BSLightingShaderProperty':
            texset.num_textures = 9
            texset.textures.update_size()
            if self.detailmtex:
                texset.textures[6] = self.texture_writer.export_texture_filename(self.detailmtex.texture)
            if self.glossmtex:
                texset.textures[7] = self.texture_writer.export_texture_filename(self.glossmtex.texture)

        if b_obj.niftools_shader.bs_shadertype == 'BSEffectShaderProperty':
            bsshader.source_texture = self.texture_writer.export_texture_filename(self.basemtex.texture)
            bsshader.greyscale_texture = self.texture_writer.export_texture_filename(self.glowmtex.texture)


        return bsshader
    
    
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
        for block in self.nif_export.dict_blocks:
            if isinstance(block, NifFormat.NiTexturingProperty) \
               and block.get_hash() == texprop.get_hash():
                return block

        # no texturing property with given settings found, so use and register
        # the new one
        return texprop


    def export_nitextureprop_tex_descs(self, texprop):

        if self.basemtex:
            texprop.has_base_texture = True
            self.texture_writer.export_tex_desc(texdesc = texprop.base_texture,
                                 uvlayers = self.nif_export.dict_mesh_uvlayers,
                                 b_mat_texslot = self.basemtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.texture.name)
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.animationhelper.texture_animation.export_flip_controller(fliptxt, self.basemtex.texture, texprop, 0)

        if self.glowmtex:
            texprop.has_glow_texture = True
            self.texture_writer.export_tex_desc(texdesc = texprop.glow_texture,
                                 uvlayers = self.nif_export.dict_mesh_uvlayers,
                                 b_mat_texslot = self.glowmtex)

        if self.bumpmtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_bump_map_texture = True
                self.texture_writer.export_tex_desc(texdesc = texprop.bump_map_texture,
                                     uvlayers = self.nif_export.dict_mesh_uvlayers,
                                     b_mat_texslot = self.bumpmtex)
                texprop.bump_map_luma_scale = 1.0
                texprop.bump_map_luma_offset = 0.0
                texprop.bump_map_matrix.m_11 = 1.0
                texprop.bump_map_matrix.m_12 = 0.0
                texprop.bump_map_matrix.m_21 = 0.0
                texprop.bump_map_matrix.m_22 = 1.0

        if self.normalmtex:
                shadertexdesc = texprop.shader_textures[1]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.texture_writer.export_source_texture(texture=self.normalmtex.texture)

        if self.glossmtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_gloss_texture = True
                self.texture_writer.export_tex_desc(texdesc = texprop.gloss_texture,
                                     uvlayers = self.nif_export.dict_mesh_uvlayers,
                                     b_mat_texslot = self.glossmtex)
            else:
                shadertexdesc = texprop.shader_textures[2]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.texture_writer.export_source_texture(texture=self.glossmtex.texture)

        if self.darkmtex:
            texprop.has_dark_texture = True
            self.texture_writer.export_tex_desc(texdesc = texprop.dark_texture,
                                 uvlayers = self.nif_export.dict_mesh_uvlayers,
                                 b_mat_texslot = self.darkmtex)

        if self.detailmtex:
            texprop.has_detail_texture = True
            self.texture_writer.export_tex_desc(texdesc = texprop.detail_texture,
                                 uvlayers = self.nif_export.dict_mesh_uvlayers,
                                 b_mat_texslot = self.detailmtex)

        if self.refmtex:
            if NifOp.props.game not in self.USED_EXTRA_SHADER_TEXTURES:
                NifLog.warn("Cannot export reflection texture for this game.")
                #texprop.hasRefTexture = True
                #self.export_tex_desc(texdesc = texprop.refTexture,
                #                     uvlayers = uvlayers,
                #                     mtex = refmtex)
            else:
                shadertexdesc = texprop.shader_textures[3]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.texture_writer.export_source_texture(texture=self.refmtex.texture)

    
    def export_texture_shader_effect(self, texprop):
        # export extra shader textures
        if NifOp.props.game == 'SID_MEIER_S_RAILROADS':
            # sid meier's railroads:
            # some textures end up in the shader texture list
            # there are 5 slots available, so set them up
            texprop.num_shader_textures = 5
            texprop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(texprop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex
    
            # some texture slots required by the engine
            shadertexdesc_envmap = texprop.shader_textures[0]
            shadertexdesc_envmap.is_used = True
            shadertexdesc_envmap.texture_data.source = \
                self.texture_writer.export_source_texture(filename="RRT_Engine_Env_map.dds")
    
            shadertexdesc_cubelightmap = texprop.shader_textures[4]
            shadertexdesc_cubelightmap.is_used = True
            shadertexdesc_cubelightmap.texture_data.source = \
                self.texture_writer.export_source_texture(filename="RRT_Cube_Light_map_128.dds")

        elif NifOp.props.game == 'CIVILIZATION_IV':
            # some textures end up in the shader texture list
            # there are 4 slots available, so set them up
            texprop.num_shader_textures = 4
            texprop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(texprop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex
    
    
    def export_texture_effect(self, b_mat_texslot = None):
        """Export a texture effect block from material texture mtex (MTex, not
        Texture)."""
        texeff = NifFormat.NiTextureEffect()
        texeff.flags = 4
        texeff.rotation.set_identity()
        texeff.scale = 1.0
        texeff.model_projection_matrix.set_identity()
        texeff.texture_filtering = NifFormat.TexFilterMode.FILTER_TRILERP
        texeff.texture_clamping  = NifFormat.TexClampMode.WRAP_S_WRAP_T
        texeff.texture_type = NifFormat.EffectType.EFFECT_ENVIRONMENT_MAP
        texeff.coordinate_generation_type = NifFormat.CoordGenType.CG_SPHERE_MAP
        if b_mat_texslot:
            texeff.source_texture = self.texture_writer.export_source_texture(b_mat_texslot.texture)
            if NifOp.props.game == 'MORROWIND':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return self.register_block(texeff)


    def export_uv_offset(self, shader):
        shader.uv_offset.u = self.basemtex.offset.x
        shader.uv_offset.v = self.basemtex.offset.y
            
        return shader
        
    def export_uv_scale(self, shader):
        shader.uv_scale.u = self.basemtex.scale.x
        shader.uv_scale.v = self.basemtex.scale.y
        
        return shader
        
    def export_shader_flags(self, b_obj, shader):
        
        b_flag_list = b_obj.niftools_shader.bl_rna.properties.keys()
        if hasattr(shader, 'shader_flags'):
            for sf_flag in shader.shader_flags._names:
                if sf_flag in b_flag_list:
                    b_flag = b_obj.niftools_shader.get(sf_flag)
                    if b_flag  == True:
                        sf_flag_index = shader.shader_flags._names.index(sf_flag)
                        shader.shader_flags._items[sf_flag_index]._value = 1

        if hasattr(shader, 'shader_flags_1'):
            for sf_flag in shader.shader_flags_1._names:
                if sf_flag in b_flag_list:
                    b_flag = b_obj.niftools_shader.get(sf_flag)
                    if b_flag  == True:
                        sf_flag_index = shader.shader_flags_1._names.index(sf_flag)
                        shader.shader_flags_1._items[sf_flag_index]._value = 1

        if hasattr(shader, 'shader_flags_2'):
            for sf_flag in shader.shader_flags_2._names:
                if sf_flag in b_flag_list:
                    b_flag = b_obj.niftools_shader.get(sf_flag)
                    if b_flag  == True:
                        sf_flag_index = shader.shader_flags_2._names.index(sf_flag)
                        shader.shader_flags_2._items[sf_flag_index]._value = 1

        return shader


    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[NifOp.props.game]:
            shadername = self.EXTRA_SHADER_TEXTURES[shaderindex]
            trishape.add_integer_extra_data(shadername, shaderindex)
            

    def determine_texture_types(self, b_obj, b_mat):
        
        used_slots = self.get_used_textslots(b_mat)
        self.basemtex = None
        self.bumpmtex = None
        self.darkmtex = None
        self.detailmtex = None
        self.glossmtex = None
        self.glowmtex = None
        self.normalmtex = None
        self.refmtex = None
                
        for b_mat_texslot in used_slots:
            # check REFL-mapped textures
            # (used for "NiTextureEffect" materials)
            if b_mat_texslot.texture_coords == 'REFLECTION':
                if not b_mat_texslot.use_map_color_diffuse:
                    # it should map to colour
                    raise nif_utils.NifError(
                        "Non-COL-mapped reflection texture in mesh '%s', material '%s',"
                        " these cannot be exported to NIF.\n"
                        "Either delete all non-COL-mapped reflection textures,"
                        " or in the Shading Panel, under Material Buttons,"
                        " set texture 'Map To' to 'COL'."
                        % (b_obj.name,b_mat.name))
                if b_mat_texslot.blend_type != 'ADD':
                # it should have "ADD" blending mode
                    NifLog.warn("Reflection texture should have blending mode 'Add' on texture in mesh '{0}', material '{1}').".format(b_obj.name,b_mat.name))
                # an envmap image should have an empty... don't care
                self.refmtex = b_mat_texslot
    
    
            # check UV-mapped textures
            elif b_mat_texslot.texture_coords == 'UV':
            
                # update set of uv layers that must be exported
                if not b_mat_texslot.uv_layer in self.nif_export.dict_mesh_uvlayers:
                    self.nif_export.dict_mesh_uvlayers.append(b_mat_texslot.uv_layer)
    
                #glow tex
                if b_mat_texslot.use_map_emit:
                    #multi-check
                    if self.glowmtex:
                        raise nif_utils.NifError(
                            "Multiple emissive textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " set as Influence > emit"
                            %(b_obj.name,b_mat.name))
    
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    
                    self.glowmtex = b_mat_texslot
    
                #specular
                elif (b_mat_texslot.use_map_specular or b_mat_texslot.use_map_color_spec):
                    #multi-check
                    if self.glossmtex:
                        raise nif_utils.NifError(
                            "Multiple specular gloss textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " set as Influence > specular"
                            %(b_obj.name,b_mat.name))
    
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    
                    # got the gloss map
                    self.glossmtex = b_mat_texslot
    
                #bump map
                elif b_mat_texslot.use_map_normal and \
                    b_mat_texslot.texture.use_normal_map == False:
                    #multi-check
                    if self.bumpmtex:
                        raise nif_utils.NifError(
                            "Multiple bump/normal textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " set as Influence > normal"
                            %(b_obj.name,b_mat.name))
    
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
    
                    self.bumpmtex = b_mat_texslot
    
                #normal map
                elif b_mat_texslot.use_map_normal and \
                    b_mat_texslot.texture.use_normal_map:
                    # multi-check
                    if self.normalmtex:
                        raise nif_utils.NifError(
                            "Multiple bump/normal textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " set as Influence > normal"
                            %(b_obj.name,b_mat.name))
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.normalmtex = b_mat_texslot
    
                #darken
                elif b_mat_texslot.use_map_color_diffuse and \
                     b_mat_texslot.blend_type == 'DARKEN':
                    
                    if self.darkmtex:
                        raise nif_utils.NifError(
                            "Multiple Darken textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " with Influence > Blend Type > Dark"
                            %(b_obj.name,b_mat.name))
    
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    # got the dark map
                    self.darkmtex = b_mat_texslot
    
                #diffuse
                elif b_mat_texslot.use_map_color_diffuse:
                    if self.basemtex:
                        raise nif_utils.NifError(
                            "Multiple Diffuse textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " with Influence > Diffuse > color"
                            %(b_obj.name,b_mat.name))
    
                    self.basemtex = b_mat_texslot
    
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
    
                #detail
                elif b_mat_texslot.use_map_color_diffuse:
                    if self.detailmtex:
                        raise nif_utils.NifError(
                            "Multiple detail textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " with Influence Diffuse > color"
                            %(b_obj.name,b_mat.name))
                    # extra diffuse consider as detail texture
    
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.detailmtex = b_mat_texslot
    
                #reflection
                elif (b_mat_texslot.use_map_mirror or b_mat_texslot.use_map_raymir):
                    #multi-check
                    if self.glowmtex:
                        raise nif_utils.NifError(
                            "Multiple reflection textures"
                            " in mesh '%s', material '%s'."
                            " Make sure there is only one texture"
                            " set as Influence > Mirror/Ray Mirror"
                            %(b_obj.name,b_mat.name))
                    # got the reflection map
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.refmtex = b_mat_texslot
    
                # unsupported map
                else:
                    raise nif_utils.NifError(
                        "Do not know how to export texture '%s',"
                        " in mesh '%s', material '%s'."
                        " Either delete it, or if this texture"
                        " is to be your base texture,"
                        " go to the Shading Panel,"
                        " Material Buttons, and set texture"
                        " 'Map To' to 'COL'."
                        % (b_mat_texslot.texture.name, b_obj.name, b_mat.name))
    
            # nif only support UV-mapped textures
            else:
                NifLog.warn("Non-UV texture in mesh '{0}', material '{1}'. Either delete all "
                            "non-UV textures or create a UV map for every texture associated "
                            "with selected object and run the script again.".
                            format(b_obj.name, b_mat.name))
