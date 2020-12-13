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


class TextureSlotManager:

    def __init__(self):
        self.dict_mesh_uvlayers = []
        self.texture_writer = TextureWriter()
        self.texture_anim = TextureAnimation()
        self.b_mat = None

        self.slots = {}
        self._reset_fields()

    def _reset_fields(self):
        self.slots = {
                "Base": None,
                "Dark": None,
                "Detail": None,
                "Gloss": None,
                "Glow": None,
                "Bump Map": None,
                "Decal 0": None,
                "Decal 1": None,
                "Decal 2": None,
                # extra shader stuff?
                "Specular": None,
                "Normal": None,
        }

    def get_uv_node(self, b_texture_node):
        # check if a node is plugged into the b_texture_node's vector input
        links = b_texture_node.inputs[0].links
        if not links:
            return 0
        uv_node = links[0].from_node
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
            NifLog.debug(f"Found node {b_texture_node.name} of type {b_texture_node.label}")

            # go over all slots
            for slot_name in self.slots.keys():
                if slot_name in b_texture_node.label:
                    # slot has already been populated
                    if self.slots[slot_name]:
                        raise NifError(f"Multiple {slot_name} textures in material '{b_mat.name}''.\n"
                                       f"Make sure there is only one texture node labeled as '{slot_name}'")
                    # it's a new slot so store it
                    self.slots[slot_name] = b_texture_node
                    break
            # unsupported texture type
            else:
                raise NifError(f"Do not know how to export texture node '{b_texture_node.name}' in material '{b_mat.name}'."
                               f"Delete it or change its label.")
