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
        
        # dictionary of bones, maps Blender bone name to matrix that maps the
        # NIF bone matrix on the Blender bone matrix
        # Recall from the import script
        #   B' = X * B,
        # where B' is the Blender bone matrix, and B is the NIF bone matrix,
        # both in armature space. So to restore the NIF matrices we need to do
        #   B = X^{-1} * B'
        # Hence, we will restore the X's, invert them, and store those inverses in the
        # following dictionary.
        self.nif_common.bones_extra_matrix_inv = {}
        
    def rebuild_bones_extra_matrices(self):
        """Recover bone extra matrices."""
        
        try:
            bonetxt = bpy.data.texts["BoneExMat"]
        except NameError:
            return
        # Blender bone names are unique so we can use them as keys.
        for b_textline in bonetxt.lines:
            line = b_textline.body
            if len(line)>0:
                # reconstruct matrix from text
                b, m = line.split('/')
                try:
                    matrix = mathutils.Matrix(
                        [[float(f) for f in row.split(',')]
                         for row in m.split(';')])
                except:
                    raise NifExportError('Syntax error in BoneExMat buffer.')
                # Check if matrices are clean, and if necessary fix them.
                quat = matrix.rotationPart().toQuat()
                if sum(sum(abs(x) for x in vec)
                       for vec in matrix.rotationPart() - quat.toMatrix()) > 0.01:
                    self.warning(
                        "Bad bone extra matrix for bone %s. \n"
                        "Attempting to fix... but bone transform \n"
                        "may be incompatible with existing animations." % b)
                    self.warning("old invalid matrix:\n%s" % matrix)
                    trans = matrix.translationPart()
                    matrix = quat.toMatrix().resize4x4()
                    matrix[3][0] = trans[0]
                    matrix[3][1] = trans[1]
                    matrix[3][2] = trans[2]
                    self.warning("new valid matrix:\n%s" % matrix)
                # Matrices are stored inverted for easier math later on.
                matrix.invert()
                self.set_bone_extra_matrix_inv(b, matrix)
                
    def set_bone_extra_matrix_inv(self, bonename, mat):
        """Set bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        self.nif_common.bones_extra_matrix_inv[self.nif_common.get_bone_name_for_blender(bonename)] = mat

    def get_bone_extra_matrix_inv(self, bonename):
        """Get bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        return self.nif_common.bones_extra_matrix_inv[self.nif_common.get_bone_name_for_blender(bonename)]
    
    
    def export_bones(self, arm, parent_block):
        """Export the bones of an armature."""
        # the armature was already exported as a NiNode
        # now we must export the armature's bones
        assert( arm.type == 'ARMATURE' )

        # find the root bones
        # dictionary of bones (name -> bone)
        bones = dict(list(arm.data.bones.items()))
        root_bones = []
        for root_bone in list(bones.values()):
            while root_bone.parent in list(bones.values()):
                root_bone = root_bone.parent
            if root_bones.count(root_bone) == 0:
                root_bones.append(root_bone)

        if (bpy.types.Action(arm)):
            bones_ipo = bpy.types.ActionGroups(arm) # dictionary of Bone Ipos (name -> ipo)
        else:
            bones_ipo = {} # no ipos

        bones_node = {} # maps bone names to NiNode blocks

        # here all the bones are added
        # first create all bones with their keyframes
        # and then fix the links in a second run

        # ok, let's create the bone NiNode blocks
        for bone in list(bones.values()):
            # create a new block for this bone
            node = self.nif_common.create_ninode(bone)
            # doing bone map now makes linkage very easy in second run
            bones_node[bone.name] = node

            # add the node and the keyframe for this bone
            node.name = self.nif_common.get_full_name(bone.name).encode()
            if self.nif_common.properties.game in ('OBLIVION', 'FALLOUT_3'):
                # default for Oblivion bones
                # note: bodies have 0x000E, clothing has 0x000F
                node.flags = 0x000E
            elif self.nif_common.properties.game in ('CIVILIZATION_IV', 'EMPIRE_EARTH_II'):
                if bone.children:
                    # default for Civ IV/EE II bones with children
                    node.flags = 0x0006
                else:
                    # default for Civ IV/EE II final bones
                    node.flags = 0x0016
            elif self.nif_common.properties.game in ('DIVINITY_2',):
                if bone.children:
                    # default for Div 2 bones with children
                    node.flags = 0x0186
                elif bone.name.lower()[-9:] == 'footsteps':
                    node.flags = 0x0116
                else:
                    # default for Div 2 final bones
                    node.flags = 0x0196
            else:
                node.flags = 0x0002 # default for Morrowind bones
            self.nif_common.export_matrix(bone, 'localspace', node) # rest pose

            # bone rotations are stored in the IPO relative to the rest position
            # so we must take the rest position into account
            # (need original one, without extra transforms, so extra = False)
            bonerestmat = self.get_bone_rest_matrix(bone, 'BONESPACE',
                                                    extra = False)
            try:
                bonexmat_inv = mathutils.Matrix(
                    self.get_bone_extra_matrix_inv(bone.name))
            except KeyError:
                bonexmat_inv = mathutils.Matrix()
                bonexmat_inv.identity()
            if bone.name in bones_ipo:
                self.nif_common.export_keyframes(
                    bones_ipo[bone.name], 'localspace', node,
                    bind_matrix = bonerestmat, extra_mat_inv = bonexmat_inv)

            # does bone have priority value in NULL constraint?
            for constr in arm.pose.bones[bone.name].constraints:
                # yes! store it for reference when creating the kf file
                if constr.name[:9].lower() == "priority:":
                    self.nif_common.bone_priorities[
                        self.get_bone_name_for_nif(bone.name)
                        ] = int(constr.name[9:])

        # now fix the linkage between the blocks
        for bone in list(bones.values()):
            # link the bone's children to the bone
            if bone.children:
                self.nif_common.debug("Linking children of bone %s" % bone.name)
                for child in bone.children:
                    # bone.children returns also grandchildren etc.
                    # we only want immediate children, so do a parent check
                    if child.parent.name == bone.name:
                        bones_node[bone.name].add_child(bones_node[child.name])
            # if it is a root bone, link it to the armature
            if not bone.parent:
                parent_block.add_child(bones_node[bone.name])
                
    
    def export_children(self, b_obj, parent_block):
        """Export all children of blender object b_obj as children of
        parent_block."""
        # loop over all obj's children
        for b_obj_child in b_obj.children:
            # is it a regular node?
            if b_obj_child.type in ['MESH', 'EMPTY', 'ARMATURE']:
                if (b_obj.type != 'ARMATURE'):
                    # not parented to an armature
                    self.nif_common.export_node(b_obj_child, 'localspace',
                                     parent_block, b_obj_child.name)
                else:
                    # this object is parented to an armature
                    # we should check whether it is really parented to the
                    # armature using vertex weights
                    # or whether it is parented to some bone of the armature
                    parent_bone_name = b_obj_child.parent_bone
                    if parent_bone_name is None:
                        self.nif_common.export_node(b_obj_child, 'localspace',
                                         parent_block, b_obj_child.name)
                    else:
                        # we should parent the object to the bone instead of
                        # to the armature
                        # so let's find that bone!
                        nif_bone_name = self.nif_common.get_full_name(parent_bone_name)
                        for bone_block in self.nif_common.blocks:
                            if isinstance(bone_block, NifFormat.NiNode) and \
                                bone_block.name.decode() == nif_bone_name:
                                # ok, we should parent to block
                                # instead of to parent_block
                                # two problems to resolve:
                                #   - blender bone matrix is not the exported
                                #     bone matrix!
                                #   - blender objects parented to bone have
                                #     extra translation along the Y axis
                                #     with length of the bone ("tail")
                                # this is handled in the get_object_srt function
                                self.nif_common.export_node(b_obj_child, 'localspace',
                                                 bone_block, b_obj_child.name)
                                break
                        else:
                            assert(False) # BUG!
                            
                            
    def get_bone_rest_matrix(self, bone, space, extra = True, tail = False):
        """Get bone matrix in rest position ("bind pose"). Space can be
        ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
        is BONESPACE (translation is bone head plus tail from parent bone).
        If tail is True then the matrix translation includes the bone tail."""
        # Retrieves the offset from the original NIF matrix, if existing
        corrmat = mathutils.Matrix()
        if extra:
            try:
                corrmat = mathutils.Matrix(
                    self.get_bone_extra_matrix_inv(bone.name))
            except KeyError:
                corrmat.identity()
        else:
            corrmat.identity()
        if (space == 'ARMATURESPACE'):
            matrix = mathutils.Matrix(bone.matrix_local)
            if tail:
                tail_pos = bone.tail_local
                matrix[0][3] = tail_pos[0]
                matrix[1][3] = tail_pos[1]
                matrix[2][3] = tail_pos[2]
            return corrmat * matrix
        elif (space == 'BONESPACE'):
            if bone.parent:
                # not sure why extra = True is required here
                # but if extra = extra then transforms are messed up, so keep
                # for now
                parinv = self.get_bone_rest_matrix(bone.parent, 'ARMATURESPACE',
                                                   extra = True, tail = False)
                parinv.invert()
                return self.get_bone_rest_matrix(bone,
                                                 'ARMATURESPACE',
                                                 extra = extra,
                                                 tail = tail) * parinv
            else:
                return self.get_bone_rest_matrix(bone, 'ARMATURESPACE',
                                                 extra = extra, tail = tail)
        else:
            assert(False) # bug!


