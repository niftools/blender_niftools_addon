"""This script contains helper methods to import mesh properties."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

from functools import singledispatch

from io_scene_nif.modules.nif_import.property.geometry.niproperty import NiPropertyProcessor
from io_scene_nif.modules.nif_import.property.shader.bsshaderproperty import BSShaderPropertyProcessor
from io_scene_nif.utils.util_logging import NifLog


class MeshPropertyProcessor:

    def __init__(self):
        self.niproperty = NiPropertyProcessor.get()
        self.bsshader = BSShaderPropertyProcessor().get()

        self.process_property = singledispatch(self.process_property)
        self.niproperty.register_niproperty(self.process_property)
        self.bsshader.register_bsproperty(self.process_property)

    def process_property_list(self, n_block, b_mesh):
        self.niproperty.b_mesh = b_mesh
        self.niproperty.n_block = n_block
        self.bsshader.b_mesh = b_mesh
        self.bsshader.n_block = n_block

        if n_block.properties:
            self.process_props(n_block.properties)

        if n_block.bs_properties:
            self.process_props(n_block.bs_properties)

    def process_props(self, properties):
        for prop in properties:
            NifLog.debug("{0} property found {0}".format(str(type(prop)), str(prop)))
            self.process_property(prop)

    def process_property(self, prop):
        """Base method to warn user that this property is not supported"""
        NifLog.warn("Unknown property block found : {0}".format(str(prop.name)))
        NifLog.warn("This type isn't currently supported: {0}".format(type(prop)))
