"""This script contains classes to help import material animations."""

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

from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import.animation import Animation
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.consts import LOC, SCALE


class MaterialAnimation(Animation):

    def import_material_controllers(self, n_geom, b_material):
        """Import material animation data for given geometry."""
        if not NifOp.props.animation:
            return
        n_material = math.find_property(n_geom, NifFormat.NiMaterialProperty)
        if n_material:
            self.import_material_alpha_controller(b_material, n_material)
            for b_channel, n_target_color in (("niftools.ambient_color", NifFormat.TargetColor.TC_AMBIENT),
                                              ("diffuse_color", NifFormat.TargetColor.TC_DIFFUSE),
                                              ("specular_color", NifFormat.TargetColor.TC_SPECULAR)):
                self.import_material_color_controller(b_material, n_material, b_channel, n_target_color)

        self.import_material_uv_controller(b_material, n_geom)

    def import_material_alpha_controller(self, b_material, n_material):
        # find alpha controller
        n_ctrl = math.find_controller(n_material, NifFormat.NiAlphaController)
        if not n_ctrl:
            return
        NifLog.info("Importing alpha controller")

        b_mat_action = self.create_action(b_material, "MaterialAction")
        interp = self.get_b_interp_from_n_interp(n_ctrl.data.data.interpolation)
        times, keys = self.get_keys_values(n_ctrl.data.data.keys)
        # key needs to be RGB due to current representation in blender
        keys = [(v, v, v) for v in keys]
        self.add_keys(b_mat_action, "niftools.emissive_alpha", range(3), n_ctrl.flags, times, keys, interp)

    def import_material_color_controller(self, b_material, n_material, b_channel, n_target_color):
        # find material color controller with matching target color
        for n_ctrl in n_material.get_controllers():
            if isinstance(n_ctrl, NifFormat.NiMaterialColorController):
                if n_ctrl.get_target_color() == n_target_color:
                    break
        else:
            return
        NifLog.info(f"Importing material color controller for target color {n_target_color} into blender channel {b_channel}")
        b_mat_action = self.create_action(b_material, "MaterialAction")
        interp = self.get_b_interp_from_n_interp(n_ctrl.data.data.interpolation)
        times, keys = self.get_keys_values(n_ctrl.data.data.keys)
        self.add_keys(b_mat_action, b_channel, range(3), n_ctrl.flags, times, keys, interp)

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data as a mapping node with animated values."""
        # search for the block
        n_ctrl = math.find_controller(n_geom, NifFormat.NiUVController)
        if not n_ctrl:
            return
        NifLog.info("Importing UV controller")

        if not any(n_uvgroup.keys for n_uvgroup in n_ctrl.data.uv_groups):
            return

        b_mat_action = self.create_action(b_material.node_tree, "MaterialAction")

        tree = b_material.node_tree
        transform = tree.nodes.new('ShaderNodeMapping')
        # get previous links
        used_links = []
        for link in tree.links:
            # get uv nodes
            if link.from_node.type == "UVMAP":
                used_links.append(link)

        # link the node between previous uv node and texture node
        for link in used_links:
            from_socket = link.from_socket
            to_socket = link.to_socket
            tree.links.remove(link)
            tree.links.new(from_socket, transform.inputs[0])
            tree.links.new(transform.outputs[0], to_socket)

        # loc U, loc V, scale U, scale V
        LOC_DP = 1
        SCALE_DP = 3
        dtypes = (LOC_DP, 0), (LOC_DP, 1), (SCALE_DP, 0), (SCALE_DP, 1)
        for n_uvgroup, (data_path, array_ind) in zip(n_ctrl.data.uv_groups, dtypes):
            if n_uvgroup.keys:
                interp = self.get_b_interp_from_n_interp(n_uvgroup.interpolation)
                times, keys = self.get_keys_values(n_uvgroup.keys)
                # UV V coordinate is inverted in blender
                if 1 == LOC_DP and array_ind == 1:
                    keys = [-key for key in keys]
                self.add_keys(b_mat_action, f'nodes["{transform.name}"].inputs[{data_path}].default_value', (array_ind,), n_ctrl.flags, times, keys, interp)

