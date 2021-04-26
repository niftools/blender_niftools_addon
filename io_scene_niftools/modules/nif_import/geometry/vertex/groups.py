"""This script contains helper methods to import vertex weighted data."""

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
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import.object.block_registry import block_store
from io_scene_niftools.utils.logging import NifLog


class VertexGroup:
    """Class that maps weighted vertices to specific groups"""

    @staticmethod
    def get_skin_deformation_from_partition(n_geom):
        """ Workaround because pyffi does not support this skinning method """

        # todo [pyffi] integrate this into pyffi!!!
        #              so that NiGeometry.get_skin_deformation() deals with this as intended

        # mostly a copy from pyffi...
        skin_inst = n_geom.skin_instance
        skin_data = skin_inst.data
        skin_partition = skin_inst.skin_partition
        skel_root = skin_inst.skeleton_root
        vertices = [NifFormat.Vector3() for _ in range(n_geom.data.num_vertices)]

        # ignore normals for now, not needed for import
        sum_weights = [0.0 for _ in range(n_geom.data.num_vertices)]
        skin_offset = skin_data.get_transform()

        # store one transform per bone
        bone_transforms = []
        for i, bone_block in enumerate(skin_inst.bones):
            bone_data = skin_data.bone_list[i]
            bone_offset = bone_data.get_transform()
            bone_matrix = bone_block.get_transform(skel_root)
            transform = bone_offset * bone_matrix * skin_offset
            bone_transforms.append(transform)

        # now the actual unique bit
        for block in skin_partition.skin_partition_blocks:
            # create all vgroups for this block's bones
            block_bone_transforms = [bone_transforms[i] for i in block.bones]

            # go over each vert in this block
            for vert_index, vertex_weights, bone_indices in zip(block.vertex_map, block.vertex_weights, block.bone_indices):
                # skip verts that were already processed in an earlier block
                if sum_weights[vert_index] != 0:
                    continue

                # go over all 4 weight / bone pairs and transform this vert
                for weight, b_i in zip(vertex_weights, bone_indices):
                    if weight > 0:
                        transform = block_bone_transforms[b_i]
                        vertices[vert_index] += weight * (n_geom.data.vertices[vert_index] * transform)
                        sum_weights[vert_index] += weight

        for i, s in enumerate(sum_weights):
            if abs(s - 1.0) > 0.01:
                print(f"Vertex {i:d} has weights not summing to one: {sum_weights['i']:d}")

        return vertices

    @staticmethod
    def apply_skin_deformation(n_data):
        """ Process all geometries in NIF tree to apply their skin """
        # get all geometries with skin
        n_geoms = [g for g in n_data.get_global_iterator() if isinstance(g, NifFormat.NiGeometry) and g.is_skin()]

        # make sure that each skin is applied only once to avoid distortions when a model is referred to twice
        for n_geom in set(n_geoms):
            NifLog.info(f'Applying skin deformation on geometry {n_geom.name}')
            skininst = n_geom.skin_instance
            skindata = skininst.data
            if skindata.has_vertex_weights:
                vertices = n_geom.get_skin_deformation()[0]
            else:
                NifLog.info("PyFFI does not support this type of skinning, so here's a workaround...")
                vertices = VertexGroup.get_skin_deformation_from_partition(n_geom)

            # finally we can actually set the data
            for vold, vnew in zip(n_geom.data.vertices, vertices):
                vold.x = vnew.x
                vold.y = vnew.y
                vold.z = vnew.z

    @staticmethod
    def import_skin(ni_block, b_obj):
        """Import a NiSkinInstance and its contents as vertex groups"""
        skininst = ni_block.skin_instance
        if skininst:
            skindata = skininst.data
            bones = skininst.bones
            # the usual case
            if skindata.has_vertex_weights:
                bone_weights = skindata.bone_list
                for idx, n_bone in enumerate(bones):
                    # skip empty bones (see pyffi issue #3114079)
                    if not n_bone:
                        continue

                    vertex_weights = bone_weights[idx].vertex_weights
                    group_name = block_store.import_name(n_bone)
                    if group_name not in b_obj.vertex_groups:
                        v_group = b_obj.vertex_groups.new(name=group_name)

                    for skinWeight in vertex_weights:
                        vert = skinWeight.index
                        weight = skinWeight.weight
                        v_group.add([vert], weight, 'REPLACE')

            # WLP2 - hides the weights in the partition
            else:
                skin_partition = skininst.skin_partition
                for block in skin_partition.skin_partition_blocks:
                    # create all vgroups for this block's bones
                    block_bone_names = [block_store.import_name(bones[i]) for i in block.bones]
                    for group_name in block_bone_names:
                        b_obj.vertex_groups.new(name=group_name)

                    # go over each vert in this block
                    for vert, vertex_weights, bone_indices in zip(block.vertex_map, block.vertex_weights, block.bone_indices):

                        # assign this vert's 4 weights to its 4 vgroups (at max)
                        for w, b_i in zip(vertex_weights, bone_indices):
                            if w > 0:
                                group_name = block_bone_names[b_i]
                                v_group = b_obj.vertex_groups[group_name]
                                v_group.add([vert], w, 'REPLACE')

        # import body parts as vertex groups
        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
            skinpart_list = []
            bodypart_flag = []
            skinpart = ni_block.get_skin_partition()
            for bodypart, skinpartblock in zip(skininst.partitions, skinpart.skin_partition_blocks):
                bodypart_wrap = NifFormat.BSDismemberBodyPartType()
                bodypart_wrap.set_value(bodypart.body_part)
                group_name = bodypart_wrap.get_detail_display()

                # create vertex group if it did not exist yet
                if group_name not in b_obj.vertex_groups:
                    v_group = b_obj.vertex_groups.new(name=group_name)
                    skinpart_index = len(skinpart_list)
                    skinpart_list.append((skinpart_index, group_name))
                    bodypart_flag.append(bodypart.part_flag)

                # find vertex indices of this group
                groupverts = [v_index for v_index in skinpartblock.vertex_map]

                # create the group
                v_group.add(groupverts, 1, 'ADD')
