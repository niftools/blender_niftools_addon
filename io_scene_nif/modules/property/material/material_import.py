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
from io_scene_nif.modules.property.texture.texture_import import Texture
from io_scene_nif.utility.util_global import NifData
from io_scene_nif.utility.util_logging import NifLog


class Material:

    def __init__(self):
        self.dict_materials = {}
        self.texturehelper = Texture()

    def get_material_hash(self, n_mat_prop, n_texture_prop,
                          n_alpha_prop, n_specular_prop,
                          texture_effect, n_wire_prop,
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
                tuple(extra.get_hash() for extra in extra_datas))

    @staticmethod
    def set_alpha(b_mat, n_alpha_prop):
        NifLog.debug("Alpha prop detected")
        b_mat.use_transparency = True
        # TODO [property][material] map alpha material property value
        b_mat.transparency_method = 'Z_TRANSPARENCY'  # enable z-buffered transparency
        b_mat.offset_z = n_alpha_prop.threshold  # transparency threshold
        b_mat.niftools_alpha.alphaflag = n_alpha_prop.flags

        return b_mat

    def import_material(self, n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop, texture_effect, n_wire_prop, extra_datas):

        """Creates and returns a material."""
        # First check if material has been created before.
        material_hash = self.get_material_hash(n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop, texture_effect, n_wire_prop, extra_datas)
        try:
            return self.dict_materials[material_hash]
        except KeyError:
            pass

        # name unique material
        name = Object.import_name(n_mat_prop)
        if not name:
            name = bpy.context.scene.objects.active + "_nt_mat"
        b_mat = bpy.data.materials.new(name)

        # texures
        if n_texture_prop:
            self.texturehelper.import_nitextureprop_textures(b_mat, n_texture_prop)
            if extra_datas:
                self.texturehelper.import_texture_extra_shader(b_mat, n_texture_prop, extra_datas)
        if texture_effect:
            self.texturehelper.import_texture_effect(b_mat, texture_effect)

        # material based properties
        if n_mat_prop:
            # Ambient color
            self.import_material_ambient(b_mat, n_mat_prop)

            # Diffuse color
            self.import_material_diffuse(b_mat, n_mat_prop)

            # TODO [property][material] - Detect fallout 3+, use emit multi as a degree of emission
            #        test some values to find emission maximium. 0-1 -> 0-max_val
            # Should we factor in blender bounds 0.0 - 2.0

            # Emissive
            self.import_material_emissive(b_mat, n_mat_prop)

            # gloss
            b_mat.specular_hardness = n_mat_prop.glossiness

            # Alpha
            if n_alpha_prop:
                b_mat = self.set_alpha(b_mat, n_alpha_prop)

            # Specular color
            self.import_material_specular(b_mat, n_mat_prop)

            # todo [property][specular] Need to see what is actually required here
            if not n_specular_prop or NifData.data.version != 0x14000004:
                b_mat.specular_intensity = 0.0  # no specular prop
            else:
                b_mat.specular_intensity = 1.0  # Blender multiplies specular color with this value

        # check wireframe property
        if n_wire_prop:
            # enable wireframe rendering
            b_mat.type = 'WIRE'

        self.dict_materials[material_hash] = b_mat
        return b_mat

    def set_material_vertex_mapping(self, b_mesh, f_map, n_uvco):
        b_mat = b_mesh.materials[0]
        if b_mat:
            # fix up vertex colors depending on whether we had textures in the material
            mbasetex = self.texturehelper.has_base_texture(b_mat)
            mglowtex = self.texturehelper.has_glow_texture(b_mat)
            if b_mesh.vertex_colors:
                if mbasetex or mglowtex:
                    # textured material: vertex colors influence lighting
                    b_mat.use_vertex_color_light = True
                else:
                    # non-textured material: vertex colors influence color
                    b_mat.use_vertex_color_paint = True

            # if there's a base texture assigned to this material display it in Blender's 3D view, but only if there are UV coordinates
            if mbasetex and mbasetex.texture and n_uvco:
                image = mbasetex.texture.image
                if image:
                    for b_polyimage_index in f_map:
                        if b_polyimage_index is None:
                            continue
                        tface = b_mesh.uv_textures.active.data[b_polyimage_index]
                        tface.image = image

    @staticmethod
    def import_material_specular(b_mat, n_mat_prop):
        b_mat.specular_color.r = n_mat_prop.specular_color.r
        b_mat.specular_color.g = n_mat_prop.specular_color.g
        b_mat.specular_color.b = n_mat_prop.specular_color.b

    @staticmethod
    def import_material_emissive(b_mat, n_mat_prop):
        b_mat.niftools.emissive_color.r = n_mat_prop.emissive_color.r
        b_mat.niftools.emissive_color.g = n_mat_prop.emissive_color.g
        b_mat.niftools.emissive_color.b = n_mat_prop.emissive_color.b
        b_mat.emit = n_mat_prop.emit_multi

    @staticmethod
    def import_material_diffuse(b_mat, n_mat_prop):
        b_mat.diffuse_color.r = n_mat_prop.diffuse_color.r
        b_mat.diffuse_color.g = n_mat_prop.diffuse_color.g
        b_mat.diffuse_color.b = n_mat_prop.diffuse_color.b
        b_mat.diffuse_intensity = 1.0

    @staticmethod
    def import_material_ambient(b_mat, n_mat_prop):
        b_mat.niftools.ambient_color.r = n_mat_prop.ambient_color.r
        b_mat.niftools.ambient_color.g = n_mat_prop.ambient_color.g
        b_mat.niftools.ambient_color.b = n_mat_prop.ambient_color.b


class NiMaterial(Material):

    def import_material(self, n_block, b_mat, n_mat_prop):
        """Creates and returns a material."""
        # First check if material has been created before.
        # TODO [property][material] Decide whether or not to keep the material hash
        # material_hash = self.get_material_hash(n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop)
        # try:
        #     return material.DICT_MATERIALS[material_hash]
        # except KeyError:
        #     pass

        # update material material name
        name = Object.import_name(n_mat_prop)
        if name is None:
            name = (n_block.name.decode() + "_nt_mat")
        b_mat.name = name

        # Ambient color
        self.import_material_ambient(b_mat, n_mat_prop)

        # Diffuse color
        self.import_material_diffuse(b_mat, n_mat_prop)

        # TODO [property][material] Detect fallout 3+, use emit multi as a degree of emission
        # TODO [property][material] Test some values to find emission maximium. 0-1 -> 0-max_val
        # TODO [property][material] Should we factor in blender bounds 0.0 - 2.0

        # Emissive
        self.import_material_emissive(b_mat, n_mat_prop)

        # gloss
        b_mat.specular_hardness = n_mat_prop.glossiness

        # Specular color
        self.import_material_specular(b_mat, n_mat_prop)
        b_mat.specular_intensity = 1.0  # Blender multiplies specular color with this value

        return b_mat
