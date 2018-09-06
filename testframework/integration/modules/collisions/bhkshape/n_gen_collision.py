"""Collision Helper functions"""

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

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

HAVOK_SCALE = 7

def n_attach_bsx_flag(n_ninode):
    '''Attach a BSXFlag with collision setting enabled'''
    
    n_bsxflags = NifFormat.BSXFlags()
    n_bsxflags.integer_data = 2 # enable physics
    
    # add flag to top of list
    n_ninode.num_extra_data_list += 1
    n_ninode.extra_data_list.update_size()
    n_ninode.extra_data_list.reverse()
    n_ninode.extra_data_list[-1] = n_bsxflags
    n_ninode.extra_data_list.reverse()

    
def n_check_bsx_flag(n_bsxflag):
    '''Checks the BSXFlag'''
    nose.tools.assert_is_instance(n_bsxflag, NifFormat.BSXFlags)
    nose.tools.assert_equal(n_bsxflag.integer_data, 2) #2 = enable collision flag
    
    
def n_attach_bhkcollisionobject(n_ninode):
    '''Attaches a collision object to the NiNode'''
    
    n_bhkcollisionobject = NifFormat.bhkCollisionObject()
    n_ninode.collision_object = n_bhkcollisionobject #attach to ninode
    n_bhkcollisionobject.target = n_ninode
    return n_bhkcollisionobject


def n_check_bhkcollisionobject_data(n_ninode):
    '''Checks a bhkCollision Objects default data'''
    
    nose.tools.assert_equal(n_ninode.collision_object != None, True)
    n_bhkcollisionobject = n_ninode.collision_object
    
    nose.tools.assert_is_instance(n_bhkcollisionobject, NifFormat.bhkCollisionObject)
    nose.tools.assert_equal(n_bhkcollisionobject.flags, 1)
    nose.tools.assert_equal(n_bhkcollisionobject.target, n_ninode)
    return n_bhkcollisionobject


def n_attach_bhkrigidbody(n_bhkcollisionobject):
    '''Attaches a bhkrigidBody to a bhkCollisionObject'''
    
    n_bhkrigidbody = NifFormat.bhkRigidBody()
    n_bhkcollisionobject.body = n_bhkrigidbody    
    return n_bhkrigidbody


def n_check_bhkrigidbody_data(n_bhkcollisionobject):
    '''Check we have a rigidbody'''
    
    nose.tools.assert_equal(n_bhkcollisionobject.body != None, True)
    n_bhkrigidbody = n_bhkcollisionobject.body
    nose.tools.assert_is_instance(n_bhkrigidbody, NifFormat.bhkRigidBody)
    return n_bhkrigidbody


def n_check_bhkrigidbodyt_data(self, n_data):
    # Inherited from bhkrigidbody, transformations apply. #
    # No equivilant mechanism in plugin
    pass


def n_check_upb_property(self, n_data, default = "Mass = 0.000000 Ellasticity = 0.300000 Friction = 0.300000 Unyielding = 0 Simulation_Geometry = 2 Proxy_Geometry = <None> Use_Display_Proxy = 0 Display_Children = 1 Disable_Collisions = 0 Inactive = 0 Display_Proxy = <None> "):
    
    nose.tools.assert_is_instance(n_data, NifFormat.NiStringExtraData)
    nose.tools.assert_equal(n_data.name, b'UPB') # User property buffer

#     valuestring = n_data.string_data
#     valuestring = valuestring.decode()
#     valuestring = valuestring.replace("\r\n"," ")
#     UPBString = default
#     nose.tools.assert_equal(valuestring, UPBString)
     
    