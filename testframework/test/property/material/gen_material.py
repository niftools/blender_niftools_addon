from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_material_prop(n_trishapedata):
    '''Attaches a NiMaterialProperty to a trishapedata block property's array at pos[0]'''
    
    n_nimaterialprop = NifFormat.NiMaterialProperty()

    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_nimaterialprop

    n_trishapedata.properties.reverse()

    n_nimaterialprop.name = b'Material'
    with ref(n_nimaterialprop.ambient_color) as ambient_color:
        ambient_color.r = 1.0
        ambient_color.g = 1.0
        ambient_color.b = 1.0
    with ref(n_nimaterialprop.diffuse_color) as diffuse_color:
        diffuse_color.r = 1.0
        diffuse_color.g = 1.0
        diffuse_color.b = 1.0
    with ref(n_nimaterialprop.emissive_color) as emissive_color:
        emissive_color.r = 0.0
        emissive_color.g = 0.0
        emissive_color.b = 0.0
    with ref(n_nimaterialprop.specular_color) as specular_color:
        specular_color.r = 0.0
        specular_color.g = 0.0
        specular_color.b = 0.0
    
    n_nimaterialprop.glossiness = 12.5 # default nif.xml - 0.0, blender - 12.5
    n_nimaterialprop.alpha = 1.0 # default nif.xml - 0.0

    return n_trishapedata

def n_alter_glossiness(n_nimaterialprop):
    n_nimaterialprop.glossiness = 25.0
    return n_nimaterialprop

def n_alter_emissive(n_nimaterialprop):
    n_nimaterialprop.emissive_color.r = 0.5
    return n_nimaterialprop
