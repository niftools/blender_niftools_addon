import mathutils



def import_matrix(self, niBlock, relative_to=None):
    """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
    # return Matrix(*niBlock.get_transform(relative_to).as_list())
    n_scale, n_rot_mat3, n_loc_vec3 = niBlock.get_transform(relative_to).get_scale_rotation_translation()

    # create a location matrix
    b_loc_vec = mathutils.Vector(n_loc_vec3.as_tuple())
    b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)
    
    # create a scale matrix
    b_scale_mat = mathutils.Matrix.Scale(n_scale, 4)

    # create a rotation matrix
    b_rot_mat = mathutils.Matrix()
    b_rot_mat[0].xyz = n_rot_mat3.m_11, n_rot_mat3.m_12, n_rot_mat3.m_13
    b_rot_mat[1].xyz = n_rot_mat3.m_21, n_rot_mat3.m_22, n_rot_mat3.m_23
    b_rot_mat[2].xyz = n_rot_mat3.m_31, n_rot_mat3.m_32, n_rot_mat3.m_33
    
    b_import_matrix = (b_loc_vec * b_rot_mat) * b_scale_mat
    return b_import_matrix
