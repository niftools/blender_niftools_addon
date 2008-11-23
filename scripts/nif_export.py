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

from itertools import izip

import Blender
from Blender import Ipo # for all the Ipo curve constants

from nif_common import NifImportExport
from nif_common import NifConfig
from nif_common import NifFormat
from nif_common import __version__

# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007-2008, NIF File Format Library and Tools
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
class NifExport(NifImportExport):
    IDENTITY44 = NifFormat.Matrix44()
    IDENTITY44.setIdentity()
    # map blending modes to apply modes
    APPLYMODE = {
        Blender.Texture.BlendModes["MIX"] : NifFormat.ApplyMode.APPLY_MODULATE,
        Blender.Texture.BlendModes["LIGHTEN"] : NifFormat.ApplyMode.APPLY_HILIGHT,
        Blender.Texture.BlendModes["MULTIPLY"] : NifFormat.ApplyMode.APPLY_HILIGHT2
    }
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38

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
                # reconstruct matrix from text
                b, m = ln.split('/')
                try:
                    mat = Blender.Mathutils.Matrix(
                        *[[float(f) for f in row.split(',')]
                          for row in m.split(';')])
                except:
                    raise NifExportError('Syntax error in BoneExMat buffer.')
                # Matrices are stored inverted for easier math later on.
                mat.invert()
                self.setBoneExtraMatrixInv(b, mat)

    def setBoneExtraMatrixInv(self, bonename, mat):
        """Set bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        self.bonesExtraMatrixInv[self.getBoneNameForBlender(bonename)] = mat

    def getBoneExtraMatrixInv(self, bonename):
        """Get bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        return self.bonesExtraMatrixInv[self.getBoneNameForBlender(bonename)]

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
        # blender bone naming -> nif bone naming
        unique_name = self.getBoneNameForNif(unique_name)
        # ensure uniqueness
        if unique_name in self.blockNames or unique_name in self.names.values():
            unique_int = 0
            old_name = unique_name
            while unique_name in self.blockNames or unique_name in self.names.values():
                unique_name = '%s.%02d' % (old_name, unique_int)
                unique_int += 1
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

    def getExportedObjects(self):
        """Return a list of exported objects."""
        exported_objects = []
        # iterating over self.blocks.itervalues() will count some objects
        # twice
        for obj in self.blocks.itervalues():
            # skip empty objects
            if obj is None:
                continue
            # detect doubles
            if obj in exported_objects:
                continue
            # append new object
            exported_objects.append(obj)
        # return the list of unique exported objects
        return exported_objects

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
        # dictionary mapping exported blocks to either None or to an
        # associated Blender object
        self.blocks = {}
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

        # store bone priorities (from NULL constraints) as the armature bones
        # are parsed, so they are available when writing the kf file
        # maps bone NiNode to priority value
        self.bonePriorities = {}

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
                # for morrowind: everything except keyframe controllers
                self.msg("Exporting geometry only")
            elif self.EXPORT_ANIMATION == 2:
                # for morrowind: only keyframe controllers
                self.msg("Exporting animation only (as .kf file)")

            for ob in Blender.Object.Get():
                # armatures should not be in rest position
                if ob.getType() == 'Armature':
                    # ensure we get the mesh vertices in animation mode,
                    # and not in rest position!
                    ob.data.restPosition = False
                    if (ob.data.envelopes):
                        print """'%s': Cannot export envelope skinning.
If you have vertex groups, turn off envelopes.
If you don't have vertex groups, select the bones one by one
press W to convert their envelopes to vertex weights,
and turn off envelopes."""%ob.getName()
                        raise NifExportError("""\
'%s': Cannot export envelope skinning. Check console for instructions."""
                                             % ob.getName())

                # check for non-uniform transforms
                # (lattices are not exported so ignore them as they often tend
                # to have non-uniform scaling)
                if ob.getType() != 'Lattice':
                    try:
                        self.decomposeSRT(ob.getMatrix('localspace'))
                    except NifExportError: # non-uniform scaling
                        raise NifExportError("""\
Non-uniform scaling not supported.
Workaround: apply size and rotation (CTRL-A) on '%s'.""" % ob.name)

            # extract some useful scene info
            self.scene = Blender.Scene.GetCurrent()
            context = self.scene.getRenderingContext()
            self.fspeed = 1.0 / context.framesPerSec()
            self.fstart = context.startFrame()
            self.fend = context.endFrame()
            
            # oblivion and civ4
            if (self.EXPORT_VERSION
                in ('Civilization IV', 'Oblivion', 'Fallout 3')):
                root_name = 'Scene Root'
            # other games
            else:
                root_name = self.filebase
     
            # get the root object from selected object
            # only export empties, meshes, and armatures
            if (Blender.Object.GetSelected() == None):
                raise NifExportError("""\
Please select the object(s) to export, and run this script again.""")
            root_objects = set()
            export_types = ('Empty','Mesh','Armature')
            for root_object in [ob for ob in Blender.Object.GetSelected()
                                if ob.getType() in export_types]:
                while (root_object.getParent() != None):
                    root_object = root_object.getParent()
                if root_object.getType() not in export_types:
                    raise NifExportError("""\
Root object (%s) must be an 'Empty', 'Mesh', or 'Armature' object."""
                                         % root_object.getName())
                root_objects.add(root_object)

            # smoothen seams of objects
            if self.EXPORT_SMOOTHOBJECTSEAMS:
                # get shared vertices
                self.msg("smoothing seams between objects...")
                vdict = {}
                for ob in [ob for ob in self.scene.objects
                           if ob.getType() == 'Mesh']:
                    mesh = ob.getData(mesh=1)
                    #for v in mesh.verts:
                    #    v.sel = False
                    for f in mesh.faces:
                        for v in f.verts:
                            vkey = (int(v.co[0]*200),
                                    int(v.co[1]*200),
                                    int(v.co[2]*200))
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
                    # take average of all face normals of faces that have this
                    # vertex
                    norm = Blender.Mathutils.Vector(0,0,0)
                    for v, f, mesh in vlist:
                        norm += f.no
                    norm.normalize()
                    # remove outliers (fixes better bodies issue)
                    # first calculate fitness of each face
                    fitlist = [Blender.Mathutils.DotVecs(f.no, norm)
                               for v, f, mesh in vlist]
                    bestfit = max(fitlist)
                    # recalculate normals only taking into account
                    # well-fitting faces
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
                self.msg("fixed normals on %i vertices" % nv)

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
                # export the root objects as a NiNodes; their children are
                # exported as well
                # note that localspace = worldspace, because root objects have
                # no parents
                self.exportNode(root_object, 'localspace',
                                root_block, root_object.getName())

            # post-processing:
            #-----------------

            # if we exported animations, but no animation groups are defined,
            # define a default animation group
            self.msg("Checking animation groups")
            if not animtxt:
                has_controllers = False
                for block in self.blocks:
                    # has it a controller field?
                    if isinstance(block, NifFormat.NiObjectNET):
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
            if animtxt and self.EXPORT_VERSION == "Morrowind":
                has_keyframecontrollers = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiKeyframeController):
                        has_keyframecontrollers = True
                        break
                if not has_keyframecontrollers:
                    self.msg("  defining dummy keyframe controller")
                    # add a trivial keyframe controller on the scene root
                    self.exportKeyframes(None, 'localspace', root_block)

            # oblivion skeleton export: check that all bones have a
            # transform controller and transform interpolator
            if self.EXPORT_VERSION in ("Oblivion", "Fallout 3") \
                and self.filebase.lower() in ('skeleton', 'skeletonbeast'):
                # here comes everything that is Oblivion skeleton export
                # specific
                self.msg("  adding controllers and interpolators for skeleton")
                for block in self.blocks.keys():
                    if isinstance(block, NifFormat.NiNode) \
                        and block.name == "Bip01":
                        for bone in block.tree(block_type = NifFormat.NiNode):
                            ctrl = self.createBlock("NiTransformController")
                            interp = self.createBlock("NiTransformInterpolator")

                            ctrl.interpolator = interp
                            bone.addController(ctrl)

                            ctrl.flags = 12
                            ctrl.frequency = 1.0
                            ctrl.phase = 0.0
                            ctrl.startTime = self.FLOAT_MAX
                            ctrl.stopTime = self.FLOAT_MIN
                            interp.translation.x = bone.translation.x
                            interp.translation.y = bone.translation.y
                            interp.translation.z = bone.translation.z
                            scale, quat = bone.rotation.getScaleQuat()
                            interp.rotation.x = quat.x
                            interp.rotation.y = quat.y
                            interp.rotation.z = quat.z
                            interp.rotation.w = quat.w
                            interp.scale = bone.scale
            else:
                # here comes everything that should be exported EXCEPT
                # for Oblivion skeleton exports
                # export animation groups (not for skeleton.nif export!)
                if animtxt:
                    anim_textextra = self.exportAnimGroups(animtxt, root_block)

            # oblivion furniture markers
            if (self.EXPORT_VERSION in ('Oblivion', 'Fallout 3')
                and self.filebase[:15].lower() == 'furnituremarker'):
                # exporting a furniture marker for Oblivion
                try:
                    furniturenumber = int(self.filebase[15:])
                except ValueError:
                    raise NifExportError("""\
Furniture marker has invalid number (%s). Name your file 
'furnituremarkerxx.nif' where xx is a number between 00 and 19."""
                                         % self.filebase[15:])
                # name scene root name the file base name
                root_name = self.filebase
                # create furniture marker block
                furnmark = self.createBlock("BSFurnitureMarker")
                furnmark.name = "FRN"
                furnmark.numPositions = 1
                furnmark.positions.updateSize()
                furnmark.positions[0].positionRef1 = furniturenumber
                furnmark.positions[0].positionRef2 = furniturenumber
                # create extra string data sgoKeep
                sgokeep = self.createBlock("NiStringExtraData")
                sgokeep.name = "UBP"
                sgokeep.stringData = "sgoKeep"
                # add extra blocks
                root_block.addExtraData(furnmark)
                root_block.addExtraData(sgokeep)

            self.msg("Checking collision")
            # activate oblivion collision and physics
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                hascollision = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkCollisionObject):
                       hascollision = True
                       break
                if hascollision:
                    # enable collision
                    bsx = self.createBlock("BSXFlags")
                    bsx.name = 'BSX'
                    bsx.integerData = self.EXPORT_OB_BSXFLAGS
                    root_block.addExtraData(bsx)
                # update rigid body center of gravity and mass
                # first calculate distribution of mass
                total_mass = 0
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkRigidBody):
                        block.updateMassCenterInertia(
                            solid = self.EXPORT_OB_SOLID)
                        total_mass += block.mass
                # now update the mass ensuring that total mass is
                # self.EXPORT_OB_MASS
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkRigidBody):
                        block.updateMassCenterInertia(
                            mass = self.EXPORT_OB_MASS * block.mass / total_mass,
                            solid = self.EXPORT_OB_SOLID)

                # many Oblivion nifs have a UPB, but export is disabled as
                # they do not seem to affect anything in the game
                #upb = self.createBlock("NiStringExtraData")
                #upb.name = 'UPB'
                #upb.stringData = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                #root_block.addExtraData(upb)

            # export constraints
            for b_obj in self.getExportedObjects():
                self.exportConstraints(b_obj, root_block)

            # export weapon location
            if self.EXPORT_VERSION in ("Oblivion", "Fallout 3"):
                if self.EXPORT_OB_PRN != "NONE":
                    # add string extra data
                    prn = self.createBlock("NiStringExtraData")
                    prn.name = 'Prn'
                    prn.stringData = {
                        "BACK": "BackWeapon",
                        "SIDE": "SideWeapon",
                        "QUIVER": "Quiver",
                        "SHIELD": "Bip01 L ForearmTwist",
                        "HELM": "Bip01 Head",
                        "RING": "Bip01 R Finger1"}[self.EXPORT_OB_PRN]
                    root_block.addExtraData(prn)

            # add vertex color and zbuffer properties for civ4 and railroads
            if self.EXPORT_VERSION in ["Civilization IV",
                                       "Sid Meier's Railroads"]:
                self.exportVertexColorProperty(root_block)
                self.exportZBufferProperty(root_block)

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
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkMoppBvTreeShape):
                       self.msg("Generating mopp...")
                       block.updateMopp()
                       #print "=== DEBUG: MOPP TREE ==="
                       #block.parseMopp(verbose = True)
                       #print "=== END OF MOPP TREE ==="

            # delete original scene root if a scene root object was already
            # defined
            if (root_block.numChildren == 1) \
               and (root_block.children[0].name in ['Scene Root', 'Bip01']):
                self.msg(
                    "Making '%s' the root block" % root_block.children[0].name)
                # remove root_block from self.blocks
                self.blocks.pop(root_block)
                # set new root block
                old_root_block = root_block
                root_block = old_root_block.children[0]
                # copy extra data and properties
                for extra in old_root_block.getExtraDatas():
                    # delete links in extras to avoid parentship problems
                    extra.nextExtraData = None
                    # now add it
                    root_block.addExtraData(extra)
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
                # find all nodes and keyframe controllers
                node_kfctrls = {}
                for node in root_block.tree():
                    if not isinstance(node, NifFormat.NiNode):
                        continue
                    ctrls = node.getControllers()
                    for ctrl in ctrls:
                        if not isinstance(ctrl,
                                          NifFormat.NiKeyframeController):
                            continue
                        if not node in node_kfctrls:
                            node_kfctrls[node] = []
                        node_kfctrls[node].append(ctrl)
                # morrowind
                if self.EXPORT_VERSION == "Morrowind":
                    # create kf root header
                    kf_root = self.createBlock("NiSequenceStreamHelper")
                    kf_root.addExtraData(anim_textextra)
                    # reparent controller tree
                    for node, ctrls in node_kfctrls.iteritems():
                        for ctrl in ctrls:
                            # create node reference by name
                            nodename_extra = self.createBlock(
                                "NiStringExtraData")
                            nodename_extra.bytesRemaining = len(node.name) + 4
                            nodename_extra.stringData = node.name

                            # break the controller chain
                            ctrl.nextController = None

                            # add node reference and controller
                            kf_root.addExtraData(nodename_extra)
                            kf_root.addController(ctrl)
                # oblivion
                elif self.EXPORT_VERSION in ("Oblivion", "Fallout 3",
                                             "Civilization IV"):
                    # create kf root header
                    kf_root = self.createBlock("NiControllerSequence")
                    kf_root.name = self.filebase
                    kf_root.unknownInt1 = 1
                    kf_root.weight = 1.0
                    kf_root.textKeys = anim_textextra
                    kf_root.cycleType = NifFormat.CycleType.CYCLE_CLAMP
                    kf_root.frequency = 1.0
                    kf_root.startTime =(self.fstart - 1) * self.fspeed
                    kf_root.stopTime = (self.fend - self.fstart) * self.fspeed
                    # quick hack to set correct target name
                    if "Bip01" in [node.name for
                                   node in node_kfctrls.iterkeys()]:
                        targetname = "Bip01"
                    else:
                        targetname = root_block.name
                    kf_root.targetName = targetname
                    kf_root.stringPalette = NifFormat.NiStringPalette()
                    # create ControlledLink for each controlled block
                    kf_root.numControlledBlocks = len(node_kfctrls)
                    kf_root.controlledBlocks.updateSize()
                    for controlledblock, node, ctrls \
                        in izip(kf_root.controlledBlocks,
                                node_kfctrls.iterkeys(),
                                node_kfctrls.itervalues()):
                        # only export first keyframe controller
                        ctrl = ctrls[0]
                        controlledblock.interpolator = ctrl.interpolator
                        # get bone animation priority (previously fetched from
                        # the constraints during exportBones)
                        if not node in self.bonePriorities:
                            priority = 26
                            self.msg("""\
no priority set for bone %s, falling back on default value (%i)"""
                                     % (node.name, priority))
                        else:
                            priority = self.bonePriorities[node]
                        controlledblock.priority = priority
                        # set palette, and node and controller type names
                        controlledblock.stringPalette = kf_root.stringPalette
                        controlledblock.setNodeName(node.name)
                        controlledblock.setControllerType(ctrl.__class__.__name__)
                else:
                    raise NifExportError("""\
Keyframe export for '%s' is not supported. Only Morrowind, Oblivion, Fallout 3,
and Civilization IV keyframes are supported.""" % self.EXPORT_VERSION)

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
                NifFormat.write(
                    f,
                    version = self.version, user_version = NIF_USER_VERSION,
                    roots = [root_block])
            finally:
                f.close()

        except NifExportError, e: # export error: raise a menu instead of an exception
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('EXPORT ERROR%t|' + str(e))
            print 'NifExportError: ' + str(e)
            return

        except IOError, e: # IO error: raise a menu instead of an exception
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('I/O ERROR%t|' + str(e))
            print 'IOError: ' + str(e)
            return

        except StandardError, e: # other error: raise a menu and an exception
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('ERROR%t|' + str(e) + '    Check console for possibly more details.')
            raise

        finally:
            # clear progress bar
            self.msgProgress("Finished", progbar = 1)

        # save exported file (this is used by the test suite)
        self.root_blocks = [root_block]



    def exportNode(self, ob, space, parent_block, node_name):
        """
        Export a mesh/armature/empty object ob as child of parent_block.
        Export also all children of ob.
          - space is 'none', 'worldspace', or 'localspace', and determines
            relative to what object the transformation should be stored.
          - parent_block is the parent nif block of the object (None for the
            root node)
          - for the root node, ob is None, and node_name is usually the base
            filename (either with or without extension)
        """
        # ob_type: determine the block type
        #          (None, 'Mesh', 'Empty' or 'Armature')
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
            elif ob_type == 'Mesh' and ob.name.lower()[:7] == 'bsbound':
                # add a bounding box
                self.exportBSBound(ob, parent_block)
                return None # done; stop here
            elif ob_type == 'Mesh':
                # -> mesh data.
                # If this has children or animations or more than one material
                # it gets wrapped in a purpose made NiNode.
                is_collision = (ob.getDrawType()
                                == Blender.Object.DrawTypes['BOUNDBOX'])
                has_ipo = ob_ipo and len(ob_ipo.getCurves()) > 0
                has_children = len(ob_children) > 0
                is_multimaterial = len(set([f.mat for f in ob.data.faces])) > 1
                # determine if object tracks camera
                has_track = False
                for constr in ob.constraints:
                    if constr.type == Blender.Constraint.Type.TRACKTO:
                        has_track = True
                        break
                if is_collision:
                    self.exportCollision(ob, parent_block)
                    return None # done; stop here
                elif has_ipo or has_children or is_multimaterial or has_track:
                    # -> mesh ninode for the hierarchy to work out
                    if not has_track:
                        node = self.createBlock('NiNode', ob)
                    else:
                        node = self.createBlock('NiBillboardNode', ob)
                else:
                    # don't create intermediate ninode for this guy
                    self.exportTriShapes(ob, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.createBlock("NiNode", ob)

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
        if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
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
    def exportKeyframes(self, ipo, space, parent_block, bind_mat = None,
                        extra_mat_inv = None):
        if self.EXPORT_ANIMATION == 1 and self.version < 0x0A020000:
            # keyframe controllers are not present in geometry only files
            # for more recent versions, the controller and interpolators are
            # present, only the data is not present (see further on)
            return

        # only localspace keyframes need to be exported
        assert(space == 'localspace')

        # make sure the parent is of the right type
        assert(isinstance(parent_block, NifFormat.NiNode))
        
        # add a keyframecontroller block, and refer to this block in the
        # parent's time controller
        if self.version < 0x0A020000:
            kfc = self.createBlock("NiKeyframeController", ipo)
        else:
            kfc = self.createBlock("NiTransformController", ipo)
            kfi = self.createBlock("NiTransformInterpolator", ipo)
            # link interpolator from the controller
            kfc.interpolator = kfi
            # set interpolator default data
            scale, quat, trans = \
                parent_block.getTransform().getScaleQuatTranslation()
            kfi.translation.x = trans.x
            kfi.translation.y = trans.y
            kfi.translation.z = trans.z
            kfi.rotation.x = quat.x
            kfi.rotation.y = quat.y
            kfi.rotation.z = quat.z
            kfi.rotation.w = quat.w
            kfi.scale = scale

        parent_block.addController(kfc)

        # fill in the non-trivial values
        kfc.flags = 0x0008
        kfc.frequency = 1.0
        kfc.phase = 0.0
        kfc.startTime = (self.fstart - 1) * self.fspeed
        kfc.stopTime = (self.fend - self.fstart) * self.fspeed

        if self.EXPORT_ANIMATION == 1:
            # keyframe data is not present in geometry files
            return

        # -> get keyframe information
        
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
            extra_scale_inv, extra_rot_inv, extra_trans_inv = \
                self.decomposeSRT(extra_mat_inv)
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
            # the following code makes these assumptions
            assert(Ipo.PO_SCALEX == Ipo.OB_SCALEX)
            assert(Ipo.PO_LOCX == Ipo.OB_LOCX)
            # check validity of curves
            for curvecollection in (
                (Ipo.PO_SCALEX, Ipo.PO_SCALEY, Ipo.PO_SCALEZ),
                (Ipo.PO_LOCX, Ipo.PO_LOCY, Ipo.PO_LOCZ),
                (Ipo.PO_QUATX, Ipo.PO_QUATY, Ipo.PO_QUATZ, Ipo.PO_QUATW),
                (Ipo.OB_ROTX, Ipo.OB_ROTY, Ipo.OB_ROTZ)):
                # skip invalid curves
                try:
                    ipo[curvecollection[0]]
                except KeyError:
                    continue
                # check that if any curve is defined in the collection
                # then all curves are defined in the collection
                if (any(ipo[curve] for curve in curvecollection)
                    and not all(ipo[curve] for curve in curvecollection)):
                    keytype = {Ipo.PO_SCALEX: "SCALE",
                               Ipo.PO_LOCX: "LOC",
                               Ipo.PO_QUATX: "ROT",
                               Ipo.OB_ROTX: "ROT"}
                    raise NifExportError("""\
missing curves in %s; insert %s key at frame 1 and try again"""
                                         % (ipo, keytype[curvecollection[0]]))
            # go over all curves
            ipo_curves = ipo.curveConsts.values()
            for curve in ipo_curves:
                # skip empty curves
                if ipo[curve] is None:
                    continue
                # non-empty curve: go over all frames of the curve
                for btriple in ipo[curve].bezierPoints:
                    frame = btriple.pt[0]
                    if (frame < self.fstart) or (frame > self.fend):
                        continue
                    # PO_SCALEX == OB_SCALEX, so this does both pose and object
                    # scale
                    if curve in (Ipo.PO_SCALEX, Ipo.PO_SCALEY, Ipo.PO_SCALEZ):
                        # support only uniform scaling... take the mean
                        scale_curve[frame] = (ipo[Ipo.PO_SCALEX][frame]
                                              + ipo[Ipo.PO_SCALEY][frame]
                                              + ipo[Ipo.PO_SCALEZ][frame]) / 3.0
                        # SC' * SB' / SX
                        scale_curve[frame] = \
                            scale_curve[frame] * bind_scale * extra_scale_inv
                    # object rotation
                    elif curve in (Ipo.OB_ROTX, Ipo.OB_ROTY, Ipo.OB_ROTZ):
                        rot_curve[frame] = Blender.Mathutils.Euler(
                            [10 * ipo[Ipo.OB_ROTX][frame],
                             10 * ipo[Ipo.OB_ROTY][frame],
                             10 * ipo[Ipo.OB_ROTZ][frame]]).toQuat()
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # pose rotation
                    elif curve in (Ipo.PO_QUATX, Ipo.PO_QUATY,
                                   Ipo.PO_QUATZ, Ipo.PO_QUATW):
                        rot_curve[frame] = Blender.Mathutils.Quaternion()
                        rot_curve[frame].x = ipo[Ipo.PO_QUATX][frame]
                        rot_curve[frame].y = ipo[Ipo.PO_QUATY][frame]
                        rot_curve[frame].z = ipo[Ipo.PO_QUATZ][frame]
                        rot_curve[frame].w = ipo[Ipo.PO_QUATW][frame]
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                    # PO_LOCX == OB_LOCX, so this does both pose and object
                    # location
                    elif curve in (Ipo.PO_LOCX, Ipo.PO_LOCY, Ipo.PO_LOCZ):
                        trans_curve[frame] = Blender.Mathutils.Vector(
                            [ipo[Ipo.PO_LOCX][frame],
                             ipo[Ipo.PO_LOCY][frame],
                             ipo[Ipo.PO_LOCZ][frame]])
                        # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
                        trans_curve[frame] *= bind_scale
                        trans_curve[frame] *= bind_rot
                        trans_curve[frame] += bind_trans
                        # we need RC' and SC'
                        if Ipo.OB_ROTX in ipo_curves and ipo[Ipo.OB_ROTX]:
                            rot_c = Blender.Mathutils.Euler(
                                [10 * ipo[Ipo.OB_ROTX][frame],
                                 10 * ipo[Ipo.OB_ROTY][frame],
                                 10 * ipo[Ipo.OB_ROTZ][frame]]).toMatrix()
                        elif Ipo.PO_QUATX in ipo_curves and ipo[Ipo.PO_QUATX]:
                            rot_c = Blender.Mathutils.Quaternion()
                            rot_c.x = ipo[Ipo.PO_QUATX][frame]
                            rot_c.y = ipo[Ipo.PO_QUATY][frame]
                            rot_c.z = ipo[Ipo.PO_QUATZ][frame]
                            rot_c.w = ipo[Ipo.PO_QUATW][frame]
                            rot_c = rot_c.toMatrix()
                        else:
                            rot_c = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
                        # note, PO_SCALEX == OB_SCALEX, so this does both
                        if ipo[Ipo.PO_SCALEX]:
                            # support only uniform scaling... take the mean
                            scale_c = (ipo[Ipo.PO_SCALEX][frame]
                                       + ipo[Ipo.PO_SCALEY][frame]
                                       + ipo[Ipo.PO_SCALEZ][frame]) / 3.0
                        else:
                            scale_c = 1.0
                        trans_curve[frame] += \
                            extra_trans_inv * rot_c * bind_rot * \
                            scale_c * bind_scale

        # -> now comes the real export

        if max(len(rot_curve), len(trans_curve), len(scale_curve)) <= 1 \
            and self.version >= 0x0A020000:
            # only add data if number of keys is > 1
            # (see importer comments with importKfRoot: a single frame
            # keyframe denotes an interpolator without further data)
            # insufficient keys, so set the data and we're done!
            if trans_curve:
                trans = trans_curve.values()[0]
                kfi.translation.x = trans[0]
                kfi.translation.y = trans[1]
                kfi.translation.z = trans[2]
            if rot_curve:
                rot = rot_curve.values()[0]
                kfi.rotation.x = rot.x
                kfi.rotation.y = rot.y
                kfi.rotation.z = rot.z
                kfi.rotation.w = rot.w
            # ignore scale for now...
            kfi.scale = 1.0
            # done!
            return

        # add the keyframe data
        if self.version < 0x0A020000:
            kfd = self.createBlock("NiKeyframeData", ipo)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.createBlock("NiTransformData", ipo)
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
        for i, frame in enumerate(frames):
            scale_frame = kfd.scales.keys[i]
            scale_frame.time = (frame - 1) * self.fspeed
            scale_frame.value = scale_curve[frame]

    def exportVertexColorProperty(self, block_parent,
                                  flags = 1,
                                  vertex_mode = 0, lighting_mode = 1):
        """Create a vertex color property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param vertex_mode: The C{vertexMode} of the new property.
        @param lighting_mode: The C{lightingMode} of the new property.
        @return: The new property block.
        """
        # create new vertex color property block
        vcolprop = self.createBlock("NiVertexColorProperty")
        
        # make it a property of the parent
        block_parent.addProperty(vcolprop)

        # and now export the parameters
        vcolprop.flags = flags
        vcolprop.vertexMode = vertex_mode
        vcolprop.lightingMode = lighting_mode

        return vcolprop

    def exportZBufferProperty(self, block_parent,
                              flags = 15, function = 3):
        """Create a z-buffer property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param function: The C{function} of the new property.
        @return: The new property block.
        """
        # create new z-buffer property block
        zbuf = self.createBlock("NiZBufferProperty")

        # make it a property of the parent
        block_parent.addProperty(zbuf)

        # and now export the parameters
        zbuf.flags = 15
        zbuf.function = 3

        return zbuf

    def exportAnimGroups(self, animtxt, block_parent):
        """Parse the animation groups buffer and write an extra string
        data block, and attach it to an existing block (typically, the root
        of the nif tree)."""
        if self.EXPORT_ANIMATION == 1:
            # animation group extra data is not present in geometry only files
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
            # ignore empty lines
            if not s:
                continue
            # parse line
            t = s.split('/')
            if (len(t) < 2):
                raise NifExportError("Syntax error in Anim buffer ('%s')" % s)
            f = int(t[0])
            if ((f < self.fstart) or (f > self.fend)):
                raise NifExportError("""\
Error in Anim buffer: frame out of range (%i not in [%i, %i])"""
                                     % (f, self.fstart, self.fend))
            d = t[1].strip(' ')
            for i in range(2, len(t)):
                d = d + '\r\n' + t[i].strip(' ')
            #print 'frame %d'%f + ' -> \'%s\''%d # debug
            flist.append(f)
            dlist.append(d)
        
        # -> now comes the real export
        
        # add a NiTextKeyExtraData block, and refer to this block in the
        # parent node (we choose the root block)
        textextra = self.createBlock("NiTextKeyExtraData", animtxt)
        block_parent.addExtraData(textextra)
        
        # create a text key for each frame descriptor
        textextra.numTextKeys = len(flist)
        textextra.textKeys.updateSize()
        for i, key in enumerate(textextra.textKeys):
            key.time = self.fspeed * (flist[i]-1)
            key.value = dlist[i]

        return textextra


    def exportSourceTexture(self, texture, filename = None):
        """Export a NiSourceTexture.

        @param texture: The texture object in blender to be exported.
        @param filename: The full or relative path to the texture file
            (this argument is used when exporting NiFlipControllers).
        @return: The exported NiSourceTexture block."""
        
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

            # check that image is loaded
            if texture.getImage() is None:
                raise NifExportError(
                    "image type texture has no file loaded ('%s')"
                    %texture.getName())                    

            # texture must not be packed
            if texture.getImage().packed:
                raise NifExportError(
                    "export of packed textures is not supported ('%s')"
                    %texture.getName())
            
            tfn = texture.image.getFilename()

            if not self.EXPORT_VERSION in ('Morrowind', 'Oblivion',
                                           'Fallout 3'):
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

        # no identical source texture found, so use and register
        # the new one
        return self.registerBlock(srctex, texture)



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
        tlist = fliptxt.asLines()

        # create a NiFlipController
        flip = self.createBlock("NiFlipController", fliptxt)
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
        self.msg("Exporting %s" % ob)
        self.msgProgress("Exporting %s" % ob.name)
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

        # is mesh double sided?
        mesh_doublesided = (mesh.mode & Blender.Mesh.Modes.TWOSIDED)

        # let's now export one trishape for every mesh material
        ### TODO: needs refactoring - move material, texture, etc.
        ### to separate function
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
            mesh_haswire = False  # mesh rendered as wireframe
            mesh_hasspec = False  # mesh has specular properties
            mesh_hasvcol = False
            mesh_hasnormals = False
            if (mesh_mat != None):
                mesh_hasnormals = True # for proper lighting
                # for non-textured materials, vertex colors are used to color
                # the mesh
                # for textured materials, they represent lighting details
                mesh_hasvcol = mesh.vertexColors
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
                                or (mesh_mat.getIpo() != None
                                    and mesh_mat.getIpo().getCurve('Alpha'))
                mesh_haswire = mesh_mat.mode & Blender.Material.Modes.WIRE
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
                if mesh_uvlayers:
                    # if we have uv coordinates
                    # double check that we have uv data
                    if not mesh.faceUV or len(f.uv) != len(f.v):
                        raise NifExportError(
                            'ERROR%t|Create a UV map for every texture, and run the script again.')
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
                trishape = self.createBlock("NiTriShape", ob)
            else:
                trishape = self.createBlock("NiTriStrips", ob)

            # add texture effect block (must be added as preceeding child of
            # the trishape)
            if self.EXPORT_VERSION == "Morrowind" and mesh_texeff_mtex:
                # create a new parent block for this shape
                extra_node = self.createBlock("NiNode", mesh_texeff_mtex)
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
                # (Morrowind's child naming convention)
                trishape.name += " %i"%materialIndex
            trishape.name = self.getFullName(trishape.name)
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
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
                alphaflags = 0x12ED # do we need to customize this by game?
                trishape.addProperty(
                    self.exportAlphaProperty(flags = alphaflags))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.addProperty(self.exportWireframeProperty(flags = 1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.addProperty(self.exportStencilProperty())

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
                if not(ipo is None):
                    a_curve = ipo[Ipo.MA_ALPHA]
                
                if not(a_curve is None):
                    # get the alpha keyframes from blender's ipo curve
                    alpha = {}
                    for btriple in a_curve.getPoints():
                        knot = btriple.getPoints()
                        frame = knot[0]
                        ftime = (frame - self.fstart) * self.fspeed
                        alpha[ftime] = ipo[Ipo.MA_ALPHA][frame]

                    # add and link alpha controller, data and interpolator blocks
                    alphac = self.createBlock("NiAlphaController", ipo)
                    alphad = self.createBlock("NiFloatData", ipo)
                    alphai = self.createBlock("NiFloatInterpolator", ipo)

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
                tridata = self.createBlock("NiTriShapeData", ob)
            else:
                tridata = self.createBlock("NiTriStripsData", ob)
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
            tridata.setTriangles(trilist,
                                 stitchstrips = self.EXPORT_STITCHSTRIPS)

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
                    # the vertgroups that correspond to bonenames are bones
                    # that influence the mesh
                    boneinfluences = []
                    for bone in bonenames:
                        if bone in vertgroups:
                            boneinfluences.append(bone)
                    if boneinfluences: # yes we have skinning!
                        # create new skinning instance block and link it
                        skininst = self.createBlock("NiSkinInstance", ob)
                        trishape.skinInstance = skininst
                        for block in self.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == self.getFullName(armaturename):
                                    skininst.skeletonRoot = block
                                    break
                        else:
                            raise NifExportError(
                                "Skeleton root '%s' not found."%armaturename)
            
                        # create skinning data and link it
                        skindata = self.createBlock("NiSkinData", ob)
                        skininst.data = skindata
            
                        skindata.hasVertexWeights = True
                        # fix geometry rest pose: transform relative to
                        # skeleton root
                        skindata.setTransform(
                            self.getObjectMatrix(ob, 'localspace').getInverse())
            
                        # add vertex weights
                        # first find weights and normalization factors
                        vert_list = {}
                        vert_norm = {}
                        for bone in boneinfluences:
                            try:
                                vert_list[bone] = ob.data.getVertsFromGroup(bone, 1)
                            except AttributeError:
                                # this happens when the vertex group has been
                                # added, but the weights have not been painted
                                raise NifExportError("""\
Mesh %s has vertex group for bone %s, but no weights.
Please select the mesh, and either delete the vertex group, or
go to weight paint mode, and paint weights.""" % (ob.name, bone))
                            for v in vert_list[bone]:
                                if vert_norm.has_key(v[0]):
                                    vert_norm[v[0]] += v[1]
                                else:
                                    vert_norm[v[0]] = v[1]
                        
                        # for each bone, first we get the bone block
                        # then we get the vertex weights
                        # and then we add it to the NiSkinData
                        # note: allocate memory for faster performance
                        vert_added = [False for i in xrange(len(vertlist))]
                        for bone_index, bone in enumerate(boneinfluences):
                            # find bone in exported blocks
                            bone_block = None
                            for block in self.blocks:
                                if isinstance(block, NifFormat.NiNode):
                                    if block.name == self.getFullName(bone):
                                        if not bone_block:
                                            bone_block = block
                                        else:
                                            raise NifExportError("""\
multiple bones with name '%s': probably you have multiple armatures, please
parent all meshes to a single armature and try again""" % bone)
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
                                trishape.addBone(bone_block, vert_weights)
            
                        # each vertex must have been assigned to at least one
                        # vertex group
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

                        # calculate center and radius for each skin bone data
                        # block
                        trishape.updateSkinCenterRadius()

                        if (self.version >= 0x04020100
                            and self.EXPORT_SKINPARTITION):
                            self.msg("  creating skin partition")
                            lostweight = trishape.updateSkinPartition(
                                maxbonesperpartition=self.EXPORT_BONESPERPARTITION,
                                maxbonespervertex=self.EXPORT_BONESPERVERTEX,
                                stripify=self.EXPORT_STRIPIFY,
                                stitchstrips=self.EXPORT_STITCHSTRIPS,
                                padbones=self.EXPORT_PADBONES)
                            # warn on bad config settings
                            if self.EXPORT_VERSION == 'Oblivion':
                               if self.EXPORT_PADBONES:
                                   print("""\
WARNING: using padbones on Oblivion export, you probably do not want to do this
         disable the pad bones option to get higher quality skin partitions""")
                            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                               if self.EXPORT_BONESPERPARTITION < 18:
                                   print("""\
WARNING: using less than 18 bones per partition on Oblivion/Fallout 3 export
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
                        morphctrl = self.createBlock("NiGeomMorpherController",
                                                     keyipo)
                        trishape.addController(morphctrl)
                        morphctrl.target = trishape
                        morphctrl.frequency = 1.0
                        morphctrl.phase = 0.0
                        ctrlStart = 1000000.0
                        ctrlStop = -1000000.0
                        ctrlFlags = 0x000c
                        
                        # create geometry morph data
                        morphdata = self.createBlock("NiMorphData", keyipo)
                        morphctrl.data = morphdata
                        morphdata.numMorphs = len(key.getBlocks())
                        morphdata.numVertices = len(vertlist)
                        morphdata.morphs.updateSize()
                        
                        for keyblocknum, keyblock in enumerate(key.getBlocks()):
                            # export morphed vertices
                            morph = morphdata.morphs[keyblocknum]
                            self.msg("  exporting morph %i: vertices"
                                     % keyblocknum)
                            morph.arg = morphdata.numVertices
                            morph.vectors.updateSize()
                            for b_v_index, (vert_indices, vert) \
                                in enumerate(zip(vertmap, keyblock.data)):
                                # vertmap check
                                if not vert_indices:
                                    continue
                                # copy vertex and assign morph vertex
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
                            #curve = keyipo['Key %i' % keyblocknum] # FIXME
                            # workaround
                            curve = None
                            if ( keyblocknum - 1 ) in range( len( keyipo.getCurves() ) ):
                                curve = keyipo.getCurves()[keyblocknum-1]
                            # base key has no curve all other keys should have one
                            if curve:
                                self.msg("  exporting morph %i: curve"
                                         % keyblocknum)
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
            node = self.createBlock("NiNode", bone)
            # doing bone map now makes linkage very easy in second run
            bones_node[bone.name] = node

            # add the node and the keyframe for this bone
            node.name = self.getFullName(bone.name)
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                # default for Oblivion bones
                # note: bodies have 0x000E, clothing has 0x000F
                node.flags = 0x000E
            elif self.EXPORT_VERSION == 'Civilization IV':
                if bone.children:
                    # default for Civ IV bones with children
                    node.flags = 0x0006
                else:
                    # default for Civ IV final bones
                    node.flags = 0x0016
            else:
                node.flags = 0x0002 # default for Morrowind bones
            self.exportMatrix(bone, 'localspace', node) # rest pose
            
            # bone rotations are stored in the IPO relative to the rest position
            # so we must take the rest position into account
            # (need original one, without extra transforms, so extra = False)
            bonerestmat = self.getBoneRestMatrix(bone, 'BONESPACE',
                                                 extra = False)
            try:
                bonexmat_inv = Blender.Mathutils.Matrix(
                    self.getBoneExtraMatrixInv(bone.name))
            except KeyError:
                bonexmat_inv = Blender.Mathutils.Matrix()
                bonexmat_inv.identity()
            if bones_ipo.has_key(bone.name):
                self.exportKeyframes(
                    bones_ipo[bone.name], 'localspace', node,
                    bind_mat = bonerestmat, extra_mat_inv = bonexmat_inv)

            # does bone have priority value in NULL constraint?
            for constr in arm.getPose().bones[bone.name].constraints:
                # yes! store it for reference when creating the kf file
                if constr.name[:9].lower() == "priority:":
                    self.bonePriorities[node] = int(constr.name[9:])

        # now fix the linkage between the blocks
        for bone in bones.values():
            # link the bone's children to the bone
            if bone.children:
                self.msg("  linking children of bone %s" % bone.name)
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
                    if parent_bone_name is None:
                        self.exportNode(ob_child, 'localspace',
                                        parent_block, ob_child.getName())
                    else:
                        # we should parent the object to the bone instead of
                        # to the armature
                        # so let's find that bone!
                        nif_bone_name = self.getFullName(parent_bone_name)
                        for bone_block in self.blocks:
                            if isinstance(bone_block, NifFormat.NiNode) and \
                                bone_block.name == nif_bone_name:
                                # ok, we should parent to block
                                # instead of to parent_block
                                # two problems to resolve:
                                #   - blender bone matrix is not the exported
                                #     bone matrix!
                                #   - blender objects parented to bone have
                                #     extra translation along the Y axis
                                #     with length of the bone ("tail")
                                # this is handled in the getObjectSRT function
                                self.exportNode(ob_child, 'localspace',
                                                bone_block, ob_child.getName())
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
        """Get an object's matrix as NifFormat.Matrix44

        Note: for objects parented to bones, this will return the transform
        relative to the bone parent head in nif coordinates (that is, including
        the bone correction); this differs from getMatrix which
        returns the transform relative to the armature."""
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

    def getObjectSRT(self, obj, space = 'localspace'):
        """Find scale, rotation, and translation components of an object in
        the rest pose. Returns a triple (bs, br, bt), where bs
        is a scale float, br is a 3x3 rotation matrix, and bt is a
        translation vector. It should hold that

        ob.getMatrix(space) == bs * br * bt

        Note: for objects parented to bones, this will return the transform
        relative to the bone parent head including bone correction.

        space is either 'none' (gives identity transform) or 'localspace'"""
        # TODO remove the space argument, always do local space
        # handle the trivial case first
        if (space == 'none'):
            return ( 1.0,
                     Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1]),
                     Blender.Mathutils.Vector([0, 0, 0]) )
        
        assert(space == 'localspace')

        # now write out spaces
        if (not type(obj) is Blender.Armature.Bone):
            mat = Blender.Mathutils.Matrix(obj.getMatrix('localspace'))
            bone_parent_name = obj.getParentBoneName()
            # if there is a bone parent then the object is parented
            # then get the matrix relative to the bone parent head
            if bone_parent_name:
                # so v * O * T * B' = v * Z * B
                # where B' is the Blender bone matrix in armature
                # space, T is the bone tail translation, O is the object
                # matrix (relative to the head), and B is the nif bone matrix;
                # we wish to find Z

                # obj.getMatrix('localspace')
                # gets the object local transform matrix, relative
                # to the armature!! (not relative to the bone)
                # so at this point, mat = O * T * B'
                # hence it must hold that mat = Z * B,
                # or equivalently Z = mat * B^{-1}

                # now, B' = X * B, so B^{-1} = B'^{-1} * X
                # hence Z = mat * B'^{-1} * X

                # first multiply with inverse of the Blender bone matrix
                bone_parent = obj.getParent().getData().bones[
                    bone_parent_name]
                boneinv = Blender.Mathutils.Matrix(
                    bone_parent.matrix['ARMATURESPACE'])
                boneinv.invert()
                mat = mat * boneinv
                # now multiply with the bone correction matrix X
                try:
                    extra = Blender.Mathutils.Matrix(
                        self.getBoneExtraMatrixInv(bone_parent_name))
                    extra.invert()
                    mat = mat * extra
                except KeyError:
                    # no extra local transform
                    pass
        else:
            # bones, get the rest matrix
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
                corrmat = Blender.Mathutils.Matrix(
                    self.getBoneExtraMatrixInv(bone.name))
            except KeyError:
                corrmat.identity()
        else:
            corrmat.identity()
        if (space == 'ARMATURESPACE'):
            mat = Blender.Mathutils.Matrix(bone.matrix['ARMATURESPACE'])
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



    def createBlock(self, blocktype, b_obj = None):
        """Helper function to create a new block, register it in the list of
        exported blocks, and associate it with a Blender object.

        @param blocktype: The nif block type (for instance "NiNode").
        @type blocktype: C{str}
        @param b_obj: The Blender object.
        @return: The newly created block."""
        try:
            block = getattr(NifFormat, blocktype)()
        except AttributeError:
            raise NifExportError("""\
'%s': Unknown block type (this is probably a bug).""" % blocktype)
        return self.registerBlock(block, b_obj)

    def registerBlock(self, block, b_obj = None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            self.msg("Exporting %s block"%block.__class__.__name__)
        else:
            self.msg("Exporting %s as %s block"
                     % (b_obj, block.__class__.__name__))
        self.blocks[block] = b_obj
        return block

    def registerBlenderObject(self, block, b_obj):
        """Helper function to associate a nif block with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""

    def exportCollision(self, obj, parent_block):
        """Main function for adding collision object obj to a node.""" 
        if self.EXPORT_VERSION == 'Morrowind':
             if obj.rbShapeBoundType != Blender.Object.RBShapes['POLYHEDERON']:
                 raise NifExportError("""\
Morrowind only supports Polyhedron/Static TriangleMesh collisions.""")
             node = self.createBlock("RootCollisionNode", obj)
             parent_block.addChild(node)
             node.flags = 0x0003 # default
             self.exportMatrix(obj, 'localspace', node)
             self.exportTriShapes(obj, 'none', node)

        elif self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):

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
                node = self.createBlock("NiNode", obj)
                node.setTransform(self.IDENTITY44)
                node.name = 'collisiondummy%i' % parent_block.numChildren
                node.flags = 0x000E # default
                parent_block.addChild(node)
                self.exportCollisionHelper(obj, node)

        else:
            print("""\
WARNING: only Morrowind, Oblivion, and Fallout 3 collisions are supported,
         skipped collision object '%s'""" % obj.name)

    def exportCollisionHelper(self, obj, parent_block):
        """Helper function to add collision objects to a node. This function
        exports the rigid body, and calls the appropriate function to export
        the collision geometry in the desired format.

        @param obj: The object to export as collision.
        @param parent_block: The NiNode parent of the collision.
        """

        # is it packed
        coll_ispacked = (obj.rbShapeBoundType
                         == Blender.Object.RBShapes['POLYHEDERON'])

        # find physics properties
        material = self.EXPORT_OB_MATERIAL
        layer = self.EXPORT_OB_LAYER
        motionsys = self.EXPORT_OB_MOTIONSYSTEM
        # copy physics properties from Blender properties, if they exist
        for prop in obj.getAllProperties():
            if prop.getName() == 'HavokMaterial':
                material = prop.getData()
                if isinstance(material, basestring):
                    # given as a string, not as an integer
                    material = getattr(NifFormat.HavokMaterial, material)
            elif prop.getName() == 'OblivionLayer':
                layer = getattr(NifFormat.OblivionLayer, prop.getData())
            #elif prop.getName() == 'MotionSystem':
            #    ob_mosys = getattr(NifFormat.MotionSystem, prop.getData())

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collisionObject:
            # note: collision settings are taken from lowerclasschair01.nif
            if self.EXPORT_OB_LAYER == NifFormat.OblivionLayer.OL_BIPED:
                # special collision object for creatures
                colobj = self.createBlock("bhkBlendCollisionObject", obj)
                colobj.flags = 9
                colobj.unknownFloat1 = 1.0
                colobj.unknownFloat2 = 1.0
                # also add a controller for it
                blendctrl = self.createBlock("bhkBlendController", obj)
                blendctrl.flags = 12
                blendctrl.frequency = 1.0
                blendctrl.phase = 0.0
                blendctrl.startTime = self.FLOAT_MAX
                blendctrl.stopTime = self.FLOAT_MIN
                parent_block.addController(blendctrl)
            else:
                # usual collision object
                colobj = self.createBlock("bhkCollisionObject", obj)
                colobj.flags = 1
            parent_block.collisionObject = colobj
            colobj.target = parent_block

            colbody = self.createBlock("bhkRigidBody", obj)
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
        If the current collision system is not a packed list of collisions
        (bhkPackedNiTriStripsShape), then a ValueError is raised."""

        if not colbody.shape:
            colshape = self.createBlock("bhkPackedNiTriStripsShape", obj)

            colmopp = self.createBlock("bhkMoppBvTreeShape", obj)
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

            colshape.unknownFloats[2] = 0.1
            colshape.unknownFloats[4] = 1.0
            colshape.unknownFloats[5] = 1.0
            colshape.unknownFloats[6] = 1.0
            colshape.unknownFloats[8] = 0.1
            colshape.scale = 1.0
            colshape.unknownFloats2[0] = 1.0
            colshape.unknownFloats2[1] = 1.0
        else:
            colmopp = colbody.shape
            if not isinstance(colmopp, NifFormat.bhkMoppBvTreeShape):
                raise ValueError('not a packed list of collisions')
            colshape = colmopp.shape
            if not isinstance(colshape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError('not a packed list of collisions')

        mesh = obj.data
        transform = Blender.Mathutils.Matrix(
            *self.getObjectMatrix(obj, 'localspace').asList())
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
            coltf = self.createBlock("bhkConvexTransformShape", obj)
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
            hktf = Blender.Mathutils.Matrix(
                *self.getObjectMatrix(obj, 'localspace').asList())
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
                colbox = self.createBlock("bhkBoxShape", obj)
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
                colsphere = self.createBlock("bhkSphereShape", obj)
                coltf.shape = colsphere
                colsphere.material = material
                # take average radius and
                # fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = (maxx + maxy + maxz - minx - miny -minz) / 42.0

            return coltf

        elif obj.rbShapeBoundType == Blender.Object.RBShapes['CYLINDER']:
            colcaps = self.createBlock("bhkCapsuleShape", obj)
            colcaps.material = material
            # take average radius
            localradius = (maxx + maxy - minx - miny) / 4.0
            transform = Blender.Mathutils.Matrix(
                *self.getObjectMatrix(obj, 'localspace').asList())
            vert1 = Blender.Mathutils.Vector( [ (maxx + minx)/2.0,
                                                (maxy + miny)/2.0,
                                                minz + localradius ] )
            vert2 = Blender.Mathutils.Vector( [ (maxx + minx) / 2.0,
                                                (maxy + miny) / 2.0,
                                                maxz - localradius ] )
            vert1 *= transform
            vert2 *= transform
            colcaps.firstPoint.x = vert1[0] / 7.0
            colcaps.firstPoint.y = vert1[1] / 7.0
            colcaps.firstPoint.z = vert1[2] / 7.0
            colcaps.secondPoint.x = vert2[0] / 7.0
            colcaps.secondPoint.y = vert2[1] / 7.0
            colcaps.secondPoint.z = vert2[2] / 7.0
            # set radius, with correct scale
            sizex, sizey, sizez = obj.getSize()
            colcaps.radius = localradius * (sizex + sizey) * 0.5
            colcaps.radius1 = colcaps.radius
            colcaps.radius2 = colcaps.radius
            # fix havok coordinate system for radii
            colcaps.radius /= 7.0
            colcaps.radius1 /= 7.0
            colcaps.radius2 /= 7.0

            return colcaps

        elif obj.rbShapeBoundType == 5:
            # convex hull polytope; not in Python API
            # bound type has value 5
            mesh = obj.data
            transform = Blender.Mathutils.Matrix(
                *self.getObjectMatrix(obj, 'localspace').asList())
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
                raise NifExportError("""
ERROR%t|Too many faces/vertices. Decimate/split your mesh and try again.""")
            
            colhull = self.createBlock("bhkConvexVerticesShape", obj)
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

    def exportConstraints(self, b_obj, root_block):
        """Export the constraints of an object.

        @param b_obj: The object whose constraints to export.
        @param root_block: The root of the nif tree (required for updateAB)."""
        if isinstance(b_obj, Blender.Armature.Bone):
            # bone object has its constraints stored in the posebone
            # so now we should get the posebone, but no constraints for
            # bones are exported anyway for now
            # so skip this object
            return

        if not hasattr(b_obj, "constraints"):
            # skip text buffers etc
            return

        for b_constr in b_obj.constraints:
            # rigid body joints
            if b_constr.type == Blender.Constraint.Type.RIGIDBODYJOINT:
                if self.EXPORT_VERSION not in ("Oblivion", "Fallout 3"):
                    self.msg("""\
only Oblivion/Fallout 3 rigid body constraints can be exported
skipped %s""" % b_constr)
                    continue
                # check that the object is a rigid body
                for otherbody, otherobj in self.blocks.iteritems():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) \
                        and otherobj is b_obj:
                        hkbody = otherbody
                        break
                else:
                    # no collision body for this object
                    raise NifExportError("""\
Object %s has a rigid body constraint, 
but is not exported as collision object""")
                # yes there is a rigid body constraint
                # is it of a type that is supported?
                if b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 1:
                    # ball
                    if not self.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.createBlock(
                            "bhkRagdollConstraint", b_constr)
                    else:
                        hkconstraint = self.createBlock(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 7
                    hkdescriptor = hkconstraint.ragdoll
                elif b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 2:
                    # hinge
                    if not self.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.createBlock(
                            "bhkLimitedHingeConstraint", b_constr)
                    else:
                        hkconstraint = self.createBlock(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 2
                    hkdescriptor = hkconstraint.limitedHinge
                else:
                    raise NifExportError("""\
Unsupported rigid body joint type (%i), only ball and hinge are supported.""" \
% b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE])

                # parent constraint to hkbody
                hkbody.numConstraints += 1
                hkbody.constraints.updateSize()
                hkbody.constraints[-1] = hkconstraint

                # export hkconstraint settings
                hkconstraint.numEntities = 2
                hkconstraint.entities.updateSize()
                hkconstraint.entities[0] = hkbody
                # is there a target?
                targetobj = b_constr[Blender.Constraint.Settings.TARGET]
                if not targetobj:
                    self.msg("  WARNING: constraint %s has no target, skipped")
                    continue
                # find target's bhkRigidBody
                for otherbody, otherobj in self.blocks.iteritems():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) \
                        and otherobj == targetobj:
                        hkconstraint.entities[1] = otherbody
                        break
                else:
                    # not found
                    raise NifExportError("""\
Rigid body target not exported in nif tree, 
check that %s is selected during export.""" % targetobj)
                # priority
                hkconstraint.priority = 1
                # extra malleable constraint settings
                if isinstance(hkconstraint, NifFormat.bhkMalleableConstraint):
                    # unknowns
                    hkconstraint.unknownInt2 = 2
                    hkconstraint.unknownInt3 = 1
                    # force required to keep bodies together
                    # 0.5 seems a good standard value for creatures
                    hkconstraint.tau = 0.5
                    # default damping settings
                    # (cannot access rbDamping in Blender Python API)
                    hkconstraint.damping = 0.5

                # calculate pivot point and constraint matrix
                pivot = Blender.Mathutils.Vector(
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVX],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVY],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVZ])
                constr_matrix = Blender.Mathutils.Euler(
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_AXX],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_AXY],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_AXZ])
                constr_matrix = constr_matrix.toMatrix()

                # transform pivot point and constraint matrix into bhkRigidBody
                # coordinates (also see nif_import.py, the
                # NifImport.importHavokConstraints method)
                
                # the pivot point v' is in object coordinates
                # however nif expects it in hkbody coordinates, v
                # v * R * B = v' * O * T * B'
                # with R = rigid body transform (usually unit tf)
                # B = nif bone matrix
                # O = blender object transform
                # T = bone tail matrix (translation in Y direction)
                # B' = blender bone matrix
                # so we need to cancel out the object transformation by
                # v = v' * O * T * B' * B^{-1} * R^{-1}

                # for the rotation matrix, we transform in the same way
                # but ignore all translation parts

                # assume R is unit transform...

                # apply object transform relative to the bone head
                # (this is O * T * B' * B^{-1} at once)
                transform = Blender.Mathutils.Matrix(
                    *self.getObjectMatrix(b_obj, 'localspace').asList())
                pivot = pivot * transform
                constr_matrix = constr_matrix * transform.rotationPart()

                # export hkdescriptor pivot point
                hkdescriptor.pivotA.x = pivot[0] / 7.0
                hkdescriptor.pivotA.y = pivot[1] / 7.0
                hkdescriptor.pivotA.z = pivot[2] / 7.0
                # export hkdescriptor axes and other parameters
                # (also see nif_import.py NifImport.importHavokConstraints)
                axis_x = Blender.Mathutils.Vector(1,0,0) * constr_matrix
                axis_y = Blender.Mathutils.Vector(0,1,0) * constr_matrix
                axis_z = Blender.Mathutils.Vector(0,0,1) * constr_matrix
                if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                    # z axis is the twist vector
                    hkdescriptor.twistA.x = axis_z[0]
                    hkdescriptor.twistA.y = axis_z[1]
                    hkdescriptor.twistA.z = axis_z[2]
                    # x axis is the plane vector
                    hkdescriptor.planeA.x = axis_x[0]
                    hkdescriptor.planeA.y = axis_x[1]
                    hkdescriptor.planeA.z = axis_x[2]
                    # angle limits
                    # take them twist and plane to be 45 deg (3.14 / 4 = 0.8)
                    hkdescriptor.twistMinAngle = -0.8
                    hkdescriptor.twistMaxAngle = +0.8
                    hkdescriptor.planeMinAngle = -0.8
                    hkdescriptor.planeMaxAngle = +0.8
                    # same for maximum cone angle
                    hkdescriptor.coneMaxAngle  = +0.8
                elif isinstance(hkdescriptor, NifFormat.LimitedHingeDescriptor):
                    # y axis is the zero angle vector on the plane of rotation
                    hkdescriptor.perp2AxleInA1.x = axis_y[0]
                    hkdescriptor.perp2AxleInA1.y = axis_y[1]
                    hkdescriptor.perp2AxleInA1.z = axis_y[2]
                    # x axis is the axis of rotation
                    hkdescriptor.axleA.x = axis_x[0]
                    hkdescriptor.axleA.y = axis_x[1]
                    hkdescriptor.axleA.z = axis_x[2]
                    # z is the remaining axis determining the positive
                    # direction of rotation
                    hkdescriptor.perp2AxleInA2.x = axis_z[0]
                    hkdescriptor.perp2AxleInA2.y = axis_z[1]
                    hkdescriptor.perp2AxleInA2.z = axis_z[2]
                    # angle limits
                    # typically, the constraint on one side is defined
                    # by the z axis
                    hkdescriptor.minAngle = 0.0
                    # the maximum axis is typically about 90 degrees
                    # 3.14 / 2 = 1.5
                    hkdescriptor.maxAngle = 1.5
                    
                else:
                    raise ValueError("unknown descriptor %s"
                                     % hkdescriptor.__class__.__name__)

                # friction: again, just picking a reasonable value
                if isinstance(hkconstraint,
                              NifFormat.bhkMalleableConstraint):
                    # malleable typically have 0
                    # (perhaps because they have a damping parameter)
                    hkdescriptor.maxFriction = 0.0
                else:
                    # non-malleable typically have 10
                    hkdescriptor.maxFriction = 10.0

                # do AB
                hkconstraint.updateAB(root_block)


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

    def exportSpecularProperty(self, flags = 0x0001):
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

    def exportWireframeProperty(self, flags = 0x0001):
        """Return existing wire property with given flags, or create new one
        if an wire property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiWireframeProperty) \
               and block.flags == flags:
                return block
        # no alpha property with given flag found, so create new one
        wireprop = self.createBlock("NiWireframeProperty")
        wireprop.flags = flags
        return wireprop        

    def exportStencilProperty(self):
        """Return existing stencil property with given flags, or create new one
        if an identical stencil property."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiStencilProperty):
                # all these blocks have the same setting, no further check
                # is needed
                return block
        # no stencil property found, so create new one
        stencilprop = self.createBlock("NiStencilProperty")
        return stencilprop        

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
   
        # list which determines whether the material name is relevant or not
        # only for particular names this holds, such as EnvMap2
        # by default, the material name does not affect rendering
        specialnames = ("EnvMap2", "EnvMap", "skin", "Hair",
                        "dynalpha", "HideSecret", "Lava")

        # hack to preserve EnvMap2, skinm, ... named blocks (even if they got
        # renamed to EnvMap2.xxx or skin.xxx on import)
        if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
            for specialname in specialnames:
                if (name.lower() == specialname.lower()
                    or name.lower().startswith(specialname.lower() + ".")):
                    if name != specialname:
                        print("Renaming material '%s' to '%s'"
                              % (name, specialname))
                    name = specialname

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
            if not isinstance(block, NifFormat.NiMaterialProperty):
                continue
            # when optimization is enabled, ignore material name
            if self.EXPORT_OPTIMIZE_MATERIALS:
                ignore_strings = not(block.name in specialnames)
            else:
                ignore_strings = False
            # check hash
            if (block.getHash(ignore_strings=ignore_strings) ==
                matprop.getHash(
                    ignore_strings=ignore_strings)):
                print("Merging materials '%s' and '%s' \
(they are identical in nif)"
                      % (matprop.name, block.name))
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
        return self.registerBlock(texeff)

    def exportBSBound(self, obj, block_parent):
        """Export an Oblivion bounding box."""
        bbox = self.createBlock("BSBound")
        # ... the following incurs double scaling because it will be added in
        # both the extra data list and in the old extra data sequence!!!
        #block_parent.addExtraData(bbox)
        # quick hack (better solution would be to make applyScale non-recursive)
        block_parent.numExtraDataList += 1
        block_parent.extraDataList.updateSize()
        block_parent.extraDataList[-1] = bbox
        
        bbox.name = "BBX"
        # calculate bounding box extents
        objbbox = obj.getBoundBox()
        minx = min(vert[0] for vert in objbbox)
        miny = min(vert[1] for vert in objbbox)
        minz = min(vert[2] for vert in objbbox)
        maxx = max(vert[0] for vert in objbbox)
        maxy = max(vert[1] for vert in objbbox)
        maxz = max(vert[2] for vert in objbbox)
        # set the center and dimensions
        bbox.center.x = (minx + maxx) * 0.5
        bbox.center.y = (miny + maxy) * 0.5
        bbox.center.z = (minz + maxz) * 0.5
        bbox.dimensions.x = maxx - minx
        bbox.dimensions.y = maxy - miny
        bbox.dimensions.z = maxz - minz



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
    # use global config variableso gui elements don't go out of skope
    _CONFIG = NifConfig()
    # open file selector window, and then call fileselect_callback
    Blender.Window.FileSelector(
        fileselect_callback, "Export NIF/KF", _CONFIG.config["EXPORT_FILE"])
