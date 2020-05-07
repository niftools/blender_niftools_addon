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

import itertools
from functools import singledispatch

from io_scene_nif.modules.nif_import.property.geometry.niproperty import NiPropertyProcessor
from io_scene_nif.modules.nif_import.property.shader.bsshaderlightingproperty import BSShaderLightingPropertyProcessor
from io_scene_nif.modules.nif_import.property.shader.bsshaderproperty import BSShaderPropertyProcessor
from io_scene_nif.utils.util_logging import NifLog


class MeshPropertyProcessor:

    def __init__(self):
        self.processors = (
            NiPropertyProcessor.get(),
            BSShaderPropertyProcessor.get(),
            BSShaderLightingPropertyProcessor.get()
        )

        # Register processors
        self.process_property = singledispatch(self.process_property)
        for processor in self.processors:
            processor.register(self.process_property)

    def process_property_list(self, n_block, b_mesh):
        props = list(prop for prop in itertools.chain(n_block.properties, n_block.bs_properties) if prop is not None)

        # just to avoid duped materials, a first pass, make sure a named material is created or retrieved
        for prop in props:
            if prop.name:
                name = prop.name.decode()
                if name and name in bpy.data.materials:
                    b_mat = bpy.data.materials[name]
                    NifLog.debug("Retrieved already imported material {1} from name {0} - aborting due to bug".format(name, b_mat.name))
                    # stop here since it is bugged for multiple runs
                    b_mesh.materials.append(b_mat)
                    return b_mat
                else:
                    b_mat = bpy.data.materials.new(name)
                    NifLog.debug("Created material {0} to store properties in {1}".format(name, b_mat.name))
                break
        else:
            # bs shaders often have no name, so generate one from mesh name
            name = n_block.name.decode() + "_nt_mat"
            b_mat = bpy.data.materials.new(name)
            NifLog.debug("Created material {0} to store properties in {1}".format(name, b_mat.name))

        # link the material to the mesh
        b_mesh.materials.append(b_mat)

        # set the vars on every processor
        for processor in self.processors:
            processor.b_mesh = b_mesh
            processor.n_block = n_block
            processor.b_mat = b_mat

        # run all processors
        for prop in props:
            NifLog.debug("{0} property found {0}".format(str(type(prop)), str(prop)))
            self.process_property(prop)

    def process_property(self, prop):
        """Base method to warn user that this property is not supported"""
        NifLog.warn("Unknown property block found : {0}".format(str(prop.name)))
        NifLog.warn("This type isn't currently supported: {0}".format(type(prop)))
