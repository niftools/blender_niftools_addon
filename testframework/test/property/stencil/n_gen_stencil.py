import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create_stencil_prop(n_trishapedata):
    n_nistencilproperty = NifFormat.NiStencilProperty()
    
    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_nistencilproperty
        
    n_trishapedata.properties.reverse()

def n_check_stencil_block(n_stencil_prop):
    '''Check that block is actually NiStencilProperty'''
    nose.tools.assert_is_instance(n_stencil_prop, NifFormat.NiStencilProperty)
    
def n_check_stencil_property(n_stencil_prop):
    '''Check NiStencilProperty values'''
    # nose.tools.assert_equal(n_alpha_prop.flags, 4845) # Ref: gen_alpha for values
    # nose.tools.assert_equal(n_alpha_prop.threshold, 0)