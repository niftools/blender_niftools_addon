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


"""
def process_material(self, n_block, b_mesh):

n_effect_shader_prop = nif_utils.find_property(n_block, NifFormat.BSEffectShaderProperty)

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
"""
