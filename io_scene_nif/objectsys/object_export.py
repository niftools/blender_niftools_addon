    """This script contains helper methods to export textures."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

class ObjectHelper():

    def __init__(self, parent):
        self.nif_import = parent

        # Maps exported blocks to either None or associated Blender object
        self.blocks = {}
        
        # maps Blender names to previously imported names from the FullNames
        # buffer (see self.rebuild_full_names())
        self.names = {}
        # keeps track of names of exported blocks, to make sure they are unique
        self.block_names = []
    
    
    def get_exported_objects(self):
        """Return a list of exported objects."""
        exported_objects = []
        # iterating over self.blocks.itervalues() will count some objects
        # twice
        for b_obj in self.blocks.values():
            # skip empty objects
            if b_obj is None:
                continue
            # detect doubles
            if b_obj in exported_objects:
                continue
            # append new object
            exported_objects.append(b_obj)
        # return the list of unique exported objects
        return exported_objects
    
    
    def register_block(self, block, b_obj = None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            self.info("Exporting %s block"%block.__class__.__name__)
        else:
            self.info("Exporting %s as %s block"
                     % (b_obj, block.__class__.__name__))
        self.blocks[block] = b_obj
        return block
    
    
    def export_node(self, b_obj, space, parent_block, node_name):
        """Export a mesh/armature/empty object b_obj as child of parent_block.
        Export also all children of b_obj.

        - space is 'none', 'worldspace', or 'localspace', and determines
          relative to what object the transformation should be stored.
        - parent_block is the parent nif block of the object (None for the
          root node)
        - for the root node, b_obj is None, and node_name is usually the base
          filename (either with or without extension)

        :param node_name: The name of the node to be exported.
        :type node_name: :class:`str`
        """
        # b_obj_type: determine the block type
        #          (None, 'MESH', 'EMPTY' or 'ARMATURE')
        # b_obj_ipo:  object animation ipo
        # node:    contains new NifFormat.NiNode instance
        if (b_obj == None):
            # -> root node
            assert(parent_block == None) # debug
            node = self.create_ninode()
            b_obj_type = None
            b_obj_ipo = None
        else:
            # -> empty, b_mesh, or armature
            b_obj_type = b_obj.type
            assert(b_obj_type in ['EMPTY', 'MESH', 'ARMATURE']) # debug
            assert(parent_block) # debug
            b_obj_ipo = b_obj.animation_data # get animation data
            b_obj_children = b_obj.children

            if (node_name == 'RootCollisionNode'):
                # -> root collision node (can be mesh or empty)
                # TODO do we need to fix this stuff on export?
                #b_obj.draw_bounds_type = 'POLYHEDERON'
                #b_obj.draw_type = 'BOUNDS'
                #b_obj.show_wire = True
                self.export_collision(b_obj, parent_block)
                return None # done; stop here

            elif (b_obj_type == 'MESH' and b_obj.show_bounds
                  and b_obj.name.lower().startswith('bsbound')):
                # add a bounding box
                self.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=True)
                return None # done; stop here

            elif (b_obj_type == 'MESH' and b_obj.show_bounds
                  and b_obj.name.lower().startswith("bounding box")):
                # Morrowind bounding box
                self.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=False)
                return None # done; stop here

            elif b_obj_type == 'MESH':
                # -> mesh data.
                # If this has children or animations or more than one material
                # it gets wrapped in a purpose made NiNode.
                is_collision = b_obj.game.use_collision_bounds
                has_ipo = b_obj_ipo and len(b_obj_ipo.getCurves()) > 0
                has_children = len(b_obj_children) > 0
                is_multimaterial = len(set([f.material_index for f in b_obj.data.faces])) > 1
                # determine if object tracks camera
                has_track = False
                for constr in b_obj.constraints:
                    if constr.type == Blender.Constraint.Type.TRACKTO:
                        has_track = True
                        break
                    # does geom have priority value in NULL constraint?
                    elif constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.get_bone_name_for_nif(b_obj.name)
                            ] = int(constr.name[9:])
                if is_collision:
                    self.export_collision(b_obj, parent_block)
                    return None # done; stop here
                elif has_ipo or has_children or is_multimaterial or has_track:
                    # -> mesh ninode for the hierarchy to work out
                    if not has_track:
                        node = self.create_block('NiNode', b_obj)
                    else:
                        node = self.create_block('NiBillboardNode', b_obj)
                else:
                    # don't create intermediate ninode for this guy
                    self.export_tri_shapes(b_obj, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.create_ninode(b_obj)
                # does node have priority value in NULL constraint?
                for constr in b_obj.constraints:
                    if constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.get_bone_name_for_nif(b_obj.name)
                            ] = int(constr.name[9:])

        # set transform on trishapes rather than on NiNode for skinned meshes
        # this fixes an issue with clothing slots
        if b_obj_type == 'MESH':
            if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                if b_obj_ipo:
                    # mesh with armature parent should not have animation!
                    self.warning(
                        "Mesh %s is skinned but also has object animation. "
                        "The nif format does not support this: "
                        "ignoring object animation." % b_obj.name)
                    b_obj_ipo = None
                trishape_space = space
                space = 'none'
            else:
                trishape_space = 'none'

        # make it child of its parent in the nif, if it has one
        if parent_block:
            parent_block.add_child(node)

        # and fill in this node's non-trivial values
        node.name = self.get_full_name(node_name).encode()

        # default node flags
        if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
            node.flags = 0x000E
        elif self.properties.game in ('SID_MEIER_S_RAILROADS',
                                     'CIVILIZATION_IV'):
            node.flags = 0x0010
        elif self.properties.game in ('EMPIRE_EARTH_II',):
            node.flags = 0x0002
        elif self.properties.game in ('DIVINITY_2',):
            node.flags = 0x0310
        else:
            # morrowind
            node.flags = 0x000C

        self.export_matrix(b_obj, space, node)

        if b_obj:
            # export animation
            if b_obj_ipo:
                if any(
                    b_obj_ipo[b_channel]
                    for b_channel in (Ipo.OB_LOCX, Ipo.OB_ROTX, Ipo.OB_SCALEX)):
                    self.animationhelper.export_keyframes(b_obj_ipo, space, node)
                self.export_object_vis_controller(b_obj, node)
            # if it is a mesh, export the mesh as trishape children of
            # this ninode
            if (b_obj.type == 'MESH'):
                # see definition of trishape_space above
                self.export_tri_shapes(b_obj, trishape_space, node)

            # if it is an armature, export the bones as ninode
            # children of this ninode
            elif (b_obj.type == 'ARMATURE'):
                self.armaturehelper.export_bones(b_obj, node)

            # export all children of this empty/mesh/armature/bone
            # object as children of this NiNode
            self.armaturehelper.export_children(b_obj, node)

        return node
  
    #
    # Export a blender object ob of the type mesh, child of nif block
    # parent_block, as NiTriShape and NiTriShapeData blocks, possibly
    # along with some NiTexturingProperty, NiSourceTexture,
    # NiMaterialProperty, and NiAlphaProperty blocks. We export one
    # trishape block per mesh material. We also export vertex weights.
    #
    # The parameter trishape_name passes on the name for meshes that
    # should be exported as a single mesh.
    #


    def create_ninode(self, b_obj=None):
        # trivial case first
        if not b_obj:
            return self.create_block("NiNode")
        # exporting an object, so first create node of correct type
        try:
            n_node_type = b_obj.getProperty("Type").data
        except (RuntimeError, AttributeError, NameError):
            n_node_type = "NiNode"
        n_node = self.create_block(n_node_type, b_obj)
        # customize the node data, depending on type
        if n_node_type == "NiLODNode":
            self.export_range_lod_data(n_node, b_obj)

        # return the node
        return n_node
    
    def rebuild_full_names(self):
        """Recovers the full object names from the text buffer and rebuilds
        the names dictionary."""
        try:
            namestxt = bpy.data.texts['FullNames']
        except KeyError:
            return
        for b_textline in namestxt.lines:
            line = b_textline.body
            if len(line)>0:
                name, fullname = line.split(';')
                self.names[name] = fullname

    
    #TODO: get objects to store their own names.

    def get_unique_name(self, blender_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object.

        :param blender_name: Name of object as in blender.
        :type blender_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        unique_name = "unnamed"
        if blender_name:
            unique_name = blender_name
        # blender bone naming -> nif bone naming
        unique_name = self.get_bone_name_for_nif(unique_name)
        # ensure uniqueness
        if unique_name in self.block_names or unique_name in list(self.names.values()):
            unique_int = 0
            old_name = unique_name
            while unique_name in self.block_names or unique_name in list(self.names.values()):
                unique_name = "%s.%02d" % (old_name, unique_int)
                unique_int += 1
        self.block_names.append(unique_name)
        self.names[blender_name] = unique_name
        return unique_name


    def get_full_name(self, blender_name):
        """Returns the original imported name if present, or the name by which
        the object was exported already.

        :param blender_name: Name of object as in blender.
        :type blender_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        try:
            return self.names[blender_name]
        except KeyError:
            return self.get_unique_name(blender_name)
    
    
    def export_range_lod_data(self, n_node, b_obj):
        """Export range lod data for for the children of b_obj, as a
        NiRangeLODData block on n_node.
        """
        # create range lod data object
        n_range_data = self.create_block("NiRangeLODData", b_obj)
        n_node.lod_level_data = n_range_data
        # get the children
        b_children = b_obj.children
        # set the data
        n_node.num_lod_levels = len(b_children)
        n_range_data.num_lod_levels = len(b_children)
        n_node.lod_levels.update_size()
        n_range_data.lod_levels.update_size()
        for b_child, n_lod_level, n_rd_lod_level in zip(
            b_children, n_node.lod_levels, n_range_data.lod_levels):
            n_lod_level.near_extent = b_child.getProperty("Near Extent").data
            n_lod_level.far_extent = b_child.getProperty("Far Extent").data
            n_rd_lod_level.near_extent = n_lod_level.near_extent
            n_rd_lod_level.far_extent = n_lod_level.far_extent


    