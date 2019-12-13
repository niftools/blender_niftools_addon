"""This script contains helper methods to import shader property data."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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


class BSShader:

    @staticmethod
    def import_shader_types(b_obj, b_prop):
        if isinstance(b_prop, NifFormat.BSShaderPPLightingProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSShaderPPLightingProperty'
            sf_type = NifFormat.BSShaderType._enumvalues.index(b_prop.shader_type)
            b_obj.niftools_shader.bsspplp_shaderobjtype = NifFormat.BSShaderType._enumkeys[sf_type]
            for b_flag_name in b_prop.shader_flags._names:
                sf_index = b_prop.shader_flags._names.index(b_flag_name)
                if b_prop.shader_flags._items[sf_index]._value == 1:
                    b_obj.niftools_shader[b_flag_name] = True

        if isinstance(b_prop, NifFormat.BSLightingShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSLightingShaderProperty'
            sf_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues.index(b_prop.skyrim_shader_type)
            b_obj.niftools_shader.bslsp_shaderobjtype = NifFormat.BSLightingShaderPropertyShaderType._enumkeys[sf_type]
            BSShader.import_shader_flags(b_obj, b_prop)

        elif isinstance(b_prop, NifFormat.BSEffectShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSEffectShaderProperty'
            b_obj.niftools_shader.bslsp_shaderobjtype = 'Default'
            BSShader.import_shader_flags(b_obj, b_prop)

    @staticmethod
    def import_shader_flags(b_obj, b_prop):
        for b_flag_name_1 in b_prop.shader_flags_1._names:
            sf_index = b_prop.shader_flags_1._names.index(b_flag_name_1)
            if b_prop.shader_flags_1._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_1] = True
        for b_flag_name_2 in b_prop.shader_flags_2._names:
            sf_index = b_prop.shader_flags_2._names.index(b_flag_name_2)
            if b_prop.shader_flags_2._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_2] = True
