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
from io_scene_nif.modules.geometry.mesh.mesh_import import Mesh
from io_scene_nif.modules.obj import object_import, blocks
from io_scene_nif.modules.property import texture
from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_global import NifOp, NifData
from io_scene_nif.utility.nif_logging import NifLog

from io_scene_nif.io.nif import NifFile
from io_scene_nif.io.kf import KFFile
from io_scene_nif.io.egm import EGMFile

from io_scene_nif.modules.animation.animation_import import AnimationHelper
from io_scene_nif.modules import armature, obj, animation, collision
from io_scene_nif.modules.armature.armature_import import Armature
from io_scene_nif.modules.collision.collision_import import BHKShape, Bound
from io_scene_nif.modules.constraint.constraint_import import Constraint
from io_scene_nif.modules.obj.object_import import Empty, is_grouping_node, ObjectProperty
from io_scene_nif.modules.scene import scene_import

import bpy
import mathutils

import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat


class NifImport(NifCommon):
    # degrees to radians conversion constant
    D2R = 3.14159265358979 / 180.0
    IMPORT_EXTRANODES = True

    # noinspection PyUnusedLocal
    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        self.root_ninode = 'NiNode'

        # Helper systems
        self.animation_helper = AnimationHelper()
        self.armature_helper = Armature(parent=self)
        # TODO [collision] create super collisionhelper
        self.bhkhelper = BHKShape()
        self.boundhelper = Bound()
        self.constrainthelper = Constraint()

    def execute(self):
        """Main import function."""

        # TODO resets here for now
        animation.FPS = 30
        armature.DICT_ARMATURES = {}
        armature.DICT_BONES_EXTRA_MATRIX = {}
        armature.DICT_BONES_EXTRA_MATRIX_INV = {}
        armature.DICT_BONE_PRIORITIES = {}
        collision.DICT_HAVOK_OBJECTS = {}
        obj.DICT_NAMES = {}
        obj.BLOCK_NAMES_LIST = []
        blocks.DICT_BLOCKS = {}
        texture.DICT_TEXTURES = {}

        # catch nif import errors
        try:
            # check that one armature is selected in 'import geometry + parent to armature' mode
            if NifOp.props.skeleton == "GEOMETRY_ONLY":
                if len(self.selected_objects) != 1 or self.selected_objects[0].type != 'ARMATURE':
                    raise nif_utils.NifError("You must select exactly one armature in 'Import Geometry Only + Parent To Selected Armature'  mode.")

            NifData.data = NifFile.load_nif(NifOp.props.filepath)
            if NifOp.props.override_scene_info:
                scene_import.import_version_info(NifData.data)

            kf_path = NifOp.props.keyframe_file
            if kf_path:
                self.kfdata = KFFile.load_kf(kf_path)
            else:
                self.kfdata = None

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
                animation.FPS = self.animation_helper.get_frames_per_second(NifData.data.roots + (self.kfdata.roots if self.kfdata else []))
                bpy.context.scene.render.fps = animation.FPS

            # merge skeleton roots and transform geometry into the rest pose
            if NifOp.props.merge_skeleton_roots:
                pyffi.spells.nif.fix.SpellMergeSkeletonRoots(data=NifData.data).recurse()
            if NifOp.props.send_geoms_to_bind_pos:
                pyffi.spells.nif.fix.SpellSendGeometriesToBindPosition(data=NifData.data).recurse()
            if NifOp.props.send_detached_geoms_to_node_pos:
                pyffi.spells.nif.fix.SpellSendDetachedGeometriesToNodePosition(data=NifData.data).recurse()
            if NifOp.props.send_bones_to_bind_position:
                pyffi.spells.nif.fix.SpellSendBonesToBindPosition(data=NifData.data).recurse()
            if NifOp.props.apply_skin_deformation:

                # TODO [Object] Create function & move to object/mesh class
                for n_geom in NifData.data.get_global_iterator():
                    if not isinstance(n_geom, NifFormat.NiGeometry):
                        continue
                    if not n_geom.is_skin():
                        continue
                    NifLog.info('Applying skin deformation on geometry {0}'.format(n_geom.name))
                    vertices = n_geom.get_skin_deformation()[0]
                    for v_old, v_new in zip(n_geom.data.vertices, vertices):
                        v_old.x = v_new.x
                        v_old.y = v_new.y
                        v_old.z = v_new.z

            # scale tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = NifOp.props.scale_correction_import
            pyffi.spells.nif.fix.SpellScale(data=NifData.data, toaster=toaster).recurse()

            # import all root blocks
            for block in NifData.data.roots:
                root = block
                # root hack for corrupt better bodies meshes
                # and remove geometry from better bodies on skeleton import
                for b in (b for b in block.tree() if isinstance(b, NifFormat.NiGeometry) and b.is_skin()):
                    # check if root belongs to the children list of the
                    # skeleton root (can only happen for better bodies meshes)
                    if root in [c for c in b.skin_instance.skeleton_root.children]:
                        # fix parenting and update transform accordingly
                        b.skin_instance.data.set_transform(root.get_transform() * b.skin_instance.data.get_transform())
                        b.skin_instance.skeleton_root = root
                        # delete non-skeleton nodes if we're importing
                        # skeleton only
                        if NifOp.props.skeleton == "SKELETON_ONLY":
                            nonbip_children = (child for child in root.children if child.name[:6] != 'Bip01 ')
                            for child in nonbip_children:
                                root.remove_child(child)

                # import this root block
                NifLog.debug("Root block: {0}".format(root.get_global_display()))
                # merge animation from kf tree into nif tree
                if NifOp.props.animation and self.kfdata:
                    for kf_root in self.kfdata.roots:
                        self.animation_helper.import_kf_root(kf_root, root)
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
            raise nif_utils.NifError("direct .kf import not supported")

        # divinity 2: handle CStreamableAssetData
        if isinstance(root_block, NifFormat.CStreamableAssetData):
            root_block = root_block.root

        # sets the root block parent to None, so that when crawling back the
        # script won't barf
        root_block._parent = None

        # set the block parent through the tree, to ensure I can always move backward
        self.set_parents(root_block)
        # TODO [object][properties] process flags at object level

        # mark armature nodes and bones
        self.armature_helper.mark_armatures_bones(root_block)

        # import the keyframe notes
        if NifOp.props.animation:
            self.animation_helper.import_text_keys(root_block)

        # read the NIF tree
        if self.armature_helper.is_armature_root(root_block):
            # special case 1: root node is skeleton root
            NifLog.debug("{0} is an armature root".format(root_block.name))
            b_obj = self.import_branch(root_block)
            b_obj.niftools.objectflags = root_block.flags

        elif is_grouping_node(root_block):
            # special case 2: root node is grouping node
            NifLog.debug("{0} is a grouping node".format(root_block.name))
            b_obj = self.import_branch(root_block)

            # TODO [object][flags]
            # b_obj.niftools.bsxflags = self.bsx_flags

        elif isinstance(root_block, NifFormat.NiTriBasedGeom):
            # trishape/tristrips root
            b_obj = self.import_branch(root_block)

            ObjectProperty().process_data_list(root_block, b_obj)
            # TODO [object][flags]
            # b_obj.niftools.bsxflags = self.bsx_flags

        elif isinstance(root_block, NifFormat.NiNode):

            # root node is dummy scene node
            # TODO [object][property]
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

        # store bone matrix offsets for re-export
        if armature.DICT_BONES_EXTRA_MATRIX:
            self.armature_helper.store_bones_extra_matrix()

        # store original names for re-export
        if obj.DICT_NAMES:
            self.armature_helper.store_names()

        # now all havok objects are imported, so we are
        # ready to import the havok constraints
        self.constrainthelper.import_bhk_constraints()

        # parent selected meshes to imported skeleton
        if NifOp.props.skeleton == "SKELETON_ONLY":
            # rename vertex groups to reflect bone names
            # (for blends imported with older versions of the scripts!)
            for b_child_obj in self.selected_objects:
                if b_child_obj.type == 'MESH':
                    for oldgroupname in b_child_obj.vertex_groups.items():
                        newgroupname = armature.get_bone_name_for_blender(oldgroupname)
                        if oldgroupname != newgroupname:
                            NifLog.info("{0} : renaming vertex group {1} to {2}".format(b_child_obj, oldgroupname, newgroupname))
                            b_child_obj.data.renameVertGroup(oldgroupname, newgroupname)
            # set parenting
            # b_obj.parent_set(self.selected_objects)
            bpy.ops.object.parent_set(type='OBJECT')
            scn = bpy.context.scene
            scn.objects.active = b_obj
            scn.update()

    def import_branch(self, n_block, b_armature=None, n_armature=None):
        """Read the content of the current NIF tree branch to Blender
        recursively.

        :param n_block: The nif block to import.
        :param b_armature: The blender armature for the current branch.
        :param n_armature: The corresponding nif block for the armature for
            the current branch.
        """
        if n_block:
            NifLog.info("Importing data {0} block from {1}".format(n_block.__class__.__name__, n_block.name))
        else:
            return None
        if isinstance(n_block, NifFormat.NiTriBasedGeom) and NifOp.props.skeleton != "SKELETON_ONLY":
            # it's a shape node and we're not importing skeleton only
            # (NifOp.props.skeleton ==  "SKELETON_ONLY")
            NifLog.debug("Building mesh in import_branch")
            # note: transform matrix is set during import
            self.active_obj_name = n_block.name.decode()
            b_obj = Mesh.import_mesh(n_block)

            # TODO [object][flags]
            ObjectProperty().process_data_list(n_block, b_obj)
            # b_obj.niftools.objectflags = n_block.flags

            # TODO [property][shader][material] Do proper property processing
            # if niBlock.properties:
            #     for b_prop in niBlock.properties:
            #         self.import_shader_types(b_obj, b_prop)
            # elif niBlock.bs_properties:
            #     for b_prop in niBlock.bs_properties:
            #         self.import_shader_types(b_obj, b_prop)

            # TODO [object][flags]
            # if niBlock.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
            #     cf_index = NifFormat.ConsistencyType._enumvalues.index(niBlock.data.consistency_flags)
            #     b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]
            #     b_obj.niftools.bsnumuvset = niBlock.data.bs_num_uv_sets

            # skinning? add armature modifier
            if n_block.skin_instance:
                self.armature_helper.append_armature_modifier(b_obj, b_armature)
            return b_obj
        elif isinstance(n_block, NifFormat.NiNode):
            children = n_block.children

            # bounding box child?
            bsbound = nif_utils.find_extra(n_block, NifFormat.BSBound)
            if not (children or n_block.collision_object or bsbound or n_block.has_bounding_box or self.IMPORT_EXTRANODES):
                # do not import unless the node is "interesting"
                return None

            # import object
            if self.armature_helper.is_armature_root(n_block):
                # all bones in the tree are also imported by
                # import_armature
                if NifOp.props.skeleton != "GEOMETRY_ONLY":
                    b_obj = self.armature_helper.import_armature(n_block)
                    b_armature = b_obj
                    n_armature = n_block
                else:
                    b_obj = self.selected_objects[0]
                    b_armature = b_obj
                    n_armature = n_block
                    NifLog.info("Merging nif tree '{0}' with armature '{1}'".format(n_block.name, b_obj.name))
                    if n_block.name != b_obj.name:
                        NifLog.warn("Using Nif block '{0}' as armature '{1}' but names do not match".format(n_block.name, b_obj.name))
                # armatures cannot group geometries into a single mesh
                geom_group = []

            elif self.armature_helper.is_bone(n_block):
                # bones have already been imported during import_armature
                b_obj = b_armature.data.bones[obj.DICT_NAMES[n_block]]
                # bones cannot group geometries into a single mesh

                # TODO [object][property] Object flags
                # b_obj.niftools_bone.bsxflags = self.bsx_flags
                b_obj.niftools_bone.boneflags = n_block.flags
                geom_group = []

            else:
                # is it a grouping node?
                geom_group = is_grouping_node(n_block)
                # if importing animation, remove children that have
                # morph controllers from geometry group
                if NifOp.props.animation:
                    for child in geom_group:
                        if nif_utils.find_controller(child, NifFormat.NiGeomMorpherController):
                            geom_group.remove(child)
                # import geometry/empty
                if not geom_group or not NifOp.props.combine_shapes or len(geom_group) > 16:
                    # no grouping node, or too many materials to
                    # group the geometry into a single mesh
                    # so import it as an empty
                    if not n_block.has_bounding_box:
                        b_obj = Empty().import_empty(n_block)
                    else:
                        b_obj = self.boundhelper.import_bounding_box(n_block)

                    if isinstance(n_block, NifFormat.RootCollisionNode):
                        b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
                    geom_group = []
                else:
                    # node groups geometries, so import it as a mesh
                    NifLog.info("Joining geometries {0} to single object '{1}'".format([child.name for child in geom_group], n_block.name))
                    b_obj = None
                    for child in geom_group:
                        self.active_obj_name = n_block.name.decode()
                        b_obj = Mesh.import_mesh(child, group_mesh=b_obj, applytransform=True)
                        b_obj.niftools.objectflags = child.flags

                        # TODO [property][shader] do proper property processing
                        # if child.properties:
                        #     for b_prop in child.properties:
                        #         self.import_shader_types(b_obj, b_prop)
                        #
                        # if child.bs_properties:
                        #     for b_prop in child.bs_properties:
                        #         self.import_shader_types(b_obj, b_prop)

                        if child.data.consistency_flags in NifFormat.ConsistencyType._enumvalues:
                            cf_index = NifFormat.ConsistencyType._enumvalues.index(child.data.consistency_flags)
                            b_obj.niftools.consistency_flags = NifFormat.ConsistencyType._enumkeys[cf_index]

                    b_obj.name = object_import.import_name(n_block)

                    # skinning? add armature modifier
                    if any(child.skin_instance for child in geom_group):
                        self.armature_helper.append_armature_modifier(b_obj, b_armature)

                    # settings for collision node
                    if isinstance(n_block, NifFormat.RootCollisionNode):
                        b_obj.draw_type = 'BOUNDS'
                        b_obj.show_wire = True
                        b_obj.draw_bounds_type = 'BOX'
                        b_obj.game.use_collision_bounds = True
                        b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
                        b_obj.niftools.objectflags = n_block.flags
                        # also remove duplicate vertices
                        b_mesh = b_obj.data
                        b_mesh.validate()
                        b_mesh.update()

            # find children that aren't part of the geometry group
            b_children_list = []
            children = [child for child in n_block.children if child not in geom_group]
            for n_child in children:
                b_child = self.import_branch(n_child, b_armature=b_armature, n_armature=n_armature)
                if b_child:
                    b_children_list.append((n_child, b_child))

            object_children = [(n_child, b_child) for (n_child, b_child) in b_children_list if isinstance(b_child, bpy.types.Object)]

            # if not importing skeleton only
            if NifOp.props.skeleton != "SKELETON_ONLY":
                # import collision objects
                if isinstance(n_block.collision_object, NifFormat.bhkNiCollisionObject):
                    bhk_body = n_block.collision_object.body
                    if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                        NifLog.warn("Unsupported collision structure under node {0}".format(n_block.name))

                    collision_objs = self.bhkhelper.import_bhk_shape(bhkshape=bhk_body)
                    # register children for parentship
                    object_children += [(bhk_body, b_child) for b_child in collision_objs]

                # import bounding box
                if bsbound:
                    object_children += [(bsbound, self.boundhelper.import_bounding_box(bsbound))]

            # fix parentship
            if isinstance(b_obj, bpy.types.Object):
                # simple object parentship
                for (n_child, b_child) in object_children:
                    b_child.parent = b_obj

            elif isinstance(b_obj, bpy.types.Bone):

                # TODO [Animation] MOVE TO ANIMATIONHELPER

                # bone parentship, is a bit more complicated
                # go to rest position

                # b_armature.data.restPosition = True
                bpy.context.scene.objects.active = b_armature

                # set up transforms
                for n_child, b_child in object_children:
                    # save transform

                    # TODO [armature]
                    matrix = mathutils.Matrix(b_child.matrix_local)
                    # fix transform
                    # the bone has in the nif file an armature space transform
                    # given by niBlock.get_transform(relative_to=n_armature)
                    #
                    # in detail:
                    # a vertex in the collision object has global
                    # coordinates
                    #   v * Z * B
                    # with v the vertex, Z the object transform
                    # (currently b_obj_matrix)
                    # and B the nif bone matrix

                    # in Blender however a vertex has coordinates
                    #   v * O * T * B'
                    # with B' the Blender bone matrix
                    # so we need that
                    #   Z * B = O * T * B' or equivalently
                    #   O = Z * B * B'^{-1} * T^{-1}
                    #     = Z * X^{-1} * T^{-1}
                    # since
                    #   B' = X * B
                    # with X = armature.DICT_BONES_EXTRA_MATRIX[B]

                    # post multiply Z with X^{-1}
                    extra = mathutils.Matrix(armature.DICT_BONES_EXTRA_MATRIX[n_block])
                    extra.invert()
                    matrix = matrix * extra
                    # cancel out the tail translation T
                    # (the tail causes a translation along
                    # the local Y axis)
                    matrix[1][3] -= b_obj.length
                    b_child.matrix_local = matrix

                    b_child.parent = b_armature
                    b_child.parent_type = 'BONE'
                    b_child.parent_bone = b_obj.name

            else:
                raise RuntimeError("Unexpected object type %s" % b_obj.__class__)

            # track camera for billboard nodes
            if isinstance(n_block, NifFormat.NiBillboardNode):
                # find camera object
                for b_obj in bpy.context.scene.objects:
                    if b_obj.type == 'CAMERA':
                        b_obj_camera = b_obj
                        break
                else:
                    raise nif_utils.NifError(
                        "Scene needs camera for billboard node"
                        " (add a camera and try again)")
                # make b_obj track camera object
                # b_obj.setEuler(0,0,0)
                b_obj.constraints.new('TRACK_TO')
                constr = b_obj.constraints[-1]
                constr.target = b_obj_camera
                if constr.target is None:
                    NifLog.warn("Constraint for billboard node on {0} added but target not set due to transform bug. Set target to Camera manually.".format(b_obj))
                constr.track_axis = 'TRACK_Z'
                constr.up_axis = 'UP_Y'
                # yields transform bug!
                # constr[Blender.Constraint.Settings.TARGET] = obj

            # set object transform
            # this must be done after all children objects have been
            # parented to b_obj
            if isinstance(b_obj, bpy.types.Object):
                # note: bones already have their matrix set
                b_obj.matrix_local = nif_utils.import_matrix(n_block)

                # import the animations
                if NifOp.props.animation:
                    self.animation_helper.set_animation(n_block, b_obj)
                    # import the extras
                    self.animation_helper.import_text_keys(n_block)
                    # import vis controller
                    self.animation_helper.object_animation.import_object_vis_controller(b_object=b_obj, n_node=n_block)

            # import extra node data, such as node type
            # (other types should be added here too)
            if (isinstance(n_block, NifFormat.NiLODNode)
                    # XXX additional isinstance(b_obj, bpy.types.Object)
                    # XXX is a 'workaround' to the limitation that bones
                    # XXX cannot have properties in Blender 2.4x
                    # XXX (remove this check with Blender 2.5)
                    and isinstance(b_obj, bpy.types.Object)):
                b_obj.addProperty("Type", "NiLODNode", "STRING")
                # import lod data
                range_data = n_block.lod_level_data
                for lod_level, (n_child, b_child) in zip(range_data.lod_levels, b_children_list):
                    b_child.addProperty("Near Extent", lod_level.near_extent, "FLOAT")
                    b_child.addProperty("Far Extent", lod_level.far_extent, "FLOAT")

            return b_obj
        NifLog.debug("Discarded {0} block from {1}".format(n_block.__class__.__name__, n_block.name))
        return None

    def set_parents(self, n_block):
        """Set the parent block recursively through the tree, to allow
        crawling back as needed."""
        if isinstance(n_block, NifFormat.NiNode):
            # list of non-null children
            children = [child for child in n_block.children if child]
            for child in children:
                child._parent = n_block
                self.set_parents(child)
