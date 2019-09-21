import nose

import bpy

from io_scene_nif.modules.property import texture


class TestMaterialSlot:

    def setup(self):
        self.b_mat = bpy.data.materials.new("test_material")
        self.used_textslots = []

    def teardown(self):
        bpy.data.materials.remove(self.b_mat)
        del self.b_mat

    def test_no_material(self):
        self.used_textslots = texture.get_used_textslots(None)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 0)

    def test_empty_textureslots(self):
        self.used_textslots = texture.get_used_textslots(self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 0)

    def test_single_used_textureslot(self):
        print("Adding textureslot")
        self.texture_slot0 = self.b_mat.texture_slots.add()

        self.used_textslots = texture.get_used_textslots(self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 1)

    def test_two_textures_one_used_textureslot(self):
        print("Adding textureslots: ")
        self.texture_slot0 = self.b_mat.texture_slots.add()
        self.texture_slot1 = self.b_mat.texture_slots.add()

        print("Not using second: ")
        self.texture_slot1.use = False

        self.used_textslots = texture.get_used_textslots(self.b_mat)

        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))
        nose.tools.assert_true(len(self.used_textslots) == 1)
