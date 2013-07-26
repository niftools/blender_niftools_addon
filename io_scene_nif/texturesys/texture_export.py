"""This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

import io_scene_nif.utility.nif_utils

import os.path

class Texture():
    
    # dictionary of texture files, to reuse textures
    textures = {}
    #Default ordering of Extra data blocks for different games
    USED_EXTRA_SHADER_TEXTURES = {'SID_MEIER_S_RAILROADS': (3, 0, 4, 1, 5, 2),
                                  'CIVILIZATION_IV': (3, 0, 1, 2)}
    
    def __init__(self, parent):
        self.nif_export = parent
        self.properties = parent.properties
                
    def export_texture_filename(self, texture):
        """Returns file name from texture.

        @param texture: The texture object in blender.
        @return: The file name of the image used in the texture.
        """
        if texture.type == 'ENVIRONMENT_MAP':
            # this works for morrowind only
            if self.properties.game != 'MORROWIND':
                raise nif_utils.NifExportError(
                    "cannot export environment maps for nif version '%s'"
                    %self.properties.game)
            return "enviro 01.TGA"
        elif texture.type == 'IMAGE':
            # get filename from image

            # XXX still needed? can texture.image be None in current blender?
            # check that image is loaded
            if texture.image is None:
                raise nif_utils.NifExportError(
                    "image type texture has no file loaded ('%s')"
                    % texture.name)

            filename = texture.image.filepath

            # warn if packed flag is enabled
            if texture.image.packed_file:
                self.nif_export.warning(
                    "Packed image in texture '%s' ignored, "
                    "exporting as '%s' instead."
                    % (texture.name, filename))

            # try and find a DDS alternative, force it if required
            ddsfilename = "%s%s" % (filename[:-4], '.dds')
            if os.path.exists(ddsfilename) or self.properties.force_dds:
                filename = ddsfilename

            # sanitize file path
            if not self.properties.game in ('MORROWIND', 'OBLIVION',
                                           'FALLOUT_3'):
                # strip texture file path
                filename = os.path.basename(filename)
            else:
                # strip the data files prefix from the texture's file name
                filename = filename.lower()
                idx = filename.find("textures")
                if ( idx >= 0 ):
                    filename = filename[idx:]
                else:
                    self.nif_export.warning(
                        "%s does not reside in a 'Textures' folder;"
                        " texture path will be stripped"
                        " and textures may not display in-game" % filename)
                    filename = os.path.basename(filename)
            # for linux export: fix path seperators
            return filename.replace('/', '\\')
        else:
            # texture must be of type IMAGE or ENVMAP
            raise nif_utils.NifExportError(
                "Error: Texture '%s' must be of type IMAGE or ENVMAP"
                % texture.name)
            

    def export_source_texture(self, texture=None, filename=None):
        """Export a NiSourceTexture.

        :param texture: The texture object in blender to be exported.
        :param filename: The full or relative path to the texture file
            (this argument is used when exporting NiFlipControllers
            and when exporting default shader slots that have no use in
            being imported into Blender).
        :return: The exported NiSourceTexture block.
        """

        # create NiSourceTexture
        srctex = NifFormat.NiSourceTexture()
        srctex.use_external = True
        if not filename is None:
            # preset filename
            srctex.file_name = filename
        elif not texture is None:
            srctex.file_name = self.export_texture_filename(texture)
        else:
            # this probably should not happen
            self.nif_export.warning(
                "Exporting source texture without texture or filename (bug?).")

        # fill in default values (TODO: can we use 6 for everything?)
        if self.nif_export.version >= 0x0a000100:
            srctex.pixel_layout = 6
        else:
            srctex.pixel_layout = 5
        srctex.use_mipmaps = 1
        srctex.alpha_format = 3
        srctex.unknown_byte = 1

        # search for duplicate
        for block in self.nif_export.blocks:
            if isinstance(block, NifFormat.NiSourceTexture) and block.get_hash() == srctex.get_hash():
                return block

        # no identical source texture found, so use and register
        # the new one
        return self.nif_export.register_block(srctex, texture)
    
    
    def export_tex_desc(self, texdesc=None, uvlayers=None, b_mat_texslot=None):
        """Helper function for export_texturing_property to export each texture
        slot."""
        try:
            texdesc.uv_set = uvlayers.index(b_mat_texslot.uv_layer) if b_mat_texslot.uv_layer else 0
        except ValueError: # mtex.uv_layer not in uvlayers list
            self.nif_export.warning(
                "Bad uv layer name '%s' in texture '%s'."
                " Falling back on first uv layer"
                % (b_mat_texslot.uv_layer, b_mat_texslot.texture.name))
            texdesc.uv_set = 0 # assume 0 is active layer

        texdesc.source = self.export_source_texture(b_mat_texslot.texture)
    
    
    def export_bs_shader_property(
        self, basemtex=None, normalmtex=None, glowmtex=None):
        """Export a Bethesda shader property block."""

        # create new block
        bsshader = NifFormat.BSShaderPPLightingProperty()
        # set shader options
        bsshader.shader_type = self.nif_export.EXPORT_FO3_SHADER_TYPE
        bsshader.shader_flags.zbuffer_test = self.nif_export.EXPORT_FO3_SF_ZBUF
        bsshader.shader_flags.shadow_map = self.nif_export.EXPORT_FO3_SF_SMAP
        bsshader.shader_flags.shadow_frustum = self.nif_export.EXPORT_FO3_SF_SFRU
        bsshader.shader_flags.window_environment_mapping = self.nif_export.EXPORT_FO3_SF_WINDOW_ENVMAP
        bsshader.shader_flags.empty = self.nif_export.EXPORT_FO3_SF_EMPT
        bsshader.shader_flags.unknown_31 = self.nif_export.EXPORT_FO3_SF_UN31
        # set textures
        texset = NifFormat.BSShaderTextureSet()
        bsshader.texture_set = texset
        if basemtex:
            texset.textures[0] = self.export_texture_filename(basemtex.texture)
        if normalmtex:
            texset.textures[1] = self.export_texture_filename(normalmtex.texture)
        if glowmtex:
            texset.textures[2] = self.export_texture_filename(glowmtex.texture)

        # search for duplicates
        # DISABLED: the Fallout 3 engine cannot handle them
        #for block in self.blocks:
        #    if (isinstance(block, NifFormat.BSShaderPPLightingProperty)
        #        and block.get_hash() == bsshader.get_hash()):
        #        return block

        # no duplicate found, so use and register new one
        return self.nif_export.register_block(bsshader)
    
    
    def export_texturing_property(self, flags=0x0001, applymode=None, uvlayers=None,
                                  basemtex=None, glowmtex=None, bumpmtex=None, 
                                  normalmtex=None, glossmtex=None, darkmtex=None, 
                                  detailmtex=None, refmtex=None):
        """Export texturing property. The parameters basemtex,
        glowmtex, bumpmtex, ... are the Blender material textures
        that correspond to the base, glow, bumpmap, ... textures. 
        The uvlayers parameter is a list of uvlayer strings.
        """

        texprop = NifFormat.NiTexturingProperty()

        texprop.flags = flags
        texprop.apply_mode = applymode
        texprop.texture_count = 7

        # export extra shader textures
        if self.properties.game == 'SID_MEIER_S_RAILROADS':
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
                self.export_source_texture(filename="RRT_Engine_Env_map.dds")

            shadertexdesc_cubelightmap = texprop.shader_textures[4]
            shadertexdesc_cubelightmap.is_used = True
            shadertexdesc_cubelightmap.texture_data.source = \
                self.export_source_texture(filename="RRT_Cube_Light_map_128.dds")

            # the other slots are exported below

        elif self.properties.game == 'CIVILIZATION_IV':
            # some textures end up in the shader texture list
            # there are 4 slots available, so set them up
            texprop.num_shader_textures = 4
            texprop.shader_textures.update_size()
            for mapindex, shadertexdesc in enumerate(texprop.shader_textures):
                # set default values
                shadertexdesc.is_used = False
                shadertexdesc.map_index = mapindex

        if basemtex:
            texprop.has_base_texture = True
            self.export_tex_desc(texdesc = texprop.base_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = basemtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.texture.name)
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.animationhelper.texture_animation.export_flip_controller(fliptxt, basemtex.texture, texprop, 0)

        if glowmtex:
            texprop.has_glow_texture = True
            self.export_tex_desc(texdesc = texprop.glow_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = glowmtex)

        if bumpmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_bump_map_texture = True
                self.export_tex_desc(texdesc = texprop.bump_map_texture,
                                     uvlayers = uvlayers,
                                     b_mat_texslot = bumpmtex)
                texprop.bump_map_luma_scale = 1.0
                texprop.bump_map_luma_offset = 0.0
                texprop.bump_map_matrix.m_11 = 1.0
                texprop.bump_map_matrix.m_12 = 0.0
                texprop.bump_map_matrix.m_21 = 0.0
                texprop.bump_map_matrix.m_22 = 1.0

        if normalmtex:
                shadertexdesc = texprop.shader_textures[1]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=normalmtex.texture)

        if glossmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_gloss_texture = True
                self.export_tex_desc(texdesc = texprop.gloss_texture,
                                     uvlayers = uvlayers,
                                     b_mat_texslot = glossmtex)
            else:
                shadertexdesc = texprop.shader_textures[2]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=glossmtex.texture)

        if darkmtex:
            texprop.has_dark_texture = True
            self.export_tex_desc(texdesc = texprop.dark_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = darkmtex)

        if detailmtex:
            texprop.has_detail_texture = True
            self.export_tex_desc(texdesc = texprop.detail_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = detailmtex)

        if refmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                self.nif_export.warning(
                    "Cannot export reflection texture for this game.")
                #texprop.hasRefTexture = True
                #self.export_tex_desc(texdesc = texprop.refTexture,
                #                     uvlayers = uvlayers,
                #                     mtex = refmtex)
            else:
                shadertexdesc = texprop.shader_textures[3]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=refmtex.texture)

        # search for duplicate
        for block in self.nif_export.blocks:
            if isinstance(block, NifFormat.NiTexturingProperty) \
               and block.get_hash() == texprop.get_hash():
                return block

        # no texturing property with given settings found, so use and register
        # the new one
        return self.nif_export.register_block(texprop)
    
    
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
            texeff.source_texture = self.export_source_texture(b_mat_texslot.texture)
            if self.properties.game == 'MORROWIND':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return self.register_block(texeff)


    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[self.properties.game]:
            shadername = self.EXTRA_SHADER_TEXTURES[shaderindex]
            trishape.add_integer_extra_data(shadername, shaderindex)
            
            
    def export_texture(self, b_obj, b_mat, b_mat_texslot):
            
        # check REFL-mapped textures
        # (used for "NiTextureEffect" materials)
        if b_mat_texslot.texture_coords == 'REFLECTION':
            # of course the user should set all kinds of other
            # settings to make the environment mapping come out
            # (MapTo "COL", blending mode "Add")
            # but let's not care too much about that
            # only do some simple checks
            if not b_mat_texslot.use_map_color_diffuse:
                # it should map to colour
                raise nif_utils.NifExportError("Non-COL-mapped reflection texture in mesh '%s', material '%s',"
                                     " these cannot be exported to NIF.\n"
                                     "Either delete all non-COL-mapped reflection textures,"
                                     " or in the Shading Panel, under Material Buttons,"
                                     " set texture 'Map To' to 'COL'."
                                     % (b_mesh.name,b_mat.name))
            if b_mat_texslot.blend_type != 'ADD':
            # it should have "ADD" blending mode
                 self.nif_export.warning("Reflection texture should have blending"
                             " mode 'Add' on texture"
                             " in mesh '%s', material '%s')."
                             % (b_obj.name,b_mat.name))
            # an envmap image should have an empty... don't care
            mesh_texeff_mtex = b_mat_texslot

                    # check UV-mapped textures
        elif b_mat_texslot.texture_coords == 'UV':
        # update set of uv layers that must be exported
            if not b_mat_texslot.uv_layer in mesh_uvlayers:
                mesh_uvlayers.append(b_mat_texslot.uv_layer)

            #glow tex
            if b_mat_texslot.use_map_emit:
                #multi-check
                if mesh_glow_mtex:
                    raise nif_utils.NifExportError("Multiple glow textures in mesh '%s', material '%s'.\n"
                                         "Make sure Texture -> Influence -> Shading -> Emit is disabled"
                                         %(b_mesh.name,b_mat.name))
                            
                '''
                TODO_3.0 - Fallout3 + specific.
                Check if these are still possible
                # check if calculation of alpha channel is enabled
                # for this texture
                if b_mat_texslot.texture.use_calculate_alpha and b_mat_texslot.use_map_alpha:
                self.warning(
                    "In mesh '%s', material '%s': glow texture must have"
                    " CALCALPHA flag set, and must have MapTo.ALPHA enabled."
                    %(b_obj.name,b_mat.name))
                '''
                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                
                mesh_glow_mtex = b_mat_texslot

            #specular
            elif b_mat_texslot.use_map_specular:
                #multi-check
                if mesh_gloss_mtex:
                    raise nif_utils.NifExportError("Multiple gloss textures in"
                                         " mesh '%s', material '%s'."
                                         " Make sure there is only one texture"
                                         " with MapTo.SPEC"
                                         %(b_mesh.name,b_mat.name))

                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                
                # got the gloss map
                mesh_gloss_mtex = b_mat_texslot

            #bump map
            elif b_mat_texslot.use_map_normal:
                #multi-check
                if mesh_bump_mtex:
                    raise nif_utils.NifExportError("Multiple bump/normal textures"
                                         " in mesh '%s', material '%s'."
                                         " Make sure there is only one texture"
                                         " with MapTo.NOR"
                                         %(b_mesh.name,b_mat.name))

                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True

                mesh_bump_mtex = b_mat_texslot

            #darken
            elif b_mat_texslot.use_map_color_diffuse and \
                 b_mat_texslot.blend_type == 'DARKEN' and \
                 not mesh_dark_mtex:

                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                # got the dark map
                mesh_dark_mtex = b_mat_texslot

            #diffuse
            elif b_mat_texslot.use_map_color_diffuse and \
                 not mesh_base_mtex:

                mesh_base_mtex = b_mat_texslot

                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True

                    '''
                    # in this case, Blender replaces the texture transparant parts with the underlying material color...
                    # in NIF, material alpha is multiplied with texture alpha channel...
                    # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                    # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                    # but...

                    if mesh_mat_transparency > self.properties.epsilon:
                        raise nif_utils.NifExportError(
                            "Cannot export this type of"
                            " transparency in material '%s': "
                            " instead, try to set alpha to 0.0"
                            " and to use the 'Var' slider"
                            " in the 'Map To' tab under the"
                            " material buttons."
                            %b_mat.name)
                    if (b_mat.animation_data and b_mat.animation_data.action.fcurves['Alpha']):
                        raise nif_utils.NifExportError(
                            "Cannot export animation for"
                            " this type of transparency"
                            " in material '%s':"
                            " remove alpha animation,"
                            " or turn off MapTo.ALPHA,"
                            " and try again."
                            %b_mat.name)

                    mesh_mat_transparency = b_mat_texslot.varfac # we must use the "Var" value
                    '''

            #normal map
            elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map:
                if mesh_normal_mtex:
                    raise nif_utils.NifExportError(
                        "Multiple bump/normal textures"
                        " in mesh '%s', material '%s'."
                        " Make sure there is only one texture"
                        " with MapTo.NOR"
                        %(b_mesh.name, b_mat.name))
                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                mesh_normal_mtex = b_mat_texslot

            #detail
            elif b_mat_texslot.use_map_color_diffuse and \
                 not mesh_detail_mtex:
                # extra diffuse consider as detail texture

                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                mesh_detail_mtex = b_mat_texslot

            #reflection
            elif b_mat_texslot.mapto & Blender.Texture.MapTo.REF:
                # got the reflection map
                if mesh_ref_mtex:
                    raise nif_utils.NifExportError(
                        "Multiple reflection textures"
                        " in mesh '%s', material '%s'."
                        " Make sure there is only one texture"
                        " with MapTo.REF"
                        %(b_mesh.name,b_mat.name))
                # check if alpha channel is enabled for this texture
                if(b_mat_texslot.use_map_alpha):
                    mesh_hasalpha = True
                mesh_ref_mtex = b_mat_texslot

            # unsupported map
            else:
                raise nif_utils.NifExportError(
                    "Do not know how to export texture '%s',"
                    " in mesh '%s', material '%s'."
                    " Either delete it, or if this texture"
                    " is to be your base texture,"
                    " go to the Shading Panel,"
                    " Material Buttons, and set texture"
                    " 'Map To' to 'COL'."
                    % (b_mat_texslot.texture.name,b_obj.name,b_mat.name))

        # nif only support UV-mapped textures
        else:
            raise nif_utils.NifExportError(
                "Non-UV texture in mesh '%s', material '%s'."
                " Either delete all non-UV textures,"
                " or in the Shading Panel,"
                " under Material Buttons,"
                " set texture 'Map Input' to 'UV'."
                %(b_obj.name,b_mat.name))

