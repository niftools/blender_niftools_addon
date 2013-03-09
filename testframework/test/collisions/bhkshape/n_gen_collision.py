
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