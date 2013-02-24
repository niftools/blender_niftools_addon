import nose

def b_create_wireframe_property(b_mat):
    b_mat.type = 'WIRE';
    
def b_check_wire_property(b_mat):
    nose.tools.assert_equal(b_mat.type, 'WIRE')