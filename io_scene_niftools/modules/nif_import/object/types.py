"""This script contains helper methods to import objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2016, NIF File Format Library and Tools contributors.
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
import bpy

from io_scene_niftools.modules.nif_import.object import Object


class NiTypes:

    @staticmethod
    def import_root_collision(n_node, b_obj):
        """ Import a RootCollisionNode """
        if isinstance(n_node, NifFormat.RootCollisionNode):
            b_obj["type"] = "RootCollisionNode"
            b_obj.name = "RootCollisionNode"
            b_obj.display_type = 'BOUNDS'
            b_obj.show_wire = True
            b_obj.display_bounds_type = 'BOX'
            # b_obj.game.use_collision_bounds = True
            # b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
            b_obj.niftools.flags = n_node.flags

    @staticmethod
    def import_range_lod_data(n_node, b_obj, b_children):
        """ Import LOD ranges and mark b_obj as a LOD node """
        if isinstance(n_node, NifFormat.NiLODNode):
            b_obj["type"] = "NiLODNode"
            range_data = n_node

            # where lodlevels are stored is determined by version number need more examples - just a guess here
            if not range_data.lod_levels:
                range_data = n_node.lod_level_data

            # can't just take b_obj.children because the order doesn't match
            for lod_level, b_child in zip(range_data.lod_levels, b_children):
                b_child["near_extent"] = lod_level.near_extent
                b_child["far_extent"] = lod_level.far_extent

    @staticmethod
    def import_billboard(n_node, b_obj):
        """ Import a NiBillboardNode """
        if isinstance(n_node, NifFormat.NiBillboardNode) and not isinstance(b_obj, bpy.types.Bone):
            # find camera object
            for obj in bpy.context.scene.objects:
                if obj.type == 'CAMERA':
                    b_obj_camera = obj
                    break
            # none exists, create one
            else:
                b_obj_camera_data = bpy.data.cameras.new("Camera")
                b_obj_camera = Object.create_b_obj(None, b_obj_camera_data)
            # make b_obj track camera object
            constr = b_obj.constraints.new('TRACK_TO')
            constr.target = b_obj_camera
            constr.track_axis = 'TRACK_Z'
            constr.up_axis = 'UP_Y'

    @staticmethod
    def import_empty(n_block):
        """Creates and returns a grouping empty."""
        b_empty = Object.create_b_obj(n_block, None)
        # TODO [flags] Move out to generic processing
        b_empty.niftools.flags = n_block.flags
        return b_empty
