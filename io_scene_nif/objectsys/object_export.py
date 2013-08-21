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

from io_scene_nif.utility import nif_utils

class ObjectHelper():


    def __init__(self, parent):
        self.nif_export = parent
        self.properties = parent.properties
        self.mesh_helper = MeshHelper(parent)
        
        # Maps exported blocks to either None or associated Blender object
        self.blocks = {}
        
        # maps Blender names to previously imported names from the FullNames
        # buffer (see self.rebuild_full_names())
        self.names = {}
        # keeps track of names of exported blocks, to make sure they are unique
        self.block_names = []
    
    
    def create_block(self, blocktype, b_obj = None):
        """Helper function to create a new block, register it in the list of
        exported blocks, and associate it with a Blender object.

        @param blocktype: The nif block type (for instance "NiNode").
        @type blocktype: C{str}
        @param b_obj: The Blender object.
        @return: The newly created block."""
        try:
            block = getattr(NifFormat, blocktype)()
        except AttributeError:
            raise nif_utils.NifExportError(
                "'%s': Unknown block type (this is probably a bug)."
                % blocktype)
        return self.register_block(block, b_obj)
    
    
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
            self.nif_export.info("Exporting %s block"%block.__class__.__name__)
        else:
            self.nif_export.info("Exporting %s as %s block"
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
                            self.nif_export.get_bone_name_for_nif(b_obj.name)
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
                    self.mesh_helper.export_tri_shapes(b_obj, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.create_ninode(b_obj)
                # does node have priority value in NULL constraint?
                for constr in b_obj.constraints:
                    if constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.nif_export.get_bone_name_for_nif(b_obj.name)
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
        node.name = self.get_full_name(node_name)

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

        self.nif_export.export_matrix(b_obj, space, node)

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
                self.mesh_helper.export_tri_shapes(b_obj, trishape_space, node)

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
        unique_name = self.nif_export.get_bone_name_for_nif(unique_name)
        # ensure uniqueness
        if unique_name in self.block_names or unique_name in list(self.names.values()):
            unique_int = 0
            old_name = unique_name
            while unique_name in self.block_names or unique_name in list(self.names.values()):
                unique_name = "%s.%02d" % (old_name, unique_int)
                unique_int += 1
        self.block_names.append(unique_name)
        self.names[b_name] = unique_name
        return unique_name


    def get_full_name(self, b_name):
        """Returns the original imported name if present, or the name by which
        the object was exported already.

        :param blender_name: Name of object as in blender.
        :type blender_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        try:
            return self.names[b_name]
        except KeyError:
            return self.get_unique_name(b_name)
    
    
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


class MeshHelper():

    def __init__(self, parent):
        self.nif_export = parent
        self.properties = parent.properties


    def export_tri_shapes(self, b_obj, space, parent_block, trishape_name = None):
        self.nif_export.info("Exporting %s" % b_obj)

        assert(b_obj.type == 'MESH')

        # get mesh from b_obj
        b_mesh = b_obj.data # get mesh data

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not b_obj.data.vertices:
            # do not export anything
            self.nif_export.warning("%s has no vertices, skipped." % b_obj)
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

        #vertex color check
        mesh_hasvcol = False
        mesh_hasvcola = False

        if(b_mesh.vertex_colors):
            mesh_hasvcol = True

            #vertex alpha check
            if(len(b_mesh.vertex_colors) == 1):
                self.nif_export.warning("Mesh only has one Vertex Color layer"
                             " default alpha values will be written\n"
                             " - For Alpha values add a second vertex layer, "
                             " greyscale only"
                             )
                mesh_hasvcola = False
            else:
                #iterate over colorfaces
                for b_meshcolor in b_mesh.vertex_colors[1].data:
                    #iterate over verts
                    for i in [0,1,2]:
                        b_color = getattr(b_meshcolor, "color%s" % (i + 1))
                        if(b_color.v > self.properties.epsilon):
                            mesh_hasvcola = True
                            break
                    if(mesh_hasvcola):
                        break

        # Non-textured materials, vertex colors are used to color the mesh
        # Textured materials, they represent lighting details

        # let's now export one trishape for every mesh material
        ### TODO: needs refactoring - move material, texture, etc.
        ### to separate function
        for materialIndex, b_mat in enumerate(mesh_materials):
            # -> first, extract valuable info from our b_obj

            mesh_texture_alpha = False #texture has transparency

            mesh_uvlayers = []    # uv layers used by this material
            mesh_hasalpha = False # mesh has transparency
            mesh_haswire = False  # mesh rendered as wireframe
            mesh_hasspec = False  # mesh specular property

            mesh_hasnormals = False
            if b_mat is not None:
                mesh_hasnormals = True # for proper lighting

                #ambient mat
                mesh_mat_ambient_color = [1.0, 1.0, 1.0]

                #diffuse mat
                mesh_mat_diffuse_color = [1.0, 1.0, 1.0]
                '''
                TODO_3.0 - If needed where ambient should not be defaulted

                #ambient mat
                mesh_mat_ambient_color[0] = b_mat.niftools.ambient_color[0] * b_mat.niftools.ambient_factor
                mesh_mat_ambient_color[1] = b_mat.niftools.ambient_color[1] * b_mat.niftools.ambient_factor
                mesh_mat_ambient_color[2] = b_mat.niftools.ambient_color[2] * b_mat.niftools.ambient_factor

                #diffuse mat
                mest_mat_diffuse_color[0] = b_mat.niftools.diffuse_color[0] * b_mat.niftools.diffuse_factor
                mest_mat_diffuse_color[1] = b_mat.niftools.diffuse_color[1] * b_mat.niftools.diffuse_factor
                mest_mat_diffuse_color[2] = b_mat.niftools.diffuse_color[2] * b_mat.niftools.diffuse_factor
                '''

                #emissive mat
                mesh_mat_emissive_color = [0.0, 0.0, 0.0]
                mesh_mat_emitmulti = 1.0 # default
                if self.properties.game != 'FALLOUT_3':
                    #old code
                    #mesh_mat_emissive_color = b_mat.diffuse_color * b_mat.emit
                    mesh_mat_emissive_color = b_mat.niftools.emissive_color * b_mat.emit

                else:
                    # special case for Fallout 3 (it does not store diffuse color)
                    # if emit is non-zero, set emissive color to diffuse
                    # (otherwise leave the color to zero)
                    if b_mat.emit > self.properties.epsilon:

                        #old code
                        #mesh_mat_emissive_color = b_mat.diffuse_color
                        mesh_mat_emissive_color = b_mat.niftools.emissive_color
                        mesh_mat_emitmulti = b_mat.emit * 10.0

                #specular mat
                mesh_mat_specular_color = b_mat.specular_color
                if b_mat.specular_intensity > 1.0:
                    b_mat.specular_intensity = 1.0

                mesh_mat_specular_color[0] *= b_mat.specular_intensity
                mesh_mat_specular_color[1] *= b_mat.specular_intensity
                mesh_mat_specular_color[2] *= b_mat.specular_intensity

                if ( mesh_mat_specular_color[0] > self.properties.epsilon ) \
                    or ( mesh_mat_specular_color[1] > self.properties.epsilon ) \
                    or ( mesh_mat_specular_color[2] > self.properties.epsilon ):
                    mesh_hasspec = True

                #gloss mat
                #'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_gloss = b_mat.specular_hardness / 4.0

                #alpha mat
                mesh_hasalpha = False
                mesh_mat_transparency = b_mat.alpha
                if(b_mat.use_transparency):
                    if(abs(mesh_mat_transparency - 1.0)> self.properties.epsilon):
                        mesh_hasalpha = True
                elif(mesh_hasvcola):
                    mesh_hasalpha = True
                elif(b_mat.animation_data and b_mat.animation_data.action.fcurves['Alpha']):
                    mesh_hasalpha = True

                #wire mat
                mesh_haswire = (b_mat.type == 'WIRE')
            
                    
            # list of body part (name, index, vertices) in this mesh
            bodypartgroups = []
            for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
                vertex_group = b_obj.vertex_groups.get(bodypartgroupname)
                if vertex_group:
                    self.nif_export.debug("Found body part %s" % bodypartgroupname)
                    bodypartgroups.append(
                        [bodypartgroupname,
                         getattr(NifFormat.BSDismemberBodyPartType,
                                 bodypartgroupname),
                         # FIXME how do you get the vertices in the group???
                         #set(vertex_group.vertices)])
                         {}])




            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

            # create a trishape block
            if not self.properties.stripify:
                trishape = self.nif_export.objecthelper.create_block("NiTriShape", b_obj)
            else:
                trishape = self.nif_export.objecthelper.create_block("NiTriStrips", b_obj)

            # fill in the NiTriShape's non-trivial values
            if isinstance(parent_block, NifFormat.RootCollisionNode):
                trishape.name = b""
            elif not trishape_name:
                if parent_block.name:
                    trishape.name = "Tri " + parent_block.name
                else:
                    trishape.name = "Tri " + b_obj.name
            else:
                trishape.name = trishape_name

            if len(mesh_materials) > 1:
                # multimaterial meshes: add material index
                # (Morrowind's child naming convention)
                b_name = trishape.name.decode() + ":%i" % materialIndex                
            trishape.name = self.nif_export.objecthelper.get_full_name(trishape.name)

            #Trishape Flags...
            if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
                trishape.flags = 0x000E

            elif self.properties.game in ('SID_MEIER_S_RAILROADS',
                                         'CIVILIZATION_IV'):
                trishape.flags = 0x0010
            elif self.properties.game in ('EMPIRE_EARTH_II',):
                trishape.flags = 0x0016
            elif self.properties.game in ('DIVINITY_2',):
                if trishape.name.lower[-3:] in ("med", "low"):
                    trishape.flags = 0x0014
                else:
                    trishape.flags = 0x0016
            else:
                # morrowind
                if b_obj.draw_type != 'WIRE': # not wire
                    trishape.flags = 0x0004 # use triangles as bounding box
                else:
                    trishape.flags = 0x0005 # use triangles as bounding box + hide

            # extra shader for Sid Meier's Railroads
            if self.properties.game == 'SID_MEIER_S_RAILROADS':
                trishape.has_shader = True
                trishape.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                trishape.unknown_integer = -1 # default

            self.nif_export.export_matrix(b_obj, space, trishape)

            if self.properties.game == 'FALLOUT_3':
                bs_shader = self.export_bs_shader_property(b_mat)
                
                self.nif_export.objecthelper.register_block(bs_shader)
                trishape.add_property(bs_shader)
            else:
                if self.properties.game in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES:
                    # sid meier's railroad and civ4:
                    # set shader slots in extra data
                    self.nif_export.texturehelper.add_shader_integer_extra_datas(trishape)
                    
                n_nitextureprop = self.nif_export.texturehelper.export_texturing_property(
                    flags=0x0001, # standard
                    applymode=self.nif_export.get_n_apply_mode_from_b_blend_type('MIX'),
#                         mesh_base_mtex.blend_type
#                         if mesh_base_mtex else 
                    b_mat=b_mat, b_obj=b_obj)
                
                self.nif_export.objecthelper.register_block(n_nitextureprop)
            
            trishape.add_property(n_nitextureprop)
            
            # add texture effect block (must be added as preceeding child of
            # the trishape)
            if self.properties.game == 'MORROWIND' and mesh_texeff_mtex:
                # create a new parent block for this shape
                extra_node = self.nif_export.create_block("NiNode", mesh_texeff_mtex)
                parent_block.add_child(extra_node)
                # set default values for this ninode
                extra_node.rotation.set_identity()
                extra_node.scale = 1.0
                extra_node.flags = 0x000C # morrowind
                # create texture effect block and parent the
                # texture effect and trishape to it
                texeff = self.export_texture_effect(mesh_texeff_mtex)
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
                if self.properties.game == 'SID_MEIER_S_RAILROADS':
                    alphaflags = 0x32ED
                    alphathreshold = 150
                elif self.properties.game == 'EMPIRE_EARTH_II':
                    alphaflags = 0x00ED
                    alphathreshold = 0
                else:
                    alphaflags = 0x12ED
                    alphathreshold = 0
                trishape.add_property(
                    self.propertyhelper.object_property.export_alpha_property(flags=alphaflags,
                                                                              threshold=alphathreshold))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.add_property(self.propertyhelper.object_property.export_wireframe_property(flags=1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.add_property(self.propertyhelper.object_property.export_stencil_property())

            if b_mat:
                # add NiTriShape's specular property
                # but NOT for sid meier's railroads and other extra shader
                # games (they use specularity even without this property)
                if (mesh_hasspec
                    and (self.properties.game
                         not in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES)):
                    # refer to the specular property in the trishape block
                    trishape.add_property(
                        self.nif_export.propertyhelper.object_property.export_specular_property(flags=0x0001))

                # add NiTriShape's material property
                trimatprop = self.nif_export.propertyhelper.material_property.export_material_property(
                    name=self.nif_export.objecthelper.get_full_name(b_mat.name),
                    flags=0x0001, # TODO - standard flag, check?
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
                self.nif_export.animationhelper.material_animation.export_material_controllers(
                    b_material=b_mat, n_geom=trishape)





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
            
            mesh_uvlayers = self.nif_export.texturehelper.mesh_uvlayers
            vertquad_list = [] # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [None for i in range(len(b_mesh.vertices))] # blender vertex -> nif vertices
            vertlist = []
            normlist = []
            vcollist = []
            uvlist = []
            trilist = []
            # for each face in trilist, a body part index
            bodypartfacemap = []
            faces_without_bodypart = []
            for f in b_mesh.faces:
                # does the face belong to this trishape?
                if (b_mat != None): # we have a material
                    if (f.material_index != materialIndex): # but this face has another material
                        continue # so skip this face
                f_numverts = len(f.vertices)
                if (f_numverts < 3): continue # ignore degenerate faces
                assert((f_numverts == 3) or (f_numverts == 4)) # debug
                if mesh_uvlayers:
                    # if we have uv coordinates
                    # double check that we have uv data
                    # XXX should we check that every uvlayer in mesh_uvlayers
                    # XXX is in uv_textures?
                    if not b_mesh.uv_textures:
                        raise NifExportError(
                            "ERROR%t|Create a UV map for every texture,"
                            " and run the script again.")
                # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
                f_index = [ -1 ] * f_numverts
                for i, fv_index in enumerate(f.vertices):
                    fv = b_mesh.vertices[fv_index].co
                    # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                    if mesh_hasnormals:
                        if f.use_smooth:
                            fn = b_mesh.vertices[fv_index].normal
                        else:
                            fn = f.normal
                    else:
                        fn = None
                    fuv = []
                    for uvlayer in mesh_uvlayers:
                        fuv.append(
                            getattr(b_mesh.uv_textures[uvlayer].data[f.index],
                                    "uv%i" % (i + 1)))

                    fcol = None

                    '''TODO: Need to map b_verts -> n_verts'''
                    if mesh_hasvcol:
                        vertcol = []
                        #check for an alpha layer
                        b_meshcolor = b_mesh.vertex_colors[0].data[f.index]
                        b_color = getattr(b_meshcolor, "color%s" % (i + 1))
                        if(mesh_hasvcola):
                            b_meshcoloralpha = b_mesh.vertex_colors[1].data[f.index]
                            b_colora = getattr(b_meshcolor, "color%s" % (i + 1))
                            vertcol = [b_color.r, b_color.g, b_color.b, b_colora.v]
                        else:
                            vertcol = [b_color.r, b_color.g, b_color.b, 1.0]
                        fcol = vertcol

                    else:
                        fcol = None

                    vertquad = ( fv, fuv, fn, fcol )

                    # do we already have this vertquad? (optimized by m_4444x)
                    f_index[i] = len(vertquad_list)
                    if vertmap[fv_index]:
                        # iterate only over vertices with the same vertex index
                        # and check if they have the same uvs, normals and colors (wow is that fast!)
                        for j in vertmap[fv_index]:
                            if mesh_uvlayers:
                                if max(abs(vertquad[1][uvlayer][0] - vertquad_list[j][1][uvlayer][0])
                                       for uvlayer in range(len(mesh_uvlayers))) \
                                       > self.properties.epsilon:
                                    continue
                                if max(abs(vertquad[1][uvlayer][1] - vertquad_list[j][1][uvlayer][1])
                                       for uvlayer in range(len(mesh_uvlayers))) \
                                       > self.properties.epsilon:
                                    continue
                            if mesh_hasnormals:
                                if abs(vertquad[2][0] - vertquad_list[j][2][0]) > self.properties.epsilon: continue
                                if abs(vertquad[2][1] - vertquad_list[j][2][1]) > self.properties.epsilon: continue
                                if abs(vertquad[2][2] - vertquad_list[j][2][2]) > self.properties.epsilon: continue
                            if mesh_hasvcol:
                                if abs(vertquad[3][0] - vertquad_list[j][3][0]) > self.properties.epsilon: continue
                                if abs(vertquad[3][1] - vertquad_list[j][3][1]) > self.properties.epsilon: continue
                                if abs(vertquad[3][2] - vertquad_list[j][3][2]) > self.properties.epsilon: continue
                                if abs(vertquad[3][3] - vertquad_list[j][3][3]) > self.properties.epsilon: continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise NifExportError(
                            "ERROR%t|Too many vertices. Decimate your mesh"
                            " and try again.")
                    if (f_index[i] == len(vertquad_list)):
                        # first: add it to the vertex map
                        if not vertmap[fv_index]:
                            vertmap[fv_index] = []
                        vertmap[fv_index].append(len(vertquad_list))
                        # new (vert, uv-vert, normal, vcol) quad: add it
                        vertquad_list.append(vertquad)
                        # add the vertex
                        vertlist.append(vertquad[0])
                        if mesh_hasnormals: normlist.append(vertquad[2])
                        if mesh_hasvcol:    vcollist.append(vertquad[3])
                        if mesh_uvlayers:   uvlist.append(vertquad[1])

                # now add the (hopefully, convex) face, in triangles
                for i in range(f_numverts - 2):
                    if True: #TODO: #(b_obj_scale > 0):
                        f_indexed = (f_index[0], f_index[1+i], f_index[2+i])
                    else:
                        f_indexed = (f_index[0], f_index[2+i], f_index[1+i])
                    trilist.append(f_indexed)
                    # add body part number
                    if (self.properties.game != 'FALLOUT_3'
                        or not bodypartgroups
                        or not self.EXPORT_FO3_BODYPARTS):
                        bodypartfacemap.append(0)
                    else:
                        for bodypartname, bodypartindex, bodypartverts in bodypartgroups:
                            if (set(b_vert_index for b_vert_index in f.vertices)
                                <= bodypartverts):
                                bodypartfacemap.append(bodypartindex)
                                break
                        else:
                            # this signals an error
                            faces_without_bodypart.append(f)

            # check that there are no missing body part faces
            if faces_without_bodypart:
                # switch to edit mode to select faces
                bpy.ops.object.mode_set(mode='EDIT',toggle=False)
                # select mesh object
                for b_obj in self.context.scene.objects:
                    b_obj.select = False
                self.context.scene.objects.active = b_obj
                b_obj.select = True
                # select bad faces
                for face in b_mesh.faces:
                    face.select = False
                for face in faces_without_bodypart:
                    face.select = True
                # raise exception
                raise ValueError(
                    "Some faces of %s not assigned to any body part."
                    " The unassigned faces"
                    " have been selected in the mesh so they can easily"
                    " be identified."
                    % b_obj)

            if len(trilist) > 65535:
                raise NifExportError(
                    "ERROR%t|Too many faces. Decimate your mesh and try again.")
            if len(vertlist) == 0:
                continue # m_4444x: skip 'empty' material indices

            
            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = self.nif_export.objecthelper.create_block("NiTriShapeData", b_obj)
            else:
                tridata = self.nif_export.objecthelper.create_block("NiTriStripsData", b_obj)
            trishape.data = tridata

            # flags
            tridata.consistency_flags = NifFormat.ConsistencyType.CT_STATIC

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

            if mesh_uvlayers:
                tridata.num_uv_sets = len(mesh_uvlayers)
                tridata.bs_num_uv_sets = len(mesh_uvlayers)
                if self.properties.game == 'FALLOUT_3':
                    if len(mesh_uvlayers) > 1:
                        raise NifExportError(
                            "Fallout 3 does not support multiple UV layers")
                tridata.has_uv = True
                tridata.uv_sets.update_size()
                for j, uvlayer in enumerate(mesh_uvlayers):
                    for i, uv in enumerate(tridata.uv_sets[j]):
                        uv.u = uvlist[i][j][0]
                        uv.v = 1.0 - uvlist[i][j][1] # opengl standard

            # set triangles
            # stitch strips for civ4
            tridata.set_triangles(trilist,
                                 stitchstrips=self.properties.stitch_strips)

            # update tangent space (as binary extra data only for Oblivion)
            # for extra shader texture games, only export it if those
            # textures are actually exported (civ4 seems to be consistent with
            # not using tangent space on non shadered nifs)
            if mesh_uvlayers and mesh_hasnormals:
                if (self.properties.game in ('OBLIVION', 'FALLOUT_3')
                    or (self.properties.game in self.nif_export.texturehelper.USED_EXTRA_SHADER_TEXTURES)):
                    trishape.update_tangent_space(
                        as_extra=(self.properties.game == 'OBLIVION'))

            # now export the vertex weights, if there are any
            vertgroups = {vertex_group.name
                          for vertex_group in b_obj.vertex_groups}
            bone_names = []
            if b_obj.parent:
                if b_obj.parent.type == 'ARMATURE':
                    b_obj_armature = b_obj.parent
                    armaturename = b_obj_armature.name
                    bone_names = list(b_obj_armature.data.bones.keys())
                    # the vertgroups that correspond to bone_names are bones
                    # that influence the mesh
                    boneinfluences = []
                    for bone in bone_names:
                        if bone in vertgroups:
                            boneinfluences.append(bone)
                    if boneinfluences: # yes we have skinning!
                        # create new skinning instance block and link it
                        if (self.properties.game == 'FALLOUT_3'
                            and self.EXPORT_FO3_BODYPARTS):
                            skininst = self.nif_export.objecthelper.create_block("BSDismemberSkinInstance", b_obj)
                        else:
                            skininst = self.nif_export.objecthelper.create_block("NiSkinInstance", b_obj)
                        trishape.skin_instance = skininst
                        for block in self.objecthelper.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name.decode() == self.get_full_name(armaturename):
                                    skininst.skeleton_root = block
                                    break
                        else:
                            raise NifExportError(
                                "Skeleton root '%s' not found."
                                % armaturename)

                        # create skinning data and link it
                        skindata = self.nif_export.objecthelper.create_block("NiSkinData", b_obj)
                        skininst.data = skindata

                        skindata.has_vertex_weights = True
                        # fix geometry rest pose: transform relative to
                        # skeleton root
                        skindata.set_transform(
                            self.get_object_matrix(b_obj, 'localspace').get_inverse())
                       
                        # Vertex weights,  find weights and normalization factors
                        vert_list = {}
                        vert_norm = {}
                        unassigned_verts = []
                                                
                        for bone_group in boneinfluences:
                            b_list_weight = []
                            b_vert_group = b_obj.vertex_groups[bone_group]
                            
                            for b_vert in b_obj.data.vertices:
                                if len(b_vert.groups) == 0: #check vert has weight_groups
                                    unassigned_verts.append(b_vert)
                                    continue
                                
                                for g in b_vert.groups:
                                    if b_vert_group.name in boneinfluences:
                                        if g.group == b_vert_group.index:
                                            b_list_weight.append((b_vert.index, g.weight))
                                            break
                                                
                            vert_list[bone_group] = b_list_weight             
                            
                            #create normalisation groupings
                            for v in vert_list[bone_group]:
                                if v[0] in vert_norm:
                                    vert_norm[v[0]] += v[1]
                                else:
                                    vert_norm[v[0]] = v[1]
                        
                        # vertices must be assigned at least one vertex group
                        # lets be nice and display them for the user 
                        if len(unassigned_verts) > 0:
                            for b_scene_obj in self.context.scene.objects:
                                b_scene_obj.select = False
                                
                            self.context.scene.objects.active = b_obj
                            b_obj.select = True
                            
                            # select unweighted vertices
                            for v in b_mesh.vertices:
                                v.select = False    
                            
                            for b_vert in unassigned_verts:
                                b_mesh.data.vertices[b_vert.index].select = True
                                
                            # switch to edit mode and raise exception
                            bpy.ops.object.mode_set(mode='EDIT',toggle=False)
                            raise NifExportError(
                                "Cannot export mesh with unweighted vertices."
                                " The unweighted vertices have been selected"
                                " in the mesh so they can easily be"
                                " identified.")
                        
                        
                        # for each bone, first we get the bone block
                        # then we get the vertex weights
                        # and then we add it to the NiSkinData
                        # note: allocate memory for faster performance
                        vert_added = [False for i in range(len(vertlist))]
                        for bone_index, bone in enumerate(boneinfluences):
                            # find bone in exported blocks
                            bone_block = None
                            for block in self.objecthelper.blocks:
                                if isinstance(block, NifFormat.NiNode):
                                    if block.name.decode() == self.get_full_name(bone):
                                        if not bone_block:
                                            bone_block = block
                                        else:
                                            raise NifExportError(
                                                "multiple bones"
                                                " with name '%s': probably"
                                                " you have multiple armatures,"
                                                " please parent all meshes"
                                                " to a single armature"
                                                " and try again"
                                                % bone)
                            
                            if not bone_block:
                                raise NifExportError(
                                    "Bone '%s' not found." % bone)
                            
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

                        if (self.nif_export.version >= 0x04020100
                            and self.properties.skin_partition):
                            self.info("Creating skin partition")
                            lostweight = trishape.update_skin_partition(
                                maxbonesperpartition=self.properties.max_bones_per_partition,
                                maxbonespervertex=self.properties.max_bones_per_vertex,
                                stripify=self.properties.stripify,
                                stitchstrips=self.properties.stitch_strips,
                                padbones=self.properties.pad_bones,
                                triangles=trilist,
                                trianglepartmap=bodypartfacemap,
                                maximize_bone_sharing=(
                                    self.properties.game == 'FALLOUT_3'))
                            # warn on bad config settings
                            if self.properties.game == 'OBLIVION':
                               if self.properties.pad_bones:
                                   self.warning(
                                       "Using padbones on Oblivion export,"
                                       " but you probably do not want to do"
                                       " this."
                                       " Disable the pad bones option to get"
                                       " higher quality skin partitions.")
                            if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
                               if self.properties.max_bones_per_partition < 18:
                                   self.warning(
                                       "Using less than 18 bones"
                                       " per partition on Oblivion/Fallout 3"
                                       " export."
                                       " Set it to 18 to get higher quality"
                                       " skin partitions.")
                            if lostweight > self.properties.epsilon:
                                self.warning(
                                    "Lost %f in vertex weights"
                                    " while creating a skin partition"
                                    " for Blender object '%s' (nif block '%s')"
                                    % (lostweight, b_obj.name, trishape.name))

                        # clean up
                        del vert_weights
                        del vert_added


            # shape key morphing
            key = b_mesh.shape_keys
            if key:
                if len(key.key_blocks) > 1:
                    # yes, there is a key object attached
                    # export as egm, or as morphdata?
                    if key.key_blocks[1].name.startswith("EGM"):
                        # egm export!
                        self.exportEgm(key.key_blocks)
                    elif key.ipo:
                        # regular morphdata export
                        # (there must be a shape ipo)
                        keyipo = key.ipo
                        # check that they are relative shape keys
                        if not key.relative:
                            # XXX if we do "key.relative = True"
                            # XXX would this automatically fix the keys?
                            raise ValueError(
                                "Can only export relative shape keys.")

                        # create geometry morph controller
                        morphctrl = self.nif_export.objecthelper.create_block("NiGeomMorpherController",
                                                     keyipo)
                        trishape.add_controller(morphctrl)
                        morphctrl.target = trishape
                        morphctrl.frequency = 1.0
                        morphctrl.phase = 0.0
                        ctrlStart = 1000000.0
                        ctrlStop = -1000000.0
                        ctrlFlags = 0x000c

                        # create geometry morph data
                        morphdata = self.nif_export.objecthelper.create_block("NiMorphData", keyipo)
                        morphctrl.data = morphdata
                        morphdata.num_morphs = len(key.key_blocks)
                        morphdata.num_vertices = len(vertlist)
                        morphdata.morphs.update_size()


                        # create interpolators (for newer nif versions)
                        morphctrl.num_interpolators = len(key.key_blocks)
                        morphctrl.interpolators.update_size()

                        # interpolator weights (for Fallout 3)
                        morphctrl.interpolator_weights.update_size()

                        # XXX some unknowns, bethesda only
                        # XXX just guessing here, data seems to be zero always
                        morphctrl.num_unknown_ints = len(key.key_blocks)
                        morphctrl.unknown_ints.update_size()

                        for keyblocknum, keyblock in enumerate(key.key_blocks):
                            # export morphed vertices
                            morph = morphdata.morphs[keyblocknum]
                            morph.frame_name = keyblock.name
                            self.info("Exporting morph %s: vertices"
                                             % keyblock.name)
                            morph.arg = morphdata.num_vertices
                            morph.vectors.update_size()
                            for b_v_index, (vert_indices, vert) \
                                in enumerate(list(zip(vertmap, keyblock.data))):
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

                            # create interpolator for shape key
                            # (needs to be there even if there is no curve)
                            interpol = self.nif_export.objecthelper.create_block("NiFloatInterpolator")
                            interpol.value = 0
                            morphctrl.interpolators[keyblocknum] = interpol
                            # fallout 3 stores interpolators inside the
                            # interpolator_weights block
                            morphctrl.interpolator_weights[keyblocknum].interpolator = interpol

                            # geometry only export has no float data
                            # also skip keys that have no curve (such as base key)
                            if self.properties.animation == 'GEOM_NIF' or not curve:
                                continue

                            # note: we set data on morph for older nifs
                            # and on floatdata for newer nifs
                            # of course only one of these will be actually
                            # written to the file
                            self.info("Exporting morph %s: curve"
                                             % keyblock.name)
                            interpol.data = self.nif_export.objecthelper.create_block("NiFloatData", curve)
                            floatdata = interpol.data.data
                            if curve.getExtrapolation() == "Constant":
                                ctrlFlags = 0x000c
                            elif curve.getExtrapolation() == "Cyclic":
                                ctrlFlags = 0x0008
                            morph.interpolation = NifFormat.KeyType.LINEAR_KEY
                            morph.num_keys = len(curve.getPoints())
                            morph.keys.update_size()
                            floatdata.interpolation = NifFormat.KeyType.LINEAR_KEY
                            floatdata.num_keys = len(curve.getPoints())
                            floatdata.keys.update_size()
                            for i, btriple in enumerate(curve.getPoints()):
                                knot = btriple.getPoints()
                                morph.keys[i].arg = morph.interpolation
                                morph.keys[i].time = (knot[0] - self.context.scene.frame_start) * self.context.scene.render.fps
                                morph.keys[i].value = curve.evaluate( knot[0] )
                                #morph.keys[i].forwardTangent = 0.0 # ?
                                #morph.keys[i].backwardTangent = 0.0 # ?
                                floatdata.keys[i].arg = floatdata.interpolation
                                floatdata.keys[i].time = (knot[0] - self.context.scene.frame_start) * self.context.scene.render.fps
                                floatdata.keys[i].value = curve.evaluate( knot[0] )
                                #floatdata.keys[i].forwardTangent = 0.0 # ?
                                #floatdata.keys[i].backwardTangent = 0.0 # ?
                                ctrlStart = min(ctrlStart, morph.keys[i].time)
                                ctrlStop  = max(ctrlStop,  morph.keys[i].time)
                        morphctrl.flags = ctrlFlags
                        morphctrl.start_time = ctrlStart
                        morphctrl.stop_time = ctrlStop
                        # fix data consistency type
                        tridata.consistency_flags = NifFormat.ConsistencyType.CT_VOLATILE


    def smooth_mesh_seams(self, b_objs):
        # get shared vertices
        self.nif_export.info("Smoothing seams between objects...")
        vdict = {}
        for b_obj in [b_obj for b_obj in b_objs if b_obj.type == 'MESH']:
            b_mesh = b_obj.data
            # for v in b_mesh.vertices:
            #    v.sel = False
            for f in b_mesh.faces:
                for v_index in f.vertices:
                    v = b_mesh.vertices[v_index]
                    vkey = (int(v.co[0]*self.nif_export.VERTEX_RESOLUTION),
                            int(v.co[1]*self.nif_export.VERTEX_RESOLUTION),
                            int(v.co[2]*self.nif_export.VERTEX_RESOLUTION))
                    try:
                        vdict[vkey].append((v, f, b_mesh))
                    except KeyError:
                        vdict[vkey] = [(v, f, b_mesh)]
        # set normals on shared vertices
        nv = 0
        for vlist in vdict.values():
            if len(vlist) <= 1: continue # not shared
            meshes = set([b_mesh for v, f, b_mesh in vlist])
            if len(meshes) <= 1: continue # not shared
            # take average of all face normals of faces that have this
            # vertex
            norm = mathutils.Vector()
            for v, f, b_mesh in vlist:
                norm += f.normal
            norm.normalize()
            # remove outliers (fixes better bodies issue)
            # first calculate fitness of each face
            fitlist = [f.normal.dot(norm)
                       for v, f, b_mesh in vlist]
            bestfit = max(fitlist)
            # recalculate normals only taking into account
            # well-fitting faces
            norm = mathutils.Vector()
            for (v, f, b_mesh), fit in zip(vlist, fitlist):
                if fit >= bestfit - 0.2:
                    norm += f.normal
            norm.normalize()
            # save normal of this vertex
            for v, f, b_mesh in vlist:
                v.normal = norm
                # v.sel = True
            nv += 1
        self.nif_export.info("Fixed normals on %i vertices." % nv)
    
    