"""This script imports Netimmerse/Gamebryo nif files to Blender."""

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

from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog
from io_scene_nif.io.nif import NifFile
from io_scene_nif.io.kf import KFFile
from io_scene_nif.io.egm import EGMFile 

from io_scene_nif.modules.animation.animation_import import AnimationHelper
from io_scene_nif.modules import armature
from io_scene_nif.modules.armature.armature_import import Armature
from io_scene_nif.modules.collision.collision_import import bhkshape_import, bound_import
from io_scene_nif.modules.constraint.constraint_import import constraint_import
from io_scene_nif.modules.property.material.material_import import Material
from io_scene_nif.modules.property.texture.texture_import import Texture
from io_scene_nif.modules.property.texture.texture_loader import TextureLoader
from io_scene_nif.modules.object.object_import import Object
from io_scene_nif.modules.scene import scene_import
from io_scene_nif.utility.nif_global import NifOp

import bpy
import mathutils

import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat


class NifImport(NifCommon):

    IMPORT_EXPORTEMBEDDEDTEXTURES = False

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator)
        
        self.root_ninode = 'NiNode'

        # Helper systems
        self.animationhelper = AnimationHelper(parent=self)
        self.armaturehelper = Armature(parent=self)
        # TODO: create super collisionhelper
        self.bhkhelper = bhkshape_import(parent=self)
        self.boundhelper = bound_import(parent=self)
        self.constrainthelper = constraint_import(parent=self)
        self.textureloader = TextureLoader(parent=self)
        self.texturehelper = Texture(parent=self)
        self.texturehelper.set_texture_loader(self.textureloader)
        self.materialhelper = Material(parent=self)
        self.materialhelper.set_texture_helper(self.texturehelper)
        self.objecthelper = Object(parent=self)
             
    def execute(self):
        """Main import function."""

        self.dict_havok_objects = {}
        self.dict_names = {}
        self.dict_blocks = {}
        self.dict_block_names = []
        self.dict_materials = {}
        self.dict_textures = {}
        self.dict_mesh_uvlayers = []

        # catch nif import errors
        try:
            # check that one armature is selected in 'import geometry + parent
            # to armature' mode
            if NifOp.props.skeleton == "GEOMETRY_ONLY":
                if (len(self.selected_objects) != 1
                    or self.selected_objects[0].type != 'ARMATURE'):
                    raise nif_utils.NifError(
                        "You must select exactly one armature in"
                        " 'Import Geometry Only + Parent To Selected Armature'"
                        " mode.")

            #the axes used for bone correction depend on the nif version
            armature.set_bone_orientation(NifOp.props.axis_forward, NifOp.props.axis_up)

            self.data = NifFile.load_nif(NifOp.props.filepath)
            if NifOp.props.override_scene_info:
                scene_import.import_version_info(self.data)

            egm_path = NifOp.props.egm_file
            if egm_path:
                self.egmdata = EGMFile.load_egm(egm_path)
                # scale the data
                self.egmdata.apply_scale(NifOp.props.scale_correction_import)
            else:
                self.egmdata = None

            NifLog.info("Importing data")
            # calculate and set frames per second
            if NifOp.props.animation:
                self.animationhelper.set_frames_per_second(self.data.roots)
                # + (self.kfdata.roots if self.kfdata else []) )
            
            # merge skeleton roots and transform geometry into the rest pose
            if NifOp.props.merge_skeleton_roots:
                pyffi.spells.nif.fix.SpellMergeSkeletonRoots(data=self.data).recurse()
            if NifOp.props.send_geoms_to_bind_pos:
                pyffi.spells.nif.fix.SpellSendGeometriesToBindPosition(data=self.data).recurse()
            if NifOp.props.send_detached_geoms_to_node_pos:
                pyffi.spells.nif.fix.SpellSendDetachedGeometriesToNodePosition(data=self.data).recurse()
            if NifOp.props.send_bones_to_bind_position:
                pyffi.spells.nif.fix.SpellSendBonesToBindPosition(data=self.data).recurse()
            if NifOp.props.apply_skin_deformation:
                
                # TODO Create function & move to object/mesh class
                for n_geom in self.data.get_global_iterator():
                    if not isinstance(n_geom, NifFormat.NiGeometry):
                        continue
                    if not n_geom.is_skin():
                        continue
                    NifLog.info('Applying skin deformation on geometry {0}'.format(n_geom.name))
                    vertices = n_geom.get_skin_deformation()[0]
                    for vold, vnew in zip(n_geom.data.vertices, vertices):
                        vold.x = vnew.x
                        vold.y = vnew.y
                        vold.z = vnew.z

            # scale tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = NifOp.props.scale_correction_import
            pyffi.spells.nif.fix.SpellScale(data=self.data, toaster=toaster).recurse()

            # import all root blocks
            for block in self.data.roots:
                root = block
                # root hack for corrupt better bodies meshes
                # and remove geometry from better bodies on skeleton import
                for b in (b for b in block.tree()
                          if isinstance(b, NifFormat.NiGeometry)
                          and b.is_skin()):
                    # check if root belongs to the children list of the
                    # skeleton root (can only happen for better bodies meshes)
                    if root in [c for c in b.skin_instance.skeleton_root.children]:
                        # fix parenting and update transform accordingly
                        b.skin_instance.data.set_transform(
                            root.get_transform()
                            * b.skin_instance.data.get_transform())
                        b.skin_instance.skeleton_root = root
                        # delete non-skeleton nodes if we're importing
                        # skeleton only
                        if NifOp.props.skeleton == "SKELETON_ONLY":
                            nonbip_children = (child for child in root.children
                                               if child.name[:6] != 'Bip01 ')
                            for child in nonbip_children:
                                root.remove_child(child)
                # import this root block
                NifLog.debug("Root block: {0}".format(root.get_global_display()))
                # # merge animation from kf tree into nif tree
                # if NifOp.props.animation and self.kfdata:
                    # for kf_root in self.kfdata.roots:
                        # self.animationhelper.import_kf_root(kf_root, root)
                # import the nif tree
                self.import_root(root)
        finally:
            # clear progress bar
            NifLog.info("Finished")
            # XXX no longer needed?
            # do a full scene update to ensure that transformations are applied
            bpy.context.scene.update()

        return {'FINISHED'}
     
    
    

    def import_root(self, root_block):
        """Main import function."""
        # check that this is not a kf file
        if isinstance(root_block, (NifFormat.NiSequence, NifFormat.NiSequenceStreamHelper)):
            raise nif_utils.NifError("Use the KF import operator to load KF files.")

        # divinity 2: handle CStreamableAssetData
        if isinstance(root_block, NifFormat.CStreamableAssetData):
            root_block = root_block.root

        # sets the root block parent to None, so that when crawling back the
        # script won't barf
        root_block._parent = None

        # set the block parent through the tree, to ensure I can always move
        # backward
        self.set_parents(root_block)
        self.bsxflags = self.objecthelper.import_bsxflag_data(root_block)
        self.upbflags = self.objecthelper.import_upbflag_data(root_block)
        self.objectflags = root_block.flags
        
        if isinstance(root_block, NifFormat.BSFadeNode):
            self.root_ninode = 'BSFadeNode'
            
        # mark armature nodes and bones
        self.armaturehelper.mark_armatures_bones(root_block)

        # import the keyframe notes
        if NifOp.props.animation:
            self.animationhelper.import_text_keys(root_block)

        # read the NIF tree
        if self.armaturehelper.is_armature_root(root_block):
            # special case 1: root node is skeleton root
            NifLog.debug("{0} is an armature root".format(root_block.name))
            b_obj = self.import_branch(root_block)
            b_obj.niftools.objectflags = root_block.flags

        elif self.is_grouping_node(root_block):
            # special case 2: root node is grouping node
            NifLog.debug("{0} is a grouping node".format(root_block.name))
            b_obj = self.import_branch(root_block)
            b_obj.niftools.bsxflags = self.bsxflags

        elif isinstance(root_block, NifFormat.NiTriBasedGeom):
            # trishape/tristrips root
            b_obj = self.import_branch(root_block)
            b_obj.niftools.bsxflags = self.bsxflags

        elif isinstance(root_block, NifFormat.NiNode):
            # root node is dummy scene node
            for n_extra in root_block.get_extra_datas():
                if isinstance(n_extra, NifFormat.BSBound):
                    self.boundhelper.import_bounding_box(n_extra)
            # process collision
            if root_block.collision_object:
                bhk_body = root_block.collision_object.body
                if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                    NifLog.warn("Unsupported collision structure under node {0}".format(root_block.name))
                self.bhkhelper.import_bhk_shape(bhkshape=bhk_body)

            # process all its children
            for child in root_block.children:
                b_obj = self.import_branch(child)

        elif isinstance(root_block, NifFormat.NiCamera):
            NifLog.warn('Skipped NiCamera root')

        elif isinstance(root_block, NifFormat.NiPhysXProp):
            NifLog.warn('Skipped NiPhysXProp root')

        else:
            NifLog.warn("Skipped unsupported root block type '{0}' (corrupted nif?).".format(root_block.__class__))

        if hasattr(root_block, "extra_data_list"):
            for n_extra_list in root_block.extra_data_list:
                if isinstance(n_extra_list, NifFormat.BSInvMarker):
                    b_obj.niftools_bs_invmarker.add()
                    b_obj.niftools_bs_invmarker[0].name = n_extra_list.name.decode()
                    b_obj.niftools_bs_invmarker[0].bs_inv_x = n_extra_list.rotation_x
                    b_obj.niftools_bs_invmarker[0].bs_inv_y = n_extra_list.rotation_y
                    b_obj.niftools_bs_invmarker[0].bs_inv_z = n_extra_list.rotation_z
                    b_obj.niftools_bs_invmarker[0].bs_inv_zoom = n_extra_list.zoom



        if self.root_ninode:
            b_obj.niftools.rootnode = self.root_ninode

        # now all havok objects are imported, so we are
        # ready to import the havok constraints
        self.bhkhelper.get_havok_objects()
        self.constrainthelper.import_bhk_constraints()

        # parent selected meshes to imported skeleton
        if NifOp.props.skeleton == "SKELETON_ONLY":
            # set parenting
            bpy.ops.object.parent_set(type='OBJECT')
            scn = bpy.context.scene
            scn.objects.active = b_obj
            scn.update()


    def import_branch(self, niBlock, b_armature=None, n_armature=None):
        """Read the content of the current NIF tree branch to Blender
        recursively.

        :param niBlock: The nif block to import.
        :param b_armature: The blender armature for the current branch.
        :param n_armature: The corresponding nif block for the armature for
            the current branch.
        """
        NifLog.info("Importing data")
        if not niBlock:
            return None
        elif (isinstance(niBlock, NifFormat.NiTriBasedGeom)
              and NifOp.props.skeleton != "SKELETON_ONLY"):
            # it's a shape node and we're not importing skeleton only
            # (NifOp.props.skeleton ==  "SKELETON_ONLY")
            NifLog.debug("Building mesh in import_branch")
            # note: transform matrix is set during import
            self.active_obj_name = niBlock.name.decode()
            b_obj = self.import_mesh(niBlock)
            b_obj.niftools.objectflags = niBlock.flags

            if niBlock.properties:
                for b_prop in niBlock.properties:
                    self.import_shader_types(b_obj, b_prop)
            elif niBlock.bs_properties:
                for b_prop in niBlock.bs_properties:
                    self.import_shader_types(b_obj, b_prop)
                                
            if niBlock.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
                cf_index = NifFormat.ConsistencyType._enumvalues.index(niBlock.data.consistency_flags)
                b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]
                b_obj.niftools.bsnumuvset = niBlock.data.bs_num_uv_sets
            # skinning? add armature modifier
            if niBlock.skin_instance:
                self.armaturehelper.append_armature_modifier(b_obj, b_armature)
            return b_obj
        elif isinstance(niBlock, NifFormat.NiNode):
            children = niBlock.children
            # import object
            if self.armaturehelper.is_armature_root(niBlock):
                # all bones in the tree are also imported by
                # import_armature
                if NifOp.props.skeleton != "GEOMETRY_ONLY":
                    b_obj = self.armaturehelper.import_armature(niBlock)
                    # set axis orientation - move to armature module?
                    b_obj.data.niftools.axis_forward = NifOp.props.axis_forward
                    b_obj.data.niftools.axis_up = NifOp.props.axis_up
                else:
                    n_name = self.import_name(niBlock)
                    b_obj = self.selected_objects[0]
                    NifLog.info("Merging nif tree '{0}' with armature '{1}'".format(n_name, b_obj.name))
                    if n_name != b_obj.name:
                        NifLog.warn("Using Nif block '{0}' as armature '{1}' but names do not match".format(n_name, b_obj.name))
                b_armature = b_obj
                n_armature = niBlock
                # armatures cannot group geometries into a single mesh
                geom_group = []
            elif self.armaturehelper.is_bone(niBlock):
                # bones have already been imported during import_armature
                b_obj = b_armature.data.bones[self.import_name(niBlock)]
                b_obj.niftools.bsxflags = self.bsxflags
                b_obj.niftools.boneflags = niBlock.flags
                # bones cannot group geometries into a single mesh
                geom_group = []
            else:
                # is it a grouping node?
                geom_group = self.is_grouping_node(niBlock)
                # if importing animation, remove children that have
                # morph controllers from geometry group
                if NifOp.props.animation:
                    for child in geom_group:
                        if nif_utils.find_controller(
                            child, NifFormat.NiGeomMorpherController):
                            geom_group.remove(child)
                # import geometry/empty
                if (not geom_group
                    or not NifOp.props.combine_shapes
                    or len(geom_group) > 16):
                    # no grouping node, or too many materials to
                    # group the geometry into a single mesh
                    # so import it as an empty
                    if not niBlock.has_bounding_box:
                        b_obj = self.import_empty(niBlock)
                    else:
                        b_obj = self.boundhelper.import_bounding_box(niBlock)

                    geom_group = []
                else:
                    # node groups geometries, so import it as a mesh
                    NifLog.info("Joining geometries {0} to single object '{1}'".format([child.name for child in geom_group], niBlock.name))
                    b_obj = None
                    for child in geom_group:
                        self.active_obj_name = niBlock.name.decode()
                        b_obj = self.import_mesh(child, group_mesh=b_obj, applytransform=True)
                        b_obj.niftools.objectflags = child.flags

                        if child.properties:
                            for b_prop in child.properties:
                                self.import_shader_types(b_obj, b_prop)

                        if child.bs_properties:
                            for b_prop in child.bs_properties:
                                self.import_shader_types(b_obj, b_prop)
                                
                        if child.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
                            cf_index = NifFormat.ConsistencyType._enumvalues.index(child.data.consistency_flags)
                            b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]
  
                    
                    b_obj.name = self.import_name(niBlock)
                    
                    # skinning? add armature modifier
                    if any(child.skin_instance
                           for child in geom_group):
                        self.armaturehelper.append_armature_modifier(b_obj, b_armature)


            # find children that aren't part of the geometry group
            b_children_list = []
            children = [child for child in niBlock.children
                        if child not in geom_group]
            for n_child in children:
                b_child = self.import_branch(
                    n_child, b_armature=b_armature, n_armature=n_armature)
                if b_child:
                    b_children_list.append((n_child, b_child))

            object_children = [
                (n_child, b_child) for (n_child, b_child) in b_children_list
                if isinstance(b_child, bpy.types.Object)]
            b_colliders = []
            # if not importing skeleton only
            if NifOp.props.skeleton != "SKELETON_ONLY":
                # import collision objects
                if isinstance(niBlock.collision_object, NifFormat.bhkNiCollisionObject):
                    bhk_body = niBlock.collision_object.body
                    if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                        NifLog.warn("Unsupported collision structure under node {0}".format(niBlock.name))
                    b_colliders.extend( self.bhkhelper.import_bhk_shape(bhkshape=bhk_body) )

                # import bounding box
                bsbound = nif_utils.find_extra(niBlock, NifFormat.BSBound)
                if bsbound:
                    b_colliders.append( self.boundhelper.import_bounding_box(bsbound) )
            
            # set bind pose for children
            self.objecthelper.set_object_bind(b_obj, object_children, b_colliders, b_armature)

            # import extra node data, such as node type
            self.objecthelper.import_billboard(niBlock, b_obj)
            self.objecthelper.import_range_lod_data(niBlock, b_obj)
            self.objecthelper.import_root_collision(niBlock, b_obj)
            
            # set object transform
            # this must be done after all children objects have been
            # parented to b_obj
            if isinstance(b_obj, bpy.types.Object):
                # note: bones and this object's children already have their matrix set
                b_obj.matrix_local = nif_utils.import_matrix(niBlock)

                # import the animations
                if NifOp.props.animation:
                    self.animationhelper.import_text_keys(niBlock)
                    self.animationhelper.armature_animation.import_object_animation(niBlock, b_obj)
                    self.animationhelper.object_animation.import_object_vis_controller(niBlock, b_obj)

            return b_obj
        # all else is currently discarded
        return None
    
    def import_shader_types(self, b_obj, b_prop):
        if isinstance(b_prop, NifFormat.BSShaderPPLightingProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSShaderPPLightingProperty'
            sf_type = NifFormat.BSShaderType._enumvalues.index(b_prop.shader_type)
            b_obj.niftools_shader.bsspplp_shaderobjtype = NifFormat.BSShaderType._enumkeys[sf_type]
            for b_flag_name in b_prop.shader_flags._names:
                sf_index = b_prop.shader_flags._names.index(b_flag_name)
                if b_prop.shader_flags._items[sf_index]._value == 1:
                    b_obj.niftools_shader[b_flag_name] = True
                
        if isinstance(b_prop, NifFormat.BSLightingShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSLightingShaderProperty'
            sf_type = NifFormat.BSLightingShaderPropertyShaderType._enumvalues.index(b_prop.skyrim_shader_type)
            b_obj.niftools_shader.bslsp_shaderobjtype = NifFormat.BSLightingShaderPropertyShaderType._enumkeys[sf_type]
            self.import_shader_flags(b_obj, b_prop)

        elif isinstance(b_prop, NifFormat.BSEffectShaderProperty):
            b_obj.niftools_shader.bs_shadertype = 'BSEffectShaderProperty'
            b_obj.niftools_shader.bslsp_shaderobjtype = 'Default'
            self.import_shader_flags(b_obj, b_prop)
                    
    def import_shader_flags(self, b_obj, b_prop):
        for b_flag_name_1 in b_prop.shader_flags_1._names:
            sf_index = b_prop.shader_flags_1._names.index(b_flag_name_1)
            if b_prop.shader_flags_1._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_1] = True
        for b_flag_name_2 in b_prop.shader_flags_2._names:
            sf_index = b_prop.shader_flags_2._names.index(b_flag_name_2)
            if b_prop.shader_flags_2._items[sf_index]._value == 1:
                b_obj.niftools_shader[b_flag_name_2] = True
        
    def import_name(self, niBlock):
        """Get name of niBlock, ready for blender but not necessarily unique.

        :param niBlock: A named nif block.
        :type niBlock: :class:`~pyffi.formats.nif.NifFormat.NiObjectNET`
        """
        if niBlock is None:
            return ""
        
        NifLog.debug("Importing name for {0} block from {1}".format(niBlock.__class__.__name__, niBlock.name))

        niName = niBlock.name.decode()
        # if name is empty, create something non-empty
        if not niName:
            niName = "noname"
        # todo[armature] should this be moved into armature?
        niName = armature.get_bone_name_for_blender(niName)

        return niName
    
    def import_empty(self, niBlock):
        """Creates and returns a grouping empty."""
        b_empty = self.objecthelper.create_b_obj(niBlock, None)
        b_empty.niftools.bsxflags = self.bsxflags
        b_empty.niftools.objectflags = niBlock.flags
        return b_empty

    def import_mesh(self, niBlock,
                    group_mesh=None,
                    applytransform=False,
                    relative_to=None):
        """Creates and returns a raw mesh, or appends geometry data to
        group_mesh.

        :param niBlock: The nif block whose mesh data to import.
        :type niBlock: C{NiTriBasedGeom}
        :param group_mesh: The mesh to which to append the geometry
            data. If C{None}, a new mesh is created.
        :type group_mesh: A Blender object that has mesh data.
        :param applytransform: Whether to apply the niBlock's
            transformation to the mesh. If group_mesh is not C{None},
            then applytransform must be C{True}.
        :type applytransform: C{bool}
        """
        assert(isinstance(niBlock, NifFormat.NiTriBasedGeom))

        NifLog.info("Importing mesh data for geometry {0}".format(niBlock.name))

        if group_mesh:
            b_obj = group_mesh
            b_mesh = group_mesh.data
        else:
            # Mesh name -> must be unique, so tag it if needed
            
            ni_name = niBlock.name.decode()
            # create mesh data
            b_mesh = bpy.data.meshes.new(ni_name)
            # create mesh object and link to data
            b_obj = self.objecthelper.create_b_obj(niBlock, b_mesh)
            
            # Mesh hidden flag
            if niBlock.flags & 1 == 1:
                b_obj.draw_type = 'WIRE'  # hidden: wire
            else:
                b_obj.draw_type = 'TEXTURED'  # not hidden: shaded

        # set transform matrix for the mesh
        if not applytransform:
            if group_mesh:
                raise nif_utils.NifError(
                    "BUG: cannot set matrix when importing meshes in groups;"
                    " use applytransform = True")

            b_obj.matrix_local = nif_utils.import_matrix(niBlock, relative_to=relative_to)

        else:
            # used later on
            transform = nif_utils.import_matrix(niBlock, relative_to=relative_to)

        # shortcut for mesh geometry data
        niData = niBlock.data
        if not niData:
            raise nif_utils.NifError("no shape data in %s" % ni_name)

        # vertices
        n_verts = niData.vertices

        # polygons
        n_triangles = [list(tri) for tri in niData.get_triangles()]

        # "sticky" UV coordinates: these are transformed in Blender UV's
        n_uv = list()
        for i in range(len(niData.uv_sets)):
            for lw in range(len(niData.uv_sets[i])):
                n_uvt = list()
                n_uvt.append(niData.uv_sets[i][lw].u)
                n_uvt.append(1.0 - (niData.uv_sets[i][lw].v))
                n_uv.append(tuple(n_uvt))
        n_uvco = tuple(n_uv)

        # vertex normals
        n_norms = niData.normals

        '''
        Properties
        '''

        # Stencil (for double sided meshes)
        n_stencil_prop = nif_utils.find_property(niBlock, NifFormat.NiStencilProperty)
        # we don't check flags for now, nothing fancy
        if n_stencil_prop:
            b_mesh.show_double_sided = True
        else:
            b_mesh.show_double_sided = False

        # Material
        # note that NIF files only support one material for each trishape
        # find material property
        n_mat_prop = nif_utils.find_property(
                        niBlock, NifFormat.NiMaterialProperty)
        n_shader_prop = nif_utils.find_property(
                        niBlock, NifFormat.BSLightingShaderProperty)
        n_effect_shader_prop = nif_utils.find_property(
                        niBlock, NifFormat.BSEffectShaderProperty)

        if n_mat_prop or n_shader_prop or n_effect_shader_prop:
            # Texture
            n_texture_prop = None
            if n_uvco:
                n_texture_prop = nif_utils.find_property(niBlock,
                                                  NifFormat.NiTexturingProperty)
                
            # extra datas (for sid meier's railroads) that have material info
            extra_datas = []
            for extra in niBlock.get_extra_datas():
                if isinstance(extra, NifFormat.NiIntegerExtraData):
                    if extra.name in self.EXTRA_SHADER_TEXTURES:
                        # yes, it describes the shader slot number
                        extra_datas.append(extra)    
            
            # bethesda shader
            bsShaderProperty = None
            bsShaderProperty = nif_utils.find_property(
                niBlock, NifFormat.BSShaderPPLightingProperty)
            if bsShaderProperty is None:
                bsShaderProperty = nif_utils.find_property(
                niBlock, NifFormat.BSLightingShaderProperty)
                
            if bsShaderProperty:
                for textureslot in bsShaderProperty.texture_set.textures:
                    if textureslot:
                        self.bsShaderProperty1st = bsShaderProperty
                        break
                else:
                    bsShaderProperty = self.bsShaderProperty1st
                
            bsEffectShaderProperty = None
            bsEffectShaderProperty = nif_utils.find_property(
                niBlock, NifFormat.BSEffectShaderProperty)

            
            # texturing effect for environment map
            # in official files this is activated by a NiTextureEffect child
            # preceeding the niBlock
            textureEffect = None
            if isinstance(niBlock._parent, NifFormat.NiNode):
                lastchild = None
                for child in niBlock._parent.children:
                    if child is niBlock:
                        if isinstance(lastchild, NifFormat.NiTextureEffect):
                            textureEffect = lastchild
                        break
                    lastchild = child
                else:
                    raise RuntimeError("texture effect scanning bug")
                # in some mods the NiTextureEffect child follows the niBlock
                # but it still works because it is listed in the effect list
                # so handle this case separately
                if not textureEffect:
                    for effect in niBlock._parent.effects:
                        if isinstance(effect, NifFormat.NiTextureEffect):
                            textureEffect = effect
                            break
            
            # Alpha
            n_alpha_prop = nif_utils.find_property(niBlock,
                                               NifFormat.NiAlphaProperty)
            self.ni_alpha_prop = n_alpha_prop

            # Specularity
            n_specular_prop = nif_utils.find_property(niBlock,
                                              NifFormat.NiSpecularProperty)

            # Wireframe
            n_wire_prop = nif_utils.find_property(niBlock,
                                              NifFormat.NiWireframeProperty)


            # create material and assign it to the mesh
            # XXX todo: delegate search for properties to import_material
            material = self.materialhelper.import_material(n_mat_prop, n_texture_prop,
                                            n_alpha_prop, n_specular_prop,
                                            textureEffect, n_wire_prop,
                                            bsShaderProperty,
                                            bsEffectShaderProperty,
                                            extra_datas)

            # XXX todo: merge this call into import_material
            self.animationhelper.material_animation.import_material_controllers(material, niBlock)
            b_mesh_materials = list(b_mesh.materials)
            try:
                materialIndex = b_mesh_materials.index(material)
            except ValueError:
                materialIndex = len(b_mesh_materials)
                b_mesh.materials.append(material)

            '''
            # if mesh has one material with n_wire_prop, then make the mesh
            # wire in 3D view
            if n_wire_prop:
                b_obj.draw_type = 'WIRE'
            '''
        else:
            material = None
            materialIndex = 0

        # v_map will store the vertex index mapping
        # nif vertex i maps to blender vertex v_map[i]
        v_map = [(i) for i in range(len(n_verts))]  # pre-allocate memory, for faster performance

        # Following code avoids introducing unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
        n_map = {}
        b_v_index = len(b_mesh.vertices)
        for i, v in enumerate(n_verts):
            # The key k identifies unique vertex /normal pairs.
            # We use a tuple of ints for key, this works MUCH faster than a
            # tuple of floats.
            if n_norms:
                n = n_norms[i]
                k = (int(v.x * self.VERTEX_RESOLUTION),
                     int(v.y * self.VERTEX_RESOLUTION),
                     int(v.z * self.VERTEX_RESOLUTION),
                     int(n.x * self.NORMAL_RESOLUTION),
                     int(n.y * self.NORMAL_RESOLUTION),
                     int(n.z * self.NORMAL_RESOLUTION))
            else:
                k = (int(v.x * self.VERTEX_RESOLUTION),
                     int(v.y * self.VERTEX_RESOLUTION),
                     int(v.z * self.VERTEX_RESOLUTION))
            # check if vertex was already added, and if so, what index
            try:
                # this is the bottle neck...
                # can we speed this up?
                if not NifOp.props.combine_vertices:
                    n_map_k = None
                else:
                    n_map_k = n_map[k]
            except KeyError:
                n_map_k = None
            if not n_map_k:
                # not added: new vertex / normal pair
                n_map[k] = i  # unique vertex / normal pair with key k was added, with NIF index i
                v_map[i] = b_v_index  # NIF vertex i maps to blender vertex b_v_index
                # add the vertex
                if applytransform:
                    v = mathutils.Vector([v.x, v.y, v.z])
                    v = v * transform
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                else:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                # adds normal info if present (Blender recalculates these when
                # switching between edit mode and object mode, handled further)
                # if n_norms:
                #    mv = b_mesh.vertices[b_v_index]
                #    n = n_norms[i]
                #    mv.normal = mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                # NIF vertex i maps to Blender vertex v_map[n_map_k]
                v_map[i] = v_map[n_map_k]
        # report
        NifLog.debug("{0} unique vertex-normal pairs".format(str(len(n_map))))
        # release memory
        del n_map

        # Adds the polygons to the mesh
        f_map = [None] * len(n_triangles)
        b_f_index = len(b_mesh.polygons)
        bf2_index = len(b_mesh.polygons)
        bl_index = len(b_mesh.loops)
        poly_count = len(n_triangles)
        b_mesh.polygons.add(poly_count)
        b_mesh.loops.add(poly_count * 3)
        num_new_faces = 0  # counter for debugging
        unique_faces = list()  # to avoid duplicate polygons
        tri_point_list = list()
        for i, f in enumerate(n_triangles):
            # get face index
            f_verts = [v_map[vert_index] for vert_index in f]
            if tuple(f_verts) in unique_faces:
                continue
            unique_faces.append(tuple(f_verts))
            f_map[i] = b_f_index
            tri_point_list.append(len(n_triangles[i]))
            ls_list = list()
            b_f_index += 1
            num_new_faces += 1
        for ls1 in range(0, num_new_faces * (tri_point_list[len(ls_list)]), (tri_point_list[len(ls_list)])):
            ls_list.append((ls1 + bl_index))
        for i in range(len(unique_faces)):
            if f_map[i] is None:
                continue
            b_mesh.polygons[f_map[i]].loop_start = ls_list[(f_map[i] - bf2_index)]
            b_mesh.polygons[f_map[i]].loop_total = len(unique_faces[(f_map[i] - bf2_index)])
            l = 0
            lp_points = [v_map[loop_point] for loop_point in n_triangles[(f_map[i] - bf2_index)]]
            while l < (len(n_triangles[(f_map[i] - bf2_index)])):
                b_mesh.loops[(l + (bl_index))].vertex_index = lp_points[l]
                l += 1
            bl_index += (len(n_triangles[(f_map[i] - bf2_index)]))
            
        # at this point, deleted polygons (degenerate or duplicate)
        # satisfy f_map[i] = None

        NifLog.debug("{0} unique polygons".format(num_new_faces))

        # set face smoothing and material
        for b_polysmooth_index in f_map:
            if b_polysmooth_index is None:
                continue
            polysmooth = b_mesh.polygons[b_polysmooth_index]
            polysmooth.use_smooth = True if (n_norms or niBlock.skin_instance) else False
            polysmooth.material_index = materialIndex
        # vertex colors
        

        if b_mesh.polygons and niData.vertex_colors:
            n_vcol_map = list()
            for n_vcol, n_vmap in zip(niData.vertex_colors, v_map):
                n_vcol_map.append((n_vcol, n_vmap))
            
            # create vertex_layers
            if not "VertexColor" in b_mesh.vertex_colors:
                b_mesh.vertex_colors.new(name="VertexColor")  # color layer
                b_mesh.vertex_colors.new(name="VertexAlpha")  # greyscale
            
            # Mesh Vertex Color / Mesh Face
            for b_polygon_loop in b_mesh.loops:
                b_loop_index = b_polygon_loop.index
                vcol = b_mesh.vertex_colors["VertexColor"].data[b_loop_index]
                vcola = b_mesh.vertex_colors["VertexAlpha"].data[b_loop_index]
                for n_col_index, n_map_index in n_vcol_map:
                    if n_map_index == b_polygon_loop.vertex_index:
                        col_list = n_col_index
                        vcol.color.r = col_list.r
                        vcol.color.g = col_list.g
                        vcol.color.b = col_list.b
                        vcola.color.v = col_list.a
            # vertex colors influence lighting...
            # we have to set the use_vertex_color_light flag on the material
            # see below

        # UV coordinates
        # NIF files only support 'sticky' UV coordinates, and duplicates
        # vertices to emulate hard edges and UV seam. So whenever a hard edge
        # or a UV seam is present the mesh, vertices are duplicated. Blender
        # only must duplicate vertices for hard edges; duplicating for UV seams
        # would introduce unnecessary hard edges.

        # only import UV if there are polygons
        # (some corner cases have only one vertex, and no polygons,
        # and b_mesh.faceUV = 1 on such mesh raises a runtime error)
        if b_mesh.polygons:
           
            # b_mesh.faceUV = 1
            # b_mesh.vertexUV = 0
            for i in range(len(niData.uv_sets)):
                # Set the face UV's for the mesh. The NIF format only supports
                # vertex UV's, but Blender only allows explicit editing of face
                # UV's, so load vertex UV's as face UV's
                uvlayer = self.texturehelper.get_uv_layer_name(i)
                if not uvlayer in b_mesh.uv_textures:
                    b_mesh.uv_textures.new(uvlayer)
                    uv_faces = b_mesh.uv_textures.active.data[:]
                elif uvlayer in b_mesh.uv_textures:
                    uv_faces = b_mesh.uv_textures[uvlayer].data[:]
                else:
                    uv_faces = None
                if uv_faces:
                    uvl = b_mesh.uv_layers.active.data[:]
                    for b_f_index, f in enumerate(n_triangles):
                        if b_f_index is None:
                            continue
                        uvlist = f
                        v1, v2, v3 = uvlist
                        # if v3 == 0:
                        #   v1,v2,v3 = v3,v1,v2
                        b_poly_index = b_mesh.polygons[b_f_index + bf2_index]
                        uvl[b_poly_index.loop_start].uv = n_uvco[v1]
                        uvl[b_poly_index.loop_start + 1].uv = n_uvco[v2]
                        uvl[b_poly_index.loop_start + 2].uv = n_uvco[v3]
            b_mesh.uv_textures.active_index = 0

        if material:
            # fix up vertex colors depending on whether we had textures in the
            # material
            mbasetex = self.texturehelper.has_base_texture(material)
            mglowtex = self.texturehelper.has_glow_texture(material)
            if b_mesh.vertex_colors:
                if mbasetex or mglowtex:
                    # textured material: vertex colors influence lighting
                    material.use_vertex_color_light = True
                else:
                    # non-textured material: vertex colors incluence color
                    material.use_vertex_color_paint = True

            # if there's a base texture assigned to this material sets it
            # to be displayed in Blender's 3D view
            # but only if there are UV coordinates
            if mbasetex and mbasetex.texture and n_uvco:
                imgobj = mbasetex.texture.image
                if imgobj:
                    for b_polyimage_index in f_map:
                        if b_polyimage_index is None:
                            continue
                        tface = b_mesh.uv_textures.active.data[b_polyimage_index]
                        # gone in blender 2.5x+?
                        # f.mode = Blender.Mesh.FaceModes['TEX']
                        # f.transp = Blender.Mesh.FaceTranspModes['ALPHA']
                        tface.image = imgobj

        # import skinning info, for meshes affected by bones
        self.armaturehelper.import_skin(niBlock, b_obj, v_map)

        # import morph controller
        if NifOp.props.animation:
            self.animationhelper.object_animation.import_morph_controller(niBlock, b_obj, v_map)
        # import facegen morphs
        if self.egmdata:
            self.animationhelper.object_animation.import_egm_morphs(self.egmdata, b_obj, v_map, n_verts)

        # recalculate mesh to render correctly
        # implementation note: update() without validate() can cause crash
        
        b_mesh.validate()
        b_mesh.update()
        b_obj.select = True
        scn = bpy.context.scene
        scn.objects.active = b_obj

        return b_obj
    
    def set_parents(self, niBlock):
        """Set the parent block recursively through the tree, to allow
        crawling back as needed."""
        if isinstance(niBlock, NifFormat.NiNode):
            # list of non-null children
            children = [ child for child in niBlock.children if child ]
            for child in children:
                child._parent = niBlock
                self.set_parents(child)

    def is_grouping_node(self, niBlock):
        """Determine whether node is grouping node.
        Returns the children which are grouped, or empty list if it is not a
        grouping node.
        """
        # combining shapes: disable grouping
        if not NifOp.props.combine_shapes:
            return []
        # check that it is a ninode
        if not isinstance(niBlock, NifFormat.NiNode):
            return []
        # NiLODNodes are never grouping nodes
        # (this ensures that they are imported as empties, with LODs
        # as child meshes)
        if isinstance(niBlock, NifFormat.NiLODNode):
            return []
        # root collision node: join everything
        if isinstance(niBlock, NifFormat.RootCollisionNode):
            return [ child for child in niBlock.children if
                     isinstance(child, NifFormat.NiTriBasedGeom) ]
        # check that node has name
        node_name = niBlock.name
        if not node_name:
            return []
        # strip "NonAccum" trailer, if present
        if node_name[-9:].lower() == " nonaccum":
            node_name = node_name[:-9]
        # get all geometry children
        return [ child for child in niBlock.children
                 if (isinstance(child, NifFormat.NiTriBasedGeom)
                     and child.name.find(node_name) != -1) ]
