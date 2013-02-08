from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_alpha_prop(n_trishapedata):
    '''Attaches a NiMaterialProperty to a trishapedata block property's array at pos[0]'''
    
    n_alphaprop = NifFormat.NiAlphaProperty()
    n_alphaprop.flags = 4845 # default = 237, see below
    n_alphaprop.threshold = 0 # Threshold for alpha testing (see: glAlphaFunc)
    
    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_alphaprop

    n_trishapedata.properties.reverse()
    
def n_alter_material_alpha(n_nimaterialprop):
    n_nimaterialprop.alpha = 0.5

''' Alpha flags bit values - 

    Bit 0 : alpha blending 
    enableBits 1-4 : source blend (glBlendFunc)
    modeBits 5-8 : destination blend (glBlendFunc)
    modeBit 9 : alpha test 
    enableBit 10-12 : alpha test (glAlphaFunc)
    modeBit 13 : no sorter flag ( disables triangle sorting )
        
    blend modes (glBlendFunc):
        0000 GL_ONE
        0001 GL_ZERO
        0010 GL_SRC_COLOR
        0011 GL_ONE_MINUS_SRC_COLOR
        0100 GL_DST_COLOR
        0101 GL_ONE_MINUS_DST_COLOR
        0110 GL_SRC_ALPHA
        0111 GL_ONE_MINUS_SRC_ALPHA
        1000 GL_DST_ALPHA
        1001 GL_ONE_MINUS_DST_ALPHA
        1010 GL_SRC_ALPHA_SATURATE
        
   test modes (glAlphaFunc):
       000 GL_ALWAYS
       001 GL_LESS
       010 GL_EQUAL
       011 GL_LEQUAL
       100 GL_GREATER
       101 GL_NOTEQUAL
       110 GL_GEQUAL
       111 GL_NEVER
'''