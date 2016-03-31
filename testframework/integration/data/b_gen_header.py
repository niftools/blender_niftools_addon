"""Header Helper functions"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

import bpy

import nose

MV_VER = 67108866
OB_VER = 335544325
FO3_VER = 335675399
BETH_UV = 11
BETH_UV2_FO3 = 34


def _set_version_info(nif_ver=0, user_ver=0, user_ver_2=0):
    scene = bpy.context.scene.niftools_scene
    scene.nif_version = nif_ver
    scene.user_version = user_ver
    scene.user_version_2 = user_ver_2

def b_create_morrowind_info():
    _set_version_info(nif_ver=MV_VER)
    
def b_create_oblivion_info():
    _set_version_info(nif_ver=OB_VER, user_ver=BETH_UV, user_ver_2=BETH_UV)
    
def b_create_fo3_info():
    _set_version_info(nif_ver=FO3_VER, user_ver=BETH_UV, user_ver_2=BETH_UV2_FO3)
    
def b_create_skyrim_info():
    raise NotImplementedError


def _b_check_version_info(nif_ver=0, user_ver=0, user_ver_2=0):
    scene = bpy.context.scene.niftools_scene
    print("Expected - {0}, {1}, {2}".format(nif_ver, user_ver, user_ver_2))
    
    nv = scene.nif_version
    print("nif_version - {0}".format(nv))
    nose.tools.assert_equal(nv, nif_ver)  
    
    uv = scene.user_version
    print("user_version - {0}".format(uv))
    nose.tools.assert_equal(uv, user_ver) 
    
    uv2 = scene.user_version_2
    print("user_version_2 - {0}".format(uv2))
    nose.tools.assert_equal(uv2, user_ver_2) 
    
    nose.tools.assert_equal(scene.user_version, user_ver)  
    nose.tools.assert_equal(scene.user_version_2, user_ver_2)

def b_check_morrowind_info():    
    _b_check_version_info(nif_ver=67108866)
    
def b_check_oblivion_info():
    _b_check_version_info(nif_ver=335544325, user_ver=11, user_ver_2=11)
    
def b_check_fo3_info():
    _b_check_version_info(nif_ver=335675399, user_ver=11, user_ver_2=34)
    
def b_check_skyrim_info():
    raise NotImplementedError