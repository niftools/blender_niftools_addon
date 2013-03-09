import nose
from os import path

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create_normal_map(n_nitexturingproperty):
    """Adds a diffuse texture to a NiTexturingProperty"""
    
    raise NotImplementedError

#    n_nitexturingproperty.has_base_texture = True
#    
#    n_nisourcetexture = NifFormat.NiSourceTexture()  
#    
#    file_path = 'textures' + path.sep + 'normal' + path.sep + 'normal.dds'
#    n_nisourcetexture.file_name = file_path.encode()
#    n_nisourcetexture.pixel_layout = NifFormat.PixelLayout.PIX_LAY_DEFAULT # 6
#    n_nisourcetexture.use_mipmaps = 1
#    
#    with ref(n_nitexturingproperty.base_texture) as n_texdesc:
#        n_texdesc.source = n_nisourcetexture
        
def n_check_normal_property(n_tex_prop):
    raise NotImplementedError
    
#    nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
#    nose.tools.assert_equal(n_tex_prop.has_base_texture, True)
    
def n_check_normal_source_texture(n_nisourcetexture, n_texture_path):
    raise NotImplementedError
    
#    nose.tools.assert_is_instance(n_nisourcetexture, NifFormat.NiSourceTexture)
#    
#    n_split_path = n_texture_path.split(path.sep)
#    n_rel_path = n_split_path[len(n_split_path)-3:] #get a path relative to \\textures folder
#    
#    n_src_path = n_nisourcetexture.file_name.decode()
#    n_src_path = n_src_path.split(path.sep)
#
#    nose.tools.assert_equal(n_src_path, n_rel_path)
#    nose.tools.assert_equal(n_nisourcetexture.pixel_layout, NifFormat.PixelLayout.PIX_LAY_DEFAULT) # 6
#    nose.tools.assert_equal(n_nisourcetexture.use_mipmaps, NifFormat.MipMapFormat.MIP_FMT_YES) # 1
#    nose.tools.assert_equal(n_nisourcetexture.use_external, 1)
    
    