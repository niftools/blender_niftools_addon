"""Module for unit testing that the utility module"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
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


import nose
from nose.tools import nottest

import mathutils
import math

from io_scene_nif.utils import util_math

from pyffi.formats.nif import NifFormat


@nottest
class TestMatrixOperations:
    # Read docs/development/issues.rst for more info on matrix conversions.

    @classmethod
    def setup_class(cls):
        print(f"Class setup: {cls:s}")

        cls.reinitialise()

    @classmethod
    def teardown_class(cls):
        print(f"Class Teardown: {cls:s}")

        del cls.niBlock
        del cls.nif_matrix
        del cls.blender_matrix

    @classmethod
    def setup(cls):
        print("Method setup")

        cls.nif_matrix = cls.build_nif_matrix()

        cls.niBlock = NifFormat.NiNode()
        cls.niBlock.set_transform(cls.nif_matrix)

        cls.blender_matrix = cls.build_blender_matrix()

    @classmethod
    def teardown(cls):
        cls.reinitialise()

    @classmethod
    def reinitialise(cls):
        cls.nif_matrix = None
        cls.niBlock = None
        cls.blender_matrix = None

    def test_import_matrix(self):
        converted_mat = util_math.import_matrix(self.niBlock)

        print("Comparing Matrices:")
        for row in range(0, 4):
            for col in range(0, 4):
                print(f"{row:s} : {col:s} ="
                      f"{converted_mat['row']['col']:s} : {self.blender_matrix['row']['col']:s}")
                nose.tools.assert_true(converted_mat[row][col] - self.blender_matrix[row][col]
                                       < NifFormat.EPSILON)

    def test_matrix_decompose_srt(self):
        pass

    @classmethod
    def build_blender_matrix(cls):
        translation = (2.0, 3.0, 4.0)
        scale = 2

        # Blender matrix
        b_loc_vec = mathutils.Vector(translation)
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)

        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X')
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
        b_rot_mat = b_rot_mat_x * b_rot_mat_y * b_rot_mat_z

        b_scale_mat = mathutils.Matrix.Scale(scale, 4)
        b_matrix = b_scale_mat * b_rot_mat * b_loc_vec

        # print(b_matrix)

        # (-0.0000, -0.2812,  0.4871, 20.0000)
        # ( 0.4871, -0.2436, -0.1406, 20.0000)
        # ( 0.2812,  0.4219,  0.2436, 20.0000)
        # ( 0.0000,  0.0000,  0.0000,  1.0000)

        return b_matrix

    @classmethod
    def build_nif_matrix(cls):

        n_mat = NifFormat.Matrix44()
        translation = (2.0, 3.0, 4.0)
        scale = 2.0

        n_rhs_rot_x = (1.0, 0.0, 0.0,
                       0.0, 0.866, 0.5,
                       0.0, -0.5, 0.866)

        n_rhs_rot_y = (0.5, 0.0, -0.866,
                       0.0, 1.0, 0.0,
                       0.866, 0.0, 0.5)

        n_rhs_rot_z = (0, 1, 0,
                       -1, 0, 0,
                       0, 0, 1)

        n_rhs_rot_x = cls.create_matrix(n_rhs_rot_x)
        n_rhs_rot_y = cls.create_matrix(n_rhs_rot_y)
        n_rhs_rot_z = cls.create_matrix(n_rhs_rot_z)

        n_mat33 = n_rhs_rot_z * n_rhs_rot_y * n_rhs_rot_x

        n_vec3 = NifFormat.Vector3()
        n_vec3.x = translation[0]
        n_vec3.y = translation[1]
        n_vec3.z = translation[2]

        n_mat.set_scale_rotation_translation(scale, n_mat33, n_vec3)

        return n_mat

    @classmethod
    def create_matrix(cls, element):
        n_mat33 = NifFormat.Matrix33()
        n_mat33.m_11 = element[0]
        n_mat33.m_12 = element[1]
        n_mat33.m_13 = element[2]
        n_mat33.m_21 = element[3]
        n_mat33.m_22 = element[4]
        n_mat33.m_23 = element[5]
        n_mat33.m_31 = element[6]
        n_mat33.m_32 = element[7]
        n_mat33.m_33 = element[8]

        return n_mat33


class TestFindBlockProperties:
    """Tests find_property method"""

    ni_texture_prop = None
    ni_mat_prop1 = None
    ni_mat_prop = None
    n_ninode = None

    @classmethod
    def setup_class(cls):
        print(f"Class setup: {cls:s}")
        cls.ni_mat_prop = NifFormat.NiMaterialProperty()
        cls.ni_mat_prop1 = NifFormat.NiMaterialProperty()
        cls.ni_texture_prop = NifFormat.NiTexturingProperty()

    @classmethod
    def teardown_class(cls):
        print(f"Class teardown: {cls:s}")
        del cls.ni_mat_prop
        del cls.ni_mat_prop1
        del cls.ni_texture_prop
        del cls.n_ninode
        print(str(cls))

    @classmethod
    def setup(cls):
        print("Method setup: ")
        cls.n_ninode = NifFormat.NiNode()

    @classmethod
    def teardown(cls):
        print("Method teardown: ")
        cls.n_ninode = None

    def test_find_no_prop(self):
        """Expect None, no proterty"""
        prop = util_math.find_property(self.n_ninode, NifFormat.NiMaterialProperty)
        nose.tools.assert_true((prop is None))

    def test_find_property_no_matching(self):
        """Expect None, no matching property"""
        self.n_ninode.add_property(self.ni_texture_prop)
        nose.tools.assert_equals(self.n_ninode.num_properties, 1)

        prop = util_math.find_property(self.n_ninode, NifFormat.NiMaterialProperty)
        nose.tools.assert_true(prop is None)

    def test_find_property(self):
        """Expect to find first instance of property"""
        self.n_ninode.add_property(self.ni_texture_prop)
        self.n_ninode.add_property(self.ni_mat_prop)
        self.n_ninode.add_property(self.ni_mat_prop1)
        nose.tools.assert_equals(self.n_ninode.num_properties, 3)

        prop = util_math.find_property(self.n_ninode, NifFormat.NiMaterialProperty)
        nose.tools.assert_true(prop == self.ni_mat_prop)
