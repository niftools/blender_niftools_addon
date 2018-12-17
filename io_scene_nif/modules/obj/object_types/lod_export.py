"""This script contains helper methods to export objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2018, NIF File Format Library and Tools contributors.
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


def export_range_lod_data(n_node, b_obj):
    """Export range lod data for for the children of b_obj, as an NiRangeLODData block on n_node."""

    # create range lod data object
    n_range_data = ObjectHelper.create_block("NiRangeLODData", b_obj)
    n_node.lod_level_data = n_range_data

    # get the children
    b_children = b_obj.children

    # set the data
    n_node.num_lod_levels = len(b_children)
    n_range_data.num_lod_levels = len(b_children)
    n_node.lod_levels.update_size()
    n_range_data.lod_levels.update_size()
    for b_child, n_lod_level, n_rd_lod_level in zip(b_children, n_node.lod_levels, n_range_data.lod_levels):
        n_lod_level.near_extent = b_child.getProperty("Near Extent").data
        n_lod_level.far_extent = b_child.getProperty("Far Extent").data
        n_rd_lod_level.near_extent = n_lod_level.near_extent
        n_rd_lod_level.far_extent = n_lod_level.far_extent
