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
from io_scene_niftools.modules.nif_export import types
from io_scene_niftools.modules.nif_export.animation.transform import TransformAnimation
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog


def get_bind_data(b_armature):
    """Get the required bind data of an armature. Used by standalone KF import and export. """
    if b_armature:
        bind_data = {}
        for b_bone in b_armature.data.bones:
            n_bone_bind_scale, n_bone_bind_rot, n_bone_bind_trans = math.decompose_srt(math.get_bind_matrix(b_bone))
            bind_data[b_bone.name] = (n_bone_bind_scale, n_bone_bind_rot.inverted(), n_bone_bind_trans)
        return bind_data


class Armature:

    def __init__(self):
        self.transform_anim = TransformAnimation()
        self.b_action = None

    def export_bones(self, b_obj, n_root_node):
        """Export all bones of an armature."""
        assert (b_obj.type == 'ARMATURE')

        self.b_action = self.transform_anim.get_active_action(b_obj)
        # the armature b_obj was already exported as a NiNode ("Scene Root") n_root_node
        # export the bones as NiNodes, starting from root bones
        for b_bone in b_obj.data.bones.values():
            if not b_bone.parent:
                self.export_bone(b_obj, b_bone, n_root_node)

    def export_bone(self, b_obj, b_bone, n_parent_node):
        """Exports a bone and all of its children."""
        # create a new nif block for this b_bone
        n_node = types.create_ninode(b_bone)
        n_node.name = block_store.get_full_name(b_bone)
        # link to nif parent node
        n_parent_node.add_child(n_node)

        self.export_bone_flags(b_bone, n_node)
        # rest pose
        math.set_object_matrix(b_bone, n_node)

        # per-bone animation
        self.transform_anim.export_transforms(n_node, b_obj, self.b_action, b_bone)
        # continue down the bone tree
        for b_child in b_bone.children:
            self.export_bone(b_obj, b_child, n_node)

    def export_bone_flags(self, b_bone, n_node):
        """Exports or sets the flags according to the custom data in b_bone or the game version if none was set"""
        if b_bone.niftools.flags != 0:
            n_node.flags = b_bone.niftools.flags
        else:
            game = bpy.context.scene.niftools_scene.game
            if game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                # default for Oblivion bones
                # note: bodies have 0x000E, clothing has 0x000F
                n_node.flags = 0x000E
            elif game in ('CIVILIZATION_IV', 'EMPIRE_EARTH_II'):
                if b_bone.children:
                    # default for Civ IV/EE II bones with children
                    n_node.flags = 0x0006
                else:
                    # default for Civ IV/EE II final bones
                    n_node.flags = 0x0016
            elif game in ('DIVINITY_2',):
                if b_bone.children:
                    # default for Div 2 bones with children
                    n_node.flags = 0x0186
                elif b_bone.name.lower()[-9:] == 'footsteps':
                    n_node.flags = 0x0116
                else:
                    # default for Div 2 final bones
                    n_node.flags = 0x0196
            else:
                n_node.flags = 0x0002  # default for Morrowind bones
