#!BPY

""" 
Name: 'NetImmerse/Gamebryo (.nif)'
Blender: 245
Group: 'Import'
Tip: 'Import NIF File Format (.nif)'
"""


__author__ = "The NifTools team, http://niftools.sourceforge.net/"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__bpydoc__ = """\
This script imports Netimmerse and Gamebryo .NIF files to Blender.
"""

import Blender
from Blender.Mathutils import *

from nif_common import NifConfig
from nif_common import NifFormat
from nif_common import __version__

# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007, NIF File Format Library and Tools
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

#
# A simple custom exception class.
#

class NifImportError(StandardError):
    pass

class NifImport:
    # class constants:
    # correction matrices list, the order is +X, +Y, +Z, -X, -Y, -Z
    BONE_CORRECTION_MATRICES = (\
                Matrix([ 0.0,-1.0, 0.0],[ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
                Matrix([ 1.0, 0.0, 0.0],[ 0.0, 1.0, 0.0],[ 0.0, 0.0, 1.0]),\
                Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0],[ 0.0,-1.0, 0.0]),\
                Matrix([ 0.0, 1.0, 0.0],[-1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
                Matrix([-1.0, 0.0, 0.0],[ 0.0,-1.0, 0.0],[ 0.0, 0.0, 1.0]),\
                Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0,-1.0],[ 0.0, 1.0, 0.0]))
    # identity matrix, for comparisons
    IDENTITY44 = Matrix([ 1.0,0.0, 0.0, 0.0],\
                [ 0.0, 1.0, 0.0, 0.0],\
                [ 0.0, 0.0, 1.0, 0.0],\
                [ 0.0, 0.0, 0.0, 1.0])
    # radians to degrees conversion constant
    R2D = 3.14159265358979/180.0
    
    def msg(self, message, level = 0):
        """Message wrapper."""
        if self.VERBOSITY >= level: print message

    def msgProgress(self, message, progbar = None):
        """Message wrapper for the Blender progress bar."""
        # update progress bar level
        if progbar is None:
            if self.progressBar > 0.89:
                # reset progress bar
                self.progressBar = 0
                Blender.Window.DrawProgressBar(0, message)
            self.progressBar += 0.1
        else:
            self.progressBar = progbar
        # draw the progress bar
        Blender.Window.DrawProgressBar(self.progressBar, message)

    def __init__(self, **config):
        """Main import function: open file and import all trees."""

        # initialize progress bar
        self.msgProgress("Initializing", progbar = 0)

        # store config settings
        for name, value in config.iteritems():
            setattr(self, name, value)

        # save file name
        self.filename = self.IMPORT_FILE[:]
        self.filepath = Blender.sys.dirname(self.filename)
        
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
        self.bonesExtraMatrix = {}

        # dictionary of bones that belong to a certain armature
        # maps NIF armature name to list of NIF bone name
        self.armatures = {}

        # Blender scene
        self.scene = Blender.Scene.GetCurrent()

        # selected objects
        # find and store this list now, as creating new objects adds them
        # to the selection list
        self.selectedObjects = [ob for ob in self.scene.objects.selected]
        
        # catch NifImportError
        try:
            # check that one armature is selected in 'import geometry + parent
            # to armature' mode
            if self.IMPORT_SKELETON == 2:
                if len(self.selectedObjects) != 1 or self.selectedObjects[0].getType() != 'Armature':
                    raise NifImportError("You must select exactly one armature in 'Import Geometry Only + Parent To Selected Armature' mode.")
            # open file for binary reading
            f = open(self.filename, "rb")
            try:
                # check if nif file is valid
                self.version, self.user_version = NifFormat.getVersion(f)
                if self.version >= 0:
                    # it is valid, so read the file
                    self.msg("NIF file version: 0x%08X"%self.version, 2)
                    self.msgProgress("Reading file")
                    root_blocks = NifFormat.read(self.version, self.user_version, f, verbose = 0)
                elif self.version == -1:
                    raise NifImportError("Unsupported NIF version.")
                else:
                    raise NifImportError("Not a NIF file.")
            finally:
                # the file has been read or an error occurred: close file
                f.close()

            self.msgProgress("Importing data")
            # calculate and set frames per second
            if self.IMPORT_ANIMATION:
                self.fps = self.getFramesPerSecond(root_blocks)
                self.scene.getRenderingContext().fps = self.fps
            # hack for corrupt better bodies meshes
            for block in root_blocks:
                root = block
                for b in [b for b in block.tree() if isinstance(b, NifFormat.NiGeometry)]:
                    if b.isSkin():
                        if root in [c for c in b.skinInstance.skeletonRoot.children]:
                            b.skinInstance.data.setTransform(root.getTransform() * b.skinInstance.data.getTransform())
                            b.skinInstance.skeletonRoot = root
                            # delete non-skeleton nodes if we're importing skeleton only
                            if self.IMPORT_SKELETON == 1:
                                nonbip_children = [ child for child in root.children if child.name[:6] != 'Bip01 ' ]
                                for child in nonbip_children: root.removeChild(child)
                self.msg("root block: %s" % (root.name), 3)
                self.importRoot(root)
        except NifImportError, e: # in that case, we raise a menu too
            print 'NifImportError: %s'%e
            Blender.Draw.PupMenu('ERROR%t|' + str(e))
            raise
        finally:
            # clear progress bar
            self.msgProgress("Finished", progbar = 1)
            # do a full scene update to ensure that transformations are applied
            self.scene.update(1)



    def importRoot(self, root_block):
        """Main import function."""
        # preprocessing:

        # check that this is not a kf file
        if isinstance(root_block, (NifFormat.NiSequence, NifFormat.NiSequenceStreamHelper)):
            raise NifImportError(".kf import not supported")

        # merge skeleton roots
        for niBlock in root_block.tree():
            if not isinstance(niBlock, NifFormat.NiGeometry): continue
            if not niBlock.isSkin(): continue
            merged, failed = niBlock.mergeSkeletonRoots()
            if merged:
                self.msg('reparented following blocks to skeleton root of ' + niBlock.name + ':', 2)
                self.msg([node.name for node in merged], 3)
            if failed:
                self.msg('WARNING: failed to reparent following blocks ' + niBlock.name + ':', 2)
                self.msg([node.name for node in failed], 3)

        # transform geometry into the rest pose
        if self.IMPORT_SENDBONESTOBINDPOS:
            for niBlock in root_block.tree():
                if not isinstance(niBlock, NifFormat.NiGeometry): continue
                if not niBlock.isSkin(): continue
                self.msg('sending bones of geometry ' + niBlock.name + " to their bind position", 2)
                niBlock.sendBonesToBindPosition()
        if self.IMPORT_APPLYSKINDEFORM:
            for niBlock in root_block.tree():
                if not isinstance(niBlock, NifFormat.NiGeometry): continue
                if not niBlock.isSkin(): continue
                self.msg('applying skin deformation on geometry ' + niBlock.name, 2)
                vertices, normals = niBlock.getSkinDeformation()
                for vold, vnew in zip(niBlock.data.vertices, vertices):
                    vold.x = vnew.x
                    vold.y = vnew.y
                    vold.z = vnew.z
        
        # sets the root block parent to None, so that when crawling back the script won't barf
        root_block._parent = None
        
        # set the block parent through the tree, to ensure I can always move backward
        self.set_parents(root_block)
        
        # scale tree
        root_block.applyScale(self.IMPORT_SCALE_CORRECTION)
        
        # mark armature nodes and bones
        self.markArmaturesBones(root_block)
        
        # import the keyframe notes
        if self.IMPORT_ANIMATION:
            self.fb_textkey(root_block)

        # read the NIF tree
        if self.is_armature_root(root_block):
            # special case 1: root node is skeleton root
            self.msg("%s is an armature root" % (root_block.name), 3)
            b_obj = self.read_branch(root_block)
        elif self.is_grouping_node(root_block):
            # special case 2: root node is grouping node
            self.msg("%s is a grouping node" % (root_block.name), 3)
            b_obj = self.read_branch(root_block)
        elif isinstance(root_block, NifFormat.NiTriBasedGeom):
            # trishape/tristrips root
            b_obj = self.read_branch(root_block)
        elif isinstance(root_block, NifFormat.NiNode):
            # root node is dummy scene node
            # process all its children
            for child in root_block.children:
                b_obj = self.read_branch(child)
        elif isinstance(root_block, NifFormat.NiCamera):
            self.msg('WARNING: skipped NiCamera root')
        else:
            raise NifImportError("don't know how to import nif file with root block of type '%s'"%root_block.__class__)

        # store bone matrix offsets for re-export
        if len(self.bonesExtraMatrix.keys()) > 0: self.fb_bonemat()
        # store original names for re-export
        if len(self.names) > 0: self.fb_fullnames()
        
        # parent selected meshes to imported skeleton
        if self.IMPORT_SKELETON == 1:
            b_obj.makeParentDeform(self.selectedObjects)

    def read_branch(self, niBlock):
        """Read the content of the current NIF tree branch to Blender
        recursively."""
        self.msgProgress("Importing data")
        if niBlock:
            if isinstance(niBlock, NifFormat.NiTriBasedGeom) and self.IMPORT_SKELETON == 0:
                # it's a shape node and we're not importing skeleton only
                # (IMPORT_SKELETON == 1) and not importing skinned geometries
                # only (IMPORT_SKELETON == 2)
                self.msg("building mesh in read_branch",3)
                return self.fb_mesh(niBlock)
            elif isinstance(niBlock, NifFormat.NiNode):
                children = niBlock.children
                if children:
                    # it's a parent node
                    # import object + children
                    if self.is_armature_root(niBlock):
                        # all bones in the tree are also imported by fb_armature
                        if self.IMPORT_SKELETON != 2:
                            b_obj = self.fb_armature(niBlock)
                        else:
                            b_obj = self.selectedObjects[0]
                            self.msg("merging nif tree '%s' with armature '%s'"%(niBlock.name, b_obj.name))
                            if niBlock.name != b_obj.name:
                                print("WARNING: taking nif block '%s' as armature '%s' but names do not match"%(niBlock.name, b_obj.name))
                        # now also do the meshes
                        self.read_armature_branch(b_obj, niBlock, niBlock)
                    else:
                        # is it a grouping node?
                        geom_group = self.is_grouping_node(niBlock)
                        if not geom_group:
                            # no grouping node, so import it as an empty
                            b_obj = self.fb_empty(niBlock)
                        else:
                            # node groups geometries, so import it as a mesh
                            print "joining geometries %s to single object '%s'"%([child.name for child in geom_group], niBlock.name)
                            b_obj = None
                            for child in geom_group:
                                b_obj = self.fb_mesh(child, group_mesh = b_obj, applytransform = True)
                            b_obj.name = self.fb_name(niBlock, 22)
                            # settings for collision node
                            if isinstance(niBlock, NifFormat.RootCollisionNode):
                                b_obj.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
                                b_obj.setDrawMode(32) # wire
                                b_obj.rbShapeBoundType = Blender.Object.RBShapes['POLYHEDERON']
                                # also remove duplicate vertices
                                b_mesh = b_obj.getData(mesh=True)
                                numverts = len(b_mesh.verts)
                                numdel = b_mesh.remDoubles(0.005) # 0.005 = 1/200
                                if numdel:
                                    self.msg('removed %i duplicate vertices (out of %i) from collision mesh'%(numdel, numverts), 3)
                        # import children that aren't part of the geometry group
                        b_children_list = []
                        children = [ child for child in niBlock.children if child not in geom_group ]
                        for child in children:
                            b_child_obj = self.read_branch(child)
                            if b_child_obj:
                                b_children_list.append(b_child_obj)
                        b_obj.makeParent(b_children_list)
                    b_obj.setMatrix(self.fb_matrix(niBlock))
                    # import the animations
                    if self.IMPORT_ANIMATION:
                        self.set_animation(niBlock, b_obj)
                        # import the extras
                        self.fb_textkey(niBlock)
                    return b_obj
            # all else is currently discarded
            print "todo: add cameras, lights, colliders and particle systems"
            return None

    def read_armature_branch(self, b_armature, niArmature, niBlock, group_mesh = None):
        """Reads the content of the current NIF tree branch to Blender
        recursively, as meshes parented to a given armature or parented
        to the closest bone in the armature. Note that
        niArmature must have been imported previously as an armature, along
        with all its bones. This function only imports meshes and armature ninodes."""
        # check if the block is non-null
        if not niBlock: return None, None
        branch_parent = self.get_closest_bone(niBlock, skelroot = niArmature)
        if not branch_parent:
            branch_parent = niArmature
        # is it a mesh?
        if isinstance(niBlock, NifFormat.NiTriBasedGeom) and self.IMPORT_SKELETON != 1:

            self.msg("building mesh %s in read_armature_branch" % (niBlock.name),3)
            # apply transform relative to the armature node
            return branch_parent, self.fb_mesh(niBlock, group_mesh = group_mesh, applytransform = True, relative_to = branch_parent)
        # is it another armature?
        elif self.is_armature_root(niBlock) and niBlock != niArmature:
            # an armature parented to this armature
            fb_arm = self.fb_armature(niBlock)
            # import the armature branch
            self.read_armature_branch(fb_arm, niBlock, niBlock)
            return branch_parent, fb_arm # the matrix will be set by the caller
        # is it a NiNode in the niArmature tree (possibly niArmature itself, on first call)?
        elif isinstance(niBlock, NifFormat.NiNode):
            children = niBlock.children
            if children:
                # check if geometries should be merged on import
                node_name = niBlock.name
                geom_group = self.is_grouping_node(niBlock)
                geom_other = [ child for child in niBlock.children if not child in geom_group ]
                b_objects = [] # list of (nif block, blender object) pairs
                # import grouped geometries
                if geom_group and self.IMPORT_SKELETON != 1:
                    print "joining geometries %s to single object '%s'"%([child.name for child in geom_group], node_name)
                    b_mesh = None
                    for child in geom_group:
                        b_mesh_branch_parent, b_mesh = self.read_armature_branch(b_armature, niArmature, child, group_mesh = b_mesh)
                        assert(b_mesh_branch_parent == branch_parent) # DEBUG
                    if b_mesh:
                        b_mesh.name = self.fb_name(niBlock)
                        b_objects.append((niBlock, branch_parent, b_mesh))
                # import other objects
                for child in geom_other:
                    b_obj_branch_parent, b_obj = self.read_armature_branch(b_armature, niArmature, child, group_mesh = None)
                    if b_obj:
                        b_objects.append((child, b_obj_branch_parent, b_obj))
                # fix transform and parentship
                for child, b_obj_branch_parent, b_obj in b_objects:
                    # note, b_obj is either a mesh or an armature
                    # check if it is parented to a bone or not
                    if b_obj_branch_parent != niArmature:
                        # object was parented to a bone
                        # first find the matrix in armature space we want
                        # the mesh to have
                        a_geom_matrix = self.fb_matrix(b_obj_branch_parent, relative_to = niArmature)
                        # next find the tail matrix of the bone parent
                        b_par_bone_name = self.names[b_obj_branch_parent] # blender bone name
                        b_par_bone = b_armature.data.bones[b_par_bone_name]
                        a_tail_matrix = b_par_bone.matrix['ARMATURESPACE'].copy()
                        a_tail_pos    = b_par_bone.tail['ARMATURESPACE']
                        a_tail_matrix[3][0] = a_tail_pos[0]
                        a_tail_matrix[3][1] = a_tail_pos[1]
                        a_tail_matrix[3][2] = a_tail_pos[2]
                        # fix the object matrix relative to the bone tail
                        b_obj.setMatrix(a_geom_matrix * a_tail_matrix.invert())
                        # make it parent of the bone
                        b_armature.makeParentBone([b_obj], self.names[b_obj_branch_parent])
                    else:
                        # mesh is parented to the armature
                        # the transform has already been applied
                        # still need to make it parent of the armature
                        # (if b_obj is an armature then this falls back to the usual parenting)
                        b_armature.makeParentDeform([b_obj])

        # anything else: throw away
        return None, None



    def fb_name(self, niBlock, max_length=22):
        """Get unique name for an object, preserving existing names.
        The maximum name length defaults to 22, since this is the
        maximum for Blender objects. Bone names can reach 32."""
        try:
            return self.names[niBlock]
        except KeyError:
            pass

        # find unique name for Blender to use
        uniqueInt = 0
        niName = niBlock.name
        # if name is empty, create something non-empty
        if not niName:
            if isinstance(niBlock, NifFormat.RootCollisionNode):
                niName = "collision"
            else:
                niName = "noname"
        # limit name length
        shortName = niName[:max_length-1]
        # make unique
        try:
            while Blender.Object.Get(shortName):
                shortName = '%s.%02d' % (niName[:max_length-4], uniqueInt)
                uniqueInt += 1
        except ValueError: # short name not found
            pass
        # save mapping
        self.names[niBlock] = shortName  # block niBlock has Blender name shortName
        self.blocks[shortName] = niBlock # Blender name shortName corresponds to niBlock
        return shortName
        
    def fb_matrix(self, niBlock, relative_to = None):
        """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
        return Matrix(*niBlock.getTransform(relative_to).asList())

    def fb_global_matrix(self, niBlock):
        """Retrieves a block's global transform matrix"""
        b_matrix = self.fb_matrix(niBlock)
        if niBlock._parent:
            return b_matrix * self.fb_global_matrix(niBlock._parent)
        return b_matrix


    def decompose_srt(self, m):
        """Decompose Blender transform matrix as a scale, rotation matrix, and translation vector."""
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
        assert(abs(b_scale[0]-b_scale[1]) < self.EPSILON)
        assert(abs(b_scale[1]-b_scale[2]) < self.EPSILON)
        b_scale = b_scale[0]
        # get rotation matrix
        b_rot = b_scale_rot * (1.0/b_scale)
        # get translation
        b_trans = m.translationPart()
        # done!
        return b_scale, b_rot, b_trans

    def fb_empty(self, niBlock):
        """Creates and returns a grouping empty."""
        shortName = self.fb_name(niBlock,22)
        b_empty = Blender.Object.New("Empty", shortName)
        b_empty.properties['longName'] = niBlock.name
        self.scene.objects.link(b_empty)
        return b_empty

    def fb_armature(self, niArmature):
        """Scans an armature hierarchy, and returns a whole armature.
        This is done outside the normal node tree scan to allow for positioning
        of the bones before skins are attached."""
        armature_name = self.fb_name(niArmature,22)
        armature_matrix_inverse = self.fb_global_matrix(niArmature)
        armature_matrix_inverse.invert()
        # store the matrix inverse within the niArmature, so that we won't have to recalculate it
        niArmature._invMatrix = armature_matrix_inverse
        b_armatureData = Blender.Armature.Armature()
        b_armatureData.name = armature_name
        b_armatureData.makeEditable()
        b_armatureData.drawAxes = True
        b_armatureData.envelopes = False
        b_armatureData.vertexGroups = True
        b_armatureData.drawType = Blender.Armature.STICK
        b_armature = self.scene.objects.new(b_armatureData, armature_name)

        # make armature editable and create bones
        b_armatureData.makeEditable()
        niChildBones = [child for child in niArmature.children if self.is_bone(child)]  
        for niBone in niChildBones:
            self.fb_bone(niBone, b_armature, b_armatureData, niArmature)
        b_armatureData.update()

        # The armature has been created in editmode,
        # now we are ready to set the bone keyframes.
        if self.IMPORT_ANIMATION:
            # create an action
            action = Blender.Armature.NLA.NewAction()
            action.setActive(b_armature)
            # go through all armature pose bones (http://www.elysiun.com/forum/viewtopic.php?t=58693)
            self.msgProgress('Importing Animations')
            for bone_idx, (bone_name, b_posebone) in enumerate(b_armature.getPose().bones.items()):
                # denote progress
                self.msgProgress('Animation: %s' % bone_name)
                
                self.msg('Importing animation for bone %s' % bone_name, 4)
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
                niBone = self.blocks[bone_name]
                bone_bm = self.fb_matrix(niBone) # base pose
                niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = self.decompose_srt(bone_bm)
                niBone_bind_rot_inv = Matrix(niBone_bind_rot)
                niBone_bind_rot_inv.invert()
                niBone_bind_quat_inv = niBone_bind_rot_inv.toQuat()
                # we also need the conversion of the original matrix to the new bone matrix, say X,
                # B' = X * B
                # (with B' the Blender matrix and B the NIF matrix) because we need that
                # C' * B' = X * C * B
                # and therefore
                # C' = X * C * B * inverse(B') = X * C * inverse(X), where X = B' * inverse(B)
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
                extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = self.decompose_srt(self.bonesExtraMatrix[niBone])
                extra_matrix_quat = extra_matrix_rot.toQuat()
                extra_matrix_rot_inv = Matrix(extra_matrix_rot)
                extra_matrix_rot_inv.invert()
                extra_matrix_quat_inv = extra_matrix_rot_inv.toQuat()
                # now import everything
                # ##############################
                kfc = self.find_controller(niBone, NifFormat.NiKeyframeController)
                if kfc and kfc.data:
                    # get keyframe data
                    kfd = kfc.data
                    assert(isinstance(kfd, NifFormat.NiKeyframeData))
                    translations = kfd.translations
                    scales = kfd.scales
                    # if we have translation keys, we make a dictionary of
                    # rot_keys and scale_keys, this makes the script work MUCH faster
                    # in most cases
                    if translations:
                        scale_keys_dict = {}
                        rot_keys_dict = {}
                    # add the keys
                    self.msg('Scale keys...', 4)
                    for scaleKey in scales.keys:
                        frame = 1+int(scaleKey.time * self.fps) # time 0.0 is frame 1
                        sizeVal = scaleKey.value
                        size = sizeVal / niBone_bind_scale # Schannel = Stotal / Sbind
                        b_posebone.size = Blender.Mathutils.Vector(size, size, size)
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE]) # this is very slow... :(
                        # fill optimizer dictionary
                        if translations:
                            scale_keys_dict[frame] = size
                    
                    # detect the type of rotation keys
                    rotationType = kfd.rotationType
                    if rotationType == 4:
                        # uses xyz rotation
                        self.msg('Rotation keys...(euler)', 4)
                        xyzRotations = kfd.xyzRotations
                        for key in xyzRotations:
                            frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                            keyVal = key.value
                            euler = Blender.Mathutils.Euler([keyVal.x, keyVal.y, keyVal.z])
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
                    else:
                        # uses quaternions
                        self.msg('Rotation keys...(quaternions)', 4)
                        quaternionKeys = kfd.quaternionKeys
                        for key in quaternionKeys:
                            frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                            keyVal = key.value
                            quat = Blender.Mathutils.Quaternion([keyVal.w, keyVal.x, keyVal.y, keyVal.z])
                            # beware, CrossQuats takes arguments in a counter-intuitive order:
                            # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                            quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
                            rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                            b_posebone.quat = rot
                            b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
                            # fill optimizer dictionary
                            if translations:
                                rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot)
        
                    self.msg('Translation keys...', 4)
                    for key in translations.keys:
                        frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                        keyVal = key.value
                        trans = Blender.Mathutils.Vector(keyVal.x, keyVal.y, keyVal.z)
                        locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0/niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                        # we need the rotation matrix at this frame (that's why we inserted the other keys first)
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
                            rot = Blender.Mathutils.Matrix([1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])
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
                        size = Blender.Mathutils.Matrix([sizeVal, 0.0, 0.0], [0.0, sizeVal, 0.0], [0.0, 0.0, sizeVal])
                        # now we can do the final calculation
                        loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0/extra_matrix_scale) # C' = X * C * inverse(X)
                        b_posebone.loc = loc
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
                    if translations:
                        del scale_keys_dict
                        del rot_keys_dict
        return b_armature

    def fb_bone(self, niBlock, b_armature, b_armatureData, niArmature):
        """Adds a bone to the armature in edit mode."""
        armature_matrix_inverse = niArmature._invMatrix
        # bone length for nubs and zero length bones
        nub_length = 5.0
        scale = self.IMPORT_SCALE_CORRECTION
        # bone name
        bone_name = self.fb_name(niBlock, 32)
        niChildBones = [child for child in niBlock.children if self.is_bone(child)]
        if self.is_bone(niBlock):
            # create bones here...
            b_bone = Blender.Armature.Editbone()
            # head: get position from niBlock
            armature_space_matrix = self.fb_global_matrix(niBlock) * armature_matrix_inverse
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
                child_matrices = [self.fb_global_matrix(child) * armature_matrix_inverse for child in niChildBones]
                b_bone_tail_x = sum([child_matrix[3][0] for child_matrix in child_matrices]) / len(child_matrices)
                b_bone_tail_y = sum([child_matrix[3][1] for child_matrix in child_matrices]) / len(child_matrices)
                b_bone_tail_z = sum([child_matrix[3][2] for child_matrix in child_matrices]) / len(child_matrices)
                # checking bone length
                dx = b_bone_head_x - b_bone_tail_x
                dy = b_bone_head_y - b_bone_tail_y
                dz = b_bone_head_z - b_bone_tail_z
                is_zero_length = abs(dx + dy + dz) * 200 < self.EPSILON
            elif self.IMPORT_REALIGN_BONES:
                # the correction matrix value is based on the children's head position
                # If these are missing I just set it as the same as the parent's
                m_correction = self.find_correction_matrix(niBlock._parent, niArmature)
            
            if is_zero_length:
                # this is a 0 length bone, to avoid it being removed I set a default minimum length
                if self.IMPORT_REALIGN_BONES or not self.is_bone(niBlock._parent):
                    # no parent bone, or bone is realigned with correction. I just set one random direction.
                    b_bone_tail_x = b_bone_head_x + (nub_length * scale)
                else:
                    # to keep things neat if bones aren't realigned on import I try and orient it as the vector between this
                    # bone's head and the parent's tail
                    parent_tail = b_armatureData.bones[self.names[niBlock._parent]].tail
                    dx = b_bone_head_x - parent_tail[0]
                    dy = b_bone_head_y - parent_tail[1]
                    dz = b_bone_head_z - parent_tail[2]
                    if abs(dx + dy + dz) * 200 < self.EPSILON:
                        # no offset from the parent, we follow the parent's orientation
                        parent_head = b_armatureData.bones[self.names[niBlock._parent]].head
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
            
            if self.IMPORT_REALIGN_BONES:
                # applies the corrected matrix explicitly
                b_bone.matrix = m_correction.resize4x4() * armature_space_matrix
            #else:
            #    b_bone.matrix = armature_space_matrix

            # set bone name and store the niBlock for future reference
            b_armatureData.bones[bone_name] = b_bone
            # calculate bone difference matrix; we will need this when importing animation
            old_bone_matrix_inv = Blender.Mathutils.Matrix(armature_space_matrix)
            old_bone_matrix_inv.invert()
            new_bone_matrix = Blender.Mathutils.Matrix(b_bone.matrix)
            new_bone_matrix.resize4x4()
            new_bone_matrix[3][0] = b_bone_head_x
            new_bone_matrix[3][1] = b_bone_head_y
            new_bone_matrix[3][2] = b_bone_head_z
            # stores any correction or alteration applied to the bone matrix
            self.bonesExtraMatrix[niBlock] = new_bone_matrix * old_bone_matrix_inv # new * inverse(old)
            # set bone children
            for niBone in niChildBones:
                b_child_bone =  self.fb_bone(niBone, b_armature, b_armatureData, niArmature)
                b_child_bone.parent = b_bone
            return b_bone
        return None


    def find_correction_matrix(self, niBlock, niArmature):
        """Returns the correction matrix for a bone."""
        armature_matrix_inverse = niArmature._invMatrix
        m_correction = self.IDENTITY44.rotationPart()
        if self.IMPORT_REALIGN_BONES and self.is_bone(niBlock):
            armature_space_matrix = self.fb_global_matrix(niBlock) * armature_matrix_inverse
            niChildBones = [child for child in niBlock.children if self.is_bone(child)]
            (sum_x, sum_y, sum_z, dummy) = armature_space_matrix[3]
            if len(niChildBones) > 0:
                child_local_matrices = [self.fb_matrix(child) for child in niChildBones]
                sum_x = sum([cm[3][0] for cm in child_local_matrices])
                sum_y = sum([cm[3][1] for cm in child_local_matrices])
                sum_z = sum([cm[3][2] for cm in child_local_matrices])
            listXYZ = [int(c * 200) for c in (sum_x, sum_y, sum_z, -sum_x, -sum_y, -sum_z)]
            idx_correction = listXYZ.index(max(listXYZ))
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


    def fb_texture(self, niSourceTexture):
        """Returns a Blender Texture object, and stores it in the
        self.textures dictionary."""

        if not niSourceTexture: return None
            
        try:
            return self.textures[niSourceTexture]
        except:
            pass
        
        b_image = None
        
        if niSourceTexture.useExternal:
            # the texture uses an external image file
            fn = niSourceTexture.fileName
            fn = fn.replace( '\\', Blender.sys.sep )
            fn = fn.replace( '/', Blender.sys.sep )
            # go searching for it
            importpath = Blender.sys.dirname(self.IMPORT_FILE)
            searchPathList = [importpath] + self.IMPORT_TEXTURE_PATH
            # if it looks like a Morrowind style path, use common sense to guess texture path
            meshes_index = importpath.lower().find("meshes")
            if meshes_index != -1:
                searchPathList.append(importpath[:meshes_index] + 'textures')
            # if it looks like a Civilization IV style path, use common sense to guess texture path
            art_index = importpath.lower().find("art")
            if art_index != -1:
                searchPathList.append(importpath[:art_index] + 'shared')
            # go through all texture search paths
            for texdir in searchPathList:
                texdir = texdir.replace( '\\', Blender.sys.sep )
                texdir = texdir.replace( '/', Blender.sys.sep )
                # go through all possible file names, try alternate extensions too
                # for linux, also try lower case versions of filenames
                texfns = reduce(lambda x,y: x+y, [[fn[:-4]+ext, fn[:-4].lower()+ext] for ext in ('.DDS','.dds','.PNG','.png','.TGA','.tga','.BMP','.bmp','.JPG','.jpg')])
                texfns = [fn, fn.lower()] + list(set(texfns))
                for texfn in texfns:
                     # now a little trick, to satisfy many Morrowind mods
                    if (texfn[:9].lower() == 'textures' + Blender.sys.sep) and (texdir[-9:].lower() == Blender.sys.sep + 'textures'):
                        tex = Blender.sys.join( texdir[:-9], texfn ) # strip one of the two 'textures' from the path
                    else:
                        tex = Blender.sys.join( texdir, texfn )
                    #self.msg("Searching %s" % tex, 3) # DEBUG
                    if Blender.sys.exists(tex) == 1:
                        # tries to load the file
                        b_image = Blender.Image.Load(tex)
                        # Blender 2.41 will return an image object even if the file format isn't supported,
                        # so to check if the image is actually loaded I need to force an error, hence the
                        # dummy = b_image.size line.
                        try:
                            dummy = b_image.size
                        except: # RuntimeError: couldn't load image data in Blender
                            b_image = None # not supported, delete image object
                        else:
                            # file format is supported
                            self.msg( "Found '%s' at %s" %(fn, tex), 3 )
                            del dummy
                            break
                if b_image:
                    break
            if b_image == None:
                self.msg("Texture '%s' not found and no alternate available" % fn, 2)
                b_image = Blender.Image.New(tex, 1, 1, 24) # create a stub
                b_image.filename = tex
        else:
            # the texture image is packed inside the nif -> extract it
            niPixelData = niSourceTexture.pixelData
            
            # we only load the first mipmap
            width = niPixelData.mipmaps[0].width
            height = niPixelData.mipmaps[0].height
            
            if niPixelData.pixelFormat == NifFormat.PixelFormat.PX_FMT_RGBA8:
                bpp = 24
            elif niPixelData.pixelFormat == NifFormat.PixelFormat.PX_FMT_RGB8:
                bpp = 32
            else:
                bpp = None

            if bpp == None: self.msg("unknown pixel format (%i), cannot extract texture"%niPixelData.pixelFormat, 1)

            if bpp != None:
                b_image = Blender.Image.New( "TexImg", width, height, bpp )
                
                pixels = niPixelData.pixelData.data
                pixeloffset = 0
                a = 0xff
                self.msgProgress("Image Extraction")
                for y in xrange( height ):
                    for x in xrange( width ):
                        # TODO delegate color extraction to generator in PyFFI/NIF
                        r = pixels[pixeloffset]
                        g = pixels[pixeloffset+1]
                        b = pixels[pixeloffset+2]
                        if bpp == 32:
                            a = pixels[pixeloffset+3]
                        b_image.setPixelI( x, (height-1)-y, ( r, g, b, a ) )
                        pixeloffset += bpp/8
        
        if b_image != None:
            # create a texture using the loaded image
            b_texture = Blender.Texture.New()
            b_texture.setType( 'Image' )
            b_texture.setImage( b_image )
            b_texture.imageFlags |= Blender.Texture.ImageFlags.INTERPOL
            b_texture.imageFlags |= Blender.Texture.ImageFlags.MIPMAP
            self.textures[niSourceTexture] = b_texture
            return b_texture
        else:
            self.textures[niSourceTexture] = None
            return None

    def fb_material(self, matProperty, textProperty, alphaProperty, specProperty):
        """Creates and returns a material."""
        # First check if material has been created before.
        try:
            material = self.materials[(matProperty, textProperty, alphaProperty, specProperty)]
            return material
        except KeyError:
            pass
        # use the material property for the name, other properties usually have
        # no name
        name = self.fb_name(matProperty)
        material = Blender.Material.New(name)
        # Sets the material colors
        # Specular color
        spec = matProperty.specularColor
        material.setSpecCol([spec.r, spec.g, spec.b])
        material.setSpec(1.0) # Blender multiplies specular color with this value
        # Diffuse color
        diff = matProperty.diffuseColor
        material.setRGBCol([diff.r, diff.g, diff.b])
        # Ambient & emissive color
        # We assume that ambient & emissive are fractions of the diffuse color.
        # If it is not an exact fraction, we average out.
        amb = matProperty.ambientColor
        emit = matProperty.emissiveColor
        b_amb = 0.0
        b_emit = 0.0
        b_n = 0
        if (diff.r > self.EPSILON):
            b_amb += amb.r/diff.r
            b_emit += emit.r/diff.r
            b_n += 1
        if (diff.g > self.EPSILON):
            b_amb += amb.g/diff.g
            b_emit += emit.g/diff.g
            b_n += 1
        if (diff.b > self.EPSILON):
            b_amb += amb.b/diff.b
            b_emit += emit.b/diff.b
            b_n += 1
        if (b_n > 0):
            b_amb /= b_n
            b_emit /= b_n
        if (b_amb > 1.0): b_amb = 1.0
        if (b_emit > 1.0): b_emit = 1.0
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
        baseTexture = None
        glowTexture = None
        if textProperty:
            baseTextureDesc = textProperty.baseTexture
            if baseTextureDesc:
                baseTexture = self.fb_texture(baseTextureDesc.source)
                if baseTexture:
                    # Sets the texture to use face UV coordinates.
                    texco = Blender.Texture.TexCo.UV
                    # Maps the texture to the base color channel.
                    mapto = Blender.Texture.MapTo.COL
                    # Sets the texture for the material
                    material.setTexture(0, baseTexture, texco, mapto)
                    mbaseTexture = material.getTextures()[0]
            glowTextureDesc = textProperty.glowTexture
            if glowTextureDesc:
                glowTexture = self.fb_texture(glowTextureDesc.source)
                if glowTexture:
                    # glow maps use alpha from rgb intensity
                    glowTexture.imageFlags |= Blender.Texture.ImageFlags.CALCALPHA
                    # Sets the texture to use face UV coordinates.
                    texco = Blender.Texture.TexCo.UV
                    # Maps the texture to the base color channel.
                    mapto = Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT
                    # Sets the texture for the material
                    material.setTexture(1, glowTexture, texco, mapto)
                    mglowTexture = material.getTextures()[1]
        # check transparency
        if alphaProperty:
            material.mode |= Blender.Material.Modes.ZTRANSP # enable z-buffered transparency
            # if the image has an alpha channel => then this overrides the material alpha value
            if baseTexture:
                if baseTexture.image.depth == 32 or baseTexture.image.size == [1,1]: # check for alpha channel in texture; if it's a stub then assume alpha channel
                    baseTexture.imageFlags |= Blender.Texture.ImageFlags.USEALPHA # use the alpha channel
                    mbaseTexture.mapto |=  Blender.Texture.MapTo.ALPHA # and map the alpha channel to transparency
                    # for proper display in Blender, we must set the alpha value
                    # to 0 and the "Var" slider in the texture Map To tab to the
                    # NIF material alpha value
                    material.setAlpha(0.0)
                    mbaseTexture.varfac = alpha
            # non-transparent glow textures have their alpha calculated from RGB
            # not sure what to do with glow textures that have an alpha channel
            # for now we ignore those alpha channels
        else:
            # no alpha property: force alpha 1.0 in Blender
            material.setAlpha(1.0)
        # check specularity
        if not specProperty:
            # no specular property: specular color is ignored
            # we do this by setting specularity zero
            material.setSpec(0.0)

        self.materials[(matProperty, textProperty, alphaProperty, specProperty)] = material
        return material

    def fb_mesh(self, niBlock, group_mesh = None, applytransform = False, relative_to = None):
        """Creates and returns a raw mesh, or appends geometry data to
        group_mesh. If group_mesh is not None, then applytransform must be
        True."""
        assert(isinstance(niBlock, NifFormat.NiTriBasedGeom))
        if group_mesh:
            b_mesh = group_mesh
            b_meshData = group_mesh.getData(mesh=True)
        else:
            # Mesh name -> must be unique, so tag it if needed
            b_name = self.fb_name(niBlock, 22)
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
            if group_mesh: raise NifImportError('BUG: cannot set matrix when importing meshes in groups; use applytransform = True')
            b_mesh.setMatrix(self.fb_matrix(niBlock, relative_to = relative_to))
        else:
            transform = self.fb_matrix(niBlock, relative_to = relative_to) # used later on

        # Mesh geometry data. From this I can retrieve all geometry info
        niData = niBlock.data
        if not niData:
            raise NifImportError("no ShapeData returned. Node name: %s " % b_name)
            
        # Vertices
        verts = niData.vertices
        
        # Faces
        tris = niData.getTriangles()
        
        # "Sticky" UV coordinates. these are transformed in Blender UV's
        # only the first UV set is loaded right now
        uvco = niData.uvSets
            
        # Vertex normals
        norms = niData.normals

        # Material
        # note that NIF files only support one material for each trishape
        matProperty = self.find_property(niBlock, NifFormat.NiMaterialProperty)
        if matProperty:
            # Texture
            textProperty = None
            if uvco:
                textProperty = self.find_property(niBlock, NifFormat.NiTexturingProperty)
            
            # Alpha
            alphaProperty = self.find_property(niBlock, NifFormat.NiAlphaProperty)
            
            # Specularity
            specProperty = self.find_property(niBlock, NifFormat.NiSpecularProperty)
            
            # create material and assign it to the mesh
            material = self.fb_material(matProperty, textProperty, alphaProperty, specProperty)
            b_mesh_materials = b_meshData.materials
            try:
                materialIndex = b_mesh_materials.index(material)
            except ValueError:
                materialIndex = len(b_mesh_materials)
                b_meshData.materials += [material]
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
                k = (int(v.x*200),int(v.y*200),int(v.z*200),\
                     int(n.x*200),int(n.y*200),int(n.z*200))
            else:
                k = (int(v.x*200),int(v.y*200),int(v.z*200))
            # see if we already added this guy, and if so, what index
            try:
                n_map_k = n_map[k] # this is the bottle neck... can we speed this up?
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
                # switching between edit mode and object mode, handled further)
                #if norms:
                #    mv = b_meshData.verts[b_v_index]
                #    n = norms[i]
                #    mv.no = Blender.Mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                v_map[i] = v_map[n_map_k] # NIF vertex i maps to Blender vertex v_map[n_map_k]
        # release memory
        del n_map

        # Adds the faces to the mesh
        f_map = [None]*len(tris)
        b_f_index = len(b_meshData.faces)
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
            f_map[i] = b_f_index # keep track of added faces, mapping NIF face index to Blender face index
            b_f_index += 1
        # at this point, deleted faces (degenerate or duplicate)
        # satisfy f_map[i] = None

        # Sets face smoothing and material
        for b_f_index in f_map:
            if b_f_index == None: continue
            f = b_meshData.faces[b_f_index]
            f.smooth = 1 if norms else 0
            f.mat = materialIndex

        # vertex colors
        vcol = niData.vertexColors
        
        if vcol:
            b_meshData.vertexColors = 1
            for f, b_f_index in zip(tris, f_map):
                if b_f_index == None: continue
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
        # Nif files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seams.
        # Essentially whenever an hard edge or an UV seam is present the mesh this is converted to an open mesh.
        # Blender also supports 'per face' UV coordinates, this could be a problem when exporting.
        # Also, NIF files support a series of texture sets, each one with its set of texture coordinates. For example
        # on a single "material" I could have a base texture, with a decal texture over it mapped on another set of UV
        # coordinates. I don't know if Blender can do the same.

        for uvSet in uvco:
            # Sets the face UV's for the mesh on. The NIF format only supports vertex UV's,
            # but Blender only allows explicit editing of face UV's, so I'll load vertex UV's like face UV's
            b_meshData.faceUV = 1
            b_meshData.vertexUV = 0
            for f, b_f_index in zip(tris, f_map):
                if b_f_index == None: continue
                uvlist = [ Vector(uvSet[vert_index].u, 1.0 - uvSet[vert_index].v) for vert_index in f ]
                b_meshData.faces[b_f_index].uv = tuple(uvlist)
       
        if material:
            # fix up vertex colors depending on whether we had textures in the material
            mbasetex = material.getTextures()[0]
            mglowtex = material.getTextures()[1]
            if b_meshData.vertexColors == 1:
                if mbasetex or mglowtex:
                    material.mode |= Blender.Material.Modes.VCOL_LIGHT # textured material: vertex colors influence lighting
                else:
                    material.mode |= Blender.Material.Modes.VCOL_PAINT # non-textured material: vertex colors incluence color

            # if there's a base texture assigned to this material sets it to be displayed in Blender's 3D view
            # but only if we have UV coordinates...
            if mbasetex and uvco:
                TEX = Blender.Mesh.FaceModes['TEX'] # face mode bitfield value
                imgobj = mbasetex.tex.getImage()
                if imgobj:
                    for b_f_index in f_map:
                        if b_f_index == None: continue
                        f = b_meshData.faces[b_f_index]
                        f.mode = TEX
                        f.image = imgobj

        # import skinning info, for meshes affected by bones
        # Adding groups to a mesh can be done only after this is already
        # linked to an object.
        skinInstance = niBlock.skinInstance
        if skinInstance:
            skinData = skinInstance.data
            bones = skinInstance.bones
            boneWeights = skinData.boneList
            for idx, bone in enumerate(bones):
                vertexWeights = boneWeights[idx].vertexWeights
                groupName = self.names[bone]
                if not groupName in b_meshData.getVertGroupNames():
                    b_meshData.addVertGroup(groupName)
                for skinWeight in vertexWeights:
                    vert = skinWeight.index
                    weight = skinWeight.weight
                    b_meshData.assignVertsToGroup(groupName, [v_map[vert]], weight, Blender.Mesh.AssignModes.REPLACE)
        
        # import morph controller
        if self.IMPORT_ANIMATION:
            morphCtrl = self.find_controller(niBlock, NifFormat.NiGeomMorpherController)
            if morphCtrl:
                morphData = morphCtrl.data
                if morphData.numMorphs:
                    # insert base key at frame 1
                    b_meshData.insertKey( 1, 'absolute' )
                    baseverts = morphData.morphs[0].vectors
                    b_ipo = Blender.Ipo.New( 'Key' , 'KeyIpo' )
                    b_meshData.key.ipo = b_ipo
                    for idxMorph in xrange(1, morphData.numMorphs):
                        morphverts = morphData.morphs[idxMorph].vectors
                        # for each vertex calculate the key position from base pos + delta offset
                        assert(len(baseverts) == len(morphverts) == len(v_map))
                        for bv, mv, b_v_index in zip(baseverts, morphverts, v_map):
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
                        # set up the ipo key curve
                        b_curve = b_ipo.addCurve('Key %i' % idxMorph)
                        # dunno how to set up the bezier triples -> switching to linear instead
                        b_curve.setInterpolation('Linear')
                        # select extrapolation
                        if ( morphCtrl.flags == 0x000c ):
                            b_curve.setExtrapolation( 'Constant' )
                        elif ( morphCtrl.flags == 0x0008 ):
                            b_curve.setExtrapolation( 'Cyclic' )
                        else:
                            print('WARNING: no idea which extrapolation to use, using constant')
                            b_curve.setExtrapolation( 'Constant' )
                        # set up the curve's control points
                        morphkeys = morphData.morphs[idxMorph].keys
                        for key in morphkeys:
                            x =  key.value
                            frame =  1+int(key.time * self.fps)
                            b_curve.addBezier( ( frame, x ) )
                        # finally: return to base position
                        for bv, b_v_index in zip(baseverts, v_map):
                            base = Blender.Mathutils.Vector(bv.x, bv.y, bv.z)
                            if applytransform:
                                base *= transform
                            b_meshData.verts[b_v_index].co[0] = base.x
                            b_meshData.verts[b_v_index].co[1] = base.y
                            b_meshData.verts[b_v_index].co[2] = base.z
     
        # recalculate normals
        b_meshData.calcNormals()
     
        return b_mesh



    # import animation groups
    def fb_textkey(self, niBlock):
        """Stores the text keys that define animation start and end in a text
        buffer, so that they can be re-exported. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""
        txk = self.find_extra(niBlock, NifFormat.NiTextKeyExtraData)
        if txk:
            # get animation text buffer, and clear it if it already exists
            try:
                animtxt = [txt for txt in Blender.Text.Get() if txt.getName() == "Anim"][0]
                animtxt.clear()
            except:
                animtxt = Blender.Text.New("Anim")
            
            frame = 1
            for key in txk.textKeys:
                newkey = str(key.value).replace('\r\n', '/').rstrip('/')
                frame = 1 + int(key.time * self.fps) # time 0.0 is frame 1
                animtxt.write('%i/%s\n'%(frame, newkey))
            
            # set start and end frames
            self.scene.getRenderingContext().startFrame(1)
            self.scene.getRenderingContext().endFrame(frame)
        
    def fb_bonemat(self):
        """Stores correction matrices in a text buffer so that the original
        alignment can be re-exported. In order for this to work it is necessary
        to mantain the imported names unaltered. Since the text buffer is
        cleared on each import only the last import will be exported
        correctly."""
        try:
            bonetxt = [txt for txt in Blender.Text.Get() if txt.getName() == "BoneExMat"][0]
            bonetxt.clear()
        except:
            bonetxt = Blender.Text.New("BoneExMat")
        for niBone in self.bonesExtraMatrix.keys():
            ln=''
            for row in self.bonesExtraMatrix[niBone]:
                ln='%s;%s,%s,%s,%s' % (ln, row[0],row[1],row[2],row[3])
            # print '%s/%s/%s\n' % (a, b, ln[1:])
            bonetxt.write('%s/%s\n' % (niBone.name, ln[1:]))
        

    def fb_fullnames(self):
        """Stores the original, long object names so that they can be
        re-exported. In order for this to work it is necessary to mantain the
        imported names unaltered. Since the text buffer is cleared on each
        import only the last import will be exported correctly."""
        # get the names text buffer
        try:
            namestxt = [txt for txt in Blender.Text.Get() if txt.getName() == "FullNames"][0]
            namestxt.clear()
        except:
            namestxt = Blender.Text.New("FullNames")
        for block, shortname in self.names.iteritems():
            if block.name and shortname != block.name:
                namestxt.write('%s;%s\n'% (shortname, block.name))

    def getFramesPerSecond(self, roots):
        """Scan all blocks and return a reasonable number for FPS."""
        # find all key times
        key_times = []
        for root in roots:
            for kfd in root.tree(block_type = NifFormat.NiKeyframeData):
                key_times.extend([key.time for key in kfd.translations.keys])
                key_times.extend([key.time for key in kfd.scales.keys])
                key_times.extend([key.time for key in kfd.quaternionKeys])
                key_times.extend([key.time for key in kfd.xyzRotations[0].keys])
                key_times.extend([key.time for key in kfd.xyzRotations[1].keys])
                key_times.extend([key.time for key in kfd.xyzRotations[2].keys])
        # not animated, return a reasonable default
        if not key_times:
            return 30
        # calculate FPS
        fps = 30
        lowestDiff = sum([abs(int(time*fps)-(time*fps)) for time in key_times])
        # for fps in xrange(1,120): #disabled, used for testing
        for testFps in [20, 25, 35]:
            diff = sum([abs(int(time*testFps)-(time*testFps)) for time in key_times])
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
            if kfd.rotationType == 4:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.xyzRotations.keys])
            else:
                _ANIMATION_DATA.extend([{'data': key, 'block': niBlock, 'frame': None} for key in kfd.quaternionKeys])
        
        # set the frames in the _ANIMATION_DATA list
        for key in _ANIMATION_DATA:
            # time 0 is frame 1
            key['frame'] = 1 + int(key['data'].time * self.fps)

        # sort by frame, I need this later
        _ANIMATION_DATA.sort(lambda key1, key2: cmp(key1['frame'], key2['frame']))
        """


    def find_controller(self, niBlock, controllerType):
        """Find a controller."""
        ctrl = niBlock.controller
        while ctrl:
            if isinstance(ctrl, controllerType):
                break
            ctrl = ctrl.nextController
        return ctrl

    def find_property(self, niBlock, propertyType):
        """Find a property."""
        prop = [p for p in niBlock.properties if isinstance(p, propertyType)]
        if prop:
            return prop[0]
        return None


    def find_extra(self, niBlock, extratype):
        """Find extra data."""
        # pre-10.x.x.x system: extra data chain
        extra = niBlock.extraData
        while extra:
            if isinstance(extra, extratype):
                break
            extra = extra.nextExtraData
        if extra:
            return extra

        # post-10.x.x.x system: extra data list
        for extra in niBlock.extraDataList:
            if isinstance(extra, extratype):
                return extra
        return None

    def set_parents(self, niBlock):
        """Set the parent block recursively through the tree, to allow
        crawling back as needed."""
        if isinstance(niBlock, NifFormat.NiNode):
            # list of non-null children
            children = [child for child in niBlock.children if child]
            for child in children:
                child._parent = niBlock
                self.set_parents(child)

    def markArmaturesBones(self, niBlock):
        """Mark armatures and bones by peeking into NiSkinInstance blocks."""
        # case where we import skeleton only: do all NiNode's as bones
        if self.IMPORT_SKELETON == 1:
            if not isinstance(niBlock, NifFormat.NiNode):
                raise NifImportError('cannot import skeleton: root is not a NiNode')
            # for morrowind, take the Bip01 node to be the skeleton root
            if self.version == 0x04000002:
                skelroot = niBlock.find(block_name = 'Bip01', block_type = NifFormat.NiNode)
                if not skelroot: skelroot = niBlock
            else:
                skelroot = niBlock
            if not self.armatures.has_key(skelroot):
                self.armatures[skelroot] = []
            self.msg("selecting node '%s' as skeleton root"%skelroot.name)
            # add bones
            for bone in skelroot.tree():
                if bone == skelroot: continue
                if not isinstance(bone, NifFormat.NiNode): continue
                if self.is_grouping_node(bone): continue
                self.armatures[skelroot].append(bone)
            return # done!

        # attaching to selected armature -> first identify armature and bones
        elif self.IMPORT_SKELETON == 2 and not self.armatures:
            skelroot = niBlock.find(block_name = self.selectedObjects[0].name)
            if not skelroot:
                raise NifImportError("nif has no armature '%s'"%self.selectedObjects[0].name)
            self.msg("identified '%s' as armature" % skelroot.name,3)
            self.armatures[skelroot] = []
            for bone_name in self.selectedObjects[0].data.bones.keys():
                bone_block = skelroot.find(block_name = bone_name)
                # add it to the name list if there is a bone with that name
                if bone_block:
                    self.msg("identified nif block '%s' with bone in selected armature"%bone_name)
                    self.names[bone_block] = bone_name
                    self.armatures[skelroot].append(bone_block)
                    self.complete_bone_tree(bone_block, skelroot)

        # search for all NiTriShape or NiTriStrips blocks...
        if isinstance(niBlock, NifFormat.NiTriBasedGeom):
            # yes, we found one, get its skin instance
            if niBlock.isSkin():
                self.msg("skin found on block '%s'" % niBlock.name,3)
                # it has a skin instance, so get the skeleton root
                # which is an armature only if it's not a skinning influence
                # so mark the node to be imported as an armature
                skininst = niBlock.skinInstance
                skelroot = skininst.skeletonRoot
                if self.IMPORT_SKELETON == 0:
                    if not self.armatures.has_key(skelroot):
                        self.armatures[skelroot] = []
                        self.msg("'%s' is an armature" % skelroot.name,3)
                elif self.IMPORT_SKELETON == 2:
                    if not self.armatures.has_key(skelroot):
                        #self.armatures[skelroot] = []
                        #self.msg("'%s' is an armature" % skelroot.name,3)
                        raise NifImportError("nif structure incompatible with '%s' as armature: \nnode '%s' has '%s' as armature"%(self.selectedObjects[0].name, niBlock.name, skelroot.name))

                for i, boneBlock in enumerate(skininst.bones):
                    if not boneBlock in self.armatures[skelroot]:
                        self.armatures[skelroot].append(boneBlock)
                        self.msg("'%s' is a bone of armature '%s'" % (boneBlock.name, skelroot.name), 3)
                    # now we "attach" the bone to the armature:
                    # we make sure all NiNodes from this bone all the way
                    # down to the armature NiNode are marked as bones
                    self.complete_bone_tree(boneBlock, skelroot)

        # continue down the tree
        for child in niBlock.getRefs():
            if not isinstance(child, NifFormat.NiAVObject): continue # skip blocks that don't have transforms
            self.markArmaturesBones(child)

    def complete_bone_tree(self, bone, skelroot):
        """Make sure that the bones actually form a tree all the way down to
        the armature node. Call this function on all bones of a skin instance."""
        # we must already have marked this one as a bone
        assert self.armatures.has_key(skelroot) # debug
        assert bone in self.armatures[skelroot] # debug
        # get the node parent, this should be marked as an armature or as a bone
        boneparent = bone._parent
        if boneparent != skelroot:
            # parent is not the skeleton root
            if not boneparent in self.armatures[skelroot]:
                # neither is it marked as a bone: so mark the parent as a bone
                self.armatures[skelroot].append(boneparent)
                # store the coordinates for realignement autodetection 
                self.msg("'%s' is a bone of armature '%s'"%(boneparent.name, skelroot.name),3)
            # now the parent is marked as a bone
            # recursion: complete the bone tree,
            # this time starting from the parent bone
            self.complete_bone_tree(boneparent, skelroot)

    def is_bone(self, niBlock):
        """Tests a NiNode to see if it's a bone."""
        if not niBlock : return False
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
        """Retrieves the Blender object matching the block. This is a workaround to retrieve a bone by name"""
        if self.is_bone(niBlock):
            boneName = _NAMES[niBlock]
            armatureName = None
            for armatureBlock, boneBlocks in self.armatures.iteritems():
                if niBlock in boneBlocks:
                    armatureName = self.names[armatureBlock]
                    break
            armatureObject = Blender.Object.Get(armatureName)
            armatureData = armatureObject.getData()
            bone = armatureData.bones[boneName]
            return bone
        else:
            return Blender.Object.Get(self.names[niBlock])

    def is_grouping_node(self, niBlock):
        """Determine whether node is grouping node.
        Returns the children which are grouped, or empty list if it is not a
        grouping node."""
        # check that it is a ninode
        if not isinstance(niBlock, NifFormat.NiNode): return []
        # root collision node: join everything
        if isinstance(niBlock, NifFormat.RootCollisionNode):
            return [ child for child in niBlock.children if isinstance(child, NifFormat.NiTriBasedGeom) ]
        # check that node has name
        node_name = niBlock.name
        if not node_name: return []
        # get all geometry children
        return [ child for child in niBlock.children if isinstance(child, NifFormat.NiTriBasedGeom) and child.name.find(node_name) != -1 ]

    """
    #can't retrieve bone ipo's?
    def import_animation(self):
        global _ANIMATION_DATA
        #store all keys in a flat list
        keyFrameList = []
        # _ANIMATION_DATA is sorted by frame already
        for key in _ANIMATION_DATA:
            niBlock = key['block']
            b_obj = get_blender_object(niBlock)
            b_ipo = b_obj.getIpo()
            if b_ipo == None:
                if is_bone(niBlock):
                    b_ipo = Blender.Ipo.New('Pose', b_obj.name)
                else:
                    b_ipo = Blender.Ipo.New('Object', b_obj.name)
                b_obj.setIpo(b_ipo)
                
            print key
    """

    def set_animation(self, niBlock, b_obj):
        """Load basic animation info for this object."""
        kfc = self.find_controller(niBlock, NifFormat.NiKeyframeController)
        if kfc and kfc.data:
            # create an Ipo for this object
            b_ipo = b_obj.getIpo()
            if b_ipo == None:
                b_ipo = Blender.Ipo.New('Object', b_obj.name)
                b_obj.setIpo(b_ipo)
            # denote progress
            self.msgProgress("Animation")
            # get keyframe data
            kfd = kfc.data
            assert(isinstance(kfd, NifFormat.NiKeyframeData))
            #get the animation keys
            translations = kfd.translations
            scales = kfd.scales
            # add the keys
            self.msg('Scale keys...', 4)
            for key in scales.keys:
                frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                b_obj.SizeX = key.value
                b_obj.SizeY = key.value
                b_obj.SizeZ = key.value
                b_obj.insertIpoKey(Blender.Object.SIZE)

            # detect the type of rotation keys
            rotationType = kfd.rotationType
            if rotationType == 4:
                # uses xyz rotation
                xyzRotations = kfd.xyzRotations
                self.msg('Rotation keys...(euler)', 4)
                for key in xyzRotations:
                    frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                    Blender.Set('curframe', frame)
                    b_obj.RotX = key.value.x * self.R2D
                    b_obj.RotY = key.value.y * self.R2D
                    b_obj.RotZ = key.value.z * self.R2D
                    b_obj.insertIpoKey(Blender.Object.ROT)           
            else:
                # uses quaternions
                quaternionKeys = kfd.quaternionKeys
                self.msg('Rotation keys...(quaternions)', 4)
                for key in quaternionKeys:
                    frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                    Blender.Set('curframe', frame)
                    rot = Blender.Mathutils.Quaternion(key.value.w, key.value.x, key.value.y, key.value.z).toEuler()
                    b_obj.RotX = rot.x * self.R2D
                    b_obj.RotY = rot.y * self.R2D
                    b_obj.RotZ = rot.z * self.R2D
                    b_obj.insertIpoKey(Blender.Object.ROT)
            
            self.msg('Translation keys...', 4)
            for key in translations.keys:
                frame = 1+int(key.time * self.fps) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                b_obj.LocX = key.value.x
                b_obj.LocY = key.value.y
                b_obj.LocZ = key.value.z
                b_obj.insertIpoKey(Blender.Object.LOC)
                
            Blender.Set('curframe', 1)

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
        NifImport(**config)
    finally:
        # finish import
        print 'nif import finished in %.2f seconds' % (Blender.sys.time()-t)
        Blender.Window.WaitCursor(0)
        if is_editmode: Blender.Window.EditMode(1)

def fileselect_callback(filename):
    """Called once file is selected. Starts config GUI."""
    global _config
    _config.run(NifConfig.TARGET_IMPORT, filename, config_callback)

if __name__ == '__main__':
    _config = NifConfig() # use global so gui elements don't go out of skope
    Blender.Window.FileSelector(fileselect_callback, "Import NIF", _config.config["IMPORT_FILE"])
