# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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
from os import path

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create_bump_map_property(n_nitexturingproperty):
    """Adds a bumpmap texture to a NiTexturingProperty"""
    
    n_nitexturingproperty.has_bump_map_texture = True
    n_nitexturingproperty.bump_map_luma_scale = 1.0
    n_nitexturingproperty.bump_map_luma_offset = 0.0
    n_nitexturingproperty.bump_map_matrix.m_11 = 1.0
    n_nitexturingproperty.bump_map_matrix.m_12 = 0.0
    n_nitexturingproperty.bump_map_matrix.m_21 = 0.0
    n_nitexturingproperty.bump_map_matrix.m_22 = 1.0
    
    n_nisourcetexture = NifFormat.NiSourceTexture()  
    
    file_path = 'textures' + path.sep + 'bump' + path.sep + 'bump.dds'
    n_nisourcetexture.file_name = file_path.encode()
    n_nisourcetexture.pixel_layout = NifFormat.PixelLayout.PIX_LAY_DEFAULT # 6
    n_nisourcetexture.use_mipmaps = 1
    
    with ref(n_nitexturingproperty.bump_map_texture) as n_texdesc:
        n_texdesc.source = n_nisourcetexture
    
        
def n_check_bumpmap_property(n_tex_prop):
    '''Checks the bump settings for the NiTextureProperty'''
    
    nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
    nose.tools.assert_equal(n_tex_prop.has_bump_map_texture, True)
    nose.tools.assert_equal(n_tex_prop.bump_map_luma_scale, 1.0)
    nose.tools.assert_equal(n_tex_prop.bump_map_luma_offset, 0.0)
    nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_11, 1.0)
    nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_12, 0.0)
    nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_21, 0.0)
    nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_22, 1.0)
    
    
def n_check_bumpmap_source_texture(n_nisourcetexture, n_texture_path):
    '''Checks the settings of the source bump texture'''
    
    nose.tools.assert_is_instance(n_nisourcetexture, NifFormat.NiSourceTexture)
    
    n_split_path = n_texture_path.split(path.sep)
    n_rel_path = n_split_path[len(n_split_path)-3:] #get a path relative to \\textures folder
    
    n_src_path = n_nisourcetexture.file_name.decode()
    n_src_path = n_src_path.split(path.sep)

    nose.tools.assert_equal(n_src_path, n_rel_path)
    nose.tools.assert_equal(n_nisourcetexture.pixel_layout, NifFormat.PixelLayout.PIX_LAY_DEFAULT) # 6
    # TODO - check if this setting is correct
    # nose.tools.assert_equal(n_nisourcetexture.pixel_layout, NifFormat.PixelLayout.PIX_LAY_BUMPMAP) # 4
    nose.tools.assert_equal(n_nisourcetexture.use_mipmaps, NifFormat.MipMapFormat.MIP_FMT_YES) # 1
    nose.tools.assert_equal(n_nisourcetexture.use_external, 1)
    
    