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

import nose

MV_VER = 67108866
OB_VER = 335544325
FO3_VER = 335675399
BETH_UV = 11
BETH_UV2_FO3 = 34

def n_create_header(n_data, nif_ver=0x0, user_ver=0x0, user_ver_2=0x0):
    n_data.version = nif_ver
    n_data.user_version = user_ver
    n_data.user_version_2 = user_ver_2

def n_create_header_morrowind(n_data):
    n_create_header(n_data, nif_ver=MV_VER)

def n_create_header_oblivion(n_data):
    n_create_header(n_data, nif_ver=OB_VER, user_ver=BETH_UV, user_ver_2=BETH_UV)
    
def n_create_header_fo3(n_data):
    n_create_header(n_data, nif_ver=FO3_VER, user_ver=BETH_UV, user_ver_2=BETH_UV2_FO3)
    
def n_create_header_skyrim(n_data):
    raise NotImplementedError


def n_check_version_info(n_data, nif_ver=0x0, user_ver=0x0, user_ver_2=0x0):
    print("Expected - {0}, {1}, {2}".format(nif_ver, user_ver, user_ver_2))
    
    nv = n_data.version
    print("nif_version - {0}".format(nv))
    nose.tools.assert_equal(nv, nif_ver)  
    
    uv = n_data.user_version
    print("user_version - {0}".format(uv))
    nose.tools.assert_equal(uv, user_ver) 
    
    uv2 = n_data.user_version_2
    print("user_version_2 - {0}".format(uv2))
    nose.tools.assert_equal(uv2, user_ver_2) 
    
def n_check_header_morrowind(n_data):
    n_check_version_info(n_data, nif_ver=MV_VER)

def n_check_header_oblivion(n_data):
    n_check_version_info(n_data, nif_ver=OB_VER, user_ver=BETH_UV, user_ver_2=BETH_UV)
    
    
def n_check_header_fo3(n_data):
    n_check_version_info(n_data, nif_ver=FO3_VER, user_ver=BETH_UV, user_ver_2=BETH_UV2_FO3)
    

def n_check_header_skyrim(n_data):
    raise NotImplementedError

    