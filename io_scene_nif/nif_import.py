"""This script imports Netimmerse/Gamebryo nif files to Blender."""

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

from .nif_common import NifCommon
from .collisionsys.collision_import import bhkshape_import, bound_import
from .armaturesys.skeletal import armature_import
from .materialsys.material import material_import
from .texturesys.texture import texture_import

from functools import reduce
import logging
import math
import operator
import os
import os.path

import bpy
import mathutils

import pyffi.spells.nif
import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat

class NifImportError(Exception):
    """A simple custom exception class for import errors."""
    pass

class NifImport(NifCommon):

    # degrees to radians conversion constant
    D2R = 3.14159265358979/180.0

    def execute(self):
        """Main import function."""

        # dictionary of names, to map NIF blocks to correct Blender names
        self.names = {}

        # dictionary of bones, maps Blender name to NIF block
        self.blocks = {}

        # dictionary of bones, maps Blender bone name to matrix that maps the
        # NIF bone matrix on the Blender bone matrix
        # B' = X * B, where B' is the Blender bone matrix, and B is the NIF bone matrix
        self.bones_extra_matrix = {}

        # dictionary of bones that belong to a certain armature
        # maps NIF armature name to list of NIF bone name
        self.armatures = {}

        # bone animation priorities (maps NiNode name to priority number);
        # priorities are set in import_kf_root and are stored into the name
        # of a NULL constraint (for lack of something better) in
        # import_armature
        self.bone_priorities = {}

        # dictionary mapping bhkRigidBody objects to list of objects imported
        # in Blender; after we've imported the tree, we use this dictionary
        # to set the physics constraints (ragdoll etc)
        self.havok_objects = {}

        # Helper systems
        # Store references to subsystems as needed.
        self.bhkhelper = bhkshape_import(parent=self)
        self.boundhelper = bound_import(parent=self)
        self.armaturehelper = armature_import(parent=self)
        self.texturehelper = texture_import(parent=self)
        self.materialhelper = material_import(parent=self)


        # catch NifImportError
        try:
            # check that one armature is selected in 'import geometry + parent
            # to armature' mode
            if False: #TODO self.properties.skeleton ==  "GEOMETRY_ONLY":
                if (len(self.selected_objects) != 1
                    or self.selected_objects[0].type != 'ARMATURE'):
                    raise NifImportError(
                        "You must select exactly one armature in"
                        " 'Import Geometry Only + Parent To Selected Armature'"
                        " mode.")

            # open file for binary reading
            self.info("Importing %s" % self.properties.filepath)
            niffile = open(self.properties.filepath, "rb")
            self.data = NifFormat.Data()
            try:
                # check if nif file is valid
                self.data.inspect(niffile)
                if self.data.version >= 0:
                    # it is valid, so read the file
                    self.info("NIF file version: 0x%08X" % self.data.version)
                    self.info("Reading file")
                    self.data.read(niffile)
                elif self.data.version == -1:
                    raise NifImportError("Unsupported NIF version.")
                else:
                    raise NifImportError("Not a NIF file.")
            finally:
                # the file has been read or an error occurred: close file
                niffile.close()

            if self.properties.keyframe_file:
                # open keyframe file for binary reading
                self.info("Importing %s" % self.properties.keyframe_file)
                kffile = open(self.properties.keyframe_file, "rb")
                self.kfdata = NifFormat.Data()
                try:
                    # check if kf file is valid
                    self.kfdata.inspect(kffile)
                    if self.kfdata.version >= 0:
                        # it is valid, so read the file
                        self.info(
                            "KF file version: 0x%08X" % self.kfdata.version)
                        self.info("Reading keyframe file")
                        self.kfdata.read(kffile)
                    elif self.kfdata.version == -1:
                        raise NifImportError("Unsupported KF version.")
                    else:
                        raise NifImportError("Not a KF file.")
                finally:
                    # the file has been read or an error occurred: close file
                    kffile.close()
            else:
                self.kfdata = None

            if self.properties.egm_file:
                # open facegen egm file for binary reading
                self.info("Importing %s" % self.properties.egm_file)
                egmfile = open(self.properties.egm_file, "rb")
                self.egmdata = EgmFormat.Data()
                try:
                    # check if kf file is valid
                    self.egmdata.inspect(egmfile)
                    if self.egmdata.version >= 0:
                        # it is valid, so read the file
                        self.info("EGM file version: %03i"
                                         % self.egmdata.version)
                        self.info("Reading FaceGen egm file")
                        self.egmdata.read(egmfile)
                        # scale the data
                        self.egmdata.apply_scale(1 / self.properties.scale_correction)
                    elif self.egmdata.version == -1:
                        raise NifImportError("Unsupported EGM version.")
                    else:
                        raise NifImportError("Not an EGM file.")
                finally:
                    # the file has been read or an error occurred: close file
                    egmfile.close()
            else:
                self.egmdata = None

            self.info("Importing data")
            # calculate and set frames per second
            if self.properties.animation:
                self.fps = self.get_frames_per_second(
                    self.data.roots
                    + (self.kfdata.roots if self.kfdata else []))
                self.context.scene.render.fps = self.fps

            # merge skeleton roots and transform geometry into the rest pose
            if self.properties.merge_skeleton_roots:
                pyffi.spells.nif.fix.SpellMergeSkeletonRoots(data=self.data).recurse()
            if self.properties.send_geoms_to_bind_pos:
                pyffi.spells.nif.fix.SpellSendGeometriesToBindPosition(data=self.data).recurse()
            if self.properties.send_detached_geoms_to_node_pos:
                pyffi.spells.nif.fix.SpellSendDetachedGeometriesToNodePosition(data=self.data).recurse()
            if self.properties.send_bones_to_bind_position:
                pyffi.spells.nif.fix.SpellSendBonesToBindPosition(data=self.data).recurse()
            if self.properties.apply_skin_deformation:
                for n_geom in self.data.get_global_iterator():
                    if not isinstance(n_geom, NifFormat.NiGeometry):
                        continue
                    if not n_geom.is_skin():
                        continue
                    self.info('Applying skin deformation on geometry %s'
                                     % n_geom.name)
                    vertices, normals = n_geom.get_skin_deformation()
                    for vold, vnew in zip(n_geom.data.vertices, vertices):
                        vold.x = vnew.x
                        vold.y = vnew.y
                        vold.z = vnew.z

            # scale tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = 1 / self.properties.scale_correction
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
                        if self.properties.skeleton ==  "SKELETON_ONLY":
                            nonbip_children = (child for child in root.children
                                               if child.name[:6] != 'Bip01 ')
                            for child in nonbip_children:
                                root.remove_child(child)
                # import this root block
                self.debug("Root block: %s" % root.get_global_display())
                # merge animation from kf tree into nif tree
                if self.properties.animation and self.kfdata:
                    for kf_root in self.kfdata.roots:
                        self.import_kf_root(kf_root, root)
                # import the nif tree
                self.import_root(root)
        finally:
            # clear progress bar
            self.info("Finished")
            # XXX no longer needed?
            # do a full scene update to ensure that transformations are applied
            # self.context.scene.update()

        return {'FINISHED'}

    def import_root(self, root_block):
        """Main import function."""
        # check that this is not a kf file
        if isinstance(root_block,
                      (NifFormat.NiSequence,
                       NifFormat.NiSequenceStreamHelper)):
            raise NifImportError("direct .kf import not supported")

        # divinity 2: handle CStreamableAssetData
        if isinstance(root_block, NifFormat.CStreamableAssetData):
            root_block = root_block.root

        # sets the root block parent to None, so that when crawling back the
        # script won't barf
        root_block._parent = None

        # set the block parent through the tree, to ensure I can always move
        # backward
        self.set_parents(root_block)

        # mark armature nodes and bones
        self.armaturehelper.mark_armatures_bones(root_block)

        # import the keyframe notes
        if self.properties.animation:
            self.import_text_keys(root_block)

        # read the NIF tree
        if self.armaturehelper.is_armature_root(root_block):
            # special case 1: root node is skeleton root
            self.debug("%s is an armature root" % root_block.name)
            b_obj = self.import_branch(root_block)

        elif self.is_grouping_node(root_block):
            # special case 2: root node is grouping node
            self.debug("%s is a grouping node" % root_block.name)
            b_obj = self.import_branch(root_block)

        elif isinstance(root_block, NifFormat.NiTriBasedGeom):
            # trishape/tristrips root
            b_obj = self.import_branch(root_block)

        elif isinstance(root_block, NifFormat.NiNode):
            # root node is dummy scene node

            # process collision
            if root_block.collision_object:
                bhk_body = root_block.collision_object.body
                if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                    self.warning(
                        "Unsupported collision structure under node %s"
                        % root_block.name)
                self.bhkhelper.import_bhk_shape(bhkshape=bhk_body)

            #process extra data
            for n_extra in root_block.get_extra_datas():
                if isinstance(n_extra, NifFormat.BSXFlags):
                    # get bsx flags so we can attach it to collision object
                    bsx_flags = n_extra.integer_data
                elif isinstance(n_extra, NifFormat.NiStringExtraData):
                    if n_extra.name == "UPB":
                        upbflags = n_extra.string_data
                elif isinstance(n_extra, NifFormat.BSBound):
                    self.boundhelper.import_bounding_box(n_extra)


            # process all its children
            for child in root_block.children:
                b_obj = self.import_branch(child)

        elif isinstance(root_block, NifFormat.NiCamera):
            self.warning('Skipped NiCamera root')

        elif isinstance(root_block, NifFormat.NiPhysXProp):
            self.warning('Skipped NiPhysXProp root')

        else:
            self.warning(
                "Skipped unsupported root block type '%s' (corrupted nif?)."
                % root_block.__class__)

        # store bone matrix offsets for re-export
        if self.bones_extra_matrix:
            self.armaturehelper.store_bones_extra_matrix()

        # store original names for re-export
        if self.names:
            self.armaturehelper.store_names()

        # now all havok objects are imported, so we are
        # ready to import the havok constraints
        for hkbody in self.havok_objects:
            self.import_bhk_constraints(hkbody)

        # parent selected meshes to imported skeleton
        if self.properties.skeleton ==  "SKELETON_ONLY":
            # rename vertex groups to reflect bone names
            # (for blends imported with older versions of the scripts!)
            for b_child_obj in self.selected_objects:
                if b_child_obj.type == 'MESH':
                    for oldgroupname in b_child_obj.data.getVertGroupNames():
                        newgroupname = self.get_bone_name_for_blender(oldgroupname)
                        if oldgroupname != newgroupname:
                            self.info(
                                "%s: renaming vertex group %s to %s"
                                % (b_child_obj, oldgroupname, newgroupname))
                            b_child_obj.data.renameVertGroup(
                                oldgroupname, newgroupname)
            # set parenting
            b_obj.makeParentDeform(self.selected_objects)

    def import_branch(self, niBlock, b_armature=None, n_armature=None):
        """Read the content of the current NIF tree branch to Blender
        recursively.

        :param niBlock: The nif block to import.
        :param b_armature: The blender armature for the current branch.
        :param n_armature: The corresponding nif block for the armature for
            the current branch.
        """
        self.info("Importing data")
        if not niBlock:
            return None
        elif (isinstance(niBlock, NifFormat.NiTriBasedGeom)
              and self.properties.skeleton !=  "SKELETON_ONLY"):
            # it's a shape node and we're not importing skeleton only
            # (self.properties.skeleton ==  "SKELETON_ONLY")
            self.debug("Building mesh in import_branch")
            # note: transform matrix is set during import
            b_obj = self.import_mesh(niBlock)
            # skinning? add armature modifier
            if niBlock.skin_instance:
                self.armaturehelper.append_armature_modifier(b_obj, b_armature)
            return b_obj
        elif isinstance(niBlock, NifFormat.NiNode):
            children = niBlock.children
            # bounding box child?
            bsbound = self.find_extra(niBlock, NifFormat.BSBound)
            if not (children
                    or niBlock.collision_object
                    or bsbound or niBlock.has_bounding_box
                    or self.IMPORT_EXTRANODES):
                # do not import unless the node is "interesting"
                return None
            # import object
            if self.armaturehelper.is_armature_root(niBlock):
                # all bones in the tree are also imported by
                # import_armature
                if self.properties.skeleton !=  "GEOMETRY_ONLY":
                    b_obj = self.armaturehelper.import_armature(niBlock)
                    b_armature = b_obj
                    n_armature = niBlock
                else:
                    b_obj = self.selected_objects[0]
                    b_armature = b_obj
                    n_armature = niBlock
                    self.info(
                        "Merging nif tree '%s' with armature '%s'"
                        % (niBlock.name, b_obj.name))
                    if niBlock.name != b_obj.name:
                        self.warning(
                            "Taking nif block '%s' as armature '%s'"
                            " but names do not match"
                            % (niBlock.name, b_obj.name))
                # armatures cannot group geometries into a single mesh
                geom_group = []
            elif self.armaturehelper.is_bone(niBlock):
                # bones have already been imported during import_armature
                b_obj = b_armature.data.bones[self.names[niBlock]]
                # bones cannot group geometries into a single mesh
                geom_group = []
            else:
                # is it a grouping node?
                geom_group = self.is_grouping_node(niBlock)
                # if importing animation, remove children that have
                # morph controllers from geometry group
                if self.properties.animation:
                    for child in geom_group:
                        if self.find_controller(
                            child, NifFormat.NiGeomMorpherController):
                            geom_group.remove(child)
                # import geometry/empty
                if (not geom_group
                    or not self.properties.combine_shapes
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
                    self.info(
                        "Joining geometries %s to single object '%s'"
                        %([child.name for child in geom_group],
                          niBlock.name))
                    b_obj = None
                    for child in geom_group:
                        b_obj = self.import_mesh(child,
                                                 group_mesh=b_obj,
                                                 applytransform=True)
                    b_obj.name = self.import_name(niBlock)
                    # skinning? add armature modifier
                    if any(child.skin_instance
                           for child in geom_group):
                        self.armaturehelper.append_armature_modifier(b_obj, b_armature)
                    # settings for collision node
                    if isinstance(niBlock, NifFormat.RootCollisionNode):
                        b_obj.draw_type = 'BOUNDS'
                        b_obj.show_wire = True
                        b_obj.draw_bounds_type = 'POLYHEDERON'
                        b_obj.game.use_collision_bounds = True
                        b_obj.game.collision_bounds_type = 'TRIANGLE_MESH'
                        # also remove duplicate vertices
                        b_mesh = b_obj.data
                        numverts = len(b_mesh.vertices)
                        # 0.005 = 1/200
                        numdel = b_mesh.remDoubles(0.005)
                        if numdel:
                            self.info(
                                "Removed %i duplicate vertices"
                                " (out of %i) from collision mesh"
                                % (numdel, numverts))

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

            # if not importing skeleton only
            if self.properties.skeleton !=  "SKELETON_ONLY":
                # import collision objects
                if isinstance(niBlock.collision_object, NifFormat.bhkNiCollisionObject):
                    bhk_body = niBlock.collision_object.body
                    if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                        self.warning(
                            "Unsupported collision structure"
                            " under node %s" % niBlock.name)

                    collision_objs = self.bhkhelper.import_bhk_shape(bhkshape=bhk_body)
                    # register children for parentship
                    object_children += [
                        (bhk_body, b_child) for b_child in collision_objs]

                # import bounding box
                if bsbound:
                    object_children += [
                        (bsbound, self.bhkhelper.import_bounding_box(bsbound))]

            # fix parentship
            if isinstance(b_obj, bpy.types.Object):
                # simple object parentship
                for (n_child, b_child) in object_children:
                    b_child.parent = b_obj

            elif isinstance(b_obj, bpy.types.Bone):
                # bone parentship, is a bit more complicated
                # go to rest position
                b_armature.data.restPosition = True
                # set up transforms
                for n_child, b_child in object_children:
                    # save transform
                    matrix = mathutils.Matrix(
                        b_child.getMatrix('localspace'))
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
                    # with X = self.bones_extra_matrix[B]

                    # post multiply Z with X^{-1}
                    extra = mathutils.Matrix(
                        self.bones_extra_matrix[niBlock])
                    extra.invert()
                    matrix = matrix * extra
                    # cancel out the tail translation T
                    # (the tail causes a translation along
                    # the local Y axis)
                    matrix[3][1] -= b_obj.length
                    b_child.matrix_local = matrix
                    # parent child to the bone
                    b_armature.makeParentBone(
                        [b_child], b_obj.name)
                b_armature.data.restPosition = False
            else:
                raise RuntimeError(
                    "Unexpected object type %s" % b_obj.__class__)

            # track camera for billboard nodes
            if isinstance(niBlock, NifFormat.NiBillboardNode):
                # find camera object
                for obj in self.context.scene.objects:
                    if obj.type == 'CAMERA':
                        break
                else:
                    raise NifImportError(
                        "Scene needs camera for billboard node"
                        " (add a camera and try again)")
                # make b_obj track camera object
                #b_obj.setEuler(0,0,0)
                b_obj.constraints.append(
                    bpy.types.Constraint.TRACKTO)
                self.warning(
                    "Constraint for billboard node on %s added"
                    " but target not set due to transform bug"
                    " in Blender. Set target to Camera manually."
                    % b_obj)
                constr = b_obj.constraints[-1]
                constr[Blender.Constraint.Settings.TRACK] = Blender.Constraint.Settings.TRACKZ
                constr[Blender.Constraint.Settings.UP] = Blender.Constraint.Settings.UPY
                # yields transform bug!
                #constr[Blender.Constraint.Settings.TARGET] = obj

            # set object transform
            # this must be done after all children objects have been
            # parented to b_obj
            if isinstance(b_obj, bpy.types.Object):
                # note: bones already have their matrix set
                b_obj.matrix_local = self.import_matrix(niBlock)

                # import the animations
                if self.properties.animation:
                    self.set_animation(niBlock, b_obj)
                    # import the extras
                    self.import_text_keys(niBlock)
                    # import vis controller
                    self.import_object_vis_controller(
                        b_object=b_obj, n_node=niBlock)

            # import extra node data, such as node type
            # (other types should be added here too)
            if (isinstance(niBlock, NifFormat.NiLODNode)
                # XXX additional isinstance(b_obj, bpy.types.Object)
                # XXX is a 'workaround' to the limitation that bones
                # XXX cannot have properties in Blender 2.4x
                # XXX (remove this check with Blender 2.5)
                and isinstance(b_obj, bpy.types.Object)):
                b_obj.addProperty("Type", "NiLODNode", "STRING")
                # import lod data
                range_data = niBlock.lod_level_data
                for lod_level, (n_child, b_child) in zip(
                    range_data.lod_levels, b_children_list):
                    b_child.addProperty(
                        "Near Extent", lod_level.near_extent, "FLOAT")
                    b_child.addProperty(
                        "Far Extent", lod_level.far_extent, "FLOAT")

            return b_obj
        # all else is currently discarded
        return None

    def import_name(self, niBlock, max_length=22):
        """Get unique name for an object, preserving existing names.
        The maximum name length defaults to 22, since this is the
        maximum for Blender objects. Bone names can reach length 32.

        :param niBlock: A named nif block.
        :type niBlock: :class:`~pyffi.formats.nif.NifFormat.NiObjectNET`
        :param max_length: The maximum length of the name.
        :type max_length: :class:`int`
        """
        if niBlock in self.names:
            return self.names[niBlock]

        self.debug(
            "Importing name for %s block from %s"
            % (niBlock.__class__.__name__, niBlock.name))

        # find unique name for Blender to use
        uniqueInt = 0
        # strip null terminator from name
        niBlock.name = niBlock.name.strip(b"\x00")
        niName = niBlock.name.decode()
        # if name is empty, create something non-empty
        if not niName:
            if isinstance(niBlock, NifFormat.RootCollisionNode):
                niName = "collision"
            else:
                niName = "noname"
        for uniqueInt in range(-1, 1000):
            # limit name length
            if uniqueInt == -1:
                shortName = niName[:max_length-1]
            else:
                shortName = ('%s.%02d'
                             % (niName[:max_length-4],
                                uniqueInt))
            # bone naming convention for blender
            shortName = self.get_bone_name_for_blender(shortName)
            # make sure it is unique
            if (shortName not in bpy.data.objects
                and shortName not in bpy.data.materials
                and shortName not in bpy.data.meshes):
                # shortName not in use anywhere
                break
        else:
            raise RuntimeError("Ran out of names.")
        # save mapping
        # block niBlock has Blender name shortName
        self.names[niBlock] = shortName
        # Blender name shortName corresponds to niBlock
        self.blocks[shortName] = niBlock
        self.debug("Selected unique name %s" % shortName)
        return shortName

    def import_matrix(self, niBlock, relative_to=None):
        """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
        n_scale, n_rot_mat3, n_loc_vec3 = niBlock.get_transform(relative_to).get_scale_rotation_translation()

        # create a location matrix
        b_loc_vec = mathutils.Vector(n_loc_vec3.as_tuple())
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)

        # create a scale matrix
        b_scale_mat = mathutils.Matrix.Scale(n_scale, 4)

        # create a rotation matrix
        b_rot_mat = mathutils.Matrix()
        b_rot_mat[0].xyz = n_rot_mat3.m_11, n_rot_mat3.m_21, n_rot_mat3.m_31
        b_rot_mat[1].xyz = n_rot_mat3.m_12, n_rot_mat3.m_22, n_rot_mat3.m_32
        b_rot_mat[2].xyz = n_rot_mat3.m_13, n_rot_mat3.m_23, n_rot_mat3.m_33

        return b_loc_vec * b_rot_mat * b_scale_mat

    def import_empty(self, niBlock):
        """Creates and returns a grouping empty."""
        shortname = self.import_name(niBlock)
        b_empty = bpy.data.objects.new(shortname, None)

        # TODO - is longname needed???
        b_empty.niftools.longname = niBlock.name.decode()

        self.context.scene.objects.link(b_empty)

        if niBlock.name in self.bone_priorities:
            constr = b_empty.constraints.append(
                bpy.types.Constraint.NULL)
            constr.name = "priority:%i" % self.bone_priorities[niBlock.name]
        return b_empty



    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not self.properties.animation:
            return

        self.import_material_alpha_controller(b_material, n_geom)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("MirR", "MirG", "MirB"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("R", "G", "B"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.import_material_color_controller(
            b_material=b_material,
            b_channels=("SpecR", "SpecG", "SpecB"),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_SPECULAR)
        self.import_material_uv_controller(b_material, n_geom)

    def import_material_uv_controller(self, b_material, n_geom):
        """Import UV controller data."""
        # search for the block
        n_ctrl = self.find_controller(n_geom,
                                      NifFormat.NiUVController)
        if not(n_ctrl and n_ctrl.data):
            return
        self.info("importing UV controller")
        b_channels = ("OfsX", "OfsY", "SizeX", "SizeY")
        for b_channel, n_uvgroup in zip(b_channels,
                                        n_ctrl.data.uv_groups):
            if n_uvgroup.keys:
                # create curve in material ipo
                b_ipo = self.get_material_ipo(b_material)
                b_curve = b_ipo.addCurve(b_channel)
                b_curve.interpolation = self.get_b_ipol_from_n_ipol(
                    n_uvgroup.interpolation)
                b_curve.extend = self.get_extend_from_flags(n_ctrl.flags)
                for n_key in n_uvgroup.keys:
                    if b_channel.startswith("Ofs"):
                        # offsets are negated
                        b_curve[1 + n_key.time * self.fps] = -n_key.value
                    else:
                        b_curve[1 + n_key.time * self.fps] = n_key.value

    def import_material_alpha_controller(self, b_material, n_geom):
        # find alpha controller
        n_matprop = self.find_property(n_geom, NifFormat.NiMaterialProperty)
        if not n_matprop:
            return
        n_alphactrl = self.find_controller(n_matprop,
                                           NifFormat.NiAlphaController)
        if not(n_alphactrl and n_alphactrl.data):
            return
        self.info("importing alpha controller")
        b_channel = "Alpha"
        b_ipo = self.get_material_ipo(b_material)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = self.get_b_ipol_from_n_ipol(
            n_alphactrl.data.data.interpolation)
        b_curve.extend = self.get_extend_from_flags(n_alphactrl.flags)
        for n_key in n_alphactrl.data.data.keys:
            b_curve[1 + n_key.time * self.fps] = n_key.value

    def import_material_color_controller(
        self, b_material, b_channels, n_geom, n_target_color):
        # find material color controller with matching target color
        n_matprop = self.find_property(n_geom, NifFormat.NiMaterialProperty)
        if not n_matprop:
            return
        for ctrl in n_matprop.get_controllers():
            if isinstance(ctrl, NifFormat.NiMaterialColorController):
                if ctrl.get_target_color() == n_target_color:
                    n_matcolor_ctrl = ctrl
                    break
        else:
            return
        self.info(
            "importing material color controller for target color %s"
            " into blender channels %s"
            % (n_target_color, b_channels))
        # import data as curves
        b_ipo = self.get_material_ipo(b_material)
        for i, b_channel in enumerate(b_channels):
            b_curve = b_ipo.addCurve(b_channel)
            b_curve.interpolation = self.get_b_ipol_from_n_ipol(
                n_matcolor_ctrl.data.data.interpolation)
            b_curve.extend = self.get_extend_from_flags(n_matcolor_ctrl.flags)
            for n_key in n_matcolor_ctrl.data.data.keys:
                b_curve[1 + n_key.time * self.fps] = n_key.value.as_list()[i]

    def get_material_ipo(self, b_material):
        """Return existing material ipo data, or if none exists, create one
        and return that.
        """
        if not b_material.ipo:
            b_material.ipo = Blender.Ipo.New("Material", "MatIpo")
        return b_material.ipo

    def import_object_vis_controller(self, b_object, n_node):
        """Import vis controller for blender object."""
        n_vis_ctrl = self.find_controller(n_node, NifFormat.NiVisController)
        if not(n_vis_ctrl and n_vis_ctrl.data):
            return
        self.info("importing vis controller")
        b_channel = "Layer"
        b_ipo = self.get_object_ipo(b_object)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = Blender.IpoCurve.InterpTypes.CONST
        b_curve.extend = self.get_extend_from_flags(n_vis_ctrl.flags)
        for n_key in n_vis_ctrl.data.keys:
            b_curve[1 + n_key.time * self.fps] = (
                2 ** (n_key.value + max([1] + self.context.scene.getLayers()) - 1))

    def get_object_ipo(self, b_object):
        """Return existing object ipo data, or if none exists, create one
        and return that.
        """
        if not b_object.ipo:
            b_object.ipo = Blender.Ipo.New("Object", "Ipo")
        return b_object.ipo

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

        self.info("Importing mesh data for geometry %s" % niBlock.name)

        if group_mesh:
            b_obj = group_mesh
            b_mesh = group_mesh.data
        else:
            # Mesh name -> must be unique, so tag it if needed
            b_name = self.import_name(niBlock)
            # create mesh data
            b_mesh = bpy.data.meshes.new(b_name)
            # create mesh object and link to data
            b_obj = bpy.data.objects.new(b_name, b_mesh)
            # link mesh object to the scene
            self.context.scene.objects.link(b_obj)
            # save original name as object property, for export
            if b_name != niBlock.name.decode():
                b_obj['Nif Name'] = niBlock.name.decode()

            # Mesh hidden flag
            if niBlock.flags & 1 == 1:
                b_obj.draw_type = 'WIRE' # hidden: wire
            else:
                b_obj.draw_type = 'TEXTURED' # not hidden: shaded

        # set transform matrix for the mesh
        if not applytransform:
            if group_mesh:
                raise NifImportError(
                    "BUG: cannot set matrix when importing meshes in groups;"
                    " use applytransform = True")

            b_obj.matrix_local = self.import_matrix(niBlock, relative_to=relative_to)

        else:
            # used later on
            transform = self.import_matrix(niBlock, relative_to=relative_to)

        # shortcut for mesh geometry data
        niData = niBlock.data
        if not niData:
            raise NifImportError("no shape data in %s" % b_name)

        # vertices
        n_verts = niData.vertices

        # faces
        n_tris = [list(tri) for tri in niData.get_triangles()]

        # "sticky" UV coordinates: these are transformed in Blender UV's
        n_uvco = niData.uv_sets

        # vertex normals
        n_norms = niData.normals

        '''
        Properties
        '''

        # Stencil (for double sided meshes)
        n_stencil_prop = self.find_property(niBlock, NifFormat.NiStencilProperty)
        # we don't check flags for now, nothing fancy
        if n_stencil_prop:
            b_mesh.show_double_sided = True
        else:
            b_mesh.show_double_sided = False

        # Material
        # note that NIF files only support one material for each trishape
        # find material property
        n_mat_prop = self.find_property(niBlock,
                                         NifFormat.NiMaterialProperty)

        if n_mat_prop:
            # Texture
            n_texture_prop = None
            if n_uvco:
                n_texture_prop = self.find_property(niBlock,
                                                  NifFormat.NiTexturingProperty)

            # Alpha
            n_alpha_prop = self.find_property(niBlock,
                                               NifFormat.NiAlphaProperty)

            # Specularity
            n_specular_prop = self.find_property(niBlock,
                                              NifFormat.NiSpecularProperty)

            # Wireframe
            n_wire_prop = self.find_property(niBlock,
                                              NifFormat.NiWireframeProperty)

            # bethesda shader
            bsShaderProperty = self.find_property(
                niBlock, NifFormat.BSShaderPPLightingProperty)

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

            # extra datas (for sid meier's railroads) that have material info
            extra_datas = []
            for extra in niBlock.get_extra_datas():
                if isinstance(extra, NifFormat.NiIntegerExtraData):
                    if extra.name in self.EXTRA_SHADER_TEXTURES:
                        # yes, it describes the shader slot number
                        extra_datas.append(extra)

            # create material and assign it to the mesh
            # XXX todo: delegate search for properties to import_material
            material = self.materialhelper.import_material(n_mat_prop, n_texture_prop,
                                            n_alpha_prop, n_specular_prop,
                                            textureEffect, n_wire_prop,
                                            bsShaderProperty, extra_datas)
            # XXX todo: merge this call into import_material
            self.import_material_controllers(material, niBlock)
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

        # if there are no vertices then enable face index shifts
        # (this fixes an issue with indexing)
        if len(b_mesh.vertices) == 0:
            check_shift = True
        else:
            check_shift = False

        # v_map will store the vertex index mapping
        # nif vertex i maps to blender vertex v_map[i]
        v_map = [0 for i in range(len(n_verts))] # pre-allocate memory, for faster performance

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
                k = (int(v.x*self.VERTEX_RESOLUTION),
                     int(v.y*self.VERTEX_RESOLUTION),
                     int(v.z*self.VERTEX_RESOLUTION),
                     int(n.x*self.NORMAL_RESOLUTION),
                     int(n.y*self.NORMAL_RESOLUTION),
                     int(n.z*self.NORMAL_RESOLUTION))
            else:
                k = (int(v.x*self.VERTEX_RESOLUTION),
                     int(v.y*self.VERTEX_RESOLUTION),
                     int(v.z*self.VERTEX_RESOLUTION))
            # check if vertex was already added, and if so, what index
            try:
                # this is the bottle neck...
                # can we speed this up?
                n_map_k = n_map[k]
            except KeyError:
                n_map_k = None
            if not n_map_k:
                # not added: new vertex / normal pair
                n_map[k] = i         # unique vertex / normal pair with key k was added, with NIF index i
                v_map[i] = b_v_index # NIF vertex i maps to blender vertex b_v_index
                # add the vertex
                if applytransform:
                    v = mathutils.Vector([v.x, v.y, v.z])
                    v  = v * transform
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                else:
                    b_mesh.vertices.add(1)
                    b_mesh.vertices[-1].co = [v.x, v.y, v.z]
                # adds normal info if present (Blender recalculates these when
                # switching between edit mode and object mode, handled further)
                #if n_norms:
                #    mv = b_mesh.vertices[b_v_index]
                #    n = n_norms[i]
                #    mv.normal = mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                # NIF vertex i maps to Blender vertex v_map[n_map_k]
                v_map[i] = v_map[n_map_k]
        # report
        self.debug("%i unique vertex-normal pairs" % len(n_map))
        # release memory
        del n_map

        # Adds the faces to the mesh
        f_map = [None]*len(n_tris)
        b_f_index = len(b_mesh.faces)
        num_new_faces = 0 # counter for debugging
        unique_faces = set() # to avoid duplicate faces
        for i, f in enumerate(n_tris):
            # get face index
            f_verts = [v_map[vert_index] for vert_index in f]
            # skip degenerate faces
            # we get a ValueError on faces.extend otherwise
            if (f_verts[0] == f_verts[1]) or (f_verts[1] == f_verts[2]) or (f_verts[2] == f_verts[0]):
                continue
            if tuple(f_verts) in unique_faces:
                continue
            unique_faces.add(tuple(f_verts))
            b_mesh.faces.add(1)
            if f_verts[2] == 0:
                # eeekadoodle fix
                f_verts[0], f_verts[1], f_verts[2] = f_verts[2], f_verts[0], f_verts[1]
                f[0], f[1], f[2] = f[2], f[0], f[1] # f[0] comes second
            b_mesh.faces[-1].vertices_raw = f_verts + [0]
            # keep track of added faces, mapping NIF face index to
            # Blender face index
            f_map[i] = b_f_index
            b_f_index += 1
            num_new_faces += 1
        # at this point, deleted faces (degenerate or duplicate)
        # satisfy f_map[i] = None

        self.debug("%i unique faces" % num_new_faces)

        # set face smoothing and material
        for b_f_index in f_map:
            if b_f_index is None:
                continue
            f = b_mesh.faces[b_f_index]
            f.use_smooth = True if n_norms else False
            f.material_index = materialIndex

        # vertex colors
        n_vcol = niData.vertex_colors

        if n_vcol:
            # create vertex_layers
            b_meshcolorlayer = b_mesh.vertex_colors.new(name="VertexColor") # color layer
            b_meshcolorlayeralpha = b_mesh.vertex_colors.new(name="VertexAlpha") # greyscale

            # Mesh Vertex Color / Mesh Face
            for n_tri, b_face_index in zip(n_tris, f_map):
                if b_face_index is None:
                    continue

                # MeshFace to MeshColor
                b_meshcolor = b_meshcolorlayer.data[b_face_index]
                b_meshalpha = b_meshcolorlayeralpha.data[b_face_index]

                for n_vert_index, n_vert in enumerate(n_tri):
                    '''TODO: Request index access in the Bpy API
                    b_meshcolor.color[n_vert_index]'''

                    # Each MeshColor has n Color's, mapping to (n)_vertex.
                    b_color = getattr(b_meshcolor, "color%s" % (n_vert_index + 1))
                    b_colora = getattr(b_meshalpha, "color%s" % (n_vert_index + 1))

                    b_color.r = n_vcol[n_vert].r
                    b_color.g = n_vcol[n_vert].g
                    b_color.b = n_vcol[n_vert].b
                    b_colora.v = n_vcol[n_vert].a

            # vertex colors influence lighting...
            # we have to set the use_vertex_color_light flag on the material
            # see below

        # UV coordinates
        # NIF files only support 'sticky' UV coordinates, and duplicates
        # vertices to emulate hard edges and UV seam. So whenever a hard edge
        # or a UV seam is present the mesh, vertices are duplicated. Blender
        # only must duplicate vertices for hard edges; duplicating for UV seams
        # would introduce unnecessary hard edges.

        # only import UV if there are faces
        # (some corner cases have only one vertex, and no faces,
        # and b_mesh.faceUV = 1 on such mesh raises a runtime error)
        if b_mesh.faces:
            # blender 2.5+ aloways uses uv's per face?
            #b_mesh.faceUV = 1
            #b_mesh.vertexUV = 0
            for i, uv_set in enumerate(n_uvco):
                # Set the face UV's for the mesh. The NIF format only supports
                # vertex UV's, but Blender only allows explicit editing of face
                # UV's, so load vertex UV's as face UV's
                uvlayer = self.materialhelper.get_uv_layer_name(i)
                if not uvlayer in b_mesh.uv_textures:
                    b_mesh.uv_textures.new(uvlayer)
                for f, b_f_index in zip(n_tris, f_map):
                    if b_f_index is None:
                        continue
                    uvlist = [(uv_set[vert_index].u, 1.0 - uv_set[vert_index].v) for vert_index in f]
                    b_mesh.uv_textures[uvlayer].data[b_f_index].uv1 = uvlist[0]
                    b_mesh.uv_textures[uvlayer].data[b_f_index].uv2 = uvlist[1]
                    b_mesh.uv_textures[uvlayer].data[b_f_index].uv3 = uvlist[2]
            b_mesh.uv_textures.active_index = 0

        if material:
            # fix up vertex colors depending on whether we had textures in the
            # material
            mbasetex = material.texture_slots[0]
            mglowtex = material.texture_slots[1]
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
                    for b_f_index in f_map:
                        if b_f_index is None:
                            continue
                        tface = b_mesh.uv_textures.active.data[b_f_index]
                        # gone in blender 2.5x+?
                        # f.mode = Blender.Mesh.FaceModes['TEX']
                        # f.transp = Blender.Mesh.FaceTranspModes['ALPHA']
                        tface.image = imgobj

        # import skinning info, for meshes affected by bones
        skininst = niBlock.skin_instance
        if skininst:
            skindata = skininst.data
            bones = skininst.bones
            boneWeights = skindata.bone_list
            for idx, bone in enumerate(bones):
                # skip empty bones (see pyffi issue #3114079)
                if not bone:
                    continue
                vertex_weights = boneWeights[idx].vertex_weights
                groupname = self.names[bone]
                if not groupname in b_mesh.getVertGroupNames():
                    b_mesh.addVertGroup(groupname)
                for skinWeight in vertex_weights:
                    vert = skinWeight.index
                    weight = skinWeight.weight
                    b_mesh.assignVertsToGroup(
                        groupname, [v_map[vert]], weight,
                        Blender.Mesh.AssignModes.REPLACE)

        # import body parts as vertex groups
        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
            skinpart = niBlock.get_skin_partition()
            for bodypart, skinpartblock in zip(
                skininst.partitions, skinpart.skin_partition_blocks):
                bodypart_wrap = NifFormat.BSDismemberBodyPartType()
                bodypart_wrap.set_value(bodypart.body_part)
                groupname = bodypart_wrap.get_detail_display()
                # create vertex group if it did not exist yet
                if not(groupname in b_mesh.getVertGroupNames()):
                    b_mesh.addVertGroup(groupname)
                # find vertex indices of this group
                groupverts = [v_map[v_index]
                              for v_index in skinpartblock.vertex_map]
                # create the group
                b_mesh.assignVertsToGroup(
                    groupname, groupverts, 1,
                    Blender.Mesh.AssignModes.ADD)

        # import morph controller
        # XXX todo: move this to import_mesh_controllers
        if self.properties.animation:
            morphCtrl = self.find_controller(niBlock, NifFormat.NiGeomMorpherController)
            if morphCtrl:
                morphData = morphCtrl.data
                if morphData.num_morphs:
                    # insert base key at frame 1, using relative keys
                    b_mesh.insertKey(1, 'relative')
                    # get name for base key
                    keyname = morphData.morphs[0].frame_name
                    if not keyname:
                        keyname = 'Base'
                    # set name for base key
                    b_mesh.key.blocks[0].name = keyname
                    # get base vectors and import all morphs
                    baseverts = morphData.morphs[0].vectors
                    b_ipo = Blender.Ipo.New('Key' , 'KeyIpo')
                    b_mesh.key.ipo = b_ipo
                    for idxMorph in range(1, morphData.num_morphs):
                        # get name for key
                        keyname = morphData.morphs[idxMorph].frame_name
                        if not keyname:
                            keyname = 'Key %i' % idxMorph
                        self.info("inserting key '%s'" % keyname)
                        # get vectors
                        morphverts = morphData.morphs[idxMorph].vectors
                        # for each vertex calculate the key position from base
                        # pos + delta offset
                        assert(len(baseverts) == len(morphverts) == len(v_map))
                        for bv, mv, b_v_index in zip(baseverts, morphverts, v_map):
                            base = mathutils.Vector(bv.x, bv.y, bv.z)
                            delta = mathutils.Vector(mv.x, mv.y, mv.z)
                            v = base + delta
                            if applytransform:
                                v *= transform
                            b_mesh.vertices[b_v_index].co[0] = v.x
                            b_mesh.vertices[b_v_index].co[1] = v.y
                            b_mesh.vertices[b_v_index].co[2] = v.z
                        # update the mesh and insert key
                        b_mesh.insertKey(idxMorph, 'relative')
                        # set name for key
                        b_mesh.key.blocks[idxMorph].name = keyname
                        # set up the ipo key curve
                        try:
                            b_curve = b_ipo.addCurve(keyname)
                        except ValueError:
                            # this happens when two keys have the same name
                            # an instance of this is in fallout 3
                            # meshes/characters/_male/skeleton.nif HeadAnims:0
                            self.warning(
                                "skipped duplicate of key '%s'" % keyname)
                        # no idea how to set up the bezier triples -> switching
                        # to linear instead
                        b_curve.interpolation = Blender.IpoCurve.InterpTypes.LINEAR
                        # select extrapolation
                        b_curve.extend = self.get_extend_from_flags(morphCtrl.flags)
                        # set up the curve's control points
                        # first find the keys
                        # older versions store keys in the morphData
                        morphkeys = morphData.morphs[idxMorph].keys
                        # newer versions store keys in the controller
                        if (not morphkeys) and morphCtrl.interpolators:
                            morphkeys = morphCtrl.interpolators[idxMorph].data.data.keys
                        for key in morphkeys:
                            x =  key.value
                            frame =  1+int(key.time * self.fps + 0.5)
                            b_curve.addBezier( ( frame, x ) )
                        # finally: return to base position
                        for bv, b_v_index in zip(baseverts, v_map):
                            base = mathutils.Vector(bv.x, bv.y, bv.z)
                            if applytransform:
                                base *= transform
                            b_mesh.vertices[b_v_index].co[0] = base.x
                            b_mesh.vertices[b_v_index].co[1] = base.y
                            b_mesh.vertices[b_v_index].co[2] = base.z

        # import facegen morphs
        if self.egmdata:
            # XXX if there is an egm, the assumption is that there is only one
            # XXX mesh in the nif
            sym_morphs = [list(morph.get_relative_vertices())
                          for morph in self.egmdata.sym_morphs]
            asym_morphs = [list(morph.get_relative_vertices())
                          for morph in self.egmdata.asym_morphs]

            # insert base key at frame 1, using relative keys
            b_mesh.insertKey(1, 'relative')

            if self.IMPORT_EGMANIM:
                # if morphs are animated: create key ipo for mesh
                b_ipo = Blender.Ipo.New('Key' , 'KeyIpo')
                b_mesh.key.ipo = b_ipo


            morphs = ([(morph, "EGM SYM %i" % i)
                       for i, morph in enumerate(sym_morphs)]
                      +
                      [(morph, "EGM ASYM %i" % i)
                       for i, morph in enumerate(asym_morphs)])

            for morphverts, keyname in morphs:
                # length check disabled
                # as sometimes, oddly, the morph has more vertices...
                #assert(len(verts) == len(morphverts) == len(v_map))

                # for each vertex calculate the key position from base
                # pos + delta offset
                for bv, mv, b_v_index in zip(verts, morphverts, v_map):
                    base = mathutils.Vector(bv.x, bv.y, bv.z)
                    delta = mathutils.Vector(mv[0], mv[1], mv[2])
                    v = base + delta
                    if applytransform:
                        v *= transform
                    b_mesh.vertices[b_v_index].co[0] = v.x
                    b_mesh.vertices[b_v_index].co[1] = v.y
                    b_mesh.vertices[b_v_index].co[2] = v.z
                # update the mesh and insert key
                b_mesh.insertKey(1, 'relative')
                # set name for key
                b_mesh.key.blocks[-1].name = keyname

                if self.IMPORT_EGMANIM:
                    # set up the ipo key curve
                    b_curve = b_ipo.addCurve(keyname)
                    # linear interpolation
                    b_curve.interpolation = Blender.IpoCurve.InterpTypes.LINEAR
                    # constant extrapolation
                    b_curve.extend = Blender.IpoCurve.ExtendTypes.CONST
                    # set up the curve's control points
                    framestart = 1 + len(b_mesh.key.blocks) * 10
                    for frame, value in ((framestart, 0),
                                         (framestart + 5, self.IMPORT_EGMANIMSCALE),
                                         (framestart + 10, 0)):
                        b_curve.addBezier( ( frame, value ) )

            if self.IMPORT_EGMANIM:
                # set begin and end frame
                self.context.scene.getRenderingContext().startFrame(1)
                self.context.scene.getRenderingContext().endFrame(
                    11 + len(b_mesh.key.blocks) * 10)

            # finally: return to base position
            for bv, b_v_index in zip(verts, v_map):
                base = mathutils.Vector(bv.x, bv.y, bv.z)
                if applytransform:
                    base *= transform
                b_mesh.vertices[b_v_index].co[0] = base.x
                b_mesh.vertices[b_v_index].co[1] = base.y
                b_mesh.vertices[b_v_index].co[2] = base.z


        # import priority if existing
        if niBlock.name in self.bone_priorities:
            constr = b_obj.constraints.append(
                bpy.types.Constraint.NULL)
            constr.name = "priority:%i" % self.bone_priorities[niBlock.name]

        # recalculate mesh to render correctly
        # implementation note: update() without validate() can cause crash
        b_mesh.calc_normals()
        b_mesh.validate()
        b_mesh.update()

        return b_obj

    # import animation groups

    def import_text_keys(self, niBlock):
        """Stores the text keys that define animation start and end in a text
        buffer, so that they can be re-exported. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""
        if isinstance(niBlock, NifFormat.NiControllerSequence):
            txk = niBlock.text_keys
        else:
            txk = niBlock.find(block_type=NifFormat.NiTextKeyExtraData)
        if txk:
            # get animation text buffer, and clear it if it already exists
            # TODO git rid of try-except block here
            try:
                animtxt = [txt for txt in bpy.data.texts if txt.name == "Anim"][0]
                animtxt.clear()
            except:
                animtxt = bpy.data.texts.new("Anim")

            frame = 1
            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = 1 + int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                animtxt.write('%i/%s\n'%(frame, newkey))

            # set start and end frames
            self.context.scene.getRenderingContext().startFrame(1)
            self.context.scene.getRenderingContext().endFrame(frame)

    def get_frames_per_second(self, roots):
        """Scan all blocks and return a reasonable number for FPS."""
        # find all key times
        key_times = []
        for root in roots:
            for kfd in root.tree(block_type=NifFormat.NiKeyframeData):
                key_times.extend(key.time for key in kfd.translations.keys)
                key_times.extend(key.time for key in kfd.scales.keys)
                key_times.extend(key.time for key in kfd.quaternion_keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[0].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[1].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[2].keys)
            for kfi in root.tree(block_type=NifFormat.NiBSplineInterpolator):
                if not kfi.basis_data:
                    # skip bsplines without basis data (eg bowidle.kf in
                    # Oblivion)
                    continue
                key_times.extend(
                    point * (kfi.stop_time - kfi.start_time)
                    / (kfi.basis_data.num_control_points - 2)
                    for point in range(kfi.basis_data.num_control_points - 2))
            for uvdata in root.tree(block_type=NifFormat.NiUVData):
                for uvgroup in uvdata.uv_groups:
                    key_times.extend(key.time for key in uvgroup.keys)
        # not animated, return a reasonable default
        if not key_times:
            return 30
        # calculate FPS
        fps = 30
        lowest_diff = sum(abs(int(time * fps + 0.5) - (time * fps))
                          for time in key_times)
        # for fps in range(1,120): #disabled, used for testing
        for test_fps in [20, 25, 35]:
            diff = sum(abs(int(time * test_fps + 0.5)-(time * test_fps))
                       for time in key_times)
            if diff < lowest_diff:
                lowest_diff = diff
                fps = test_fps
        self.info("Animation estimated at %i frames per second." % fps)
        return fps

    def store_animation_data(self, rootBlock):
        return
        # very slow, implement later
        """
        niBlockList = [block for block in rootBlock.tree() if isinstance(block, NifFormat.NiAVObject)]
        for niBlock in niBlockList:
            kfc = self.find_controller(niBlock, NifFormat.NiKeyframeController)
            if not kfc: continue
            kfd = kfc.data
            if not kfd: continue
            _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.translations.keys])
            _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.scales.keys])
            if kfd.rotation_type == 4:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.xyz_rotations.keys])
            else:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.quaternion_keys])

        # set the frames in the _ANIMATION_DATA list
        for key in _ANIMATION_DATA:
            # time 0 is frame 1
            key['frame'] = 1 + int(key['data'].time * self.fps + 0.5)

        # sort by frame, I need this later
        _ANIMATION_DATA.sort(lambda key1, key2: cmp(key1['frame'], key2['frame']))
        """

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
        if not self.properties.combine_shapes:
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

    def set_animation(self, niBlock, b_obj):
        """Load basic animation info for this object."""
        kfc = self.find_controller(niBlock, NifFormat.NiKeyframeController)
        if not kfc:
            # no animation data: do nothing
            return

        if kfc.interpolator:
            if isinstance(kfc.interpolator, NifFormat.NiBSplineInterpolator):
                kfd = None # not supported yet so avoids fatal error - should be kfc.interpolator.spline_data when spline data is figured out.
            else:
                kfd = kfc.interpolator.data
        else:
            kfd = kfc.data

        if not kfd:
            # no animation data: do nothing
            return

        # denote progress
        self.info("Animation")
        self.info("Importing animation data for %s" % b_obj.name)
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        # create an Ipo for this object
        b_ipo = self.get_object_ipo(b_obj)
        # get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys
        self.debug('Scale keys...')
        for key in scales.keys:
            frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.SizeX = key.value
            b_obj.SizeY = key.value
            b_obj.SizeZ = key.value
            b_obj.insertIpoKey(Blender.Object.SIZE)

        # detect the type of rotation keys
        rotation_type = kfd.rotation_type
        if rotation_type == 4:
            # uses xyz rotation
            xkeys = kfd.xyz_rotations[0].keys
            ykeys = kfd.xyz_rotations[1].keys
            zkeys = kfd.xyz_rotations[2].keys
            self.debug('Rotation keys...(euler)')
            for (xkey, ykey, zkey) in zip(xkeys, ykeys, zkeys):
                frame = 1+int(xkey.time * self.fps + 0.5) # time 0.0 is frame 1
                # XXX we assume xkey.time == ykey.time == zkey.time
                Blender.Set('curframe', frame)
                # both in radians, no conversion needed
                b_obj.RotX = xkey.value
                b_obj.RotY = ykey.value
                b_obj.RotZ = zkey.value
                b_obj.insertIpoKey(Blender.Object.ROT)
        else:
            # uses quaternions
            if kfd.quaternion_keys:
                self.debug('Rotation keys...(quaternions)')
            for key in kfd.quaternion_keys:
                frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                rot = mathutils.Quaternion(key.value.w, key.value.x, key.value.y, key.value.z).toEuler()
                # Blender euler is in degrees, object RotXYZ is in radians
                b_obj.RotX = rot.x * self.D2R
                b_obj.RotY = rot.y * self.D2R
                b_obj.RotZ = rot.z * self.D2R
                b_obj.insertIpoKey(Blender.Object.ROT)

        if translations.keys:
            self.debug('Translation keys...')
        for key in translations.keys:
            frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.LocX = key.value.x
            b_obj.LocY = key.value.y
            b_obj.LocZ = key.value.z
            b_obj.insertIpoKey(Blender.Object.LOC)

        Blender.Set('curframe', 1)

    def import_bhk_constraints(self, hkbody):
        """Imports a bone havok constraint as Blender object constraint."""
        assert(isinstance(hkbody, NifFormat.bhkRigidBody))

        # check for constraints
        if not hkbody.constraints:
            return

        # find objects
        if len(self.havok_objects[hkbody]) != 1:
            self.warning(
                "Rigid body with no or multiple shapes, constraints skipped")
            return

        b_hkobj = self.havok_objects[hkbody][0]

        self.info("Importing constraints for %s" % b_hkobj.name)

        # now import all constraints
        for hkconstraint in hkbody.constraints:

            # check constraint entities
            if not hkconstraint.num_entities == 2:
                self.warning(
                    "Constraint with more than 2 entities, skipped")
                continue
            if not hkconstraint.entities[0] is hkbody:
                self.warning(
                    "First constraint entity not self, skipped")
                continue
            if not hkconstraint.entities[1] in self.havok_objects:
                self.warning(
                    "Second constraint entity not imported, skipped")
                continue

            # get constraint descriptor
            if isinstance(hkconstraint, NifFormat.bhkRagdollConstraint):
                hkdescriptor = hkconstraint.ragdoll
            elif isinstance(hkconstraint, NifFormat.bhkLimitedHingeConstraint):
                hkdescriptor = hkconstraint.limited_hinge
            elif isinstance(hkconstraint, NifFormat.bhkHingeConstraint):
                hkdescriptor = hkconstraint.hinge
            elif isinstance(hkconstraint, NifFormat.bhkMalleableConstraint):
                if hkconstraint.type == 7:
                    hkdescriptor = hkconstraint.ragdoll
                elif hkconstraint.type == 2:
                    hkdescriptor = hkconstraint.limited_hinge
                else:
                    self.warning("Unknown malleable type (%i), skipped"
                                        % hkconstraint.type)
                # extra malleable constraint settings
                ### damping parameters not yet in Blender Python API
                ### tau (force between bodies) not supported by Blender
            else:
                self.warning("Unknown constraint type (%s), skipped"
                                    % hkconstraint.__class__.__name__)
                continue

            # add the constraint as a rigid body joint
            b_constr = b_hkobj.constraints.append(bpy.types.Constraint.RIGIDBODYJOINT)

            # note: rigidbodyjoint parameters (from Constraint.c)
            # CONSTR_RB_AXX 0.0
            # CONSTR_RB_AXY 0.0
            # CONSTR_RB_AXZ 0.0
            # CONSTR_RB_EXTRAFZ 0.0
            # CONSTR_RB_MAXLIMIT0 0.0
            # CONSTR_RB_MAXLIMIT1 0.0
            # CONSTR_RB_MAXLIMIT2 0.0
            # CONSTR_RB_MAXLIMIT3 0.0
            # CONSTR_RB_MAXLIMIT4 0.0
            # CONSTR_RB_MAXLIMIT5 0.0
            # CONSTR_RB_MINLIMIT0 0.0
            # CONSTR_RB_MINLIMIT1 0.0
            # CONSTR_RB_MINLIMIT2 0.0
            # CONSTR_RB_MINLIMIT3 0.0
            # CONSTR_RB_MINLIMIT4 0.0
            # CONSTR_RB_MINLIMIT5 0.0
            # CONSTR_RB_PIVX 0.0
            # CONSTR_RB_PIVY 0.0
            # CONSTR_RB_PIVZ 0.0
            # CONSTR_RB_TYPE 12
            # LIMIT 63
            # PARSIZEY 63
            # TARGET [Object "capsule.002"]

            # limit 3, 4, 5 correspond to angular limits along x, y and z
            # and are measured in degrees

            # pivx/y/z is the pivot point

            # set constraint target
            b_constr[Blender.Constraint.Settings.TARGET] = \
                self.havok_objects[hkconstraint.entities[1]][0]
            # set rigid body type (generic)
            b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] = 12
            # limiting parameters (limit everything)
            b_constr[Blender.Constraint.Settings.LIMIT] = 63

            # get pivot point
            pivot = mathutils.Vector(
                hkdescriptor.pivot_a.x * self.HAVOK_SCALE,
                hkdescriptor.pivot_a.y * self.HAVOK_SCALE,
                hkdescriptor.pivot_a.z * self.HAVOK_SCALE)

            # get z- and x-axes of the constraint
            # (also see export_nif.py NifImport.export_constraints)
            if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                # for ragdoll, take z to be the twist axis (central axis of the
                # cone, that is)
                axis_z = mathutils.Vector(
                    hkdescriptor.twist_a.x,
                    hkdescriptor.twist_a.y,
                    hkdescriptor.twist_a.z)
                # for ragdoll, let x be the plane vector
                axis_x = mathutils.Vector(
                    hkdescriptor.plane_a.x,
                    hkdescriptor.plane_a.y,
                    hkdescriptor.plane_a.z)
                # set the angle limits
                # (see http://niftools.sourceforge.net/wiki/Oblivion/Bhk_Objects/Ragdoll_Constraint
                # for a nice picture explaining this)
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MINLIMIT5] = \
                    hkdescriptor.twist_min_angle
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MAXLIMIT5] = \
                    hkdescriptor.twist_max_angle
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MINLIMIT3] = \
                    -hkdescriptor.cone_max_angle
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MAXLIMIT3] = \
                    hkdescriptor.cone_max_angle
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MINLIMIT4] = \
                    hkdescriptor.plane_min_angle
                b_constr[Blender.Constraint.Settings.CONSTR_RB_MAXLIMIT4] = \
                    hkdescriptor.plane_max_angle
            elif isinstance(hkdescriptor, NifFormat.LimitedHingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_1.x,
                    hkdescriptor.perp_2_axle_in_a_1.y,
                    hkdescriptor.perp_2_axle_in_a_1.z)
                # for hinge, take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.Vector(
                    hkdescriptor.axle_a.x,
                    hkdescriptor.axle_a.y,
                    hkdescriptor.axle_a.z)
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_2.x,
                    hkdescriptor.perp_2_axle_in_a_2.y,
                    hkdescriptor.perp_2_axle_in_a_2.z)
                # they should form a orthogonal basis
                if (mathutils.CrossVecs(axis_x, axis_y)
                    - axis_z).length > 0.01:
                    # either not orthogonal, or negative orientation
                    if (mathutils.CrossVecs(-axis_x, axis_y)
                        - axis_z).length > 0.01:
                        self.warning(
                            "Axes are not orthogonal in %s;"
                            " arbitrary orientation has been chosen"
                            % hkdescriptor.__class__.__name__)
                        axis_z = mathutils.CrossVecs(axis_x, axis_y)
                    else:
                        # fix orientation
                        self.warning(
                            "X axis flipped in %s to fix orientation"
                            % hkdescriptor.__class__.__name__)
                        axis_x = -axis_x
                # getting properties with no blender constraint
                # equivalent and setting as obj properties
                b_hkobj.addProperty("LimitedHinge_MaxAngle",
                                    hkdescriptor.max_angle)
                b_hkobj.addProperty("LimitedHinge_MinAngle",
                                    hkdescriptor.min_angle)
                b_hkobj.addProperty("LimitedHinge_MaxFriction",
                                    hkdescriptor.max_friction)

            elif isinstance(hkdescriptor, NifFormat.HingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_1.x,
                    hkdescriptor.perp_2_axle_in_a_1.y,
                    hkdescriptor.perp_2_axle_in_a_1.z)
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_2.x,
                    hkdescriptor.perp_2_axle_in_a_2.y,
                    hkdescriptor.perp_2_axle_in_a_2.z)
                # take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.CrossVecs(axis_y, axis_z)
            else:
                raise ValueError("unknown descriptor %s"
                                 % hkdescriptor.__class__.__name__)

            # transform pivot point and constraint matrix into object
            # coordinates
            # (also see export_nif.py NifImport.export_constraints)

            # the pivot point v is in hkbody coordinates
            # however blender expects it in object coordinates, v'
            # v * R * B = v' * O * T * B'
            # with R = rigid body transform (usually unit tf)
            # B = nif bone matrix
            # O = blender object transform
            # T = bone tail matrix (translation in Y direction)
            # B' = blender bone matrix
            # so we need to cancel out the object transformation by
            # v' = v * R * B * B'^{-1} * T^{-1} * O^{-1}

            # the local rotation L at the pivot point must be such that
            # (axis_z + v) * R * B = ([0 0 1] * L + v') * O * T * B'
            # so (taking the rotation parts of all matrices!!!)
            # [0 0 1] * L = axis_z * R * B * B'^{-1} * T^{-1} * O^{-1}
            # and similarly
            # [1 0 0] * L = axis_x * R * B * B'^{-1} * T^{-1} * O^{-1}
            # hence these give us the first and last row of L
            # which is exactly enough to provide the euler angles

            # multiply with rigid body transform
            if isinstance(hkbody, NifFormat.bhkRigidBodyT):
                # set rotation
                transform = mathutils.Quaternion(
                    hkbody.rotation.w, hkbody.rotation.x,
                    hkbody.rotation.y, hkbody.rotation.z).toMatrix()
                transform.resize4x4()
                # set translation
                transform[3][0] = hkbody.translation.x * 7
                transform[3][1] = hkbody.translation.y * 7
                transform[3][2] = hkbody.translation.z * 7
                # apply transform
                pivot = pivot * transform
                transform = transform.rotationPart()
                axis_z = axis_z * transform
                axis_x = axis_x * transform

            # next, cancel out bone matrix correction
            # note that B' = X * B with X = self.bones_extra_matrix[B]
            # so multiply with the inverse of X
            for niBone in self.bones_extra_matrix:
                if niBone.collision_object \
                   and niBone.collision_object.body is hkbody:
                    transform = mathutils.Matrix(
                        self.bones_extra_matrix[niBone])
                    transform.invert()
                    pivot = pivot * transform
                    transform = transform.rotationPart()
                    axis_z = axis_z * transform
                    axis_x = axis_x * transform
                    break

            # cancel out bone tail translation
            if b_hkobj.parentbonename:
                pivot[1] -= b_hkobj.parent.data.bones[
                    b_hkobj.parentbonename].length

            # cancel out object transform
            transform = mathutils.Matrix(
                b_hkobj.getMatrix('localspace'))
            transform.invert()
            pivot = pivot * transform
            transform = transform.rotationPart()
            axis_z = axis_z * transform
            axis_x = axis_x * transform

            # set pivot point
            b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVX] = pivot[0]
            b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVY] = pivot[1]
            b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVZ] = pivot[2]

            # set euler angles
            constr_matrix = mathutils.Matrix(
                axis_x,
                mathutils.CrossVecs(axis_z, axis_x),
                axis_z)
            constr_euler = constr_matrix.toEuler()
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXX] = constr_euler.x
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXY] = constr_euler.y
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXZ] = constr_euler.z
            # DEBUG
            assert((axis_x - mathutils.Vector(1,0,0) * constr_matrix).length < 0.0001)
            assert((axis_z - mathutils.Vector(0,0,1) * constr_matrix).length < 0.0001)

            # the generic rigid body type is very buggy... so for simulation
            # purposes let's transform it into ball and hinge
            if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                # ball
                b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] = 1
            elif isinstance(hkdescriptor, (NifFormat.LimitedHingeDescriptor,
                                         NifFormat.HingeDescriptor)):
                # (limited) hinge
                b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] = 2
            else:
                raise ValueError("unknown descriptor %s"
                                 % hkdescriptor.__class__.__name__)



    def import_kf_root(self, kf_root, root):
        """Merge kf into nif.

        *** Note: this function will eventually move to PyFFI. ***
        """

        self.info("Merging kf tree into nif tree")

        # check that this is an Oblivion style kf file
        if not isinstance(kf_root, NifFormat.NiControllerSequence):
            raise NifImportError("non-Oblivion .kf import not supported")

        # import text keys
        self.import_text_keys(kf_root)


        # go over all controlled blocks
        for controlledblock in kf_root.controlled_blocks:
            # get the name
            nodename = controlledblock.get_node_name()
            # match from nif tree?
            node = root.find(block_name = nodename)
            if not node:
                self.info(
                    "Animation for %s but no such node found in nif tree"
                    % nodename)
                continue
            # node found, now find the controller
            controllertype = controlledblock.get_controller_type()
            if not controllertype:
                self.info(
                    "Animation for %s without controller type, so skipping"
                    % nodename)
                continue
            controller = self.find_controller(node, getattr(NifFormat, controllertype))
            if not controller:
                self.info(
                    "Animation for %s with %s controller,"
                    " but no such controller type found"
                    " in corresponding node, so creating one"
                    % (nodename, controllertype))
                controller = getattr(NifFormat, controllertype)()
                # TODO set all the fields of this controller
                node.add_controller(controller)
            # yes! attach interpolator
            controller.interpolator = controlledblock.interpolator
            # in case of a NiTransformInterpolator without a data block
            # we still must re-export the interpolator for Oblivion to
            # accept the file
            # so simply add dummy keyframe data for this one with just a single
            # key to flag the exporter to export the keyframe as interpolator
            # (i.e. length 1 keyframes are simply interpolators)
            if isinstance(controller.interpolator,
                          NifFormat.NiTransformInterpolator) \
                and controller.interpolator.data is None:
                # create data block
                kfi = controller.interpolator
                kfi.data = NifFormat.NiTransformData()
                # fill with info from interpolator
                kfd = controller.interpolator.data
                # copy rotation
                kfd.num_rotation_keys = 1
                kfd.rotation_type = NifFormat.KeyType.LINEAR_KEY
                kfd.quaternion_keys.update_size()
                kfd.quaternion_keys[0].time = 0.0
                kfd.quaternion_keys[0].value.x = kfi.rotation.x
                kfd.quaternion_keys[0].value.y = kfi.rotation.y
                kfd.quaternion_keys[0].value.z = kfi.rotation.z
                kfd.quaternion_keys[0].value.w = kfi.rotation.w
                # copy translation
                if kfi.translation.x < -1000000:
                    # invalid, happens in fallout 3, e.g. h2haim.kf
                    self.warning("ignored NaN in interpolator translation")
                else:
                    kfd.translations.num_keys = 1
                    kfd.translations.keys.update_size()
                    kfd.translations.keys[0].time = 0.0
                    kfd.translations.keys[0].value.x = kfi.translation.x
                    kfd.translations.keys[0].value.y = kfi.translation.y
                    kfd.translations.keys[0].value.z = kfi.translation.z
                # ignore scale, usually contains invalid data in interpolator

            # save priority for future reference
            # (priorities will be stored into the name of a NULL constraint on
            # bones, see import_armature function)
            self.bone_priorities[nodename] = controlledblock.priority

        # DEBUG: save the file for manual inspection
        #niffile = open("C:\\test.nif", "wb")
        #NifFormat.write(niffile,
        #                version = 0x14000005, user_version = 11, roots = [root])

def menu_func(self, context):
    """Import operator for the menu."""
    # TODO get default path from config registry
    # default_path = bpy.data.filename.replace(".blend", ".nif")
    default_path = "import.nif"
    self.layout.operator(
        NifImport.bl_idname,
        text="NetImmerse/Gamebryo (.nif & .kf & .egm)"
        ).filepath = default_path

def register():
    """Register nif import operator."""
    bpy.types.register(NifImport)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    """Unregister nif import operator."""
    bpy.types.unregister(NifImport)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == '__main__':
    """Register nif import, when starting Blender."""
    register()
