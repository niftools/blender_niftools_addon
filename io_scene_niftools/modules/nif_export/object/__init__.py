"""This script contains helper methods to export objects."""

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
import mathutils
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_export import types
from io_scene_niftools.modules.nif_export.animation.transform import TransformAnimation
from io_scene_niftools.modules.nif_export.animation.object import ObjectAnimation
from io_scene_niftools.modules.nif_export.armature import Armature
from io_scene_niftools.modules.nif_export.collision.bound import NiCollision, BSBound
from io_scene_niftools.modules.nif_export.collision.havok import BhkCollision
from io_scene_niftools.modules.nif_export.geometry.mesh import Mesh
from io_scene_niftools.modules.nif_export.property.object import ObjectDataProperty
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math
from io_scene_niftools.utils.logging import NifLog

# dictionary of names, to map NIF blocks to correct Blender names
DICT_NAMES = {}

# keeps track of names of exported blocks, to make sure they are unique
BLOCK_NAMES_LIST = []

# identity matrix, for comparisons
IDENTITY44 = mathutils.Matrix([[1.0, 0.0, 0.0, 0.0],
                               [0.0, 1.0, 0.0, 0.0],
                               [0.0, 0.0, 1.0, 0.0],
                               [0.0, 0.0, 0.0, 1.0]])


class Object:

    export_types = ('EMPTY', 'MESH', 'ARMATURE')

    def __init__(self):
        self.armaturehelper = Armature()
        self.mesh_helper = Mesh()
        self.transform_anim = TransformAnimation()
        self.object_anim = ObjectAnimation()
        self.bhk_helper = BhkCollision()
        self.bound_helper = NiCollision()
        self.bs_helper = BSBound()

    def get_export_objects(self, only_selected=True):
        """Get all exportable object and a subset of those objects representing root objects"""
        # get the root object from selected object
        selected_objects = bpy.context.selected_objects
        # if none are selected to begin with or we ignore the selection, just get all of this scene's objects
        if not selected_objects or not only_selected:
            selected_objects = bpy.context.scene.objects

        # only export empties, meshes, and armatures
        exportable_objects = [b_obj for b_obj in selected_objects if b_obj.type in self.export_types]

        # find all objects that do not have a parent
        root_objects = [b_obj for b_obj in exportable_objects if not b_obj.parent]

        # we have objects that we can export, but the selection did not contain a suitable root
        if exportable_objects and not root_objects:
            # todo [object] better but more complicated: growing the selection recursively until we have a root
            return self.get_export_objects(only_selected=False)
        return exportable_objects, root_objects

    def export_root_node(self, root_objects, filebase):
        """ Exports a nif's root node; use blender root if there is only one, else create a meta root """
        # TODO [collsion] detect root collision -> root collision node (can be mesh or empty)
        #     self.nif_export.collisionhelper.export_collision(b_obj, n_parent)
        #     return None  # done; stop here

        # there is only one root object so that will be our final root
        if len(root_objects) == 1:
            b_obj = root_objects[0]
            n_root = self.export_node(b_obj, None)

        # there is more than one root object so we create a meta root
        else:
            NifLog.info("Created meta root because blender scene had multiple root objects")
            n_root = types.create_ninode()
            n_root.name = "Scene Root"
            for b_obj in root_objects:
                self.export_node(b_obj, n_root)

        # TODO [object] How dow we know we are selecting the right node in the case of multi-root?
        # making root block a fade node
        root_type = b_obj.niftools.rootnode
        if bpy.context.scene.niftools_scene.game in ('FALLOUT_3', 'SKYRIM') and root_type == 'BSFadeNode':
            NifLog.info("Making root block a BSFadeNode")
            fade_root_block = NifFormat.BSFadeNode().deepcopy(n_root)
            fade_root_block.replace_global_node(n_root, fade_root_block)
            n_root = fade_root_block

        # various extra datas
        object_property = ObjectDataProperty()
        object_property.export_bsxflags_upb(n_root)
        object_property.export_inventory_marker(n_root, root_objects)
        object_property.export_weapon_location(n_root, b_obj)
        types.export_furniture_marker(n_root, filebase)
        return n_root

    def set_node_flags(self, b_obj, n_node):
        # default node flags
        game = bpy.context.scene.niftools_scene.game
        if b_obj.niftools.flags != 0:
            n_node.flags = b_obj.niftools.flags
        else:
            if game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                n_node.flags = 0x000E
            elif game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                n_node.flags = 0x0010
            elif game is 'EMPIRE_EARTH_II':
                n_node.flags = 0x0002
            elif game is 'DIVINITY_2':
                n_node.flags = 0x0310
            else:
                n_node.flags = 0x000C  # morrowind

    def export_node(self, b_obj, n_parent):
        """Export a mesh/armature/empty object b_obj as child of n_parent.
        Export also all children of b_obj.

        :param n_parent:
        :param b_obj:
        """

        if not b_obj:
            return None

        b_action = self.object_anim.get_active_action(b_obj)

        # can we export this b_obj?
        if b_obj.type not in self.export_types:
            return None
        if b_obj.type == 'MESH':
            if self.export_collision(b_obj, n_parent):
                return
            else:
                # -> mesh data.
                is_multimaterial = len(set([f.material_index for f in b_obj.data.polygons])) > 1

                # determine if object tracks camera
                # nb normally, imported models will have tracking constraints on their parent empty
                # but users may create track_to constraints directly on objects, so keep it for now
                has_track = types.has_track(b_obj)

                # If this has children or animations or more than one material it gets wrapped in a purpose made NiNode.
                if not (b_action or b_obj.children or is_multimaterial or has_track):
                    return self.mesh_helper.export_tri_shapes(b_obj, n_parent, b_obj.name)

                # set transform on trishapes rather than NiNodes for skinned meshes to fix an issue with clothing slots
                if b_obj.parent and b_obj.parent.type == 'ARMATURE' and b_action:
                    # mesh with armature parent should not have animation!
                    NifLog.warn(f"Mesh {b_obj.name} is skinned but also has object animation. "
                                f"The nif format does not support this, ignoring object animation.")
                    b_action = False

        # -> everything else (empty/armature) is a (more or less regular) node
        node = types.create_ninode(b_obj)

        # make it child of its parent in the nif, if it has one
        if n_parent:
            n_parent.add_child(node)

        # and fill in this node's non-trivial values
        node.name = block_store.get_full_name(b_obj)
        self.set_node_flags(b_obj, node)
        math.set_object_matrix(b_obj, node)

        # export object animation
        self.transform_anim.export_transforms(node, b_obj, b_action)
        self.object_anim.export_visibility(node, b_action)
        # if it is a mesh, export the mesh as trishape children of this ninode
        if b_obj.type == 'MESH':
            return self.mesh_helper.export_tri_shapes(b_obj, node)
        # if it is an armature, export the bones as ninode children of this ninode
        elif b_obj.type == 'ARMATURE':
            self.armaturehelper.export_bones(b_obj, node)

        # export all children of this b_obj as children of this NiNode
        self.export_children(b_obj, node)

        return node

    def export_children(self, b_parent, n_parent):
        """Export all children of blender object b_parent as children of n_parent."""
        # loop over all obj's children
        for b_child in b_parent.children:
            temp_parent = n_parent
            # special case: objects parented to armature bones - find the nif parent bone
            if b_parent.type == 'ARMATURE' and b_child.parent_bone != "":
                parent_bone = b_parent.data.bones[b_child.parent_bone]
                assert (parent_bone in block_store.block_to_obj.values())
                for temp_parent, obj in block_store.block_to_obj.items():
                    if obj == parent_bone:
                        break
            self.export_node(b_child, temp_parent)

    def export_collision(self, b_obj, n_parent):
        """Main function for adding collision object b_obj to a node.
        Returns True if this object is exported as a collision"""

        if b_obj.display_type != "BOUNDS":
            return
        if b_obj.name.lower().startswith('bsbound'):
            # add a bounding box
            self.bs_helper.export_bounds(b_obj, n_parent, bsbound=True)

        elif b_obj.name.lower().startswith("bounding box"):
            # Morrowind bounding box
            self.bs_helper.export_bounds(b_obj, n_parent, bsbound=False)
        if bpy.context.scene.niftools_scene.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):

            nodes = [n_parent]
            nodes.extend([block for block in n_parent.children if block.name[:14] == 'collisiondummy'])
            for node in nodes:
                try:
                    self.bhk_helper.export_collision_helper(b_obj, node)
                    break
                except ValueError:  # adding collision failed
                    continue
            else:
                # all nodes failed so add new one
                node = types.create_ninode(b_obj)
                # node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy{:d}'.format(n_parent.num_children)
                if b_obj.niftools.flags != 0:
                    node_flag_hex = hex(b_obj.niftools.flags)
                else:
                    node_flag_hex = 0x000E  # default
                node.flags = node_flag_hex
                n_parent.add_child(node)
                self.bhk_helper.export_collision_helper(b_obj, node)

        elif bpy.context.scene.niftools_scene.game in ('ZOO_TYCOON_2',):
            self.bound_helper.export_nicollisiondata(b_obj, n_parent)
        else:
            NifLog.warn(f"Collisions not supported for game '{bpy.context.scene.niftools_scene.game}', skipped collision object '{b_obj.name}'")

        return True