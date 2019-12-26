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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.property import texture
from io_scene_nif.utility import nif_utils


class Property:

    def __init__(self, materialhelper, animationhelper):
        self.bsShaderProperty1st = None
        self.materialhelper = materialhelper
        self.animationhelper = animationhelper

    # TODO [property] This will be moved to dispatch method later
    @staticmethod
    def import_stencil_property(n_mesh, b_mesh):
        """ Imports a NiStencilProperty attached to n_mesh """
        # Stencil (for double sided meshes)
        n_stencil_prop = nif_utils.find_property(n_mesh, NifFormat.NiStencilProperty)
        # we don't check flags for now, nothing fancy
        if n_stencil_prop:
            b_mesh.show_double_sided = True
        else:
            b_mesh.show_double_sided = False

    def process_properties(self, b_mesh, n_block):
        # Material
        # note that NIF files only support one material for each trishape
        # find material property

        self.import_stencil_property(n_block, b_mesh)

        material = None
        material_index = 0

        n_mat_prop = nif_utils.find_property(n_block, NifFormat.NiMaterialProperty)

        n_effect_shader_prop = nif_utils.find_property(n_block, NifFormat.BSEffectShaderProperty)

        bs_effect_shader_property = nif_utils.find_property(n_block, NifFormat.BSEffectShaderProperty)

        bs_shader_property = self.find_bsshaderproperty(n_block)

        # Alpha
        n_alpha_prop = nif_utils.find_property(n_block, NifFormat.NiAlphaProperty)

        # Specularity
        n_specular_prop = nif_utils.find_property(n_block, NifFormat.NiSpecularProperty)

        # Wireframe
        n_wire_prop = nif_utils.find_property(n_block, NifFormat.NiWireframeProperty)

        # Texture
        n_texture_prop = nif_utils.find_property(n_block, NifFormat.NiTexturingProperty)

        if n_mat_prop or n_effect_shader_prop or bs_shader_property or bs_effect_shader_property:

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
            if bs_shader_property or bs_effect_shader_property:
                material = self.materialhelper.import_bsshader_material(bs_shader_property, bs_effect_shader_property, n_alpha_prop)

            # TODO [animation][material] merge this call into import_material
            self.animationhelper.material.import_material_controllers(material, n_block)

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
