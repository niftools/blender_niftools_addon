"""This script contains classes to export collision objects."""

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


class Collision:

    @staticmethod
    def calculate_largest_value(box_extends):
        return ((box_extends[0][1] - box_extends[0][0]) * 0.5,
                (box_extends[1][1] - box_extends[1][0]) * 0.5,
                (box_extends[2][1] - box_extends[2][0]) * 0.5)

    @staticmethod
    def calculate_box_extents(b_obj):
        # calculate bounding box extents
        b_vertlist = [vert.co for vert in b_obj.data.vertices]
        minx = min([b_vert[0] for b_vert in b_vertlist])
        maxx = max([b_vert[0] for b_vert in b_vertlist])
        maxy = max([b_vert[1] for b_vert in b_vertlist])
        miny = min([b_vert[1] for b_vert in b_vertlist])
        minz = min([b_vert[2] for b_vert in b_vertlist])
        maxz = max([b_vert[2] for b_vert in b_vertlist])
        return [[minx, maxx], [miny, maxy], [minz, maxz]]