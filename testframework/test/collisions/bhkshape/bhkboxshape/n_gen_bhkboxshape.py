from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create_blocks(n_data):
#    n_ninode_1 = NifFormat.NiNode()
#    n_bsxflags_1 = NifFormat.BSXFlags()
#    n_nistringextradata_1 = NifFormat.NiStringExtraData()
#    n_bhkcollisionobject_1 = NifFormat.bhkCollisionObject()
#    n_bhkrigidbody_1 = NifFormat.bhkRigidBody()
#    n_bhkconvextransformshape_1 = NifFormat.bhkConvexTransformShape()
#    n_bhkboxshape_1 = NifFormat.bhkBoxShape()
#    n_nitrishape_1 = NifFormat.NiTriShape()
#    n_nitrishapedata_1 = NifFormat.NiTriShapeData()
#    n_data.roots = [n_ninode_1]
#
#    with ref(n_ninode_1) as n_ninode:
#        n_ninode.name = b'Scene Root'
#        n_ninode.num_extra_data_list = 2
#        n_ninode.extra_data_list.update_size()
#        n_ninode.extra_data_list[0] = n_bsxflags_1
#        n_ninode.extra_data_list[1] = n_nistringextradata_1
#        n_ninode.flags = 14
#        with ref(n_ninode.translation) as n_vector3:
#            n_vector3.x = 22.45
#            n_vector3.y = 12.96
#            n_vector3.z = -8.12
#        n_ninode.collision_object = n_bhkcollisionobject_1
#        n_ninode.num_children = 1
#        n_ninode.children.update_size()
#        n_ninode.children[0] = n_nitrishape_1
#    with ref(n_bsxflags_1) as n_bsxflags:
#        n_bsxflags.name = b'BSX'
#        n_bsxflags.integer_data = 2
#    with ref(n_nistringextradata_1) as n_nistringextradata:
#        n_nistringextradata.name = b'UPB'
#        n_nistringextradata.string_data = b'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
#    with ref(n_bhkcollisionobject_1) as n_bhkcollisionobject:
#        n_bhkcollisionobject.target = n_ninode_1
#        n_bhkcollisionobject.body = n_bhkrigidbody_1
#    with ref(n_bhkrigidbody_1) as n_bhkrigidbody:
#        n_bhkrigidbody.shape = n_bhkconvextransformshape_1
#        n_bhkrigidbody.unknown_int_2 = 2084020722
#        n_bhkrigidbody.unknown_3_ints.update_size()
#        n_bhkrigidbody.unknown_byte = 0
#        n_bhkrigidbody.unknown_2_shorts.update_size()
#        n_bhkrigidbody.unknown_2_shorts[0] = 35899
#        n_bhkrigidbody.unknown_2_shorts[1] = 16336
#        n_bhkrigidbody.unknown_7_shorts.update_size()
#        n_bhkrigidbody.unknown_7_shorts[1] = 21280
#        n_bhkrigidbody.unknown_7_shorts[2] = 4581
#        n_bhkrigidbody.unknown_7_shorts[3] = 62977
#        n_bhkrigidbody.unknown_7_shorts[4] = 65535
#        n_bhkrigidbody.unknown_7_shorts[5] = 44
#        with ref(n_bhkrigidbody.inertia) as n_inertiamatrix:
#            n_inertiamatrix.m_11 = 1.36054
#            n_inertiamatrix.m_12 = -7.10731e-08
#            n_inertiamatrix.m_13 = 1.9443e-07
#            n_inertiamatrix.m_21 = -7.10731e-08
#            n_inertiamatrix.m_22 = 1.36054
#            n_inertiamatrix.m_23 = -2.08093e-07
#            n_inertiamatrix.m_31 = 1.9443e-07
#            n_inertiamatrix.m_32 = -2.08093e-07
#            n_inertiamatrix.m_33 = 1.36055
#        n_bhkrigidbody.linear_damping = 0.1
#        n_bhkrigidbody.angular_damping = 0.05
#        n_bhkrigidbody.friction = 0.3
#        n_bhkrigidbody.restitution = 0.3
#        n_bhkrigidbody.max_angular_velocity = 31.4159
#        n_bhkrigidbody.penetration_depth = 0.15
#        n_bhkrigidbody.motion_system = 7
#    with ref(n_bhkconvextransformshape_1) as n_bhkconvextransformshape:
#        n_bhkconvextransformshape.shape = n_bhkboxshape_1
#        n_bhkconvextransformshape.material = 9
#        n_bhkconvextransformshape.unknown_float_1 = 0.1
#        n_bhkconvextransformshape.unknown_8_bytes.update_size()
#        n_bhkconvextransformshape.unknown_8_bytes[0] = 96
#        n_bhkconvextransformshape.unknown_8_bytes[1] = 120
#        n_bhkconvextransformshape.unknown_8_bytes[2] = 53
#        n_bhkconvextransformshape.unknown_8_bytes[3] = 19
#        n_bhkconvextransformshape.unknown_8_bytes[4] = 24
#        n_bhkconvextransformshape.unknown_8_bytes[5] = 9
#        n_bhkconvextransformshape.unknown_8_bytes[6] = 253
#        n_bhkconvextransformshape.unknown_8_bytes[7] = 4
#        with ref(n_bhkconvextransformshape.transform) as n_matrix44:
#            n_matrix44.m_11 = 0.931622
#            n_matrix44.m_21 = -0.123415
#            n_matrix44.m_31 = 0.341831
#            n_matrix44.m_12 = 0.237641
#            n_matrix44.m_22 = 0.918499
#            n_matrix44.m_32 = -0.316048
#            n_matrix44.m_13 = -0.274966
#            n_matrix44.m_23 = 0.37567
#            n_matrix44.m_33 = 0.885023
#    with ref(n_bhkboxshape_1) as n_bhkboxshape:
#        n_bhkboxshape.material = 9
#        n_bhkboxshape.radius = 0.1
#        n_bhkboxshape.unknown_8_bytes.update_size()
#        n_bhkboxshape.unknown_8_bytes[0] = 107
#        n_bhkboxshape.unknown_8_bytes[1] = 238
#        n_bhkboxshape.unknown_8_bytes[2] = 67
#        n_bhkboxshape.unknown_8_bytes[3] = 64
#        n_bhkboxshape.unknown_8_bytes[4] = 58
#        n_bhkboxshape.unknown_8_bytes[5] = 239
#        n_bhkboxshape.unknown_8_bytes[6] = 142
#        n_bhkboxshape.unknown_8_bytes[7] = 62
#        with ref(n_bhkboxshape.dimensions) as n_vector3:
#            n_vector3.x = 1.42857
#            n_vector3.y = 1.42857
#            n_vector3.z = 1.42857
#        n_bhkboxshape.minimum_size = 1.42857
#    with ref(n_nitrishape_1) as n_nitrishape:
#        n_nitrishape.name = b'Cube'
#        n_nitrishape.flags = 14
#        with ref(n_nitrishape.rotation) as n_matrix33:
#            n_matrix33.m_11 = 0.985069
#            n_matrix33.m_21 = -0.129862
#            n_matrix33.m_31 = -0.11303
#            n_matrix33.m_12 = 0.119638
#            n_matrix33.m_22 = 0.988453
#            n_matrix33.m_32 = -0.0929873
#            n_matrix33.m_13 = 0.1238
#            n_matrix33.m_23 = 0.0780762
#            n_matrix33.m_33 = 0.989231
#        n_nitrishape.scale = 1
#        n_nitrishape.data = n_nitrishapedata_1
#    with ref(n_nitrishapedata_1) as n_nitrishapedata:
#        n_nitrishapedata.num_vertices = 8
#        n_nitrishapedata.vertices.update_size()
#        with ref(n_nitrishapedata.vertices[0]) as n_vector3:
#            n_vector3.x = 10
#            n_vector3.y = 10
#            n_vector3.z = -10
#        with ref(n_nitrishapedata.vertices[1]) as n_vector3:
#            n_vector3.x = 10
#            n_vector3.y = -10
#            n_vector3.z = -10
#        with ref(n_nitrishapedata.vertices[2]) as n_vector3:
#            n_vector3.x = -10
#            n_vector3.y = -10
#            n_vector3.z = -10
#        with ref(n_nitrishapedata.vertices[3]) as n_vector3:
#            n_vector3.x = -10
#            n_vector3.y = 10
#            n_vector3.z = -10
#        with ref(n_nitrishapedata.vertices[4]) as n_vector3:
#            n_vector3.x = 10
#            n_vector3.y = 9.99999
#            n_vector3.z = 10
#        with ref(n_nitrishapedata.vertices[5]) as n_vector3:
#            n_vector3.x = -10
#            n_vector3.y = 10
#            n_vector3.z = 10
#        with ref(n_nitrishapedata.vertices[6]) as n_vector3:
#            n_vector3.x = -10
#            n_vector3.y = -10
#            n_vector3.z = 10
#        with ref(n_nitrishapedata.vertices[7]) as n_vector3:
#            n_vector3.x = 9.99999
#            n_vector3.y = -10
#            n_vector3.z = 10
#        with ref(n_nitrishapedata.center) as n_vector3:
#            n_vector3.x = 5.96046e-07
#            n_vector3.y = -1.19209e-06
#        n_nitrishapedata.radius = 17.3205
#        n_nitrishapedata.consistency_flags = 16384
#        n_nitrishapedata.num_triangles = 12
#        n_nitrishapedata.num_triangle_points = 36
#        n_nitrishapedata.has_triangles = True
#        n_nitrishapedata.triangles.update_size()
#        with ref(n_nitrishapedata.triangles[0]) as n_triangle:
#            n_triangle.v_2 = 1
#            n_triangle.v_3 = 2
#        with ref(n_nitrishapedata.triangles[1]) as n_triangle:
#            n_triangle.v_2 = 2
#            n_triangle.v_3 = 3
#        with ref(n_nitrishapedata.triangles[2]) as n_triangle:
#            n_triangle.v_1 = 4
#            n_triangle.v_2 = 5
#            n_triangle.v_3 = 6
#        with ref(n_nitrishapedata.triangles[3]) as n_triangle:
#            n_triangle.v_1 = 4
#            n_triangle.v_2 = 6
#            n_triangle.v_3 = 7
#        with ref(n_nitrishapedata.triangles[4]) as n_triangle:
#            n_triangle.v_2 = 4
#            n_triangle.v_3 = 7
#        with ref(n_nitrishapedata.triangles[5]) as n_triangle:
#            n_triangle.v_2 = 7
#            n_triangle.v_3 = 1
#        with ref(n_nitrishapedata.triangles[6]) as n_triangle:
#            n_triangle.v_1 = 1
#            n_triangle.v_2 = 7
#            n_triangle.v_3 = 6
#        with ref(n_nitrishapedata.triangles[7]) as n_triangle:
#            n_triangle.v_1 = 1
#            n_triangle.v_2 = 6
#            n_triangle.v_3 = 2
#        with ref(n_nitrishapedata.triangles[8]) as n_triangle:
#            n_triangle.v_1 = 2
#            n_triangle.v_2 = 6
#            n_triangle.v_3 = 5
#        with ref(n_nitrishapedata.triangles[9]) as n_triangle:
#            n_triangle.v_1 = 2
#            n_triangle.v_2 = 5
#            n_triangle.v_3 = 3
#        with ref(n_nitrishapedata.triangles[10]) as n_triangle:
#            n_triangle.v_1 = 4
#            n_triangle.v_3 = 3
#        with ref(n_nitrishapedata.triangles[11]) as n_triangle:
#            n_triangle.v_1 = 4
#            n_triangle.v_2 = 3
#            n_triangle.v_3 = 5
    return n_data

def n_check_bhkboxshape_data(data):
    nose.tools.assert_is_instance(data.body, NifFormat.bhkRigidBody);
    nose.tools.assert_is_instance(data.body.shape.shape, NifFormat.bhkBoxShape);
    nose.tools.assert_equal(data.body.shape.material, 9);
