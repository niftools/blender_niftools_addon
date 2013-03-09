"""Export and import meshes with material."""

import bpy
import nose.tools

def b_check_collision_data(self, b_col_obj):
    #We check if the collision settings have been added
    nose.tools.assert_equal(b_col_obj.game.use_collision_bounds, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.use_blender_properties, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.motion_system, "MO_SYS_FIXED")
    nose.tools.assert_equal(b_col_obj.nifcollision.oblivion_layer, "OL_STATIC")
    nose.tools.assert_equal(b_col_obj.nifcollision.col_filter, 0)
    nose.tools.assert_equal(b_col_obj.nifcollision.havok_material, "HAV_MAT_WOOD")
    
def n_check_bsxflags_property(self, n_data):
    #We check that there is a BSXFlags node. This is regarding collisions.
    #Without a BSXFlags, collisions will not work
    nose.tools.assert_is_instance(n_data, NifFormat.BSXFlags)
    nose.tools.assert_equal(n_data.integer_data, 2) #2 = enable collision flag

def n_check_upb_property(self, n_data, default = "Mass = 0.000000 Ellasticity = 0.300000 Friction = 0.300000 Unyielding = 0 Simulation_Geometry = 2 Proxy_Geometry = <None> Use_Display_Proxy = 0 Display_Children = 1 Disable_Collisions = 0 Inactive = 0 Display_Proxy = <None> "):
    #We check that there is an NiStringExtraData node and that its name is 'UPB'
    #'UPB' stands for 'User Property Buffer'
    nose.tools.assert_is_instance(n_data, NifFormat.NiStringExtraData)
    nose.tools.assert_equal(n_data.name, b'UPB')

    valuestring = n_data.string_data
    valuestring = valuestring.decode()
    valuestring = valuestring.replace("\r\n"," ")
    UPBString = default
    nose.tools.assert_equal(valuestring, UPBString)