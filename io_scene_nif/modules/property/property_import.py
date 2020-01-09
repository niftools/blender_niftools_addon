"""This script contains classes to help import properties."""

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

from functools import singledispatch

import bpy

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.animation.material_import import MaterialAnimation
from io_scene_nif.modules.property import texture
from io_scene_nif.modules.property.material.material_import import Material
from io_scene_nif.modules.property.shader.shader_import import BSShader
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifData
from io_scene_nif.utility.util_logging import NifLog


class Property:

    def __init__(self, materialhelper):
        self.materialhelper = materialhelper
        self.material_anim = MaterialAnimation()

    # TODO [property] This will be moved to dispatch method later
    @staticmethod
    def import_stencil_property(b_mesh, b_obj):
        """ Imports a NiStencilProperty attached to n_mesh """
        # Stencil (for double sided meshes)
        n_stencil_prop = nif_utils.find_property(b_obj, NifFormat.NiStencilProperty)
        # we don't check flags for now, nothing fancy
        if n_stencil_prop:
            b_mesh.show_double_sided = True
        else:
            b_mesh.show_double_sided = False

    def import_shader_property(self, b_obj, n_block):
        if n_block.properties:
            for b_prop in n_block.properties:
                BSShader.import_shader_types(b_obj, b_prop)
        elif n_block.bs_properties:
            for b_prop in n_block.bs_properties:
                BSShader.import_shader_types(b_obj, b_prop)

    def process_properties(self, b_obj, n_block):
        # Material
        # note that NIF files only support one material for each trishape
        # find material property

        self.import_stencil_property(n_block, b_obj)
        # self.import_shader_property(n_block, b_obj)
        return self.process_material(n_block, b_obj)

    def process_material(self, n_block, b_mesh):

        material = None
        material_index = 0

        n_mat_prop = nif_utils.find_property(n_block, NifFormat.NiMaterialProperty)

        n_effect_shader_prop = nif_utils.find_property(n_block, NifFormat.BSEffectShaderProperty)

        # Alpha
        n_alpha_prop = nif_utils.find_property(n_block, NifFormat.NiAlphaProperty)

        # Specularity
        n_specular_prop = nif_utils.find_property(n_block, NifFormat.NiSpecularProperty)

        # Wireframe
        n_wire_prop = nif_utils.find_property(n_block, NifFormat.NiWireframeProperty)

        # Texture
        n_texture_prop = nif_utils.find_property(n_block, NifFormat.NiTexturingProperty)

        if n_mat_prop or n_effect_shader_prop:  # TODO [shader] or bs_shader_property or bs_effect_shader_property:

            # extra datas (for sid meier's railroads) that have material info
            extra_datas = []
            for extra in n_block.get_extra_datas():
                if isinstance(extra, NifFormat.NiIntegerExtraData):
                    if extra.name in texture.EXTRA_SHADER_TEXTURES:
                        # yes, it describes the shader slot number
                        extra_datas.append(extra)

            # texturing effect for environment map in official files this is activated by a NiTextureEffect child
            # preceeding the n_block
            textureEffect = None
            if isinstance(n_block._parent, NifFormat.NiNode):
                lastchild = None
                for child in n_block._parent.children:
                    if child is n_block:
                        if isinstance(lastchild, NifFormat.NiTextureEffect):
                            textureEffect = lastchild
                        break
                    lastchild = child
                else:
                    raise RuntimeError("texture effect scanning bug")
                # in some mods the NiTextureEffect child follows the n_block
                # but it still works because it is listed in the effect list
                # so handle this case separately
                if not textureEffect:
                    for effect in n_block._parent.effects:
                        if isinstance(effect, NifFormat.NiTextureEffect):
                            textureEffect = effect
                            break

            # create material and assign it to the mesh
            # TODO [material] delegate search for properties to import_material
            if n_mat_prop:
                material = self.materialhelper.import_material(n_mat_prop, n_texture_prop, n_alpha_prop, n_specular_prop,
                                                               textureEffect, n_wire_prop, extra_datas)
            # TODO [property] Extract to shader import
            # if bs_shader_property or bs_effect_shader_property:
            #     material = self.materialhelper.import_bsshader_material(bs_shader_property, bs_effect_shader_property, n_alpha_prop)

            # TODO [animation][material] merge this call into import_material
            self.material_anim.import_material_controllers(material, n_block)

            b_mesh_materials = list(b_mesh.materials)
            try:
                material_index = b_mesh_materials.index(material)
            except ValueError:
                material_index = len(b_mesh_materials)
                b_mesh.materials.append(material)

            '''
            # if mesh has one material with n_wire_prop, then make the mesh wire in 3D view
            if n_wire_prop:
                b_obj.draw_type = 'WIRE'
            '''
        return material, material_index


class MeshProperty:

    def __init__(self):
        self.b_mesh = None
        self.n_block = None
        self.process_property = singledispatch(self.process_property)
        self.process_property.register(NifFormat.NiStencilProperty, self.process_nistencil_property)
        self.process_property.register(NifFormat.NiSpecularProperty, self.process_nispecular_property)
        self.process_property.register(NifFormat.NiWireframeProperty, self.process_niwireframe_property)
        self.process_property.register(NifFormat.NiMaterialProperty, self.process_nimaterial_property)
        self.process_property.register(NifFormat.NiAlphaProperty, self.process_nialphs_property)
        self.process_property.register(NifFormat.NiTexturingProperty, self.process_nitexturing_property)
        self.process_property.register(NifFormat.NiVertexColorProperty, self.process_nivertexcolor_property)

    def process_property_list(self, n_block, b_mesh):
        self.n_block = n_block
        self.b_mesh = b_mesh
        for prop in n_block.properties:
            NifLog.debug("About to process" + str(type(prop)))
            self.process_property(prop)
        return

    def process_property(self, prop):
        """Base method to warn user that this property is not supported"""
        NifLog.warn("Unknown property block found : " + str(prop.name))
        NifLog.warn("This type isn't currently supported: {}".format(type(prop)))

    def process_nistencil_property(self, prop):
        """Stencil (for double sided meshes"""
        NifLog.debug("NiStencilProperty property found " + str(prop))
        self.b_mesh.show_double_sided = True  # We don't check flags for now, nothing fancy

    def process_nispecular_property(self, prop):
        """SpecularProperty based specular"""
        NifLog.debug("NiSpecularProperty property found " + str(prop))
        b_mat = self._find_or_create_material()

        # TODO [material][property]
        if NifData.data.version == 0x14000004:
            b_mat.specular_intensity = 0.0  # no specular prop

    def process_nialphs_property(self, prop):
        """Import a NiAlphaProperty based material"""
        NifLog.debug("NiAlphaProperty property found " + str(prop))
        b_mat = self._find_or_create_material()
        Material.set_alpha(b_mat, prop)

    def process_nimaterial_property(self, prop):
        """Import a NiMaterialProperty based material"""
        NifLog.debug("NiMaterialProperty property found " + str(prop))
        b_mat = self._find_or_create_material()
        # todo [material] import
        # Material().import_material(self.n_block, b_mat, prop)

    def process_nitexturing_property(self, prop):
        """Import a NiTexturingProperty based material"""
        NifLog.debug("NiTexturingProperty property found " + str(prop))
        b_mat = self._find_or_create_material()
        # NiTextureProp.get().import_nitextureprop_textures(self.n_block, b_mat, prop)

    def process_niwireframe_property(self, prop):
        """Material based specular"""
        NifLog.debug("NiWireframeProperty found " + str(prop))
        b_mat = self._find_or_create_material()
        b_mat.type = 'WIRE'

    def process_nivertexcolor_property(self, prop):
        """Material based specular"""
        NifLog.debug("NiVertexColorProperty found " + str(prop))
        b_mat = self._find_or_create_material()
        # TODO [property][mesh] Use the vertex color modes

    def _find_or_create_material(self):
        b_mats = self.b_mesh.materials
        if len(b_mats) == 0:
            # assign to 1st material slot
            NifLog.debug("Creating placeholder material to store properties in")
            b_mat = bpy.data.materials.new("")
            self.b_mesh.materials.append(b_mat)
        else:
            NifLog.debug("Reusing existing material to store additional properties in")
            b_mat = self.b_mesh.materials[0]
        return b_mat
