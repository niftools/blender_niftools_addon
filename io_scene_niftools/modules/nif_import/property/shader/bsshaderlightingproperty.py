"""This script contains helper methods to import BSShaderLightingProperty based properties."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

from io_scene_niftools.modules.nif_import.property.shader import BSShader
from io_scene_niftools.modules.nif_import.property.texture.types.bsshadertexture import BSShaderTexture

"""
<niobject name="BSShaderLightingProperty" abstract="true" inherit="BSShaderProperty" module="BSMain" versions="#FO3#">Bethesda-specific property.
<niobject name="BSShaderNoLightingProperty" inherit="BSShaderLightingProperty" module="BSMain" versions="#FO3#">Bethesda-specific property.
<niobject name="BSShaderPPLightingProperty" inherit="BSShaderLightingProperty" module="BSMain" versions="#FO3#">Bethesda-specific property.
<niobject name="SkyShaderProperty" inherit="BSShaderLightingProperty" module="BSMain" versions="#BETHESDA#">Bethesda-specific property. Found in Fallout3
<niobject name="TileShaderProperty" inherit="BSShaderLightingProperty" module="BSMain" versions="#FO3#">Bethesda-specific property.
"""


class BSShaderLightingPropertyProcessor(BSShader):

    __instance = None

    def __init__(self):
        """ Virtually private constructor. """
        if BSShaderLightingPropertyProcessor.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            BSShaderLightingPropertyProcessor.__instance = self
            self.texturehelper = BSShaderTexture.get()

    @staticmethod
    def get():
        """ Static access method. """
        if not BSShaderLightingPropertyProcessor.__instance:
            BSShaderLightingPropertyProcessor()
        return BSShaderLightingPropertyProcessor.__instance

    def register(self, processor):
        processor.register(NifFormat.BSShaderPPLightingProperty, self.import_bs_shader_pp_lighting_property)

    def import_bs_shader_pp_lighting_property(self, bs_shader_prop):
        # Shader Flags
        b_shader = self._b_mat.niftools_shader
        b_shader.bs_shadertype = 'BSShaderPPLightingProperty'

        shader_type = NifFormat.BSShaderType._enumvalues.index(bs_shader_prop.shader_type)
        b_shader.bsspplp_shaderobjtype = NifFormat.BSShaderType._enumkeys[shader_type]

        flags = bs_shader_prop.shader_flags
        self.import_flags(self._b_mat, flags)
        self.texturehelper.import_bsshaderproperty_textureset(bs_shader_prop, self._nodes_wrapper)
