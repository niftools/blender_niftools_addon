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

from io_scene_nif.modules.nif_export.animation.texture import TextureAnimation
from io_scene_nif.modules.nif_export.property import texture
from io_scene_nif.modules.nif_export.property.texture.writer import TextureWriter
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_logging import NifLog


class TextureSlotManager:

    def __init__(self):
        self.dict_mesh_uvlayers = []
        self.texture_writer = TextureWriter()
        self.texture_anim = TextureAnimation()

        self.base_mtex = None
        self.glow_mtex = None
        self.bump_mtex = None
        self.normal_mtex = None
        self.gloss_mtex = None
        self.dark_mtex = None
        self.detail_mtex = None
        self.ref_mtex = None

    @staticmethod
    def get_used_textslots(b_mat):
        used_slots = []
        if b_mat is not None:
            used_slots = [b_texslot for b_texslot in b_mat.texture_slots if b_texslot is not None and b_texslot.use]
        return used_slots

    @staticmethod
    def get_uv_layers(b_mat):
        used_uvlayers = set()
        texture_slots = TextureSlotManager.get_used_textslots(b_mat)
        for slot in texture_slots:
            used_uvlayers.add(slot.uv_layer)
        return used_uvlayers

    def determine_texture_types(self, b_mat):

        used_slots = self.get_used_textslots(b_mat)
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
                    raise util_math.NifError("Non-COL-mapped reflection texture in mesh '%s', material '%s', these cannot be exported to NIF.\n"
                                             "Either delete all non-COL-mapped reflection textures, or in the Shading Panel, under Material Buttons, set texture 'Map To' to 'COL'." % (b_mat.name, b_mat.name))
                if b_mat_texslot.blend_type != 'ADD':
                    # it should have "ADD" blending mode
                    NifLog.warn("Reflection texture should have blending mode 'Add' on texture in mesh '{0}', material '{1}').".format(b_mat.name, b_mat.name))
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
                        raise util_math.NifError("Multiple emissive textures in mesh '{0}', material '{1}''.\n"
                                                 "Make sure there is only one texture set as Influence > emit".format(b_mat.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    self.glow_mtex = b_mat_texslot

                # specular
                elif b_mat_texslot.use_map_specular or b_mat_texslot.use_map_color_spec:
                    # multi-check
                    if self.gloss_mtex:
                        raise util_math.NifError("Multiple specular gloss textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > specular".format(b_mat.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    # got the gloss map
                    self.gloss_mtex = b_mat_texslot

                # bump map
                elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map is False:
                    # multi-check
                    if self.bump_mtex:
                        raise util_math.NifError("Multiple bump/normal texture in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".format(b_mat.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True

                    self.bump_mtex = b_mat_texslot

                # normal map
                elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map:
                    # multi-check
                    if self.normal_mtex:
                        raise util_math.NifError("Multiple bump/normal textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > normal".format(b_mat.name, b_mat.name))
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.normal_mtex = b_mat_texslot

                # darken
                elif b_mat_texslot.use_map_color_diffuse and b_mat_texslot.blend_type == 'DARKEN':

                    if self.dark_mtex:
                        raise util_math.NifError("Multiple Darken textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Blend Type > Dark".format(b_mat.name, b_mat.name))

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    # got the dark map
                    self.dark_mtex = b_mat_texslot

                # diffuse
                elif b_mat_texslot.use_map_color_diffuse:
                    if self.base_mtex:
                        raise util_math.NifError("Multiple Diffuse textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture with Influence > Diffuse > color".format(b_mat.name, b_mat.name))

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
                        raise util_math.NifError("Multiple detail textures in mesh '{0}', material '{1}'.\n" 
                                                 "Make sure there is only one texture with Influence Diffuse > color".format(b_mat.name, b_mat.name))
                    # extra diffuse consider as detail texture

                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.detail_mtex = b_mat_texslot

                # reflection
                elif b_mat_texslot.use_map_mirror or b_mat_texslot.use_map_raymir:
                    # multi-check
                    if self.ref_mtex:
                        raise util_math.NifError("Multiple reflection textures in mesh '{0}', material '{1}'.\n"
                                                 "Make sure there is only one texture set as Influence > Mirror/Ray Mirror".format(b_mat.name, b_mat.name))
                    # got the reflection map
                    # check if alpha channel is enabled for this texture
                    if b_mat_texslot.use_map_alpha:
                        mesh_hasalpha = True
                    self.ref_mtex = b_mat_texslot

                # unsupported map
                else:
                    raise util_math.NifError("Do not know how to export texture '{0}', in mesh '{1}', material '{2}'.\n"
                                             "Either delete it, or if this texture is to be your base texture.\n"
                                             "Go to the Shading Panel Material Buttons, and set texture 'Map To' to 'COL'.".format(b_mat_texslot.texture.name, b_mat.name, b_mat.name))

            # nif only support UV-mapped textures
            else:
                NifLog.warn("Non-UV texture in mesh '{0}', material '{1}'.\nEither delete all non-UV textures or "
                            "create a UV map for every texture associated with selected object and run the script again.".format(b_mat.name, b_mat.name))

    def has_diffuse_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.diffusetextures

        for b_mat_texslot in self.get_used_textslots(b_mat):
            if b_mat_texslot.use_map_color_diffuse:
                self.diffusetextures.append(b_mat_texslot)
        return self.diffusetextures

    def has_glow_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.glowtextures

        for b_mat_texslot in self.get_used_textslots(b_mat):
            if b_mat_texslot.use_map_emit:
                self.glowtextures.append(b_mat_texslot)
        return self.glowtextures

    def has_bumpmap_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.bumpmaptextures

        for b_mat_texslot in self.get_used_textslots(b_mat):
            if b_mat_texslot.texture.use_normal_map is False and b_mat_texslot.use_map_color_diffuse is False:
                self.bumpmaptextures.append(b_mat_texslot)
        return self.bumpmaptextures

    def has_gloss_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.glosstextures

        for b_mat_texslot in self.get_used_textslots(b_mat):
            if b_mat_texslot.use_map_color_spec:
                self.glosstextures.append(b_mat_texslot)
        return self.glosstextures

    def has_normalmap_textures(self, b_mat):
        if self.b_mat == b_mat:
            return self.normalmaptextures

        for b_mat_texslot in self.get_used_textslots(b_mat):
            if b_mat_texslot.use_map_color_diffuse is False and b_mat_texslot.texture.use_normal_map and b_mat_texslot.use_map_normal:
                self.normalmaptextures.append(b_mat_texslot)
        return self.normalmaptextures
