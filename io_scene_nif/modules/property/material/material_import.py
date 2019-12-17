"""This script contains helper methods to import materials."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2012, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules.object.object_import import Object
from io_scene_nif.utility.util_global import NifData
from io_scene_nif.utility.util_logging import NifLog


class Material:

    def __init__(self, parent):
        self.nif_import = parent

    def set_texture_helper(self, texture_helper):
        self.texturehelper = texture_helper

    def get_material_hash(self, n_mat_prop, n_texture_prop,
                          n_alpha_prop, n_specular_prop,
                          texture_effect, n_wire_prop,
                          bs_shader_property, bs_effect_shader_property,
                          extra_datas):
        """Helper function for import_material. Returns a key that
        uniquely identifies a material from its properties. The key
        ignores the material name as that does not affect the
        rendering.
        """
        return (n_mat_prop.get_hash()[1:] if n_mat_prop else None,  # skip first element, which is name
                n_texture_prop.get_hash() if n_texture_prop else None,
                n_alpha_prop.get_hash() if n_alpha_prop else None,
                n_specular_prop.get_hash() if n_specular_prop else None,
                texture_effect.get_hash() if texture_effect else None,
                n_wire_prop.get_hash() if n_wire_prop else None,
                bs_shader_property.get_hash() if bs_shader_property else None,
                bs_effect_shader_property.get_hash() if bs_effect_shader_property else None,
                tuple(extra.get_hash() for extra in extra_datas))

    def set_alpha(self, b_mat, shader_property, n_alpha_prop):
        NifLog.debug("Alpha prop detected")
        b_mat.use_transparency = True
        if hasattr(shader_property, 'alpha'):
            b_mat.alpha = (1 - shader_property.alpha)
        else:
            b_mat.alpha = 0
        b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency
        b_mat.offset_z = n_alpha_prop.threshold  # transparency threshold
        b_mat.niftools_alpha.alphaflag = n_alpha_prop.flags

        return b_mat

    def import_material(self, n_mat_prop, n_texture_prop,
                        n_alpha_prop, n_specular_prop,
                        texture_effect, n_wire_prop,
                        bs_shader_property, bs_effect_shader_property,
                        extra_datas):

        """Creates and returns a material."""
        # First check if material has been created before.
        material_hash = self.get_material_hash(n_mat_prop, n_texture_prop,
                                               n_alpha_prop, n_specular_prop,
                                               texture_effect, n_wire_prop,
                                               bs_shader_property,
                                               bs_effect_shader_property,
                                               extra_datas)
        try:
            return self.nif_import.dict_materials[material_hash]
        except KeyError:
            pass

        # name unique material
        name = Object.import_name(n_mat_prop)
        if not name:
            name = (self.nif_import.active_obj_name + "_nt_mat")
        b_mat = bpy.data.materials.new(name)

        # texures
        if n_texture_prop:
            self.texturehelper.import_nitextureprop_textures(b_mat, n_texture_prop)
            if extra_datas:
                self.texturehelper.import_texture_extra_shader(b_mat, n_texture_prop, extra_datas)
        if bs_shader_property:
            self.texturehelper.import_bsshaderproperty(b_mat, bs_shader_property)
        if bs_effect_shader_property:
            self.texturehelper.import_bseffectshaderproperty(b_mat, bs_effect_shader_property)
        if texture_effect:
            self.texturehelper.import_texture_effect(b_mat, texture_effect)

        # material based properties
        if n_mat_prop:
            # Ambient color
            b_mat.niftools.ambient_color.r = n_mat_prop.ambient_color.r
            b_mat.niftools.ambient_color.g = n_mat_prop.ambient_color.g
            b_mat.niftools.ambient_color.b = n_mat_prop.ambient_color.b

            # Diffuse color
            b_mat.diffuse_color.r = n_mat_prop.diffuse_color.r
            b_mat.diffuse_color.g = n_mat_prop.diffuse_color.g
            b_mat.diffuse_color.b = n_mat_prop.diffuse_color.b
            b_mat.diffuse_intensity = 1.0

            # TODO [property][material] - Detect fallout 3+, use emit multi as a degree of emission
            #        test some values to find emission maximium. 0-1 -> 0-max_val
            # Should we factor in blender bounds 0.0 - 2.0

            # Emissive
            b_mat.niftools.emissive_color.r = n_mat_prop.emissive_color.r
            b_mat.niftools.emissive_color.g = n_mat_prop.emissive_color.g
            b_mat.niftools.emissive_color.b = n_mat_prop.emissive_color.b
            b_mat.emit = n_mat_prop.emit_multi

            # gloss
            b_mat.specular_hardness = n_mat_prop.glossiness

            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha(b_mat, bs_shader_property, n_alpha_prop)

            # Specular color
            b_mat.specular_color.r = n_mat_prop.specular_color.r
            b_mat.specular_color.g = n_mat_prop.specular_color.g
            b_mat.specular_color.b = n_mat_prop.specular_color.b

            if (not n_specular_prop) and (NifData.data.version != 0x14000004):
                b_mat.specular_intensity = 0.0  # no specular prop
            else:
                b_mat.specular_intensity = 1.0  # Blender multiplies specular color with this value

        # shader based properties
        if n_mat_prop is None and bs_shader_property:

            # Diffuse color
            if bs_shader_property.skin_tint_color:
                b_mat.diffuse_color.r = bs_shader_property.skin_tint_color.r
                b_mat.diffuse_color.g = bs_shader_property.skin_tint_color.g
                b_mat.diffuse_color.b = bs_shader_property.skin_tint_color.b
                b_mat.diffuse_intensity = 1.0

            if (b_mat.diffuse_color.r + b_mat.diffuse_color.g + b_mat.diffuse_color.g) == 0:
                b_mat.diffuse_color.r = bs_shader_property.hair_tint_color.r
                b_mat.diffuse_color.g = bs_shader_property.hair_tint_color.g
                b_mat.diffuse_color.b = bs_shader_property.hair_tint_color.b
                b_mat.diffuse_intensity = 1.0

            # Emissive
            b_mat.niftools.emissive_color.r = bs_shader_property.emissive_color.r
            b_mat.niftools.emissive_color.g = bs_shader_property.emissive_color.g
            b_mat.niftools.emissive_color.b = bs_shader_property.emissive_color.b
            b_mat.emit = bs_shader_property.emissive_multiple

            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha(b_mat, bs_shader_property, n_alpha_prop)

            # gloss
            b_mat.specular_hardness = bs_shader_property.glossiness

            # Specular color
            b_mat.specular_color.r = bs_shader_property.specular_color.r
            b_mat.specular_color.g = bs_shader_property.specular_color.g
            b_mat.specular_color.b = bs_shader_property.specular_color.b
            b_mat.specular_intensity = bs_shader_property.specular_strength

            # lighting effect
            b_mat.niftools.lightingeffect1 = bs_shader_property.lighting_effect_1
            b_mat.niftools.lightingeffect2 = bs_shader_property.lighting_effect_2

        if n_mat_prop is None and bs_effect_shader_property:
            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha(b_mat, bs_shader_property, n_alpha_prop)

            if bs_effect_shader_property.emissive_color:
                b_mat.niftools.emissive_color.r = bs_effect_shader_property.emissive_color.r
                b_mat.niftools.emissive_color.g = bs_effect_shader_property.emissive_color.g
                b_mat.niftools.emissive_color.b = bs_effect_shader_property.emissive_color.b
                b_mat.niftools.emissive_alpha = bs_effect_shader_property.emissive_color.a
                b_mat.emit = bs_effect_shader_property.emissive_multiple
            b_mat.niftools_alpha.textureflag = bs_effect_shader_property.controller.flags

        # check wireframe property
        if n_wire_prop:
            # enable wireframe rendering
            b_mat.type = 'WIRE'

        self.nif_import.dict_materials[material_hash] = b_mat
        return b_mat
