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
    
    