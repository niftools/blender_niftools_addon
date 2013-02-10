import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_wire_prop(n_trishapedata):
    '''Attaches a NiWireProperty to a trishapedata block property's array at pos[0]'''
    
    n_niwireframeprop = NifFormat.NiWireframeProperty()
    n_niwireframeprop.flags = 1
    
    # add property to top of list
    n_trishapedata.properties.reverse()
    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_niwireframeprop
    n_trishapedata.properties.reverse()

def n_check_wire_property(n_wire_prop):
    nose.tools.assert_is_instance(n_wire_prop, NifFormat.NiWireframeProperty)
    nose.tools.assert_equal(n_wire_prop.flags, 0x1)
