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

import nose
from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

from integration.modules.property.texture import n_gen_texture


def n_create_diffuse_map(n_nitexturingproperty, file_path):
    """Adds a diffuse texture to a NiTexturingProperty"""
    
    n_nitexturingproperty.has_base_texture = True
    n_nisourcetexture = n_gen_texture.n_create_base_nisourcetexture(file_path)
    
    with ref(n_nitexturingproperty.base_texture) as n_texdesc:
        n_texdesc.source = n_nisourcetexture
    
        
def n_check_diffuse_property(n_tex_prop):
    """Checks the diffuse settings for the NiTextureProperty"""
    
    nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
    nose.tools.assert_equal(n_tex_prop.has_base_texture, True)


def n_check_diffuse_source_texture(n_nisourcetexture, n_texture_path):
    """Checks the settings of the source diffuse texture"""

    n_gen_texture.n_check_source_texture(n_nisourcetexture, n_texture_path)
    nose.tools.assert_equal(n_nisourcetexture.pixel_layout, NifFormat.PixelLayout.PIX_LAY_DEFAULT)  # 6
    nose.tools.assert_equal(n_nisourcetexture.use_mipmaps, NifFormat.MipMapFormat.MIP_FMT_YES)  # 1
    nose.tools.assert_equal(n_nisourcetexture.use_external, 1)
