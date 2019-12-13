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

from io_scene_nif.utility.util_logging import NifLog


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
        vertices = [NifFormat.Vector3() for i in range(n_geom.data.num_vertices)]

        # ignore normals for now, not needed for import
        sum_weights = [0.0 for i in range(n_geom.data.num_vertices)]
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
                print("Vertex %i has weights not summing to one: %i" % (i, sum_weights[i]))

        return vertices

    @staticmethod
    def apply_skin_deformation(n_data):
        """ Process all geometries in NIF tree to apply their skin """
        # get all geometries with skin
        n_geoms = [g for g in n_data.get_global_iterator() if isinstance(g, NifFormat.NiGeometry) and g.is_skin()]

        # make sure that each skin is applied only once to avoid distortions when a model is referred to twice
        for n_geom in set(n_geoms):
            NifLog.info('Applying skin deformation on geometry {0}'.format(n_geom.name))
            skininst = n_geom.skin_instance
            skindata = skininst.data
            if skindata.has_vertex_weights:
                vertices = n_geom.get_skin_deformation()[0]
            else:
                NifLog.info("PYFFI does not support this type of skinning, so here's a workaround...")
                vertices = VertexGroup.get_skin_deformation_from_partition(n_geom)

            # finally we can actually set the data
            for vold, vnew in zip(n_geom.data.vertices, vertices):
                vold.x = vnew.x
                vold.y = vnew.y
                vold.z = vnew.z
