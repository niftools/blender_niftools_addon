"""This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from io_scene_niftools.modules.nif_export.animation.texture import TextureAnimation
from io_scene_niftools.modules.nif_export.property import texture
from io_scene_niftools.modules.nif_export.property.texture.writer import TextureWriter
from io_scene_niftools.utils.logging import NifLog, NifError
from io_scene_niftools.utils.consts import TEX_SLOTS


class TextureSlotManager:

    def __init__(self):
        self.dict_mesh_uvlayers = []
        self.texture_writer = TextureWriter()
        self.texture_anim = TextureAnimation()
        self.b_mat = None

        self.slots = {}
        self._reset_fields()

    def _reset_fields(self):
        self.slots = {}
        for slot_name in vars(TEX_SLOTS).values():
            self.slots[slot_name] = None

    def get_input_node_of_type(self, input_socket, node_types):
        # search back in the node tree for nodes of a certain type(s), depth-first
        links = input_socket.links
        if not links:
            # this socket has no inputs
            return None
        node = links[0].from_node
        if isinstance(node, node_types):
            # the input node is of the required type
            return node
        else:
            if len(node.inputs) > 0:
                for input in node.inputs:
                    # check every input if somewhere up that tree is a node of the required type
                    input_results = self.get_input_node_of_type(input, node_types)
                    if input_results:
                        return input_results
                # we found nothing
                return None
            else:
                # this has no inputs, and doesn't classify itself
                return None

    def get_uv_node(self, b_texture_node):
        uv_node = self.get_input_node_of_type(b_texture_node.inputs[0], (bpy.types.ShaderNodeUVMap, bpy.types.ShaderNodeTexCoord))
        if uv_node is None:
            links = b_texture_node.inputs[0].links
            if not links:
                # nothing is plugged in, so it will use the first UV map
                return 0
        if isinstance(uv_node, bpy.types.ShaderNodeUVMap):
            uv_name = uv_node.uv_map
            try:
                # ignore the "UV" prefix
                return int(uv_name[2:])
            except:
                return 0
        elif isinstance(uv_node, bpy.types.ShaderNodeTexCoord):
            return "REFLECT"
        else:
            raise NifError(f"Unsupported vector input for {b_texture_node.name} in material '{self.b_mat.name}''.\n"
                           f"Expected 'UV Map' or 'Texture Coordinate' nodes")

    def get_global_uv_transform_clip(self):
        # get the values from the nodes, find the nodes by name, or search back in the node tree
        x_scale = y_scale = x_offset = y_offset = clamp_x = clamp_y = None
        # first check if there are any of the preset name - much more time efficient
        try:
            combine_node = self.b_mat.node_tree.nodes["Combine UV0"]
            if not isinstance(combine_node, bpy.types.ShaderNodeCombineXYZ):
                combine_node = None
                NifLog.warn(f"Found node with name 'Combine UV0', but it was of the wrong type.")
        except:
            # if there is a combine node, it does not have the standard name
            combine_node = None
            NifLog.warn(f"Did not find node with 'Combine UV0' name.")

        if combine_node is None:
            # did not find a (correct) combine node, search through the first existing texture node vector input
            b_texture_node = None
            for slot_name, slot_node in self.slots.items():
                if slot_node is not None:
                    break
            if slot_node is not None:
                combine_node = self.get_input_node_of_type(slot_node.inputs[0], bpy.types.ShaderNodeCombineXYZ)
                NifLog.warn(f"Searching through vector input of {slot_name} texture gave {combine_node}")

        if combine_node:
            x_link = combine_node.inputs[0].links
            if x_link:
                x_node = x_link[0].from_node
                x_scale = x_node.inputs[1].default_value
                x_offset = x_node.inputs[2].default_value
                clamp_x = x_node.use_clamp
            y_link = combine_node.inputs[1].links
            if y_link:
                y_node = y_link[0].from_node
                y_scale = y_node.inputs[1].default_value
                y_offset = y_node.inputs[2].default_value
                clamp_y = y_node.use_clamp
        return x_scale, y_scale, x_offset, y_offset, clamp_x, clamp_y

    @staticmethod
    def get_used_textslots(b_mat):
        used_slots = []
        if b_mat is not None and b_mat.use_nodes:
            used_slots = [node for node in b_mat.node_tree.nodes if isinstance(node, bpy.types.ShaderNodeTexImage)]
        return used_slots

    @staticmethod
    def get_uv_layers(b_mat):
        used_uvlayers = set()
        texture_slots = TextureSlotManager.get_used_textslots(b_mat)
        for slot in texture_slots:
            used_uvlayers.add(slot.uv_layer)
        return used_uvlayers

    def determine_texture_types(self, b_mat):
        """Checks all texture nodes of a material and checks their labels for relevant texture cues.
        Stores all slots as class properties."""
        self.b_mat = b_mat
        self._reset_fields()

        for b_texture_node in self.get_used_textslots(b_mat):
            shown_label = b_texture_node.label
            if shown_label == '':
                shown_label = b_texture_node.image.name
            NifLog.debug(f"Found node {b_texture_node.name} of type {shown_label}")

            # go over all slots
            for slot_name in self.slots.keys():
                if slot_name in shown_label:
                    # slot has already been populated
                    if self.slots[slot_name]:
                        raise NifError(f"Multiple {slot_name} textures in material '{b_mat.name}''.\n"
                                       f"Make sure there is only one texture node labeled as '{slot_name}'")
                    # it's a new slot so store it
                    self.slots[slot_name] = b_texture_node
                    break
            # unsupported texture type
            else:
                raise NifError(f"Do not know how to export texture node '{b_texture_node.name}' in material '{b_mat.name}' with label '{shown_label}'."
                               f"Delete it or change its label.")
