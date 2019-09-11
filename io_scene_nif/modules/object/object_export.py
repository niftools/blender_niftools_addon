"""This script contains helper methods to export objects."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

from io_scene_nif.modules import armature
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility.nif_logging import NifLog


class ObjectHelper:

    def __init__(self, parent):
        self.nif_export = parent
        self.mesh_helper = MeshHelper(parent)

    def create_block(self, blocktype, b_obj=None):
        """Helper function to create a new block, register it in the list of
        exported blocks, and associate it with a Blender object.

        @param blocktype: The nif block type (for instance "NiNode").
        @type blocktype: C{str}
        @param b_obj: The Blender object.
        @return: The newly created block."""
        try:
            block = getattr(NifFormat, blocktype)()
        except AttributeError:
            raise nif_utils.NifError("'{0}': Unknown block type (this is probably a bug).".format(blocktype))
        return self.register_block(block, b_obj)

    def get_exported_objects(self):
        """Return a list of exported objects."""
        exported_objects = []
        # iterating over self.nif_export.dict_blocks.itervalues() will count some objects twice
        for b_obj in self.nif_export.dict_blocks.values():
            # skip empty & known objects
            if b_obj and b_obj not in exported_objects:
                # append new object
                exported_objects.append(b_obj)
        # return the list of unique exported objects
        return exported_objects

    def register_block(self, block, b_obj=None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            NifLog.info("Exporting {0} block".format(block.__class__.__name__))
        else:
            NifLog.info("Exporting {0} as {1} block".format(b_obj, block.__class__.__name__))
        self.nif_export.dict_blocks[block] = b_obj
        return block

    def export_node(self, b_obj, parent_block, node_name):
        """Export a mesh/armature/empty object b_obj as child of parent_block.
        Export also all children of b_obj.

        - parent_block is the parent nif block of the object (None for the
          root node)
        - for the root node, b_obj is None, and node_name is usually the base
          filename (either with or without extension)

        :param parent_block:
        :param b_obj:
        :param node_name: The name of the node to be exported.
        :type node_name: :class:`str`
        """
        # b_obj_type: determine the block type
        #          (None, 'MESH', 'EMPTY' or 'ARMATURE')
        # b_obj_anim_data:  object animation ipo
        # node:    contains new NifFormat.NiNode instance
        
        export_types = ('EMPTY', 'MESH', 'ARMATURE')
        if b_obj is None:
            selected_exportable_objects = [b_obj for b_obj in bpy.context.selected_objects if b_obj.type in export_types]
            if len(selected_exportable_objects) == 0:
                raise nif_utils.NifError("Selected objects ({0}) are not exportable.".format(str(bpy.context.selected_objects)))

            for root_object in [b_obj for b_obj in bpy.context.selected_objects if b_obj.type in export_types]:
                while root_object.parent:
                    root_object = root_object.parent

            # root node
            if root_object.type == 'ARMATURE':
                b_obj = root_object

            # root node
            if b_obj is None:
                assert parent_block is None  # debug
                node = self.create_ninode()
                b_obj_type = None
                b_obj_anim_data = None
            else:
                b_obj_type = b_obj.type
                assert (b_obj_type in export_types)  # debug
                assert (parent_block is None)  # debug
                b_obj_anim_data = b_obj.animation_data  # get animation data
                b_obj_children = b_obj.children
                node_name = b_obj.name

        elif b_obj.name != parent_block.name.decode() and b_obj.parent is not None:
            # -> empty, b_mesh, or armature
            b_obj_type = b_obj.type
            assert (b_obj_type in export_types)  # debug
            assert parent_block  # debug
            b_obj_anim_data = b_obj.animation_data  # get animation data
            b_obj_children = b_obj.children

        elif b_obj.name != parent_block.name.decode() and b_obj.type != 'ARMATURE':
            # -> empty, b_mesh, or armature
            b_obj_type = b_obj.type
            assert b_obj_type in ['EMPTY', 'MESH']  # debug
            assert parent_block  # debug
            b_obj_anim_data = b_obj.animation_data  # get animation data
            b_obj_children = b_obj.children

        else:
            return None

        has_anim = True if b_obj_anim_data and b_obj_anim_data.action.fcurves else False
        if node_name == 'RootCollisionNode':
            # -> root collision node (can be mesh or empty)
            self.nif_export.export_collision(b_obj, parent_block)
            return None  # done; stop here

        elif b_obj_type == 'MESH' and b_obj.show_bounds and b_obj.name.lower().startswith('bsbound'):
            # add a bounding box
            self.nif_export.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=True)
            return None  # done; stop here

        elif b_obj_type == 'MESH' and b_obj.show_bounds and b_obj.name.lower().startswith("bounding box"):
            # Morrowind bounding box
            self.nif_export.boundhelper.export_bounding_box(b_obj, parent_block, bsbound=False)
            return None  # done; stop here

        elif b_obj_type == 'MESH':
            # -> mesh data.
            # If this has children or animations or more than one material it gets wrapped in a purpose made NiNode.
            is_collision = b_obj.game.use_collision_bounds
            has_children = len(b_obj_children) > 0
            is_multimaterial = len(set([f.material_index for f in b_obj.data.polygons])) > 1

            # determine if object tracks camera
            # nb normally, imported models will have tracking constraints on their parent empty
            # but users may create track_to constraints directly on objects, so keep it for now
            has_track = self.has_track(b_obj)

            if is_collision:
                self.nif_export.export_collision(b_obj, parent_block)
                return None  # done; stop here
            elif has_anim or has_children or is_multimaterial or has_track:
                # create a ninode as parent of this mesh for the hierarchy to work out
                node = self.create_ninode(b_obj)
            else:
                # don't create intermediate ninode for this guy
                self.mesh_helper.export_tri_shapes(b_obj, parent_block, node_name)
                # we didn't create a ninode, return nothing
                return None

        elif b_obj is not None:
            # -> everything else (empty/armature) is a (more or less regular) node
            node = self.create_ninode(b_obj)
            
        # set transform on trishapes rather than on NiNode for skinned meshes
        # this fixes an issue with clothing slots
        if b_obj_type == 'MESH':
            if b_obj.parent and b_obj.parent.type == 'ARMATURE':
                if b_obj_anim_data:
                    # mesh with armature parent should not have animation!
                    NifLog.warn("Mesh {0} is skinned but also has object animation. "
                                "The nif format does not support this, ignoring object animation.".format(b_obj.name))
                    has_anim = False

        # make it child of its parent in the nif, if it has one
        if parent_block:
            parent_block.add_child(node)

        # and fill in this node's non-trivial values
        node.name = self.get_full_name(b_obj)

        # default node flags
        if b_obj_type in export_types:
            if b_obj_type is 'EMPTY' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            if b_obj_type is 'MESH' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags != 0:
                node.flags = b_obj.niftools.objectflags
            elif b_obj_type is 'ARMATURE' and b_obj.niftools.objectflags == 0 and b_obj.parent is None:
                node.flags = b_obj.niftools.objectflags
            else:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    node.flags = 0x000E
                elif NifOp.props.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                    node.flags = 0x0010
                elif NifOp.props.game is 'EMPIRE_EARTH_II':
                    node.flags = 0x0002
                elif NifOp.props.game is 'DIVINITY_2':
                    node.flags = 0x0310
                else:
                    node.flags = 0x000C  # morrowind

        self.set_object_matrix(b_obj, node)

        if b_obj:
            # export object animation
            if has_anim:
                self.nif_export.animationhelper.export_keyframes(node, b_obj)
                self.nif_export.animationhelper.object_animation.export_object_vis_controller(node, b_obj)
            # if it is a mesh, export the mesh as trishape children of this ninode
            if b_obj.type == 'MESH':
                self.mesh_helper.export_tri_shapes(b_obj, node)

            # if it is an armature, export the bones as ninode children of this ninode
            elif b_obj.type == 'ARMATURE':
                self.nif_export.armaturehelper.export_bones(b_obj, node)

            # export all children of this empty/mesh/armature/bone object as children of this NiNode
            self.nif_export.armaturehelper.export_children(b_obj, node)

        return node

    # Export a blender object ob of the type mesh, child of nif block
    # parent_block, as NiTriShape and NiTriShapeData blocks, possibly
    # along with some NiTexturingProperty, NiSourceTexture,
    # NiMaterialProperty, and NiAlphaProperty blocks. We export one
    # trishape block per mesh material. We also export vertex weights.
    #
    # The parameter trishape_name passes on the name for meshes that
    # should be exported as a single mesh.

    def create_ninode(self, b_obj=None):
        """Essentially a wrapper around create_block() that creates nodes of the right type"""
        # when no b_obj is passed, it means we create a root node
        if not b_obj:
            return self.create_block("NiNode")

        # get node type - some are stored as custom property of the b_obj
        try:
            n_node_type = b_obj["type"]
        except:
            n_node_type = "NiNode"
        # ...others by presence of constraints
        if self.has_track(b_obj):
            n_node_type = "NiBillboardNode"
        # noew create the node
        n_node = self.create_block(n_node_type, b_obj)
        # customize the node data, depending on type
        if n_node_type == "NiLODNode":
            self.export_range_lod_data(n_node, b_obj)
        # return the node
        return n_node

    def get_unique_name(self, b_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object.

        :param b_name: Name of object as in blender.
        :type b_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        unique_name = "unnamed"
        if b_name:
            unique_name = b_name
        # blender bone naming -> nif bone naming
        unique_name = armature.get_bone_name_for_nif(unique_name)
        # # ensure uniqueness
        # if unique_name in self.nif_export.dict_block_names or unique_name in list(self.nif_export.dict_names.values()):
            # unique_int = 0
            # old_name = unique_name
            # while unique_name in self.nif_export.dict_block_names or unique_name in list(self.nif_export.dict_names.values()):
                # unique_name = "%s.%02d" % (old_name, unique_int)
                # unique_int += 1
        self.nif_export.dict_block_names.append(unique_name)
        self.nif_export.dict_names[b_name] = unique_name
        return unique_name

    def get_full_name(self, b_obj):
        """Returns the original imported name if present, or the name by which
        the object was exported already.
        """
        longname = ""
        if b_obj:
            try:
                longname = b_obj.niftools.longname
            except:
                pass
            if not longname:
                longname = self.get_unique_name(b_obj.name)
        return longname

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
        for b_child, n_lod_level, n_rd_lod_level in zip(b_children, n_node.lod_levels, n_range_data.lod_levels):
            n_lod_level.near_extent = b_child["near_extent"]
            n_lod_level.far_extent = b_child["far_extent"]
            n_rd_lod_level.near_extent = n_lod_level.near_extent
            n_rd_lod_level.far_extent = n_lod_level.far_extent

    def set_object_matrix(self, b_obj, block):
        """Set a blender object's transform matrix to a NIF object's transformation matrix in rest pose."""
        block.set_transform( self.get_object_matrix(b_obj) )
        
    def get_object_matrix(self, b_obj):
        """Get a blender object's matrix as NifFormat.Matrix44"""
        return self.mathutils_to_nifformat_matrix( self.get_object_bind(b_obj) )
        
    def set_b_matrix_to_n_block(self, b_matrix, block):
        """Set a blender matrix to a NIF object's transformation matrix in rest pose."""
        ### TODO [object] maybe favor this over the above two methods for more flexibility and transparency?
        block.set_transform( self.mathutils_to_nifformat_matrix(b_matrix) )

    def mathutils_to_nifformat_matrix(self, b_matrix):
        """Convert a blender matrix to a NifFormat.Matrix44"""
        # transpose to swap columns for rows so we can use pyffi's set_rows() directly
        # instead of setting every single value manually
        n_matrix = NifFormat.Matrix44()
        n_matrix.set_rows( *b_matrix.transposed() )
        return n_matrix
        
    def get_object_bind(self, b_obj):
        """Get the bind matrix of a blender object.
        
        Returns the final NIF matrix for the given blender object.
        Blender space and axes order are corrected for the NIF.
        Returns a 4x4 mathutils.Matrix()
        """

        if isinstance(b_obj, bpy.types.Bone):
            matrix = armature.get_bind_matrix(b_obj)

        elif isinstance(b_obj, bpy.types.Object):
            # TODO MOVE TO ARMATUREHELPER

            matrix = b_obj.matrix_local.copy()

            # if there is a bone parent then the object is parented then get the matrix relative to the bone parent head
            if b_obj.parent_bone:
                # get parent bone
                parent_bone = b_obj.parent.data.bones[b_obj.parent_bone]
                # restore bone length that was substracted here on import
                matrix.translation.y += parent_bone.length
                
                # undo the calculations from import - multiply with inverse of the Blender bone matrix
                matrix = parent_bone.matrix_local.to_3x3().to_4x4() * matrix
                
        #Nonetype, maybe other weird stuff
        else:
            matrix = mathutils.Matrix()
        return matrix

    def has_track(self, b_obj):
        for constr in b_obj.constraints:
            if constr.type == 'TRACK_TO':
                return True

class MeshHelper:

    def __init__(self, parent):
        self.nif_export = parent

    def export_tri_shapes(self, b_obj, parent_block, trishape_name=None):
        NifLog.info("Exporting {0}".format(b_obj))

        assert (b_obj.type == 'MESH')

        # get mesh from b_obj
        b_mesh = b_obj.data  # get mesh data

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not b_obj.data.vertices:
            # do not export anything
            NifLog.warn("{0} has no vertices, skipped.".format(b_obj))
            return

        # get the mesh's materials, this updates the mesh material list
        if not isinstance(parent_block, NifFormat.RootCollisionNode):
            mesh_materials = b_mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_materials = []
        # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
        if not mesh_materials:
            mesh_materials = [None]

        # is mesh double sided?
        mesh_doublesided = b_mesh.show_double_sided

        # vertex color check
        mesh_hasvcol = False
        mesh_hasvcola = False

        if b_mesh.vertex_colors:
            mesh_hasvcol = True

            # vertex alpha check
            if len(b_mesh.vertex_colors) == 1:
                NifLog.warn("Mesh only has one Vertex Color layer. Default alpha values will be written."
                            "For Custom alpha values add a second vertex layer, greyscale only")
            else:
                for b_loop in b_mesh.vertex_colors[1].data:
                    if b_loop.color.v > NifOp.props.epsilon:
                        mesh_hasvcola = True
                        break

        # Non-textured materials, vertex colors are used to color the mesh
        # Textured materials, they represent lighting details

        # let's now export one trishape for every mesh material
        # TODO: needs refactoring - move material, texture, etc. to separate function
        for materialIndex, b_mat in enumerate(mesh_materials):

            b_ambient_prop = False
            b_diffuse_prop = False
            b_spec_prop = False
            b_emissive_prop = False
            b_gloss_prop = False
            b_alpha_prop = False
            b_emit_prop = False

            # use the texture properties as preference
            for b_slot in self.nif_export.texturehelper.get_used_textslots(b_mat):
                # replace with texture helper queries
                b_ambient_prop |= b_slot.use_map_ambient
                b_diffuse_prop |= b_slot.use_map_color_diffuse
                b_spec_prop |= b_slot.use_map_color_spec
                b_emissive_prop |= b_slot.use_map_emit
                b_gloss_prop |= b_slot.use_map_hardness
                b_alpha_prop |= b_slot.use_map_alpha
                b_emit_prop |= b_slot.use_map_emit

            # -> first, extract valuable info from our b_obj

            mesh_texture_alpha = False  # texture has transparency

            mesh_uv_layers = []  # uv layers used by this material
            mesh_hasalpha = False  # mesh has transparency
            mesh_haswire = False  # mesh rendered as wireframe
            mesh_hasspec = False  # mesh specular property

            mesh_hasnormals = False
            if b_mat is not None:
                mesh_hasnormals = True  # for proper lighting
                if (NifOp.props.game == 'SKYRIM') and (b_obj.niftools_shader.bslsp_shaderobjtype == 'Skin Tint'):
                    mesh_hasnormals = False  # for proper lighting

                # ambient mat
                mesh_mat_ambient_color = b_mat.niftools.ambient_color
                # diffuse mat
                mesh_mat_diffuse_color = b_mat.diffuse_color
                # emissive mat
                mesh_mat_emissive_color = b_mat.niftools.emissive_color
                mesh_mat_emitmulti = b_mat.emit
                # specular mat
                mesh_mat_specular_color = b_mat.specular_color

                eps = NifOp.props.epsilon
                if (mesh_mat_specular_color.r > eps) or (mesh_mat_specular_color.g > eps) or (mesh_mat_specular_color.b > eps):
                    mesh_hasspec = b_spec_prop

                # gloss mat 'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_gloss = b_mat.specular_hardness

                # alpha mat
                mesh_hasalpha = b_alpha_prop
                mesh_mat_transparency = (1 - b_mat.alpha)
                if b_mat.use_transparency:
                    if abs(mesh_mat_transparency - 1.0) > NifOp.props.epsilon:
                        mesh_hasalpha = True
                elif mesh_hasvcola:
                    mesh_hasalpha = True
                elif b_mat.animation_data and \
                        'Alpha' in b_mat.animation_data.action.fcurves:
                    mesh_hasalpha = True

                # wire mat
                mesh_haswire = (b_mat.type == 'WIRE')

            # list of body part (name, index, vertices) in this mesh
            bodypartgroups = []
            for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
                vertex_group = b_obj.vertex_groups.get(bodypartgroupname)
                vertices_list = set()
                if vertex_group:
                    for b_vert in b_mesh.vertices:
                        for b_groupname in b_vert.groups:
                            if b_groupname.group == vertex_group.index:
                                vertices_list.add(b_vert.index)
                    NifLog.debug("Found body part {0}".format(bodypartgroupname))
                    bodypartgroups.append(
                        [bodypartgroupname, getattr(NifFormat.BSDismemberBodyPartType, bodypartgroupname), vertices_list])

            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

            # create a trishape block
            if not NifOp.props.stripify:
                trishape = self.nif_export.objecthelper.create_block("NiTriShape", b_obj)
            else:
                trishape = self.nif_export.objecthelper.create_block("NiTriStrips", b_obj)

            # fill in the NiTriShape's non-trivial values
            if isinstance(parent_block, NifFormat.RootCollisionNode):
                trishape.name = ""
            else:
                if not trishape_name:
                    if parent_block.name:
                        trishape.name = "Tri " + parent_block.name.decode()
                    else:
                        trishape.name = "Tri " + b_obj.name.decode()
                else:
                    trishape.name = trishape_name

                # multimaterial meshes: add material index
                # (Morrowind's child naming convention)
                if len(mesh_materials) > 1:
                    trishape.name = trishape.name.decode() + ":%i" % materialIndex
                else:
                    trishape.name = self.nif_export.objecthelper.get_full_name(trishape)

            # Trishape Flags...
            if (b_obj.type == 'MESH') and (b_obj.niftools.objectflags != 0):
                trishape.flags = b_obj.niftools.objectflags
            else:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    trishape.flags = 0x000E

                elif NifOp.props.game in ('SID_MEIER_S_RAILROADS', 'CIVILIZATION_IV'):
                    trishape.flags = 0x0010
                elif NifOp.props.game in ('EMPIRE_EARTH_II',):
                    trishape.flags = 0x0016
                elif NifOp.props.game in ('DIVINITY_2',):
                    if trishape.name.lower[-3:] in ("med", "low"):
                        trishape.flags = 0x0014
                    else:
                        trishape.flags = 0x0016
                else:
                    # morrowind
                    if b_obj.draw_type != 'WIRE':  # not wire
                        trishape.flags = 0x0004  # use triangles as bounding box
                    else:
                        trishape.flags = 0x0005  # use triangles as bounding box + hide

            # extra shader for Sid Meier's Railroads
            if NifOp.props.game == 'SID_MEIER_S_RAILROADS':
                trishape.has_shader = True
                trishape.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                trishape.unknown_integer = -1  # default

            # if we have an animation of a blender mesh
            # an intermediate NiNode has been created which holds this b_obj's transform
            # the trishape itself then needs identity transform (default)
            if trishape_name is not None:
                # only export the bind matrix on trishapes that were not animated
                self.nif_export.objecthelper.set_object_matrix(b_obj, trishape)
            
            # add textures
            if NifOp.props.game == 'FALLOUT_3':
                if b_mat:
                    bsshader = self.nif_export.texturehelper.export_bs_shader_property(b_obj, b_mat)

                    self.nif_export.objecthelper.register_block(bsshader)
                    trishape.add_property(bsshader)
            elif NifOp.props.game == 'SKYRIM':
                if b_mat:
                    bsshader = self.nif_export.texturehelper.export_bs_shader_property(b_obj, b_mat)

                    self.nif_export.objecthelper.register_block(bsshader)
                    num_props = trishape.num_properties
                    trishape.num_properties = num_props + 1
                    trishape.bs_properties.update_size()
                    trishape.bs_properties[num_props] = bsshader

                    # trishape.add_property(bsshader)
                    '''Neomonkeus I had to do this because you still have not merged those changes 
                    ttl269 made to the xml can you make the effort to contact him and get him to 
                    rebase and clear the conflict so it can be merged'''
                    if isinstance(bsshader, NifFormat.BSEffectShaderProperty):
                        effect_control = self.nif_export.objecthelper.create_block("BSEffectShaderPropertyFloatController", bsshader)
                        effect_control.flags = b_mat.niftools_alpha.textureflag
                        effect_control.frequency = b_slot.texture.image.fps
                        effect_control.start_time = b_slot.texture.image.frame_start
                        effect_control.stop_time = b_slot.texture.image.frame_end
                        bsshader.add_controller(effect_control)
            else:
                if NifOp.props.game in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES:
                    # sid meier's railroad and civ4:
                    # set shader slots in extra data
                    self.nif_export.texturehelper.add_shader_integer_extra_datas(trishape)

                if b_mat:
                    n_nitextureprop = self.nif_export.texturehelper.export_texturing_property(
                        flags=0x0001,  # standard
                        applymode=self.nif_export.get_n_apply_mode_from_b_blend_type('MIX'),
                        b_mat=b_mat, b_obj=b_obj)

                    self.nif_export.objecthelper.register_block(n_nitextureprop)
                    trishape.add_property(n_nitextureprop)

            # add texture effect block (must be added as preceeding child of the trishape)
            ref_mtex = self.nif_export.texturehelper.ref_mtex
            if NifOp.props.game == 'MORROWIND' and ref_mtex:
                # create a new parent block for this shape
                extra_node = self.create_block("NiNode", ref_mtex)
                parent_block.add_child(extra_node)
                # set default values for this ninode
                extra_node.rotation.set_identity()
                extra_node.scale = 1.0
                extra_node.flags = 0x000C  # morrowind
                # create texture effect block and parent the
                # texture effect and trishape to it
                texeff = self.export_texture_effect(ref_mtex)
                extra_node.add_child(texeff)
                extra_node.add_child(trishape)
                extra_node.add_effect(texeff)
            else:
                # refer to this block in the parent's
                # children list
                parent_block.add_child(trishape)

            if mesh_hasalpha:
                # add NiTriShape's alpha propery
                # refer to the alpha property in the trishape block
                if b_mat.niftools_alpha.alphaflag != 0:
                    alphaflags = b_mat.niftools_alpha.alphaflag
                    alphathreshold = b_mat.offset_z
                elif NifOp.props.game == 'SID_MEIER_S_RAILROADS':
                    alphaflags = 0x32ED
                    alphathreshold = 150
                elif NifOp.props.game == 'EMPIRE_EARTH_II':
                    alphaflags = 0x00ED
                    alphathreshold = 0
                else:
                    alphaflags = 0x12ED
                    alphathreshold = 0
                trishape.add_property(self.nif_export.propertyhelper.object_property.export_alpha_property(flags=alphaflags, threshold=alphathreshold))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.add_property(self.nif_export.propertyhelper.object_property.export_wireframe_property(flags=1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.add_property(self.nif_export.propertyhelper.object_property.export_stencil_property())

            if b_mat and not (NifOp.props.game == 'SKYRIM'):
                # add NiTriShape's specular property
                # but NOT for sid meier's railroads and other extra shader
                # games (they use specularity even without this property)
                if mesh_hasspec and (NifOp.props.game not in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES):
                    # refer to the specular property in the trishape block
                    trishape.add_property(self.nif_export.propertyhelper.object_property.export_specular_property(flags=0x0001))

                # add NiTriShape's material property
                trimatprop = self.nif_export.propertyhelper.material_property.export_material_property(
                    name=self.nif_export.objecthelper.get_full_name(b_mat),
                    flags=0x0001,
                    # TODO: - standard flag, check? material and texture properties in morrowind style nifs had a flag
                    ambient=mesh_mat_ambient_color,
                    diffuse=mesh_mat_diffuse_color,
                    specular=mesh_mat_specular_color,
                    emissive=mesh_mat_emissive_color,
                    gloss=mesh_mat_gloss,
                    alpha=mesh_mat_transparency,
                    emitmulti=mesh_mat_emitmulti)

                self.nif_export.objecthelper.register_block(trimatprop)

                # refer to the material property in the trishape block
                trishape.add_property(trimatprop)

                # material animation
                self.nif_export.animationhelper.material_animation.export_material_controllers(b_material=b_mat, n_geom=trishape)

            # -> now comes the real export

            '''
                NIF has one uv vertex and one normal per vertex,
                per vert, vertex coloring.

                NIF uses the normal table for lighting.
                Smooth faces should use Blender's vertex normals,
                solid faces should use Blender's face normals.

                Blender's uv vertices and normals per face.
                Blender supports per face vertex coloring,
            '''

            # We now extract vertices, uv-vertices, normals, and
            # vertex colors from the mesh's face list. Some vertices must be duplicated.

            # The following algorithm extracts all unique quads(vert, uv-vert, normal, vcol),
            # produce lists of vertices, uv-vertices, normals, vertex colors, and face indices.

            mesh_uv_layers = self.nif_export.texturehelper.get_uv_layers(b_mat)
            vertquad_list = []  # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [None for _ in range(len(b_mesh.vertices))]  # blender vertex -> nif vertices
            vertlist = []
            normlist = []
            vcollist = []
            uvlist = []
            trilist = []
            # for each face in trilist, a body part index
            bodypartfacemap = []
            polygons_without_bodypart = []
            for poly in b_mesh.polygons:

                # does the face belong to this trishape?
                if b_mat is not None:  # we have a material
                    if poly.material_index != materialIndex:  # but this face has another material
                        continue  # so skip this face

                f_numverts = len(poly.vertices)
                if f_numverts < 3:
                    continue  # ignore degenerate polygons
                assert ((f_numverts == 3) or (f_numverts == 4))  # debug
                if mesh_uv_layers:
                    # if we have uv coordinates double check that we have uv data
                    if not b_mesh.uv_layer_stencil:
                        NifLog.warn("No UV map for texture associated with poly {0} of selected mesh '{1}'.".format(str(poly.index), b_mesh.name))

                # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
                f_index = [-1] * f_numverts
                for i, loop_index in enumerate(range(poly.loop_start, poly.loop_start + poly.loop_total)):

                    fv_index = b_mesh.loops[loop_index].vertex_index
                    vertex = b_mesh.vertices[fv_index]
                    vertex_index = vertex.index
                    fv = vertex.co

                    # smooth = vertex normal, non-smooth = face normal)
                    if mesh_hasnormals:
                        if poly.use_smooth:
                            fn = vertex.normal
                        else:
                            fn = poly.normal
                    else:
                        fn = None

                    fuv = []
                    for uv_layer in mesh_uv_layers:
                        if uv_layer != "":
                            # TODO: map uv layer to index
                            # currently we have uv_layer names, but we need their index value
                            # b_mesh.uv_layers[0].data[poly.index].uv
                            fuv.append(b_mesh.uv_layers[uv_layer].data[loop_index].uv)
                        else:
                            NifLog.warn("Texture is set to use UV but no UV Map is Selected for Mapping > Map")

                    # TODO: Need to map b_verts -> n_verts
                    if mesh_hasvcol:
                        # check for an alpha layer
                        b_color = b_mesh.vertex_colors[0].data[loop_index].color
                        if mesh_hasvcola:
                            b_alpha = b_mesh.vertex_colors[1].data[loop_index].color
                            f_col = [b_color.r, b_color.g, b_color.b, b_alpha.v]
                        else:
                            f_col = [b_color.r, b_color.g, b_color.b, 1.0]
                    else:
                        f_col = None

                    vertquad = (fv, fuv, fn, f_col)

                    # check for duplicate vertquad?
                    f_index[i] = len(vertquad_list)
                    if vertmap[vertex_index] is not None:
                        # iterate only over vertices with the same vertex index and check if they have the same uvs, normals and colors
                        for j in vertmap[vertex_index]:
                            # TODO use function to do comparison
                            if mesh_uv_layers:
                                num_uvs_layers = len(mesh_uv_layers)
                                if max(abs(vertquad[1][uv_layer][0] - vertquad_list[j][1][uv_layer][0]) for uv_layer in range(num_uvs_layers)) > NifOp.props.epsilon:
                                    continue
                                if max(abs(vertquad[1][uv_layer][1] - vertquad_list[j][1][uv_layer][1]) for uv_layer in range(num_uvs_layers)) > NifOp.props.epsilon:
                                    continue
                            if mesh_hasnormals:
                                if abs(vertquad[2][0] - vertquad_list[j][2][0]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[2][1] - vertquad_list[j][2][1]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[2][2] - vertquad_list[j][2][2]) > NifOp.props.epsilon:
                                    continue
                            if mesh_hasvcol:
                                if abs(vertquad[3][0] - vertquad_list[j][3][0]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][1] - vertquad_list[j][3][1]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][2] - vertquad_list[j][3][2]) > NifOp.props.epsilon:
                                    continue
                                if abs(vertquad[3][3] - vertquad_list[j][3][3]) > NifOp.props.epsilon:
                                    continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise nif_utils.NifError("Too many vertices. Decimate your mesh and try again.")

                    if f_index[i] == len(vertquad_list):
                        # first: add it to the vertex map
                        if not vertmap[vertex_index]:
                            vertmap[vertex_index] = []
                        vertmap[vertex_index].append(len(vertquad_list))
                        # new (vert, uv-vert, normal, vcol) quad: add it
                        vertquad_list.append(vertquad)

                        # add the vertex
                        vertlist.append(vertquad[0])
                        if mesh_hasnormals:
                            normlist.append(vertquad[2])
                        if mesh_hasvcol:
                            vcollist.append(vertquad[3])
                        if mesh_uv_layers:
                            uvlist.append(vertquad[1])

                # now add the (hopefully, convex) face, in triangles
                for i in range(f_numverts - 2):
                    if (b_obj.scale.x + b_obj.scale.y + b_obj.scale.z) > 0:
                        f_indexed = (f_index[0], f_index[1 + i], f_index[2 + i])
                    else:
                        f_indexed = (f_index[0], f_index[2 + i], f_index[1 + i])
                    trilist.append(f_indexed)

                    # add body part number
                    if NifOp.props.game not in ('FALLOUT_3', 'SKYRIM') or not bodypartgroups:
                        # TODO: or not self.EXPORT_FO3_BODYPARTS):
                        bodypartfacemap.append(0)
                    else:
                        for bodypartname, bodypartindex, bodypartverts in bodypartgroups:
                            if set(b_vert_index for b_vert_index in poly.vertices) <= bodypartverts:
                                bodypartfacemap.append(bodypartindex)
                                break
                        else:
                            # this signals an error
                            polygons_without_bodypart.append(poly)

            # check that there are no missing body part polygons
            if polygons_without_bodypart:
                # select mesh object
                for b_deselect_obj in bpy.context.scene.objects:
                    b_deselect_obj.select = False
                bpy.context.scene.objects.active = b_obj
                b_obj.select = True
                # select bad polygons
                # switch to edit mode to select polygons
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                for face in b_mesh.polygons:
                    face.select = False
                for face in polygons_without_bodypart:
                    face.select = True
                # raise exception
                raise ValueError("Some polygons of {0} not assigned to any body part."
                                 "The unassigned polygons have been selected in the mesh so they can easily be identified.".format(b_obj))

            if len(trilist) > 65535:
                raise nif_utils.NifError("Too many polygons. Decimate your mesh and try again.")
            if len(vertlist) == 0:
                continue  # m_4444x: skip 'empty' material indices

            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = self.nif_export.objecthelper.create_block("NiTriShapeData", b_obj)
            else:
                tridata = self.nif_export.objecthelper.create_block("NiTriStripsData", b_obj)
            trishape.data = tridata

            # flags
            if b_obj.niftools.consistency_flags in NifFormat.ConsistencyType._enumkeys:
                cf_index = NifFormat.ConsistencyType._enumkeys.index(b_obj.niftools.consistency_flags)
                tridata.consistency_flags = NifFormat.ConsistencyType._enumvalues[cf_index]
            else:
                tridata.consistency_flags = NifFormat.ConsistencyType.CT_STATIC
                NifLog.warn("{0} has no consistency type set using default CT_STATIC.".format(b_obj))

            # data
            tridata.num_vertices = len(vertlist)
            tridata.has_vertices = True
            tridata.vertices.update_size()
            for i, v in enumerate(tridata.vertices):
                v.x = vertlist[i][0]
                v.y = vertlist[i][1]
                v.z = vertlist[i][2]
            tridata.update_center_radius()

            if mesh_hasnormals:
                tridata.has_normals = True
                tridata.normals.update_size()
                for i, v in enumerate(tridata.normals):
                    v.x = normlist[i][0]
                    v.y = normlist[i][1]
                    v.z = normlist[i][2]

            if mesh_hasvcol:
                tridata.has_vertex_colors = True
                tridata.vertex_colors.update_size()
                for i, v in enumerate(tridata.vertex_colors):
                    v.r = vcollist[i][0]
                    v.g = vcollist[i][1]
                    v.b = vcollist[i][2]
                    v.a = vcollist[i][3]

            if mesh_uv_layers:
                tridata.num_uv_sets = len(mesh_uv_layers)
                tridata.bs_num_uv_sets = len(mesh_uv_layers)
                if NifOp.props.game == 'FALLOUT_3':
                    if len(mesh_uv_layers) > 1:
                        raise nif_utils.NifError("Fallout 3 does not support multiple UV layers")
                tridata.has_uv = True
                tridata.uv_sets.update_size()
                for j, uv_layer in enumerate(mesh_uv_layers):
                    for i, uv in enumerate(tridata.uv_sets[j]):
                        if len(uvlist[i]) == 0:
                            continue  # skip non-uv textures
                        uv.u = uvlist[i][j][0]
                        uv.v = 1.0 - uvlist[i][j][1]  # opengl standard

            # set triangles
            # stitch strips for civ4
            tridata.set_triangles(trilist,
                                  stitchstrips=NifOp.props.stitch_strips)

            # update tangent space (as binary extra data only for Oblivion)
            # for extra shader texture games, only export it if those
            # textures are actually exported (civ4 seems to be consistent with
            # not using tangent space on non shadered nifs)
            if mesh_uv_layers and mesh_hasnormals:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') or (NifOp.props.game in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES):
                    trishape.update_tangent_space(as_extra=(NifOp.props.game == 'OBLIVION'))

            # now export the vertex weights, if there are any
            vertgroups = {vertex_group.name for vertex_group in b_obj.vertex_groups}
            bone_names = []
            if b_obj.parent:
                if b_obj.parent.type == 'ARMATURE':
                    b_obj_armature = b_obj.parent
                    bone_names = list(b_obj_armature.data.bones.keys())
                    # the vertgroups that correspond to bone_names are bones that influence the mesh
                    boneinfluences = []
                    for bone in bone_names:
                        if bone in vertgroups:
                            boneinfluences.append(bone)
                    if boneinfluences:  # yes we have skinning!
                        # create new skinning instance block and link it
                        if NifOp.props.game in ('FALLOUT_3', 'SKYRIM') and bodypartgroups:
                            skininst = self.nif_export.objecthelper.create_block("BSDismemberSkinInstance", b_obj)
                        else:
                            skininst = self.nif_export.objecthelper.create_block("NiSkinInstance", b_obj)
                        trishape.skin_instance = skininst
                        for block in self.nif_export.dict_blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name.decode() == self.nif_export.objecthelper.get_full_name(b_obj_armature):
                                    skininst.skeleton_root = block
                                    break
                        else:
                            raise nif_utils.NifError("Skeleton root '%s' not found." % b_obj_armature.name)

                        # create skinning data and link it
                        skindata = self.nif_export.objecthelper.create_block("NiSkinData", b_obj)
                        skininst.data = skindata

                        skindata.has_vertex_weights = True
                        # fix geometry rest pose: transform relative to skeleton root
                        skindata.set_transform(self.nif_export.objecthelper.get_object_matrix(b_obj).get_inverse())

                        # Vertex weights,  find weights and normalization factors
                        vert_list = {}
                        vert_norm = {}
                        unassigned_verts = []

                        for bone_group in boneinfluences:
                            b_list_weight = []
                            b_vert_group = b_obj.vertex_groups[bone_group]

                            for b_vert in b_obj.data.vertices:
                                if len(b_vert.groups) == 0:  # check vert has weight_groups
                                    unassigned_verts.append(b_vert)
                                    continue

                                for g in b_vert.groups:
                                    if b_vert_group.name in boneinfluences:
                                        if g.group == b_vert_group.index:
                                            b_list_weight.append((b_vert.index, g.weight))
                                            break

                            vert_list[bone_group] = b_list_weight

                            # create normalisation groupings
                            for v in vert_list[bone_group]:
                                if v[0] in vert_norm:
                                    vert_norm[v[0]] += v[1]
                                else:
                                    vert_norm[v[0]] = v[1]

                        # vertices must be assigned at least one vertex group
                        # lets be nice and display them for the user 
                        if len(unassigned_verts) > 0:
                            for b_scene_obj in bpy.context.scene.objects:
                                b_scene_obj.select = False

                            b_obj = bpy.context.scene.objects.active
                            b_obj.select = True

                            # switch to edit mode and raise exception
                            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                            # clear all currently selected vertices
                            bpy.ops.mesh.select_all(action='DESELECT')
                            # select unweighted vertices
                            bpy.ops.mesh.select_ungrouped(extend=False)

                            raise nif_utils.NifError("Cannot export mesh with unweighted vertices. "
                                                     "The unweighted vertices have been selected in the mesh so they can easily be identified.")

                        # for each bone, first we get the bone block
                        # then we get the vertex weights
                        # and then we add it to the NiSkinData
                        # note: allocate memory for faster performance
                        vert_added = [False for i in range(len(vertlist))]
                        for bone_index, bone in enumerate(boneinfluences):
                            # find bone in exported blocks
                            bone_block = None
                            for block in self.nif_export.dict_blocks:
                                if isinstance(block, NifFormat.NiNode):
                                    if block.name.decode() == self.nif_export.objecthelper.get_full_name(b_obj_armature.data.bones[bone]):
                                        if not bone_block:
                                            bone_block = block
                                        else:
                                            raise nif_utils.NifError("Multiple bones with name '%s': "
                                                                     "probably you have multiple armatures. "
                                                                     "Please parent all meshes to a single armature and try again"
                                                                     % bone)
                            if not bone_block:
                                raise nif_utils.NifError("Bone '%s' not found." % bone)

                            # find vertex weights
                            vert_weights = {}
                            for v in vert_list[bone]:
                                # v[0] is the original vertex index
                                # v[1] is the weight

                                # vertmap[v[0]] is the set of vertices (indices)
                                # to which v[0] was mapped
                                # so we simply export the same weight as the
                                # original vertex for each new vertex

                                # write the weights
                                # extra check for multi material meshes
                                if vertmap[v[0]] and vert_norm[v[0]]:
                                    for vert_index in vertmap[v[0]]:
                                        vert_weights[vert_index] = v[1] / vert_norm[v[0]]
                                        vert_added[vert_index] = True
                            # add bone as influence, but only if there were
                            # actually any vertices influenced by the bone
                            if vert_weights:
                                trishape.add_bone(bone_block, vert_weights)

                        # update bind position skinning data
                        trishape.update_bind_position()

                        # calculate center and radius for each skin bone data
                        # block
                        trishape.update_skin_center_radius()

                        if self.nif_export.version >= 0x04020100 and NifOp.props.skin_partition:
                            NifLog.info("Creating skin partition")
                            lostweight = trishape.update_skin_partition(
                                maxbonesperpartition=NifOp.props.max_bones_per_partition,
                                maxbonespervertex=NifOp.props.max_bones_per_vertex,
                                stripify=NifOp.props.stripify,
                                stitchstrips=NifOp.props.stitch_strips,
                                padbones=NifOp.props.pad_bones,
                                triangles=trilist,
                                trianglepartmap=bodypartfacemap,
                                maximize_bone_sharing=(NifOp.props.game in ('FALLOUT_3', 'SKYRIM')))
                            # warn on bad config settings
                            if NifOp.props.game == 'OBLIVION':
                                if NifOp.props.pad_bones:
                                    NifLog.warn("Using padbones on Oblivion export. Disable the pad bones option to get higher quality skin partitions.")
                            if NifOp.props.game in ('OBLIVION', 'FALLOUT_3'):
                                if NifOp.props.max_bones_per_partition < 18:
                                    NifLog.warn("Using less than 18 bones per partition on Oblivion/Fallout 3 export."
                                                "Set it to 18 to get higher quality skin partitions.")
                            if NifOp.props.game in 'SKYRIM':
                                if NifOp.props.max_bones_per_partition < 24:
                                    NifLog.warn("Using less than 24 bones per partition on Skyrim export."
                                                "Set it to 24 to get higher quality skin partitions.")
                            if lostweight > NifOp.props.epsilon:
                                NifLog.warn("Lost {0} in vertex weights while creating a skin partition for Blender object '{1}' (nif block '{2}')".format(str(lostweight), b_obj.name, trishape.name))

                        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
                            partitions = skininst.partitions
                            b_obj_part_flags = b_obj.niftools_part_flags
                            for s_part in partitions:
                                s_part_index = NifFormat.BSDismemberBodyPartType._enumvalues.index(s_part.body_part)
                                s_part_name = NifFormat.BSDismemberBodyPartType._enumkeys[s_part_index]
                                for b_part in b_obj_part_flags:
                                    if s_part_name == b_part.name:
                                        s_part.part_flag.pf_start_net_boneset = b_part.pf_startflag
                                        s_part.part_flag.pf_editor_visible = b_part.pf_editorflag

                        # clean up
                        del vert_weights
                        del vert_added

            # shape key morphing
            key = b_mesh.shape_keys
            if key:
                if len(key.key_blocks) > 1:
                    # yes, there is a key object attached
                    # export as egm, or as morph_data?
                    if key.key_blocks[1].name.startswith("EGM"):
                        # egm export!
                        self.exportEgm(key.key_blocks)
                    elif key.ipo:
                        # regular morph_data export
                        # (there must be a shape ipo)
                        keyipo = key.ipo
                        # check that they are relative shape keys
                        if not key.relative:
                            # XXX if we do "key.relative = True"
                            # XXX would this automatically fix the keys?
                            raise ValueError("Can only export relative shape keys.")

                        # create geometry morph controller
                        morph_ctrl = self.nif_export.objecthelper.create_block("NiGeomMorpherController", keyipo)
                        morph_ctrl.target = trishape
                        morph_ctrl.frequency = 1.0
                        morph_ctrl.phase = 0.0
                        trishape.add_controller(morph_ctrl)
                        ctrl_start = 1000000.0
                        ctrl_stop = -1000000.0
                        ctrl_flags = 0x000c

                        # create geometry morph data
                        morph_data = self.nif_export.objecthelper.create_block("NiMorphData", keyipo)
                        morph_ctrl.data = morph_data
                        morph_data.num_morphs = len(key.key_blocks)
                        morph_data.num_vertices = len(vertlist)
                        morph_data.morphs.update_size()

                        # create interpolators (for newer nif versions)
                        morph_ctrl.num_interpolators = len(key.key_blocks)
                        morph_ctrl.interpolators.update_size()

                        # interpolator weights (for Fallout 3)
                        morph_ctrl.interpolator_weights.update_size()

                        # XXX some unknowns, bethesda only
                        # XXX just guessing here, data seems to be zero always
                        morph_ctrl.num_unknown_ints = len(key.key_blocks)
                        morph_ctrl.unknown_ints.update_size()

                        for keyblocknum, keyblock in enumerate(key.key_blocks):
                            # export morphed vertices
                            morph = morph_data.morphs[keyblocknum]
                            morph.frame_name = keyblock.name
                            NifLog.info("Exporting morph {0}: vertices".format(keyblock.name))
                            morph.arg = morph_data.num_vertices
                            morph.vectors.update_size()
                            for b_v_index, (vert_indices, vert) in enumerate(list(zip(vertmap, keyblock.data))):
                                # vertmap check
                                if not vert_indices:
                                    continue
                                # copy vertex and assign morph vertex
                                mv = vert.copy()
                                if keyblocknum > 0:
                                    mv.x -= b_mesh.vertices[b_v_index].co.x
                                    mv.y -= b_mesh.vertices[b_v_index].co.y
                                    mv.z -= b_mesh.vertices[b_v_index].co.z
                                for vert_index in vert_indices:
                                    morph.vectors[vert_index].x = mv.x
                                    morph.vectors[vert_index].y = mv.y
                                    morph.vectors[vert_index].z = mv.z

                            # export ipo shape key curve
                            curve = keyipo[keyblock.name]

                            # create interpolator for shape key (needs to be there even if there is no curve)
                            interpol = self.nif_export.objecthelper.create_block("NiFloatInterpolator")
                            interpol.value = 0
                            morph_ctrl.interpolators[keyblocknum] = interpol
                            # fallout 3 stores interpolators inside the interpolator_weights block
                            morph_ctrl.interpolator_weights[keyblocknum].interpolator = interpol

                            # geometry only export has no float data
                            # also skip keys that have no curve (such as base key)
                            if NifOp.props.animation == 'GEOM_NIF' or not curve:
                                continue

                            # note: we set data on morph for older nifs and on floatdata for newer nifs
                            # of course only one of these will be actually written to the file
                            NifLog.info("Exporting morph {0}: curve".format(keyblock.name))
                            interpol.data = self.nif_export.objecthelper.create_block("NiFloatData", curve)
                            floatdata = interpol.data.data
                            if curve.getExtrapolation() == "Constant":
                                ctrl_flags = 0x000c
                            elif curve.getExtrapolation() == "Cyclic":
                                ctrl_flags = 0x0008

                            morph.interpolation = NifFormat.KeyType.LINEAR_KEY
                            morph.num_keys = len(curve.getPoints())
                            morph.keys.update_size()

                            floatdata.interpolation = NifFormat.KeyType.LINEAR_KEY
                            floatdata.num_keys = len(curve.getPoints())
                            floatdata.keys.update_size()

                            for i, btriple in enumerate(curve.getPoints()):
                                knot = btriple.getPoints()
                                morph.keys[i].arg = morph.interpolation
                                morph.keys[i].time = (knot[0] - bpy.context.scene.frame_start) * self.context.scene.render.fps
                                morph.keys[i].value = curve.evaluate(knot[0])
                                # morph.keys[i].forwardTangent = 0.0 # ?
                                # morph.keys[i].backwardTangent = 0.0 # ?
                                floatdata.keys[i].arg = floatdata.interpolation
                                floatdata.keys[i].time = (knot[
                                                              0] - bpy.context.scene.frame_start) * self.context.scene.render.fps
                                floatdata.keys[i].value = curve.evaluate(
                                    knot[0])
                                # floatdata.keys[i].forwardTangent = 0.0 # ?
                                # floatdata.keys[i].backwardTangent = 0.0 # ?
                                ctrl_start = min(ctrl_start, morph.keys[i].time)
                                ctrl_stop = max(ctrl_stop, morph.keys[i].time)
                        morph_ctrl.flags = ctrl_flags
                        morph_ctrl.start_time = ctrl_start
                        morph_ctrl.stop_time = ctrl_stop

                        # fix data consistency type
                        tridata.consistency_flags = b_obj.niftools.consistency_flags

    def smooth_mesh_seams(self, b_objs):
        # get shared vertices
        NifLog.info("Smoothing seams between objects...")
        vdict = {}
        for b_obj in [b_obj for b_obj in b_objs if b_obj.type == 'MESH']:
            b_mesh = b_obj.data
            # for vertex in b_mesh.vertices:
            #    vertex.sel = False
            for poly in b_mesh.polygons:
                for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    pv_index = b_mesh.loops[loop_index].vertex_index
                    vertex = b_mesh.vertices[pv_index]
                    vertex_vec = vertex.co
                    vkey = (int(vertex_vec[0] * self.nif_export.VERTEX_RESOLUTION),
                            int(vertex_vec[1] * self.nif_export.VERTEX_RESOLUTION),
                            int(vertex_vec[2] * self.nif_export.VERTEX_RESOLUTION))
                    try:
                        vdict[vkey].append((vertex, poly, b_mesh))
                    except KeyError:
                        vdict[vkey] = [(vertex, poly, b_mesh)]

        # set normals on shared vertices
        nv = 0
        for vlist in vdict.values():
            if len(vlist) <= 1:
                continue  # not shared

            meshes = set([b_mesh for vertex, poly, b_mesh in vlist])
            if len(meshes) <= 1:
                continue  # not shared

            # take average of all face normals of polygons that have this vertex
            norm = mathutils.Vector()
            for vertex, poly, b_mesh in vlist:
                norm += poly.normal
            norm.normalize()
            # remove outliers (fixes better bodies issue) first calculate fitness of each face
            fitlist = [poly.normal.dot(norm)
                       for vertex, poly, b_mesh in vlist]
            bestfit = max(fitlist)
            # recalculate normals only taking into account
            # well-fitting polygons
            norm = mathutils.Vector()
            for (vertex, poly, b_mesh), fit in zip(vlist, fitlist):
                if fit >= bestfit - 0.2:
                    norm += poly.normal
            norm.normalize()
            # save normal of this vertex
            for vertex, poly, b_mesh in vlist:
                vertex.normal = norm
                # vertex.sel = True
            nv += 1
        NifLog.info("Fixed normals on {0} vertices.".format(str(nv)))
