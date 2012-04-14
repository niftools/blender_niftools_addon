"""Import and export collision data"""

import bpy
import nose.tools

from test.test_geom import TestBaseGeom
from pyffi.formats.nif import NifFormat

class TestBhkCollision():
    ''' Helper class with common features of Collision Tree'''

    def n_check_bsxflags_property(self, n_data):
        nose.tools.assert_is_instance(n_data, NifFormat.BSXFlags)
        nose.tools.assert_equal(n_data.integer_data, 2) #enable collision flag
    
    #user property buffer
    def n_check_upb_property(self, n_data):
        nose.tools.assert_is_instance(n_data, NifFormat.NiStringExtraData)
        nose.tools.assert_equal(n_data.name, 'UPB')
        
        valuestring = n_data.string_data
        #check the string's values.
        #should these values correspond to the values in rigidbody?
        
    
    def n_check_bhkcollisionobject_data(self, n_data):
        nose.assert_is_instance(n_data, NifFormat.bhkCollisionObject)
        nose.assert_equal(n_data.flags, 1)# what do these mean?
        
        
    def n_check_bhkrigidbody_data(self, n_data):
        #add code to test lots of lovely things
        pass
            
    def n_check_bhkrighidbodyt_data(self, n_data):
        #this is inherited from bhkrigidbody, but what is the difference?
        pass

class TestBhkCollisionBoxShape(TestGeom, TestBhkCollision):
    n_name = "collision/base_bhkcollision_box" #name of nif
    b_name = "Cube" #name of blender mesh object
    
    def b_create_object(self):
        b_obj = TestBaseGeom.b_create_object(self)
        #mimic how the user would create the shape 
    	#TODO - create common setup using shared class
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
    	return b_obj 

    def b_check_object(self, b_obj):
    	TestBaseGeom.b_check_data(self, b_obj)# we double check the base mesh
        
        
    	self.b_check_collision_data(b_obj)

    def b_check_collision_data(self, b_obj):
        #here we check our blender collision data
        pass

    def n_check_data(self, n_data):
        n_ninode = n_data.roots
        nose.tools.assert_is_instance(n_ninode, NifFormat.NiNode)
        #check that we have the other blocks
        
        self.n_check_bsxflags_property(n_data.extra_data[0])
        self.n_check_upb_property(n_ninode.extra_data[1])
        pass

    def n_check_bhkboxshape_data(self, data):
        #Check specific block data
        pass

'''
Use above as template for the rest.

class TestBhkCollisionSphereShape(TestGeom, TestBhkCollision):

class TestBhkCollisionCapsule(TestGeom, TestBhkCollision):
'''