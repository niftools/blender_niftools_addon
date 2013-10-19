import nose
from nose.tools import with_setup

import bpy

import io_scene_nif
from io_scene_nif.texturesys.texture_export import TextureHelper

class Test_TextureHelper_Used_Slots:    
        
    def setUp(self):
        self.b_mat = bpy.data.materials.new("test_material")
        self.used_textslots = []

    def tearDown(self):
        bpy.data.materials.remove(self.b_mat)
        del self.b_mat
     
     
    def test_empty_textureslots(self):
        self.used_textslots = TextureHelper.get_used_textslots(self, self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))
        
        nose.tools.assert_true(len(self.used_textslots) == 0)


    def test_single_used_textureslot(self):
        print("Adding textureslot")
        self.texture_slot0 = self.b_mat.texture_slots.add()
                   
        self.used_textslots = TextureHelper.get_used_textslots(self, self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))
        
        nose.tools.assert_true(len(self.used_textslots) == 1)
        
    def test_two_textures_one_used_textureslot(self):
        
        print("Adding textureslots: ")
        self.texture_slot0 = self.b_mat.texture_slots.add()
        self.texture_slot1 = self.b_mat.texture_slots.add()
        
        print("Not using second: ")
        self.texture_slot1.use = False
        
        self.used_textslots = TextureHelper.get_used_textslots(self, self.b_mat)
        
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))
        nose.tools.assert_true(len(self.used_textslots) == 1)