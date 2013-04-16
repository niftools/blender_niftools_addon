'''Script to import/export all the skeleton related objects.'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
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

import os

import bpy
import mathutils

from pyffi.formats.nif import NifFormat

class Armature():
    
    
    def __init__(self, parent):
        self.nif_common = parent
        
    
    def rebuild_bones_extra_matrices(self):
        """Recover bone extra matrices."""
        
        try:
            bonetxt = Blender.Text.Get('BoneExMat')
        except NameError:
            return
        # Blender bone names are unique so we can use them as keys.
        for ln in bonetxt.asLines():
            if len(ln)>0:
                # reconstruct matrix from text
                b, m = ln.split('/')
                try:
                    mat = mathutils.Matrix(
                        [[float(f) for f in row.split(',')]
                         for row in m.split(';')])
                except:
                    raise NifExportError('Syntax error in BoneExMat buffer.')
                # Check if matrices are clean, and if necessary fix them.
                quat = mat.rotationPart().toQuat()
                if sum(sum(abs(x) for x in vec)
                       for vec in mat.rotationPart() - quat.toMatrix()) > 0.01:
                    self.warning(
                        "Bad bone extra matrix for bone %s. \n"
                        "Attempting to fix... but bone transform \n"
                        "may be incompatible with existing animations." % b)
                    self.warning("old invalid matrix:\n%s" % mat)
                    trans = mat.translationPart()
                    mat = quat.toMatrix().resize4x4()
                    mat[3][0] = trans[0]
                    mat[3][1] = trans[1]
                    mat[3][2] = trans[2]
                    self.warning("new valid matrix:\n%s" % mat)
                # Matrices are stored inverted for easier math later on.
                mat.invert()
                self.set_bone_extra_matrix_inv(b, mat)
                
    def set_bone_extra_matrix_inv(self, bonename, mat):
        """Set bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        self.bones_extra_matrix_inv[self.get_bone_name_for_blender(bonename)] = mat

    def get_bone_extra_matrix_inv(self, bonename):
        """Get bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        return self.bones_extra_matrix_inv[self.get_bone_name_for_blender(bonename)]