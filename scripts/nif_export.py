#!BPY

"""
Name: 'NetImmerse/Gamebryo (.nif & .kf)'
Blender: 245
Group: 'Export'
Tooltip: 'Export NIF File Format (.nif & .kf)'
"""

__author__ = "The NifTools team, http://niftools.sourceforge.net/"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__bpydoc__ = """\
This script exports Netimmerse and Gamebryo .nif files from Blender.
"""

import Blender

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

class NifExportError(StandardError):
    pass

# main export class
class NifExport:
    # map blending modes to apply modes
    APPLYMODE = {
        Blender.Texture.BlendModes["MIX"] : NifFormat.ApplyMode.APPLY_MODULATE,
        Blender.Texture.BlendModes["LIGHTEN"] : NifFormat.ApplyMode.APPLY_HILIGHT,
        Blender.Texture.BlendModes["MULTIPLY"] : NifFormat.ApplyMode.APPLY_HILIGHT2
    }

    def msg(self, message, level=2):
        """Wrapper for debug messages."""
        if self.VERBOSITY and level <= self.VERBOSITY:
            print message

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

    def rebuildBonesExtraMatrices(self):
        """Recover bone extra matrices."""
        try:
            bonetxt = Blender.Text.Get('BoneExMat')
        except NameError:
            return
        # Blender bone names are unique so we can use them as keys.
        for ln in bonetxt.asLines():
            if len(ln)>0:
                b, m = ln.split('/')
                # Matrices are stored inverted for easier math later on.
                try:
                    mat = Blender.Mathutils.Matrix(*[[float(f) for f in row.split(',')] for row in m.split(';')])
                except:
                    raise NifExportError('Syntax error in BoneExMat buffer.')
                mat.invert()
                self.bonesExtraMatrixInv[b] = mat # X^{-1}

    def rebuildFullNames(self):
        """Recovers the full object names from the text buffer and rebuilds
        the names dictionary."""
        try:
            namestxt = Blender.Text.Get('FullNames')
        except NameError:
            return
        for ln in namestxt.asLines():
            if len(ln)>0:
                name, fullname = ln.split(';')
                self.names[name] = fullname


    def getUniqueName(self, blender_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object."""
        unique_name = "default_name"
        if blender_name != None:
            unique_name = blender_name
        if unique_name in self.blockNames or unique_name in self.names.values():
            unique_int = 0
            old_name = unique_name
            while unique_name in self.blockNames or unique_name in self.names.values():
                unique_name = '%s.%02d' % (old_name, unique_int)
                unique_int +=1
        self.blockNames.append(unique_name)
        self.names[blender_name] = unique_name
        return unique_name

    def getFullName(self, blender_name):
        """Returns the original imported name if present, or the name by which
        the object was exported already."""
        try:
            return self.names[blender_name]
        except KeyError:
            return self.getUniqueName(blender_name)

    def __init__(self, **config):
        """Main export function."""

        # preparation:
        #--------------
        self.msgProgress("Initializing", progbar = 0)
        
        # store configuration in self
        for name, value in config.iteritems():
            setattr(self, name, value)

        # save file name
        self.filename = self.EXPORT_FILE[:]
        self.filepath = Blender.sys.dirname(self.filename)
        self.filebase, self.fileext = Blender.sys.splitext(
            Blender.sys.basename(self.filename))

        # variables
        self.progressBar = 0
        # list of all exported blocks
        self.blocks = []
        # maps Blender names to previously imported names from the FullNames
        # buffer (see self.rebuildFullNames())
        self.names = {}
        # keeps track of names of exported blocks, to make sure they are unique
        self.blockNames = []

        # dictionary of bones, maps Blender bone name to matrix that maps the
        # NIF bone matrix on the Blender bone matrix
        # Recall from the import script
        #   B' = X * B,
        # where B' is the Blender bone matrix, and B is the NIF bone matrix,
        # both in armature space. So to restore the NIF matrices we need to do
        #   B = X^{-1} * B'
        # Hence, we will restore the X's, invert them, and store those inverses in the
        # following dictionary.
        self.bonesExtraMatrixInv = {}

        try: # catch export errors

            # find nif version to write
            try:
                self.version = NifFormat.versions[self.EXPORT_VERSION]
                self.msg("Writing NIF version 0x%08X"%self.version)
            except KeyError:
                self.version = NifFormat.games[self.EXPORT_VERSION][-1] # select highest nif version that the game supports
                self.msg("Writing %s NIF (version 0x%08X)"%(self.EXPORT_VERSION,self.version))

            if self.EXPORT_ANIMATION == 0:
                self.msg("Exporting geometry and animation")
            elif self.EXPORT_ANIMATION == 1:
                self.msg("Exporting geometry only") # for morrowind: everything except keyframe controllers
            elif self.EXPORT_ANIMATION == 2:
                self.msg("Exporting animation only (as .kf file)") # for morrowind: only keyframe controllers

            for ob in Blender.Object.Get():
                # armatures should not be in rest position
                if ob.getType() == 'Armature':
                    ob.data.restPosition = False # ensure we get the mesh vertices in animation mode, and not in rest position!
                    if (ob.data.envelopes):
                        print """'%s': Cannot export envelope skinning.
If you have vertex groups, turn off envelopes.
If you don't have vertex groups, select the bones one by one
press W to convert their envelopes to vertex weights,
and turn off envelopes."""%ob.getName()
                        raise NifExportError("'%s': Cannot export envelope skinning. Check console for instructions."%ob.getName())

                # check for non-uniform transforms
                # (lattices are not exported so ignore them as they often tend
                # to have non-uniform scaling)
                if ob.getType() != 'Lattice':
                    try:
                        self.decomposeSRT(ob.getMatrix('localspace'))
                    except NifExportError: # non-uniform scaling
                        raise NifExportError("Non-uniform scaling not supported. Workaround: apply size and rotation (CTRL-A) on '%s'."%ob.name)

            # extract some useful scene info
            self.scene = Blender.Scene.GetCurrent()
            context = self.scene.getRenderingContext()
            self.fspeed = 1.0 / context.framesPerSec()
            self.fstart = context.startFrame()
            self.fend = context.endFrame()
            
            if self.EXPORT_VERSION in ['Oblivion', 'Civilization IV']:
                root_name = 'Scene Root'
            else:
                root_name = self.filebase
     
            # get the root object from selected object
            # only export empties, meshes, and armatures
            if (Blender.Object.GetSelected() == None):
                raise NifExportError("Please select the object(s) that you wish to export, and run this script again.")
            root_objects = set()
            export_types = ('Empty','Mesh','Armature')
            for root_object in [ob for ob in Blender.Object.GetSelected() if ob.getType() in export_types]:
                while (root_object.getParent() != None):
                    root_object = root_object.getParent()
                if root_object.getType() not in export_types:
                    raise NifExportError("Root object (%s) must be an 'Empty', 'Mesh', or 'Armature' object."%root_object.getName())
                root_objects.add(root_object)

            # smoothen seams of objects
            if self.EXPORT_SMOOTHOBJECTSEAMS:
                # get shared vertices
                self.msg("smoothing seams between objects...")
                vdict = {}
                for ob in [ob for ob in self.scene.objects if ob.getType() == 'Mesh']:
                    mesh = ob.getData(mesh=1)
                    #for v in mesh.verts:
                    #    v.sel = False
                    for f in mesh.faces:
                        for v in f.verts:
                            vkey = (int(v.co[0]*200), int(v.co[1]*200), int(v.co[2]*200))
                            try:
                                vdict[vkey].append((v, f, mesh))
                            except KeyError:
                                vdict[vkey] = [(v, f, mesh)]
                # set normals on shared vertices
                nv = 0
                for vlist in vdict.itervalues():
                    if len(vlist) <= 1: continue # not shared
                    meshes = set([mesh for v, f, mesh in vlist])
                    if len(meshes) <= 1: continue # not shared
                    # take average of all face normals of faces that have this vertex
                    norm = Blender.Mathutils.Vector(0,0,0)
                    for v, f, mesh in vlist:
                        norm += f.no
                    norm.normalize()
                    # remove outliers (fixes better bodies issue)
                    # first calculate fitness of each face
                    fitlist = [Blender.Mathutils.DotVecs(f.no, norm) for v, f, mesh in vlist]
                    bestfit = max(fitlist)
                    # recalculate normals only taking into account well-fitting faces
                    norm = Blender.Mathutils.Vector(0,0,0)
                    for (v, f, mesh), fit in zip(vlist, fitlist):
                        if fit >= bestfit - 0.2:
                            norm += f.no
                    norm.normalize()
                    # save normal of this vertex
                    for v, f, mesh in vlist:
                        v.no = norm
                        #v.sel = True
                    nv += 1
                self.msg("fixed normals on %i vertices"%nv)

            ## TODO use Blender actions for animation groups
            # check for animation groups definition in a text buffer 'Anim'
            try:
                animtxt = Blender.Text.Get("Anim")
            except NameError:
                animtxt = None
                    
            # rebuild the bone extra matrix dictionary from the 'BoneExMat' text buffer
            self.rebuildBonesExtraMatrices()
            
            # rebuild the full name dictionary from the 'FullNames' text buffer 
            self.rebuildFullNames()
            
            # export nif:
            #------------
            self.msgProgress("Exporting")
            
            # create a nif object
            
            # export the root node (the name is fixed later to avoid confusing the
            # exporter with duplicate names)
            root_block = self.exportNode(None, 'none', None, '')
            
            # export objects
            self.msg("Exporting objects")
            for root_object in root_objects:
                # export the root objects as a NiNodes; their children are exported as well
                # note that localspace = worldspace, because root objects have no parents
                self.exportNode(root_object, 'localspace', root_block, root_object.getName())

            # post-processing:
            #-----------------

            # if we exported animations, but no animation groups are defined, define a default animation group
            self.msg("Checking animation groups")
            if not animtxt:
                has_controllers = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiObjectNET): # has it a controller field?
                        if block.controller:
                            has_controllers = True
                            break
                if has_controllers:
                    self.msg("Defining default animation group")
                    # write the animation group text buffer
                    animtxt = Blender.Text.New("Anim")
                    animtxt.write("%i/Idle: Start/Idle: Loop Start\n%i/Idle: Loop Stop/Idle: Stop"%(self.fstart,self.fend))

            # animations without keyframe animations crash the TESCS
            # if we are in that situation, add a trivial keyframe animation
            self.msg("Checking controllers")
            if animtxt:
                has_keyframecontrollers = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiKeyframeController):
                        has_keyframecontrollers = True
                        break
                if not has_keyframecontrollers:
                    self.msg("Defining dummy keyframe controller")
                    # add a trivial keyframe controller on the scene root
                    self.exportKeyframes(None, 'localspace', root_block)
            
            # export animation groups
            if animtxt:
                anim_textextra = self.exportAnimGroups(animtxt, root_block)

            # activate oblivion collision and physics
            if self.EXPORT_VERSION == 'Oblivion':
                hascollision = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkCollisionObject):
                       hascollision = True
                       break
                if hascollision:
                    bsx = self.createBlock("BSXFlags")
                    bsx.name = 'BSX'
                    bsx.integerData = self.EXPORT_OB_BSXFLAGS # enable collision
                    root_block.addExtraData(bsx)
                # update rigid body center of gravity
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkRigidBody):
                        block.updateMassCenterInertia(
                            mass = self.EXPORT_OB_MASS,
                            solid = self.EXPORT_OB_SOLID)

                # many Oblivion nifs have a UPB, but export is disabled as
                # they do not seem to affect anything in the game
                #upb = self.createBlock("NiStringExtraData")
                #upb.name = 'UPB'
                #upb.stringData = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                #root_block.addExtraData(upb)

            # add vertex color and zbuffer properties for civ4
            if self.EXPORT_VERSION == 'Civilization IV':
                vcol = self.createBlock("NiVertexColorProperty")
                vcol.flags = 1
                vcol.vertexMode = 0
                vcol.lightingMode = 1
                zbuf = self.createBlock("NiZBufferProperty")
                zbuf.flags = 15
                zbuf.function = 3
                root_block.addProperty(vcol)
                root_block.addProperty(zbuf)

            if self.EXPORT_FLATTENSKIN:
                # (warning: trouble if armatures parent other armatures or
                # if bones parent geometries, or if object is animated)
                # flatten skins
                skelroots = set()
                affectedbones = []
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiGeometry) and block.isSkin():
                        self.msg("Flattening skin on geometry %s"%block.name)
                        affectedbones.extend(block.flattenSkin())
                        skelroots.add(block.skinInstance.skeletonRoot)
                # remove NiNodes that do not affect skin
                for skelroot in skelroots:
                    self.msg("Removing unused NiNodes in '%s'"%skelroot.name)
                    skelrootchildren = [child for child in skelroot.children if (not isinstance(child, NifFormat.NiNode)) or (child in affectedbones)]
                    skelroot.numChildren = len(skelrootchildren)
                    skelroot.children.updateSize()
                    for i, child in enumerate(skelrootchildren):
                        skelroot.children[i] = child

            # apply scale
            if abs(self.EXPORT_SCALE_CORRECTION - 1.0) > NifFormat._EPSILON:
                self.msg("Applying scale correction %f"%self.EXPORT_SCALE_CORRECTION)
                root_block.applyScale(self.EXPORT_SCALE_CORRECTION)

            # generate mopps (must be done after applying scale!)
            if self.EXPORT_VERSION == 'Oblivion':
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkMoppBvTreeShape):
                       self.msg("Generating mopp...")
                       block.updateOriginScale()
                       block.updateMopp()
                       #print "=== DEBUG: MOPP TREE ==="
                       #block.parseMopp(verbose = True)
                       #print "=== END OF MOPP TREE ==="


            # delete original scene root if a scene root object was already defined
            if (root_block.numChildren == 1) and (root_block.children[0].name in ['Scene Root', 'Bip01']):
                self.msg("Making '%s' the root block"%root_block.children[0].name)
                # remove root_block from self.blocks
                self.blocks = [b for b in self.blocks if b != root_block] 
                # set new root block
                old_root_block = root_block
                root_block = old_root_block.children[0]
                # copy extra data and properties
                for b in old_root_block.getExtraDatas():
                    root_block.addExtraData(b)
                for b in old_root_block.getControllers():
                    root_block.addController(b)
                for b in old_root_block.properties:
                    root_block.addProperty(b)
                for b in old_root_block.effects:
                    root_block.addEffect(b)
            else:
                root_block.name = root_name
     
            # create keyframe file:
            #----------------------

            # convert root_block tree into a keyframe tree
            if self.EXPORT_ANIMATION == 2:
                # morrowind
                if self.EXPORT_VERSION == "Morrowind":
                    # create kf root header
                    kf_root = self.createBlock("NiSequenceStreamHelper")
                    kf_root.addExtraData(anim_textextra)
                    # find all nodes and keyframe controllers
                    nodekfs = {}
                    for node in root_block.tree():
                        if not isinstance(node, NifFormat.NiNode): continue
                        nodekfs[node] = []
                        ctrls = node.getControllers()
                        for ctrl in ctrls:
                            if not isinstance(ctrl, NifFormat.NiKeyframeController): continue
                            nodekfs[node].append(ctrl)
                    # reparent controller tree
                    for node, ctrls in nodekfs.iteritems():
                        for ctrl in ctrls:
                            # create node reference by name
                            nodename_extra = self.createBlock("NiStringExtraData")
                            nodename_extra.bytesRemaining = len(node.name) + 4
                            nodename_extra.stringData = node.name

                            # break the controller chain
                            ctrl.nextController = None

                            # add node reference and controller
                            kf_root.addExtraData(nodename_extra)
                            kf_root.addController(ctrl)

                #elif self.EXPORT_VERSION == "Oblivion":
                #    pass
                else:
                    raise NifExportError("Keyframe export for '%s' is not supported. Only Morrowind keyframes are supported."%self.EXPORT_VERSION)

                # make keyframe root block the root block to be written
                root_block = kf_root

            # write the file:
            #----------------
            ext = ".nif" if (self.EXPORT_ANIMATION != 2) else ".kf"
            self.msg("Writing %s file"%ext)
            self.msgProgress("Writing %s file"%ext)

            # make sure we have the right file extension
            if (self.fileext.lower() != ext):
                self.msg("WARNING: changing extension from %s to %s on output file"%(self.fileext,ext))
                self.filename = Blender.sys.join(self.filepath, self.filebase + ext)
            NIF_USER_VERSION = 0 if self.version != 0x14000005 else 11
            f = open(self.filename, "wb")
            try:
                NifFormat.write(f, version = self.version, user_version = NIF_USER_VERSION, roots = [root_block])
            finally:
                f.close()

        except NifExportError, e: # export error: raise a menu instead of an exception
            Blender.Draw.PupMenu('EXPORT ERROR%t|' + str(e))
            print 'NifExportError: ' + str(e)
            return

        except IOError, e: # IO error: raise a menu instead of an exception
            Blender.Draw.PupMenu('I/O ERROR%t|' + str(e))
            print 'IOError: ' + str(e)
            return

        except StandardError, e: # other error: raise a menu and an exception
            Blender.Draw.PupMenu('ERROR%t|' + str(e) + '    Check console for possibly more details.')
            raise

        finally:
            # clear progress bar
            self.msgProgress("Finished", progbar = 1)
    


    def exportNode(self, ob, space, parent_block, node_name):
        """
        Export a mesh/armature/empty object ob as child of parent_block.
        Export also all children of ob.
        - space is 'none', 'worldspace', or 'localspace', and determines
          relative to what object the transformation should be stored.
        - parent_block is the parent nif block of the object (None for the root node)
        - for the root node, ob is None, and node_name is usually the base
          filename (either with or without extension)
        """
        self.msg("Exporting NiNode %s"%node_name)

        # ob_type: determine the block type (None, 'Mesh', 'Empty' or 'Armature')
        # ob_ipo:  object animation ipo
        # node:    contains new NifFormat.NiNode instance
        if (ob == None):
            # -> root node
            assert(parent_block == None) # debug
            node = self.createBlock("NiNode")
            ob_type = None
            ob_ipo = None
        else:
            # -> empty, mesh, or armature
            ob_type = ob.getType()
            assert(ob_type in ['Empty', 'Mesh', 'Armature']) # debug
            assert(parent_block) # debug
            ob_ipo = ob.getIpo() # get animation data
            ob_children = [child for child in Blender.Object.Get() if child.parent == ob]
            
            if (node_name == 'RootCollisionNode'):
                # -> root collision node (can be mesh or empty)
                ob.rbShapeBoundType = Blender.Object.RBShapes['POLYHEDERON']
                ob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
                ob.drawMode = Blender.Object.DrawModes['WIRE']
                self.exportCollision(ob, parent_block)
                return None # done; stop here
            elif ob_type == 'Mesh':
                # -> mesh data.
                # If this has children or animations or more than one material
                # it gets wrapped in a purpose made NiNode.
                is_collision = (ob.getDrawType() == Blender.Object.DrawTypes['BOUNDBOX'])
                has_ipo = ob_ipo and len(ob_ipo.getCurves()) > 0
                has_children = len(ob_children) > 0
                is_multimaterial = len(set([f.mat for f in ob.data.faces])) > 1
                if is_collision:
                    self.exportCollision(ob, parent_block)
                    return None # done; stop here
                elif has_ipo or has_children or is_multimaterial:
                    # -> mesh ninode for the hierarchy to work out
                    node = self.createBlock('NiNode')
                else:
                    # don't create intermediate ninode for this guy
                    self.exportTriShapes(ob, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.createBlock("NiNode")

        # set transform on trishapes rather than on NiNode for skinned meshes
        # this fixes an issue with clothing slots
        if ob_type == 'Mesh':
            ob_parent = ob.getParent()
            if ob_parent and ob_parent.getType() == 'Armature':
                trishape_space = space
                space = 'none'
            else:
                trishape_space = 'none'

        # make it child of its parent in the nif, if it has one
        if parent_block:
            parent_block.addChild(node)

        # and fill in this node's non-trivial values
        node.name = self.getFullName(node_name)

        # default node flags
        if self.EXPORT_VERSION == 'Oblivion':
            node.flags = 0x000E
        else:
            # morrowind
            node.flags = 0x000C

        self.exportMatrix(ob, space, node)

        if (ob != None):
            # export animation
            if (ob_ipo != None):
                self.exportKeyframes(ob_ipo, space, node)
        
            # if it is a mesh, export the mesh as trishape children of this ninode
            if (ob.getType() == 'Mesh'):
                self.exportTriShapes(ob, trishape_space, node) # see definition of trishape_space above
                
            # if it is an armature, export the bones as ninode children of this ninode
            elif (ob.getType() == 'Armature'):
                self.exportBones(ob, node)

            # export all children of this empty/mesh/armature/bone object as children of this NiNode
            self.exportChildren(ob, node)

        return node



    #
    # Export the animation of blender Ipo as keyframe controller and
    # keyframe data. Extra quaternion is multiplied prior to keyframe
    # rotation, and dito for translation. These extra fields come in handy
    # when exporting bone ipo's, which are relative to the rest pose, so
    # we can pass the rest pose through these extra transformations.
    #
    # bind_mat is the original Blender bind matrix (the B' matrix below)
    # extra_mat_inv is the inverse matrix which transforms the Blender bone matrix
    # to the NIF bone matrix (the inverse of the X matrix below)
    #
    # Explanation of extra transformations:
    # Final transformation matrix is vec * Rchannel * Tchannel * Rbind * Tbind
    # So we export:
    # [ SRchannel 0 ]    [ SRbind 0 ]   [ SRchannel * SRbind        0 ]
    # [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel * SRbind + Tbind 1 ]
    # or, in detail,
    # Stotal = Schannel * Sbind
    # Rtotal = Rchannel * Rbind
    # Ttotal = Tchannel * Sbind * Rbind + Tbind
    # We also need the conversion of the new bone matrix to the original matrix, say X,
    # B' = X * B
    # (with B' the Blender matrix and B the NIF matrix) because we need that
    # C' * B' = X * C * B
    # and therefore
    # C * B = inverse(X) * C' * B'
    # (we need to write out C * B, the NIF format stores total transformation in keyframes).
    # In detail:
    #          [ SRX 0 ]     [ SRC' 0 ]   [ SRB' 0 ]
    # inverse( [ TX  1 ] ) * [ TC'  1 ] * [ TB'  1 ] =
    # [ inverse(SRX)         0 ]   [ SRC' * SRB'         0 ]
    # [ -TX * inverse(SRX)   1 ] * [ TC' * SRB' + TB'    1 ] =
    # [ inverse(SRX) * SRC' * SRB'                       0 ]
    # [ (-TX * inverse(SRX) * SRC' + TC') * SRB' + TB'    1 ]
    # Hence
    # S = SC' * SB' / SX
    # R = inverse(RX) * RC' * RB'
    # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
    #
    # Finally, note that
    # - TX * inverse(RX) / SX = translation part of inverse(X)
    # inverse(RX) = rotation part of inverse(X)
    # 1 / SX = scale part of inverse(X)
    # so having inverse(X) around saves on calculations
    def exportKeyframes(self, ipo, space, parent_block, bind_mat = None, extra_mat_inv = None):
        if self.EXPORT_ANIMATION == 1: # keyframe controllers are not present in geometry only files
            return

        self.msg("Exporting keyframe %s"%parent_block.name)
        # -> get keyframe information
        
        assert(space == 'localspace') # we don't support anything else (yet)
        assert(isinstance(parent_block, NifFormat.NiNode)) # make sure the parent is of the right type
        
        # some calculations
        if bind_mat:
            bind_scale, bind_rot, bind_trans = self.decomposeSRT(bind_mat)
            bind_quat = bind_rot.toQuat()
        else:
            bind_scale = 1.0
            bind_rot = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
            bind_quat = Blender.Mathutils.Quaternion(1,0,0,0)
            bind_trans = Blender.Mathutils.Vector(0,0,0)
        if extra_mat_inv:
            extra_scale_inv, extra_rot_inv, extra_trans_inv = self.decomposeSRT(extra_mat_inv)
            extra_quat_inv = extra_rot_inv.toQuat()
        else:
            extra_scale_inv = 1.0
            extra_rot_inv = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
            extra_quat_inv = Blender.Mathutils.Quaternion(1,0,0,0)
            extra_trans_inv = Blender.Mathutils.Vector(0,0,0)

        # sometimes we need to export an empty keyframe... this will take care of that
        if (ipo == None):
            scale_curve = {}
            rot_curve = {}
            trans_curve = {}
        # the usual case comes now...
        else:
            # merge the animation curves into a rotation vector and translation vector curve
            scale_curve = {}
            rot_curve = {}
            trans_curve = {}
            for curve in ipo.getCurves():
                for btriple in curve.getPoints():
                    knot = btriple.getPoints()
                    frame = knot[0]
                    if (frame < self.fstart) or (frame > self.fend): continue
                    if (curve.getName() == 'SizeX') or (curve.getName() == 'SizeY') or (curve.getName() == 'SizeZ'):
                        scale_curve[frame] = ( ipo.getCurve('SizeX').evaluate(frame)\
                                            + ipo.getCurve('SizeY').evaluate(frame)\
                                            + ipo.getCurve('SizeZ').evaluate(frame) ) / 3.0 # support only uniform scaling... take the mean
                        scale_curve[frame] = scale_curve[frame] * bind_scale * extra_scale_inv # SC' * SB' / SX
                    if (curve.getName() == 'RotX') or (curve.getName() == 'RotY') or (curve.getName() == 'RotZ'):
                        rot_curve[frame] = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toQuat()
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    elif (curve.getName() == 'QuatX') or (curve.getName() == 'QuatY') or (curve.getName() == 'QuatZ') or  (curve.getName() == 'QuatW'):
                        rot_curve[frame] = Blender.Mathutils.Quaternion()
                        rot_curve[frame].x = ipo.getCurve('QuatX').evaluate(frame)
                        rot_curve[frame].y = ipo.getCurve('QuatY').evaluate(frame)
                        rot_curve[frame].z = ipo.getCurve('QuatZ').evaluate(frame)
                        rot_curve[frame].w = ipo.getCurve('QuatW').evaluate(frame)
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    if (curve.getName() == 'LocX') or (curve.getName() == 'LocY') or (curve.getName() == 'LocZ'):
                        trans_curve[frame] = Blender.Mathutils.Vector([ipo.getCurve('LocX').evaluate(frame), ipo.getCurve('LocY').evaluate(frame), ipo.getCurve('LocZ').evaluate(frame)])
                        # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
                        trans_curve[frame] *= bind_scale
                        trans_curve[frame] *= bind_rot
                        trans_curve[frame] += bind_trans
                        # we need RC' and SC'
                        if ipo.getCurve('RotX'):
                            rot_c = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toMatrix()
                        elif ipo.getCurve('QuatX'):
                            rot_c = Blender.Mathutils.Quaternion()
                            rot_c.x = ipo.getCurve('QuatX').evaluate(frame)
                            rot_c.y = ipo.getCurve('QuatY').evaluate(frame)
                            rot_c.z = ipo.getCurve('QuatZ').evaluate(frame)
                            rot_c.w = ipo.getCurve('QuatW').evaluate(frame)
                            rot_c = rot_c.toMatrix()
                        else:
                            rot_c = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
                        if ipo.getCurve('SizeX'):
                            scale_c = ( ipo.getCurve('SizeX').evaluate(frame)\
                                      + ipo.getCurve('SizeY').evaluate(frame)\
                                      + ipo.getCurve('SizeZ').evaluate(frame) ) / 3.0 # support only uniform scaling... take the mean
                        else:
                            scale_c = 1.0
                        trans_curve[frame] += extra_trans_inv * rot_c * bind_rot * scale_c * bind_scale

        # -> now comes the real export

        # add a keyframecontroller block, and refer to this block in the parent's time controller
        if self.version < 0x0A020000:
            kfc = self.createBlock("NiKeyframeController")
        else:
            kfc = self.createBlock("NiTransformController")
            kfi = self.createBlock("NiTransformInterpolator")
            kfc.interpolator = kfi
        parent_block.addController(kfc)

        # fill in the non-trivial values
        kfc.flags = 0x0008
        kfc.frequency = 1.0
        kfc.phase = 0.0
        kfc.startTime = (self.fstart - 1) * self.fspeed
        kfc.stopTime = (self.fend - self.fstart) * self.fspeed

        # add the keyframe data
        if self.version < 0x0A020000:
            kfd = self.createBlock("NiKeyframeData")
            kfc.data = kfd
        else:
            kfd = self.createBlock("NiTransformData")
            kfi.data = kfd

        frames = rot_curve.keys()
        frames.sort()
        kfd.rotationType = NifFormat.KeyType.LINEAR_KEY
        kfd.numRotationKeys = len(frames)
        kfd.quaternionKeys.updateSize()
        for i, frame in enumerate(frames):
            rot_frame = kfd.quaternionKeys[i]
            rot_frame.time = (frame - 1) * self.fspeed
            rot_frame.value.w = rot_curve[frame].w
            rot_frame.value.x = rot_curve[frame].x
            rot_frame.value.y = rot_curve[frame].y
            rot_frame.value.z = rot_curve[frame].z

        frames = trans_curve.keys()
        frames.sort()
        kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.translations.numKeys = len(frames)
        kfd.translations.keys.updateSize()
        for i, frame in enumerate(frames):
            trans_frame = kfd.translations.keys[i]
            trans_frame.time = (frame - 1) * self.fspeed
            trans_frame.value.x = trans_curve[frame][0]
            trans_frame.value.y = trans_curve[frame][1]
            trans_frame.value.z = trans_curve[frame][2]

        frames = scale_curve.keys()
        frames.sort()
        kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.scales.numKeys = len(frames)
        kfd.scales.keys.updateSize()
        for frame in frames:
            scale_frame = kfd.scales.keys[i]
            scale_frame.time = (frame - 1) * self.fspeed
            scale_frame.value = scale_curve[frame]



    def exportVColProp(self, vertex_mode, lighting_mode):
        self.msg("Exporting NiVertexColorProperty")
        # create new vertex color property block
        vcolprop = self.createBlock("NiVertexColorProperty")
        
        # make it a property of the root node
        self.blocks[0].addChild(vcolprop)

        # and now export the parameters
        vcolprop.vertexMode = vertex_mode
        vcolprop.lightingMode = lighting_mode



    #
    # parse the animation groups buffer and write an extra string data block,
    # parented to the root block
    #
    def exportAnimGroups(self, animtxt, block_parent):
        if self.EXPORT_ANIMATION == 1: # animation group extra data is not present in geometry only files
            return

        self.msg("Exporting animation groups")
        # -> get animation groups information

        # parse the anim text descriptor
        
        # the format is:
        # frame/string1[/string2[.../stringN]]
        
        # example:
        # 001/Idle: Start/Idle: Stop/Idle2: Start/Idle2: Loop Start
        # 051/Idle2: Stop/Idle3: Start
        # 101/Idle3: Loop Start/Idle3: Stop

        slist = animtxt.asLines()
        flist = []
        dlist = []
        for s in slist:
            if ( s == '' ): continue # ignore empty lines
            t = s.split('/')
            if (len(t) < 2): raise NifExportError("Syntax error in Anim buffer ('%s')"%s)
            f = int(t[0])
            if ((f < self.fstart) or (f > self.fend)): raise NifExportError("Error in Anim buffer: frame out of range (%i not in [%i, %i])"%(f, self.fstart, self.fend))
            d = t[1].strip(' ')
            for i in range(2, len(t)):
                d = d + '\r\n' + t[i].strip(' ')
            #print 'frame %d'%f + ' -> \'%s\''%d # debug
            flist.append(f)
            dlist.append(d)
        
        # -> now comes the real export
        
        # add a NiTextKeyExtraData block, and refer to this block in the
        # parent node (we choose the root block)
        textextra = self.createBlock("NiTextKeyExtraData")
        block_parent.addExtraData(textextra)
        
        # create a NiTextKey for each frame descriptor
        textextra.numTextKeys = len(flist)
        textextra.textKeys.updateSize()
        for i in range(len(flist)):
            key = textextra.textKeys[i]
            key.time = self.fspeed * (flist[i]-1)
            key.value = dlist[i]

        return textextra


    def exportSourceTexture(self, texture, filename = None):
        """Export a NiSourceTexture.

        The texture argument is the texture object in blender to be exported
        and filename is the full or relative path to the texture file
        (this argument is used when exporting NiFlipControllers).
        Returns block of the exported NiSourceTexture."""
        
        # create NiSourceTexture
        srctex = NifFormat.NiSourceTexture()
        srctex.useExternal = True
        if not filename is None:
            # preset filename
            srctex.fileName = filename
        elif ( texture.type == Blender.Texture.Types.ENVMAP ):
            # this works for morrowind only
            if self.EXPORT_VERSION != "Morrowind":
                raise NifExportError(
                    "cannot export environment maps for nif version '%s'"%
                    self.EXPORT_VERSION)
            srctex.fileName = "enviro 01.TGA"
        elif ( texture.type == Blender.Texture.Types.IMAGE ):
            # get filename from image

            # texture must not be packed
            if texture.getImage().packed:
                raise NifExportError(
                    "export of packed textures is not supported ('%s')"
                    %texture.getName())
            
            tfn = texture.image.getFilename()

            if not self.EXPORT_VERSION in ['Morrowind', 'Oblivion']:
                # strip texture file path
                srctex.fileName = Blender.sys.basename(tfn)
            else:
                # strip the data files prefix from the texture's file name
                tfn = tfn.lower()
                idx = tfn.find("textures")
                if ( idx >= 0 ):
                    tfn = tfn[idx:]
                    srctex.fileName = tfn
                else:
                    srctex.fileName = Blender.sys.basename(tfn)
            # try and find a DDS alternative, force it if required
            ddsFile = "%s%s" % (srctex.fileName[:-4], '.dds')
            if Blender.sys.exists(ddsFile) or self.EXPORT_FORCEDDS:
                srctex.fileName = ddsFile
            # for linux export: fix path
            srctex.fileName = srctex.fileName.replace('/', '\\')
        else:
            # texture must be of type IMAGE or ENVMAP
            raise NifExportError(
                "Error: Texture '%s' must be of type IMAGE or ENVMAP"
                %texture.getName())


        # fill in default values
        srctex.pixelLayout = 5
        srctex.useMipmaps = 2
        srctex.alphaFormat = 3
        srctex.unknownByte = 1
        srctex.unknownByte2 = 1

        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiSourceTexture) and block.getHash() == srctex.getHash():
                return block

        self.msg("Exporting source texture %s"%texture.getName())

        # no identical source texture found, so use and register
        # the new one
        return self.registerBlock(srctex)



    ## TODO port code to use native Blender texture flipping system
    #
    # export a NiFlipController
    #
    # fliptxt is a blender text object containing the flip definitions
    # texture is the texture object in blender ( texture is used to checked for pack and mipmap flags )
    # target is the NiTexturingProperty
    # target_tex is the texture to flip ( 0 = base texture, 4 = glow texture )
    #
    # returns exported NiFlipController
    # 
    def exportFlipController(self, fliptxt, texture, target, target_tex):
        self.msg("Exporting NiFlipController for texture %s"%texture.getName())
        tlist = fliptxt.asLines()

        # create a NiFlipController
        flip = self.createBlock("NiFlipController")
        target.addController(flip)

        # fill in NiFlipController's values
        flip.flags = 0x0008
        flip.frequency = 1.0
        flip.startTime = (self.fstart - 1) * self.fspeed
        flip.stopTime = ( self.fend - self.fstart ) * self.fspeed
        flip.textureSlot = target_tex
        count = 0
        for t in tlist:
            if len( t ) == 0: continue  # skip empty lines
            # create a NiSourceTexture for each flip
            tex = self.exportSourceTexture(texture, t)
            flip.numSources += 1
            flip.sources.updateSize()
            flip.sources[flip.numSources-1] = tex
            count += 1
        if count < 2:
            raise NifExportError("Error in Texture Flip buffer '%s': Must define at least two textures"%fliptxt.getName())
        flip.delta = (flip.stopTime - flip.startTime) / count



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
    def exportTriShapes(self, ob, space, parent_block, trishape_name = None):
        self.msg("Exporting NiTriShapes/NiTriStrips for %s"%ob.name)
        self.msgProgress("Exporting %s"%ob.name)
        assert(ob.getType() == 'Mesh')

        # get mesh from ob
        mesh = ob.getData(mesh=1) # get mesh data
        
        # get the mesh's materials, this updates the mesh material list
        if not isinstance(parent_block, NifFormat.RootCollisionNode):
            mesh_mats = mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_mats = []
        # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
        if (mesh_mats == []):
            mesh_mats = [ None ]

        # let's now export one trishape for every mesh material
        
        for materialIndex, mesh_mat in enumerate( mesh_mats ):
            # -> first, extract valuable info from our ob
            
            mesh_base_mtex = None
            mesh_glow_mtex = None
            mesh_bump_mtex = None
            mesh_gloss_mtex = None
            mesh_dark_mtex = None
            mesh_detail_mtex = None
            mesh_texeff_mtex = None
            mesh_uvlayers = []    # uv layers used by this material
            mesh_hasalpha = False # mesh has transparency
            mesh_hasspec = False  # mesh has specular properties
            mesh_hasvcol = False
            mesh_hasnormals = False
            if (mesh_mat != None):
                mesh_hasnormals = True # for proper lighting
                # for non-textured materials, vertex colors are used to color the mesh
                # for textured materials, they represent lighting details
                # strange: mesh.vertexColors only returns true if the mesh has no texture coordinates
                mesh_hasvcol = mesh.vertexColors or ((mesh_mat.mode & Blender.Material.Modes.VCOL_LIGHT != 0) or (mesh_mat.mode & Blender.Material.Modes.VCOL_PAINT != 0))
                # read the Blender Python API documentation to understand this hack
                mesh_mat_ambient = mesh_mat.getAmb()            # 'Amb' scrollbar in blender (MW -> 1.0 1.0 1.0)
                mesh_mat_diffuse_color = mesh_mat.getRGBCol()   # 'Col' colour in Blender (MW -> 1.0 1.0 1.0)
                mesh_mat_specular_color = mesh_mat.getSpecCol() # 'Spe' colour in Blender (MW -> 0.0 0.0 0.0)
                specval = mesh_mat.getSpec()                    # 'Spec' slider in Blender
                mesh_mat_specular_color[0] *= specval
                mesh_mat_specular_color[1] *= specval
                mesh_mat_specular_color[2] *= specval
                if mesh_mat_specular_color[0] > 1.0: mesh_mat_specular_color[0] = 1.0
                if mesh_mat_specular_color[1] > 1.0: mesh_mat_specular_color[1] = 1.0
                if mesh_mat_specular_color[2] > 1.0: mesh_mat_specular_color[2] = 1.0
                if ( mesh_mat_specular_color[0] > NifFormat._EPSILON ) \
                    or ( mesh_mat_specular_color[1] > NifFormat._EPSILON ) \
                    or ( mesh_mat_specular_color[2] > NifFormat._EPSILON ):
                    mesh_hasspec = True
                mesh_mat_emissive = mesh_mat.getEmit()              # 'Emit' scrollbar in Blender (MW -> 0.0 0.0 0.0)
                mesh_mat_glossiness = mesh_mat.getHardness() / 4.0  # 'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_transparency = mesh_mat.getAlpha()         # 'A(lpha)' scrollbar in Blender (MW -> 1.0)
                mesh_hasalpha = (abs(mesh_mat_transparency - 1.0) > NifFormat._EPSILON) \
                                or (mesh_mat.getIpo() != None and mesh_mat.getIpo().getCurve('Alpha'))
                mesh_mat_ambient_color = [0.0,0.0,0.0]
                mesh_mat_ambient_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_ambient
                mesh_mat_ambient_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_ambient
                mesh_mat_ambient_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_ambient
                mesh_mat_emissive_color = [0.0,0.0,0.0]
                mesh_mat_emissive_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_emissive
                mesh_mat_emissive_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_emissive
                mesh_mat_emissive_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_emissive
                # the base texture = first material texture
                # note that most morrowind files only have a base texture, so let's for now only support single textured materials
                for mtex in mesh_mat.getTextures():
                    if not mtex:
                        # skip empty texture slots
                        continue

                    # check REFL-mapped textures
                    # (used for "NiTextureEffect" materials)
                    if mtex.texco == Blender.Texture.TexCo.REFL:
                        # of course the user should set all kinds of other
                        # settings to make the environment mapping come out
                        # (MapTo "COL", blending mode "Add")
                        # but let's not care too much about that
                        # only do some simple checks
                        if (mtex.mapto & Blender.Texture.MapTo.COL) == 0:
                            # it should map to colour
                            raise NifExportError("Non-COL-mapped reflection \
texture in mesh '%s', material '%s', these cannot be exported to NIF. Either \
delete all non-COL-mapped reflection textures, or in the Shading Panel, under \
Material Buttons, set texture 'Map To' to \
'COL'." % (ob.getName(),mesh_mat.getName()))
                        if mtex.blendmode != Blender.Texture.BlendModes["ADD"]:
                            # it should have "ADD" blending mode
                            raise NifExportError("Reflection texture should \
have blending mode 'Add' on texture in \
mesh '%s', material '%s')."%(ob.getName(),mesh_mat.getName()))
                            # an envmap image should have an empty... don't care
                        mesh_texeff_mtex = mtex

                    # check UV-mapped textures
                    elif mtex.texco == Blender.Texture.TexCo.UV:
                        # update set of uv layers that must be exported
                        uvlayer = ( mtex.uvlayer if mtex.uvlayer
                                    else mesh.activeUVLayer )
                        if not uvlayer in mesh_uvlayers:
                            mesh_uvlayers.append(uvlayer)
                        # check which texture slot this mtex belongs to
                        if mtex.mapto & Blender.Texture.MapTo.COL \
                           and mtex.mapto & Blender.Texture.MapTo.EMIT:
                            # got the glow tex
                            if mesh_glow_mtex:
                                raise NifExportError("Multiple glow textures \
in mesh '%s', material '%s'. Make sure there is only one texture with \
MapTo.EMIT"%(mesh.name,mesh_mat.getName()))
                            # check if calculation of alpha channel is enabled
                            # for this texture
                            if (mtex.tex.imageFlags & Blender.Texture.ImageFlags.CALCALPHA != 0) \
                               and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                raise NifExportError("In mesh '%s', material \
'%s': glow texture must have CALCALPHA flag set, and must have MapTo.ALPHA \
enabled."%(ob.getName(),mesh_mat.getName()))
                            mesh_glow_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.SPEC:
                            # got the gloss map
                            if mesh_gloss_mtex:
                                raise NifExportError("Multiple gloss textures \
in mesh '%s', material '%s'. Make sure there is only one texture with \
MapTo.SPEC"%(mesh.name,mesh_mat.getName()))
                            mesh_gloss_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.NOR:
                            # got the normal map
                            if mesh_bump_mtex:
                                raise NifExportError("Multiple bump textures \
in mesh '%s', material '%s'. Make sure there is only one texture with \
MapTo.NOR"%(mesh.name,mesh_mat.getName()))
                            mesh_bump_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.COL and \
                             mtex.blendmode == Blender.Texture.BlendModes["DARKEN"] and \
                             not mesh_dark_mtex:
                            # got the dark map
                            mesh_dark_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.COL and \
                             not mesh_base_mtex:
                            # anything else that maps to COL is considered
                            # as base texture
                            mesh_base_mtex = mtex
                            # check if alpha channel is enabled for this texture
                            if (mesh_base_mtex.tex.imageFlags & Blender.Texture.ImageFlags.USEALPHA != 0) and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                # in this case, Blender replaces the texture transparant parts with the underlying material color...
                                # in NIF, material alpha is multiplied with texture alpha channel...
                                # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                                # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                                # but...
                                if mesh_mat_transparency > NifFormat._EPSILON:
                                    raise NifExportError("Cannot export this \
type of transparency in material '%s': instead, try to set alpha to 0.0 and to \
use the 'Var' slider in the 'Map To' tab under the material \
buttons."%mesh_mat.getName())
                                if (mesh_mat.getIpo() and mesh_mat.getIpo().getCurve('Alpha')):
                                    raise NifExportError("Cannot export \
animation for this type of transparency in material '%s': remove alpha \
animation, or turn off MapTo.ALPHA, and try again."%mesh_mat.getName())
                                mesh_mat_transparency = mtex.varfac # we must use the "Var" value
                                mesh_hasalpha = True
                        elif mtex.mapto & Blender.Texture.MapTo.COL and \
                             not mesh_detail_mtex:
                            # extra COL channel is considered
                            # as detail texture
                            mesh_detail_mtex = mtex
                        else:
                            # unknown map
                            raise NifExportError("Do not know how to export \
texture '%s', in mesh '%s', material '%s'. Either delete it, or if this \
texture is to be your base texture, go to the Shading Panel, Material Buttons, \
and set texture 'Map To' to 'COL'." % (mtex.tex.getName(),
                                       ob.getName(),
                                       mesh_mat.getName()))
                    else:
                        # nif only support UV-mapped textures
                        raise NifExportError("Non-UV texture in mesh '%s', \
material '%s'. Either delete all non-UV textures, or in the Shading Panel, \
under Material Buttons, set texture 'Map Input' to 'UV'."%
                                             (ob.getName(),mesh_mat.getName()))



            # -> now comes the real export
            
            # We now extract vertices, uv-vertices, normals, and vertex
            # colors from the mesh's face list. NIF has one uv vertex and
            # one normal per vertex, unlike blender's uv vertices and
            # normals per face... therefore some vertices must be
            # duplicated. The following algorithm extracts all unique
            # (vert, uv-vert, normal, vcol) quads, and uses this list to
            # produce the list of vertices, uv-vertices, normals, vertex
            # colors, and face indices.

            # Blender only supports one set of uv coordinates per mesh;
            # therefore, we shall have trouble when importing
            # multi-textured trishapes in blender. For this export script,
            # no problem: we must simply duplicate the uv vertex list.

            # NIF uses the normal table for lighting. So, smooth faces
            # should use Blender's vertex normals, and solid faces should
            # use Blender's face normals.
            
            vertquad_list = [] # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [ None for i in xrange(len(mesh.verts)) ] # blender vertex -> nif vertices
            vertlist = []
            normlist = []
            vcollist = []
            uvlist = []
            trilist = []
            for f in mesh.faces:
                # does the face belong to this trishape?
                if (mesh_mat != None): # we have a material
                    if (f.mat != materialIndex): # but this face has another material
                        continue # so skip this face
                f_numverts = len(f.v)
                if (f_numverts < 3): continue # ignore degenerate faces
                assert((f_numverts == 3) or (f_numverts == 4)) # debug
                if mesh_uvlayers: # if we have uv coordinates
                    if len(f.uv) != len(f.v): # make sure we have UV data
                        raise NifExportError('ERROR%t|Create a UV map for every texture, and run the script again.')
                # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
                f_index = [ -1 ] * f_numverts
                for i in range(f_numverts):
                    fv = f.v[i].co
                    # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                    if mesh_hasnormals:
                        if f.smooth:
                            fn = f.v[i].no
                        else:
                            fn = f.no
                    else:
                        fn = None
                    fuv = []
                    for uvlayer in mesh_uvlayers:
                        mesh.activeUVLayer = uvlayer
                        fuv.append(f.uv[i])
                    if mesh_hasvcol:
                        if (len(f.col) == 0):
                            print 'WARNING: vertex color painting/lighting enabled, but mesh has no vertex color data; vertex weights will not be written.'
                            fcol = None
                            mesh_hasvcol = False
                        else:
                            # NIF stores the colour values as floats
                            fcol = f.col[i]
                    else:
                        fcol = None
                        
                    vertquad = ( fv, fuv, fn, fcol )

                    # do we already have this quad? (optimized by m4444x)
                    f_index[i] = len(vertquad_list)
                    v_index = f.v[i].index
                    if vertmap[v_index]:
                        # iterate only over vertices with the same vertex index
                        # and check if they have the same uvs, normals and colors (wow is that fast!)
                        for j in vertmap[v_index]:
                            if mesh_uvlayers:
                                if max(abs(vertquad[1][uvlayer][0]
                                           - vertquad_list[j][1][uvlayer][0])
                                       for uvlayer
                                       in xrange(len(mesh_uvlayers))) \
                                       > NifFormat._EPSILON:
                                     continue
                                if max(abs(vertquad[1][uvlayer][1]
                                           - vertquad_list[j][1][uvlayer][1])
                                       for uvlayer
                                       in xrange(len(mesh_uvlayers))) \
                                       > NifFormat._EPSILON:
                                    continue
                            if mesh_hasnormals:
                                if abs(vertquad[2][0] - vertquad_list[j][2][0]) > NifFormat._EPSILON: continue
                                if abs(vertquad[2][1] - vertquad_list[j][2][1]) > NifFormat._EPSILON: continue
                                if abs(vertquad[2][2] - vertquad_list[j][2][2]) > NifFormat._EPSILON: continue
                            if mesh_hasvcol:
                                if abs(vertquad[3].r - vertquad_list[j][3].r) > NifFormat._EPSILON: continue
                                if abs(vertquad[3].g - vertquad_list[j][3].g) > NifFormat._EPSILON: continue
                                if abs(vertquad[3].b - vertquad_list[j][3].b) > NifFormat._EPSILON: continue
                                if abs(vertquad[3].a - vertquad_list[j][3].a) > NifFormat._EPSILON: continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise NifExportError('ERROR%t|Too many vertices. Decimate your mesh and try again.')
                    if (f_index[i] == len(vertquad_list)):
                        # first: add it to the vertex map
                        if not vertmap[v_index]:
                            vertmap[v_index] = []
                        vertmap[v_index].append(len(vertquad_list))
                        # new (vert, uv-vert, normal, vcol) quad: add it
                        vertquad_list.append(vertquad)
                        # add the vertex
                        vertlist.append(vertquad[0])
                        if mesh_hasnormals: normlist.append(vertquad[2])
                        if mesh_hasvcol:    vcollist.append(vertquad[3])
                        if mesh_uvlayers:   uvlist.append(vertquad[1])
                # now add the (hopefully, convex) face, in triangles
                for i in range(f_numverts - 2):
                    if True: #TODO: #(ob_scale > 0):
                        f_indexed = (f_index[0], f_index[1+i], f_index[2+i])
                    else:
                        f_indexed = (f_index[0], f_index[2+i], f_index[1+i])
                    trilist.append(f_indexed)

            if len(trilist) > 65535:
                raise NifExportError(
                    'ERROR%t|Too many faces. Decimate your mesh and try again.')
            if len(vertlist) == 0:
                continue # m4444x: skip 'empty' material indices
            
            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

            # create a trishape block
            if not self.EXPORT_STRIPIFY:
                trishape = self.createBlock("NiTriShape")
            else:
                trishape = self.createBlock("NiTriStrips")

            # add texture effect block (must be added as preceeding child of
            # the trishape)
            if self.EXPORT_VERSION == "Morrowind" and mesh_texeff_mtex:
                # create a new parent block for this shape
                extra_node = self.createBlock("NiNode")
                parent_block.addChild(extra_node)
                # set default values for this ninode
                extra_node.rotation.setIdentity()
                extra_node.scale = 1.0
                extra_node.flags = 0x000C # morrowind
                # create texture effect block and parent the
                # texture effect and trishape to it
                texeff = self.exportTextureEffect(mesh_texeff_mtex)
                extra_node.addChild(texeff)
                extra_node.addChild(trishape)
                extra_node.addEffect(texeff)
            else:
                # refer to this block in the parent's
                # children list
                parent_block.addChild(trishape)
            
            # fill in the NiTriShape's non-trivial values
            if isinstance(parent_block, NifFormat.RootCollisionNode):
                trishape.name = ""
            elif not trishape_name:
                if parent_block.name:
                    trishape.name = "Tri " + parent_block.name
                else:
                    trishape.name = "Tri " + ob.getName()
            else:
                trishape.name = trishape_name
            if len(mesh_mats) > 1:
                # multimaterial meshes: add material index
                trishape.name += " %i"%materialIndex # Morrowind's child naming convention
            trishape.name = self.getFullName(trishape.name)
            if self.EXPORT_VERSION == 'Oblivion':
                trishape.flags = 0x000E
            else:
                # morrowind
                if ob.getDrawType() != 2: # not wire
                    trishape.flags = 0x0004 # use triangles as bounding box
                else:
                    trishape.flags = 0x0005 # use triangles as bounding box + hide

            self.exportMatrix(ob, space, trishape)
            
            if mesh_base_mtex or mesh_glow_mtex:
                # add NiTriShape's texturing property
                trishape.addProperty(self.exportTexturingProperty(
                    flags = 0x0001, # standard
                    applymode = self.APPLYMODE[mesh_base_mtex.blendmode if mesh_base_mtex else Blender.Texture.BlendModes["MIX"]],
                    uvlayers = mesh_uvlayers,
                    basemtex = mesh_base_mtex,
                    glowmtex = mesh_glow_mtex,
                    bumpmtex = mesh_bump_mtex,
                    glossmtex = mesh_gloss_mtex,
                    darkmtex = mesh_dark_mtex,
                    detailmtex = mesh_detail_mtex))

            if mesh_hasalpha:
                # add NiTriShape's alpha propery
                # refer to the alpha property in the trishape block
                trishape.addProperty(self.exportAlphaProperty(flags = 0x00ED))

            if mesh_mat:
                # add NiTriShape's specular property
                if mesh_hasspec:
                    # refer to the specular property in the trishape block
                    trishape.addProperty(self.exportSpecularProperty(flags = 0x0001))
                
                # add NiTriShape's material property
                trimatprop = self.exportMaterialProperty(
                    name = self.getFullName(mesh_mat.getName()),
                    flags = 0x0001, # ? standard
                    ambient = mesh_mat_ambient_color,
                    diffuse = mesh_mat_diffuse_color,
                    specular = mesh_mat_specular_color,
                    emissive = mesh_mat_emissive_color,
                    glossiness = mesh_mat_glossiness,
                    alpha = mesh_mat_transparency)
                
                # refer to the material property in the trishape block
                trishape.addProperty(trimatprop)


                # material animation
                ipo = mesh_mat.getIpo()
                a_curve = None
                if ( ipo != None ):
                    a_curve = ipo.getCurve( 'Alpha' )
                
                if ( a_curve != None ):
                    # get the alpha keyframes from blender's ipo curve
                    alpha = {}
                    for btriple in a_curve.getPoints():
                        knot = btriple.getPoints()
                        frame = knot[0]
                        ftime = (frame - self.fstart) * self.fspeed
                        alpha[ftime] = ipo.getCurve( 'Alpha' ).evaluate(frame)

                    # add and link alpha controller, data and interpolator blocks
                    alphac = self.createBlock("NiAlphaController")
                    alphad = self.createBlock("NiFloatData")
                    alphai = self.createBlock("NiFloatInterpolator")

                    trimatprop.addController(alphac)
                    alphac.interpolator = alphai
                    alphac.data = alphad
                    alphai.data = alphad

                    # select extrapolation mode
                    if ( a_curve.getExtrapolation() == "Cyclic" ):
                        alphac.flags = 0x0008
                    elif ( a_curve.getExtrapolation() == "Constant" ):
                        alphac.flags = 0x000c
                    else:
                        print "WARNING: extrapolation \"%s\" for alpha curve not supported using \"cycle reverse\" instead"%a_curve.getExtrapolation()
                        alphac.flags = 0x000a

                    # fill in timing values
                    alphac.frequency = 1.0
                    alphac.phase = 0.0
                    alphac.startTime = (self.fstart - 1) * self.fspeed
                    alphac.stopTime = (self.fend - self.fstart) * self.fspeed

                    # select interpolation mode and export the alpha curve data
                    if ( a_curve.getInterpolation() == "Linear" ):
                        alphad.data.interpolation = NifFormat.KeyType.LINEAR_KEY
                    elif ( a_curve.getInterpolation() == "Bezier" ):
                        alphad.data.interpolation = NifFormat.KeyType.QUADRATIC_KEY
                    else:
                        raise NifExportError( 'interpolation %s for alpha curve not supported use linear or bezier instead'%a_curve.getInterpolation() )

                    alphad.data.numKeys = len(alpha)
                    alphad.data.keys.updateSize()
                    for ftime, key in zip(sorted(alpha), alphad.data.keys):
                        key.time = ftime
                        key.value = alpha[ftime]
                        key.forward = 0.0 # ?
                        key.backward = 0.0 # ?

            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = self.createBlock("NiTriShapeData")
            else:
                tridata = self.createBlock("NiTriStripsData")
            trishape.data = tridata

            tridata.numVertices = len(vertlist)
            tridata.hasVertices = True
            tridata.vertices.updateSize()
            for i, v in enumerate(tridata.vertices):
                v.x = vertlist[i][0]
                v.y = vertlist[i][1]
                v.z = vertlist[i][2]
            tridata.updateCenterRadius()
            
            if mesh_hasnormals:
                tridata.hasNormals = True
                tridata.normals.updateSize()
                for i, v in enumerate(tridata.normals):
                    v.x = normlist[i][0]
                    v.y = normlist[i][1]
                    v.z = normlist[i][2]
                
            if mesh_hasvcol:
                tridata.hasVertexColors = True
                tridata.vertexColors.updateSize()
                for i, v in enumerate(tridata.vertexColors):
                    v.r = vcollist[i].r / 255.0
                    v.g = vcollist[i].g / 255.0
                    v.b = vcollist[i].b / 255.0
                    v.a = vcollist[i].a / 255.0

            if mesh_uvlayers:
                tridata.numUvSets = len(mesh_uvlayers)
                tridata.hasUv = True
                tridata.uvSets.updateSize()
                for j, uvlayer in enumerate(mesh_uvlayers):
                    for i, uv in enumerate(tridata.uvSets[j]):
                        uv.u = uvlist[i][j][0]
                        uv.v = 1.0 - uvlist[i][j][1] # opengl standard

            # set triangles
            # stitch strips for civ4
            tridata.setTriangles(trilist, stitchstrips = self.EXPORT_STITCHSTRIPS)

            # update tangent space
            if mesh_uvlayers and mesh_hasnormals:
                if self.version >= 0x14000005:
                    trishape.updateTangentSpace()

            # now export the vertex weights, if there are any
            vertgroups = ob.data.getVertGroupNames()
            bonenames = []
            if ob.getParent():
                if ob.getParent().getType() == 'Armature':
                    ob_armature = ob.getParent()
                    armaturename = ob_armature.getName()
                    bonenames = ob_armature.getData().bones.keys()
                    # the vertgroups that correspond to bonenames are bones that influence the mesh
                    boneinfluences = []
                    for bone in bonenames:
                        if bone in vertgroups:
                            boneinfluences.append(bone)
                    if boneinfluences: # yes we have skinning!
                        # create new skinning instance block and link it
                        skininst = self.createBlock("NiSkinInstance")
                        trishape.skinInstance = skininst
                        for block in self.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == self.getFullName(armaturename):
                                    skininst.skeletonRoot = block
                                    break
                        else:
                            raise NifExportError("Skeleton root '%s' not found."%armaturename)
            
                        # create skinning data and link it
                        skindata = self.createBlock("NiSkinData")
                        skininst.data = skindata
            
                        skindata.hasVertexWeights = True
                        # fix geometry rest pose: transform relative to skeleton root
                        skindata.setTransform(self.getObjectMatrix(ob, 'localspace').getInverse())
            
                        # add vertex weights
                        # first find weights and normalization factors
                        vert_list = {}
                        vert_norm = {}
                        for bone in boneinfluences:
                            vert_list[bone] = ob.data.getVertsFromGroup(bone, 1)
                            for v in vert_list[bone]:
                                if vert_norm.has_key(v[0]):
                                    vert_norm[v[0]] += v[1]
                                else:
                                    vert_norm[v[0]] = v[1]
                        
                        # for each bone, first we get the bone block
                        # then we get the vertex weights
                        # and then we add it to the NiSkinData
                        vert_added = [False for i in xrange(len(vertlist))] # allocate memory for faster performance
                        for bone_index, bone in enumerate(boneinfluences):
                            # find bone in exported blocks
                            bone_block = None
                            for block in self.blocks:
                                if isinstance(block, NifFormat.NiNode):
                                    if block.name == self.getFullName(bone):
                                        if not bone_block:
                                            bone_block = block
                                        else:
                                            raise NifExportError("multiple bones with name '%s': probably you have multiple armatures, please parent all meshes to a single armature and try again"%bone)
                            if not bone_block:
                                raise NifExportError("Bone '%s' not found."%bone)
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
                                if vertmap[v[0]] and vert_norm[v[0]]: # extra check for multi material meshes
                                    for vert_index in vertmap[v[0]]:
                                        vert_weights[vert_index] = v[1] / vert_norm[v[0]]
                                        vert_added[vert_index] = True
                            # add bone as influence, but only if there were actually any vertices influenced by the bone
                            if vert_weights:
                                trishape.addBone(bone_block, vert_weights)
            
                        # each vertex must have been assigned to at least one vertex group
                        # or the model doesn't display correctly in the TESCS
                        vert_weights = {}
                        if False in vert_added:
                            # select mesh object
                            for bobj in self.scene.objects:
                                bobj.sel = False
                            self.scene.objects.active = ob
                            ob.sel = 1
                            # select bad vertices
                            for v in mesh.verts:
                                v.sel = 0
                            for i, added in enumerate(vert_added):
                                if not added:
                                    for j, vlist in enumerate(vertmap):
                                        if vlist and (i in vlist):
                                            idx = j
                                            break
                                    else:
                                        raise RuntimeError("vertmap bug")
                                    mesh.verts[idx].sel = 1
                            # switch to edit mode and raise exception
                            Blender.Window.EditMode(1)
                            raise NifExportError("Cannot export mesh with \
unweighted vertices. The unweighted vertices have been selected in the mesh so \
they can easily be identified.")

                        # update bind position skinning data
                        trishape.updateBindPosition()

                        # calculate center and radius for each skin bone data block
                        trishape.updateSkinCenterRadius()

                        if self.version >= 0x04020100 and self.EXPORT_SKINPARTITION:
                            self.msg("creating 'NiSkinPartition'")
                            lostweight = trishape.updateSkinPartition(maxbonesperpartition = self.EXPORT_BONESPERPARTITION, maxbonespervertex = self.EXPORT_BONESPERVERTEX, stripify = self.EXPORT_STRIPIFY, stitchstrips = self.EXPORT_STITCHSTRIPS, padbones = self.EXPORT_PADBONES)
                            # warn on bad config settings
                            if self.EXPORT_VERSION == 'Oblivion':
                               if self.EXPORT_PADBONES:
                                   print("""\
WARNING: using padbones on Oblivion export, you probably do not want to do this
         disable the pad bones option to get higher quality skin partitions""")
                               if self.EXPORT_BONESPERPARTITION < 18:
                                   print("""\
WARNING: using less than 18 bones per partition on Oblivion export
         set it to 18 to get higher quality skin partitions""")
                            if lostweight > NifFormat._EPSILON:
                                print("""\
WARNING: lost %f in vertex weights while creating a skin partition for
         Blender object '%s' (nif block '%s')""" % (lostweight,
                                                    ob.name, trishape.name))

                        # clean up
                        del vert_weights
                        del vert_added

            
            # shape key morphing
            key = mesh.key
            if key:
                if len( key.getBlocks() ) > 1:
                    # yes, there is a key object attached
                    # FIXME: check if key object contains relative shape keys
                    keyipo = key.getIpo()
                    if keyipo:
                        # yes, there is a shape ipo too
                        
                        # create geometry morph controller
                        morphctrl = self.createBlock("NiGeomMorpherController")
                        trishape.addController(morphctrl)
                        morphctrl.frequency = 1.0
                        morphctrl.phase = 0.0
                        ctrlStart = 1000000.0
                        ctrlStop = -1000000.0
                        ctrlFlags = 0x000c
                        
                        # create geometry morph data
                        morphdata = self.createBlock("NiMorphData")
                        morphctrl.data = morphdata
                        morphdata.numMorphs = len(key.getBlocks())
                        morphdata.numVertices = len(vertlist)
                        morphdata.morphs.updateSize()
                        
                        for keyblocknum, keyblock in enumerate( key.getBlocks() ):
                            # export morphed vertices
                            morph = morphdata.morphs[keyblocknum]
                            self.msg("exporting morph %i: vertices"%keyblocknum)
                            morph.arg = morphdata.numVertices
                            morph.vectors.updateSize()
                            for b_v_index, (vert_indices, vert) in enumerate(zip(vertmap, keyblock.data)):
                                mv = vert.copy()
                                if keyblocknum > 0:
                                    mv.x -= mesh.verts[b_v_index].co.x
                                    mv.y -= mesh.verts[b_v_index].co.y
                                    mv.z -= mesh.verts[b_v_index].co.z
                                for vert_index in vert_indices:
                                    morph.vectors[vert_index].x = mv.x
                                    morph.vectors[vert_index].y = mv.y
                                    morph.vectors[vert_index].z = mv.z
                            
                            # export ipo shape key curve
                            #curve = keyipo.getCurve( 'Key %i'%keyblocknum ) # FIXME
                            # workaround
                            curve = None
                            if ( keyblocknum - 1 ) in range( len( keyipo.getCurves() ) ):
                                curve = keyipo.getCurves()[keyblocknum-1]
                            # base key has no curve all other keys should have one
                            if curve:
                                self.msg("exporting morph %i: curve"%keyblocknum)
                                if ( curve.getExtrapolation() == "Constant" ):
                                    ctrlFlags = 0x000c
                                elif ( curve.getExtrapolation() == "Cyclic" ):
                                    ctrlFlags = 0x0008
                                morph.interpolation = NifFormat.KeyType.LINEAR_KEY
                                morph.numKeys = len(curve.getPoints())
                                morph.keys.updateSize()
                                for i, btriple in enumerate(curve.getPoints()):
                                    knot = btriple.getPoints()
                                    morph.keys[i].arg = morph.interpolation
                                    morph.keys[i].time = (knot[0] - self.fstart) * self.fspeed
                                    morph.keys[i].value = curve.evaluate( knot[0] )
                                    #morph.keys[i].forwardTangent = 0.0 # ?
                                    #morph.keys[i].backwardTangent = 0.0 # ?
                                    ctrlStart = min(ctrlStart, morph.keys[i].time)
                                    ctrlStop  = max(ctrlStop,  morph.keys[i].time)
                        morphctrl.flags = ctrlFlags
                        morphctrl.startTime = ctrlStart
                        morphctrl.stopTime = ctrlStop



    def exportBones(self, arm, parent_block):
        """Export the bones of an armature."""
        self.msg("Exporting bones for armature %s"%arm.getName())
        # the armature was already exported as a NiNode
        # now we must export the armature's bones
        assert( arm.getType() == 'Armature' )

        # find the root bones
        # dictionary of bones (name -> bone)
        bones = dict(arm.getData().bones.items())
        root_bones = []
        for root_bone in bones.values():
            while root_bone.parent in bones.values():
                root_bone = root_bone.parent
            if root_bones.count(root_bone) == 0:
                root_bones.append(root_bone)

        if (arm.getAction()):
            bones_ipo = arm.getAction().getAllChannelIpos() # dictionary of Bone Ipos (name -> ipo)
        else:
            bones_ipo = {} # no ipos

        bones_node = {} # maps bone names to NiNode blocks

        # here all the bones are added
        # first create all bones with their keyframes
        # and then fix the links in a second run

        # ok, let's create the bone NiNode blocks
        for bone in bones.values():
            # create a new block for this bone
            self.msg("Exporting NiNode for bone %s"%bone.name)
            node = self.createBlock("NiNode")
            bones_node[bone.name] = node # doing this now makes linkage very easy in second run

            # add the node and the keyframe for this bone
            node.name = self.getFullName(bone.name)
            if self.EXPORT_VERSION == 'Oblivion':
                node.flags = 0x000E # default for Oblivion bones (note: bodies have 0x000E, clothing has 0x000F)
            else:
                node.flags = 0x0002 # default for Morrowind bones
            self.exportMatrix(bone, 'localspace', node) # rest pose
            
            # bone rotations are stored in the IPO relative to the rest position
            # so we must take the rest position into account
            # (need original one, without extra transforms, so extra = False)
            bonerestmat = self.getBoneRestMatrix(bone, 'BONESPACE',
                                                 extra = False)
            try:
                bonexmat_inv = self.bonesExtraMatrixInv[bone.name]
            except KeyError:
                bonexmat_inv = Blender.Mathutils.Matrix()
                bonexmat_inv.identity()
            if bones_ipo.has_key(bone.name):
                self.exportKeyframes(bones_ipo[bone.name], 'localspace', node, bind_mat = bonerestmat, extra_mat_inv = bonexmat_inv)

        # now fix the linkage between the blocks
        for bone in bones.values():
            # link the bone's children to the bone
            if bone.children:
                self.msg("Linking children of bone %s"%bone.name)
                for child in bone.children:
                    # bone.children returns also grandchildren etc.
                    # we only want immediate children, so do a parent check
                    if child.parent.name == bone.name:
                        bones_node[bone.name].addChild(bones_node[child.name])
            # if it is a root bone, link it to the armature
            if not bone.parent:
                parent_block.addChild(bones_node[bone.name])



    def exportChildren(self, obj, parent_block):
        """Export all children of blender object ob as children of
        parent_block."""
        # loop over all obj's children
        for ob_child in [ cld  for cld in Blender.Object.Get()
                          if cld.getParent() == obj ]:
            # is it a regular node?
            if ob_child.getType() in ['Mesh', 'Empty', 'Armature']:
                if (obj.getType() != 'Armature'):
                    # not parented to an armature
                    self.exportNode(ob_child, 'localspace',
                                    parent_block, ob_child.getName())
                else:
                    # this object is parented to an armature
                    # we should check whether it is really parented to the
                    # armature using vertex weights
                    # or whether it is parented to some bone of the armature
                    parent_bone_name = ob_child.getParentBoneName()
                    if parent_bone_name == None:
                        self.exportNode(ob_child, 'localspace',
                                        parent_block, ob_child.getName())
                    else:
                        # we should parent the object to the bone instead of
                        # to the armature
                        # so let's find that bone!
                        nif_bone_name = self.getFullName(parent_bone_name)
                        for block in self.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == nif_bone_name:
                                    self.exportNode(ob_child, 'localspace',
                                                    block, ob_child.getName())
                                    break
                        else:
                            assert(False) # BUG!



    def exportMatrix(self, obj, space, block):
        """Set a block's transform matrix to an object's
        transformation matrix in rest pose."""
        # decompose
        bscale, brot, btrans = self.getObjectSRT(obj, space)
        
        # and fill in the values
        block.translation.x = btrans[0]
        block.translation.y = btrans[1]
        block.translation.z = btrans[2]
        block.rotation.m11 = brot[0][0]
        block.rotation.m12 = brot[0][1]
        block.rotation.m13 = brot[0][2]
        block.rotation.m21 = brot[1][0]
        block.rotation.m22 = brot[1][1]
        block.rotation.m23 = brot[1][2]
        block.rotation.m31 = brot[2][0]
        block.rotation.m32 = brot[2][1]
        block.rotation.m33 = brot[2][2]
        block.velocity.x = 0.0
        block.velocity.y = 0.0
        block.velocity.z = 0.0
        block.scale = bscale

        return bscale, brot, btrans

    def getObjectMatrix(self, obj, space):
        """Get an object's matrix as NifFormat.Matrix44"""
        bscale, brot, btrans = self.getObjectSRT(obj, space)
        mat = NifFormat.Matrix44()
        
        mat.m41 = btrans[0]
        mat.m42 = btrans[1]
        mat.m43 = btrans[2]

        mat.m11 = brot[0][0] * bscale
        mat.m12 = brot[0][1] * bscale
        mat.m13 = brot[0][2] * bscale
        mat.m21 = brot[1][0] * bscale
        mat.m22 = brot[1][1] * bscale
        mat.m23 = brot[1][2] * bscale
        mat.m31 = brot[2][0] * bscale
        mat.m32 = brot[2][1] * bscale
        mat.m33 = brot[2][2] * bscale

        mat.m14 = 0.0
        mat.m24 = 0.0
        mat.m34 = 0.0
        mat.m44 = 1.0
        
        return mat

    def getObjectSRT(self, obj, space):
        """Find scale, rotation, and translation components of an object in
        the rest pose. Returns a triple (bs, br, bt), where bs
        is a scale float, br is a 3x3 rotation matrix, and bt is a
        translation vector. It should hold that
        ob.getMatrix(space) == bs * br * bt""" 
        # handle the trivial case first
        if (space == 'none'):
            return ( 1.0,
                     Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1]),
                     Blender.Mathutils.Vector([0, 0, 0]) )
        
        assert((space == 'worldspace') or (space == 'localspace'))

        # now write out spaces
        if (not type(obj) is Blender.Armature.Bone):
            # get world matrix
            mat = self.getObjectRestMatrix(obj, 'worldspace')
            # handle localspace: L * Ba * B * P = W
            # (with L localmatrix, Ba bone animation channel, B bone rest matrix (armature space), P armature parent matrix, W world matrix)
            # so L = W * P^(-1) * (Ba * B)^(-1)
            if (space == 'localspace'):
                if (obj.getParent() != None):
                    matparentinv = self.getObjectRestMatrix(obj.getParent(),
                                                            'worldspace')
                    matparentinv.invert()
                    mat *= matparentinv
                    if (obj.getParent().getType() == 'Armature'):
                        # the object is parented to the armature...
                        # we must get the matrix relative to the bone parent
                        bone_parent_name = obj.getParentBoneName()
                        if bone_parent_name:
                            bone_parent = obj.getParent().getData().bones[bone_parent_name]
                            # get bone parent matrix, including tail
                            # NOTE still a transform bug to iron out (see babelfish.nif)
                            matparentbone = self.getBoneRestMatrix(bone_parent, 'ARMATURESPACE', extra = True, tail = True)
                            matparentboneinv = Blender.Mathutils.Matrix(matparentbone)
                            matparentboneinv.invert()
                            mat *= matparentboneinv
        else: # bones, get the rest matrix
            assert(space == 'localspace') # in this function, we only need bones in localspace
            mat = self.getBoneRestMatrix(obj, 'BONESPACE')
        
        return self.decomposeSRT(mat)



    def decomposeSRT(self, mat):
        """Decompose Blender transform matrix as a scale, rotation matrix, and
        translation vector."""
        # get scale components
        b_scale_rot = mat.rotationPart()
        b_scale_rot_t = Blender.Mathutils.Matrix(b_scale_rot)
        b_scale_rot_t.transpose()
        b_scale_rot_2 = b_scale_rot * b_scale_rot_t
        b_scale = Blender.Mathutils.Vector(\
            b_scale_rot_2[0][0] ** 0.5,\
            b_scale_rot_2[1][1] ** 0.5,\
            b_scale_rot_2[2][2] ** 0.5)
        # and fix their sign
        if (b_scale_rot.determinant() < 0):
            b_scale.negate()
        # only uniform scaling
        # allow rather large error to accomodate some nifs
        if abs(b_scale[0]-b_scale[1]) + abs(b_scale[1]-b_scale[2]) > 0.02:
            raise NifExportError("""\
Non-uniform scaling not supported.
Workaround: apply size and rotation (CTRL-A).""")
        b_scale = b_scale[0]
        # get rotation matrix
        b_rot = b_scale_rot * (1.0 / b_scale)
        # get translation
        b_trans = mat.translationPart()
        # done!
        return b_scale, b_rot, b_trans



    def getBoneRestMatrix(self, bone, space, extra = True, tail = False):
        """Get bone matrix in rest position ("bind pose"). Space can be
        ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
        is BONESPACE (translation is bone head plus tail from parent bone).
        If tail is True then the matrix translation includes the bone tail."""
        # Retrieves the offset from the original NIF matrix, if existing
        corrmat = Blender.Mathutils.Matrix()
        if extra:
            try:
                corrmat = self.bonesExtraMatrixInv[bone.name]
            except KeyError:
                corrmat.identity()
        else:
            corrmat.identity()
        if (space == 'ARMATURESPACE'):
            mat = bone.matrix['ARMATURESPACE'].copy()
            if tail:
                tail_pos = bone.tail['ARMATURESPACE']
                mat[3][0] = tail_pos[0]
                mat[3][1] = tail_pos[1]
                mat[3][2] = tail_pos[2]
            return corrmat * mat
        elif (space == 'BONESPACE'):
            if bone.parent:
                # not sure why extra = True is required here
                # but if extra = extra then transforms are messed up, so keep
                # for now
                parinv = self.getBoneRestMatrix(bone.parent, 'ARMATURESPACE',
                                                extra = True, tail = False)
                parinv.invert()
                return self.getBoneRestMatrix(bone,
                                              'ARMATURESPACE',
                                              extra = extra,
                                              tail = tail) * parinv
            else:
                return self.getBoneRestMatrix(bone, 'ARMATURESPACE',
                                              extra = extra, tail = tail)
        else:
            assert(False) # bug!



    def getObjectRestMatrix(self, obj, space, extra = True):
        """Get the object's rest matrix; space can be 'localspace' or
        'worldspace'."""
        mat = Blender.Mathutils.Matrix(obj.getMatrix('worldspace')) # TODO cancel out IPO's
        if (space == 'localspace'):
            par = obj.getParent()
            if par:
                parinv = self.getObjectRestMatrix(par, 'worldspace')
                parinv.invert()
                mat *= parinv
        return mat



    def createBlock(self, blocktype):
        """Helper function to create a new block and register it in the list of
        exported blocks."""
        try:
            block = getattr(NifFormat, blocktype)()
        except AttributeError:
            raise NifExportError("'%s': Unknown block type (this is probably a bug).")
        return self.registerBlock(block)

    def registerBlock(self, block):
        """Helper function to register a newly created block in the list of
        exported blocks."""
        self.msg("registering '%s'"%block.__class__.__name__) # DEBUG
        self.blocks.append(block)
        return block


    def exportCollision(self, obj, parent_block):
        """Main function for adding collision object obj to a node.""" 
        if self.EXPORT_VERSION == 'Morrowind':
             if obj.rbShapeBoundType != Blender.Object.RBShapes['POLYHEDERON']:
                 raise NifExportError("""\
Morrowind only supports Polyhedron/Static TriangleMesh collisions.""")
             node = self.createBlock("RootCollisionNode")
             parent_block.addChild(node)
             node.flags = 0x0003 # default
             self.exportMatrix(obj, 'localspace', node)
             self.exportTriShapes(obj, 'none', node)

        elif self.EXPORT_VERSION == 'Oblivion':

            nodes = [ parent_block ]
            nodes.extend([ block for block in parent_block.children
                           if block.name[:14] == 'collisiondummy' ])
            for node in nodes:
                try:
                    self.exportCollisionHelper(obj, node)
                    break
                except ValueError: # adding collision failed
                    continue
            else: # all nodes failed so add new one
                node = NifFormat.NiNode()
                node.rotation = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
                node.scale = 1
                node.name = 'collisiondummy%i' % parent_block.numChildren
                node.flags = 0x000E # default
                parent_block.addChild(node)
                self.exportCollisionHelper(obj, node)

        else:
            print("""\
WARNING: only Morrowind and Oblivion collisions are supported, skipped
         collision object '%s'""" % obj.name)

    def exportCollisionHelper(self, obj, parent_block):
        """Helper function to add collision objects to a node."""

        # is it packed
        coll_ispacked = (obj.rbShapeBoundType == Blender.Object.RBShapes['POLYHEDERON'])

        # find physics properties
        material = self.EXPORT_OB_MATERIAL
        layer = self.EXPORT_OB_LAYER
        motionsys = self.EXPORT_OB_MOTIONSYSTEM
        # copy physics properties from Blender properties, if they exist
        for prop in obj.getAllProperties():
            if prop.getName() == 'HavokMaterial':
                material = getattr(NifFormat.HavokMaterial, prop.getData())
            elif prop.getName() == 'OblivionLayer':
                layer = getattr(NifFormat.OblivionLayer, prop.getData())
            #elif prop.getName() == 'MotionSystem':
            #    ob_mosys = getattr(NifFormat.MotionSystem, prop.getData())

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collisionObject:
            # note: collision settings are taken from lowerclasschair01.nif
            colobj = self.createBlock("bhkCollisionObject")
            parent_block.collisionObject = colobj
            colobj.target = parent_block
            colobj.unknownShort = 1

            colbody = self.createBlock("bhkRigidBody")
            colobj.body = colbody
            colbody.layer = layer
            colbody.unknown5Floats[1] = 3.8139e+36
            colbody.unknown4Shorts[0] = 1
            colbody.unknown4Shorts[1] = 65535
            colbody.unknown4Shorts[2] = 35899
            colbody.unknown4Shorts[3] = 16336
            colbody.layerCopy = layer
            colbody.unknown7Shorts[1] = 21280
            colbody.unknown7Shorts[2] = 4581
            colbody.unknown7Shorts[3] = 62977
            colbody.unknown7Shorts[4] = 65535
            colbody.unknown7Shorts[5] = 44
            colbody.translation.x = 0.0
            colbody.translation.y = 0.0
            colbody.translation.z = 0.0
            colbody.rotation.w = 1.0
            colbody.rotation.x = 0.0
            colbody.rotation.y = 0.0
            colbody.rotation.z = 0.0
            colbody.mass = 1.0 # will be fixed later
            colbody.linearDamping = 0.1
            colbody.angularDamping = 0.05
            colbody.friction = 0.3
            colbody.restitution = 0.3
            colbody.maxLinearVelocity = 250.0
            colbody.maxAngularVelocity = 31.4159
            colbody.penetrationDepth = 0.15
            colbody.motionSystem = motionsys
            colbody.unknownByte1 = self.EXPORT_OB_UNKNOWNBYTE1
            colbody.unknownByte2 = self.EXPORT_OB_UNKNOWNBYTE2
            colbody.qualityType = self.EXPORT_OB_QUALITYTYPE
            colbody.unknownInt6 = 3216641024
            colbody.unknownInt7 = 3249467941
            colbody.unknownInt8 = 83276283
            colbody.unknownInt9 = self.EXPORT_OB_WIND
        else:
            colbody = parent_block.collisionObject.body

        if coll_ispacked:
            self.exportCollisionPacked(obj, colbody, layer, material)
        else:
            if self.EXPORT_BHKLISTSHAPE:
                self.exportCollisionList(obj, colbody, layer, material)
            else:
                self.exportCollisionSingle(obj, colbody, layer, material)



    def exportCollisionPacked(self, obj, colbody, layer, material):
        """Add object ob as packed collision object to collision body colbody.
        If parent_block hasn't any collisions yet, a new packed list is created.
        If the current collision system is not a packed list of collisions (bhkPackedNiTriStripsShape), then
        a ValueError is raised."""

        if not colbody.shape:
            colshape = self.createBlock("bhkPackedNiTriStripsShape")

            if self.EXPORT_MOPP:
                colmopp = self.createBlock("bhkMoppBvTreeShape")
                colbody.shape = colmopp
                colmopp.material = material
                colmopp.unknown8Bytes[0] = 160
                colmopp.unknown8Bytes[1] = 13
                colmopp.unknown8Bytes[2] = 75
                colmopp.unknown8Bytes[3] = 1
                colmopp.unknown8Bytes[4] = 192
                colmopp.unknown8Bytes[5] = 207
                colmopp.unknown8Bytes[6] = 144
                colmopp.unknown8Bytes[7] = 11
                colmopp.unknownFloat = 1.0
                # the mopp origin, scale, and data are written later
                colmopp.shape = colshape
            else:
                colbody.shape = colshape

            colshape.unknownFloats[2] = 0.1
            colshape.unknownFloats[4] = 1.0
            colshape.unknownFloats[5] = 1.0
            colshape.unknownFloats[6] = 1.0
            colshape.unknownFloats[8] = 0.1
            colshape.scale = 1.0
            colshape.unknownFloats2[0] = 1.0
            colshape.unknownFloats2[1] = 1.0
        else:
            if self.EXPORT_MOPP:
                colmopp = colbody.shape
                colshape = colmopp.shape
            else:
                colshape = colbody.shape
            if not isinstance(colshape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError('not a packed list of collisions')

        mesh = obj.data
        transform = obj.getMatrix('localspace').copy()
        rotation = transform.rotationPart()

        vertices = [vert.co * transform for vert in mesh.verts]
        triangles = []
        normals = []
        for face in mesh.faces:
            if len(face.v) < 3:
                continue # ignore degenerate faces
            triangles.append([face.v[i].index for i in (0, 1, 2)])
            # note: face.no is a Python list, not a vector
            normals.append(Blender.Mathutils.Vector(face.no) * rotation)
            if len(face.v) == 4:
                triangles.append([face.v[i].index for i in (0, 2, 3)])
                normals.append(Blender.Mathutils.Vector(face.no) * rotation)

        colshape.addShape(triangles, normals, vertices, layer, material)



    def exportCollisionSingle(self, obj, colbody, layer, material):
        """Add collision object to colbody.
        If colbody already has a collision shape, throw ValueError."""
        if colbody.shape:
            raise ValueError('collision body already has a shape')
        colbody.shape = self.exportCollisionObject(obj, layer, material)



    def exportCollisionList(self, obj, colbody, layer, material):
        """Add collision object obj to the list of collision objects of colbody.
        If colbody has no collisions yet, a new list is created.
        If the current collision system is not a list of collisions
        (bhkListShape), then a ValueError is raised."""

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody -> bhkListShape
        # (this works in all cases, can be simplified just before
        # the file is written)
        if not colbody.shape:
            colshape = self.createBlock("bhkListShape")
            colbody.shape = colshape
            colshape.material = material
        else:
            colshape = colbody.shape
            if not isinstance(colshape, NifFormat.bhkListShape):
                raise ValueError('not a list of collisions')

        colshape.addShape(self.exportCollisionObject(obj, layer, material))



    def exportCollisionObject(self, obj, layer, material):
        """Export object obj as box, sphere, capsule, or convex hull.
        Note: polyheder is handled by exportCollisionPacked."""

        # find bounding box data
        minx = min([vert[0] for vert in obj.data.verts])
        miny = min([vert[1] for vert in obj.data.verts])
        minz = min([vert[2] for vert in obj.data.verts])
        maxx = max([vert[0] for vert in obj.data.verts])
        maxy = max([vert[1] for vert in obj.data.verts])
        maxz = max([vert[2] for vert in obj.data.verts])

        if obj.rbShapeBoundType in ( Blender.Object.RBShapes['BOX'],
                                    Blender.Object.RBShapes['SPHERE'] ):
            # note: collision settings are taken from lowerclasschair01.nif
            coltf = self.createBlock("bhkConvexTransformShape")
            coltf.material = material
            coltf.unknownFloat1 = 0.1
            coltf.unknown8Bytes[0] = 96
            coltf.unknown8Bytes[1] = 120
            coltf.unknown8Bytes[2] = 53
            coltf.unknown8Bytes[3] = 19
            coltf.unknown8Bytes[4] = 24
            coltf.unknown8Bytes[5] = 9
            coltf.unknown8Bytes[6] = 253
            coltf.unknown8Bytes[7] = 4
            hktf = obj.getMatrix('localspace').copy()
            # the translation part must point to the center of the data
            # so calculate the center in local coordinates
            center = Blender.Mathutils.Vector((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0)
            # and transform it to global coordinates
            center *= hktf
            hktf[3][0] = center[0]
            hktf[3][1] = center[1]
            hktf[3][2] = center[2]
            # we need to store the transpose of the matrix
            hktf.transpose()
            coltf.transform.setRows(*hktf)
            # fix matrix for havok coordinate system
            coltf.transform.m14 /= 7.0
            coltf.transform.m24 /= 7.0
            coltf.transform.m34 /= 7.0

            if obj.rbShapeBoundType == Blender.Object.RBShapes['BOX']:
                colbox = self.createBlock("bhkBoxShape")
                coltf.shape = colbox
                colbox.material = material
                colbox.radius = 0.1
                colbox.unknown8Bytes[0] = 0x6b
                colbox.unknown8Bytes[1] = 0xee
                colbox.unknown8Bytes[2] = 0x43
                colbox.unknown8Bytes[3] = 0x40
                colbox.unknown8Bytes[4] = 0x3a
                colbox.unknown8Bytes[5] = 0xef
                colbox.unknown8Bytes[6] = 0x8e
                colbox.unknown8Bytes[7] = 0x3e
                # fix dimensions for havok coordinate system
                colbox.dimensions.x = (maxx - minx) / 14.0
                colbox.dimensions.y = (maxy - miny) / 14.0
                colbox.dimensions.z = (maxz - minz) / 14.0
                colbox.minimumSize = min(colbox.dimensions.x, colbox.dimensions.y, colbox.dimensions.z)
            elif obj.rbShapeBoundType == Blender.Object.RBShapes['SPHERE']:
                colsphere = self.createBlock("bhkSphereShape")
                coltf.shape = colsphere
                colsphere.material = material
                # take average radius and
                # fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = (maxx + maxy + maxz - minx - miny -minz) / 42.0

            return coltf

        elif obj.rbShapeBoundType == Blender.Object.RBShapes['CYLINDER']:
            colcaps = self.createBlock("bhkCapsuleShape")
            colcaps.material = material
            # take average radius
            colcaps.radius = (maxx + maxy - minx - miny) / 4.0
            colcaps.radius1 = colcaps.radius
            colcaps.radius2 = colcaps.radius
            transform = obj.getMatrix('localspace').copy()
            vert1 = Blender.Mathutils.Vector( [ (maxx + minx)/2.0,
                                                (maxy + miny)/2.0,
                                                minz + colcaps.radius ] )
            vert2 = Blender.Mathutils.Vector( [ (maxx + minx) / 2.0,
                                                (maxy + miny) / 2.0,
                                                maxz - colcaps.radius ] )
            vert1 *= transform
            vert2 *= transform
            colcaps.firstPoint.x = vert1[0] / 7.0
            colcaps.firstPoint.y = vert1[1] / 7.0
            colcaps.firstPoint.z = vert1[2] / 7.0
            colcaps.secondPoint.x = vert2[0] / 7.0
            colcaps.secondPoint.y = vert2[1] / 7.0
            colcaps.secondPoint.z = vert2[2] / 7.0
            # fix havok coordinate system for radii
            colcaps.radius /= 7.0
            colcaps.radius1 /= 7.0
            colcaps.radius2 /= 7.0

            return colcaps

        elif obj.rbShapeBoundType == 5:
            # convex hull polytope; not in Python API
            # bound type has value 5
            mesh = obj.data
            transform = obj.getMatrix('localspace').copy()
            rotation = transform.rotationPart()
            scale = rotation.determinant()
            if scale < 0:
                scale = - (-scale) ** (1.0 / 3)
            else:
                scale = scale ** (1.0 / 3)
            rotation *= 1.0 / scale # /= not supported in Python API

            # calculate vertices, normals, and distances
            vertlist = [ vert.co * transform for vert in mesh.verts ]
            fnormlist = [ Blender.Mathutils.Vector(face.no) * rotation
                          for face in mesh.faces]
            fdistlist = [
                Blender.Mathutils.DotVecs(
                    -face.v[0].co * transform,
                    Blender.Mathutils.Vector(face.no) * rotation)
                for face in mesh.faces ]

            # remove duplicates through dictionary
            vertdict = {}
            for i, vert in enumerate(vertlist):
                vertdict[(int(vert[0]*200),
                          int(vert[1]*200),
                          int(vert[2]*200))] = i
            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0]*200),
                       int(norm[1]*200),
                       int(norm[2]*200),
                       int(dist*200))] = i
            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [ vertlist[vertdict[hsh]] for hsh in vertkeys ]
            fnormlist = [ fnormlist[fdict[hsh]] for hsh in fkeys ]
            fdistlist = [ fdistlist[fdict[hsh]] for hsh in fkeys ]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise NifExportError('ERROR%t|Too many faces/vertices. Decimate your mesh and try again.')
            
            colhull = self.createBlock("bhkConvexVerticesShape")
            colhull.material = material
            colhull.radius = 0.1
            colhull.unknown6Floats[2] = -0.0 # enables arrow detection
            colhull.unknown6Floats[5] = -0.0 # enables arrow detection
            # note: unknown 6 floats are usually all 0
            colhull.numVertices = len(vertlist)
            colhull.vertices.updateSize()
            for vhull, vert in zip(colhull.vertices, vertlist):
                vhull.x = vert[0] / 7.0
                vhull.y = vert[1] / 7.0
                vhull.z = vert[2] / 7.0
                # w component is 0
            colhull.numNormals = len(fnormlist)
            colhull.normals.updateSize()
            for nhull, norm, dist in zip(colhull.normals, fnormlist, fdistlist):
                nhull.x = norm[0]
                nhull.y = norm[1]
                nhull.z = norm[2]
                nhull.w = dist / 7.0

            return colhull

        else:
            raise NifExportError(
                'cannot export collision type %s to collision shape list'
                % obj.rbShapeBoundType)

    def exportAlphaProperty(self, flags = 0x00ED):
        """Return existing alpha property with given flags, or create new one
        if an alpha property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiAlphaProperty) \
               and block.flags == flags:
                return block
        # no alpha property with given flag found, so create new one
        alphaprop = self.createBlock("NiAlphaProperty")
        alphaprop.flags = flags
        return alphaprop        

    def exportSpecularProperty(self, flags = 0x00ED):
        """Return existing specular property with given flags, or create new one
        if a specular property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiSpecularProperty) \
               and block.flags == flags:
                return block
        # no specular property with given flag found, so create new one
        specprop = self.createBlock("NiSpecularProperty")
        specprop.flags = flags
        return specprop        

    def exportMaterialProperty(self, name = '', flags = 0x0001,
                               ambient = (1.0, 1.0, 1.0),
                               diffuse = (1.0, 1.0, 1.0),
                               specular = (0.0, 0.0, 0.0),
                               emissive = (0.0, 0.0, 0.0),
                               glossiness = 10.0,
                               alpha = 1.0):
        """Return existing material property with given settings, or create
        a new one if a material property with these settings is not found."""

        # create block (but don't register it yet in self.blocks)
        matprop = NifFormat.NiMaterialProperty()
   
        matprop.name = name
        matprop.flags = flags
        matprop.ambientColor.r = ambient[0]
        matprop.ambientColor.g = ambient[1]
        matprop.ambientColor.b = ambient[2]
        matprop.diffuseColor.r = diffuse[0]
        matprop.diffuseColor.g = diffuse[1]
        matprop.diffuseColor.b = diffuse[2]
        matprop.specularColor.r = specular[0]
        matprop.specularColor.g = specular[1]
        matprop.specularColor.b = specular[2]
        matprop.emissiveColor.r = emissive[0]
        matprop.emissiveColor.g = emissive[1]
        matprop.emissiveColor.b = emissive[2]
        matprop.glossiness = glossiness
        matprop.alpha = alpha

        # search for duplicate
        # (ignore the name string as sometimes import needs to create different
        # materials even when NiMaterialProperty is the same)
        for block in self.blocks:
            if isinstance(block, NifFormat.NiMaterialProperty) \
               and block.getHash(ignore_strings = True) == matprop.getHash(ignore_strings = True):
                return block

        # no material property with given settings found, so use and register
        # the new one
        return self.registerBlock(matprop)

    def exportTexDesc(self, texdesc = None, uvlayers = None, mtex = None):
        """Helper function for exportTexturingProperty to export each texture
        slot."""
        texdesc.isUsed = True

        try:
            texdesc.uvSet = uvlayers.index(mtex.uvlayer) if mtex.uvlayer else 0
        except ValueError: # mtex.uvlayer not in uvlayers list
            print("""\
WARNING: bad uv layer name '%s' in texture '%s'
         falling back on first uv layer""" % (mtex.uvlayer, mtex.tex.getName()))
            texdesc.uvSet = 0 # assume 0 is active layer

        texdesc.source = self.exportSourceTexture(mtex.tex)

    def exportTexturingProperty(
        self, flags = 0x0001, applymode = None, uvlayers = None,
        basemtex = None, glowmtex = None, bumpmtex = None, glossmtex = None,
        darkmtex = None, detailmtex = None):
        """Export texturing property. The parameters basemtex, glowmtex,
        bumpmtex, ... are the Blender material textures (MTex, not Texture)
        that correspond to the base, glow, bump map, ... textures. The uvlayers
        parameter is a list of uvlayer strings, that is, mesh.getUVLayers()."""

        texprop = NifFormat.NiTexturingProperty()

        texprop.flags = flags
        texprop.applyMode = applymode
        texprop.textureCount = 7

        if basemtex:
            texprop.hasBaseTexture = True
            self.exportTexDesc(texdesc = texprop.baseTexture,
                               uvlayers = uvlayers,
                               mtex = basemtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.tex.getName())
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.exportFlipController(fliptxt, basemtex.tex, texprop, 0)

        if glowmtex:
            texprop.hasGlowTexture = True
            self.exportTexDesc(texdesc = texprop.glowTexture,
                               uvlayers = uvlayers,
                               mtex = glowmtex)

        if bumpmtex:
            texprop.hasBumpMapTexture = True
            self.exportTexDesc(texdesc = texprop.bumpMapTexture,
                               uvlayers = uvlayers,
                               mtex = bumpmtex)
            texprop.bumpMapLumaScale = 1.0
            texprop.bumpMapLumaOffset = 0.0
            texprop.bumpMapMatrix.m11 = 1.0
            texprop.bumpMapMatrix.m12 = 0.0
            texprop.bumpMapMatrix.m21 = 0.0
            texprop.bumpMapMatrix.m22 = 1.0

        if glossmtex:
            texprop.hasGlossTexture = True
            self.exportTexDesc(texdesc = texprop.glossTexture,
                               uvlayers = uvlayers,
                               mtex = glossmtex)

        if darkmtex:
            texprop.hasDarkTexture = True
            self.exportTexDesc(texdesc = texprop.darkTexture,
                               uvlayers = uvlayers,
                               mtex = darkmtex)

        if detailmtex:
            texprop.hasDetailTexture = True
            self.exportTexDesc(texdesc = texprop.detailTexture,
                               uvlayers = uvlayers,
                               mtex = detailmtex)

        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiTexturingProperty) \
               and block.getHash() == texprop.getHash():
                return block

        # no texturing property with given settings found, so use and register
        # the new one
        return self.registerBlock(texprop)

    def exportTextureEffect(self, mtex = None):
        """Export a texture effect block from material texture mtex (MTex, not
        Texture)."""
        texeff = NifFormat.NiTextureEffect()
        texeff.flags = 4
        texeff.rotation.setIdentity()
        texeff.scale = 1.0
        texeff.modelProjectionMatrix.setIdentity()
        texeff.textureFiltering = NifFormat.TexFilterMode.FILTER_TRILERP
        texeff.textureClamping  = NifFormat.TexClampMode.WRAP_S_WRAP_T
        texeff.textureType = NifFormat.EffectType.EFFECT_ENVIRONMENT_MAP
        texeff.coordinateGenerationType = NifFormat.CoordGenType.CG_SPHERE_MAP
        if mtex:
            texeff.sourceTexture = self.exportSourceTexture(mtex.tex)
        texeff.unknownVector.x = 1.0
        texeff.ps2K = 65461
        return self.registerBlock(texeff)

def config_callback(**config):
    """Called when config script is done. Starts and times import."""
    starttime = Blender.sys.time()
    # run exporter
    NifExport(**config)
    # finish export
    print('nif export finished in %.2f seconds'
          % (Blender.sys.time() - starttime))
    Blender.Window.WaitCursor(0)

def fileselect_callback(filename):
    """Called once file is selected. Starts config GUI."""
    global _CONFIG
    _CONFIG.run(NifConfig.TARGET_EXPORT, filename, config_callback)

if __name__ == '__main__':
    _CONFIG = NifConfig() # use global so gui elements don't go out of skope
    Blender.Window.FileSelector(fileselect_callback, "Export NIF", _CONFIG.config["EXPORT_FILE"])
