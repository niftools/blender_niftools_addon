from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat


def n_create_data():
    n_data = NifFormat.Data()
    n_data.version = 0x4000002
    n_create_blocks(n_data)
    return n_data

def n_create_blocks(n_data):
    n_ninode_1 = NifFormat.NiNode()
    n_ninode_2 = NifFormat.NiNode()
    n_data.roots = [n_ninode_1]

    with ref(n_ninode_1) as n_ninode:
        n_ninode.name = b'BBoxTest'
        n_ninode.flags = 12
        n_ninode.num_children = 1
        n_ninode.children.update_size()
        n_ninode.children[0] = n_ninode_2
    with ref(n_ninode_2) as n_ninode:
        n_ninode.name = b'Bounding Box'
        n_ninode.flags = 4
        n_ninode.has_bounding_box = True
        with ref(n_ninode.bounding_box) as n_boundingbox:
            with ref(n_boundingbox.radius) as n_vector3:
                n_vector3.x = 10
                n_vector3.y = 10
                n_vector3.z = 10
    return n_data
