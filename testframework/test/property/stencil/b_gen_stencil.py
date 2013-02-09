import nose

def b_create_stensil_property(b_obj):
    b_obj.data.show_double_sided = True

def b_check_stencil_property(b_obj):
    nose.tools.assert_equal(b_obj.data.show_double_sided, True)