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
import itertools

from io_scene_niftools.modules.nif_import.property.geometry.niproperty import NiPropertyProcessor
from io_scene_niftools.modules.nif_import.property.nodes_wrapper import NodesWrapper
from io_scene_niftools.modules.nif_import.property.shader.bsshaderlightingproperty import BSShaderLightingPropertyProcessor
from io_scene_niftools.modules.nif_import.property.shader.bsshaderproperty import BSShaderPropertyProcessor
from io_scene_niftools.utils.logging import NifLog


class MeshPropertyProcessor:

    def __init__(self):
        # get processor singletons
        self.nodes_wrapper = NodesWrapper()
        self.processors = (
            NiPropertyProcessor(),
            BSShaderPropertyProcessor.get(),
            BSShaderLightingPropertyProcessor.get()
        )

        # Register processors
        self.process_property = singledispatch(self.process_property)
        for processor in self.processors:
            processor.register(self.process_property)

    def process_property_list(self, n_block, b_obj):
        b_mesh = b_obj.data

        # get all valid properties that are attached to n_block
        props = list(prop for prop in itertools.chain(n_block.properties, n_block.bs_properties) if prop is not None)

        # we need no material if we have no properties
        if not props:
            return

        # just to avoid duped materials, a first pass, make sure a named material is created or retrieved
        for prop in props:
            if prop.name:
                name = prop.name.decode()
                if name and name in bpy.data.materials:
                    b_mat = bpy.data.materials[name]
                    NifLog.debug(f"Retrieved already imported material {b_mat.name} from name {name}")
                else:
                    b_mat = bpy.data.materials.new(name)
                    NifLog.debug(f"Created material {name} to store properties in {b_mat.name}")
                break
        else:
            # bs shaders often have no name, so generate one from mesh name
            name = n_block.name.decode() + "_nt_mat"
            b_mat = bpy.data.materials.new(name)
            NifLog.debug(f"Created material {name} to store properties in {b_mat.name}")

        # do initial settings for the material here
        self.nodes_wrapper.b_mat = b_mat
        self.nodes_wrapper.clear_default_nodes()

        # link the material to the mesh
        b_mesh.materials.append(b_mat)

        # set the vars on every processor
        for processor in self.processors:
            processor.n_block = n_block
            processor.b_obj = b_obj
            processor.b_mesh = b_mesh
            processor.b_mat = b_mat
            processor.nodes_wrapper = self.nodes_wrapper

        # run all processors
        for prop in props:
            NifLog.debug(f"{type(prop)} property found")
            self.process_property(prop)

        self.nodes_wrapper.connect_to_output(b_mesh.vertex_colors)

    def process_property(self, prop):
        """Base method to warn user that this property is not supported"""
        NifLog.warn(f"Unknown property block found : {prop.name:s}")
        NifLog.warn(f"This type isn't currently supported: {type(prop)}")
