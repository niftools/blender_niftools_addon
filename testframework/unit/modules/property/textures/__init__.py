"""Module for unit testing that the blender nif plugin armature modules"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import nose

import bpy

from io_scene_nif.modules.nif_export.property.texture import TextureSlotManager


class TestTextureSlotManager:

    @classmethod
    def setUpClass(cls):
        cls.texture_helper = TextureSlotManager()

    def setup(self):
        self.b_mat = bpy.data.materials.new("test_material")
        self.used_textslots = []

    def teardown(self):
        bpy.data.materials.remove(self.b_mat)
        del self.b_mat

    def test_no_material(self):
        self.used_textslots = self.texture_helper.get_used_textslots(None)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 0)

    def test_empty_textureslots(self):
        self.used_textslots = self.texture_helper.get_used_textslots(self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 0)

    def test_single_used_textureslot(self):
        print("Adding textureslot")
        self.texture_slot0 = self.b_mat.texture_slots.add()

        self.used_textslots = self.texture_helper.get_used_textslots(self.b_mat)
        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))

        nose.tools.assert_true(len(self.used_textslots) == 1)

    def test_two_textures_one_used_textureslot(self):
        print("Adding textureslots: ")
        self.b_mat.texture_slots.add()
        texture_slot1 = self.b_mat.texture_slots.add()

        print("Not using second: ")
        texture_slot1.use = False

        self.used_textslots = self.texture_helper.get_used_textslots(self.b_mat)

        print("Used Slots: %s, items = %s" % (self.used_textslots, len(self.used_textslots)))
        nose.tools.assert_true(len(self.used_textslots) == 1)

