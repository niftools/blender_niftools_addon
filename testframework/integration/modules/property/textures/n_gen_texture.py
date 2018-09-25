# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import nose
from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat


def n_create_blocks(n_data):
    n_ninode_1 = NifFormat.NiNode()
    n_nitrishape_1 = NifFormat.NiTriShape()
    n_nitrishapedata_1 = NifFormat.NiTriShapeData()
    n_data.roots = [n_ninode_1]

    with ref(n_ninode_1) as n_ninode:
        n_ninode.name = b'Scene Root'
        n_ninode.flags = 14
        n_ninode.num_children = 1
        n_ninode.children.update_size()
        n_ninode.children[0] = n_nitrishape_1
        
    with ref(n_nitrishape_1) as n_nitrishape:
        n_nitrishape.name = b'Cube'
        n_nitrishape.flags = 14
        
        with ref(n_nitrishape.translation) as n_vector3:
            n_vector3.x = 20
            n_vector3.y = 20
            n_vector3.z = 20
            
        with ref(n_nitrishape.rotation) as n_matrix33:
            n_matrix33.m_11 = -2.98023e-08
            n_matrix33.m_21 = -0.5
            n_matrix33.m_31 = 0.866025
            n_matrix33.m_12 = 0.866025
            n_matrix33.m_22 = -0.433013
            n_matrix33.m_32 = -0.25
            n_matrix33.m_13 = 0.5
            n_matrix33.m_23 = 0.75
            n_matrix33.m_33 = 0.433012
            
        n_nitrishape.scale = 0.75
        n_nitrishape.data = n_nitrishapedata_1 
    
    with ref(n_nitrishapedata_1) as n_nitrishapedata:
        n_nitrishapedata.num_vertices = 20
        n_nitrishapedata.vertices.update_size()
        with ref(n_nitrishapedata.vertices[0]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[1]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[2]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[3]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[4]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[5]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[6]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[7]) as n_vector3:
            n_vector3.x = 7.49999
            n_vector3.y = -3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[8]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[9]) as n_vector3:
            n_vector3.x = 7.49999
            n_vector3.y = -3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[10]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[11]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[12]) as n_vector3:
            n_vector3.x = 7.49999
            n_vector3.y = -3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[13]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[14]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[15]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[16]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[17]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[18]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[19]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = 3.5
            
        n_nitrishapedata.num_uv_sets = 1
        n_nitrishapedata.has_normals = True
        n_nitrishapedata.normals.update_size()
        with ref(n_nitrishapedata.normals[0]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = 0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[1]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[2]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[3]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = 0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[4]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = 0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[5]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = 0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[6]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = -0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[7]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[8]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = 0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[9]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[10]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[11]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[12]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = -0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[13]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[14]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = -0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[15]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = -0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[16]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = 0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.normals[17]) as n_vector3:
            n_vector3.x = 0.57735
            n_vector3.y = 0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[18]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = 0.57735
            n_vector3.z = -0.57735
        with ref(n_nitrishapedata.normals[19]) as n_vector3:
            n_vector3.x = -0.57735
            n_vector3.y = 0.57735
            n_vector3.z = 0.57735
        with ref(n_nitrishapedata.center) as n_vector3:
            n_vector3.x = 4.76837e-07
            n_vector3.y = 2.14577e-06
        
        n_nitrishapedata.radius = 11.1692
        
        n_nitrishapedata.uv_sets.update_size()
        with ref(n_nitrishapedata.uv_sets[0][0]) as n_texcoord:
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][1]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][2]) as n_texcoord:
            n_texcoord.u = 1
        with ref(n_nitrishapedata.uv_sets[0][4]) as n_texcoord:
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][5]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][6]) as n_texcoord:
            n_texcoord.u = 1
        with ref(n_nitrishapedata.uv_sets[0][8]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][9]) as n_texcoord:
            n_texcoord.u = 1
        with ref(n_nitrishapedata.uv_sets[0][11]) as n_texcoord:
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][12]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][14]) as n_texcoord:
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][15]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][16]) as n_texcoord:
            n_texcoord.u = 1
        with ref(n_nitrishapedata.uv_sets[0][17]) as n_texcoord:
            n_texcoord.u = 1
            n_texcoord.v = 1
        with ref(n_nitrishapedata.uv_sets[0][18]) as n_texcoord:
            n_texcoord.u = 1
            
        n_nitrishapedata.consistency_flags = NifFormat.ConsistencyType.CT_STATIC
        
        n_nitrishapedata.num_triangles = 12
        n_nitrishapedata.num_triangle_points = 36
        n_nitrishapedata.has_triangles = True
        n_nitrishapedata.triangles.update_size()
        with ref(n_nitrishapedata.triangles[0]) as n_triangle:
            n_triangle.v_2 = 1
            n_triangle.v_3 = 2
        with ref(n_nitrishapedata.triangles[1]) as n_triangle:
            n_triangle.v_2 = 2
            n_triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[2]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 5
            n_triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[3]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 6
            n_triangle.v_3 = 7
        with ref(n_nitrishapedata.triangles[4]) as n_triangle:
            n_triangle.v_2 = 8
            n_triangle.v_3 = 9
        with ref(n_nitrishapedata.triangles[5]) as n_triangle:
            n_triangle.v_2 = 9
            n_triangle.v_3 = 10
        with ref(n_nitrishapedata.triangles[6]) as n_triangle:
            n_triangle.v_1 = 11
            n_triangle.v_2 = 12
            n_triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[7]) as n_triangle:
            n_triangle.v_1 = 11
            n_triangle.v_2 = 6
            n_triangle.v_3 = 13
        with ref(n_nitrishapedata.triangles[8]) as n_triangle:
            n_triangle.v_1 = 14
            n_triangle.v_2 = 15
            n_triangle.v_3 = 16
        with ref(n_nitrishapedata.triangles[9]) as n_triangle:
            n_triangle.v_1 = 14
            n_triangle.v_2 = 16
            n_triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[10]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 17
            n_triangle.v_3 = 18
        with ref(n_nitrishapedata.triangles[11]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 18
            n_triangle.v_3 = 19
    return n_data


def n_create_texture_property(n_trishape):
    """Adds a NiTexturing Property at the top of the property list"""
    n_nitexturingproperty = NifFormat.NiTexturingProperty()
    
    # add property to top of list
    n_trishape.properties.reverse()
    n_trishape.num_properties += 1
    n_trishape.properties.update_size()
    n_trishape.properties[-1] = n_nitexturingproperty
    n_trishape.properties.reverse()


def n_create_store_normal_data(n_nitrishape):
    """Store normal data as BinaryExtraData"""
    n_nibinaryextradata_1 = NifFormat.NiBinaryExtraData()
    
    n_nitrishape.num_extra_data_list = 1
    n_nitrishape.extra_data_list.update_size()
    n_nitrishape.extra_data_list[0] = n_nibinaryextradata_1
    
    with ref(n_nibinaryextradata_1) as n_nibinaryextradata:
        n_nibinaryextradata.name = b'Tangent space (binormal & tangent vectors)'
        n_nibinaryextradata.binary_data = b'\xfb\x05\xd1>\xdc\x05\xd1>\xec\x05Q?\xaf\xd2H?\xf6\x9d\x16?\xe2\xd2H>\xb7\xa4O?\x15,\xf9\xbeY\x1d\xa6\xbe\xec\x05Q?\xda\x05\xd1>\xfd\x05\xd1\xbe\x89\xfe\xa6>\xc6f\xf8>\xa8\xb2O\xbf\xf2YC?\x00"\x05>q\x11"?\xb3\xb3O?\x90\x0f\xa7\xbe\xd5W\xf8>\x98L\x0f?\xfcnK?\x90\x89p>\x89\xfe\xa6>\xc6f\xf8>\xa8\xb2O\xbf\x98L\x0f?\xfcnK?\x90\x89p>\xaf\xd2H?\xf6\x9d\x16?\xe2\xd2H>\xaf\xd2H?\xf6\x9d\x16?\xe2\xd2H>\x98L\x0f?\xfcnK?\x90\x89p>\xb7\xa4O?\x15,\xf9\xbeY\x1d\xa6\xbe\xb7\xa4O?\x15,\xf9\xbeY\x1d\xa6\xbe\xb3\xb3O?\x90\x0f\xa7\xbe\xd5W\xf8>\xf2YC?\x00"\x05>q\x11"?\xfb\x05\xd1>\xdc\x05\xd1>\xec\x05Q?\xec\x05Q?\xda\x05\xd1>\xfd\x05\xd1\xbe\xf2YC?\x00"\x05>q\x11"?\xef\x045?\xf8\x045\xbf\xeec\x11\xb5\xb7\xe3g>~\xee\x10\xbfl\xe7J?.\xd0\xbf\xbd\x0e\xd6\'\xbf\x13\xd0??\xbc+\x1d\xb5\xf8\x045\xbf\xee\x045\xbf+\x9f?\xbf\x1c\x1f(?x\x00\xbc=B\xb5\x94\xbe2[N\xbf\x91\x00\x04?\xa4\xb6\xbb\xbdu\x9b??\xa0$(?\xc5+\x18\xbf\x9e\x0f@>\xad/H?+\x9f?\xbf\x1c\x1f(?x\x00\xbc=\xc5+\x18\xbf\x9e\x0f@>\xad/H?\xb7\xe3g>~\xee\x10\xbfl\xe7J?\xb7\xe3g>~\xee\x10\xbfl\xe7J?\xc5+\x18\xbf\x9e\x0f@>\xad/H?.\xd0\xbf\xbd\x0e\xd6\'\xbf\x13\xd0??.\xd0\xbf\xbd\x0e\xd6\'\xbf\x13\xd0??\xa4\xb6\xbb\xbdu\x9b??\xa0$(?B\xb5\x94\xbe2[N\xbf\x91\x00\x04?\xef\x045?\xf8\x045\xbf\xeec\x11\xb5\xbc+\x1d\xb5\xf8\x045\xbf\xee\x045\xbfB\xb5\x94\xbe2[N\xbf\x91\x00\x04?'


def n_check_texturing_property(n_tex_prop):
    nose.tools.assert_equal(n_tex_prop.apply_mode, NifFormat.ApplyMode.APPLY_MODULATE)  # 2
    # TODO check flags
    # TODO texture count


def n_check_texdesc(n_tex_desc):
    nose.tools.assert_equal(n_tex_desc.clamp_mode, 3)
    nose.tools.assert_equal(n_tex_desc.filter_mode, 2)
    nose.tools.assert_equal(n_tex_desc.uv_set, 0)
    nose.tools.assert_equal(n_tex_desc.has_texture_transform, False)
