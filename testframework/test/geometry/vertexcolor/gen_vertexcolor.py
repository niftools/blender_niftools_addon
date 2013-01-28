from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_add_vertex_colors(n_nitrishapedata):
    
           
    n_nitrishapedata.has_vertex_colors = True
    n_nitrishapedata.vertex_colors.update_size()
    with ref(n_nitrishapedata.vertex_colors[0]) as n_color4:
        n_color4.r = 1
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[1]) as n_color4:
        n_color4.b = 1
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[2]) as n_color4:
        n_color4.g = 1
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[3]) as n_color4:
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[4]) as n_color4:
        n_color4.r = 1
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[5]) as n_color4:
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[6]) as n_color4:
        n_color4.g = 1
        n_color4.a = 1
    with ref(n_nitrishapedata.vertex_colors[7]) as n_color4:
        n_color4.b = 1
        n_color4.a = 1
    return n_nitrishapedata