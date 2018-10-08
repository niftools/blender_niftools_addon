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
from pyffi.formats.nif import NifFormat
from functools import singledispatch

from io_scene_nif.modules.property.material.material_import import Material
from io_scene_nif.utility.nif_global import NifData
from io_scene_nif.utility.nif_logging import NifLog


class Property:

    def __init__(self):
        self.b_mesh = None
        self.n_block = None
        self.process_property = singledispatch(self.process_property)
        self.process_property.register(NifFormat.NiStencilProperty, self.process_nistencil_property)
        self.process_property.register(NifFormat.NiSpecularProperty, self.process_nispecular_property)
        self.process_property.register(NifFormat.NiWireframeProperty, self.process_niwireframe_property)
        self.process_property.register(NifFormat.NiMaterialProperty, self.process_nimaterial_property)
        self.process_property.register(NifFormat.NiAlphaProperty, self.process_nialphs_property)

    def process_property_list(self, n_block, b_mesh):
        self.n_block = n_block
        self.b_mesh = b_mesh
        for prop in n_block.properties:
            NifLog.debug("About to process" + str(type(prop)))
            self.process_property(prop)
        return

    def process_property(self, prop):
        """Base method to warn user that this property is not supported"""
        NifLog.warn("Unknown property block found : " + str(prop.name))
        NifLog.warn("This type isn't currently supported: {}".format(type(prop)))

    def process_nistencil_property(self, prop):
        """Stencil (for double sided meshes"""
        NifLog.debug("NiStencilProperty property found" + str(prop))
        self.b_mesh.show_double_sided = True  # We don't check flags for now, nothing fancy

    def process_nispecular_property(self, prop):
        """SpecularProperty based specular"""
        NifLog.debug("NiSpecularProperty property found" + str(prop))
        b_mat = self._find_or_create_material()

        # TODO [material][property]
        if NifData.data.version == 0x14000004:
            b_mat.specular_intensity = 0.0  # no specular prop

    def process_nialphs_property(self, prop):
        """Import a NiAlphaProperty based material"""
        NifLog.debug("NiAlphaProperty property found" + str(prop))
        b_mat = self._find_or_create_material()
        Material.set_alpha(b_mat, prop)

    def process_nimaterial_property(self, prop):
        """Import a NiMaterialProperty based material"""
        NifLog.debug("NiMaterialProperty property found" + str(prop))
        b_mat = self._find_or_create_material()
        Material().import_material(self.n_block, b_mat, prop)

    def process_niwireframe_property(self, prop):
        """Material based specular"""
        NifLog.debug("NiWireframeProperty found" + str(prop))
        b_mat = self._find_or_create_material()
        b_mat.type = 'WIRE'

    def _find_or_create_material(self):
        b_mats = self.b_mesh.materials
        if len(b_mats) == 0:
            # assign to 1st material slot
            NifLog.debug("Creating placeholder material to store properties in")
            b_mat = bpy.data.materials.new("")
            self.b_mesh.materials.append(b_mat)
        else:
            NifLog.debug("Reusing existing material to store additional properties in")
            b_mat = self.b_mesh.materials[0]
        return b_mat
