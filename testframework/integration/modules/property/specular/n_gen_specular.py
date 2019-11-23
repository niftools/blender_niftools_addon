# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005, NIF File Format Library and Tools contributors.
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


def n_attach_specular_prop(n_trishapedata):
    """Attaches a NiSpecularProperty to a trishapedata block property's array at pos[0]"""

    n_nispecularprop = NifFormat.NiSpecularProperty()
    n_nispecularprop.flags = 0x1

    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_nispecularprop

    n_trishapedata.properties.reverse()


def n_alter_material_specular(n_nimaterialprop):
    with ref(n_nimaterialprop.specular_color) as n_color3:
        n_color3.r = 0.5
        n_color3.g = 0.0
        n_color3.b = 0.0


def n_check_material_specular(n_mat_prop):
    nose.tools.assert_equal((n_mat_prop.specular_color.r,
                             n_mat_prop.specular_color.g,
                             n_mat_prop.specular_color.b),
                            (0.5, 0.0, 0.0))


def n_check_specular_block(n_mat_prop):
    nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiSpecularProperty)


def n_check_specular_property(n_specular_prop):
    nose.tools.assert_equal(n_specular_prop.flags, 0x1)
