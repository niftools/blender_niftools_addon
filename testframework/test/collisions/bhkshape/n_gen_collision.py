
def n_check_bhkcollisionobject_data(n_data):

    #check if n_ninode.collision_object is bhkCollisionObject, not None or other
    nose.assert_is_instance(n_data, NifFormat.bhkCollisionObject)
    #Most Objects collision data flags are 1
    nose.assert_equal(n_data.flags, 1)

def n_check_bhkrigidbody_data(n_data):
    #add code to test lots of lovely things
    pass

def n_check_bhkrighidbodyt_data(self, n_data):
    #this is inherited from bhkrigidbody, but what is the difference?
    pass

def n_check_data(self, n_data):
#    n_ninode = n_data.roots[0]
#    nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
#    #check that we have the other blocks

    #check to see that n_ninode.num_extra_data_list == 2, so we can execute the methods bellow
    nose.tools.assert_equal(n_ninode.num_extra_data_list,2)
    self.n_check_bsxflags_property(n_ninode.extra_data_list[0])
    self.n_check_upb_property(n_ninode.extra_data_list[1])
    
    
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