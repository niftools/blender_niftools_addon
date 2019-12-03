"""Unit testing that the decorator utility"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules import armature

B_NPC_L = "NPC XXX [XXX].L"
B_NPC_R = "NPC XXX [XXX].R"
N_NPC_L = "NPC L XXX [LXXX]"
N_NPC_R = "NPC R XXX [RXXX]"

B_BIP01_L = "Bip01 XXX.L"
B_BIP01_R = "Bip01 XXX.R"
N_BIP01_L = "Bip01 L XXX"
N_BIP01_R = "Bip01 R XXX"


class TestArmature:

    def test_nif_to_blender_left_conversion_npc(self):
        l_side = armature.get_bone_name_for_blender(N_NPC_L)
        nose.tools.assert_equals(l_side, B_NPC_L)

    def test_nif_to_blender_right_conversion_npc(self):
        r_side = armature.get_bone_name_for_blender(N_NPC_R)
        nose.tools.assert_equals(r_side, B_NPC_R)

    def test_blender_to_nif_name_left_conversion_npc(self):
        l_side = armature.get_bone_name_for_nif(B_NPC_L)
        nose.tools.assert_equals(l_side, N_NPC_L)

    def test_blender_to_nif_name_right_conversion_npc(self):
        r_side = armature.get_bone_name_for_nif(B_NPC_R)
        nose.tools.assert_equals(r_side, N_NPC_R)

    def test_nif_to_blender_left_conversion_bip(self):
        l_side = armature.get_bone_name_for_blender(N_BIP01_L)
        nose.tools.assert_equals(l_side, B_BIP01_L)

    def test_nif_to_blender_right_conversion_bip(self):
        r_side = armature.get_bone_name_for_blender(N_BIP01_R)
        nose.tools.assert_equals(r_side, B_BIP01_R)

    def test_blender_to_nif_name_left_conversion_bip(self):
        l_side = armature.get_bone_name_for_nif(B_BIP01_L)
        nose.tools.assert_equals(l_side, N_BIP01_L)

    def test_blender_to_nif_name_right_conversion_bip(self):
        r_side = armature.get_bone_name_for_nif(B_BIP01_R)
        nose.tools.assert_equals(r_side, N_BIP01_R)

