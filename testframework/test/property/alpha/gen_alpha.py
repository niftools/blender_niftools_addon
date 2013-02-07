from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_alpha_prop(n_trishapedata):
    '''Attaches a NiMaterialProperty to a trishapedata block property's array at pos[0]'''
    
    n_alphaprop = NifFormat.NiAlphaProperty()
    n_alphaprop.flags = 4845 # default = 237
    
    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_alphaprop

    n_trishapedata.properties.reverse()
    
    
    
def n_alter_material_alpha(n_nimaterialprop):
    n_nimaterialprop.alpha = 0.5
    return n_nimaterialprop