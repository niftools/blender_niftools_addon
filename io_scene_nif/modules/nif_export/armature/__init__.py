"""Script to import/export all the skeleton related objects."""

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
import bpy
from io_scene_nif.modules.nif_export import types
from io_scene_nif.modules.nif_export.animation.transform import TransformAnimation
from io_scene_nif.modules.nif_export.block_registry import block_store
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_global import NifOp
from io_scene_nif.utils.util_logging import NifLog


def get_bind_data(b_armature):
    """Get the required bind data of an armature. Used by standalone KF import and export. """
    if b_armature:
        bind_data = {}
        for b_bone in b_armature.data.bones:
            n_bone_bind_scale, n_bone_bind_rot, n_bone_bind_trans = util_math.decompose_srt(util_math.get_bind_matrix(b_bone))
            bind_data[b_bone.name] = (n_bone_bind_scale, n_bone_bind_rot.inverted(), n_bone_bind_trans)
        return bind_data


class Armature:

    def __init__(self):
        self.transform_anim = TransformAnimation()

    def export_bones(self, b_obj, parent_block):
        """Export the bones of an armature."""
        # the armature was already exported as a NiNode
        # now we must export the armature's bones
        assert (b_obj.type == 'ARMATURE')

        b_action = self.transform_anim.get_active_action(b_obj)

        # find the root bones
        # list of all bones
        bones = b_obj.data.bones.values()

        # maps b_bone names to NiNode blocks
        bones_node = {}

        # here all the bones are added
        # first create all bones with their keyframes
        # and then fix the links in a second run

        # ok, let's create the b_bone NiNode blocks
        for b_bone in bones:
            # create a new nif block for this b_bone
            n_bone = types.create_ninode(b_bone)
            # doing b_bone map now makes linkage very easy in second run
            bones_node[b_bone.name] = n_bone

            # add the n_bone and the keyframe for this b_bone
            n_bone.name = block_store.get_full_name(b_bone)

            if b_bone.niftools.flags != 0:
                n_bone.flags = b_bone.niftools.flags
            else:
                if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    # default for Oblivion bones
                    # note: bodies have 0x000E, clothing has 0x000F
                    n_bone.flags = 0x000E
                elif bpy.context.scene.niftools_scene.game in ('CIVILIZATION_IV', 'EMPIRE_EARTH_II'):
                    if b_bone.children:
                        # default for Civ IV/EE II bones with children
                        n_bone.flags = 0x0006
                    else:
                        # default for Civ IV/EE II final bones
                        n_bone.flags = 0x0016
                elif bpy.context.scene.niftools_scene.game in ('DIVINITY_2',):
                    if b_bone.children:
                        # default for Div 2 bones with children
                        n_bone.flags = 0x0186
                    elif b_bone.name.lower()[-9:] == 'footsteps':
                        n_bone.flags = 0x0116
                    else:
                        # default for Div 2 final bones
                        n_bone.flags = 0x0196
                else:
                    n_bone.flags = 0x0002  # default for Morrowind bones
            # rest pose
            util_math.set_object_matrix(b_bone, n_bone)

            # per-bone animation
            self.transform_anim.export_transforms(n_bone, b_obj, b_action, b_bone)

        # now fix the linkage between the blocks
        for b_bone in bones:
            # link the bone's children to the bone
            NifLog.debug("Linking children of b_bone {0}".format(b_bone.name))
            for child in b_bone.children:
                bones_node[b_bone.name].add_child(bones_node[child.name])
            # if it is a root bone, link it to the armature
            if not b_bone.parent:
                parent_block.add_child(bones_node[b_bone.name])
