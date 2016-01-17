#!BPY

""" 
Name: 'NetImmerse/Gamebryo (.nif & .kf & .egm)'
Blender: 245
Group: 'Import'
Tip: 'Import NIF File Format (.nif & .kf & .egm)'
"""


__author__ = "The NifTools team, http://niftools.sourceforge.net/"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__bpydoc__ = """\
This script imports Netimmerse and Gamebryo .NIF files to Blender.
"""

import Blender
from Blender.Mathutils import *

from nif_common import NifImportExport
from nif_common import NifConfig
from nif_common import NifFormat
from nif_common import EgmFormat
from nif_common import __version__

from itertools import izip
import logging
import math
import operator

import pyffi.utils.quickhull
import pyffi.spells.nif
import pyffi.spells.nif.fix

# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2011, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****
# --------------------------------------------------------------------------

class NifImportError(StandardError):
    """A simple custom exception class for import errors."""
    pass

class NifImport(NifImportExport):
    """A class which bundles the main import function along with all helper
    functions and data shared between these functions."""
    # class constants:
    # correction matrices list, the order is +X, +Y, +Z, -X, -Y, -Z
    BONE_CORRECTION_MATRICES = (
        Matrix([ 0.0,-1.0, 0.0],[ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),
        Matrix([ 1.0, 0.0, 0.0],[ 0.0, 1.0, 0.0],[ 0.0, 0.0, 1.0]),
        Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0],[ 0.0,-1.0, 0.0]),
        Matrix([ 0.0, 1.0, 0.0],[-1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),
        Matrix([-1.0, 0.0, 0.0],[ 0.0,-1.0, 0.0],[ 0.0, 0.0, 1.0]),
        Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0,-1.0],[ 0.0, 1.0, 0.0]) )
    # identity matrix, for comparisons
    IDENTITY44 = Matrix( [ 1.0, 0.0, 0.0, 0.0],
                         [ 0.0, 1.0, 0.0, 0.0],
                         [ 0.0, 0.0, 1.0, 0.0],
                         [ 0.0, 0.0, 0.0, 1.0] )
    # degrees to radians conversion constant
    D2R = 3.14159265358979/180.0
    
    def __init__(self, **config):
        """Main import function: open file and import all trees."""

        # initialize progress bar
        self.msg_progress("Initializing", progbar = 0)

        # store config settings
        for name, value in config.iteritems():
            setattr(self, name, value)

        # shortcut to import logger
        self.logger = logging.getLogger("niftools.blender.import")

        # save file name
        self.filename = self.IMPORT_FILE[:]
        self.filepath = Blender.sys.dirname(self.filename)
        self.filebase, self.fileext = Blender.sys.splitext(
            Blender.sys.basename(self.filename))
        
        # dictionary of texture files, to reuse textures
        self.textures = {}

        # dictionary of materials, to reuse materials
        self.materials = {}

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

        # Blender scene
        self.scene = Blender.Scene.GetCurrent()

        # selected objects
        # find and store this list now, as creating new objects adds them
        # to the selection list
        self.selected_objects = [ob for ob in self.scene.objects.selected]
        
        # catch NifImportError
        try:
            # check that one armature is selected in 'import geometry + parent
            # to armature' mode
            if self.IMPORT_SKELETON == 2:
                if (len(self.selected_objects) != 1
                    or self.selected_objects[0].getType() != 'Armature'):
                    raise NifImportError(
                        "You must select exactly one armature in"
                        " 'Import Geometry Only + Parent To Selected Armature'"
                        " mode.")

            # open file for binary reading
            self.logger.info("Importing %s" % self.filename)
            niffile = open(self.filename, "rb")
            data = NifFormat.Data()
            try:
                # check if nif file is valid
                data.inspect(niffile)
                self.version = data.version
                if self.version >= 0:
                    # it is valid, so read the file
                    self.logger.info("NIF file version: 0x%08X" % self.version)
                    self.msg_progress("Reading file")
                    data.read(niffile)
                    root_blocks = data.roots
                elif self.version == -1:
                    raise NifImportError("Unsupported NIF version.")
                else:
                    raise NifImportError("Not a NIF file.")
            finally:
                # the file has been read or an error occurred: close file
                niffile.close()

            if self.IMPORT_KEYFRAMEFILE:
                # open keyframe file for binary reading
                self.logger.info("Importing %s" % self.IMPORT_KEYFRAMEFILE)
                kffile = open(self.IMPORT_KEYFRAMEFILE, "rb")
                kfdata = NifFormat.Data()
                try:
                    # check if kf file is valid
                    kfdata.inspect(kffile)
                    self.kfversion = kfdata.version
                    if self.kfversion >= 0:
                        # it is valid, so read the file
                        self.logger.info(
                            "KF file version: 0x%08X" % self.kfversion)
                        self.msg_progress("Reading keyframe file")
                        kfdata.read(kffile)
                        kf_root_blocks = kfdata.roots
                    elif self.kfversion == -1:
                        raise NifImportError("Unsupported KF version.")
                    else:
                        raise NifImportError("Not a KF file.")
                finally:
                    # the file has been read or an error occurred: close file
                    kffile.close()
            else:
                kf_root_blocks = []

            if self.IMPORT_EGMFILE:
                # open facegen egm file for binary reading
                self.logger.info("Importing %s" % self.IMPORT_EGMFILE)
                egmfile = open(self.IMPORT_EGMFILE, "rb")
                self.egmdata = EgmFormat.Data()
                try:
                    # check if kf file is valid
                    self.egmdata.inspect(egmfile)
                    if self.egmdata.version >= 0:
                        # it is valid, so read the file
                        self.logger.info("EGM file version: %03i"
                                         % self.egmdata.version)
                        self.msg_progress("Reading FaceGen egm file")
                        self.egmdata.read(egmfile)
                        # scale the data
                        self.egmdata.apply_scale(self.IMPORT_SCALE_CORRECTION)
                    elif self.egmdata.version == -1:
                        raise NifImportError("Unsupported EGM version.")
                    else:
                        raise NifImportError("Not an EGM file.")
                finally:
                    # the file has been read or an error occurred: close file
                    egmfile.close()
            else:
                self.egmdata = None

            self.msg_progress("Importing data")
            # calculate and set frames per second
            if self.IMPORT_ANIMATION:
                self.fps = self.get_frames_per_second(root_blocks + kf_root_blocks)
                self.scene.getRenderingContext().fps = self.fps

            # import all root blocks
            for block in root_blocks:
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
                        if self.IMPORT_SKELETON == 1:
                            nonbip_children = (child for child in root.children
                                               if child.name[:6] != 'Bip01 ')
                            for child in nonbip_children:
                                root.remove_child(child)
                # import this root block
                self.logger.debug("Root block: %s" % root.get_global_display())
                # merge animation from kf tree into nif tree
                if self.IMPORT_ANIMATION:
                    for kf_root in kf_root_blocks:
                        self.import_kf_root(kf_root, root)
                # import the nif tree
                self.import_root(root)
        except NifImportError, e: # in that case, we raise a menu too
            self.logger.exception('NifImportError: %s' % e)
            Blender.Draw.PupMenu('ERROR%t|' + str(e))
            raise
        finally:
            # clear progress bar
            self.msg_progress("Finished", progbar = 1)
            # do a full scene update to ensure that transformations are applied
            self.scene.update(1)

        # save nif root blocks (used by test suites)
        self.root_blocks = root_blocks


    def import_root(self, root_block):
        """Main import function."""
        # preprocessing:

        # check that this is not a kf file
        if isinstance(root_block,
                      (NifFormat.NiSequence,
                       NifFormat.NiSequenceStreamHelper)):
            raise NifImportError("direct .kf import not supported")

        # divinity 2: handle CStreamableAssetData
        if isinstance(root_block, NifFormat.CStreamableAssetData):
            root_block = root_block.root

        # merge skeleton roots
        # and transform geometry into the rest pose
        # fake a data element with given root, for spells
        # TODO: use data element directly, i.e. upgrade this import_root
        #       function to an importData function
        data = NifFormat.Data()
        data.roots = [root_block]
        if self.IMPORT_MERGESKELETONROOTS:
            pyffi.spells.nif.fix.SpellMergeSkeletonRoots(data=data).recurse()
        if self.IMPORT_SENDGEOMETRIESTOBINDPOS:
            pyffi.spells.nif.fix.SpellSendGeometriesToBindPosition(data=data).recurse()
        if self.IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS:
            pyffi.spells.nif.fix.SpellSendDetachedGeometriesToNodePosition(data=data).recurse()
        if self.IMPORT_SENDBONESTOBINDPOS:
            pyffi.spells.nif.fix.SpellSendBonesToBindPosition(data=data).recurse()
        if self.IMPORT_APPLYSKINDEFORM:
            for niBlock in root_block.tree(unique=True):
                if not isinstance(niBlock, NifFormat.NiGeometry):
                    continue
                if not niBlock.is_skin():
                    continue
                self.logger.info('Applying skin deformation on geometry %s'
                                 % niBlock.name)
                vertices, normals = niBlock.get_skin_deformation()
                for vold, vnew in izip(niBlock.data.vertices, vertices):
                    vold.x = vnew.x
                    vold.y = vnew.y
                    vold.z = vnew.z
        
        # sets the root block parent to None, so that when crawling back the
        # script won't barf
        root_block._parent = None
        
        # set the block parent through the tree, to ensure I can always move
        # backward
        self.set_parents(root_block)
        
        # scale tree
        toaster = pyffi.spells.nif.NifToaster()
        toaster.scale = self.IMPORT_SCALE_CORRECTION
        pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()
        
        # mark armature nodes and bones
        self.mark_armatures_bones(root_block)
        
        # import the keyframe notes
        if self.IMPORT_ANIMATION:
            self.import_text_keys(root_block)

        # read the NIF tree
        if self.is_armature_root(root_block):
            # special case 1: root node is skeleton root
            self.logger.debug("%s is an armature root" % root_block.name)
            b_obj = self.import_branch(root_block)
        elif self.is_grouping_node(root_block):
            # special case 2: root node is grouping node
            self.logger.debug("%s is a grouping node" % root_block.name)
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
                    self.logger.warning(
                        "Unsupported collision structure under node %s"
                        % root_block.name)
                self.import_bhk_shape(bhk_body)
            # process bounding box
            for n_extra in root_block.get_extra_datas():
                if isinstance(n_extra, NifFormat.BSBound):
                    self.import_bounding_box(n_extra)
            # process all its children
            for child in root_block.children:
                b_obj = self.import_branch(child)
        elif isinstance(root_block, NifFormat.NiCamera):
            self.logger.warning('Skipped NiCamera root')
        elif isinstance(root_block, NifFormat.NiPhysXProp):
            self.logger.warning('Skipped NiPhysXProp root')
        else:
            self.logger.warning(
                "Skipped unsupported root block type '%s' (corrupted nif?)."
                % root_block.__class__)

        # store bone matrix offsets for re-export
        if self.bones_extra_matrix:
            self.store_bones_extra_matrix()

        # store original names for re-export
        if self.names:
            self.store_names()
        
        # now all havok objects are imported, so we are
        # ready to import the havok constraints
        for hkbody in self.havok_objects:
            self.import_bhk_constraints(hkbody)

        # parent selected meshes to imported skeleton
        if self.IMPORT_SKELETON == 1:
            # rename vertex groups to reflect bone names
            # (for blends imported with older versions of the scripts!)
            for b_child_obj in self.selected_objects:
                if b_child_obj.getType() == "Mesh":
                    for oldgroupname in b_child_obj.data.getVertGroupNames():
                        newgroupname = self.get_bone_name_for_blender(oldgroupname)
                        if oldgroupname != newgroupname:
                            self.logger.info(
                                "%s: renaming vertex group %s to %s"
                                % (b_child_obj, oldgroupname, newgroupname))
                            b_child_obj.data.renameVertGroup(
                                oldgroupname, newgroupname)
            # set parenting
            b_obj.makeParentDeform(self.selected_objects)


    def append_armature_modifier(self, b_obj, b_armature):
        """Append an armature modifier for the object."""
        b_mod = b_obj.modifiers.append(
            Blender.Modifier.Types.ARMATURE)
        b_mod[Blender.Modifier.Settings.OBJECT] = b_armature
        b_mod[Blender.Modifier.Settings.ENVELOPES] = False
        b_mod[Blender.Modifier.Settings.VGROUPS] = True

    def import_branch(self, niBlock, b_armature=None, n_armature=None):
        """Read the content of the current NIF tree branch to Blender
        recursively.

        @param niBlock: The nif block to import.
        @param b_armature: The blender armature for the current branch.
        @param n_armature: The corresponding nif block for the armature for
            the current branch.
        """
        self.msg_progress("Importing data")
        if not niBlock:
            return None
        elif (isinstance(niBlock, NifFormat.NiTriBasedGeom)
              and self.IMPORT_SKELETON != 1):
            # it's a shape node and we're not importing skeleton only
            # (IMPORT_SKELETON == 1)
            self.logger.debug("Building mesh in import_branch")
            # note: transform matrix is set during import
            b_obj = self.import_mesh(niBlock)
            # skinning? add armature modifier
            if niBlock.skin_instance:
                self.append_armature_modifier(b_obj, b_armature)
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
            if self.is_armature_root(niBlock):
                # all bones in the tree are also imported by
                # import_armature
                if self.IMPORT_SKELETON != 2:
                    b_obj = self.import_armature(niBlock)
                    b_armature = b_obj
                    n_armature = niBlock
                else:
                    b_obj = self.selected_objects[0]
                    b_armature = b_obj
                    n_armature = niBlock
                    self.logger.info(
                        "Merging nif tree '%s' with armature '%s'"
                        % (niBlock.name, b_obj.name))
                    if niBlock.name != b_obj.name:
                        self.logger.warning(
                            "Taking nif block '%s' as armature '%s'"
                            " but names do not match"
                            % (niBlock.name, b_obj.name))
                # armatures cannot group geometries into a single mesh
                geom_group = []
            elif self.is_bone(niBlock):
                # bones have already been imported during import_armature
                b_obj = b_armature.data.bones[self.names[niBlock]]
                # bones cannot group geometries into a single mesh
                geom_group = []
            else:
                # is it a grouping node?
                geom_group = self.is_grouping_node(niBlock)
                # if importing animation, remove children that have
                # morph controllers from geometry group
                if self.IMPORT_ANIMATION:
                    for child in geom_group:
                        if self.find_controller(
                            child, NifFormat.NiGeomMorpherController):
                            geom_group.remove(child)
                # import geometry/empty
                if (not geom_group
                    or not self.IMPORT_COMBINESHAPES
                    or len(geom_group) > 16):
                    # no grouping node, or too many materials to
                    # group the geometry into a single mesh
                    # so import it as an empty
                    if not niBlock.has_bounding_box:
                        b_obj = self.import_empty(niBlock)
                    else:
                        b_obj = self.import_bounding_box(niBlock)
                    geom_group = []
                else:
                    # node groups geometries, so import it as a mesh
                    self.logger.info(
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
                        self.append_armature_modifier(b_obj, b_armature)
                    # settings for collision node
                    if isinstance(niBlock, NifFormat.RootCollisionNode):
                        b_obj.setDrawType(
                            Blender.Object.DrawTypes['BOUNDBOX'])
                        b_obj.setDrawMode(32) # wire
                        b_obj.rbShapeBoundType = \
                            Blender.Object.RBShapes['POLYHEDERON']
                        # also remove duplicate vertices
                        b_mesh = b_obj.getData(mesh=True)
                        numverts = len(b_mesh.verts)
                        # 0.005 = 1/200
                        numdel = b_mesh.remDoubles(0.005)
                        if numdel:
                            self.logger.info(
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
                if self.isinstance_blender_object(b_child)]

            # if not importing skeleton only
            if self.IMPORT_SKELETON != 1:
                # import collision objects
                if isinstance(niBlock.collision_object,
                              NifFormat.bhkNiCollisionObject):
                    bhk_body = niBlock.collision_object.body
                    if not isinstance(bhk_body, NifFormat.bhkRigidBody):
                        self.logger.warning(
                            "Unsupported collision structure"
                            " under node %s" % niBlock.name)
                    collision_objs = self.import_bhk_shape(bhk_body)
                    # register children for parentship
                    object_children += [
                        (bhk_body, b_child) for b_child in collision_objs]
                
                # import bounding box
                if bsbound:
                    object_children += [
                        (bsbound, self.import_bounding_box(bsbound))]


            # fix parentship
            if self.isinstance_blender_object(b_obj):
                # simple object parentship
                b_obj.makeParent(
                    [b_child for (n_child, b_child) in object_children])
            elif isinstance(b_obj, Blender.Armature.Bone):
                # bone parentship, is a bit more complicated
                # go to rest position
                b_armature.data.restPosition = True
                # set up transforms
                for n_child, b_child in object_children:
                    # save transform
                    matrix = Blender.Mathutils.Matrix(
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
                    extra = Blender.Mathutils.Matrix(
                        self.bones_extra_matrix[niBlock])
                    extra.invert()
                    matrix = matrix * extra
                    # cancel out the tail translation T
                    # (the tail causes a translation along
                    # the local Y axis)
                    matrix[3][1] -= b_obj.length
                    b_child.setMatrix(matrix)
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
                for obj in self.scene.objects:
                    if obj.getType() == "Camera":
                        break
                else:
                    raise NifImportError(
                        "Scene needs camera for billboard node"
                        " (add a camera and try again)")
                # make b_obj track camera object
                #b_obj.setEuler(0,0,0)
                b_obj.constraints.append(
                    Blender.Constraint.Type.TRACKTO)
                self.logger.warning(
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
            if self.isinstance_blender_object(b_obj):
                # note: bones already have their matrix set
                b_obj.setMatrix(self.import_matrix(niBlock))

                # import the animations
                if self.IMPORT_ANIMATION:
                    self.set_animation(niBlock, b_obj)
                    # import the extras
                    self.import_text_keys(niBlock)
                    # import vis controller
                    self.import_object_vis_controller(
                        b_object=b_obj, n_node=niBlock)

            # import extra node data, such as node type
            # (other types should be added here too)
            if (isinstance(niBlock, NifFormat.NiLODNode)
                # XXX additional self.isinstance_blender_object(b_obj)
                # XXX is a 'workaround' to the limitation that bones
                # XXX cannot have properties in Blender 2.4x
                # XXX (remove this check with Blender 2.5)
                and self.isinstance_blender_object(b_obj)):
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

    def import_name(self, niBlock, max_length=22, postfix=""):
        """Get unique name for an object, preserving existing names.
        The maximum name length defaults to 22, since this is the
        maximum for Blender objects. Bone names can reach length 32.

        @param niBlock: A named nif block.
        @type niBlock: C{NiObjectNET}
        @param max_length: The maximum length of the name.
        @type max_length: C{int}
        @param postfix: Extra string to append to the name.
        @type postfix: C{str}
        """
        if niBlock in self.names:
            if not postfix:
                return self.names[niBlock]
            else:
                # force postfix!
                # the same block may be imported with different postfixes
                if self.names[niBlock].endswith(postfix):
                    return self.names[niBlock]

        self.logger.debug(
            "Importing name for %s block from %s%s"
            % (niBlock.__class__.__name__, niBlock.name, postfix))

        # find unique name for Blender to use
        uniqueInt = 0
        # strip null terminator from name
        niBlock.name = niBlock.name.strip("\x00")
        niName = niBlock.name
        # if name is empty, create something non-empty
        if not niName:
            if isinstance(niBlock, NifFormat.RootCollisionNode):
                niName = "collision"
            else:
                niName = "noname"
        for uniqueInt in xrange(-1, 100):
            # limit name length
            if uniqueInt == -1:
                if max_length - len(postfix) - 1 <= 0:
                    raise ValueError("Name postfix '%s' too long." % postfix)
                shortName = niName[:max_length-len(postfix)-1] + postfix
            else:
                if max_length - len(postfix) - 4 <= 0:
                    raise ValueError("Name postfix '%s' too long." % postfix)
                shortName = ('%s.%02d%s' 
                             % (niName[:max_length-len(postfix)-4],
                                uniqueInt,
                                postfix))
            # bone naming convention for blender
            shortName = self.get_bone_name_for_blender(shortName)
            # make sure it is unique
            try:
                Blender.Object.Get(shortName)
            except ValueError:
                # short name not found in object list
                pass
            else:
                # try another integer
                continue
            try:
                Blender.Material.Get(shortName)
            except NameError:
                # short name not found in material list
                break
        else:
            raise RuntimeError("Ran out of names.")
        # save mapping
        # block niBlock has Blender name shortName
        self.names[niBlock] = shortName
        # Blender name shortName corresponds to niBlock
        self.blocks[shortName] = niBlock
        self.logger.debug("Selected unique name %s" % shortName)
        return shortName
        
    def import_matrix(self, niBlock, relative_to=None):
        """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
        return Matrix(*niBlock.get_transform(relative_to).as_list())

    def decompose_srt(self, m):
        """Decompose Blender transform matrix as a scale, rotation matrix, and
        translation vector."""
        # get scale components
        b_scale_rot = m.rotationPart()
        b_scale_rot_T = Matrix(b_scale_rot)
        b_scale_rot_T.transpose()
        b_scale_rot_2 = b_scale_rot * b_scale_rot_T
        b_scale = Vector(b_scale_rot_2[0][0] ** 0.5,\
                         b_scale_rot_2[1][1] ** 0.5,\
                         b_scale_rot_2[2][2] ** 0.5)
        # and fix their sign
        if (b_scale_rot.determinant() < 0): b_scale.negate()
        # only uniform scaling
        if (abs(b_scale[0]-b_scale[1]) >= self.EPSILON
            or abs(b_scale[1]-b_scale[2]) >= self.EPSILON):
            self.logger.warn(
                "Corrupt rotation matrix in nif: geometry errors may result.")
        b_scale = b_scale[0]
        # get rotation matrix
        b_rot = b_scale_rot * (1.0/b_scale)
        # get translation
        b_trans = m.translationPart()
        # done!
        return b_scale, b_rot, b_trans

    def import_empty(self, niBlock):
        """Creates and returns a grouping empty."""
        shortName = self.import_name(niBlock)
        b_empty = self.scene.objects.new("Empty", shortName)
        b_empty.properties['longName'] = niBlock.name
        if niBlock.name in self.bone_priorities:
            constr = b_empty.constraints.append(
                Blender.Constraint.Type.NULL)
            constr.name = "priority:%i" % self.bone_priorities[niBlock.name]  
        return b_empty

    def import_armature(self, niArmature):
        """Scans an armature hierarchy, and returns a whole armature.
        This is done outside the normal node tree scan to allow for positioning
        of the bones before skins are attached."""
        armature_name = self.import_name(niArmature)

        b_armatureData = Blender.Armature.Armature()
        b_armatureData.name = armature_name
        b_armatureData.drawAxes = True
        b_armatureData.envelopes = False
        b_armatureData.vertexGroups = True
        b_armatureData.drawType = Blender.Armature.STICK
        b_armature = self.scene.objects.new(b_armatureData, armature_name)

        # make armature editable and create bones
        b_armatureData.makeEditable()
        niChildBones = [child for child in niArmature.children
                        if self.is_bone(child)]
        for niBone in niChildBones:
            self.import_bone(
                niBone, b_armature, b_armatureData, niArmature)
        b_armatureData.update()

        # The armature has been created in editmode,
        # now we are ready to set the bone keyframes.
        if self.IMPORT_ANIMATION:
            # create an action
            action = Blender.Armature.NLA.NewAction()
            action.setActive(b_armature)
            # go through all armature pose bones
            # see http://www.elysiun.com/forum/viewtopic.php?t=58693
            self.msg_progress('Importing Animations')
            for bone_name, b_posebone in b_armature.getPose().bones.items():
                # denote progress
                self.msg_progress('Animation: %s' % bone_name)
                self.logger.debug(
                    'Importing animation for bone %s' % bone_name)
                niBone = self.blocks[bone_name]

                # get bind matrix (NIF format stores full transformations in keyframes,
                # but Blender wants relative transformations, hence we need to know
                # the bind position for conversion). Since
                # [ SRchannel 0 ]    [ SRbind 0 ]   [ SRchannel * SRbind         0 ]   [ SRtotal 0 ]
                # [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel  * SRbind + Tbind 1 ] = [ Ttotal  1 ]
                # with
                # 'total' the transformations as stored in the NIF keyframes,
                # 'bind' the Blender bind pose, and
                # 'channel' the Blender IPO channel,
                # it follows that
                # Schannel = Stotal / Sbind
                # Rchannel = Rtotal * inverse(Rbind)
                # Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                bone_bm = self.import_matrix(niBone) # base pose
                niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = self.decompose_srt(bone_bm)
                niBone_bind_rot_inv = Matrix(niBone_bind_rot)
                niBone_bind_rot_inv.invert()
                niBone_bind_quat_inv = niBone_bind_rot_inv.toQuat()
                # we also need the conversion of the original matrix to the
                # new bone matrix, say X,
                # B' = X * B
                # (with B' the Blender matrix and B the NIF matrix) because we
                # need that
                # C' * B' = X * C * B
                # and therefore
                # C' = X * C * B * inverse(B') = X * C * inverse(X),
                # where X = B' * inverse(B)
                #
                # In detail:
                # [ SRX 0 ]   [ SRC 0 ]            [ SRX 0 ]
                # [ TX  1 ] * [ TC  1 ] * inverse( [ TX  1 ] ) =
                # [ SRX * SRC       0 ]   [ inverse(SRX)         0 ]
                # [ TX * SRC + TC   1 ] * [ -TX * inverse(SRX)   1 ] =
                # [ SRX * SRC * inverse(SRX)              0 ]
                # [ (TX * SRC + TC - TX) * inverse(SRX)   1 ]
                # Hence
                # SC' = SX * SC / SX = SC
                # RC' = RX * RC * inverse(RX)
                # TC' = (TX * SC * RC + TC - TX) * inverse(RX) / SX
                extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = self.decompose_srt(self.bones_extra_matrix[niBone])
                extra_matrix_quat = extra_matrix_rot.toQuat()
                extra_matrix_rot_inv = Matrix(extra_matrix_rot)
                extra_matrix_rot_inv.invert()
                extra_matrix_quat_inv = extra_matrix_rot_inv.toQuat()
                # now import everything
                # ##############################

                # get controller, interpolator, and data
                # note: the NiKeyframeController check also includes
                #       NiTransformController (see hierarchy!)
                kfc = self.find_controller(niBone,
                                           NifFormat.NiKeyframeController)
                # old style: data directly on controller
                kfd = kfc.data if kfc else None
                # new style: data via interpolator
                kfi = kfc.interpolator if kfc else None
                # next is a quick hack to make the new transform
                # interpolator work as if it is an old style keyframe data
                # block parented directly on the controller
                if isinstance(kfi, NifFormat.NiTransformInterpolator):
                    kfd = kfi.data
                    # for now, in this case, ignore interpolator
                    kfi = None

                # B-spline curve import
                if isinstance(kfi, NifFormat.NiBSplineInterpolator):
                    times = list(kfi.get_times())
                    translations = list(kfi.get_translations())
                    scales = list(kfi.get_scales())
                    rotations = list(kfi.get_rotations())

                    # if we have translation keys, we make a dictionary of
                    # rot_keys and scale_keys, this makes the script work MUCH
                    # faster in most cases
                    if translations:
                        scale_keys_dict = {}
                        rot_keys_dict = {}

                    # scales: ignore for now, implement later
                    #         should come here
                    scales = None

                    # rotations
                    if rotations:
                        self.logger.debug(
                            'Rotation keys...(bspline quaternions)')
                        for time, quat in izip(times, rotations):
                            frame = 1 + int(time * self.fps + 0.5)
                            quat = Blender.Mathutils.Quaternion(
                                [quat[0], quat[1], quat[2],  quat[3]])
                            # beware, CrossQuats takes arguments in a
                            # counter-intuitive order:
                            # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                            quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
                            rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                            b_posebone.quat = rot
                            b_posebone.insertKey(b_armature, frame,
                                                 [Blender.Object.Pose.ROT])
                            # fill optimizer dictionary
                            if translations:
                                rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot)

                    # translations
                    if translations:
                        self.logger.debug('Translation keys...(bspline)')
                        for time, translation in izip(times, translations):
                            # time 0.0 is frame 1
                            frame = 1 + int(time * self.fps + 0.5)
                            trans = Blender.Mathutils.Vector(*translation)
                            locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0/niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                            # the rotation matrix is needed at this frame (that's
                            # why the other keys are inserted first)
                            if rot_keys_dict:
                                try:
                                    rot = rot_keys_dict[frame].toMatrix()
                                except KeyError:
                                    # fall back on slow method
                                    ipo = action.getChannelIpo(bone_name)
                                    quat = Blender.Mathutils.Quaternion()
                                    quat.x = ipo.getCurve('QuatX').evaluate(frame)
                                    quat.y = ipo.getCurve('QuatY').evaluate(frame)
                                    quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                                    quat.w = ipo.getCurve('QuatW').evaluate(frame)
                                    rot = quat.toMatrix()
                            else:
                                rot = Blender.Mathutils.Matrix([1.0,0.0,0.0],
                                                               [0.0,1.0,0.0],
                                                               [0.0,0.0,1.0])
                            # we also need the scale at this frame
                            if scale_keys_dict:
                                try:
                                    sizeVal = scale_keys_dict[frame]
                                except KeyError:
                                    ipo = action.getChannelIpo(bone_name)
                                    if ipo.getCurve('SizeX'):
                                        sizeVal = ipo.getCurve('SizeX').evaluate(frame) # assume uniform scale
                                    else:
                                        sizeVal = 1.0
                            else:
                                sizeVal = 1.0
                            size = Blender.Mathutils.Matrix([sizeVal, 0.0, 0.0],
                                                            [0.0, sizeVal, 0.0],
                                                            [0.0, 0.0, sizeVal])
                            # now we can do the final calculation
                            loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0/extra_matrix_scale) # C' = X * C * inverse(X)
                            b_posebone.loc = loc
                            b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])

                    # delete temporary dictionaries
                    if translations:
                        del scale_keys_dict
                        del rot_keys_dict

                # NiKeyframeData and NiTransformData import
                elif isinstance(kfd, NifFormat.NiKeyframeData):

                    translations = kfd.translations
                    scales = kfd.scales
                    # if we have translation keys, we make a dictionary of
                    # rot_keys and scale_keys, this makes the script work MUCH
                    # faster in most cases
                    if translations:
                        scale_keys_dict = {}
                        rot_keys_dict = {}
                    # add the keys

                    # Scaling
                    if scales.keys:
                        self.logger.debug('Scale keys...')
                    for scaleKey in scales.keys:
                        # time 0.0 is frame 1
                        frame = 1 + int(scaleKey.time * self.fps + 0.5)
                        sizeVal = scaleKey.value
                        size = sizeVal / niBone_bind_scale # Schannel = Stotal / Sbind
                        b_posebone.size = Blender.Mathutils.Vector(size, size, size)
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE]) # this is very slow... :(
                        # fill optimizer dictionary
                        if translations:
                            scale_keys_dict[frame] = size

                    # detect the type of rotation keys
                    rotation_type = kfd.rotation_type

                    # Euler Rotations
                    if rotation_type == 4:
                        # uses xyz rotation
                        if kfd.xyz_rotations[0].keys:
                            self.logger.debug('Rotation keys...(euler)')
                        for xkey, ykey, zkey in izip(kfd.xyz_rotations[0].keys,
                                                     kfd.xyz_rotations[1].keys,
                                                     kfd.xyz_rotations[2].keys):
                            # time 0.0 is frame 1
                            # XXX it is assumed that all the keys have the
                            # XXX same times!!!
                            if (abs(xkey.time - ykey.time) > self.EPSILON
                                or abs(xkey.time - zkey.time) > self.EPSILON):
                                self.logger.warn(
                                    "xyz key times do not correspond, "
                                    "animation may not be correctly imported")
                            frame = 1 + int(xkey.time * self.fps + 0.5)
                            euler = Blender.Mathutils.Euler(
                                [xkey.value*180.0/math.pi,
                                 ykey.value*180.0/math.pi,
                                 zkey.value*180.0/math.pi])
                            quat = euler.toQuat()

                            # beware, CrossQuats takes arguments in a counter-intuitive order:
                            # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()

                            quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
                            rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                            b_posebone.quat = rot
                            b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
                            # fill optimizer dictionary
                            if translations:
                                rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot) 

                    # Quaternion Rotations
                    else:
                        # TODO take rotation type into account for interpolation
                        if kfd.quaternion_keys:
                            self.logger.debug('Rotation keys...(quaternions)')
                        quaternion_keys = kfd.quaternion_keys
                        for key in quaternion_keys:
                            frame = 1 + int(key.time * self.fps + 0.5)
                            keyVal = key.value
                            quat = Blender.Mathutils.Quaternion([keyVal.w, keyVal.x, keyVal.y,  keyVal.z])
                            # beware, CrossQuats takes arguments in a
                            # counter-intuitive order:
                            # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                            quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
                            rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                            b_posebone.quat = rot
                            b_posebone.insertKey(b_armature, frame,
                                                 [Blender.Object.Pose.ROT])
                            # fill optimizer dictionary
                            if translations:
                                rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot)
#                    else:
#                        print("""Rotation keys...(unknown)
#WARNING: rotation animation data of type %i found, but this type is not yet
#         supported; data has been skipped""" % rotation_type)                        
        
                    # Translations
                    if translations.keys:
                        self.logger.debug('Translation keys...')
                    for key in translations.keys:
                        # time 0.0 is frame 1
                        frame = 1 + int(key.time * self.fps + 0.5)
                        keyVal = key.value
                        trans = Blender.Mathutils.Vector(keyVal.x, keyVal.y, keyVal.z)
                        locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0/niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                        # the rotation matrix is needed at this frame (that's
                        # why the other keys are inserted first)
                        if rot_keys_dict:
                            try:
                                rot = rot_keys_dict[frame].toMatrix()
                            except KeyError:
                                # fall back on slow method
                                ipo = action.getChannelIpo(bone_name)
                                quat = Blender.Mathutils.Quaternion()
                                quat.x = ipo.getCurve('QuatX').evaluate(frame)
                                quat.y = ipo.getCurve('QuatY').evaluate(frame)
                                quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                                quat.w = ipo.getCurve('QuatW').evaluate(frame)
                                rot = quat.toMatrix()
                        else:
                            rot = Blender.Mathutils.Matrix([1.0,0.0,0.0],
                                                           [0.0,1.0,0.0],
                                                           [0.0,0.0,1.0])
                        # we also need the scale at this frame
                        if scale_keys_dict:
                            try:
                                sizeVal = scale_keys_dict[frame]
                            except KeyError:
                                ipo = action.getChannelIpo(bone_name)
                                if ipo.getCurve('SizeX'):
                                    sizeVal = ipo.getCurve('SizeX').evaluate(frame) # assume uniform scale
                                else:
                                    sizeVal = 1.0
                        else:
                            sizeVal = 1.0
                        size = Blender.Mathutils.Matrix([sizeVal, 0.0, 0.0],
                                                        [0.0, sizeVal, 0.0],
                                                        [0.0, 0.0, sizeVal])
                        # now we can do the final calculation
                        loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0/extra_matrix_scale) # C' = X * C * inverse(X)
                        b_posebone.loc = loc
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
                    if translations:
                        del scale_keys_dict
                        del rot_keys_dict
                # set extend mode for all ipo curves
                if kfc:
                    try:
                        ipo = action.getChannelIpo(bone_name)
                    except ValueError:
                        # no channel for bone_name
                        pass
                    else:
                        for b_curve in ipo:
                            b_curve.extend = self.get_extend_from_flags(kfc.flags)

        # constraints (priority)
        # must be done outside edit mode hence after calling
        for bone_name, b_posebone in b_armature.getPose().bones.items():
            # find bone nif block
            niBone = self.blocks[bone_name]
            # store bone priority, if applicable
            if niBone.name in self.bone_priorities:
                constr = b_posebone.constraints.append(
                    Blender.Constraint.Type.NULL)
                constr.name = "priority:%i" % self.bone_priorities[niBone.name]

        return b_armature

    def import_bone(self, niBlock, b_armature, b_armatureData, niArmature):
        """Adds a bone to the armature in edit mode."""
        # check that niBlock is indeed a bone
        if not self.is_bone(niBlock):
            return None

        # bone length for nubs and zero length bones
        nub_length = 5.0
        scale = self.IMPORT_SCALE_CORRECTION
        # bone name
        bone_name = self.import_name(niBlock, 32)
        niChildBones = [ child for child in niBlock.children
                         if self.is_bone(child) ]
        # create a new bone
        b_bone = Blender.Armature.Editbone()
        # head: get position from niBlock
        armature_space_matrix = self.import_matrix(niBlock,
                                                   relative_to=niArmature)

        b_bone_head_x = armature_space_matrix[3][0]
        b_bone_head_y = armature_space_matrix[3][1]
        b_bone_head_z = armature_space_matrix[3][2]
        # temporarily sets the tail as for a 0 length bone
        b_bone_tail_x = b_bone_head_x
        b_bone_tail_y = b_bone_head_y
        b_bone_tail_z = b_bone_head_z
        is_zero_length = True
        # tail: average of children location
        if len(niChildBones) > 0:
            m_correction = self.find_correction_matrix(niBlock, niArmature)
            child_matrices = [ self.import_matrix(child,
                                                  relative_to=niArmature)
                               for child in niChildBones ]
            b_bone_tail_x = sum(child_matrix[3][0]
                                for child_matrix
                                in child_matrices) / len(child_matrices)
            b_bone_tail_y = sum(child_matrix[3][1]
                                for child_matrix
                                in child_matrices) / len(child_matrices)
            b_bone_tail_z = sum(child_matrix[3][2]
                                for child_matrix
                                in child_matrices) / len(child_matrices)
            # checking bone length
            dx = b_bone_head_x - b_bone_tail_x
            dy = b_bone_head_y - b_bone_tail_y
            dz = b_bone_head_z - b_bone_tail_z
            is_zero_length = abs(dx + dy + dz) * 200 < self.EPSILON
        elif self.IMPORT_REALIGN_BONES == 2:
            # The correction matrix value is based on the childrens' head
            # positions.
            # If there are no children then set it as the same as the
            # parent's correction matrix.
            m_correction = self.find_correction_matrix(niBlock._parent,
                                                       niArmature)
        
        if is_zero_length:
            # this is a 0 length bone, to avoid it being removed
            # set a default minimum length
            if (self.IMPORT_REALIGN_BONES == 2) \
               or not self.is_bone(niBlock._parent):
                # no parent bone, or bone is realigned with correction
                # set one random direction
                b_bone_tail_x = b_bone_head_x + (nub_length * scale)
            else:
                # to keep things neat if bones aren't realigned on import
                # orient it as the vector between this
                # bone's head and the parent's tail
                parent_tail = b_armatureData.bones[
                    self.names[niBlock._parent]].tail
                dx = b_bone_head_x - parent_tail[0]
                dy = b_bone_head_y - parent_tail[1]
                dz = b_bone_head_z - parent_tail[2]
                if abs(dx + dy + dz) * 200 < self.EPSILON:
                    # no offset from the parent: follow the parent's
                    # orientation
                    parent_head = b_armatureData.bones[
                        self.names[niBlock._parent]].head
                    dx = parent_tail[0] - parent_head[0]
                    dy = parent_tail[1] - parent_head[1]
                    dz = parent_tail[2] - parent_head[2]
                direction = Vector(dx, dy, dz)
                direction.normalize()
                b_bone_tail_x = b_bone_head_x + (direction[0] * nub_length * scale)
                b_bone_tail_y = b_bone_head_y + (direction[1] * nub_length * scale)
                b_bone_tail_z = b_bone_head_z + (direction[2] * nub_length * scale)
                
        # sets the bone heads & tails
        b_bone.head = Vector(b_bone_head_x, b_bone_head_y, b_bone_head_z)
        b_bone.tail = Vector(b_bone_tail_x, b_bone_tail_y, b_bone_tail_z)
        
        if self.IMPORT_REALIGN_BONES == 2:
            # applies the corrected matrix explicitly
            b_bone.matrix = m_correction.resize4x4() * armature_space_matrix
        elif self.IMPORT_REALIGN_BONES == 1:
            # do not do anything, keep unit matrix
            pass
        else:
            # no realign, so use original matrix
            b_bone.matrix = armature_space_matrix

        # set bone name and store the niBlock for future reference
        b_armatureData.bones[bone_name] = b_bone
        # calculate bone difference matrix; we will need this when
        # importing animation
        old_bone_matrix_inv = Blender.Mathutils.Matrix(armature_space_matrix)
        old_bone_matrix_inv.invert()
        new_bone_matrix = Blender.Mathutils.Matrix(b_bone.matrix)
        new_bone_matrix.resize4x4()
        new_bone_matrix[3][0] = b_bone_head_x
        new_bone_matrix[3][1] = b_bone_head_y
        new_bone_matrix[3][2] = b_bone_head_z
        # stores any correction or alteration applied to the bone matrix
        # new * inverse(old)
        self.bones_extra_matrix[niBlock] = new_bone_matrix * old_bone_matrix_inv
        # set bone children
        for niBone in niChildBones:
            b_child_bone =  self.import_bone(
                niBone, b_armature, b_armatureData, niArmature)
            b_child_bone.parent = b_bone

        return b_bone

    def find_correction_matrix(self, niBlock, niArmature):
        """Returns the correction matrix for a bone."""
        m_correction = self.IDENTITY44.rotationPart()
        if (self.IMPORT_REALIGN_BONES == 2) and self.is_bone(niBlock):
            armature_space_matrix = self.import_matrix(niBlock,
                                                       relative_to=niArmature)

            niChildBones = [ child for child in niBlock.children
                             if self.is_bone(child) ]
            (sum_x, sum_y, sum_z, dummy) = armature_space_matrix[3]
            if len(niChildBones) > 0:
                child_local_matrices = [ self.import_matrix(child)
                                         for child in niChildBones ]
                sum_x = sum(cm[3][0] for cm in child_local_matrices)
                sum_y = sum(cm[3][1] for cm in child_local_matrices)
                sum_z = sum(cm[3][2] for cm in child_local_matrices)
            list_xyz = [ int(c * 200)
                         for c in (sum_x, sum_y, sum_z,
                                   -sum_x, -sum_y, -sum_z) ]
            idx_correction = list_xyz.index(max(list_xyz))
            alignment_offset = 0.0
            if (idx_correction == 0 or idx_correction == 3) and abs(sum_x) > 0:
                alignment_offset = float(abs(sum_y) + abs(sum_z)) / abs(sum_x)
            elif (idx_correction == 1 or idx_correction == 4) and abs(sum_y) > 0:
                alignment_offset = float(abs(sum_z) + abs(sum_x)) / abs(sum_y)
            elif abs(sum_z) > 0:
                alignment_offset = float(abs(sum_x) + abs(sum_y)) / abs(sum_z)
            # if alignment is good enough, use the (corrected) NIF matrix
            # this gives nice ortogonal matrices
            if alignment_offset < 0.25:
                m_correction = self.BONE_CORRECTION_MATRICES[idx_correction]
        return m_correction


    def get_texture_hash(self, source):
        """Helper function for import_texture. Returns a key that uniquely
        identifies a texture from its source (which is either a
        NiSourceTexture block, or simply a path string).
        """
        if not source:
            return None
        elif isinstance(source, NifFormat.NiSourceTexture):
            return source.get_hash()
        elif isinstance(source, basestring):
            return source.lower()
        else:
            raise TypeError("source must be NiSourceTexture block or string")

    def import_texture(self, source):
        """Convert a NiSourceTexture block, or simply a path string,
        to a Blender Texture object, return the Texture object and
        stores it in the self.textures dictionary to avoid future
        duplicate imports.
        """

        # if the source block is not linked then return None
        if not source:
            return None

        # calculate the texture hash key
        texture_hash = self.get_texture_hash(source)

        try:
            # look up the texture in the dictionary of imported textures
            # and return it if found
            return self.textures[texture_hash]
        except KeyError:
            pass

        b_image = None
        
        if (isinstance(source, NifFormat.NiSourceTexture)
            and not source.use_external):
            # find a file name (but avoid overwriting)
            n = 0
            while True:
                fn = "image%03i.dds" % n
                tex = Blender.sys.join(Blender.sys.dirname(self.IMPORT_FILE),
                                       fn)
                if not Blender.sys.exists(tex):
                    break
                n += 1
            if self.IMPORT_EXPORTEMBEDDEDTEXTURES:
                # save embedded texture as dds file
                stream = open(tex, "wb")
                try:
                    self.logger.info("Saving embedded texture as %s" % tex)
                    source.pixel_data.save_as_dds(stream)
                except ValueError:
                    # value error means that the pixel format is not supported
                    b_image = None
                else:
                    # saving dds succeeded so load the file
                    b_image = Blender.Image.Load(tex)
                    # Blender will return an image object even if the
                    # file format is not supported,
                    # so to check if the image is actually loaded an error
                    # is forced via "b_image.size"
                    try:
                        b_image.size
                    except: # RuntimeError: couldn't load image data in Blender
                        b_image = None # not supported, delete image object
                finally:
                    stream.close()
            else:
                b_image = None
        else:
            # the texture uses an external image file
            if isinstance(source, NifFormat.NiSourceTexture):
                fn = source.file_name
            elif isinstance(source, basestring):
                fn = source
            else:
                raise TypeError(
                    "source must be NiSourceTexture block or string")
            fn = fn.replace( '\\', Blender.sys.sep )
            fn = fn.replace( '/', Blender.sys.sep )
            # go searching for it
            importpath = Blender.sys.dirname(self.IMPORT_FILE)
            searchPathList = (
                [importpath]
                + self.IMPORT_TEXTURE_PATH)
            if Blender.Get("texturesdir"):
                searchPathList += [
                    Blender.sys.dirname(Blender.Get("texturesdir"))]
            # if it looks like a Morrowind style path, use common sense to
            # guess texture path
            meshes_index = importpath.lower().find("meshes")
            if meshes_index != -1:
                searchPathList.append(importpath[:meshes_index] + 'textures')
            # if it looks like a Civilization IV style path, use common sense
            # to guess texture path
            art_index = importpath.lower().find("art")
            if art_index != -1:
                searchPathList.append(importpath[:art_index] + 'shared')
            # go through all texture search paths
            for texdir in searchPathList:
                texdir = texdir.replace( '\\', Blender.sys.sep )
                texdir = texdir.replace( '/', Blender.sys.sep )
                # go through all possible file names, try alternate extensions
                # too; for linux, also try lower case versions of filenames
                texfns = reduce(operator.add,
                                [ [ fn[:-4]+ext, fn[:-4].lower()+ext ]
                                  for ext in ('.DDS','.dds','.PNG','.png',
                                             '.TGA','.tga','.BMP','.bmp',
                                             '.JPG','.jpg') ] )
                texfns = [fn, fn.lower()] + list(set(texfns))
                for texfn in texfns:
                     # now a little trick, to satisfy many Morrowind mods
                    if (texfn[:9].lower() == 'textures' + Blender.sys.sep) \
                       and (texdir[-9:].lower() == Blender.sys.sep + 'textures'):
                        # strip one of the two 'textures' from the path
                        tex = Blender.sys.join( texdir[:-9], texfn )
                    else:
                        tex = Blender.sys.join( texdir, texfn )
                    self.logger.debug("Searching %s" % tex)
                    if Blender.sys.exists(tex) == 1:
                        # tries to load the file
                        b_image = Blender.Image.Load(tex)
                        # Blender will return an image object even if the
                        # file format is not supported,
                        # so to check if the image is actually loaded an error
                        # is forced via "b_image.size"
                        try:
                            b_image.size
                        except: # RuntimeError: couldn't load image data in Blender
                            b_image = None # not supported, delete image object
                        else:
                            # file format is supported
                            self.logger.debug("Found '%s' at %s" % (fn, tex))
                            break
                if b_image:
                    break
            else:
                tex = Blender.sys.join(searchPathList[0], fn)

        # create a stub image if the image could not be loaded
        if not b_image:
            self.logger.warning(
                "Texture '%s' not found or not supported"
                " and no alternate available"
                % fn)
            b_image = Blender.Image.New(fn, 1, 1, 24) # create a stub
            b_image.filename = tex

        # create a texture
        b_texture = Blender.Texture.New()
        b_texture.setType('Image')
        b_texture.setImage(b_image)
        b_texture.imageFlags |= Blender.Texture.ImageFlags.INTERPOL
        b_texture.imageFlags |= Blender.Texture.ImageFlags.MIPMAP

        # save texture to avoid duplicate imports, and return it
        self.textures[texture_hash] = b_texture
        return b_texture

    def get_material_hash(self, matProperty, textProperty,
                          alphaProperty, specProperty,
                          textureEffect, wireProperty,
                          bsShaderProperty, extra_datas):
        """Helper function for import_material. Returns a key that
        uniquely identifies a material from its properties. The key
        ignores the material name as that does not affect the
        rendering.
        """
        return (matProperty.get_hash()[1:] # skip first element, which is name
                if matProperty else None,
                textProperty.get_hash()     if textProperty  else None,
                alphaProperty.get_hash()    if alphaProperty else None,
                specProperty.get_hash()     if specProperty  else None,
                textureEffect.get_hash()    if textureEffect else None,
                wireProperty.get_hash()     if wireProperty  else None,
                bsShaderProperty.get_hash() if bsShaderProperty else None,
                tuple(extra.get_hash() for extra in extra_datas))

    def import_material(self, matProperty, textProperty,
                        alphaProperty, specProperty,
                        textureEffect, wireProperty,
                        bsShaderProperty, extra_datas):
        """Creates and returns a material."""
        # First check if material has been created before.
        material_hash = self.get_material_hash(matProperty, textProperty,
                                               alphaProperty, specProperty,
                                               textureEffect, wireProperty,
                                               bsShaderProperty,
                                               extra_datas)
        try:
            return self.materials[material_hash]                
        except KeyError:
            pass
        # use the material property for the name, other properties usually have
        # no name
        name = self.import_name(matProperty)
        material = Blender.Material.New(name)
        # get apply mode, and convert to blender "blending mode"
        blendmode = Blender.Texture.BlendModes["MIX"] # default
        if textProperty:
            if textProperty.apply_mode == NifFormat.ApplyMode.APPLY_MODULATE:
                blendmode = Blender.Texture.BlendModes["MIX"]
            elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_REPLACE:
                blendmode = Blender.Texture.BlendModes["MIX"]
            elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_DECAL:
                blendmode = Blender.Texture.BlendModes["MIX"]
            elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT:
                blendmode = Blender.Texture.BlendModes["LIGHTEN"]
            elif textProperty.apply_mode == NifFormat.ApplyMode.APPLY_HILIGHT2:
                blendmode = Blender.Texture.BlendModes["MULTIPLY"]
            else:
                self.logger.warning(
                    "Unknown apply mode (%i) in material '%s',"
                    " using blending mode 'MIX'"
                    % (textProperty.apply_mode, matProperty.name))
        elif bsShaderProperty:
            # default blending mode for fallout 3
            blendmode = Blender.Texture.BlendModes["MIX"]
        # Sets the colors
        # Specular color
        spec = matProperty.specular_color
        material.setSpecCol([spec.r, spec.g, spec.b])
        # Blender multiplies specular color with this value
        material.setSpec(1.0)
        # Diffuse color
        diff = matProperty.diffuse_color
        emit = matProperty.emissive_color
        # fallout 3 hack: convert diffuse black to emit if emit is not black
        if diff.r < self.EPSILON and diff.g < self.EPSILON and diff.b < self.EPSILON:
            if (emit.r + emit.g + emit.b) < self.EPSILON:
                # emit is black... set diffuse color to white
                diff.r = 1.0
                diff.g = 1.0
                diff.b = 1.0
            else:
                diff.r = emit.r
                diff.g = emit.g
                diff.b = emit.b
        material.setRGBCol(diff.r, diff.g, diff.b)
        # Ambient & emissive color
        # We assume that ambient & emissive are fractions of the diffuse color.
        # If it is not an exact fraction, we average out.
        amb = matProperty.ambient_color
        # fallout 3 hack:convert ambient black to white and set emit
        if amb.r < self.EPSILON and amb.g < self.EPSILON and amb.b < self.EPSILON:
            amb.r = 1.0
            amb.g = 1.0
            amb.b = 1.0
            b_amb = 1.0
            if (emit.r + emit.g + emit.b) < self.EPSILON:
                b_emit = 0.0
            else:
                b_emit = matProperty.emit_multi / 10.0
        else:
            b_amb = 0.0
            b_emit = 0.0
            b_n = 0
            if diff.r > self.EPSILON:
                b_amb += amb.r/diff.r
                b_emit += emit.r/diff.r
                b_n += 1
            if diff.g > self.EPSILON:
                b_amb += amb.g/diff.g
                b_emit += emit.g/diff.g
                b_n += 1
            if diff.b > self.EPSILON:
                b_amb += amb.b/diff.b
                b_emit += emit.b/diff.b
                b_n += 1
            if b_n > 0:
                b_amb /= b_n
                b_emit /= b_n
        if b_amb > 1.0:
            b_amb = 1.0
        if b_emit > 1.0:
            b_emit = 1.0
        material.setAmb(b_amb)
        material.setEmit(b_emit)
        # glossiness
        glossiness = matProperty.glossiness
        hardness = int(glossiness * 4) # just guessing really
        if hardness < 1: hardness = 1
        if hardness > 511: hardness = 511
        material.setHardness(hardness)
        # Alpha
        alpha = matProperty.alpha
        material.setAlpha(alpha)
        # textures
        base_texture = None
        glow_texture = None
        envmapTexture = None # for NiTextureEffect
        bumpTexture = None
        dark_texture = None
        detail_texture = None
        refTexture = None
        if textProperty:
            # standard texture slots
            baseTexDesc = textProperty.base_texture
            glowTexDesc = textProperty.glow_texture
            bumpTexDesc = textProperty.bump_map_texture
            glossTexDesc = textProperty.gloss_texture
            darkTexDesc = textProperty.dark_texture
            detailTexDesc = textProperty.detail_texture
            refTexDesc = None
            # extra texture shader slots
            for shader_tex_desc in textProperty.shader_textures:
                if not shader_tex_desc.is_used:
                    continue
                # it is used, figure out the slot it is used for
                for extra in extra_datas:
                    if extra.integer_data == shader_tex_desc.map_index:
                        # found!
                        shader_name = extra.name
                        break
                else:
                    # none found
                    self.logger.warn(
                        "No slot for shader texture %s."
                        % shader_tex_desc.texture_data.source.file_name)
                    continue
                try:
                    extra_shader_index = (
                        self.EXTRA_SHADER_TEXTURES.index(shader_name))
                except ValueError:
                    # shader_name not in self.EXTRA_SHADER_TEXTURES
                    self.logger.warn(
                        "No slot for shader texture %s."
                        % shader_tex_desc.texture_data.source.file_name)
                    continue
                if extra_shader_index == 0:
                    # EnvironmentMapIndex
                    if shader_tex_desc.texture_data.source.file_name.lower().startswith("rrt_engine_env_map"):
                        # sid meier's railroads: env map generated by engine
                        # we can skip this
                        continue
                    # XXX todo, civ4 uses this
                    self.logger.warn("Skipping environment map texture.")
                    continue
                elif extra_shader_index == 1:
                    # NormalMapIndex
                    bumpTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 2:
                    # SpecularIntensityIndex
                    glossTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 3:
                    # EnvironmentIntensityIndex (this is reflection)
                    refTexDesc = shader_tex_desc.texture_data
                elif extra_shader_index == 4:
                    # LightCubeMapIndex
                    if shader_tex_desc.texture_data.source.file_name.lower().startswith("rrt_cube_light_map"):
                        # sid meier's railroads: light map generated by engine
                        # we can skip this
                        continue
                    self.logger.warn("Skipping light cube texture.")
                    continue
                elif extra_shader_index == 5:
                    # ShadowTextureIndex
                    self.logger.warn("Skipping shadow texture.")
                    continue
                    
            if baseTexDesc:
                base_texture = self.import_texture(baseTexDesc.source)
                if base_texture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the base color channel
                    mapto = Blender.Texture.MapTo.COL
                    # set the texture for the material
                    material.setTexture(0, base_texture, texco, mapto)
                    mbase_texture = material.getTextures()[0]
                    mbase_texture.blendmode = blendmode
                    mbase_texture.uvlayer = self.get_uv_layer_name(baseTexDesc.uv_set)
            if glowTexDesc:
                glow_texture = self.import_texture(glowTexDesc.source)
                if glow_texture:
                    # glow maps use alpha from rgb intensity
                    glow_texture.imageFlags |= Blender.Texture.ImageFlags.CALCALPHA
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the base color and emit channel
                    mapto = Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT
                    # set the texture for the material
                    material.setTexture(1, glow_texture, texco, mapto)
                    mglow_texture = material.getTextures()[1]
                    mglow_texture.uvlayer = self.get_uv_layer_name(glowTexDesc.uv_set)
            if bumpTexDesc:
                bumpTexture = self.import_texture(bumpTexDesc.source)
                if bumpTexture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the normal channel
                    mapto = Blender.Texture.MapTo.NOR
                    # set the texture for the material
                    material.setTexture(2, bumpTexture, texco, mapto)
                    mbumpTexture = material.getTextures()[2]
                    mbumpTexture.uvlayer = self.get_uv_layer_name(bumpTexDesc.uv_set)
            if glossTexDesc:
                gloss_texture = self.import_texture(glossTexDesc.source)
                if gloss_texture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the specularity channel
                    mapto = Blender.Texture.MapTo.SPEC
                    # set the texture for the material
                    material.setTexture(4, gloss_texture, texco, mapto)
                    mgloss_texture = material.getTextures()[4]
                    mgloss_texture.uvlayer = self.get_uv_layer_name(glossTexDesc.uv_set)
            if darkTexDesc:
                dark_texture = self.import_texture(darkTexDesc.source)
                if dark_texture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the COL channel
                    mapto = Blender.Texture.MapTo.COL
                    # set the texture for the material
                    material.setTexture(5, dark_texture, texco, mapto)
                    mdark_texture = material.getTextures()[5]
                    mdark_texture.uvlayer = self.get_uv_layer_name(darkTexDesc.uv_set)
                    # set blend mode to "DARKEN"
                    mdark_texture.blendmode = Blender.Texture.BlendModes["DARKEN"]
            if detailTexDesc:
                detail_texture = self.import_texture(detailTexDesc.source)
                if detail_texture:
                    # import detail texture as extra base texture
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the COL channel
                    mapto = Blender.Texture.MapTo.COL
                    # set the texture for the material
                    material.setTexture(6, detail_texture, texco, mapto)
                    mdetail_texture = material.getTextures()[6]
                    mdetail_texture.uvlayer = self.get_uv_layer_name(detailTexDesc.uv_set)
            if refTexDesc:
                refTexture = self.import_texture(refTexDesc.source)
                if refTexture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the base color and emit channel
                    mapto = Blender.Texture.MapTo.REF
                    # set the texture for the material
                    material.setTexture(7, refTexture, texco, mapto)
                    mrefTexture = material.getTextures()[7]
                    mrefTexture.uvlayer = self.get_uv_layer_name(refTexDesc.uv_set)
        # if not a texture property, but a bethesda shader property...
        elif bsShaderProperty:
            # also contains textures, used in fallout 3
            baseTexFile = bsShaderProperty.texture_set.textures[0]
            if baseTexFile:
                base_texture = self.import_texture(baseTexFile)
                if base_texture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the base color channel
                    mapto = Blender.Texture.MapTo.COL
                    # set the texture for the material
                    material.setTexture(0, base_texture, texco, mapto)
                    mbase_texture = material.getTextures()[0]
                    mbase_texture.blendmode = blendmode

            glowTexFile = bsShaderProperty.texture_set.textures[2]
            if glowTexFile:
                glow_texture = self.import_texture(glowTexFile)
                if glow_texture:
                    # glow maps use alpha from rgb intensity
                    glow_texture.imageFlags |= Blender.Texture.ImageFlags.CALCALPHA
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the base color and emit channel
                    mapto = Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT
                    # set the texture for the material
                    material.setTexture(1, glow_texture, texco, mapto)
                    mglow_texture = material.getTextures()[1]
                    mglow_texture.blendmode = blendmode

            bumpTexFile = bsShaderProperty.texture_set.textures[1]
            if bumpTexFile:
                bumpTexture = self.import_texture(bumpTexFile)
                if bumpTexture:
                    # set the texture to use face UV coordinates
                    texco = Blender.Texture.TexCo.UV
                    # map the texture to the normal channel
                    mapto = Blender.Texture.MapTo.NOR
                    # set the texture for the material
                    material.setTexture(2, bumpTexture, texco, mapto)
                    mbumpTexture = material.getTextures()[2]
                    mbumpTexture.blendmode = blendmode

        if textureEffect:
            envmapTexture = self.import_texture(textureEffect.source_texture)
            if envmapTexture:
                # set the texture to use face reflection coordinates
                texco = Blender.Texture.TexCo.REFL
                # map the texture to the base color channel
                mapto = Blender.Texture.MapTo.COL
                # set the texture for the material
                material.setTexture(3, envmapTexture, texco, mapto)
                menvmapTexture = material.getTextures()[3]
                menvmapTexture.blendmode = Blender.Texture.BlendModes["ADD"]
        # check transparency
        if alphaProperty:
            material.mode |= Blender.Material.Modes.ZTRANSP # enable z-buffered transparency
            # if the image has an alpha channel => then this overrides the material alpha value
            if base_texture:
                # old method:
                #if base_texture.image.depth == 32 or base_texture.image.size == [1,1]: # check for alpha channel in texture; if it's a stub then assume alpha channel
                # new method: let's just assume there is alpha
                if True:
                    base_texture.imageFlags |= Blender.Texture.ImageFlags.USEALPHA # use the alpha channel
                    mbase_texture.mapto |=  Blender.Texture.MapTo.ALPHA # and map the alpha channel to transparency
                    # for proper display in Blender, we must set the alpha value
                    # to 0 and the "Var" slider in the texture Map To tab to the
                    # NIF material alpha value
                    material.setAlpha(0.0)
                    mbase_texture.varfac = alpha
            # non-transparent glow textures have their alpha calculated from RGB
            # not sure what to do with glow textures that have an alpha channel
            # for now we ignore those alpha channels
        else:
            # no alpha property: force alpha 1.0 in Blender
            material.setAlpha(1.0)
        # check specularity
        if (not specProperty) and (self.version != 0x14000004):
            # no specular property: specular color is ignored
            # (for most games)
            # we do this by setting specularity zero
            # however, for Sid Meier's Railroads the specular color is NOT
            # ignored! hence the exception for version 0x14000004
            material.setSpec(0.0)
        # check wireframe property
        if wireProperty:
            # enable wireframe rendering
            material.mode |= Blender.Material.Modes.WIRE

        self.materials[material_hash] = material
        return material

    def import_material_controllers(self, b_material, n_geom):
        """Import material animation data for given geometry."""
        if not self.IMPORT_ANIMATION:
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
        self.logger.info("importing UV controller")
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
        self.logger.info("importing alpha controller")
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
        self.logger.info(
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
        self.logger.info("importing vis controller")
        b_channel = "Layer"
        b_ipo = self.get_object_ipo(b_object)
        b_curve = b_ipo.addCurve(b_channel)
        b_curve.interpolation = Blender.IpoCurve.InterpTypes.CONST
        b_curve.extend = self.get_extend_from_flags(n_vis_ctrl.flags)
        for n_key in n_vis_ctrl.data.keys:
            b_curve[1 + n_key.time * self.fps] = (
                2 ** (n_key.value + max([1] + self.scene.getLayers()) - 1))

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

        @param niBlock: The nif block whose mesh data to import.
        @type niBlock: C{NiTriBasedGeom}
        @param group_mesh: The mesh to which to append the geometry
            data. If C{None}, a new mesh is created.
        @type group_mesh: A Blender object that has mesh data.
        @param applytransform: Whether to apply the niBlock's
            transformation to the mesh. If group_mesh is not C{None},
            then applytransform must be C{True}.
        @type applytransform: C{bool}
        """
        assert(isinstance(niBlock, NifFormat.NiTriBasedGeom))

        logger = logging.getLogger("niftools.blender.import.mesh")
        logger.info("Importing mesh data for geometry %s" % niBlock.name)

        if group_mesh:
            b_mesh = group_mesh
            b_meshData = group_mesh.getData(mesh=True)
        else:
            # Mesh name -> must be unique, so tag it if needed
            b_name = self.import_name(niBlock)
            # create mesh data
            b_meshData = Blender.Mesh.New(b_name)
            b_meshData.properties['longName'] = niBlock.name
            # create mesh object and link to data
            b_mesh = self.scene.objects.new(b_meshData, b_name)

            # Mesh hidden flag
            if niBlock.flags & 1 == 1:
                b_mesh.setDrawType(2) # hidden: wire
            else:
                b_mesh.setDrawType(4) # not hidden: shaded

        # set transform matrix for the mesh
        if not applytransform:
            if group_mesh:
                raise NifImportError(
                    "BUG: cannot set matrix when importing meshes in groups;"
                    " use applytransform = True")
            b_mesh.setMatrix(self.import_matrix(niBlock,
                                                relative_to=relative_to))
        else:
            # used later on
            transform = self.import_matrix(niBlock, relative_to=relative_to)

        # shortcut for mesh geometry data
        niData = niBlock.data
        if not niData:
            raise NifImportError("no shape data in %s" % b_name)

        # vertices
        verts = niData.vertices

        # faces
        tris = [list(tri) for tri in niData.get_triangles()]

        # "sticky" UV coordinates: these are transformed in Blender UV's
        uvco = niData.uv_sets

        # vertex normals
        norms = niData.normals

        # Stencil (for double sided meshes)
        stencilProperty = self.find_property(niBlock,
                                             NifFormat.NiStencilProperty)
        # we don't check flags for now, nothing fancy
        if stencilProperty:
            b_meshData.mode |= Blender.Mesh.Modes.TWOSIDED
        else:
            b_meshData.mode &= ~Blender.Mesh.Modes.TWOSIDED

        # Material
        # note that NIF files only support one material for each trishape
        # find material property
        matProperty = self.find_property(niBlock, NifFormat.NiMaterialProperty)
        if matProperty:
            # Texture
            textProperty = None
            if uvco:
                textProperty = self.find_property(niBlock,
                                                  NifFormat.NiTexturingProperty)
            
            # Alpha
            alphaProperty = self.find_property(niBlock,
                                               NifFormat.NiAlphaProperty)
            
            # Specularity
            specProperty = self.find_property(niBlock,
                                              NifFormat.NiSpecularProperty)

            # Wireframe
            wireProperty = self.find_property(niBlock,
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
            material = self.import_material(matProperty, textProperty,
                                            alphaProperty, specProperty,
                                            textureEffect, wireProperty,
                                            bsShaderProperty, extra_datas)
            # XXX todo: merge this call into import_material
            self.import_material_controllers(material, niBlock)
            b_mesh_materials = b_meshData.materials
            try:
                materialIndex = b_mesh_materials.index(material)
            except ValueError:
                materialIndex = len(b_mesh_materials)
                b_meshData.materials += [material]
            # if mesh has one material with wireproperty, then make the mesh
            # wire in 3D view
            if wireProperty:
                b_mesh.drawType = Blender.Object.DrawTypes["WIRE"]
        else:
            material = None
            materialIndex = 0

        # if there are no vertices then enable face index shifts
        # (this fixes an issue with indexing)
        if len(b_meshData.verts) == 0:
            check_shift = True
        else:
            check_shift = False

        # v_map will store the vertex index mapping
        # nif vertex i maps to blender vertex v_map[i]
        v_map = [0 for i in xrange(len(verts))] # pre-allocate memory, for faster performance
        
        # Following code avoids introducing unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
        n_map = {}
        b_v_index = len(b_meshData.verts)
        for i, v in enumerate(verts):
            # The key k identifies unique vertex /normal pairs.
            # We use a tuple of ints for key, this works MUCH faster than a
            # tuple of floats.
            if norms:
                n = norms[i]
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
                    v = Blender.Mathutils.Vector(v.x, v.y, v.z)
                    v *= transform
                    b_meshData.verts.extend(v)
                else:
                    b_meshData.verts.extend(v.x, v.y, v.z)
                # adds normal info if present (Blender recalculates these when
                # switching between edit mode and object mode)
                if norms:
                    mv = b_meshData.verts[b_v_index]
                    n = norms[i]
                    mv.no = Blender.Mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                # NIF vertex i maps to Blender vertex v_map[n_map_k]
                v_map[i] = v_map[n_map_k]
        # report
        logger.debug("%i unique vertex-normal pairs" % len(n_map))
        # release memory
        del n_map

        # Adds the faces to the mesh
        f_map = [None]*len(tris)
        b_f_index = len(b_meshData.faces)
        num_new_faces = 0 # counter for debugging
        for i, f in enumerate(tris):
            # get face index
            f_verts = [b_meshData.verts[v_map[vert_index]] for vert_index in f]
            # skip degenerate faces
            # we get a ValueError on faces.extend otherwise
            if (f_verts[0] == f_verts[1]) or (f_verts[1] == f_verts[2]) or (f_verts[2] == f_verts[0]): continue
            tmp1 = len(b_meshData.faces)
            # extend checks for duplicate faces
            # see http://www.blender3d.org/documentation/240PythonDoc/Mesh.MFaceSeq-class.html
            b_meshData.faces.extend(*f_verts)
            if tmp1 == len(b_meshData.faces): continue # duplicate face!
            # faces.extend does not necessarily add vertices in the order
            # they were given in the argument list
            # so we must fix the face index order
            if check_shift:
                added_face = b_meshData.faces[-1]
                if added_face.verts[0] == f_verts[0]: # most common case, checking it first will speed up the script
                    pass # f[0] comes first, everything ok
                elif added_face.verts[2] == f_verts[0]: # second most common case
                    f[0], f[1], f[2] = f[1], f[2], f[0] # f[0] comes last
                elif added_face.verts[1] == f_verts[0]: # this never seems to occur, leave it just in case
                    f[0], f[1], f[2] = f[2], f[0], f[1] # f[0] comes second
                else:
                    raise RuntimeError("face extend index bug")
            # keep track of added faces, mapping NIF face index to
            # Blender face index
            f_map[i] = b_f_index
            b_f_index += 1
            num_new_faces += 1
        # at this point, deleted faces (degenerate or duplicate)
        # satisfy f_map[i] = None

        logger.debug("%i unique faces" % num_new_faces)

        # set face smoothing and material
        for b_f_index in f_map:
            if b_f_index is None:
                continue
            f = b_meshData.faces[b_f_index]
            f.smooth = 1 if norms else 0
            f.mat = materialIndex

        # vertex colors
        vcol = niData.vertex_colors
        
        if vcol:
            b_meshData.vertexColors = 1
            for f, b_f_index in izip(tris, f_map):
                if b_f_index is None:
                    continue
                b_face = b_meshData.faces[b_f_index]
                # now set the vertex colors
                for f_vert_index, vert_index in enumerate(f):
                    b_face.col[f_vert_index].r = int(vcol[vert_index].r * 255)
                    b_face.col[f_vert_index].g = int(vcol[vert_index].g * 255)
                    b_face.col[f_vert_index].b = int(vcol[vert_index].b * 255)
                    b_face.col[f_vert_index].a = int(vcol[vert_index].a * 255)
            # vertex colors influence lighting...
            # so now we have to set the VCOL_LIGHT flag on the material
            # see below
            
        # UV coordinates
        # NIF files only support 'sticky' UV coordinates, and duplicates
        # vertices to emulate hard edges and UV seam. So whenever a hard edge
        # or a UV seam is present the mesh, vertices are duplicated. Blender
        # only must duplicate vertices for hard edges; duplicating for UV seams
        # would introduce unnecessary hard edges.

        # only import UV if there are faces
        # (some corner cases have only one vertex, and no faces,
        # and b_meshData.faceUV = 1 on such mesh raises a runtime error)
        if b_meshData.faces:
            b_meshData.faceUV = 1
            b_meshData.vertexUV = 0
            for i, uv_set in enumerate(uvco):
                # Set the face UV's for the mesh. The NIF format only supports
                # vertex UV's, but Blender only allows explicit editing of face
                # UV's, so load vertex UV's as face UV's
                uvlayer = self.get_uv_layer_name(i)
                if not uvlayer in b_meshData.getUVLayerNames():
                    b_meshData.addUVLayer(uvlayer)
                b_meshData.activeUVLayer = uvlayer
                for f, b_f_index in izip(tris, f_map):
                    if b_f_index is None:
                        continue
                    uvlist = [ Vector(uv_set[vert_index].u, 1.0 - uv_set[vert_index].v) for vert_index in f ]
                    b_meshData.faces[b_f_index].uv = tuple(uvlist)
            b_meshData.activeUVLayer = self.get_uv_layer_name(0)
        
        if material:
            # fix up vertex colors depending on whether we had textures in the
            # material
            mbasetex = material.getTextures()[0]
            mglowtex = material.getTextures()[1]
            if b_meshData.vertexColors == 1:
                if mbasetex or mglowtex:
                    # textured material: vertex colors influence lighting
                    material.mode |= Blender.Material.Modes.VCOL_LIGHT
                else:
                    # non-textured material: vertex colors incluence color
                    material.mode |= Blender.Material.Modes.VCOL_PAINT

            # if there's a base texture assigned to this material sets it
            # to be displayed in Blender's 3D view
            # but only if there are UV coordinates
            if mbasetex and uvco:
                # face mode bitfield value
                TEX = Blender.Mesh.FaceModes['TEX']
                # face transparency enum
                ALPHA = Blender.Mesh.FaceTranspModes['ALPHA']
                imgobj = mbasetex.tex.getImage()
                if imgobj:
                    for b_f_index in f_map:
                        if b_f_index is None:
                            continue
                        f = b_meshData.faces[b_f_index]
                        f.mode = TEX
                        f.transp = ALPHA
                        f.image = imgobj

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
                if not groupname in b_meshData.getVertGroupNames():
                    b_meshData.addVertGroup(groupname)
                for skinWeight in vertex_weights:
                    vert = skinWeight.index
                    weight = skinWeight.weight
                    b_meshData.assignVertsToGroup(
                        groupname, [v_map[vert]], weight,
                        Blender.Mesh.AssignModes.REPLACE)

        # import body parts as vertex groups
        if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
            skinpart = niBlock.get_skin_partition()
            for bodypart, skinpartblock in izip(
                skininst.partitions, skinpart.skin_partition_blocks):
                bodypart_wrap = NifFormat.BSDismemberBodyPartType()
                bodypart_wrap.set_value(bodypart.body_part)
                groupname = bodypart_wrap.get_detail_display()
                # create vertex group if it did not exist yet
                if not(groupname in b_meshData.getVertGroupNames()):
                    b_meshData.addVertGroup(groupname)
                # find vertex indices of this group
                groupverts = [v_map[v_index]
                              for v_index in skinpartblock.vertex_map]
                # create the group
                b_meshData.assignVertsToGroup(
                    groupname, groupverts, 1,
                    Blender.Mesh.AssignModes.ADD)

        # import morph controller
        # XXX todo: move this to import_mesh_controllers
        if self.IMPORT_ANIMATION:
            morphCtrl = self.find_controller(niBlock, NifFormat.NiGeomMorpherController)
            if morphCtrl:
                morphData = morphCtrl.data
                if morphData.num_morphs:
                    # insert base key at frame 1, using relative keys
                    b_meshData.insertKey(1, 'relative')
                    # get name for base key
                    keyname = morphData.morphs[0].frame_name
                    if not keyname:
                        keyname = 'Base'
                    # set name for base key
                    b_meshData.key.blocks[0].name = keyname
                    # get base vectors and import all morphs
                    baseverts = morphData.morphs[0].vectors
                    b_ipo = Blender.Ipo.New('Key' , 'KeyIpo')
                    b_meshData.key.ipo = b_ipo
                    for idxMorph in xrange(1, morphData.num_morphs):
                        # get name for key
                        keyname = morphData.morphs[idxMorph].frame_name
                        if not keyname:
                            keyname = 'Key %i' % idxMorph
                        self.logger.info("inserting key '%s'" % keyname)
                        # get vectors
                        morphverts = morphData.morphs[idxMorph].vectors
                        # for each vertex calculate the key position from base
                        # pos + delta offset
                        assert(len(baseverts) == len(morphverts) == len(v_map))
                        for bv, mv, b_v_index in izip(baseverts, morphverts, v_map):
                            base = Blender.Mathutils.Vector(bv.x, bv.y, bv.z)
                            delta = Blender.Mathutils.Vector(mv.x, mv.y, mv.z)
                            v = base + delta
                            if applytransform:
                                v *= transform
                            b_meshData.verts[b_v_index].co[0] = v.x
                            b_meshData.verts[b_v_index].co[1] = v.y
                            b_meshData.verts[b_v_index].co[2] = v.z
                        # update the mesh and insert key
                        b_meshData.insertKey(idxMorph, 'relative')
                        # set name for key
                        b_meshData.key.blocks[idxMorph].name = keyname
                        # set up the ipo key curve
                        try:
                            b_curve = b_ipo.addCurve(keyname)
                        except ValueError:
                            # this happens when two keys have the same name
                            # an instance of this is in fallout 3
                            # meshes/characters/_male/skeleton.nif HeadAnims:0
                            self.logger.warn(
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
                        for bv, b_v_index in izip(baseverts, v_map):
                            base = Blender.Mathutils.Vector(bv.x, bv.y, bv.z)
                            if applytransform:
                                base *= transform
                            b_meshData.verts[b_v_index].co[0] = base.x
                            b_meshData.verts[b_v_index].co[1] = base.y
                            b_meshData.verts[b_v_index].co[2] = base.z

        # import facegen morphs
        if self.egmdata:
            # XXX if there is an egm, the assumption is that there is only one
            # XXX mesh in the nif
            sym_morphs = [list(morph.get_relative_vertices())
                          for morph in self.egmdata.sym_morphs]
            asym_morphs = [list(morph.get_relative_vertices())
                          for morph in self.egmdata.asym_morphs]

            # insert base key at frame 1, using relative keys
            b_meshData.insertKey(1, 'relative')

            if self.IMPORT_EGMANIM:
                # if morphs are animated: create key ipo for mesh
                b_ipo = Blender.Ipo.New('Key' , 'KeyIpo')
                b_meshData.key.ipo = b_ipo


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
                for bv, mv, b_v_index in izip(verts, morphverts, v_map):
                    base = Blender.Mathutils.Vector(bv.x, bv.y, bv.z)
                    delta = Blender.Mathutils.Vector(mv[0], mv[1], mv[2])
                    v = base + delta
                    if applytransform:
                        v *= transform
                    b_meshData.verts[b_v_index].co[0] = v.x
                    b_meshData.verts[b_v_index].co[1] = v.y
                    b_meshData.verts[b_v_index].co[2] = v.z
                # update the mesh and insert key
                b_meshData.insertKey(1, 'relative')
                # set name for key
                b_meshData.key.blocks[-1].name = keyname

                if self.IMPORT_EGMANIM:
                    # set up the ipo key curve
                    b_curve = b_ipo.addCurve(keyname)
                    # linear interpolation
                    b_curve.interpolation = Blender.IpoCurve.InterpTypes.LINEAR
                    # constant extrapolation
                    b_curve.extend = Blender.IpoCurve.ExtendTypes.CONST
                    # set up the curve's control points
                    framestart = 1 + len(b_meshData.key.blocks) * 10
                    for frame, value in ((framestart, 0),
                                         (framestart + 5, self.IMPORT_EGMANIMSCALE),
                                         (framestart + 10, 0)):
                        b_curve.addBezier( ( frame, value ) )

            if self.IMPORT_EGMANIM:
                # set begin and end frame
                self.scene.getRenderingContext().startFrame(1)
                self.scene.getRenderingContext().endFrame(
                    11 + len(b_meshData.key.blocks) * 10)

            # finally: return to base position
            for bv, b_v_index in izip(verts, v_map):
                base = Blender.Mathutils.Vector(bv.x, bv.y, bv.z)
                if applytransform:
                    base *= transform
                b_meshData.verts[b_v_index].co[0] = base.x
                b_meshData.verts[b_v_index].co[1] = base.y
                b_meshData.verts[b_v_index].co[2] = base.z
     
        # recalculate normals if we did not import them
        if not norms:
            b_meshData.calcNormals()
        # import priority if existing
        if niBlock.name in self.bone_priorities:
            constr = b_mesh.constraints.append(
                Blender.Constraint.Type.NULL)
            constr.name = "priority:%i" % self.bone_priorities[niBlock.name]

        return b_mesh

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
            try:
                animtxt = [txt for txt in Blender.Text.Get() if txt.getName() == "Anim"][0]
                animtxt.clear()
            except:
                animtxt = Blender.Text.New("Anim")
            
            frame = 1
            for key in txk.text_keys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = 1 + int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                animtxt.write('%i/%s\n'%(frame, newkey))
            
            # set start and end frames
            self.scene.getRenderingContext().startFrame(1)
            self.scene.getRenderingContext().endFrame(frame)
        
    def store_bones_extra_matrix(self):
        """Stores correction matrices in a text buffer so that the original
        alignment can be re-exported. In order for this to work it is necessary
        to mantain the imported names unaltered. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""
        # clear the text buffer, or create new buffer
        try:
            bonetxt = Blender.Text.Get("BoneExMat")
        except NameError:
            bonetxt = Blender.Text.New("BoneExMat")
        bonetxt.clear()
        # write correction matrices to text buffer
        for niBone, correction_matrix in self.bones_extra_matrix.iteritems():
            # skip identity transforms
            if sum(sum(abs(x) for x in row)
                   for row in (correction_matrix - self.IDENTITY44)) \
                < self.EPSILON:
                continue
            # 'pickle' the correction matrix
            line = ''
            for row in correction_matrix:
                line = '%s;%s,%s,%s,%s' % (line, row[0], row[1], row[2], row[3])
            # we write the bone names with their blender name!
            blender_bone_name = self.names[niBone] # NOT niBone.name !!
            # write it to the text buffer
            bonetxt.write('%s/%s\n' % (blender_bone_name, line[1:]))
        

    def store_names(self):
        """Stores the original, long object names so that they can be
        re-exported. In order for this to work it is necessary to mantain the
        imported names unaltered. Since the text buffer is cleared on each
        import only the last import will be exported correctly."""
        # clear the text buffer, or create new buffer
        try:
            namestxt = Blender.Text.Get("FullNames")
        except NameError:
            namestxt = Blender.Text.New("FullNames")
        namestxt.clear()
        # write the names to the text buffer
        for block, shortname in self.names.iteritems():
            if block.name and shortname != block.name:
                namestxt.write('%s;%s\n'% (shortname, block.name))

    def get_frames_per_second(self, roots):
        """Scan all blocks and return a reasonable number for FPS."""
        # find all key times
        key_times = []
        for root in roots:
            for kfd in root.tree(block_type = NifFormat.NiKeyframeData):
                key_times.extend(key.time for key in kfd.translations.keys)
                key_times.extend(key.time for key in kfd.scales.keys)
                key_times.extend(key.time for key in kfd.quaternion_keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[0].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[1].keys)
                key_times.extend(key.time for key in kfd.xyz_rotations[2].keys)
            for kfi in root.tree(block_type = NifFormat.NiBSplineInterpolator):
                if not kfi.basis_data:
                    # skip bsplines without basis data (eg bowidle.kf in
                    # Oblivion)
                    continue
                key_times.extend(
                    point * (kfi.stop_time - kfi.start_time)
                    / (kfi.basis_data.num_control_points - 2)
                    for point in xrange(kfi.basis_data.num_control_points - 2))
            for uvdata in root.tree(block_type = NifFormat.NiUVData):
                for uvgroup in uvdata.uv_groups:
                    key_times.extend(key.time for key in uvgroup.keys)
        # not animated, return a reasonable default
        if not key_times:
            return 30
        # calculate FPS
        fps = 30
        lowestDiff = sum(abs(int(time*fps+0.5)-(time*fps)) for time in key_times)
        # for fps in xrange(1,120): #disabled, used for testing
        for testFps in [20, 25, 35]:
            diff = sum(abs(int(time*testFps+0.5)-(time*testFps)) for time in key_times)
            if diff < lowestDiff:
                lowestDiff = diff
                fps = testFps
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

    def mark_armatures_bones(self, niBlock):
        """Mark armatures and bones by peeking into NiSkinInstance blocks."""
        # case where we import skeleton only,
        # or importing an Oblivion or Fallout 3 skeleton:
        # do all NiNode's as bones
        if self.IMPORT_SKELETON == 1 or (
            self.version in (0x14000005, 0x14020007) and
            self.filebase.lower() in ('skeleton', 'skeletonbeast')):
            
            if not isinstance(niBlock, NifFormat.NiNode):
                raise NifImportError(
                    "cannot import skeleton: root is not a NiNode")
            # for morrowind, take the Bip01 node to be the skeleton root
            if self.version == 0x04000002:
                skelroot = niBlock.find(block_name = 'Bip01',
                                        block_type = NifFormat.NiNode)
                if not skelroot:
                    skelroot = niBlock
            else:
                skelroot = niBlock
            if skelroot not in self.armatures:
                self.armatures[skelroot] = []
            self.logger.info("Selecting node '%s' as skeleton root"
                             % skelroot.name)
            # add bones
            for bone in skelroot.tree():
                if bone is skelroot:
                    continue
                if not isinstance(bone, NifFormat.NiNode):
                    continue
                if self.is_grouping_node(bone):
                    continue
                if bone not in self.armatures[skelroot]:
                    self.armatures[skelroot].append(bone)
            return # done!

        # attaching to selected armature -> first identify armature and bones
        elif self.IMPORT_SKELETON == 2 and not self.armatures:
            skelroot = niBlock.find(block_name = self.selected_objects[0].name)
            if not skelroot:
                raise NifImportError(
                    "nif has no armature '%s'" % self.selected_objects[0].name)
            self.logger.debug("Identified '%s' as armature" % skelroot.name)
            self.armatures[skelroot] = []
            for bone_name in self.selected_objects[0].data.bones.keys():
                # blender bone naming -> nif bone naming
                nif_bone_name = self.get_bone_name_for_nif(bone_name)
                # find a block with bone name
                bone_block = skelroot.find(block_name = nif_bone_name)
                # add it to the name list if there is a bone with that name
                if bone_block:
                    self.logger.info(
                        "Identified nif block '%s' with bone '%s' "
                        "in selected armature" % (nif_bone_name, bone_name))
                    self.names[bone_block] = bone_name
                    self.armatures[skelroot].append(bone_block)
                    self.complete_bone_tree(bone_block, skelroot)

        # search for all NiTriShape or NiTriStrips blocks...
        if isinstance(niBlock, NifFormat.NiTriBasedGeom):
            # yes, we found one, get its skin instance
            if niBlock.is_skin():
                self.logger.debug("Skin found on block '%s'" % niBlock.name)
                # it has a skin instance, so get the skeleton root
                # which is an armature only if it's not a skinning influence
                # so mark the node to be imported as an armature
                skininst = niBlock.skin_instance
                skelroot = skininst.skeleton_root
                if self.IMPORT_SKELETON == 0:
                    if not self.armatures.has_key(skelroot):
                        self.armatures[skelroot] = []
                        self.logger.debug("'%s' is an armature"
                                          % skelroot.name)
                elif self.IMPORT_SKELETON == 2:
                    if not self.armatures.has_key(skelroot):
                        raise NifImportError(
                            "nif structure incompatible with '%s' as armature:"
                            " node '%s' has '%s' as armature"
                            % (self.selected_objects[0].name, niBlock.name,
                               skelroot.name))

                for i, boneBlock in enumerate(skininst.bones):
                    # boneBlock can be None; see pyffi issue #3114079
                    if not boneBlock:
                        continue
                    if boneBlock not in self.armatures[skelroot]:
                        self.armatures[skelroot].append(boneBlock)
                        self.logger.debug(
                            "'%s' is a bone of armature '%s'"
                            % (boneBlock.name, skelroot.name))
                    # now we "attach" the bone to the armature:
                    # we make sure all NiNodes from this bone all the way
                    # down to the armature NiNode are marked as bones
                    self.complete_bone_tree(boneBlock, skelroot)

                # mark all nodes as bones if asked
                if self.IMPORT_EXTRANODES:
                    # add bones
                    for bone in skelroot.tree():
                        if bone is skelroot:
                            continue
                        if not isinstance(bone, NifFormat.NiNode):
                            continue
                        if isinstance(bone, NifFormat.NiLODNode):
                            # LOD nodes are never bones
                            continue
                        if self.is_grouping_node(bone):
                            continue
                        if bone not in self.armatures[skelroot]:
                            self.armatures[skelroot].append(bone)
                            self.logger.debug(
                                "'%s' marked as extra bone of armature '%s'"
                                % (bone.name, skelroot.name))
                            # we make sure all NiNodes from this bone
                            # all the way down to the armature NiNode
                            # are marked as bones
                            self.complete_bone_tree(bone, skelroot)

        # continue down the tree
        for child in niBlock.get_refs():
            if not isinstance(child, NifFormat.NiAVObject): continue # skip blocks that don't have transforms
            self.mark_armatures_bones(child)

    def complete_bone_tree(self, bone, skelroot):
        """Make sure that the bones actually form a tree all the way
        down to the armature node. Call this function on all bones of
        a skin instance.
        """
        # we must already have marked this one as a bone
        assert self.armatures.has_key(skelroot) # debug
        assert bone in self.armatures[skelroot] # debug
        # get the node parent, this should be marked as an armature or as a bone
        boneparent = bone._parent
        if boneparent != skelroot:
            # parent is not the skeleton root
            if boneparent not in self.armatures[skelroot]:
                # neither is it marked as a bone: so mark the parent as a bone
                self.armatures[skelroot].append(boneparent)
                # store the coordinates for realignement autodetection 
                self.logger.debug("'%s' is a bone of armature '%s'"
                                  % (boneparent.name, skelroot.name))
            # now the parent is marked as a bone
            # recursion: complete the bone tree,
            # this time starting from the parent bone
            self.complete_bone_tree(boneparent, skelroot)

    def is_bone(self, niBlock):
        """Tests a NiNode to see if it's a bone."""
        if not niBlock :
            return False
        for bones in self.armatures.values():
            if niBlock in bones:
                return True
        return False

    def is_armature_root(self, niBlock):
        """Tests a block to see if it's an armature."""
        if isinstance(niBlock, NifFormat.NiNode):
            return  self.armatures.has_key(niBlock)
        return False
        
    def get_closest_bone(self, niBlock, skelroot):
        """Detect closest bone ancestor."""
        par = niBlock._parent
        while par:
            if par == skelroot:
                return None
            if self.is_bone(par):
                return par
            par = par._parent
        return par

    def get_blender_object(self, niBlock):
        """Retrieves the Blender object or Blender bone matching the block."""
        if self.is_bone(niBlock):
            boneName = self.names[niBlock]
            armatureName = None
            for armatureBlock, boneBlocks in self.armatures.iteritems():
                if niBlock in boneBlocks:
                    armatureName = self.names[armatureBlock]
                    break
            else:
                raise NifImportError("cannot find bone '%s'" % boneName)
            armatureObject = Blender.Object.Get(armatureName)
            return armatureObject.data.bones[boneName]
        else:
            return Blender.Object.Get(self.names[niBlock])

    def is_grouping_node(self, niBlock):
        """Determine whether node is grouping node.
        Returns the children which are grouped, or empty list if it is not a
        grouping node.
        """
        # combining shapes: disable grouping
        if not self.IMPORT_COMBINESHAPES:
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
                kfd = None #not supported yet so avoids fatal error - should be kfc.interpolator.spline_data when spline data is figured out.
            else:
                kfd = kfc.interpolator.data
        else:
            kfd = kfc.data

        if not kfd:
            # no animation data: do nothing
            return

        # denote progress
        self.msg_progress("Animation")
        self.logger.info("Importing animation data for %s" % b_obj.name)
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        # create an Ipo for this object
        b_ipo = self.get_object_ipo(b_obj)
        # get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys
        self.logger.debug('Scale keys...')
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
            self.logger.debug('Rotation keys...(euler)')
            for (xkey, ykey, zkey) in izip(xkeys, ykeys, zkeys):
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
                self.logger.debug('Rotation keys...(quaternions)')
            for key in kfd.quaternion_keys:
                frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                rot = Blender.Mathutils.Quaternion(key.value.w, key.value.x, key.value.y, key.value.z).toEuler()
                # Blender euler is in degrees, object RotXYZ is in radians
                b_obj.RotX = rot.x * self.D2R
                b_obj.RotY = rot.y * self.D2R
                b_obj.RotZ = rot.z * self.D2R
                b_obj.insertIpoKey(Blender.Object.ROT)

        if translations.keys:
            self.logger.debug('Translation keys...')
        for key in translations.keys:
            frame = 1+int(key.time * self.fps + 0.5) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            b_obj.LocX = key.value.x
            b_obj.LocY = key.value.y
            b_obj.LocZ = key.value.z
            b_obj.insertIpoKey(Blender.Object.LOC)
            
        Blender.Set('curframe', 1)

    def import_bhk_shape(self, bhkshape):
        """Import an oblivion collision shape as list of blender meshes."""
        if isinstance(bhkshape, NifFormat.bhkConvexVerticesShape):
            # find vertices (and fix scale)
            vertices, triangles = pyffi.utils.quickhull.qhull3d(
                [ (7 * vert.x, 7 * vert.y, 7 * vert.z)
                  for vert in bhkshape.vertices ])

            # create convex mesh
            me = Blender.Mesh.New('convexpoly')
            for vert in vertices:
                me.verts.extend(*vert)
            for triangle in triangles:
                me.faces.extend(triangle)

            # link mesh to scene and set transform
            ob = self.scene.objects.new(me, 'convexpoly')

            # set bounds type
            ob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
            # convex hull shape not in blender Python API
            # Blender.Object.RBShapes['CONVEXHULL'] should be 5
            ob.rbShapeBoundType = 5
            ob.drawMode = Blender.Object.DrawModes['WIRE']
            # radius: quick estimate
            ob.rbRadius = min(vert.co.length for vert in me.verts)
            ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[bhkshape.material], "STRING")
            
            # also remove duplicate vertices
            numverts = len(me.verts)
            # 0.005 = 1/200
            numdel = me.remDoubles(0.005)
            if numdel:
                self.logger.info(
                    "Removed %i duplicate vertices"
                    " (out of %i) from collision mesh" % (numdel, numverts))

            return [ ob ]

        elif isinstance(bhkshape, NifFormat.bhkTransformShape):
            # import shapes
            collision_objs = self.import_bhk_shape(bhkshape.shape)
            # find transformation matrix
            transform = Blender.Mathutils.Matrix(*bhkshape.transform.as_list())
            transform.transpose()
            # fix scale
            transform[3][0] *= 7
            transform[3][1] *= 7
            transform[3][2] *= 7
            # apply transform
            for ob in collision_objs:
                ob.setMatrix(ob.getMatrix('localspace') * transform)
                ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[bhkshape.material], "STRING")
            # and return a list of transformed collision shapes
            return collision_objs

        elif isinstance(bhkshape, NifFormat.bhkRigidBody):
            # import shapes
            collision_objs = self.import_bhk_shape(bhkshape.shape)
            # find transformation matrix in case of the T version
            if isinstance(bhkshape, NifFormat.bhkRigidBodyT):
                # set rotation
                transform = Blender.Mathutils.Quaternion(
                    bhkshape.rotation.w, bhkshape.rotation.x,
                    bhkshape.rotation.y, bhkshape.rotation.z).toMatrix()
                transform.resize4x4()
                # set translation
                transform[3][0] = bhkshape.translation.x * 7
                transform[3][1] = bhkshape.translation.y * 7
                transform[3][2] = bhkshape.translation.z * 7
                # apply transform
                for ob in collision_objs:
                    ob.setMatrix(ob.getMatrix('localspace') * transform)
            # set physics flags and mass
            for ob in collision_objs:
                ob.rbFlags = (
                    Blender.Object.RBFlags.ACTOR |
                    Blender.Object.RBFlags.DYNAMIC |
                    Blender.Object.RBFlags.RIGIDBODY |
                    Blender.Object.RBFlags.BOUNDS)
                if bhkshape.mass > 0.0001:
                    # for physics emulation
                    # (mass 0 results in issues with simulation)
                    ob.rbMass = bhkshape.mass / len(collision_objs)
                ob.addProperty("OblivionLayer", self.OB_LAYER[bhkshape.layer], "STRING")
                ob.addProperty("QualityType", self.QUALITY_TYPE[bhkshape.quality_type], "STRING")
                ob.addProperty("MotionSystem", self.MOTION_SYS[bhkshape.motion_system], "STRING")
                # note: also imported as rbMass, but hard to find by users
                # so we import it as a property, and this is also what will
                # be re-exported
                ob.addProperty("Mass", bhkshape.mass / len(collision_objs), "FLOAT")
                ob.addProperty("ColFilter", bhkshape.col_filter, "INT")

            # import constraints
            # this is done once all objects are imported
            # for now, store all imported havok shapes with object lists
            self.havok_objects[bhkshape] = collision_objs
            # and return a list of transformed collision shapes
            return collision_objs
        
        elif isinstance(bhkshape, NifFormat.bhkBoxShape):
            # create box
            minx = -bhkshape.dimensions.x * 7
            maxx = +bhkshape.dimensions.x * 7
            miny = -bhkshape.dimensions.y * 7
            maxy = +bhkshape.dimensions.y * 7
            minz = -bhkshape.dimensions.z * 7
            maxz = +bhkshape.dimensions.z * 7

            me = Blender.Mesh.New('box')
            for x in [minx, maxx]:
                for y in [miny, maxy]:
                    for z in [minz, maxz]:
                        me.verts.extend(x,y,z)
            me.faces.extend(
                [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

            # link box to scene and set transform
            ob = self.scene.objects.new(me, 'box')

            # set bounds type
            ob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
            ob.rbShapeBoundType = Blender.Object.RBShapes['BOX']
            ob.rbRadius = min(maxx, maxy, maxz)
            ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[bhkshape.material], "STRING")
            return [ ob ]

        elif isinstance(bhkshape, NifFormat.bhkSphereShape):
            minx = miny = minz = -bhkshape.radius * 7
            maxx = maxy = maxz = +bhkshape.radius * 7
            me = Blender.Mesh.New('sphere')
            for x in [minx, maxx]:
                for y in [miny, maxy]:
                    for z in [minz, maxz]:
                        me.verts.extend(x,y,z)
            me.faces.extend(
                [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

            # link box to scene and set transform
            ob = self.scene.objects.new(me, 'sphere')

            # set bounds type
            ob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
            ob.rbShapeBoundType = Blender.Object.RBShapes['SPHERE']
            ob.rbRadius = maxx
            ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[bhkshape.material], "STRING")
            return [ ob ]

        elif isinstance(bhkshape, NifFormat.bhkCapsuleShape):
            # create capsule mesh
            length = (bhkshape.first_point - bhkshape.second_point).norm()
            minx = miny = -bhkshape.radius * 7
            maxx = maxy = +bhkshape.radius * 7
            minz = -(length + 2*bhkshape.radius) * 3.5
            maxz = +(length + 2*bhkshape.radius) * 3.5

            me = Blender.Mesh.New('capsule')
            for x in [minx, maxx]:
                for y in [miny, maxy]:
                    for z in [minz, maxz]:
                        me.verts.extend(x,y,z)
            me.faces.extend(
                [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

            # link box to scene and set transform
            ob = self.scene.objects.new(me, 'capsule')

            # set bounds type
            ob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
            ob.rbShapeBoundType = Blender.Object.RBShapes['CYLINDER']
            ob.rbRadius = maxx
            ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[bhkshape.material], "STRING")

            # find transform
            if length > self.EPSILON:
                normal = (bhkshape.first_point - bhkshape.second_point) / length
                normal = Blender.Mathutils.Vector(normal.x, normal.y, normal.z)
            else:
                self.logger.warn(
                    "bhkCapsuleShape with identical points:"
                    " using arbitrary axis")
                normal = Blender.Mathutils.Vector(0, 0, 1)
            minindex = min((abs(x), i) for i, x in enumerate(normal))[1]
            orthvec = Blender.Mathutils.Vector([(1 if i == minindex else 0)
                                                for i in (0,1,2)])
            vec1 = Blender.Mathutils.CrossVecs(normal, orthvec)
            vec1.normalize()
            vec2 = Blender.Mathutils.CrossVecs(normal, vec1)
            # the rotation matrix should be such that
            # (0,0,1) maps to normal
            transform = Blender.Mathutils.Matrix(vec1, vec2, normal)
            transform.resize4x4()
            transform[3][0] = 3.5 * (bhkshape.first_point.x
                                     + bhkshape.second_point.x)
            transform[3][1] = 3.5 * (bhkshape.first_point.y
                                     + bhkshape.second_point.y)
            transform[3][2] = 3.5 * (bhkshape.first_point.z
                                     + bhkshape.second_point.z)
            ob.setMatrix(transform)

            # return object
            return [ ob ]

        elif isinstance(bhkshape, NifFormat.bhkPackedNiTriStripsShape):
            # create mesh for each sub shape
            hk_objects = []
            vertex_offset = 0
            subshapes = bhkshape.sub_shapes
            if not subshapes:
                # fallout 3 stores them in the data
                subshapes = bhkshape.data.sub_shapes
            for subshape_num, subshape in enumerate(subshapes):
                me = Blender.Mesh.New('poly%i' % subshape_num)
                for vert_index in xrange(vertex_offset,
                                         vertex_offset + subshape.num_vertices):
                    vert = bhkshape.data.vertices[vert_index]
                    me.verts.extend(vert.x * 7, vert.y * 7, vert.z * 7)
                for hktriangle in bhkshape.data.triangles:
                    if ((vertex_offset <= hktriangle.triangle.v_1)
                        and (hktriangle.triangle.v_1
                             < vertex_offset + subshape.num_vertices)):
                        me.faces.extend(hktriangle.triangle.v_1 - vertex_offset,
                                        hktriangle.triangle.v_2 - vertex_offset,
                                        hktriangle.triangle.v_3 - vertex_offset)
                    else:
                        continue
                    # check face normal
                    align_plus = sum(abs(x)
                                     for x in ( me.faces[-1].no[0]
                                                + hktriangle.normal.x,
                                                me.faces[-1].no[1]
                                                + hktriangle.normal.y,
                                                me.faces[-1].no[2]
                                                + hktriangle.normal.z ))
                    align_minus = sum(abs(x)
                                      for x in ( me.faces[-1].no[0]
                                                 - hktriangle.normal.x,
                                                 me.faces[-1].no[1]
                                                 - hktriangle.normal.y,
                                                 me.faces[-1].no[2]
                                                 - hktriangle.normal.z ))
                    # fix face orientation
                    if align_plus < align_minus:
                        me.faces[-1].verts = ( me.faces[-1].verts[1],
                                               me.faces[-1].verts[0],
                                               me.faces[-1].verts[2] )

                # link mesh to scene and set transform
                ob = self.scene.objects.new(me, 'poly%i' % subshape_num)

                # set bounds type
                ob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
                ob.rbShapeBoundType = Blender.Object.RBShapes['POLYHEDERON']
                ob.drawMode = Blender.Object.DrawModes['WIRE']
                # radius: quick estimate
                ob.rbRadius = min(vert.co.length for vert in me.verts)
                # set material
                ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[subshape.material], "STRING")

                # also remove duplicate vertices
                numverts = len(me.verts)
                # 0.005 = 1/200
                numdel = me.remDoubles(0.005)
                if numdel:
                    self.logger.info(
                        "Removed %i duplicate vertices"
                        " (out of %i) from collision mesh"
                        % (numdel, numverts))

                vertex_offset += subshape.num_vertices
                hk_objects.append(ob)

            return hk_objects

        elif isinstance(bhkshape, NifFormat.bhkNiTriStripsShape):
            self.havok_mat = bhkshape.material
            return reduce(operator.add,
                          (self.import_bhk_shape(strips)
                           for strips in bhkshape.strips_data))
                
        elif isinstance(bhkshape, NifFormat.NiTriStripsData):
            me = Blender.Mesh.New('poly')
            # no factor 7 correction!!!
            for vert in bhkshape.vertices:
                me.verts.extend(vert.x, vert.y, vert.z)
            me.faces.extend(list(bhkshape.get_triangles()))

            # link mesh to scene and set transform
            ob = self.scene.objects.new(me, 'poly')

            # set bounds type
            ob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
            ob.rbShapeBoundType = Blender.Object.RBShapes['POLYHEDERON']
            ob.drawMode = Blender.Object.DrawModes['WIRE']
            # radius: quick estimate
            ob.rbRadius = min(vert.co.length for vert in me.verts)
            ob.addProperty("HavokMaterial", self.HAVOK_MATERIAL[self.havok_mat], "STRING")

            # also remove duplicate vertices
            numverts = len(me.verts)
            # 0.005 = 1/200
            numdel = me.remDoubles(0.005)
            if numdel:
                self.logger.info(
                    "Removed %i duplicate vertices"
                    " (out of %i) from collision mesh"
                    % (numdel, numverts))

            return [ ob ]

        elif isinstance(bhkshape, NifFormat.bhkMoppBvTreeShape):
            return self.import_bhk_shape(bhkshape.shape)

        elif isinstance(bhkshape, NifFormat.bhkListShape):
            return reduce(operator.add, ( self.import_bhk_shape(subshape)
                                          for subshape in bhkshape.sub_shapes ))

        self.logger.warning("Unsupported bhk shape %s"
                            % bhkshape.__class__.__name__)
        return []



    def import_bhk_constraints(self, hkbody):
        """Imports a bone havok constraint as Blender object constraint."""
        assert(isinstance(hkbody, NifFormat.bhkRigidBody))

        # check for constraints
        if not hkbody.constraints:
            return

        # find objects
        if len(self.havok_objects[hkbody]) != 1:
            self.logger.warning(
                "Rigid body with no or multiple shapes, constraints skipped")
            return

        b_hkobj = self.havok_objects[hkbody][0]
        
        self.logger.info("Importing constraints for %s" % b_hkobj.name)

        # now import all constraints
        for hkconstraint in hkbody.constraints:

            # check constraint entities
            if not hkconstraint.num_entities == 2:
                self.logger.warning(
                    "Constraint with more than 2 entities, skipped")
                continue
            if not hkconstraint.entities[0] is hkbody:
                self.logger.warning(
                    "First constraint entity not self, skipped")
                continue
            if not hkconstraint.entities[1] in self.havok_objects:
                self.logger.warning(
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
                    self.logger.warning("Unknown malleable type (%i), skipped"
                                        % hkconstraint.type)
                # extra malleable constraint settings
                ### damping parameters not yet in Blender Python API
                ### tau (force between bodies) not supported by Blender
            else:
                self.logger.warning("Unknown constraint type (%s), skipped"
                                    % hkconstraint.__class__.__name__)
                continue

            # add the constraint as a rigid body joint
            b_constr = b_hkobj.constraints.append(Blender.Constraint.Type.RIGIDBODYJOINT)

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
            pivot = Blender.Mathutils.Vector(
                hkdescriptor.pivot_a.x * 7,
                hkdescriptor.pivot_a.y * 7,
                hkdescriptor.pivot_a.z * 7)

            # get z- and x-axes of the constraint
            # (also see export_nif.py NifImport.export_constraints)
            if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                # for ragdoll, take z to be the twist axis (central axis of the
                # cone, that is)
                axis_z = Blender.Mathutils.Vector(
                    hkdescriptor.twist_a.x,
                    hkdescriptor.twist_a.y,
                    hkdescriptor.twist_a.z)
                # for ragdoll, let x be the plane vector
                axis_x = Blender.Mathutils.Vector(
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
                axis_y = Blender.Mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_1.x,
                    hkdescriptor.perp_2_axle_in_a_1.y,
                    hkdescriptor.perp_2_axle_in_a_1.z)
                # for hinge, take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = Blender.Mathutils.Vector(
                    hkdescriptor.axle_a.x,
                    hkdescriptor.axle_a.y,
                    hkdescriptor.axle_a.z)
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = Blender.Mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_2.x,
                    hkdescriptor.perp_2_axle_in_a_2.y,
                    hkdescriptor.perp_2_axle_in_a_2.z)
                # they should form a orthogonal basis
                if (Blender.Mathutils.CrossVecs(axis_x, axis_y)
                    - axis_z).length > 0.01:
                    # either not orthogonal, or negative orientation
                    if (Blender.Mathutils.CrossVecs(-axis_x, axis_y)
                        - axis_z).length > 0.01:
                        self.logger.warning(
                            "Axes are not orthogonal in %s;"
                            " arbitrary orientation has been chosen"
                            % hkdescriptor.__class__.__name__)
                        axis_z = Blender.Mathutils.CrossVecs(axis_x, axis_y)
                    else:
                        # fix orientation
                        self.logger.warning(
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
                axis_y = Blender.Mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_1.x,
                    hkdescriptor.perp_2_axle_in_a_1.y,
                    hkdescriptor.perp_2_axle_in_a_1.z)
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = Blender.Mathutils.Vector(
                    hkdescriptor.perp_2_axle_in_a_2.x,
                    hkdescriptor.perp_2_axle_in_a_2.y,
                    hkdescriptor.perp_2_axle_in_a_2.z)
                # take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = Blender.Mathutils.CrossVecs(axis_y, axis_z)
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
                transform = Blender.Mathutils.Quaternion(
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
                    transform = Blender.Mathutils.Matrix(
                        self.bones_extra_matrix[niBone])
                    transform.invert()
                    pivot = pivot * transform
                    transform = transform.rotationPart()
                    axis_z = axis_z * transform
                    axis_x = axis_x * transform
                    break

            # cancel out bone tail translation
            if b_hkobj.parentbonename:
                pivot[1] -= b_hkobj.getParent().data.bones[
                    b_hkobj.parentbonename].length

            # cancel out object transform
            transform = Blender.Mathutils.Matrix(
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
            constr_matrix = Blender.Mathutils.Matrix(
                axis_x,
                Blender.Mathutils.CrossVecs(axis_z, axis_x),
                axis_z)
            constr_euler = constr_matrix.toEuler()
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXX] = constr_euler.x
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXY] = constr_euler.y
            b_constr[Blender.Constraint.Settings.CONSTR_RB_AXZ] = constr_euler.z
            # DEBUG
            assert((axis_x - Blender.Mathutils.Vector(1,0,0) * constr_matrix).length < 0.0001)
            assert((axis_z - Blender.Mathutils.Vector(0,0,1) * constr_matrix).length < 0.0001)

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

    def import_bounding_box(self, bbox):
        """Import a bounding box (BSBound, or NiNode with bounding box)."""
        # calculate bounds
        if isinstance(bbox, NifFormat.BSBound):
            me = Blender.Mesh.New('BSBound')
            minx = bbox.center.x - bbox.dimensions.x
            miny = bbox.center.y - bbox.dimensions.y
            minz = bbox.center.z - bbox.dimensions.z
            maxx = bbox.center.x + bbox.dimensions.x
            maxy = bbox.center.y + bbox.dimensions.y
            maxz = bbox.center.z + bbox.dimensions.z
        elif isinstance(bbox, NifFormat.NiNode):
            if not bbox.has_bounding_box:
                raise ValueError("Expected NiNode with bounding box.")
            me = Blender.Mesh.New('Bounding Box')
            # weirdly, bounding box center (bbox.bounding_box.translation)
            # is specified relative to the *parent* (not relative to bbox!)
            minx = bbox.bounding_box.translation.x - bbox.translation.x - bbox.bounding_box.radius.x
            miny = bbox.bounding_box.translation.y - bbox.translation.y - bbox.bounding_box.radius.y
            minz = bbox.bounding_box.translation.z - bbox.translation.z - bbox.bounding_box.radius.z
            maxx = bbox.bounding_box.translation.x - bbox.translation.x + bbox.bounding_box.radius.x
            maxy = bbox.bounding_box.translation.y - bbox.translation.y + bbox.bounding_box.radius.y
            maxz = bbox.bounding_box.translation.z - bbox.translation.z + bbox.bounding_box.radius.z
        else:
            raise TypeError("Expected BSBound or NiNode but got %s."
                            % bbox.__class__.__name__)

        # create mesh
        for x in [minx, maxx]:
            for y in [miny, maxy]:
                for z in [minz, maxz]:
                    me.verts.extend(x,y,z)
        me.faces.extend(
            [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

        # link box to scene and set transform
        if isinstance(bbox, NifFormat.BSBound):
            ob = self.scene.objects.new(me, 'BSBound')
        else:
            ob = self.scene.objects.new(me, 'Bounding Box')
            # XXX this is set in the import_branch method
            #ob.setMatrix(Blender.Mathutils.Matrix(
            #    *bbox.bounding_box.rotation.as_list()))
            #ob.setLocation(
            #    *bbox.bounding_box.translation.as_list())

        # set bounds type
        ob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
        ob.rbShapeBoundType = Blender.Object.RBShapes['BOX']
        ob.rbRadius = min(maxx, maxy, maxz)
        return ob

    def get_uv_layer_name(self, uvset):
        return "UVTex.%03i" % uvset if uvset != 0 else "UVTex"



    def import_kf_root(self, kf_root, root):
        """Merge kf into nif.

        *** Note: this function will eventually move to PyFFI. ***
        """

        self.logger.info("Merging kf tree into nif tree")

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
                self.logger.info(
                    "Animation for %s but no such node found in nif tree"
                    % nodename)
                continue
            # node found, now find the controller
            controllertype = controlledblock.get_controller_type()
            if not controllertype:
                self.logger.info(
                    "Animation for %s without controller type, so skipping"
                    % nodename)
                continue
            controller = self.find_controller(node, getattr(NifFormat, controllertype))
            if not controller:
                self.logger.info(
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
                    self.logger.warn("ignored NaN in interpolator translation")
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
            if self.IMPORT_BONEPRIORITIES:
                self.bone_priorities[nodename] = controlledblock.priority

        # DEBUG: save the file for manual inspection
        #niffile = open("C:\\test.nif", "wb")
        #NifFormat.write(niffile,
        #                version = 0x14000005, user_version = 11, roots = [root])

def config_callback(**config):
    """Called when config script is done. Starts and times import."""
    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Blender.Window.EditMode()
    Blender.Window.EditMode(0)
    Blender.Window.WaitCursor(1)
    t = Blender.sys.time()

    try:
        # run importer
        importer = NifImport(**config)
        importer.logger.info(
            'Finished in %.2f seconds' % (Blender.sys.time()-t))
    finally:
        Blender.Window.WaitCursor(0)
        if is_editmode:
            Blender.Window.EditMode(1)

def fileselect_callback(filename):
    """Called once file is selected. Starts config GUI."""
    global _CONFIG
    _CONFIG.run(NifConfig.TARGET_IMPORT, filename, config_callback)

if __name__ == '__main__':
    _CONFIG = NifConfig() # use global so gui elements don't go out of skope
    Blender.Window.FileSelector(fileselect_callback, "Import NIF", _CONFIG.config["IMPORT_FILE"])
