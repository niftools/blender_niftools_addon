"""This script contains helper methods to import skin data."""

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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.obj import object_import


class Skin:

    @staticmethod
    def process_geometry_skin(b_obj, n_block, skininst, v_map):
        skindata = skininst.data
        bones = skininst.bones
        bone_weights = skindata.bone_list
        for idx, bone in enumerate(bones):
            # skip empty bones (see pyffi issue #3114079)
            if not bone:
                continue
            vertex_weights = bone_weights[idx].vertex_weights
            groupname = object_import.DICT_NAMES[bone]
            if groupname not in b_obj.vertex_groups.items():
                v_group = b_obj.vertex_groups.new(groupname)
            for skinWeight in vertex_weights:
                vert = skinWeight.index
                weight = skinWeight.weight
                v_group.add([v_map[vert]], weight, 'REPLACE')

        # TODO [geometry]
        # import body parts as vertex groups
        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
            skinpart_list = []
            bodypart_flag = []
            skinpart = n_block.get_skin_partition()
            for bodypart, skinpartblock in zip(skininst.partitions, skinpart.skin_partition_blocks):
                bodypart_wrap = NifFormat.BSDismemberBodyPartType()
                bodypart_wrap.set_value(bodypart.body_part)
                groupname = bodypart_wrap.get_detail_display()
                # create vertex group if it did not exist yet
                if not (groupname in b_obj.vertex_groups.items()):
                    v_group = b_obj.vertex_groups.new(groupname)
                    skinpart_index = len(skinpart_list)
                    skinpart_list.append((skinpart_index, groupname))
                    bodypart_flag.append(bodypart.part_flag)

                # find vertex indices of this group
                groupverts = [v_map[v_index] for v_index in skinpartblock.vertex_map]
                # create the group
                v_group.add(groupverts, 1, 'ADD')

            b_obj.niftools_part_flags_panel.pf_partcount = len(skinpart_list)
            for i, pl_name in skinpart_list:
                b_obj_partflag = b_obj.niftools_part_flags.add()
                # b_obj.niftools_part_flags.pf_partint = (i)
                b_obj_partflag.name = pl_name
                b_obj_partflag.pf_editorflag = bodypart_flag[i].pf_editor_visible
                b_obj_partflag.pf_startflag = bodypart_flag[i].pf_start_net_boneset
