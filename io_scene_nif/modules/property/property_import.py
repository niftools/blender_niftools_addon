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
from functools import singledispatch

from pyffi.formats.nif import NifFormat

from io_scene_nif.utility.nif_decorator import overload_method


class Property:

    def __init__(self):
        self.b_mesh = None
        self.process_property = singledispatch(self.process_property)
        self.process_property.register(NifFormat.NiStencilProperty, self.process_nistencilproperty_property)

    def process_property_list(self, n_block, b_mesh):
        self.b_mesh = b_mesh
        for prop in n_block.properties:
            print("About to process" + str(prop.__class__))
            self.process_property(prop)

    # @overload_method(NifFormat.NiStencilProperty)
    def process_nistencilproperty_property(self, prop):
        """Stencil (for double sided meshes"""
        print("NiStencilProperty property found" + str(prop))
        self.b_mesh.show_double_sided = True  # We don't check flags for now, nothing fancy

    # # @overload_method(NifFormat.NiAlphaProperty)
    # def process_property(self, prop):
    #     """Alpha for transparancy in the material or texture"""
    #     print("NiAlphaProperty property found" + str(prop))
    #
    # # @overload_method(NifFormat.NiSpecularProperty)
    # def process_property(self, prop):
    #     """Material based specular"""
    #     print("NiSpecularProperty property found" + str(prop))
    #
    # # @overload_method(NifFormat.NiWireframeProperty)
    # def process_property(self, prop):
    #     """Material based specular"""
    #     print("NiWireframeProperty found" + str(prop))

    # @overload_method(object)
    def process_property(self, prop):
        """Stencil (for double sided meshes"""
        print("Unknown property found" + str(prop))
        print("This type isn't supported: {}".format(type(prop.__class__)))
