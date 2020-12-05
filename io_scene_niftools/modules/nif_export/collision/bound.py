"""Script to export collision bounds."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

import mathutils

from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export import types
from io_scene_niftools.modules.nif_export.collision import Collision
from io_scene_niftools.utils import math


class BSBound(Collision):

    def export_bounds(self, b_obj, block_parent, bsbound=False):
        """Export a Morrowind or Oblivion bounding box."""
        if bsbound:
            self.export_bsbound(b_obj, block_parent)
        else:
            self.export_bounding_box(b_obj, block_parent)

    # TODO [object][data] Stored as object property
    def export_bsbound(self, b_obj, block_parent):
        box_extends = self.calculate_box_extents(b_obj)
        n_bbox = block_store.create_block("BSBound")
        # ... the following incurs double scaling because it will be added in
        # both the extra data list and in the old extra data sequence!!!
        # block_parent.add_extra_data(n_bbox)
        # quick hack (better solution would be to make apply_scale non-recursive)
        block_parent.num_extra_data_list += 1
        block_parent.extra_data_list.update_size()
        block_parent.extra_data_list[-1] = n_bbox
        # set name, center, and dimensions
        n_bbox.name = "BBX"
        center = n_bbox.center
        center.x = b_obj.location[0]
        center.y = b_obj.location[1]
        center.z = b_obj.location[2]

        largest = self.calculate_largest_value(box_extends)
        dims = n_bbox.dimensions
        dims.x = largest[0]
        dims.y = largest[1]
        dims.z = largest[2]

    def export_bounding_box(self, b_obj, block_parent):
        box_extends = self.calculate_box_extents(b_obj)
        n_bbox = types.create_ninode()
        block_parent.add_child(n_bbox)
        # set name, flags, translation, and radius
        n_bbox.name = "Bounding Box"
        n_bbox.flags = 4

        trans = n_bbox.translation
        trans.x = (box_extends[0][0] + box_extends[0][1]) * 0.5 + b_obj.location[0]
        trans.y = (box_extends[1][0] + box_extends[1][1]) * 0.5 + b_obj.location[1]
        trans.z = (box_extends[2][0] + box_extends[2][1]) * 0.5 + b_obj.location[2]
        n_bbox.rotation.set_identity()
        n_bbox.has_bounding_box = True
        # Ninode's(n_bbox) behaves like a seperate mesh.
        # bounding_box center(n_bbox.bounding_box.trans) is relative to the bound_box
        n_bbox.bounding_box.translation.deepcopy(trans)
        n_bbox.bounding_box.rotation.set_identity()

        largest = self.calculate_largest_value(box_extends)
        radius = n_bbox.bounding_box.radius
        radius.x = largest[0]
        radius.y = largest[1]
        radius.z = largest[2]


class NiCollision(Collision):

    def export_nicollisiondata(self, b_obj, n_parent):
        """ Export b_obj as a NiCollisionData """
        n_coll_data = block_store.create_block("NiCollisionData", b_obj)
        n_coll_data.use_abv = 1
        n_coll_data.target = n_parent
        n_parent.collision_object = n_coll_data

        n_bv = n_coll_data.bounding_volume
        if b_obj.display_bounds_type == 'SPHERE':
            self.export_spherebv(b_obj, n_bv)
        elif b_obj.display_bounds_type == 'BOX':
            self.export_boxbv(b_obj, n_bv)
        elif b_obj.display_bounds_type == 'CAPSULE':
            self.export_capsulebv(b_obj, n_bv)

    def export_spherebv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume sphere """

        n_bv.collision_type = 0
        matrix = math.get_object_bind(b_obj)
        center = matrix.translation
        n_bv.sphere.radius = b_obj.dimensions.x / 2
        sphere_center = n_bv.sphere.center
        sphere_center.x = center.x
        sphere_center.y = center.y
        sphere_center.z = center.z

    def export_boxbv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume box """

        n_bv.collision_type = 1
        matrix = math.get_object_bind(b_obj)

        # set center
        center = matrix.translation
        box_center = n_bv.box.center
        box_center.x = center.x
        box_center.y = center.y
        box_center.z = center.z

        # set axes to unity 3x3 matrix
        axis = n_bv.box.axis
        axis[0].x = 1
        axis[1].y = 1
        axis[2].z = 1

        # set extent
        extent = b_obj.dimensions / 2
        box_extent = n_bv.box.extent
        box_extent[0] = extent.x
        box_extent[1] = extent.y
        box_extent[2] = extent.z

    def export_capsulebv(self, b_obj, n_bv):
        """ Export b_obj as a NiCollisionData's bounding_volume capsule """

        n_bv.collision_type = 2
        matrix = math.get_object_bind(b_obj)
        offset = matrix.translation
        # calculate the direction unit vector
        v_dir = (mathutils.Vector((0, 0, 1)) @ matrix.to_3x3().inverted()).normalized()
        extent = b_obj.dimensions.z - b_obj.dimensions.x
        radius = b_obj.dimensions.x / 2

        # store data
        capsule = n_bv.capsule

        center = capsule.center
        center.x = offset.x
        center.y = offset.y
        center.z = offset.z

        origin = capsule.origin
        origin.x = v_dir.x
        origin.y = v_dir.y
        origin.z = v_dir.z

        # TODO [collision] nb properly named in newer nif.xmls
        capsule.unknown_float_1 = extent
        capsule.unknown_float_2 = radius
