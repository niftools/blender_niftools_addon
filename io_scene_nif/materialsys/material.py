"""This script contains helper methods to import/export materials."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

class material_import():
    
    def __init__(self, parent):
        self.nif_common = parent
        
        # dictionary of materials, to reuse materials
        self.materials = {}
        self.texturehelper = self.nif_common.texturehelper

    def get_material_hash(self, n_mat_prop, n_texture_prop,
                          n_alpha_prop, n_specular_prop,
                          textureEffect, n_wire_prop,
                          bsShaderProperty, extra_datas):
        """Helper function for import_material. Returns a key that
        uniquely identifies a material from its properties. The key
        ignores the material name as that does not affect the
        rendering.
        """
        return (n_mat_prop.get_hash()[1:]   if n_mat_prop else None, # skip first element, which is name
                n_texture_prop.get_hash()   if n_texture_prop  else None,
                n_alpha_prop.get_hash()     if n_alpha_prop else None,
                n_specular_prop.get_hash()  if n_specular_prop  else None,
                textureEffect.get_hash()    if textureEffect else None,
                n_wire_prop.get_hash()      if n_wire_prop  else None,
                bsShaderProperty.get_hash() if bsShaderProperty else None,
                tuple(extra.get_hash()      for extra in extra_datas))
        
    
    def import_material(self, n_mat_prop, n_texture_prop,
                        n_alpha_prop, n_specular_prop,
                        textureEffect, n_wire_prop,
                        bsShaderProperty, extra_datas):
        
        """Creates and returns a material."""
        # First check if material has been created before.
        material_hash = self.get_material_hash(n_mat_prop, n_texture_prop,
                                               n_alpha_prop, n_specular_prop,
                                               textureEffect, n_wire_prop,
                                               bsShaderProperty,
                                               extra_datas)
        try:
            return self.materials[material_hash]                
        except KeyError:
            pass
        
        # name unique material
        name = self.nif_common.import_name(n_mat_prop)
        b_mat = bpy.data.materials.new(name)
        
        # get apply mode, and convert to blender "blending mode"
        blend_type = 'MIX' # default
        if n_texture_prop:
            blend_type = self.get_b_blend_type_from_n_apply_mode(
                n_texture_prop.apply_mode)
        elif bsShaderProperty:
            # default blending mode for fallout 3
            blend_type = 'MIX'
        # Sets the colors
        
        # textures
        base_texture = None
        glow_texture = None
        envmapTexture = None # for NiTextureEffect
        bumpTexture = None
        dark_texture = None
        detail_texture = None
        refTexture = None
        if n_texture_prop:
            # standard texture slots
            baseTexDesc = n_texture_prop.base_texture
            glowTexDesc = n_texture_prop.glow_texture
            bumpTexDesc = n_texture_prop.bump_map_texture
            glossTexDesc = n_texture_prop.gloss_texture
            darkTexDesc = n_texture_prop.dark_texture
            detailTexDesc = n_texture_prop.detail_texture
            refTexDesc = None
            # extra texture shader slots
            for shader_tex_desc in n_texture_prop.shader_textures:
                if not shader_tex_desc.is_used:
                    continue
                # it is used, figure out the slot it is used for
                for extra in extra_datas:
                    if extra.integer_data == shader_tex_desc.map_index:
                        # found!
                        shader_name = extra.name
                        break
                else:
                    # none found
                    self.nif_common.warning(
                        "No slot for shader texture %s."
                        % shader_tex_desc.texture_data.source.file_name)
                    continue
                try:
                    extra_shader_index = (
                        self.EXTRA_SHADER_TEXTURES.index(shader_name))
                except ValueError:
                    # shader_name not in self.EXTRA_SHADER_TEXTURES
                    self.nif_common.warning(
                        "No slot for shader texture %s."
                        % shader_tex_desc.texture_data.source.file_name)
                    continue
                if extra_shader_index == 0:
                    # EnvironmentMapIndex
                    if shader_tex_desc.texture_data.source.file_name.lower().startswith("rrt_engine_env_map"):
                        # sid meier's railroads: env map generated by engine
                        # we can skip this
                        continue
                    # XXX todo, civ4 uses this
                    self.nif_common.warning("Skipping environment map texture.")
                    continue
                elif extra_shader_index == 1:
                    # NormalMapIndex
                    bumpTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 2:
                    # SpecularIntensityIndex
                    glossTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 3:
                    # EnvironmentIntensityIndex (this is reflection)
                    refTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 4:
                    # LightCubeMapIndex
                    if shader_tex_desc.texture_data.source.file_name.lower().startswith("rrt_cube_light_map"):
                        # sid meier's railroads: light map generated by engine
                        # we can skip this
                        continue
                    self.nif_common.warning("Skipping light cube texture.")
                    continue
                elif extra_shader_index == 5:
                    # ShadowTextureIndex
                    self.nif_common.warning("Skipping shadow texture.")
                    continue
                    
            if baseTexDesc:
                base_texture = self.texturehelper.import_texture(baseTexDesc.source)
                if base_texture:
                    b_mat_texslot = b_mat.texture_slots.create(0)
                    b_mat_texslot.texture = base_texture
                    b_mat_texslot.use = True
                    
                    # Influence mapping
                    
                    # Mapping
                    b_mat_texslot.texture_coords = 'UV'
                    b_mat_texslot.uv_layer = self.get_uv_layer_name(baseTexDesc.uv_set)
                    
                    # Influence
                    b_mat_texslot.use_map_color_diffuse = True
                    b_mat_texslot.blend_type = blend_type
                    if(n_alpha_prop):
                        b_mat_texslot.use_map_alpha
                    # update: needed later
                    base_texture = b_mat_texslot
                    
            if bumpTexDesc:
                bump_texture = self.texturehelper.import_texture(bumpTexDesc.source)
                if bump_texture:
                    b_mat_texslot = b_mat.texture_slots.create(1)
                    b_mat_texslot.texture = bump_texture
                    b_mat_texslot.use = True
                    
                    # Influence mapping
                    b_mat_texslot.texture.use_normal_map = False # causes artifacts otherwise.
                    b_mat_texslot.use_map_color_diffuse = False
                    # Mapping
                    b_mat_texslot.texture_coords = 'UV'
                    b_mat_texslot.uv_layer = self.get_uv_layer_name(bumpTexDesc.uv_set)
                    # Influence
                    b_mat_texslot.use_map_normal = True
                    b_mat_texslot.blend_type = blend_type
                    if(n_alpha_prop):
                        b_mat_texslot.use_map_alpha
                        
                    # update: needed later
                    bump_texture = b_mat_texslot
                    
            if glowTexDesc:
                glow_texture = self.texturehelper.import_texture(glowTexDesc.source)
                if glow_texture:
                    b_mat_texslot = b_mat.texture_slots.create(2)
                    b_mat_texslot.texture = glow_texture
                    b_mat_texslot.use = True
                    
                    # Influence mapping
                    b_mat_texslot.texture.use_alpha = False
                    b_mat_texslot.use_map_color_diffuse = False
                    # Mapping
                    b_mat_texslot.texture_coords = 'UV'
                    b_mat_texslot.uv_layer = self.get_uv_layer_name(glowTexDesc.uv_set)
                    # Influence
                    b_mat_texslot.use_map_emit = True
                    b_mat_texslot.blend_type = blend_type
                    if(n_alpha_prop):
                        b_mat_texslot.use_map_alpha
                        
                    # update: needed later
                    glow_texture = b_mat_texslot
                    
            if glossTexDesc:
                gloss_texture = self.texturehelper.import_texture(glossTexDesc.source)
                if gloss_texture:
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the specularity channel
                    mapto = FIXME.use_map_specular
                    # set the texture for the material
                    material.setTexture(4, gloss_texture, texco, mapto)
                    mgloss_texture = material.getTextures()[4]
                    mgloss_texture.uv_layer = self.get_uv_layer_name(glossTexDesc.uv_set)
            
            if darkTexDesc:
                dark_texture = self.texturehelper.import_texture(darkTexDesc.source)
                if dark_texture:
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the COL channel
                    mapto = FIXME.use_map_color_diffuse
                    # set the texture for the material
                    material.setTexture(5, dark_texture, texco, mapto)
                    mdark_texture = material.getTextures()[5]
                    mdark_texture.uv_layer = self.get_uv_layer_name(darkTexDesc.uv_set)
                    # set blend mode to "DARKEN"
                    mdark_texture.blend_type = 'DARKEN'
            
            if detailTexDesc:
                detail_texture = self.texturehelper.import_texture(detailTexDesc.source)
                if detail_texture:
                    # import detail texture as extra base texture
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the COL channel
                    mapto = FIXME.use_map_color_diffuse
                    # set the texture for the material
                    material.setTexture(6, detail_texture, texco, mapto)
                    mdetail_texture = material.getTextures()[6]
                    mdetail_texture.uv_layer = self.get_uv_layer_name(detailTexDesc.uv_set)
            
            if refTexDesc:
                refTexture = self.texturehelper.import_texture(refTexDesc.source)
                if refTexture:
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the base color and emit channel
                    mapto = Blender.Texture.MapTo.REF
                    # set the texture for the material
                    material.setTexture(7, refTexture, texco, mapto)
                    mrefTexture = material.getTextures()[7]
                    mrefTexture.uv_layer = self.get_uv_layer_name(refTexDesc.uv_set)
        
        # if not a texture property, but a bethesda shader property...
        elif bsShaderProperty:
            # also contains textures, used in fallout 3
            baseTexFile = bsShaderProperty.texture_set.textures[0]
            if baseTexFile:
                base_texture = self.texturehelper.import_texture(baseTexFile)
                if base_texture:
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the base color channel
                    mapto = FIXME.use_map_color_diffuse
                    # set the texture for the material
                    material.setTexture(0, base_texture, texco, mapto)
                    mbase_texture = material.getTextures()[0]
                    mbase_texture.blend_type = blend_type

            glowTexFile = bsShaderProperty.texture_set.textures[2]
            if glowTexFile:
                glow_texture = self.texturehelper.import_texture(glowTexFile)
                if glow_texture:
                    # glow maps use alpha from rgb intensity
                    glow_texture.use_calculate_alpha = True
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the base color and emit channel
                    mapto = FIXME.use_map_color_diffuse | FIXME.use_map_emit
                    # set the texture for the material
                    material.setTexture(1, glow_texture, texco, mapto)
                    mglow_texture = material.getTextures()[1]
                    mglow_texture.blend_type = blend_type

            bumpTexFile = bsShaderProperty.texture_set.textures[1]
            if bumpTexFile:
                bumpTexture = self.texturehelper.import_texture(bumpTexFile)
                if bumpTexture:
                    # set the texture to use face UV coordinates
                    texco = 'UV'
                    # map the texture to the normal channel
                    mapto = FIXME.use_map_normal
                    # set the texture for the material
                    material.setTexture(2, bumpTexture, texco, mapto)
                    mbumpTexture = material.getTextures()[2]
                    mbumpTexture.blend_type = blend_type

        if textureEffect:
            envmapTexture = self.texturehelper.import_texture(textureEffect.source_texture)
            if envmapTexture:
                # set the texture to use face reflection coordinates
                texco = 'REFLECTION'
                # map the texture to the base color channel
                mapto = FIXME.use_map_color_diffuse
                # set the texture for the material
                material.setTexture(3, envmapTexture, texco, mapto)
                menvmapTexture = material.getTextures()[3]
                menvmapTexture.blend_type = 'ADD'
        
        # Diffuse color
        b_mat.diffuse_color[0] = n_mat_prop.diffuse_color.r
        b_mat.diffuse_color[1] = n_mat_prop.diffuse_color.g
        b_mat.diffuse_color[2] = n_mat_prop.diffuse_color.b
        b_mat.diffuse_intensity = 1.0
        
        # TODO - Detect fallout 3+, use emit multi as a degree of emission
        #        test some values to find emission maximium. 0-1 -> 0-max_val
        # Should we factor in blender bounds 0.0 - 2.0
        
        # Emissive
        b_mat.niftools.emissive_color[0] = n_mat_prop.emissive_color.r
        b_mat.niftools.emissive_color[1] = n_mat_prop.emissive_color.g
        b_mat.niftools.emissive_color[2] = n_mat_prop.emissive_color.b
        if(b_mat.niftools.emissive_color[0] > self.nif_common.properties.epsilon or 
           b_mat.niftools.emissive_color[1] > self.nif_common.properties.epsilon or 
           b_mat.niftools.emissive_color[2] > self.nif_common.properties.epsilon):
            b_mat.emit = 1.0
        else:
            b_mat.emit = 0.0
            
        # gloss
        gloss = n_mat_prop.glossiness
        hardness = int(gloss * 4) # just guessing really
        if hardness < 1: hardness = 1
        if hardness > 511: hardness = 511
        b_mat.specular_hardness = hardness
        
        # Alpha
        if n_alpha_prop:
            if(n_mat_prop.alpha < 1.0):
                self.nif_common.debug("Alpha prop detected")
                b_mat.use_transparency = True 
                b_mat.alpha = n_mat_prop.alpha
                b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency

        # Specular color
        b_mat.specular_color[0] = n_mat_prop.specular_color.r
        b_mat.specular_color[1] = n_mat_prop.specular_color.g
        b_mat.specular_color[2] = n_mat_prop.specular_color.b
        
        if (not n_specular_prop) and (self.nif_common.data.version != 0x14000004):
            b_mat.specular_intensity = 0.0 # no specular prop 
        else:
            b_mat.specular_intensity = 1.0 # Blender multiplies specular color with this value
        
        # check wireframe property
        if n_wire_prop:
            # enable wireframe rendering
            b_mat.type = 'WIRE'

        self.materials[material_hash] = b_mat
        return b_mat

    def get_b_blend_type_from_n_apply_mode(self, n_apply_mode):
        # TODO - Check out n_apply_modes
        if n_apply_mode == NifFormat.ApplyMode.APPLY_MODULATE:
            return "MIX"
        # TODO - These seem unsupported by Blender, check
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_REPLACE:
            return "MIX"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_DECAL:
            return "MIX"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT:
            return "LIGHTEN"
        elif n_apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT2: # used by Oblivion for parallax
            return "MULTIPLY"
        self.nif_common.warning(
            "Unknown apply mode (%i) in material,"
            " using blend type 'MIX'" % n_apply_mode)
        return "MIX"
    
    # TODO: Move to texture.py
    def get_uv_layer_name(self, uvset):
        return "UVMap.%03i" % uvset if uvset != 0 else "UVMap"
