"""This script contains classes to export havok based collision objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2018, NIF File Format Library and Tools contributors.
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
from io_scene_nif.modules.obj.object_export import ObjectHelper


class Bound:

    def export_bounding_box(self, b_obj, block_parent, bsbound=False):
        """Export a Morrowind or Oblivion bounding box."""
        # calculate bounding box extents
        b_vert_list = [vert.co for vert in b_obj.data.vertices]

        min_x = min([b_vert[0] for b_vert in b_vert_list])
        min_y = min([b_vert[1] for b_vert in b_vert_list])
        min_z = min([b_vert[2] for b_vert in b_vert_list])
        max_x = max([b_vert[0] for b_vert in b_vert_list])
        max_y = max([b_vert[1] for b_vert in b_vert_list])
        max_z = max([b_vert[2] for b_vert in b_vert_list])

        if bsbound:
            n_bbox = ObjectHelper.create_block("BSBound")
            # ... the following incurs double scaling because it will be added in
            # both the extra data list and in the old extra data sequence!!!
            # block_parent.add_extra_data(n_bbox)
            # quick hack (better solution would be to make apply_scale non-recursive)
            block_parent.num_extra_data_list += 1
            block_parent.extra_data_list.update_size()
            block_parent.extra_data_list[-1] = n_bbox

            # set name, center, and dimensions
            n_bbox.name = "BBX"
            n_bbox.center.x = b_obj.location[0]
            n_bbox.center.y = b_obj.location[1]
            n_bbox.center.z = b_obj.location[2]
            n_bbox.dimensions.x = (max_x - min_x) * b_obj.scale[0] * 0.5
            n_bbox.dimensions.y = (max_y - min_y) * b_obj.scale[1] * 0.5
            n_bbox.dimensions.z = (max_z - min_z) * b_obj.scale[2] * 0.5

        else:
            n_bbox = ObjectHelper.create_ninode()
            block_parent.add_child(n_bbox)
            # set name, flags, translation, and radius
            n_bbox.name = "Bounding Box"
            n_bbox.flags = 4
            n_bbox.translation.x = (min_x + max_x) * 0.5 + b_obj.location[0]
            n_bbox.translation.y = (min_x + max_x) * 0.5 + b_obj.location[1]
            n_bbox.translation.z = (min_x + max_x) * 0.5 + b_obj.location[2]
            n_bbox.rotation.set_identity()
            n_bbox.has_bounding_box = True

            # Ninode's(n_bbox) behaves like a seperate mesh.
            # bounding_box center(n_bbox.bounding_box.translation) is relative to the bound_box
            n_bbox.bounding_box.translation.deepcopy(n_bbox.translation)
            n_bbox.bounding_box.rotation.set_identity()
            n_bbox.bounding_box.radius.x = (max_x - min_x) * 0.5
            n_bbox.bounding_box.radius.y = (max_y - min_y) * 0.5
            n_bbox.bounding_box.radius.z = (max_z - min_z) * 0.5
