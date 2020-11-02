"""This script contains classes to import collision objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2012, NIF File Format Library and Tools contributors.
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
import mathutils

from io_scene_niftools.modules.nif_import import collision


HAVOK_SCALE = 6.996

# dictionary mapping bhkRigidBody objects to objects imported in Blender;
# we use this dictionary to set the physics constraints (ragdoll etc)
DICT_HAVOK_OBJECTS = {}


def get_material(mat_name):
    """Returns material of mat_name, create new one if required"""
    if mat_name not in bpy.data.materials:
        bpy.data.materials.new(mat_name)
    return bpy.data.materials[mat_name]


class Collision:
    """Import basic and Havok Collision Shapes"""

    @staticmethod
    def center_origin_to_matrix(n_center, n_dir):
        """Helper for capsules to transform nif data into a local matrix """
        # get the rotation that makes (1,0,0) match m_dir
        m_dir = mathutils.Vector((n_dir.x, n_dir.y, n_dir.z)).normalized()
        rot = m_dir.to_track_quat("Z", "Y").to_matrix().to_4x4()
        rot.translation = (n_center.x, n_center.y, n_center.z)
        return rot

    @staticmethod
    def set_b_collider(b_obj, radius, n_obj=None, bounds_type='BOX', display_type='BOX'):
        """Helper function to set up b_obj so it becomes recognizable as a collision object"""
        # set bounds type
        b_obj.show_bounds = True
        b_obj.display_type = 'BOUNDS'
        b_obj.display_bounds_type = display_type

        override = bpy.context.copy()
        override['selected_objects'] = b_obj
        bpy.ops.rigidbody.object_add(override)
        # viable alternative:
        # bpy.context.view_layer.objects.active = b_col_obj
        # bpy.ops.rigidbody.object_add(type='PASSIVE')

        b_r_body = b_obj.rigid_body
        b_r_body.enabled = True
        b_r_body.use_margin = True
        b_r_body.collision_margin = radius
        b_r_body.collision_shape = bounds_type
        # if they are set to active they explode once you play back an anim
        b_r_body.type = "PASSIVE"

        b_me = b_obj.data
        if n_obj:
            # todo [pyffi] nif xml 0.7.1.1 HavokMaterial is a union of 3 enums under the HavokMaterial.material field, probably broken!
            #              needs union support on pyffi end
            for mat_type in ("material", "oblivion_havok_material", "fallout_3_havok_material", "skyrim_havok_material"):
                havok_material = getattr(n_obj, mat_type, None)
                if havok_material:
                    if hasattr(havok_material, "material"):
                        # HavokMaterial.material is an enum under the hood
                        # pyffi exposes it as an int (struct.get_basic_attribute) and returns the enum's default value
                        # we treat it as if it was non-basic to get the enum itself
                        mat_enum = havok_material.get_attribute("material")
                        mat_name = str(mat_enum)
                    else:
                        # fallback, not sure if we should do this
                        mat_name = str(havok_material)
                    b_mat = get_material(mat_name)
                    b_me.materials.append(b_mat)
