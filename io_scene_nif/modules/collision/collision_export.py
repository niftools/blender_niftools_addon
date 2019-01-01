"""This script contains classes to export collision objects."""

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
from io_scene_nif.modules import obj
from io_scene_nif.modules.collision.havok import BHKShape
from io_scene_nif.modules.obj.object_export import ObjectHelper, BlockRegistry
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class Collision:

    def __init__(self):
        self.object_helper = ObjectHelper()
        self.bhkshapehelper = BHKShape()

    def export_collision(self, b_obj, parent_block):
        """Main function for adding collision object to a node."""
        if NifOp.props.game == 'MORROWIND':
            if b_obj.game.collision_bounds_type != 'TRIANGLE_MESH':
                raise nif_utils.NifError("Morrowind only supports Triangle Mesh collisions.")
            node = BlockRegistry.create_block("RootCollisionNode", b_obj)
            parent_block.add_child(node)
            node.flags = 0x0003  # default
            self.object_helper.set_object_matrix(b_obj, 'localspace', node)
            for child in b_obj.children:
                ObjectHelper.export_node(child, 'localspace', node, None)

        elif NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
            nodes = [parent_block]
            nodes.extend([block for block in parent_block.children if block.name[:14] == 'collisiondummy'])
            for node in nodes:
                try:
                    self.bhkshapehelper.export_collision_helper(b_obj, node)
                    break
                except ValueError:  # adding collision failed
                    continue
            else:  # all nodes failed so add new one
                node = BlockRegistry.create_ninode(b_obj)
                node.set_transform(obj.IDENTITY44)
                node.name = 'collisiondummy%i' % parent_block.num_children
                if b_obj.niftools.objectflags != 0:
                    node_flag_hex = hex(b_obj.niftools.objectflags)
                else:
                    node_flag_hex = 0x000E  # default
                node.flags = node_flag_hex
                parent_block.add_child(node)
                self.bhkshapehelper.export_collision_helper(b_obj, node)
    
        else:
            NifLog.warn(
                "Only Morrowind, Oblivion, and Fallout 3 collisions are supported, skipped collision object '{0}'".format(
                    b_obj.name))
