"""This module contains helper methods to import/export object type data."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp


def create_ninode(b_obj=None):
    """Essentially a wrapper around create_block() that creates nodes of the right type"""
    # when no b_obj is passed, it means we create a root node
    if not b_obj:
        return block_store.create_block("NiNode")

    # get node type - some are stored as custom property of the b_obj
    try:
        n_node_type = b_obj["type"]
    except KeyError:
        n_node_type = "NiNode"

    # ...others by presence of constraints
    if has_track(b_obj):
        n_node_type = "NiBillboardNode"

    # now create the node
    n_node = block_store.create_block(n_node_type, b_obj)

    # customize the node data, depending on type
    if n_node_type == "NiLODNode":
        export_range_lod_data(n_node, b_obj)

    return n_node


def has_track(b_obj):
    """ Determine if this b_obj has a track_to constraint """
    # bones do not have constraints
    if not isinstance(b_obj, bpy.types.Bone):
        for constr in b_obj.constraints:
            if constr.type == 'TRACK_TO':
                return True


def export_range_lod_data(n_node, b_obj):
    """Export range lod data for for the children of b_obj, as a
    NiRangeLODData block on n_node.
    """
    # create range lod data object
    n_range_data = block_store.create_block("NiRangeLODData", b_obj)
    n_node.lod_level_data = n_range_data

    # get the children
    b_children = b_obj.children

    # set the data
    n_node.num_lod_levels = len(b_children)
    n_range_data.num_lod_levels = len(b_children)
    n_node.lod_levels.update_size()
    n_range_data.lod_levels.update_size()
    for b_child, n_lod_level, n_rd_lod_level in zip(b_children, n_node.lod_levels, n_range_data.lod_levels):
        n_lod_level.near_extent = b_child["near_extent"]
        n_lod_level.far_extent = b_child["far_extent"]
        n_rd_lod_level.near_extent = n_lod_level.near_extent
        n_rd_lod_level.far_extent = n_lod_level.far_extent


def export_furniture_marker(n_root, filebase):
    # oblivion and Fallout 3 furniture markers
    if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') and filebase[:15].lower() == 'furnituremarker':
        # exporting a furniture marker for Oblivion/FO3
        try:
            furniturenumber = int(filebase[15:])
        except ValueError:
            raise io_scene_niftools.utils.logging.NifError("Furniture marker has invalid number ({0}).\n"
                                     "Name your file 'furnituremarkerxx.nif' where xx is a number between 00 and 19.".format(filebase[15:]))

        # create furniture marker block
        furnmark = block_store.create_block("BSFurnitureMarker")
        furnmark.name = "FRN"
        furnmark.num_positions = 1
        furnmark.positions.update_size()
        furnmark.positions[0].position_ref_1 = furniturenumber
        furnmark.positions[0].position_ref_2 = furniturenumber

        # create extra string data sgoKeep
        sgokeep = block_store.create_block("NiStringExtraData")
        sgokeep.name = "UPB"  # user property buffer
        sgokeep.string_data = "sgoKeep=1 ExportSel = Yes"  # Unyielding = 0, sgoKeep=1ExportSel = Yes

        # add extra blocks
        n_root.add_extra_data(furnmark)
        n_root.add_extra_data(sgokeep)
