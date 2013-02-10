import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_specular_prop(n_trishapedata):
    '''Attaches a NiSpecularProperty to a trishapedata block property's array at pos[0]'''
    
    n_nispecularprop = NifFormat.NiSpecularProperty()
    n_nispecularprop.flags = 0x1
    
    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_nispecularprop

    n_trishapedata.properties.reverse()
    
def n_alter_material_specular(n_nimaterialprop):
    with ref(n_nimaterialprop.specular_color) as n_color3:
        n_color3.r = 0.5
        n_color3.g = 0.0
        n_color3.b = 0.0
        
def n_check_material_specular(n_mat_prop):
    nose.tools.assert_equal((n_mat_prop.specular_color.r,
                             n_mat_prop.specular_color.g,
                             n_mat_prop.specular_color.b),
                             (0.5,0.0,0.0))
    
def n_check_specular_block(n_mat_prop):
    nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiSpecularProperty)

def n_check_specular_property(n_specular_prop):
    nose.tools.assert_equal(n_specular_prop.flags, 0x1)
