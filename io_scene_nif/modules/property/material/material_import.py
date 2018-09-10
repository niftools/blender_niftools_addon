"""This script contains helper methods to import/export materials."""

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


import bpy
from io_scene_nif.utility.nif_logging import NifLog


class NiMaterialProperty:
    
    def __init__(self, parent):
        self.nif_import = parent
        
    def set_texture_helper(self, texturehelper):
        self.texturehelper = texturehelper

    def get_material_hash(self, n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop, nitextureeffect, n_wire_prop, extra_datas):
        """Helper function for import_material. Returns a key that
        uniquely identifies a material from its properties. The key
        ignores the material name as that does not affect the
        rendering.
        """
        return (n_mat_prop.get_hash()[1:] if n_mat_prop else None,  # skip first element, which is name
                n_texture_prop.get_hash() if n_texture_prop else None,
                n_alpha_prop.get_hash() if n_alpha_prop else None,
                n_specular_prop.get_hash() if n_specular_prop else None,
                nitextureeffect.get_hash() if nitextureeffect else None,
                n_wire_prop.get_hash() if n_wire_prop else None,
                tuple(extra.get_hash() for extra in extra_datas))

    @staticmethod
    def set_alpha(b_mat, n_alpha_prop):
        NifLog.debug("Alpha prop detected")
        b_mat.use_transparency = True
        b_mat.alpha = 0
        b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency
        b_mat.offset_z = n_alpha_prop.threshold  # Transparency threshold
        b_mat.niftools_alpha.alphaflag = n_alpha_prop.flags
        
        return b_mat

    def import_material(self, n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop, n_texture_effect, n_wire_prop, extra_datas):
        
        """Creates and returns a material."""
        # First check if material has been created before.
        material_hash = self.get_material_hash(n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop,
                                               n_texture_effect, n_wire_prop, extra_datas)
        try:
            return self.nif_import.dict_materials[material_hash]
        except KeyError:
            pass
        
        # name unique material
        name = self.nif_import.import_name(n_mat_prop)
        if name is None:
            name = (self.nif_import.active_obj_name + "_nt_mat")
        b_mat = bpy.data.materials.new(name)
        
        # texures
        if n_texture_prop:
            self.texturehelper.import_nitextureprop_textures(b_mat, n_texture_prop)
            if extra_datas:
                self.texturehelper.import_texture_extra_shader(b_mat, n_texture_prop, extra_datas)
        if n_texture_effect:
            self.texturehelper.import_texture_effect(b_mat, n_texture_effect)
        
        # material based properties
        if n_mat_prop:
            # Ambient color
            self.import_ambient(b_mat, n_mat_prop)

            # Diffuse color
            self.import_diffuse(b_mat, n_mat_prop)

        
            # TODO: Detect fallout 3+, use emit multi as a degree of emission
            # TODO: Test some values to find emission maximium. 0-1 -> 0-max_val
            # TODO: Should we factor in blender bounds 0.0 - 2.0
            
            # Emissive
            self.import_material_emissive(b_mat, n_mat_prop)

            # gloss
            b_mat.specular_hardness = n_mat_prop.glossiness
            
            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha(b_mat, n_alpha_prop)
    
            # Specular color
            self.import_material_specular(b_mat, n_mat_prop)

            if (not n_specular_prop) and (self.nif_import.data.version != 0x14000004):
                b_mat.specular_intensity = 0.0  # no specular prop
            else:
                b_mat.specular_intensity = 1.0  # Blender multiplies specular color with this value
                
        # check wireframe property
        if n_wire_prop:
            # enable wireframe rendering
            b_mat.type = 'WIRE'

        self.nif_import.dict_materials[material_hash] = b_mat
        return b_mat

    def import_material_specular(self, b_mat, n_mat_prop):
        b_mat.specular_color.r = n_mat_prop.specular_color.r
        b_mat.specular_color.g = n_mat_prop.specular_color.g
        b_mat.specular_color.b = n_mat_prop.specular_color.b

    def import_material_emissive(self, b_mat, n_mat_prop):
        b_mat.niftools.emissive_color.r = n_mat_prop.emissive_color.r
        b_mat.niftools.emissive_color.g = n_mat_prop.emissive_color.g
        b_mat.niftools.emissive_color.b = n_mat_prop.emissive_color.b
        b_mat.emit = n_mat_prop.emit_multi

    def import_diffuse(self, b_mat, n_mat_prop):
        b_mat.diffuse_color.r = n_mat_prop.diffuse_color.r
        b_mat.diffuse_color.g = n_mat_prop.diffuse_color.g
        b_mat.diffuse_color.b = n_mat_prop.diffuse_color.b
        b_mat.diffuse_intensity = 1.0

    def import_ambient(self, b_mat, n_mat_prop):
        b_mat.niftools.ambient_color.r = n_mat_prop.ambient_color.r
        b_mat.niftools.ambient_color.g = n_mat_prop.ambient_color.g
        b_mat.niftools.ambient_color.b = n_mat_prop.ambient_color.b
