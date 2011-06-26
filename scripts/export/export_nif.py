#!BPY

"""
Name: 'NetImmerse/Gamebryo (.nif & .kf & .egm)'
Blender: 245
Group: 'Export'
Tooltip: 'Export NIF File Format (.nif & .kf & egm)'
"""

__author__ = "The NifTools team, http://niftools.sourceforge.net/"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__bpydoc__ = """\
This script exports Netimmerse and Gamebryo .nif files from Blender.
"""

from itertools import izip
import logging

import Blender
from Blender import Ipo # for all the Ipo curve constants

from nif_common import NifImportExport
from nif_common import NifConfig
from nif_common import NifFormat
from nif_common import EgmFormat
from nif_common import __version__

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

class NifExportError(StandardError):
    pass

# main export class
class NifExport(NifImportExport):
    IDENTITY44 = NifFormat.Matrix44()
    IDENTITY44.set_identity()
    # map blending modes to apply modes
    APPLYMODE = {
        Blender.Texture.BlendModes["MIX"] : NifFormat.ApplyMode.APPLY_MODULATE,
        Blender.Texture.BlendModes["LIGHTEN"] : NifFormat.ApplyMode.APPLY_HILIGHT,
        Blender.Texture.BlendModes["MULTIPLY"] : NifFormat.ApplyMode.APPLY_HILIGHT2
    }
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38

    def rebuild_bones_extra_matrices(self):
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
                # Check if matrices are clean, and if necessary fix them.
                quat = mat.rotationPart().toQuat()
                if sum(sum(abs(x) for x in vec)
                       for vec in mat.rotationPart() - quat.toMatrix()) > 0.01:
                    self.logger.warn(
                        "Bad bone extra matrix for bone %s. \n"
                        "Attempting to fix... but bone transform \n"
                        "may be incompatible with existing animations." % b)
                    self.logger.warn("old invalid matrix:\n%s" % mat)
                    trans = mat.translationPart()
                    mat = quat.toMatrix().resize4x4()
                    mat[3][0] = trans[0]
                    mat[3][1] = trans[1]
                    mat[3][2] = trans[2]
                    self.logger.warn("new valid matrix:\n%s" % mat)
                # Matrices are stored inverted for easier math later on.
                mat.invert()
                self.set_bone_extra_matrix_inv(b, mat)

    def set_bone_extra_matrix_inv(self, bonename, mat):
        """Set bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        self.bones_extra_matrix_inv[self.get_bone_name_for_blender(bonename)] = mat

    def get_bone_extra_matrix_inv(self, bonename):
        """Get bone extra matrix, inverted. The bonename is first converted
        to blender style (to ensure compatibility with older imports).
        """
        return self.bones_extra_matrix_inv[self.get_bone_name_for_blender(bonename)]

    def rebuild_full_names(self):
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


    def get_unique_name(self, blender_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object."""
        unique_name = "default_name"
        if blender_name != None:
            unique_name = blender_name
        # blender bone naming -> nif bone naming
        unique_name = self.get_bone_name_for_nif(unique_name)
        # ensure uniqueness
        if unique_name in self.block_names or unique_name in self.names.values():
            unique_int = 0
            old_name = unique_name
            while unique_name in self.block_names or unique_name in self.names.values():
                unique_name = '%s.%02d' % (old_name, unique_int)
                unique_int += 1
        self.block_names.append(unique_name)
        self.names[blender_name] = unique_name
        return unique_name

    def get_full_name(self, blender_name):
        """Returns the original imported name if present, or the name by which
        the object was exported already."""
        try:
            return self.names[blender_name]
        except KeyError:
            return self.get_unique_name(blender_name)

    def get_exported_objects(self):
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
        self.msg_progress("Initializing", progbar=0)

        # store configuration in self
        for name, value in config.iteritems():
            setattr(self, name, value)
        if self.EXPORT_MW_NIFXNIFKF and self.EXPORT_VERSION == 'Morrowind':
            # if exporting in nif+xnif+kf mode, then first export
            # the nif with geometry + animation, which is done by:
            self.EXPORT_ANIMATION = 0

        # shortcut to export logger
        self.logger = logging.getLogger("niftools.blender.export")

        # save file name
        self.filename = self.EXPORT_FILE[:]
        self.filepath = Blender.sys.dirname(self.filename)
        self.filebase, self.fileext = Blender.sys.splitext(
            Blender.sys.basename(self.filename))

        # variables
        # dictionary mapping exported blocks to either None or to an
        # associated Blender object
        self.blocks = {}
        # maps Blender names to previously imported names from the FullNames
        # buffer (see self.rebuild_full_names())
        self.names = {}
        # keeps track of names of exported blocks, to make sure they are unique
        self.block_names = []

        # dictionary of bones, maps Blender bone name to matrix that maps the
        # NIF bone matrix on the Blender bone matrix
        # Recall from the import script
        #   B' = X * B,
        # where B' is the Blender bone matrix, and B is the NIF bone matrix,
        # both in armature space. So to restore the NIF matrices we need to do
        #   B = X^{-1} * B'
        # Hence, we will restore the X's, invert them, and store those inverses in the
        # following dictionary.
        self.bones_extra_matrix_inv = {}

        # store bone priorities (from NULL constraints) as the armature bones
        # are parsed, so they are available when writing the kf file
        # maps bone NiNode to priority value
        self.bone_priorities = {}

        # if an egm is exported, this will contain the data
        self.egmdata = None

        try: # catch export errors

            # find nif version to write
            try:
                self.version = NifFormat.versions[self.EXPORT_VERSION]
                self.logger.info("Writing NIF version 0x%08X" % self.version)
            except KeyError:
                # select highest nif version that the game supports
                self.version = NifFormat.games[self.EXPORT_VERSION][-1]
                self.logger.info("Writing %s NIF (version 0x%08X)"
                                 % (self.EXPORT_VERSION, self.version))

            if self.EXPORT_ANIMATION == 0:
                self.logger.info("Exporting geometry and animation")
            elif self.EXPORT_ANIMATION == 1:
                # for morrowind: everything except keyframe controllers
                self.logger.info("Exporting geometry only")
            elif self.EXPORT_ANIMATION == 2:
                # for morrowind: only keyframe controllers
                self.logger.info("Exporting animation only (as .kf file)")

            for ob in Blender.Object.Get():
                # armatures should not be in rest position
                if ob.getType() == 'Armature':
                    # ensure we get the mesh vertices in animation mode,
                    # and not in rest position!
                    ob.data.restPosition = False
                    if (ob.data.envelopes):
                        self.logger.critical(
                            "'%s': Cannot export envelope skinning."
                            " If you have vertex groups,"
                            " turn off envelopes. If you don't have vertex"
                            " groups, select the bones one by one press W"
                            " to convert their envelopes to vertex weights,"
                            " and turn off envelopes."
                            % ob.getName())
                        raise NifExportError(
                            "'%s': Cannot export envelope skinning."
                            " Check console for instructions."
                            % ob.getName())

                # check for non-uniform transforms
                # (lattices are not exported so ignore them as they often tend
                # to have non-uniform scaling)
                if ob.getType() != 'Lattice':
                    try:
                        self.decompose_srt(ob.getMatrix('localspace'))
                    except NifExportError: # non-uniform scaling
                        raise NifExportError(
                            "Non-uniform scaling not supported."
                            " Workaround: apply size and rotation (CTRL-A)"
                            " on '%s'." % ob.name)

            # extract some useful scene info
            self.scene = Blender.Scene.GetCurrent()
            context = self.scene.getRenderingContext()
            self.fspeed = 1.0 / context.framesPerSec()
            self.fstart = context.startFrame()
            self.fend = context.endFrame()
            
            # oblivion, Fallout 3 and civ4
            if (self.EXPORT_VERSION
                in ('Civilization IV', 'Oblivion', 'Fallout 3')):
                root_name = 'Scene Root'
            # other games
            else:
                root_name = self.filebase
     
            # get the root object from selected object
            # only export empties, meshes, and armatures
            if (Blender.Object.GetSelected() == None):
                raise NifExportError(
                    "Please select the object(s) to export,"
                    " and run this script again.")
            root_objects = set()
            export_types = ('Empty', 'Mesh', 'Armature')
            for root_object in [ob for ob in Blender.Object.GetSelected()
                                if ob.getType() in export_types]:
                while (root_object.getParent() != None):
                    root_object = root_object.getParent()
                if root_object.getType() not in export_types:
                    raise NifExportError(
                        "Root object (%s) must be an 'Empty', 'Mesh',"
                        " or 'Armature' object."
                        % root_object.getName())
                root_objects.add(root_object)

            # smoothen seams of objects
            if self.EXPORT_SMOOTHOBJECTSEAMS:
                # get shared vertices
                self.logger.info("Smoothing seams between objects...")
                vdict = {}
                for ob in [ob for ob in self.scene.objects
                           if ob.getType() == 'Mesh']:
                    mesh = ob.getData(mesh=1)
                    #for v in mesh.verts:
                    #    v.sel = False
                    for f in mesh.faces:
                        for v in f.verts:
                            vkey = (int(v.co[0]*self.VERTEX_RESOLUTION),
                                    int(v.co[1]*self.VERTEX_RESOLUTION),
                                    int(v.co[2]*self.VERTEX_RESOLUTION))
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
                self.logger.info("Fixed normals on %i vertices." % nv)

            ## TODO use Blender actions for animation groups
            # check for animation groups definition in a text buffer 'Anim'
            try:
                animtxt = Blender.Text.Get("Anim")
            except NameError:
                animtxt = None
                    
            # rebuild the bone extra matrix dictionary from the 'BoneExMat' text buffer
            self.rebuild_bones_extra_matrices()
            
            # rebuild the full name dictionary from the 'FullNames' text buffer 
            self.rebuild_full_names()
            
            # export nif:
            #------------
            self.msg_progress("Exporting")
            
            # create a nif object
            
            # export the root node (the name is fixed later to avoid confusing the
            # exporter with duplicate names)
            root_block = self.export_node(None, 'none', None, '')
            
            # export objects
            self.logger.info("Exporting objects")
            for root_object in root_objects:
                # export the root objects as a NiNodes; their children are
                # exported as well
                # note that localspace = worldspace, because root objects have
                # no parents
                self.export_node(root_object, 'localspace',
                                 root_block, root_object.getName())

            # post-processing:
            #-----------------

            # if we exported animations, but no animation groups are defined,
            # define a default animation group
            self.logger.info("Checking animation groups")
            if not animtxt:
                has_controllers = False
                for block in self.blocks:
                    # has it a controller field?
                    if isinstance(block, NifFormat.NiObjectNET):
                        if block.controller:
                            has_controllers = True
                            break
                if has_controllers:
                    self.logger.info("Defining default animation group.")
                    # write the animation group text buffer
                    animtxt = Blender.Text.New("Anim")
                    animtxt.write("%i/Idle: Start/Idle: Loop Start\n%i/Idle: Loop Stop/Idle: Stop" % (self.fstart, self.fend))

            # animations without keyframe animations crash the TESCS
            # if we are in that situation, add a trivial keyframe animation
            self.logger.info("Checking controllers")
            if animtxt and self.EXPORT_VERSION == "Morrowind":
                has_keyframecontrollers = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiKeyframeController):
                        has_keyframecontrollers = True
                        break
                if ((not has_keyframecontrollers)
                    and (not self.EXPORT_MW_BS_ANIMATION_NODE)):
                    self.logger.info("Defining dummy keyframe controller")
                    # add a trivial keyframe controller on the scene root
                    self.export_keyframes(None, 'localspace', root_block)
            if (self.EXPORT_MW_BS_ANIMATION_NODE
                and self.EXPORT_VERSION == "Morrowind"):
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiNode):
                        # if any of the shape children has a controller
                        # or if the ninode has a controller
                        # convert its type
                        if block.controller or any(
                            child.controller
                            for child in block.children
                            if isinstance(child, NifFormat.NiGeometry)):
                            new_block = NifFormat.NiBSAnimationNode().deepcopy(
                                block)
                            # have to change flags to 42 to make it work
                            new_block.flags = 42
                            root_block.replace_global_node(block, new_block)
                            if root_block is block:
                                root_block = new_block

            # oblivion skeleton export: check that all bones have a
            # transform controller and transform interpolator
            if self.EXPORT_VERSION in ("Oblivion", "Fallout 3") \
                and self.filebase.lower() in ('skeleton', 'skeletonbeast'):
                # here comes everything that is Oblivion skeleton export
                # specific
                self.logger.info(
                    "Adding controllers and interpolators for skeleton")
                for block in self.blocks.keys():
                    if isinstance(block, NifFormat.NiNode) \
                        and block.name == "Bip01":
                        for bone in block.tree(block_type = NifFormat.NiNode):
                            ctrl = self.create_block("NiTransformController")
                            interp = self.create_block("NiTransformInterpolator")

                            ctrl.interpolator = interp
                            bone.add_controller(ctrl)

                            ctrl.flags = 12
                            ctrl.frequency = 1.0
                            ctrl.phase = 0.0
                            ctrl.start_time = self.FLOAT_MAX
                            ctrl.stop_time = self.FLOAT_MIN
                            interp.translation.x = bone.translation.x
                            interp.translation.y = bone.translation.y
                            interp.translation.z = bone.translation.z
                            scale, quat = bone.rotation.get_scale_quat()
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
                    anim_textextra = self.export_anim_groups(animtxt, root_block)
                else:
                    anim_textextra = None

            # oblivion and Fallout 3 furniture markers
            if (self.EXPORT_VERSION in ('Oblivion', 'Fallout 3')
                and self.filebase[:15].lower() == 'furnituremarker'):
                # exporting a furniture marker for Oblivion/FO3
                try:
                    furniturenumber = int(self.filebase[15:])
                except ValueError:
                    raise NifExportError(
                        "Furniture marker has invalid number (%s)."
                        " Name your file 'furnituremarkerxx.nif'"
                        " where xx is a number between 00 and 19."
                        % self.filebase[15:])
                # name scene root name the file base name
                root_name = self.filebase
                # create furniture marker block
                furnmark = self.create_block("BSFurnitureMarker")
                furnmark.name = "FRN"
                furnmark.num_positions = 1
                furnmark.positions.update_size()
                furnmark.positions[0].position_ref_1 = furniturenumber
                furnmark.positions[0].position_ref_2 = furniturenumber
                # create extra string data sgoKeep
                sgokeep = self.create_block("NiStringExtraData")
                sgokeep.name = "UBP"
                sgokeep.string_data = "sgoKeep"
                # add extra blocks
                root_block.add_extra_data(furnmark)
                root_block.add_extra_data(sgokeep)

            self.logger.info("Checking collision")
            # activate oblivion/Fallout 3 collision and physics
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                hascollision = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkCollisionObject):
                       hascollision = True
                       break
                if hascollision:
                    # enable collision
                    bsx = self.create_block("BSXFlags")
                    bsx.name = 'BSX'
                    bsx.integer_data = self.EXPORT_OB_BSXFLAGS
                    root_block.add_extra_data(bsx)
                # update rigid body center of gravity and mass
                if self.EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES:
                    # we are not using blender properties to set the mass
                    # so calculate mass automatically
                    # first calculate distribution of mass
                    total_mass = 0
                    for block in self.blocks:
                        if isinstance(block, NifFormat.bhkRigidBody):
                            block.update_mass_center_inertia(
                                solid = self.EXPORT_OB_SOLID)
                            total_mass += block.mass
                    if total_mass == 0:
                        # to avoid zero division error later
                        # (if mass is zero then this does not matter
                        # anyway)
                        total_mass = 1
                    # now update the mass ensuring that total mass is
                    # self.EXPORT_OB_MASS
                    for block in self.blocks:
                        if isinstance(block, NifFormat.bhkRigidBody):
                            mass = self.EXPORT_OB_MASS * block.mass / total_mass
                            # lower bound on mass
                            if mass < 0.0001:
                                mass = 0.05
                            block.update_mass_center_inertia(
                                mass = mass,
                                solid = self.EXPORT_OB_SOLID)
                else:
                    # using blender properties, so block.mass *should* have
                    # been set properly
                    for block in self.blocks:
                        if isinstance(block, NifFormat.bhkRigidBody):
                            # lower bound on mass
                            if block.mass < 0.0001:
                                block.mass = 0.05
                            block.update_mass_center_inertia(
                                mass=block.mass,
                                solid=self.EXPORT_OB_SOLID)

                # many Oblivion nifs have a UPB, but export is disabled as
                # they do not seem to affect anything in the game
                #upb = self.create_block("NiStringExtraData")
                #upb.name = 'UPB'
                #upb.string_data = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                #root_block.add_extra_data(upb)

            # bhkConvexVerticesShape of children of bhkListShapes
            # need an extra bhkConvexTransformShape
            # (see issue #3308638, reported by Koniption)
            # note: self.blocks changes during iteration, so need list copy
            for block in list(self.blocks):
                if isinstance(block, NifFormat.bhkListShape):
                    for i, sub_shape in enumerate(block.sub_shapes):
                        if isinstance(sub_shape,
                                      NifFormat.bhkConvexVerticesShape):
                            coltf = self.create_block("bhkConvexTransformShape")
                            coltf.material = sub_shape.material
                            coltf.unknown_float_1 = 0.1
                            coltf.unknown_8_bytes[0] = 96
                            coltf.unknown_8_bytes[1] = 120
                            coltf.unknown_8_bytes[2] = 53
                            coltf.unknown_8_bytes[3] = 19
                            coltf.unknown_8_bytes[4] = 24
                            coltf.unknown_8_bytes[5] = 9
                            coltf.unknown_8_bytes[6] = 253
                            coltf.unknown_8_bytes[7] = 4
                            coltf.transform.set_identity()
                            coltf.shape = sub_shape
                            block.sub_shapes[i] = coltf

            # export constraints
            for b_obj in self.get_exported_objects():
                self.export_constraints(b_obj, root_block)

            # export weapon location
            if self.EXPORT_VERSION in ("Oblivion", "Fallout 3"):
                if self.EXPORT_OB_PRN != "NONE":
                    # add string extra data
                    prn = self.create_block("NiStringExtraData")
                    prn.name = 'Prn'
                    prn.string_data = {
                        "BACK": "BackWeapon",
                        "SIDE": "SideWeapon",
                        "QUIVER": "Quiver",
                        "SHIELD": "Bip01 L ForearmTwist",
                        "HELM": "Bip01 Head",
                        "RING": "Bip01 R Finger1"}[self.EXPORT_OB_PRN]
                    root_block.add_extra_data(prn)

            # add vertex color and zbuffer properties for civ4 and railroads
            if self.EXPORT_VERSION in ("Civilization IV",
                                       "Sid Meier's Railroads"):
                self.export_vertex_color_property(root_block)
                self.export_z_buffer_property(root_block)
            elif self.EXPORT_VERSION in ("Empire Earth II",):
                self.export_vertex_color_property(root_block)
                self.export_z_buffer_property(root_block, flags=15, function=1)

            if self.EXPORT_FLATTENSKIN:
                # (warning: trouble if armatures parent other armatures or
                # if bones parent geometries, or if object is animated)
                # flatten skins
                skelroots = set()
                affectedbones = []
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiGeometry) and block.is_skin():
                        self.logger.info("Flattening skin on geometry %s"
                                         % block.name)
                        affectedbones.extend(block.flatten_skin())
                        skelroots.add(block.skin_instance.skeleton_root)
                # remove NiNodes that do not affect skin
                for skelroot in skelroots:
                    self.logger.info("Removing unused NiNodes in '%s'"
                                     % skelroot.name)
                    skelrootchildren = [child for child in skelroot.children
                                        if ((not isinstance(child,
                                                            NifFormat.NiNode))
                                            or (child in affectedbones))]
                    skelroot.num_children = len(skelrootchildren)
                    skelroot.children.update_size()
                    for i, child in enumerate(skelrootchildren):
                        skelroot.children[i] = child

            # apply scale
            if abs(self.EXPORT_SCALE_CORRECTION - 1.0) > self.EPSILON:
                self.logger.info("Applying scale correction %f"
                                 % self.EXPORT_SCALE_CORRECTION)
                data = NifFormat.Data()
                data.roots = [root_block]
                toaster = pyffi.spells.nif.NifToaster()
                toaster.scale = self.EXPORT_SCALE_CORRECTION
                pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()
                # also scale egm
                if self.egmdata:
                    self.egmdata.apply_scale(self.EXPORT_SCALE_CORRECTION)

            # generate mopps (must be done after applying scale!)
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkMoppBvTreeShape):
                       self.logger.info("Generating mopp...")
                       block.update_mopp()
                       #print "=== DEBUG: MOPP TREE ==="
                       #block.parse_mopp(verbose = True)
                       #print "=== END OF MOPP TREE ==="
                       # warn about mopps on non-static objects
                       if any(sub_shape.layer != 1
                              for sub_shape in block.shape.sub_shapes):
                           self.logger.warn(
                               "Mopps for non-static objects may not function"
                               " correctly in-game. You may wish to use"
                               " simple primitives for collision.")

            # delete original scene root if a scene root object was already
            # defined
            if ((root_block.num_children == 1)
                and ((root_block.children[0].name in ['Scene Root', 'Bip01']) or root_block.children[0].name[-3:] == 'nif')):
                if root_block.children[0].name[-3:] == 'nif':
                    root_block.children[0].name = self.filebase
                self.logger.info(
                    "Making '%s' the root block" % root_block.children[0].name)
                # remove root_block from self.blocks
                self.blocks.pop(root_block)
                # set new root block
                old_root_block = root_block
                root_block = old_root_block.children[0]
                # copy extra data and properties
                for extra in old_root_block.get_extra_datas():
                    # delete links in extras to avoid parentship problems
                    extra.next_extra_data = None
                    # now add it
                    root_block.add_extra_data(extra)
                for b in old_root_block.get_controllers():
                    root_block.add_controller(b)
                for b in old_root_block.properties:
                    root_block.add_property(b)
                for b in old_root_block.effects:
                    root_block.add_effect(b)
            else:
                root_block.name = root_name

            # making root block a fade node
            if (self.EXPORT_VERSION == "Fallout 3"
                and self.EXPORT_FO3_FADENODE):
                self.logger.info(
                    "Making root block a BSFadeNode")
                fade_root_block = NifFormat.BSFadeNode().deepcopy(root_block)
                fade_root_block.replace_global_node(root_block, fade_root_block)
                root_block = fade_root_block

            # figure out user version and user version 2
            if self.EXPORT_VERSION == "Oblivion":
                NIF_USER_VERSION = 11
                NIF_USER_VERSION2 = 11
            elif self.EXPORT_VERSION == "Fallout 3":
                NIF_USER_VERSION = 11
                NIF_USER_VERSION2 = 34
            elif self.EXPORT_VERSION == "Divinity 2":
                NIF_USER_VERSION = 131072
                NIF_USER_VERSION = 0
            else:
                NIF_USER_VERSION = 0
                NIF_USER_VERSION2 = 0

            # export nif file:
            #-----------------

            if self.EXPORT_ANIMATION != 2:
                if self.EXPORT_VERSION == "Empire Earth II":
                    ext = ".nifcache"
                else:
                    ext = ".nif"
                self.logger.info("Writing %s file" % ext)
                self.msg_progress("Writing %s file" % ext)

                # make sure we have the right file extension
                if (self.fileext.lower() != ext):
                    self.logger.warning(
                        "Changing extension from %s to %s on output file"
                        % (self.fileext, ext))
                    self.filename = Blender.sys.join(self.filepath,
                                                     self.filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version2=NIF_USER_VERSION2)
                data.roots = [root_block]
                if self.EXPORT_VERSION == "NeoSteam":
                    data.modification = "neosteam"
                elif self.EXPORT_VERSION == "Atlantica":
                    data.modification = "ndoors"
                elif self.EXPORT_VERSION == "Howling Sword":
                    data.modification = "jmihs1"
                stream = open(self.filename, "wb")
                try:
                    data.write(stream)
                finally:
                    stream.close()

            # create and export keyframe file and xnif file:
            #-----------------------------------------------

            # convert root_block tree into a keyframe tree
            if self.EXPORT_ANIMATION == 2 or self.EXPORT_MW_NIFXNIFKF:
                self.logger.info("Creating keyframe tree")
                # find all nodes and relevant controllers
                node_kfctrls = {}
                for node in root_block.tree():
                    if not isinstance(node, NifFormat.NiAVObject):
                        continue
                    # get list of all controllers for this node
                    ctrls = node.get_controllers()
                    for ctrl in ctrls:
                        if self.EXPORT_VERSION == "Morrowind":
                            # morrowind: only keyframe controllers
                            if not isinstance(ctrl,
                                              NifFormat.NiKeyframeController):
                                continue
                        if not node in node_kfctrls:
                            node_kfctrls[node] = []
                        node_kfctrls[node].append(ctrl)
                # morrowind
                if self.EXPORT_VERSION in ("Morrowind", "Freedom Force"):
                    # create kf root header
                    kf_root = self.create_block("NiSequenceStreamHelper")
                    kf_root.add_extra_data(anim_textextra)
                    # reparent controller tree
                    for node, ctrls in node_kfctrls.iteritems():
                        for ctrl in ctrls:
                            # create node reference by name
                            nodename_extra = self.create_block(
                                "NiStringExtraData")
                            nodename_extra.bytes_remaining = len(node.name) + 4
                            nodename_extra.string_data = node.name

                            # break the controller chain
                            ctrl.next_controller = None

                            # add node reference and controller
                            kf_root.add_extra_data(nodename_extra)
                            kf_root.add_controller(ctrl)
                            # wipe controller target
                            ctrl.target = None
                # oblivion
                elif self.EXPORT_VERSION in ("Oblivion", "Fallout 3",
                                             "Civilization IV", "Zoo Tycoon 2",
                                             "Freedom Force vs. the 3rd Reich"):
                    # create kf root header
                    kf_root = self.create_block("NiControllerSequence")
                    if self.EXPORT_ANIMSEQUENCENAME:
                        kf_root.name = self.EXPORT_ANIMSEQUENCENAME
                    else:
                        kf_root.name = self.filebase
                    kf_root.unknown_int_1 = 1
                    kf_root.weight = 1.0
                    kf_root.text_keys = anim_textextra
                    kf_root.cycle_type = NifFormat.CycleType.CYCLE_CLAMP
                    kf_root.frequency = 1.0
                    kf_root.start_time =(self.fstart - 1) * self.fspeed
                    kf_root.stop_time = (self.fend - self.fstart) * self.fspeed
                    # quick hack to set correct target name
                    if not self.EXPORT_ANIMTARGETNAME:
                        if "Bip01" in [node.name for
                                       node in node_kfctrls.iterkeys()]:
                            targetname = "Bip01"
                        elif "Bip02" in [node.name for
                                        node in node_kfctrls.iterkeys()]:
                            targetname = "Bip02"
                        else:
                            targetname = root_block.name
                    else:
                        targetname = self.EXPORT_ANIMTARGETNAME
                    kf_root.target_name = targetname
                    kf_root.string_palette = NifFormat.NiStringPalette()
                    for node, ctrls \
                        in izip(node_kfctrls.iterkeys(),
                                node_kfctrls.itervalues()):
                        # export a block for every interpolator in every
                        # controller
                        for ctrl in ctrls:
                            # XXX add get_interpolators to pyffi interface
                            if isinstance(ctrl,
                                          NifFormat.NiSingleInterpController):
                                interpolators = [ctrl.interpolator]
                            elif isinstance(
                                ctrl, (NifFormat.NiGeomMorpherController,
                                       NifFormat.NiMorphWeightsController)):
                                interpolators = ctrl.interpolators
                            if isinstance(ctrl,
                                          NifFormat.NiGeomMorpherController):
                                variable_2s = [morph.frame_name
                                               for morph in ctrl.data.morphs]
                            else:
                                variable_2s = [None
                                               for interpolator in interpolators]
                            for interpolator, variable_2 in izip(interpolators,
                                                                variable_2s):
                                # create ControlledLink for each
                                # interpolator
                                controlledblock = kf_root.add_controlled_block()
                                if self.version < 0x0A020000:
                                    # older versions need the actual controller
                                    # blocks
                                    controlledblock.target_name = node.name
                                    controlledblock.controller = ctrl
                                    # erase reference to target node
                                    ctrl.target = None
                                else:
                                    # newer versions need the interpolator
                                    # blocks
                                    controlledblock.interpolator = interpolator
                                # get bone animation priority (previously
                                # fetched from the constraints during
                                # export_bones)
                                if not node.name in self.bone_priorities or self.EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES:
                                    if self.EXPORT_ANIMPRIORITY != 0:
                                        priority = self.EXPORT_ANIMPRIORITY
                                    else:
                                        priority = 26
                                        self.logger.warning(
                                            "No priority set for bone %s, "
                                            "falling back on default value (%i)"
                                            % (node.name, priority))
                                else:
                                    priority = self.bone_priorities[node.name]
                                controlledblock.priority = priority
                                # set palette, and node and controller type
                                # names, and variables
                                controlledblock.string_palette = kf_root.string_palette
                                controlledblock.set_node_name(node.name)
                                controlledblock.set_controller_type(ctrl.__class__.__name__)
                                if variable_2:
                                    controlledblock.set_variable_2(variable_2)
                else:
                    raise NifExportError(
                        "Keyframe export for '%s' is not supported. "
                        " Only Morrowind, Oblivion, Fallout 3, Civilization IV,"
                        " Zoo Tycoon 2, Freedom Force, and"
                        " Freedom Force vs. the 3rd Reich"
                        " keyframes are supported."
                        % self.EXPORT_VERSION)

                # write kf (and xnif if asked)
                prefix = "" if not self.EXPORT_MW_NIFXNIFKF else "x"

                ext = ".kf"
                self.logger.info("Writing %s file" % (prefix + ext))
                self.msg_progress("Writing %s file" % (prefix + ext))

                self.filename = Blender.sys.join(self.filepath,
                                                 prefix + self.filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version2=NIF_USER_VERSION2)
                data.roots = [kf_root]
                data.neosteam = (self.EXPORT_VERSION == "NeoSteam")
                stream = open(self.filename, "wb")
                try:
                    data.write(stream)
                finally:
                    stream.close()

            if self.EXPORT_MW_NIFXNIFKF:
                self.logger.info("Detaching keyframe controllers from nif")
                # detach the keyframe controllers from the nif (for xnif)
                for node in root_block.tree():
                    if not isinstance(node, NifFormat.NiNode):
                        continue
                    # remove references to keyframe controllers from node
                    # (for xnif)
                    while isinstance(node.controller, NifFormat.NiKeyframeController):
                        node.controller = node.controller.next_controller
                    ctrl = node.controller
                    while ctrl:
                        if isinstance(ctrl.next_controller,
                                      NifFormat.NiKeyframeController):
                            ctrl.next_controller = ctrl.next_controller.next_controller
                        else:
                            ctrl = ctrl.next_controller

                self.logger.info("Detaching animation text keys from nif")
                # detach animation text keys
                if root_block.extra_data is not anim_textextra:
                    raise RuntimeError(
                        "Oops, you found a bug! Animation extra data"
                        " wasn't where expected...")
                root_block.extra_data = None

                prefix = "x" # we are in morrowind 'nifxnifkf mode'
                ext = ".nif"
                self.logger.info("Writing %s file" % (prefix + ext))
                self.msg_progress("Writing %s file" % (prefix + ext))

                self.filename = Blender.sys.join(self.filepath,
                                                 prefix + self.filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version2=NIF_USER_VERSION2)
                data.roots = [root_block]
                data.neosteam = (self.EXPORT_VERSION == "NeoSteam")
                stream = open(self.filename, "wb")
                try:
                    data.write(stream)
                finally:
                    stream.close()

            # export egm file:
            #-----------------

            if self.egmdata:
                ext = ".egm"
                self.logger.info("Writing %s file" % ext)
                self.msg_progress("Writing %s file" % ext)

                self.filename = Blender.sys.join(self.filepath,
                                                 self.filebase + ext)
                stream = open(self.filename, "wb")
                try:
                    self.egmdata.write(stream)
                finally:
                    stream.close()

        # export error: raise a menu instead of an exception
        except NifExportError, e:
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('EXPORT ERROR%t|' + str(e))
            print 'NifExportError: ' + str(e)
            return

        # IO error: raise a menu instead of an exception
        except IOError, e: 
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('I/O ERROR%t|' + str(e))
            print 'IOError: ' + str(e)
            return

        # other error: raise a menu and an exception
        except StandardError, e:
            e = str(e).replace("\n", " ")
            Blender.Draw.PupMenu('ERROR%t|' + str(e) + '    Check console for possibly more details.')
            raise

        finally:
            # clear progress bar
            self.msg_progress("Finished", progbar = 1)

        # save exported file (this is used by the test suite)
        self.root_blocks = [root_block]



    def export_node(self, ob, space, parent_block, node_name):
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
            node = self.create_ninode()
            ob_type = None
            ob_ipo = None
        else:
            # -> empty, mesh, or armature
            ob_type = ob.getType()
            assert(ob_type in ['Empty', 'Mesh', 'Armature']) # debug
            assert(parent_block) # debug
            ob_ipo = ob.getIpo() # get animation data
            ob_children = self.get_b_children(ob)
            
            if (node_name == 'RootCollisionNode'):
                # -> root collision node (can be mesh or empty)
                ob.rbShapeBoundType = Blender.Object.RBShapes['POLYHEDERON']
                ob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
                ob.drawMode = Blender.Object.DrawModes['WIRE']
                self.export_collision(ob, parent_block)
                return None # done; stop here
            elif ob_type == 'Mesh' and ob.name.lower().startswith('bsbound'):
                # add a bounding box
                self.export_bounding_box(ob, parent_block, bsbound=True)
                return None # done; stop here
            elif (ob_type == 'Mesh'
                  and ob.name.lower().startswith("bounding box")):
                # Morrowind bounding box
                self.export_bounding_box(ob, parent_block, bsbound=False)
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
                    # does geom have priority value in NULL constraint?
                    elif constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.get_bone_name_for_nif(ob.name)
                            ] = int(constr.name[9:])
                if is_collision:
                    self.export_collision(ob, parent_block)
                    return None # done; stop here
                elif has_ipo or has_children or is_multimaterial or has_track:
                    # -> mesh ninode for the hierarchy to work out
                    if not has_track:
                        node = self.create_block('NiNode', ob)
                    else:
                        node = self.create_block('NiBillboardNode', ob)
                else:
                    # don't create intermediate ninode for this guy
                    self.export_tri_shapes(ob, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.create_ninode(ob)
                # does node have priority value in NULL constraint?
                for constr in ob.constraints:
                    if constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.get_bone_name_for_nif(ob.name)
                            ] = int(constr.name[9:])

        # set transform on trishapes rather than on NiNode for skinned meshes
        # this fixes an issue with clothing slots
        if ob_type == 'Mesh':
            ob_parent = ob.getParent()
            if ob_parent and ob_parent.getType() == 'Armature':
                if ob_ipo:
                    # mesh with armature parent should not have animation!
                    self.logger.warn(
                        "Mesh %s is skinned but also has object animation. "
                        "The nif format does not support this: "
                        "ignoring object animation." % ob.name)
                    ob_ipo = None
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
        if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
            node.flags = 0x000E
        elif self.EXPORT_VERSION in ("Sid Meier's Railroads",
                                     "Civilization IV"):
            node.flags = 0x0010
        elif self.EXPORT_VERSION in ("Empire Earth II",):
            node.flags = 0x0002
        elif self.EXPORT_VERSION in ("Divinity 2",):
            node.flags = 0x0310
        else:
            # morrowind
            node.flags = 0x000C

        self.export_matrix(ob, space, node)

        if ob:
            # export animation
            if ob_ipo:
                if any(
                    ob_ipo[b_channel]
                    for b_channel in (Ipo.OB_LOCX, Ipo.OB_ROTX, Ipo.OB_SCALEX)):
                    self.export_keyframes(ob_ipo, space, node)
                self.export_object_vis_controller(b_object=ob, n_node=node)
            # if it is a mesh, export the mesh as trishape children of
            # this ninode
            if (ob.getType() == 'Mesh'):
                # see definition of trishape_space above
                self.export_tri_shapes(ob, trishape_space, node)
                
            # if it is an armature, export the bones as ninode
            # children of this ninode
            elif (ob.getType() == 'Armature'):
                self.export_bones(ob, node)

            # export all children of this empty/mesh/armature/bone
            # object as children of this NiNode
            self.export_children(ob, node)

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
    def export_keyframes(self, ipo, space, parent_block, bind_mat = None,
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
            kfc = self.create_block("NiKeyframeController", ipo)
        else:
            kfc = self.create_block("NiTransformController", ipo)
            kfi = self.create_block("NiTransformInterpolator", ipo)
            # link interpolator from the controller
            kfc.interpolator = kfi
            # set interpolator default data
            scale, quat, trans = \
                parent_block.get_transform().get_scale_quat_translation()
            kfi.translation.x = trans.x
            kfi.translation.y = trans.y
            kfi.translation.z = trans.z
            kfi.rotation.x = quat.x
            kfi.rotation.y = quat.y
            kfi.rotation.z = quat.z
            kfi.rotation.w = quat.w
            kfi.scale = scale

        parent_block.add_controller(kfc)

        # determine cycle mode for this controller
        # this is stored in the blender ipo curves
        # while we're at it, we also determine the
        # start and stop frames
        extend = None
        if ipo:
            start_frame = +1000000
            stop_frame = -1000000
            for curve in ipo:
                # get cycle mode
                if extend is None:
                    extend = curve.extend
                elif extend != curve.extend:
                    self.logger.warn(
                        "Inconsistent extend type in %s, will use %s."
                        % (ipo, extend))
                # get start and stop frames
                start_frame = min(
                    start_frame,
                    min(btriple.pt[0] for btriple in curve.bezierPoints))
                stop_frame = max(
                    stop_frame,
                    max(btriple.pt[0] for btriple in curve.bezierPoints))
        else:
            # dummy ipo
            # default extend, start, and end
            extend = Blender.IpoCurve.ExtendTypes.CYCLIC
            start_frame = self.fstart
            stop_frame = self.fend

        # fill in the non-trivial values
        kfc.flags = 8 # active
        kfc.flags |= self.get_flags_from_extend(extend)
        kfc.frequency = 1.0
        kfc.phase = 0.0
        kfc.start_time = (start_frame - 1) * self.fspeed
        kfc.stop_time = (stop_frame - 1) * self.fspeed

        if self.EXPORT_ANIMATION == 1:
            # keyframe data is not present in geometry files
            return

        # -> get keyframe information
        
        # some calculations
        if bind_mat:
            bind_scale, bind_rot, bind_trans = self.decompose_srt(bind_mat)
            bind_quat = bind_rot.toQuat()
        else:
            bind_scale = 1.0
            bind_rot = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
            bind_quat = Blender.Mathutils.Quaternion(1,0,0,0)
            bind_trans = Blender.Mathutils.Vector(0,0,0)
        if extra_mat_inv:
            extra_scale_inv, extra_rot_inv, extra_trans_inv = \
                self.decompose_srt(extra_mat_inv)
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
                    raise NifExportError(
                        "missing curves in %s; insert %s key at frame 1"
                        " and try again"
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
                             10 * ipo[Ipo.OB_ROTZ][frame]])
                        # use quat if we have bind matrix and/or extra matrix
                        # XXX maybe we should just stick with eulers??
                        if bind_mat or extra_mat_inv:
                            rot_curve[frame] = rot_curve[frame].toQuat()
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

        if (max(len(rot_curve), len(trans_curve), len(scale_curve)) <= 1
            and self.version >= 0x0A020000):
            # only add data if number of keys is > 1
            # (see importer comments with import_kf_root: a single frame
            # keyframe denotes an interpolator without further data)
            # insufficient keys, so set the data and we're done!
            if trans_curve:
                trans = trans_curve.values()[0]
                kfi.translation.x = trans[0]
                kfi.translation.y = trans[1]
                kfi.translation.z = trans[2]
            if rot_curve:
                rot = rot_curve.values()[0]
                # XXX blender weirdness... Euler() is a function!!
                if isinstance(rot, Blender.Mathutils.Euler().__class__):
                    rot = rot.toQuat()
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
            kfd = self.create_block("NiKeyframeData", ipo)
            kfc.data = kfd
        else:
            # number of frames is > 1, so add transform data
            kfd = self.create_block("NiTransformData", ipo)
            kfi.data = kfd

        frames = rot_curve.keys()
        frames.sort()
        # XXX blender weirdness... Euler() is a function!!
        if (frames
            and isinstance(rot_curve.values()[0],
                           Blender.Mathutils.Euler().__class__)):
            # eulers
            kfd.rotation_type = NifFormat.KeyType.XYZ_ROTATION_KEY
            kfd.num_rotation_keys = 1 # *NOT* len(frames) this crashes the engine!
            kfd.xyz_rotations[0].num_keys = len(frames)
            kfd.xyz_rotations[1].num_keys = len(frames)
            kfd.xyz_rotations[2].num_keys = len(frames)
            # XXX todo: quadratic interpolation?
            kfd.xyz_rotations[0].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[1].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[2].interpolation = NifFormat.KeyType.LINEAR_KEY
            kfd.xyz_rotations[0].keys.update_size()
            kfd.xyz_rotations[1].keys.update_size()
            kfd.xyz_rotations[2].keys.update_size()
            for i, frame in enumerate(frames):
                # XXX todo: speed up by not recalculating stuff
                rot_frame_x = kfd.xyz_rotations[0].keys[i]
                rot_frame_y = kfd.xyz_rotations[1].keys[i]
                rot_frame_z = kfd.xyz_rotations[2].keys[i]
                rot_frame_x.time = (frame - 1) * self.fspeed
                rot_frame_y.time = (frame - 1) * self.fspeed
                rot_frame_z.time = (frame - 1) * self.fspeed
                rot_frame_x.value = rot_curve[frame].x * 3.14159265358979323846 / 180.0
                rot_frame_y.value = rot_curve[frame].y * 3.14159265358979323846 / 180.0
                rot_frame_z.value = rot_curve[frame].z * 3.14159265358979323846 / 180.0
        else:
            # quaternions
            # XXX todo: quadratic interpolation?
            kfd.rotation_type = NifFormat.KeyType.LINEAR_KEY
            kfd.num_rotation_keys = len(frames)
            kfd.quaternion_keys.update_size()
            for i, frame in enumerate(frames):
                rot_frame = kfd.quaternion_keys[i]
                rot_frame.time = (frame - 1) * self.fspeed
                rot_frame.value.w = rot_curve[frame].w
                rot_frame.value.x = rot_curve[frame].x
                rot_frame.value.y = rot_curve[frame].y
                rot_frame.value.z = rot_curve[frame].z

        frames = trans_curve.keys()
        frames.sort()
        kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.translations.num_keys = len(frames)
        kfd.translations.keys.update_size()
        for i, frame in enumerate(frames):
            trans_frame = kfd.translations.keys[i]
            trans_frame.time = (frame - 1) * self.fspeed
            trans_frame.value.x = trans_curve[frame][0]
            trans_frame.value.y = trans_curve[frame][1]
            trans_frame.value.z = trans_curve[frame][2]

        frames = scale_curve.keys()
        frames.sort()
        kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
        kfd.scales.num_keys = len(frames)
        kfd.scales.keys.update_size()
        for i, frame in enumerate(frames):
            scale_frame = kfd.scales.keys[i]
            scale_frame.time = (frame - 1) * self.fspeed
            scale_frame.value = scale_curve[frame]

    def export_vertex_color_property(self, block_parent,
                                     flags=1,
                                     vertex_mode=0, lighting_mode=1):
        """Create a vertex color property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param vertex_mode: The C{vertex_mode} of the new property.
        @param lighting_mode: The C{lighting_mode} of the new property.
        @return: The new property block.
        """
        # create new vertex color property block
        vcolprop = self.create_block("NiVertexColorProperty")
        
        # make it a property of the parent
        block_parent.add_property(vcolprop)

        # and now export the parameters
        vcolprop.flags = flags
        vcolprop.vertex_mode = vertex_mode
        vcolprop.lighting_mode = lighting_mode

        return vcolprop

    def export_z_buffer_property(self, block_parent,
                                 flags=15, function=3):
        """Create a z-buffer property, and attach it to an existing block
        (typically, the root of the nif tree).

        @param block_parent: The block to which to attach the new property.
        @param flags: The C{flags} of the new property.
        @param function: The C{function} of the new property.
        @return: The new property block.
        """
        # create new z-buffer property block
        zbuf = self.create_block("NiZBufferProperty")

        # make it a property of the parent
        block_parent.add_property(zbuf)

        # and now export the parameters
        zbuf.flags = flags
        zbuf.function = function

        return zbuf

    def export_anim_groups(self, animtxt, block_parent):
        """Parse the animation groups buffer and write an extra string
        data block, and attach it to an existing block (typically, the root
        of the nif tree)."""
        if self.EXPORT_ANIMATION == 1:
            # animation group extra data is not present in geometry only files
            return

        self.logger.info("Exporting animation groups")
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
                self.logger.warn("frame in animation buffer out of range "
                                 "(%i not in [%i, %i])"
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
        textextra = self.create_block("NiTextKeyExtraData", animtxt)
        block_parent.add_extra_data(textextra)
        
        # create a text key for each frame descriptor
        textextra.num_text_keys = len(flist)
        textextra.text_keys.update_size()
        for i, key in enumerate(textextra.text_keys):
            key.time = self.fspeed * (flist[i]-1)
            key.value = dlist[i]

        return textextra

    def export_texture_filename(self, texture):
        """Returns file name from texture.

        @param texture: The texture object in blender.
        @return: The file name of the image used in the texture.
        """
        if texture.type == Blender.Texture.Types.ENVMAP:
            # this works for morrowind only
            if self.EXPORT_VERSION != "Morrowind":
                raise NifExportError(
                    "cannot export environment maps for nif version '%s'"
                    %self.EXPORT_VERSION)
            return "enviro 01.TGA"
        elif texture.type == Blender.Texture.Types.IMAGE:
            # get filename from image

            # check that image is loaded
            if texture.getImage() is None:
                raise NifExportError(
                    "image type texture has no file loaded ('%s')"
                    % texture.getName())                    

            filename = texture.image.getFilename()

            # warn if packed flag is enabled
            if texture.getImage().packed:
                self.logger.warn(
                    "Packed image in texture '%s' ignored, "
                    "exporting as '%s' instead."
                    % (texture.getName(), filename))
            
            # try and find a DDS alternative, force it if required
            ddsfilename = "%s%s" % (filename[:-4], '.dds')
            if Blender.sys.exists(ddsfilename) or self.EXPORT_FORCEDDS:
                filename = ddsfilename

            # sanitize file path
            if not self.EXPORT_VERSION in ('Morrowind', 'Oblivion',
                                           'Fallout 3'):
                # strip texture file path
                filename = Blender.sys.basename(filename)
            else:
                # strip the data files prefix from the texture's file name
                filename = filename.lower()
                idx = filename.find("textures")
                if ( idx >= 0 ):
                    filename = filename[idx:]
                else:
                    self.logger.warn(
                        "%s does not reside in a 'Textures' folder;"
                        " texture path will be stripped"
                        " and textures may not display in-game" % filename)
                    filename = Blender.sys.basename(filename)
            # for linux export: fix path seperators
            return filename.replace('/', '\\')
        else:
            # texture must be of type IMAGE or ENVMAP
            raise NifExportError(
                "Error: Texture '%s' must be of type IMAGE or ENVMAP"
                % texture.getName())

    def export_source_texture(self, texture=None, filename=None):
        """Export a NiSourceTexture.

        @param texture: The texture object in blender to be exported.
        @param filename: The full or relative path to the texture file
            (this argument is used when exporting NiFlipControllers
            and when exporting default shader slots that have no use in
            being imported into Blender).
        @return: The exported NiSourceTexture block."""
        
        # create NiSourceTexture
        srctex = NifFormat.NiSourceTexture()
        srctex.use_external = True
        if not filename is None:
            # preset filename
            srctex.file_name = filename
        elif not texture is None:
            srctex.file_name = self.export_texture_filename(texture)
        else:
            # this probably should not happen
            logger.warning(
                "Exporting source texture without texture or filename (bug?).")

        # fill in default values (TODO: can we use 6 for everything?)
        if self.version >= 0x0a000100:
            srctex.pixel_layout = 6
        else:
            srctex.pixel_layout = 5
        srctex.use_mipmaps = 1
        srctex.alpha_format = 3
        srctex.unknown_byte = 1

        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiSourceTexture) and block.get_hash() == srctex.get_hash():
                return block

        # no identical source texture found, so use and register
        # the new one
        return self.register_block(srctex, texture)



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
    def export_flip_controller(self, fliptxt, texture, target, target_tex):
        tlist = fliptxt.asLines()

        # create a NiFlipController
        flip = self.create_block("NiFlipController", fliptxt)
        target.add_controller(flip)

        # fill in NiFlipController's values
        flip.flags = 8 # active
        flip.frequency = 1.0
        flip.start_time = (self.fstart - 1) * self.fspeed
        flip.stop_time = ( self.fend - self.fstart ) * self.fspeed
        flip.texture_slot = target_tex
        count = 0
        for t in tlist:
            if len( t ) == 0: continue  # skip empty lines
            # create a NiSourceTexture for each flip
            tex = self.export_source_texture(texture, t)
            flip.num_sources += 1
            flip.sources.update_size()
            flip.sources[flip.num_sources-1] = tex
            count += 1
        if count < 2:
            raise NifExportError(
                "Error in Texture Flip buffer '%s':"
                " must define at least two textures"
                %fliptxt.getName())
        flip.delta = (flip.stop_time - flip.start_time) / count



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
    def export_tri_shapes(self, ob, space, parent_block, trishape_name = None):
        self.logger.info("Exporting %s" % ob)
        self.msg_progress("Exporting %s" % ob.name)
        assert(ob.getType() == 'Mesh')

        # get mesh from ob
        mesh = ob.getData(mesh=1) # get mesh data
        
        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if len(ob.data.verts) == 0:
            # do not export anything
            self.logger.warn("%s has no vertices, skipped." % ob)
            return

        # get the mesh's materials, this updates the mesh material list
        if not isinstance(parent_block, NifFormat.RootCollisionNode):
            mesh_mats = mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_mats = []
        # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
        if (mesh_mats == []):
            mesh_mats = [None]

        # is mesh double sided?
        mesh_doublesided = (mesh.mode & Blender.Mesh.Modes.TWOSIDED)

        # let's now export one trishape for every mesh material
        ### TODO: needs refactoring - move material, texture, etc.
        ### to separate function
        for materialIndex, mesh_mat in enumerate(mesh_mats):
            # -> first, extract valuable info from our ob
            
            mesh_base_mtex = None
            mesh_glow_mtex = None
            mesh_bump_mtex = None
            mesh_gloss_mtex = None
            mesh_dark_mtex = None
            mesh_detail_mtex = None
            mesh_texeff_mtex = None
            mesh_ref_mtex = None
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
                if ( mesh_mat_specular_color[0] > self.EPSILON ) \
                    or ( mesh_mat_specular_color[1] > self.EPSILON ) \
                    or ( mesh_mat_specular_color[2] > self.EPSILON ):
                    mesh_hasspec = True
                mesh_mat_emissive = mesh_mat.getEmit()              # 'Emit' scrollbar in Blender (MW -> 0.0 0.0 0.0)
                mesh_mat_glossiness = mesh_mat.getHardness() / 4.0  # 'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_transparency = mesh_mat.getAlpha()         # 'A(lpha)' scrollbar in Blender (MW -> 1.0)
                mesh_hasalpha = (abs(mesh_mat_transparency - 1.0) > self.EPSILON) \
                                or (mesh_mat.getIpo() != None
                                    and mesh_mat.getIpo().getCurve('Alpha'))
                mesh_haswire = mesh_mat.mode & Blender.Material.Modes.WIRE
                mesh_mat_ambient_color = [0.0, 0.0, 0.0]
                mesh_mat_ambient_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_ambient
                mesh_mat_ambient_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_ambient
                mesh_mat_ambient_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_ambient
                mesh_mat_emissive_color = [0.0, 0.0, 0.0]
                mesh_mat_emitmulti = 1.0 # default
                if self.EXPORT_VERSION != "Fallout 3":
                    mesh_mat_emissive_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_emissive
                    mesh_mat_emissive_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_emissive
                    mesh_mat_emissive_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_emissive
                else:
                    # special case for Fallout 3 (it does not store diffuse color)
                    # if emit is non-zero, set emissive color to diffuse
                    # (otherwise leave the color to zero)
                    if mesh_mat.emit > self.EPSILON:
                        mesh_mat_emissive_color = mesh_mat_diffuse_color
                        mesh_mat_emitmulti = mesh_mat.emit * 10.0
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
                            raise NifExportError(
                                "Non-COL-mapped reflection texture in"
                                " mesh '%s', material '%s',"
                                " these cannot be exported to NIF."
                                " Either delete all non-COL-mapped"
                                " reflection textures,"
                                " or in the Shading Panel,"
                                " under Material Buttons,"
                                " set texture 'Map To' to 'COL'."
                                % (ob.getName(),mesh_mat.getName()))
                        if mtex.blendmode != Blender.Texture.BlendModes["ADD"]:
                            # it should have "ADD" blending mode
                            self.logger.warn(
                               "Reflection texture should have blending"
                               " mode 'Add' on texture"
                               " in mesh '%s', material '%s')."
                               % (ob.getName(),mesh_mat.getName()))
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
                        if mtex.mapto & Blender.Texture.MapTo.EMIT:
                            # got the glow tex
                            if mesh_glow_mtex:
                                raise NifExportError(
                                    "Multiple glow textures in"
                                    " mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.EMIT"
                                    %(mesh.name,mesh_mat.getName()))
                            # check if calculation of alpha channel is enabled
                            # for this texture
                            if (mtex.tex.imageFlags & Blender.Texture.ImageFlags.CALCALPHA != 0) \
                               and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                self.logger.warn(
                                    "In mesh '%s', material '%s':"
                                    " glow texture must have"
                                    " CALCALPHA flag set, and must have"
                                    " MapTo.ALPHA enabled."
                                    %(ob.getName(),mesh_mat.getName()))
                            mesh_glow_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.SPEC:
                            # got the gloss map
                            if mesh_gloss_mtex:
                                raise NifExportError(
                                    "Multiple gloss textures in"
                                    " mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.SPEC"
                                    %(mesh.name,mesh_mat.getName()))
                            mesh_gloss_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.NOR:
                            # got the normal map
                            if mesh_bump_mtex:
                                raise NifExportError(
                                    "Multiple bump/normal textures"
                                    " in mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.NOR"
                                    %(mesh.name,mesh_mat.getName()))
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
                                if mesh_mat_transparency > self.EPSILON:
                                    raise NifExportError(
                                        "Cannot export this type of"
                                        " transparency in material '%s': "
                                        " instead, try to set alpha to 0.0"
                                        " and to use the 'Var' slider"
                                        " in the 'Map To' tab under the"
                                        " material buttons."
                                        %mesh_mat.getName())
                                if (mesh_mat.getIpo() and mesh_mat.getIpo().getCurve('Alpha')):
                                    raise NifExportError(
                                        "Cannot export animation for"
                                        " this type of transparency"
                                        " in material '%s':"
                                        " remove alpha animation,"
                                        " or turn off MapTo.ALPHA,"
                                        " and try again."
                                        %mesh_mat.getName())
                                mesh_mat_transparency = mtex.varfac # we must use the "Var" value
                                mesh_hasalpha = True
                        elif mtex.mapto & Blender.Texture.MapTo.COL and \
                             not mesh_detail_mtex:
                            # extra COL channel is considered
                            # as detail texture
                            mesh_detail_mtex = mtex
                        elif mtex.mapto & Blender.Texture.MapTo.REF:
                            # got the reflection map
                            if mesh_ref_mtex:
                                raise NifExportError(
                                    "Multiple reflection textures"
                                    " in mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.REF"
                                    %(mesh.name,mesh_mat.getName()))
                            mesh_ref_mtex = mtex
                        else:
                            # unknown map
                            raise NifExportError(
                                "Do not know how to export texture '%s',"
                                " in mesh '%s', material '%s'."
                                " Either delete it, or if this texture"
                                " is to be your base texture,"
                                " go to the Shading Panel,"
                                " Material Buttons, and set texture"
                                " 'Map To' to 'COL'."
                                % (mtex.tex.getName(),ob.getName(),mesh_mat.getName()))
                    else:
                        # nif only support UV-mapped textures
                        raise NifExportError(
                            "Non-UV texture in mesh '%s', material '%s'."
                            " Either delete all non-UV textures,"
                            " or in the Shading Panel,"
                            " under Material Buttons,"
                            " set texture 'Map Input' to 'UV'."
                            %(ob.getName(),mesh_mat.getName()))

            # list of body part (name, index, vertices) in this mesh
            bodypartgroups = []
            for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
                if bodypartgroupname in ob.data.getVertGroupNames():
                    self.logger.debug("Found body part %s"
                                      % bodypartgroupname)
                    bodypartgroups.append(
                        [bodypartgroupname,
                         getattr(NifFormat.BSDismemberBodyPartType,
                                 bodypartgroupname),
                         set(ob.data.getVertsFromGroup(bodypartgroupname))])

            # -> now comes the real export
            
            # We now extract vertices, uv-vertices, normals, and vertex
            # colors from the mesh's face list. NIF has one uv vertex and
            # one normal per vertex, unlike blender's uv vertices and
            # normals per face... therefore some vertices must be
            # duplicated. The following algorithm extracts all unique
            # (vert, uv-vert, normal, vcol) quads, and uses this list to
            # produce the list of vertices, uv-vertices, normals, vertex
            # colors, and face indices.

            # NIF uses the normal table for lighting. So, smooth faces
            # should use Blender's vertex normals, and solid faces should
            # use Blender's face normals.
            
            vertquad_list = [] # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [None for i in xrange(len(mesh.verts))] # blender vertex -> nif vertices
            vertlist = []
            normlist = []
            vcollist = []
            uvlist = []
            trilist = []
            # for each face in trilist, a body part index
            bodypartfacemap = []
            faces_without_bodypart = []
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
                            "ERROR%t|Create a UV map for every texture,"
                            " and run the script again.")
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
                            self.logger.warning(
                                "Vertex color painting/lighting enabled,"
                                " but mesh has no vertex color data;"
                                " vertex colors will not be written.")
                            fcol = None
                            mesh_hasvcol = False
                        else:
                            # NIF stores the colour values as floats
                            fcol = f.col[i]
                    else:
                        fcol = None
                        
                    vertquad = ( fv, fuv, fn, fcol )

                    # do we already have this quad? (optimized by m_4444x)
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
                                       > self.EPSILON:
                                     continue
                                if max(abs(vertquad[1][uvlayer][1]
                                           - vertquad_list[j][1][uvlayer][1])
                                       for uvlayer
                                       in xrange(len(mesh_uvlayers))) \
                                       > self.EPSILON:
                                    continue
                            if mesh_hasnormals:
                                if abs(vertquad[2][0] - vertquad_list[j][2][0]) > self.EPSILON: continue
                                if abs(vertquad[2][1] - vertquad_list[j][2][1]) > self.EPSILON: continue
                                if abs(vertquad[2][2] - vertquad_list[j][2][2]) > self.EPSILON: continue
                            if mesh_hasvcol:
                                if abs(vertquad[3].r - vertquad_list[j][3].r) > self.EPSILON: continue
                                if abs(vertquad[3].g - vertquad_list[j][3].g) > self.EPSILON: continue
                                if abs(vertquad[3].b - vertquad_list[j][3].b) > self.EPSILON: continue
                                if abs(vertquad[3].a - vertquad_list[j][3].a) > self.EPSILON: continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break

                    if f_index[i] > 65535:
                        raise NifExportError(
                            "ERROR%t|Too many vertices. Decimate your mesh"
                            " and try again.")
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
                    # add body part number
                    if (self.EXPORT_VERSION != "Fallout 3"
                        or not bodypartgroups
                        or not self.EXPORT_FO3_BODYPARTS):
                        bodypartfacemap.append(0)
                    else:
                        for bodypartname, bodypartindex, bodypartverts in bodypartgroups:
                            if (set(b_vert.index for b_vert in f.verts)
                                <= bodypartverts):
                                bodypartfacemap.append(bodypartindex)
                                break
                        else:
                            # this signals an error
                            faces_without_bodypart.append(f)

            # check that there are no missing body part faces
            if faces_without_bodypart:
                Blender.Window.EditMode(0)
                # select mesh object
                for bobj in self.scene.objects:
                    bobj.sel = False
                self.scene.objects.active = ob
                ob.sel = 1
                # select bad faces
                for face in mesh.faces:
                    face.sel = 0
                for face in faces_without_bodypart:
                    face.sel = 1
                # switch to edit mode and raise exception
                Blender.Window.EditMode(1)
                raise ValueError(
                    "Some faces of %s not assigned to any body part."
                    " The unassigned faces"
                    " have been selected in the mesh so they can easily"
                    " be identified."
                    % ob)

            if len(trilist) > 65535:
                raise NifExportError(
                    "ERROR%t|Too many faces. Decimate your mesh and try again.")
            if len(vertlist) == 0:
                continue # m_4444x: skip 'empty' material indices
            
            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

            # create a trishape block
            if not self.EXPORT_STRIPIFY:
                trishape = self.create_block("NiTriShape", ob)
            else:
                trishape = self.create_block("NiTriStrips", ob)

            # add texture effect block (must be added as preceeding child of
            # the trishape)
            if self.EXPORT_VERSION == "Morrowind" and mesh_texeff_mtex:
                # create a new parent block for this shape
                extra_node = self.create_block("NiNode", mesh_texeff_mtex)
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
            trishape.name = self.get_full_name(trishape.name)
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                trishape.flags = 0x000E
            elif self.EXPORT_VERSION in ("Sid Meier's Railroads",
                                         "Civilization IV"):
                trishape.flags = 0x0010
            elif self.EXPORT_VERSION in ("Empire Earth II",):
                trishape.flags = 0x0016
            elif self.EXPORT_VERSION in ("Divinity 2",):
                if trishape.name.lower[-3:] in ("med", "low"):
                    trishape.flags = 0x0014
                else:
                    trishape.flags = 0x0016
            else:
                # morrowind
                if ob.getDrawType() != 2: # not wire
                    trishape.flags = 0x0004 # use triangles as bounding box
                else:
                    trishape.flags = 0x0005 # use triangles as bounding box + hide

            # extra shader for Sid Meier's Railroads
            if self.EXPORT_VERSION == "Sid Meier's Railroads":
                trishape.has_shader = True
                trishape.shader_name = "RRT_NormalMap_Spec_Env_CubeLight"
                trishape.unknown_integer = -1 # default

            self.export_matrix(ob, space, trishape)
            
            if mesh_base_mtex or mesh_glow_mtex:
                # add NiTriShape's texturing property
                if self.EXPORT_VERSION == "Fallout 3":
                    trishape.add_property(self.export_bs_shader_property(
                        basemtex = mesh_base_mtex,
                        glowmtex = mesh_glow_mtex,
                        bumpmtex = mesh_bump_mtex))
                        #glossmtex = mesh_gloss_mtex,
                        #darkmtex = mesh_dark_mtex,
                        #detailmtex = mesh_detail_mtex)) 
                else:
                    if (self.EXPORT_VERSION in self.USED_EXTRA_SHADER_TEXTURES
                        and self.EXPORT_EXTRA_SHADER_TEXTURES):
                        # sid meier's railroad and civ4:
                        # set shader slots in extra data
                        self.add_shader_integer_extra_datas(trishape)
                    trishape.add_property(self.export_texturing_property(
                        flags=0x0001, # standard
                        applymode=self.APPLYMODE[mesh_base_mtex.blendmode if mesh_base_mtex else Blender.Texture.BlendModes["MIX"]],
                        uvlayers=mesh_uvlayers,
                        basemtex=mesh_base_mtex,
                        glowmtex=mesh_glow_mtex,
                        bumpmtex=mesh_bump_mtex,
                        glossmtex=mesh_gloss_mtex,
                        darkmtex=mesh_dark_mtex,
                        detailmtex=mesh_detail_mtex,
                        refmtex=mesh_ref_mtex))

            if mesh_hasalpha:
                # add NiTriShape's alpha propery
                # refer to the alpha property in the trishape block
                if self.EXPORT_VERSION == "Sid Meier's Railroads":
                    alphaflags = 0x32ED
                    alphathreshold = 150
                elif self.EXPORT_VERSION == "Empire Earth II":
                    alphaflags = 0x00ED
                    alphathreshold = 0
                else:
                    alphaflags = 0x12ED
                    alphathreshold = 0
                trishape.add_property(
                    self.export_alpha_property(flags=alphaflags,
                                             threshold=alphathreshold))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.add_property(self.export_wireframe_property(flags=1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.add_property(self.export_stencil_property())

            if mesh_mat:
                # add NiTriShape's specular property
                # but NOT for sid meier's railroads and other extra shader
                # games (they use specularity even without this property)
                if (mesh_hasspec
                    and (self.EXPORT_VERSION
                         not in self.USED_EXTRA_SHADER_TEXTURES)):
                    # refer to the specular property in the trishape block
                    trishape.add_property(
                        self.export_specular_property(flags=0x0001))
                
                # add NiTriShape's material property
                trimatprop = self.export_material_property(
                    name=self.get_full_name(mesh_mat.getName()),
                    flags=0x0001, # ? standard
                    ambient=mesh_mat_ambient_color,
                    diffuse=mesh_mat_diffuse_color,
                    specular=mesh_mat_specular_color,
                    emissive=mesh_mat_emissive_color,
                    glossiness=mesh_mat_glossiness,
                    alpha=mesh_mat_transparency,
                    emitmulti=mesh_mat_emitmulti)
                
                # refer to the material property in the trishape block
                trishape.add_property(trimatprop)


                # material animation
                self.export_material_controllers(
                    b_material=mesh_mat, n_geom=trishape)

            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = self.create_block("NiTriShapeData", ob)
            else:
                tridata = self.create_block("NiTriStripsData", ob)
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
                    v.r = vcollist[i].r / 255.0
                    v.g = vcollist[i].g / 255.0
                    v.b = vcollist[i].b / 255.0
                    v.a = vcollist[i].a / 255.0

            if mesh_uvlayers:
                tridata.num_uv_sets = len(mesh_uvlayers)
                tridata.bs_num_uv_sets = len(mesh_uvlayers)
                if self.EXPORT_VERSION == "Fallout 3":
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
                                 stitchstrips=self.EXPORT_STITCHSTRIPS)

            # update tangent space (as binary extra data only for Oblivion)
            # for extra shader texture games, only export it if those
            # textures are actually exported (civ4 seems to be consistent with
            # not using tangent space on non shadered nifs)
            if mesh_uvlayers and mesh_hasnormals:
                if (self.EXPORT_VERSION in ("Oblivion", "Fallout 3")
                    or (self.EXPORT_VERSION in self.USED_EXTRA_SHADER_TEXTURES
                        and self.EXPORT_EXTRA_SHADER_TEXTURES)):
                    trishape.update_tangent_space(
                        as_extra=(self.EXPORT_VERSION == "Oblivion"))

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
                        if (self.EXPORT_VERSION == "Fallout 3"
                            and self.EXPORT_FO3_BODYPARTS):
                            skininst = self.create_block("BSDismemberSkinInstance", ob)
                        else:
                            skininst = self.create_block("NiSkinInstance", ob)
                        trishape.skin_instance = skininst
                        for block in self.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == self.get_full_name(armaturename):
                                    skininst.skeleton_root = block
                                    break
                        else:
                            raise NifExportError(
                                "Skeleton root '%s' not found."
                                % armaturename)
            
                        # create skinning data and link it
                        skindata = self.create_block("NiSkinData", ob)
                        skininst.data = skindata
            
                        skindata.has_vertex_weights = True
                        # fix geometry rest pose: transform relative to
                        # skeleton root
                        skindata.set_transform(
                            self.get_object_matrix(ob, 'localspace').get_inverse())
            
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
                                raise NifExportError(
                                    "Mesh %s has vertex group for bone %s,"
                                    " but no weights."
                                    " Please select the mesh, and either"
                                    " delete the vertex group,"
                                    " or go to weight paint mode,"
                                    " and paint weights."
                                    % (ob.name, bone))
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
                                    if block.name == self.get_full_name(bone):
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
                            raise NifExportError(
                                "Cannot export mesh with unweighted vertices."
                                " The unweighted vertices have been selected"
                                " in the mesh so they can easily be"
                                " identified.")

                        # update bind position skinning data
                        trishape.update_bind_position()

                        # calculate center and radius for each skin bone data
                        # block
                        trishape.update_skin_center_radius()

                        if (self.version >= 0x04020100
                            and self.EXPORT_SKINPARTITION):
                            self.logger.info("Creating skin partition")
                            lostweight = trishape.update_skin_partition(
                                maxbonesperpartition=self.EXPORT_BONESPERPARTITION,
                                maxbonespervertex=self.EXPORT_BONESPERVERTEX,
                                stripify=self.EXPORT_STRIPIFY,
                                stitchstrips=self.EXPORT_STITCHSTRIPS,
                                padbones=self.EXPORT_PADBONES,
                                triangles=trilist,
                                trianglepartmap=bodypartfacemap,
                                maximize_bone_sharing=(
                                    self.EXPORT_VERSION == 'Fallout 3'))
                            # warn on bad config settings
                            if self.EXPORT_VERSION == 'Oblivion':
                               if self.EXPORT_PADBONES:
                                   self.logger.warning(
                                       "Using padbones on Oblivion export,"
                                       " but you probably do not want to do"
                                       " this."
                                       " Disable the pad bones option to get"
                                       " higher quality skin partitions.")
                            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                               if self.EXPORT_BONESPERPARTITION < 18:
                                   self.logger.warning(
                                       "Using less than 18 bones"
                                       " per partition on Oblivion/Fallout 3"
                                       " export."
                                       " Set it to 18 to get higher quality"
                                       " skin partitions.")
                            if lostweight > self.EPSILON:
                                self.logger.warning(
                                    "Lost %f in vertex weights"
                                    " while creating a skin partition"
                                    " for Blender object '%s' (nif block '%s')"
                                    % (lostweight, ob.name, trishape.name))

                        # clean up
                        del vert_weights
                        del vert_added

            
            # shape key morphing
            key = mesh.key
            if key:
                if len(key.blocks) > 1:
                    # yes, there is a key object attached
                    # export as egm, or as morphdata?
                    if key.blocks[1].name.startswith("EGM"):
                        # egm export!
                        self.exportEgm(key.blocks)
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
                        morphctrl = self.create_block("NiGeomMorpherController",
                                                     keyipo)
                        trishape.add_controller(morphctrl)
                        morphctrl.target = trishape
                        morphctrl.frequency = 1.0
                        morphctrl.phase = 0.0
                        ctrlStart = 1000000.0
                        ctrlStop = -1000000.0
                        ctrlFlags = 0x000c
                        
                        # create geometry morph data
                        morphdata = self.create_block("NiMorphData", keyipo)
                        morphctrl.data = morphdata
                        morphdata.num_morphs = len(key.blocks)
                        morphdata.num_vertices = len(vertlist)
                        morphdata.morphs.update_size()
                        

                        # create interpolators (for newer nif versions)
                        morphctrl.num_interpolators = len(key.blocks)
                        morphctrl.interpolators.update_size()

                        # interpolator weights (for Fallout 3)
                        morphctrl.interpolator_weights.update_size()

                        # XXX some unknowns, bethesda only
                        # XXX just guessing here, data seems to be zero always
                        morphctrl.num_unknown_ints = len(key.blocks)
                        morphctrl.unknown_ints.update_size()

                        for keyblocknum, keyblock in enumerate(key.blocks):
                            # export morphed vertices
                            morph = morphdata.morphs[keyblocknum]
                            morph.frame_name = keyblock.name
                            self.logger.info("Exporting morph %s: vertices"
                                             % keyblock.name)
                            morph.arg = morphdata.num_vertices
                            morph.vectors.update_size()
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
                            curve = keyipo[keyblock.name]

                            # create interpolator for shape key
                            # (needs to be there even if there is no curve)
                            interpol = self.create_block("NiFloatInterpolator")
                            interpol.value = 0
                            morphctrl.interpolators[keyblocknum] = interpol
                            # fallout 3 stores interpolators inside the
                            # interpolator_weights block
                            morphctrl.interpolator_weights[keyblocknum].interpolator = interpol

                            # geometry only export has no float data
                            # also skip keys that have no curve (such as base key)
                            if self.EXPORT_ANIMATION == 1 or not curve:
                                continue

                            # note: we set data on morph for older nifs
                            # and on floatdata for newer nifs
                            # of course only one of these will be actually
                            # written to the file
                            self.logger.info("Exporting morph %s: curve"
                                             % keyblock.name)
                            interpol.data = self.create_block("NiFloatData", curve)
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
                                morph.keys[i].time = (knot[0] - self.fstart) * self.fspeed
                                morph.keys[i].value = curve.evaluate( knot[0] )
                                #morph.keys[i].forwardTangent = 0.0 # ?
                                #morph.keys[i].backwardTangent = 0.0 # ?
                                floatdata.keys[i].arg = floatdata.interpolation
                                floatdata.keys[i].time = (knot[0] - self.fstart) * self.fspeed
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



    def export_material_controllers(self, b_material, n_geom):
        """Export material animation data for given geometry."""
        if self.EXPORT_ANIMATION == 1:
            # geometry only: don't write controllers
            return

        self.export_material_alpha_controller(b_material, n_geom)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_MIRR, Blender.Ipo.MA_MIRG, Blender.Ipo.MA_MIRB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_AMBIENT)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_R, Blender.Ipo.MA_G, Blender.Ipo.MA_B),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_DIFFUSE)
        self.export_material_color_controller(
            b_material=b_material,
            b_channels=(
                Blender.Ipo.MA_SPECR, Blender.Ipo.MA_SPECG, Blender.Ipo.MA_SPECB),
            n_geom=n_geom,
            n_target_color=NifFormat.TargetColor.TC_SPECULAR)
        self.export_material_uv_controller(b_material, n_geom)

    def export_material_alpha_controller(self, b_material, n_geom):
        """Export the material alpha controller data."""
        b_ipo = b_material.getIpo()
        if not b_ipo:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_ipo[Blender.Ipo.MA_ALPHA]
        if not b_curve:
            return
        n_floatdata = self.create_block("NiFloatData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        n_floatdata.data.num_keys = len(b_curve.bezierPoints)
        n_floatdata.data.interpolation = self.get_n_ipol_from_b_ipol(
            b_curve.interpolation)
        n_floatdata.data.keys.update_size()
        for b_point, n_key in zip(b_curve.bezierPoints, n_floatdata.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_key.arg = n_floatdata.data.interpolation
            n_key.time = (b_time - 1) * self.fspeed
            n_key.value = b_value
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_alphactrl = self.create_block("NiAlphaController", b_ipo)
            n_alphaipol = self.create_block("NiFloatInterpolator", b_ipo)
            n_alphactrl.interpolator = n_alphaipol
            n_alphactrl.flags = 8 # active
            n_alphactrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_alphactrl.frequency = 1.0
            n_alphactrl.start_time = min(n_times)
            n_alphactrl.stop_time = max(n_times)
            n_alphactrl.data = n_floatdata
            n_alphaipol.data = n_floatdata
            # attach block to geometry
            n_matprop = self.find_property(n_geom,
                                           NifFormat.NiMaterialProperty)
            if not n_matprop:
                raise ValueError(
                    "bug!! must add material property"
                    " before exporting alpha controller")
            n_matprop.add_controller(n_alphactrl)

    def export_material_color_controller(
        self, b_material, b_channels, n_geom, n_target_color):
        """Export the material color controller data."""
        b_ipo = b_material.getIpo()
        if not b_ipo:
            return
        # get the material color curves and translate it into nif data
        b_curves = [b_ipo[b_channel] for b_channel in b_channels]
        if not all(b_curves):
            return
        n_posdata = self.create_block("NiPosData", b_curves)
        # and also to have common reference times for all curves
        b_times = set()
        for b_curve in b_curves:
            b_times |= set(b_point.pt[0] for b_point in b_curve.bezierPoints)
        # track all nif times: used later in start time and end time
        n_times = []
        n_posdata.data.num_keys = len(b_times)
        n_posdata.data.interpolation = self.get_n_ipol_from_b_ipol(
            b_curves[0].interpolation)
        n_posdata.data.keys.update_size()
        for b_time, n_key in zip(sorted(b_times), n_posdata.data.keys):
            # add each point of the curves
            n_key.arg = n_posdata.data.interpolation
            n_key.time = (b_time - 1) * self.fspeed
            n_key.value.x = b_curves[0][b_time]
            n_key.value.y = b_curves[1][b_time]
            n_key.value.z = b_curves[2][b_time]
            # track time
            n_times.append(n_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_matcolor_ctrl = self.create_block(
                "NiMaterialColorController", b_ipo)
            n_matcolor_ipol = self.create_block(
                "NiPoint3Interpolator", b_ipo)
            n_matcolor_ctrl.interpolator = n_matcolor_ipol
            n_matcolor_ctrl.flags = 8 # active
            n_matcolor_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_matcolor_ctrl.set_target_color(n_target_color)
            n_matcolor_ctrl.frequency = 1.0
            n_matcolor_ctrl.start_time = min(n_times)
            n_matcolor_ctrl.stop_time = max(n_times)
            n_matcolor_ctrl.data = n_posdata
            n_matcolor_ipol.data = n_posdata
            # attach block to geometry
            n_matprop = self.find_property(n_geom,
                                           NifFormat.NiMaterialProperty)
            if not n_matprop:
                raise ValueError(
                    "bug!! must add material property"
                    " before exporting material color controller")
            n_matprop.add_controller(n_matcolor_ctrl)

    def export_material_uv_controller(self, b_material, n_geom):
        """Export the material UV controller data."""
        # get the material ipo
        b_ipo = b_material.ipo
        if not b_ipo:
            return
        # get the uv curves and translate them into nif data
        n_uvdata = NifFormat.NiUVData()
        n_times = [] # track all times (used later in start time and end time)
        b_channels = (Blender.Ipo.MA_OFSX, Blender.Ipo.MA_OFSY,
                      Blender.Ipo.MA_SIZEX, Blender.Ipo.MA_SIZEY)
        for b_channel, n_uvgroup in zip(b_channels, n_uvdata.uv_groups):
            b_curve = b_ipo[b_channel]
            if b_curve:
                self.logger.info("Exporting %s as NiUVData" % b_curve)
                n_uvgroup.num_keys = len(b_curve.bezierPoints)
                n_uvgroup.interpolation = self.get_n_ipol_from_b_ipol(
                    b_curve.interpolation)
                n_uvgroup.keys.update_size()
                for b_point, n_key in zip(b_curve.bezierPoints, n_uvgroup.keys):
                    # add each point of the curve
                    b_time, b_value = b_point.pt
                    if b_channel in (Blender.Ipo.MA_OFSX, Blender.Ipo.MA_OFSY):
                        # offsets are negated in blender
                        b_value = -b_value
                    n_key.arg = n_uvgroup.interpolation
                    n_key.time = (b_time - 1) * self.fspeed
                    n_key.value = b_value
                    # track time
                    n_times.append(n_key.time)
                # save extend mode to export later
                b_curve_extend = b_curve.extend
        # if uv data is present (we check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_uvctrl = NifFormat.NiUVController()
            n_uvctrl.flags = 8 # active
            n_uvctrl.flags |= self.get_flags_from_extend(b_curve_extend)
            n_uvctrl.frequency = 1.0
            n_uvctrl.start_time = min(n_times)
            n_uvctrl.stop_time = max(n_times)
            n_uvctrl.data = n_uvdata
            # attach block to geometry
            n_geom.add_controller(n_uvctrl)

    def export_object_vis_controller(self, b_object, n_node):
        """Export the material alpha controller data."""
        b_ipo = b_object.ipo
        if not b_ipo:
            return
        # get the alpha curve and translate it into nif data
        b_curve = b_ipo[Blender.Ipo.OB_LAYER]
        if not b_curve:
            return
        # NiVisData = old style, NiBoolData = new style
        n_vis_data = self.create_block("NiVisData", b_curve)
        n_bool_data = self.create_block("NiBoolData", b_curve)
        n_times = [] # track all times (used later in start time and end time)
        # we just leave interpolation at constant
        n_bool_data.data.interpolation = NifFormat.KeyType.CONST_KEY
        #n_bool_data.data.interpolation = self.get_n_ipol_from_b_ipol(
        #    b_curve.interpolation)
        n_vis_data.num_keys = len(b_curve.bezierPoints)
        n_bool_data.data.num_keys = len(b_curve.bezierPoints)
        n_vis_data.keys.update_size()
        n_bool_data.data.keys.update_size()
        visible_layer = 2 ** (min(self.scene.getLayers()) - 1)
        for b_point, n_vis_key, n_bool_key in zip(
            b_curve.bezierPoints, n_vis_data.keys, n_bool_data.data.keys):
            # add each point of the curve
            b_time, b_value = b_point.pt
            n_vis_key.arg = n_bool_data.data.interpolation # n_vis_data has no interpolation stored
            n_vis_key.time = (b_time - 1) * self.fspeed
            n_vis_key.value = 1 if (int(b_value + 0.01) & visible_layer) else 0
            n_bool_key.arg = n_bool_data.data.interpolation
            n_bool_key.time = n_vis_key.time
            n_bool_key.value = n_vis_key.value
            # track time
            n_times.append(n_vis_key.time)
        # if alpha data is present (check this by checking if times were added)
        # then add the controller so it is exported
        if n_times:
            n_vis_ctrl = self.create_block("NiVisController", b_ipo)
            n_vis_ipol = self.create_block("NiBoolInterpolator", b_ipo)
            n_vis_ctrl.interpolator = n_vis_ipol
            n_vis_ctrl.flags = 8 # active
            n_vis_ctrl.flags |= self.get_flags_from_extend(b_curve.extend)
            n_vis_ctrl.frequency = 1.0
            n_vis_ctrl.start_time = min(n_times)
            n_vis_ctrl.stop_time = max(n_times)
            n_vis_ctrl.data = n_vis_data
            n_vis_ipol.data = n_bool_data
            # attach block to node
            n_node.add_controller(n_vis_ctrl)

    def export_bones(self, arm, parent_block):
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
            node = self.create_ninode(bone)
            # doing bone map now makes linkage very easy in second run
            bones_node[bone.name] = node

            # add the node and the keyframe for this bone
            node.name = self.get_full_name(bone.name)
            if self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):
                # default for Oblivion bones
                # note: bodies have 0x000E, clothing has 0x000F
                node.flags = 0x000E
            elif self.EXPORT_VERSION in ('Civilization IV', 'Empire Earth II'):
                if bone.children:
                    # default for Civ IV/EE II bones with children
                    node.flags = 0x0006
                else:
                    # default for Civ IV/EE II final bones
                    node.flags = 0x0016
            elif self.EXPORT_VERSION in ('Divinity 2',):
                if bone.children:
                    # default for Div 2 bones with children
                    node.flags = 0x0186
                elif bone.name.lower()[-9:] == 'footsteps':
                    node.flags = 0x0116
                else:
                    # default for Div 2 final bones
                    node.flags = 0x0196
            else:
                node.flags = 0x0002 # default for Morrowind bones
            self.export_matrix(bone, 'localspace', node) # rest pose
            
            # bone rotations are stored in the IPO relative to the rest position
            # so we must take the rest position into account
            # (need original one, without extra transforms, so extra = False)
            bonerestmat = self.get_bone_rest_matrix(bone, 'BONESPACE',
                                                    extra = False)
            try:
                bonexmat_inv = Blender.Mathutils.Matrix(
                    self.get_bone_extra_matrix_inv(bone.name))
            except KeyError:
                bonexmat_inv = Blender.Mathutils.Matrix()
                bonexmat_inv.identity()
            if bones_ipo.has_key(bone.name):
                self.export_keyframes(
                    bones_ipo[bone.name], 'localspace', node,
                    bind_mat = bonerestmat, extra_mat_inv = bonexmat_inv)

            # does bone have priority value in NULL constraint?
            for constr in arm.getPose().bones[bone.name].constraints:
                # yes! store it for reference when creating the kf file
                if constr.name[:9].lower() == "priority:":
                    self.bone_priorities[
                        self.get_bone_name_for_nif(bone.name)
                        ] = int(constr.name[9:])

        # now fix the linkage between the blocks
        for bone in bones.values():
            # link the bone's children to the bone
            if bone.children:
                self.logger.debug("Linking children of bone %s" % bone.name)
                for child in bone.children:
                    # bone.children returns also grandchildren etc.
                    # we only want immediate children, so do a parent check
                    if child.parent.name == bone.name:
                        bones_node[bone.name].add_child(bones_node[child.name])
            # if it is a root bone, link it to the armature
            if not bone.parent:
                parent_block.add_child(bones_node[bone.name])



    def export_children(self, obj, parent_block):
        """Export all children of blender object ob as children of
        parent_block."""
        # loop over all obj's children
        for ob_child in self.get_b_children(obj):
            # is it a regular node?
            if ob_child.getType() in ['Mesh', 'Empty', 'Armature']:
                if (obj.getType() != 'Armature'):
                    # not parented to an armature
                    self.export_node(ob_child, 'localspace',
                                     parent_block, ob_child.getName())
                else:
                    # this object is parented to an armature
                    # we should check whether it is really parented to the
                    # armature using vertex weights
                    # or whether it is parented to some bone of the armature
                    parent_bone_name = ob_child.getParentBoneName()
                    if parent_bone_name is None:
                        self.export_node(ob_child, 'localspace',
                                         parent_block, ob_child.getName())
                    else:
                        # we should parent the object to the bone instead of
                        # to the armature
                        # so let's find that bone!
                        nif_bone_name = self.get_full_name(parent_bone_name)
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
                                # this is handled in the get_object_srt function
                                self.export_node(ob_child, 'localspace',
                                                 bone_block, ob_child.getName())
                                break
                        else:
                            assert(False) # BUG!



    def export_matrix(self, obj, space, block):
        """Set a block's transform matrix to an object's
        transformation matrix in rest pose."""
        # decompose
        bscale, brot, btrans = self.get_object_srt(obj, space)
        
        # and fill in the values
        block.translation.x = btrans[0]
        block.translation.y = btrans[1]
        block.translation.z = btrans[2]
        block.rotation.m_11 = brot[0][0]
        block.rotation.m_12 = brot[0][1]
        block.rotation.m_13 = brot[0][2]
        block.rotation.m_21 = brot[1][0]
        block.rotation.m_22 = brot[1][1]
        block.rotation.m_23 = brot[1][2]
        block.rotation.m_31 = brot[2][0]
        block.rotation.m_32 = brot[2][1]
        block.rotation.m_33 = brot[2][2]
        block.velocity.x = 0.0
        block.velocity.y = 0.0
        block.velocity.z = 0.0
        block.scale = bscale

        return bscale, brot, btrans

    def get_object_matrix(self, obj, space):
        """Get an object's matrix as NifFormat.Matrix44

        Note: for objects parented to bones, this will return the transform
        relative to the bone parent head in nif coordinates (that is, including
        the bone correction); this differs from getMatrix which
        returns the transform relative to the armature."""
        bscale, brot, btrans = self.get_object_srt(obj, space)
        mat = NifFormat.Matrix44()
        
        mat.m_41 = btrans[0]
        mat.m_42 = btrans[1]
        mat.m_43 = btrans[2]

        mat.m_11 = brot[0][0] * bscale
        mat.m_12 = brot[0][1] * bscale
        mat.m_13 = brot[0][2] * bscale
        mat.m_21 = brot[1][0] * bscale
        mat.m_22 = brot[1][1] * bscale
        mat.m_23 = brot[1][2] * bscale
        mat.m_31 = brot[2][0] * bscale
        mat.m_32 = brot[2][1] * bscale
        mat.m_33 = brot[2][2] * bscale

        mat.m_14 = 0.0
        mat.m_24 = 0.0
        mat.m_34 = 0.0
        mat.m_44 = 1.0
        
        return mat

    def get_object_srt(self, obj, space = 'localspace'):
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
                        self.get_bone_extra_matrix_inv(bone_parent_name))
                    extra.invert()
                    mat = mat * extra
                except KeyError:
                    # no extra local transform
                    pass
        else:
            # bones, get the rest matrix
            mat = self.get_bone_rest_matrix(obj, 'BONESPACE')
        
        try:
            return self.decompose_srt(mat)
        except NifExportError: # non-uniform scaling
            self.logger.debug(str(mat))
            raise NifExportError(
                "Non-uniform scaling on bone '%s' not supported."
                " This could be a bug... No workaround. :-( Post your blend!"
                % obj.name)



    def decompose_srt(self, mat):
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
            raise NifExportError(
                "Non-uniform scaling not supported."
                " Workaround: apply size and rotation (CTRL-A).")
        b_scale = b_scale[0]
        # get rotation matrix
        b_rot = b_scale_rot * (1.0 / b_scale)
        # get translation
        b_trans = mat.translationPart()
        # done!
        return b_scale, b_rot, b_trans



    def get_bone_rest_matrix(self, bone, space, extra = True, tail = False):
        """Get bone matrix in rest position ("bind pose"). Space can be
        ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
        is BONESPACE (translation is bone head plus tail from parent bone).
        If tail is True then the matrix translation includes the bone tail."""
        # Retrieves the offset from the original NIF matrix, if existing
        corrmat = Blender.Mathutils.Matrix()
        if extra:
            try:
                corrmat = Blender.Mathutils.Matrix(
                    self.get_bone_extra_matrix_inv(bone.name))
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
                parinv = self.get_bone_rest_matrix(bone.parent, 'ARMATURESPACE',
                                                   extra = True, tail = False)
                parinv.invert()
                return self.get_bone_rest_matrix(bone,
                                                 'ARMATURESPACE',
                                                 extra = extra,
                                                 tail = tail) * parinv
            else:
                return self.get_bone_rest_matrix(bone, 'ARMATURESPACE',
                                                 extra = extra, tail = tail)
        else:
            assert(False) # bug!



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
            raise NifExportError(
                "'%s': Unknown block type (this is probably a bug)."
                % blocktype)
        return self.register_block(block, b_obj)


    def register_block(self, block, b_obj = None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            self.logger.info("Exporting %s block"%block.__class__.__name__)
        else:
            self.logger.info("Exporting %s as %s block"
                     % (b_obj, block.__class__.__name__))
        self.blocks[block] = b_obj
        return block

    def export_collision(self, obj, parent_block):
        """Main function for adding collision object obj to a node.""" 
        if self.EXPORT_VERSION == 'Morrowind':
             if obj.rbShapeBoundType != Blender.Object.RBShapes['POLYHEDERON']:
                 raise NifExportError(
                     "Morrowind only supports Polyhedron/Static"
                     " TriangleMesh collisions.")
             node = self.create_block("RootCollisionNode", obj)
             parent_block.add_child(node)
             node.flags = 0x0003 # default
             self.export_matrix(obj, 'localspace', node)
             self.export_tri_shapes(obj, 'none', node)

        elif self.EXPORT_VERSION in ('Oblivion', 'Fallout 3'):

            nodes = [ parent_block ]
            nodes.extend([ block for block in parent_block.children
                           if block.name[:14] == 'collisiondummy' ])
            for node in nodes:
                try:
                    self.export_collision_helper(obj, node)
                    break
                except ValueError: # adding collision failed
                    continue
            else: # all nodes failed so add new one
                node = self.create_ninode(obj)
                node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy%i' % parent_block.num_children
                node.flags = 0x000E # default
                parent_block.add_child(node)
                self.export_collision_helper(obj, node)

        else:
            self.logger.warning(
                "Only Morrowind, Oblivion, and Fallout 3"
                " collisions are supported, skipped collision object '%s'"
                % obj.name)

    def export_collision_helper(self, obj, parent_block):
        """Helper function to add collision objects to a node. This function
        exports the rigid body, and calls the appropriate function to export
        the collision geometry in the desired format.

        @param obj: The object to export as collision.
        @param parent_block: The NiNode parent of the collision.
        """

        # is it packed
        coll_ispacked = (obj.rbShapeBoundType
                         == Blender.Object.RBShapes['POLYHEDERON'])

        # find physics properties/defaults
        material = self.EXPORT_OB_MATERIAL
        layer = self.EXPORT_OB_LAYER
        motion_system = self.EXPORT_OB_MOTIONSYSTEM
        quality_type = self.EXPORT_OB_QUALITYTYPE
        mass = 1.0 # will be fixed later
        col_filter = 0
        # copy physics properties from Blender properties, if they exist,
        # unless forcing override
        if not self.EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES:
            for prop in obj.getAllProperties():
                if prop.getName() == 'HavokMaterial':
                    if prop.getType() == "STRING":
                        # for Anglicized names
                        if prop.getData() in self.HAVOK_MATERIAL:
                            material = self.HAVOK_MATERIAL.index(prop.getData())
                        # for the real Nif Format material names
                        else:
                            material = getattr(NifFormat.HavokMaterial, prop.getData())
                    # or if someone wants to set the material by the number
                    elif prop.getType() == "INT":
                        material = prop.getData()
                elif prop.getName() == 'OblivionLayer':
                    if prop.getType() == "STRING":
                        # for Anglicized names
                        if prop.getData() in self.OB_LAYER:
                            layer = self.OB_LAYER.index(prop.getData())
                        # for the real Nif Format layer names
                        else:
                            layer = getattr(NifFormat.OblivionLayer, prop.getData())
                    # or if someone wants to set the layer by the number
                    elif prop.getType() == "INT":
                        layer = prop.getData()
                elif prop.getName() == 'QualityType':
                    if prop.getType() == "STRING":
                        # for Anglicized names
                        if prop.getData() in self.QUALITY_TYPE:
                            quality_type = self.QUALITY_TYPE.index(prop.getData())
                        # for the real Nif Format MoQual names
                        else:
                            quality_type = getattr(NifFormat.MotionQuality, prop.getData())
                    # or if someone wants to set the Motion Quality by the number
                    elif prop.getType() == "INT":
                        quality_type = prop.getData()
                elif prop.getName() == 'MotionSystem':
                    if prop.getType() == "STRING":
                        # for Anglicized names
                        if prop.getData() in self.MOTION_SYS:
                            motion_system = self.MOTION_SYS.index(prop.getData())
                        # for the real Nif Format Motion System names
                        else:
                            motion_system = getattr(NifFormat.MotionSystem, prop.getData())
                    # or if someone wants to set the Motion System  by the number
                    elif prop.getType() == "INT":
                        motion_system = prop.getData()
                elif prop.getName() == 'Mass' and prop.getType() == "FLOAT":
                    mass = prop.getData()
                elif prop.getName() == 'ColFilter' and prop.getType() == "INT":
                    col_filter = prop.getData()

        # if no collisions have been exported yet to this parent_block
        # then create new collision tree on parent_block
        # bhkCollisionObject -> bhkRigidBody
        if not parent_block.collision_object:
            # note: collision settings are taken from lowerclasschair01.nif
            if self.EXPORT_OB_LAYER == NifFormat.OblivionLayer.OL_BIPED:
                # special collision object for creatures
                colobj = self.create_block("bhkBlendCollisionObject", obj)
                colobj.flags = 9
                colobj.unknown_float_1 = 1.0
                colobj.unknown_float_2 = 1.0
                # also add a controller for it
                blendctrl = self.create_block("bhkBlendController", obj)
                blendctrl.flags = 12
                blendctrl.frequency = 1.0
                blendctrl.phase = 0.0
                blendctrl.start_time = self.FLOAT_MAX
                blendctrl.stop_time = self.FLOAT_MIN
                parent_block.add_controller(blendctrl)
            else:
                # usual collision object
                colobj = self.create_block("bhkCollisionObject", obj)
                if layer == NifFormat.OblivionLayer.OL_ANIM_STATIC and col_filter != 128:
                    # animated collision requires flags = 41
                    # unless it is a constrainted but not keyframed object
                    colobj.flags = 41
                else:
                    # in all other cases this seems to be enough
                    colobj.flags = 1
            parent_block.collision_object = colobj
            colobj.target = parent_block
            colbody = self.create_block("bhkRigidBody", obj)
            colobj.body = colbody
            colbody.layer = layer
            colbody.col_filter = col_filter
            colbody.unknown_5_floats[1] = 3.8139e+36
            colbody.unknown_4_shorts[0] = 1
            colbody.unknown_4_shorts[1] = 65535
            colbody.unknown_4_shorts[2] = 35899
            colbody.unknown_4_shorts[3] = 16336
            colbody.layer_copy = layer
            colbody.unknown_7_shorts[1] = 21280
            colbody.unknown_7_shorts[2] = 4581
            colbody.unknown_7_shorts[3] = 62977
            colbody.unknown_7_shorts[4] = 65535
            colbody.unknown_7_shorts[5] = 44
            # mass is 1.0 at the moment (unless property was set)
            # will be fixed later
            colbody.mass = mass
            colbody.linear_damping = 0.1
            colbody.angular_damping = 0.05
            colbody.friction = 0.3
            colbody.restitution = 0.3
            colbody.max_linear_velocity = 250.0
            colbody.max_angular_velocity = 31.4159
            colbody.penetration_depth = 0.15
            colbody.motion_system = motion_system
            colbody.unknown_byte_1 = self.EXPORT_OB_UNKNOWNBYTE1
            colbody.unknown_byte_2 = self.EXPORT_OB_UNKNOWNBYTE2
            colbody.quality_type = quality_type
            colbody.unknown_int_9 = self.EXPORT_OB_WIND
        else:
            colbody = parent_block.collision_object.body
            # fix total mass
            colbody.mass += mass

        if coll_ispacked:
            self.export_collision_packed(obj, colbody, layer, material)
        else:
            if self.EXPORT_BHKLISTSHAPE:
                self.export_collision_list(obj, colbody, layer, material)
            else:
                self.export_collision_single(obj, colbody, layer, material)

    def export_collision_packed(self, obj, colbody, layer, material):
        """Add object ob as packed collision object to collision body
        colbody. If parent_block hasn't any collisions yet, a new
        packed list is created. If the current collision system is not
        a packed list of collisions (bhkPackedNiTriStripsShape), then
        a ValueError is raised.
        """

        if not colbody.shape:
            colshape = self.create_block("bhkPackedNiTriStripsShape", obj)

            colmopp = self.create_block("bhkMoppBvTreeShape", obj)
            colbody.shape = colmopp
            colmopp.material = material
            colmopp.unknown_8_bytes[0] = 160
            colmopp.unknown_8_bytes[1] = 13
            colmopp.unknown_8_bytes[2] = 75
            colmopp.unknown_8_bytes[3] = 1
            colmopp.unknown_8_bytes[4] = 192
            colmopp.unknown_8_bytes[5] = 207
            colmopp.unknown_8_bytes[6] = 144
            colmopp.unknown_8_bytes[7] = 11
            colmopp.unknown_float = 1.0
            # the mopp origin, scale, and data are written later
            colmopp.shape = colshape

            colshape.unknown_floats[2] = 0.1
            colshape.unknown_floats[4] = 1.0
            colshape.unknown_floats[5] = 1.0
            colshape.unknown_floats[6] = 1.0
            colshape.unknown_floats[8] = 0.1
            colshape.scale = 1.0
            colshape.unknown_floats_2[0] = 1.0
            colshape.unknown_floats_2[1] = 1.0
        else:
            # XXX at the moment, we disable multimaterial mopps
            # XXX do this by raising an exception when trying
            # XXX to add a collision here; code will try to readd it with
            # XXX a fresh NiNode
            raise ValueError('multimaterial mopps not supported for now')
            # XXX this code will do the trick once multimaterial mopps work
            colmopp = colbody.shape
            if not isinstance(colmopp, NifFormat.bhkMoppBvTreeShape):
                raise ValueError('not a packed list of collisions')
            colshape = colmopp.shape
            if not isinstance(colshape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError('not a packed list of collisions')

        mesh = obj.data
        transform = Blender.Mathutils.Matrix(
            *self.get_object_matrix(obj, 'localspace').as_list())
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

        colshape.add_shape(triangles, normals, vertices, layer, material)



    def export_collision_single(self, obj, colbody, layer, material):
        """Add collision object to colbody.
        If colbody already has a collision shape, throw ValueError."""
        if colbody.shape:
            raise ValueError('collision body already has a shape')
        colbody.shape = self.export_collision_object(obj, layer, material)



    def export_collision_list(self, obj, colbody, layer, material):
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
            colshape = self.create_block("bhkListShape")
            colbody.shape = colshape
            colshape.material = material
        else:
            colshape = colbody.shape
            if not isinstance(colshape, NifFormat.bhkListShape):
                raise ValueError('not a list of collisions')

        colshape.add_shape(self.export_collision_object(obj, layer, material))



    def export_collision_object(self, obj, layer, material):
        """Export object obj as box, sphere, capsule, or convex hull.
        Note: polyheder is handled by export_collision_packed."""

        # find bounding box data
        if not obj.data.verts:
            self.logger.warn(
                "Skipping collision object %s without vertices." % obj)
            return None
        minx = min([vert[0] for vert in obj.data.verts])
        miny = min([vert[1] for vert in obj.data.verts])
        minz = min([vert[2] for vert in obj.data.verts])
        maxx = max([vert[0] for vert in obj.data.verts])
        maxy = max([vert[1] for vert in obj.data.verts])
        maxz = max([vert[2] for vert in obj.data.verts])

        if obj.rbShapeBoundType in (Blender.Object.RBShapes['BOX'],
                                    Blender.Object.RBShapes['SPHERE']):
            # note: collision settings are taken from lowerclasschair01.nif
            coltf = self.create_block("bhkConvexTransformShape", obj)
            coltf.material = material
            coltf.unknown_float_1 = 0.1
            coltf.unknown_8_bytes[0] = 96
            coltf.unknown_8_bytes[1] = 120
            coltf.unknown_8_bytes[2] = 53
            coltf.unknown_8_bytes[3] = 19
            coltf.unknown_8_bytes[4] = 24
            coltf.unknown_8_bytes[5] = 9
            coltf.unknown_8_bytes[6] = 253
            coltf.unknown_8_bytes[7] = 4
            hktf = Blender.Mathutils.Matrix(
                *self.get_object_matrix(obj, 'localspace').as_list())
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
            coltf.transform.set_rows(*hktf)
            # fix matrix for havok coordinate system
            coltf.transform.m_14 /= 7.0
            coltf.transform.m_24 /= 7.0
            coltf.transform.m_34 /= 7.0

            if obj.rbShapeBoundType == Blender.Object.RBShapes['BOX']:
                colbox = self.create_block("bhkBoxShape", obj)
                coltf.shape = colbox
                colbox.material = material
                colbox.radius = 0.1
                colbox.unknown_8_bytes[0] = 0x6b
                colbox.unknown_8_bytes[1] = 0xee
                colbox.unknown_8_bytes[2] = 0x43
                colbox.unknown_8_bytes[3] = 0x40
                colbox.unknown_8_bytes[4] = 0x3a
                colbox.unknown_8_bytes[5] = 0xef
                colbox.unknown_8_bytes[6] = 0x8e
                colbox.unknown_8_bytes[7] = 0x3e
                # fix dimensions for havok coordinate system
                colbox.dimensions.x = (maxx - minx) / 14.0
                colbox.dimensions.y = (maxy - miny) / 14.0
                colbox.dimensions.z = (maxz - minz) / 14.0
                colbox.minimum_size = min(colbox.dimensions.x, colbox.dimensions.y, colbox.dimensions.z)
            elif obj.rbShapeBoundType == Blender.Object.RBShapes['SPHERE']:
                colsphere = self.create_block("bhkSphereShape", obj)
                coltf.shape = colsphere
                colsphere.material = material
                # take average radius and
                # fix for havok coordinate system (6 * 7 = 42)
                colsphere.radius = (maxx + maxy + maxz - minx - miny -minz) / 42.0

            return coltf

        elif obj.rbShapeBoundType == Blender.Object.RBShapes['CYLINDER']:
            # take average radius and calculate end points
            localradius = (maxx + maxy - minx - miny) / 4.0
            transform = Blender.Mathutils.Matrix(
                *self.get_object_matrix(obj, 'localspace').as_list())
            vert1 = Blender.Mathutils.Vector( [ (maxx + minx)/2.0,
                                                (maxy + miny)/2.0,
                                                minz + localradius ] )
            vert2 = Blender.Mathutils.Vector( [ (maxx + minx) / 2.0,
                                                (maxy + miny) / 2.0,
                                                maxz - localradius ] )
            vert1 *= transform
            vert2 *= transform
            # check if end points are far enough from each other
            if (vert1 - vert2).length < self.EPSILON:
                self.logger.warn(
                    "End points of cylinder %s too close,"
                    " converting to sphere." % obj)
                # change type
                obj.rbShapeBoundType = Blender.Object.RBShapes['SPHERE']
                # instead of duplicating code, just run the function again
                return self.export_collision_object(obj, layer, material)
            # end points are ok, so export as capsule
            colcaps = self.create_block("bhkCapsuleShape", obj)
            colcaps.material = material
            colcaps.first_point.x = vert1[0] / 7.0
            colcaps.first_point.y = vert1[1] / 7.0
            colcaps.first_point.z = vert1[2] / 7.0
            colcaps.second_point.x = vert2[0] / 7.0
            colcaps.second_point.y = vert2[1] / 7.0
            colcaps.second_point.z = vert2[2] / 7.0
            # set radius, with correct scale
            sizex, sizey, sizez = obj.getSize()
            colcaps.radius = localradius * (sizex + sizey) * 0.5
            colcaps.radius_1 = colcaps.radius
            colcaps.radius_2 = colcaps.radius
            # fix havok coordinate system for radii
            colcaps.radius /= 7.0
            colcaps.radius_1 /= 7.0
            colcaps.radius_2 /= 7.0
            return colcaps

        elif obj.rbShapeBoundType == 5:
            # convex hull polytope; not in Python API
            # bound type has value 5
            mesh = obj.data
            transform = Blender.Mathutils.Matrix(
                *self.get_object_matrix(obj, 'localspace').as_list())
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
                vertdict[(int(vert[0]*self.VERTEX_RESOLUTION),
                          int(vert[1]*self.VERTEX_RESOLUTION),
                          int(vert[2]*self.VERTEX_RESOLUTION))] = i
            fdict = {}
            for i, (norm, dist) in enumerate(zip(fnormlist, fdistlist)):
                fdict[(int(norm[0]*self.NORMAL_RESOLUTION),
                       int(norm[1]*self.NORMAL_RESOLUTION),
                       int(norm[2]*self.NORMAL_RESOLUTION),
                       int(dist*self.VERTEX_RESOLUTION))] = i
            # sort vertices and normals
            vertkeys = sorted(vertdict.keys())
            fkeys = sorted(fdict.keys())
            vertlist = [ vertlist[vertdict[hsh]] for hsh in vertkeys ]
            fnormlist = [ fnormlist[fdict[hsh]] for hsh in fkeys ]
            fdistlist = [ fdistlist[fdict[hsh]] for hsh in fkeys ]

            if len(fnormlist) > 65535 or len(vertlist) > 65535:
                raise NifExportError(
                    "ERROR%t|Too many faces/vertices."
                    " Decimate/split your mesh and try again.")
            
            colhull = self.create_block("bhkConvexVerticesShape", obj)
            colhull.material = material
            colhull.radius = 0.1
            colhull.unknown_6_floats[2] = -0.0 # enables arrow detection
            colhull.unknown_6_floats[5] = -0.0 # enables arrow detection
            # note: unknown 6 floats are usually all 0
            colhull.num_vertices = len(vertlist)
            colhull.vertices.update_size()
            for vhull, vert in zip(colhull.vertices, vertlist):
                vhull.x = vert[0] / 7.0
                vhull.y = vert[1] / 7.0
                vhull.z = vert[2] / 7.0
                # w component is 0
            colhull.num_normals = len(fnormlist)
            colhull.normals.update_size()
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

    def export_constraints(self, b_obj, root_block):
        """Export the constraints of an object.

        @param b_obj: The object whose constraints to export.
        @param root_block: The root of the nif tree (required for update_a_b)."""
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
                    self.logger.warning(
                        "Only Oblivion/Fallout 3 rigid body constraints"
                        " can be exported: skipped %s." % b_constr)
                    continue
                # check that the object is a rigid body
                for otherbody, otherobj in self.blocks.iteritems():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) \
                        and otherobj is b_obj:
                        hkbody = otherbody
                        break
                else:
                    # no collision body for this object
                    raise NifExportError(
                        "Object %s has a rigid body constraint,"
                        " but is not exported as collision object"
                        % b_obj.name)
                # yes there is a rigid body constraint
                # is it of a type that is supported?
                if b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 1:
                    # ball
                    if not self.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.create_block(
                            "bhkRagdollConstraint", b_constr)
                    else:
                        hkconstraint = self.create_block(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 7
                    hkdescriptor = hkconstraint.ragdoll
                elif b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 2:
                    # hinge
                    if not self.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.create_block(
                            "bhkLimitedHingeConstraint", b_constr)
                    else:
                        hkconstraint = self.create_block(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 2
                    hkdescriptor = hkconstraint.limited_hinge
                else:
                    raise NifExportError(
                        "Unsupported rigid body joint type (%i),"
                        " only ball and hinge are supported."
                        % b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE])

                # defaults and getting object properties for user
                # settings (should use constraint properties, but
                # blender does not have those...)
                max_angle = 1.5
                min_angle = 0.0
                # friction: again, just picking a reasonable value if
                # no real value given
                if isinstance(hkconstraint,
                              NifFormat.bhkMalleableConstraint):
                    # malleable typically have 0
                    # (perhaps because they have a damping parameter)
                    max_friction = 0
                else:
                    # non-malleable typically have 10
                    if self.EXPORT_VERSION == "Fallout 3":
                        max_friction = 100
                    else: # oblivion
                        max_friction = 10
                for prop in b_obj.getAllProperties():
                    if (prop.getName() == 'LimitedHinge_MaxAngle'
                        and prop.getType() == "FLOAT"):
                        max_angle = prop.getData()
                    if (prop.getName() == 'LimitedHinge_MinAngle'
                        and prop.getType() == "FLOAT"):
                        min_angle = prop.getData()
                    if (prop.getName() == 'LimitedHinge_MaxFriction'
                        and prop.getType() == "FLOAT"):
                        max_friction = prop.getData() 

                # parent constraint to hkbody
                hkbody.num_constraints += 1
                hkbody.constraints.update_size()
                hkbody.constraints[-1] = hkconstraint

                # export hkconstraint settings
                hkconstraint.num_entities = 2
                hkconstraint.entities.update_size()
                hkconstraint.entities[0] = hkbody
                # is there a target?
                targetobj = b_constr[Blender.Constraint.Settings.TARGET]
                if not targetobj:
                    self.logger.warning("Constraint %s has no target, skipped")
                    continue
                # find target's bhkRigidBody
                for otherbody, otherobj in self.blocks.iteritems():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) \
                        and otherobj == targetobj:
                        hkconstraint.entities[1] = otherbody
                        break
                else:
                    # not found
                    raise NifExportError(
                        "Rigid body target not exported in nif tree"
                        " check that %s is selected during export." % targetobj)
                # priority
                hkconstraint.priority = 1
                # extra malleable constraint settings
                if isinstance(hkconstraint, NifFormat.bhkMalleableConstraint):
                    # unknowns
                    hkconstraint.unknown_int_2 = 2
                    hkconstraint.unknown_int_3 = 1
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
                # coordinates (also see import_nif.py, the
                # NifImport.import_bhk_constraints method)
                
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
                    *self.get_object_matrix(b_obj, 'localspace').as_list())
                pivot = pivot * transform
                constr_matrix = constr_matrix * transform.rotationPart()

                # export hkdescriptor pivot point
                hkdescriptor.pivot_a.x = pivot[0] / 7.0
                hkdescriptor.pivot_a.y = pivot[1] / 7.0
                hkdescriptor.pivot_a.z = pivot[2] / 7.0
                # export hkdescriptor axes and other parameters
                # (also see import_nif.py NifImport.import_bhk_constraints)
                axis_x = Blender.Mathutils.Vector(1,0,0) * constr_matrix
                axis_y = Blender.Mathutils.Vector(0,1,0) * constr_matrix
                axis_z = Blender.Mathutils.Vector(0,0,1) * constr_matrix
                if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                    # z axis is the twist vector
                    hkdescriptor.twist_a.x = axis_z[0]
                    hkdescriptor.twist_a.y = axis_z[1]
                    hkdescriptor.twist_a.z = axis_z[2]
                    # x axis is the plane vector
                    hkdescriptor.plane_a.x = axis_x[0]
                    hkdescriptor.plane_a.y = axis_x[1]
                    hkdescriptor.plane_a.z = axis_x[2]
                    # angle limits
                    # take them twist and plane to be 45 deg (3.14 / 4 = 0.8)
                    hkdescriptor.twist_min_angle = -0.8
                    hkdescriptor.twist_max_angle = +0.8
                    hkdescriptor.plane_min_angle = -0.8
                    hkdescriptor.plane_max_angle = +0.8
                    # same for maximum cone angle
                    hkdescriptor.cone_max_angle  = +0.8
                elif isinstance(hkdescriptor, NifFormat.LimitedHingeDescriptor):
                    # y axis is the zero angle vector on the plane of rotation
                    hkdescriptor.perp_2_axle_in_a_1.x = axis_y[0]
                    hkdescriptor.perp_2_axle_in_a_1.y = axis_y[1]
                    hkdescriptor.perp_2_axle_in_a_1.z = axis_y[2]
                    # x axis is the axis of rotation
                    hkdescriptor.axle_a.x = axis_x[0]
                    hkdescriptor.axle_a.y = axis_x[1]
                    hkdescriptor.axle_a.z = axis_x[2]
                    # z is the remaining axis determining the positive
                    # direction of rotation
                    hkdescriptor.perp_2_axle_in_a_2.x = axis_z[0]
                    hkdescriptor.perp_2_axle_in_a_2.y = axis_z[1]
                    hkdescriptor.perp_2_axle_in_a_2.z = axis_z[2]
                    # angle limits
                    # typically, the constraint on one side is defined
                    # by the z axis
                    hkdescriptor.min_angle = min_angle
                    # the maximum axis is typically about 90 degrees
                    # 3.14 / 2 = 1.5
                    hkdescriptor.max_angle = max_angle
                    # friction
                    hkdescriptor.max_friction = max_friction
                else:
                    raise ValueError("unknown descriptor %s"
                                     % hkdescriptor.__class__.__name__)

                # do AB
                hkconstraint.update_a_b(root_block)


    def export_alpha_property(self, flags=0x00ED, threshold=0):
        """Return existing alpha property with given flags, or create new one
        if an alpha property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiAlphaProperty) \
               and block.flags == flags and block.threshold == threshold:
                return block
        # no alpha property with given flag found, so create new one
        alphaprop = self.create_block("NiAlphaProperty")
        alphaprop.flags = flags
        alphaprop.threshold = threshold
        return alphaprop

    def export_specular_property(self, flags = 0x0001):
        """Return existing specular property with given flags, or create new one
        if a specular property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiSpecularProperty) \
               and block.flags == flags:
                return block
        # no specular property with given flag found, so create new one
        specprop = self.create_block("NiSpecularProperty")
        specprop.flags = flags
        return specprop        

    def export_wireframe_property(self, flags = 0x0001):
        """Return existing wire property with given flags, or create new one
        if an wire property with required flags is not found."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiWireframeProperty) \
               and block.flags == flags:
                return block
        # no alpha property with given flag found, so create new one
        wireprop = self.create_block("NiWireframeProperty")
        wireprop.flags = flags
        return wireprop        

    def export_stencil_property(self):
        """Return existing stencil property with given flags, or create new one
        if an identical stencil property."""
        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiStencilProperty):
                # all these blocks have the same setting, no further check
                # is needed
                return block
        # no stencil property found, so create new one
        stencilprop = self.create_block("NiStencilProperty")
        if self.EXPORT_VERSION == "Fallout 3":
            stencilprop.flags = 19840
        return stencilprop        

    def export_material_property(
        self, name='', flags=0x0001,
        ambient=(1.0, 1.0, 1.0),
        diffuse=(1.0, 1.0, 1.0),
        specular=(0.0, 0.0, 0.0),
        emissive=(0.0, 0.0, 0.0),
        glossiness=10.0,
        alpha=1.0,
        emitmulti=1.0):
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
                        self.logger.warning("Renaming material '%s' to '%s'"
                                            % (name, specialname))
                    name = specialname

        # clear noname materials
        if name.lower().startswith("noname"):
            self.logger.warning("Renaming material '%s' to ''" % name)
            name = ""

        matprop.name = name
        matprop.flags = flags
        matprop.ambient_color.r = ambient[0]
        matprop.ambient_color.g = ambient[1]
        matprop.ambient_color.b = ambient[2]
        matprop.diffuse_color.r = diffuse[0]
        matprop.diffuse_color.g = diffuse[1]
        matprop.diffuse_color.b = diffuse[2]
        matprop.specular_color.r = specular[0]
        matprop.specular_color.g = specular[1]
        matprop.specular_color.b = specular[2]
        matprop.emissive_color.r = emissive[0]
        matprop.emissive_color.g = emissive[1]
        matprop.emissive_color.b = emissive[2]
        matprop.glossiness = glossiness
        matprop.alpha = alpha
        matprop.emit_multi = emitmulti

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
            first_index = 1 if ignore_strings else 0
            if (block.get_hash()[first_index:] ==
                matprop.get_hash()[first_index:]):
                self.logger.warning(
                    "Merging materials '%s' and '%s'"
                    " (they are identical in nif)"
                    % (matprop.name, block.name))
                return block

        # no material property with given settings found, so use and register
        # the new one
        return self.register_block(matprop)

    def export_tex_desc(self, texdesc=None, uvlayers=None, mtex=None):
        """Helper function for export_texturing_property to export each texture
        slot."""
        try:
            texdesc.uv_set = uvlayers.index(mtex.uvlayer) if mtex.uvlayer else 0
        except ValueError: # mtex.uvlayer not in uvlayers list
            self.logger.warning(
                "Bad uv layer name '%s' in texture '%s'."
                " Falling back on first uv layer"
                % (mtex.uvlayer, mtex.tex.getName()))
            texdesc.uv_set = 0 # assume 0 is active layer

        texdesc.source = self.export_source_texture(mtex.tex)

    def export_texturing_property(
        self, flags=0x0001, applymode=None, uvlayers=None,
        basemtex=None, glowmtex=None, bumpmtex=None, glossmtex=None,
        darkmtex=None, detailmtex=None, refmtex=None):
        """Export texturing property. The parameters basemtex,
        glowmtex, bumpmtex, ... are the Blender material textures
        (MTex, not Texture) that correspond to the base, glow, bump
        map, ... textures. The uvlayers parameter is a list of uvlayer
        strings, that is, mesh.getUVLayers().
        """

        texprop = NifFormat.NiTexturingProperty()

        texprop.flags = flags
        texprop.apply_mode = applymode
        texprop.texture_count = 7

        if self.EXPORT_EXTRA_SHADER_TEXTURES:
            if self.EXPORT_VERSION == "Sid Meier's Railroads":
                # sid meier's railroads:
                # some textures end up in the shader texture list
                # there are 5 slots available, so set them up
                texprop.num_shader_textures = 5
                texprop.shader_textures.update_size()
                for mapindex, shadertexdesc in enumerate(texprop.shader_textures):
                    # set default values
                    shadertexdesc.is_used = False
                    shadertexdesc.map_index = mapindex

                # some texture slots required by the engine
                shadertexdesc_envmap = texprop.shader_textures[0]
                shadertexdesc_envmap.is_used = True
                shadertexdesc_envmap.texture_data.source = \
                    self.export_source_texture(filename="RRT_Engine_Env_map.dds")

                shadertexdesc_cubelightmap = texprop.shader_textures[4]
                shadertexdesc_cubelightmap.is_used = True
                shadertexdesc_cubelightmap.texture_data.source = \
                    self.export_source_texture(filename="RRT_Cube_Light_map_128.dds")

                # the other slots are exported below

            elif self.EXPORT_VERSION == "Civilization IV":
                # some textures end up in the shader texture list
                # there are 4 slots available, so set them up
                texprop.num_shader_textures = 4
                texprop.shader_textures.update_size()
                for mapindex, shadertexdesc in enumerate(texprop.shader_textures):
                    # set default values
                    shadertexdesc.is_used = False
                    shadertexdesc.map_index = mapindex

        if basemtex:
            texprop.has_base_texture = True
            self.export_tex_desc(texdesc = texprop.base_texture,
                                 uvlayers = uvlayers,
                                 mtex = basemtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.tex.getName())
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.export_flip_controller(fliptxt, basemtex.tex, texprop, 0)

        if glowmtex:
            texprop.has_glow_texture = True
            self.export_tex_desc(texdesc = texprop.glow_texture,
                                 uvlayers = uvlayers,
                                 mtex = glowmtex)

        if bumpmtex:
            if self.EXPORT_VERSION not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_bump_map_texture = True
                self.export_tex_desc(texdesc = texprop.bump_map_texture,
                                     uvlayers = uvlayers,
                                     mtex = bumpmtex)
                texprop.bump_map_luma_scale = 1.0
                texprop.bump_map_luma_offset = 0.0
                texprop.bump_map_matrix.m_11 = 1.0
                texprop.bump_map_matrix.m_12 = 0.0
                texprop.bump_map_matrix.m_21 = 0.0
                texprop.bump_map_matrix.m_22 = 1.0
            elif self.EXPORT_EXTRA_SHADER_TEXTURES:
                shadertexdesc = texprop.shader_textures[1]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=bumpmtex.tex)

        if glossmtex:
            if self.EXPORT_VERSION not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_gloss_texture = True
                self.export_tex_desc(texdesc = texprop.gloss_texture,
                                     uvlayers = uvlayers,
                                     mtex = glossmtex)
            elif self.EXPORT_EXTRA_SHADER_TEXTURES:
                shadertexdesc = texprop.shader_textures[2]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=glossmtex.tex)

        if darkmtex:
            texprop.has_dark_texture = True
            self.export_tex_desc(texdesc = texprop.dark_texture,
                                 uvlayers = uvlayers,
                                 mtex = darkmtex)

        if detailmtex:
            texprop.has_detail_texture = True
            self.export_tex_desc(texdesc = texprop.detail_texture,
                                 uvlayers = uvlayers,
                                 mtex = detailmtex)

        if refmtex:
            if self.EXPORT_VERSION not in self.USED_EXTRA_SHADER_TEXTURES:
                self.logger.warn(
                    "Cannot export reflection texture for this game.")
                #texprop.hasRefTexture = True
                #self.export_tex_desc(texdesc = texprop.refTexture,
                #                     uvlayers = uvlayers,
                #                     mtex = refmtex)
            else:
                shadertexdesc = texprop.shader_textures[3]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=refmtex.tex)

        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiTexturingProperty) \
               and block.get_hash() == texprop.get_hash():
                return block

        # no texturing property with given settings found, so use and register
        # the new one
        return self.register_block(texprop)

    def export_bs_shader_property(
        self, basemtex=None, bumpmtex=None, glowmtex=None):
        """Export a Bethesda shader property block."""

        # create new block
        bsshader = NifFormat.BSShaderPPLightingProperty()
        # set shader options
        bsshader.shader_type = self.EXPORT_FO3_SHADER_TYPE
        bsshader.shader_flags.zbuffer_test = self.EXPORT_FO3_SF_ZBUF
        bsshader.shader_flags.shadow_map = self.EXPORT_FO3_SF_SMAP
        bsshader.shader_flags.shadow_frustum = self.EXPORT_FO3_SF_SFRU
        bsshader.shader_flags.window_environment_mapping = self.EXPORT_FO3_SF_WINDOW_ENVMAP
        bsshader.shader_flags.empty = self.EXPORT_FO3_SF_EMPT
        bsshader.shader_flags.unknown_31 = self.EXPORT_FO3_SF_UN31
        # set textures
        texset = NifFormat.BSShaderTextureSet()
        bsshader.texture_set = texset
        if basemtex:
            texset.textures[0] = self.export_texture_filename(basemtex.tex)
        if bumpmtex:
            texset.textures[1] = self.export_texture_filename(bumpmtex.tex)
        if glowmtex:
            texset.textures[2] = self.export_texture_filename(glowmtex.tex)

        # search for duplicates
        # DISABLED: the Fallout 3 engine cannot handle them
        #for block in self.blocks:
        #    if (isinstance(block, NifFormat.BSShaderPPLightingProperty)
        #        and block.get_hash() == bsshader.get_hash()):
        #        return block

        # no duplicate found, so use and register new one
        return self.register_block(bsshader)

    def export_texture_effect(self, mtex = None):
        """Export a texture effect block from material texture mtex (MTex, not
        Texture)."""
        texeff = NifFormat.NiTextureEffect()
        texeff.flags = 4
        texeff.rotation.set_identity()
        texeff.scale = 1.0
        texeff.model_projection_matrix.set_identity()
        texeff.texture_filtering = NifFormat.TexFilterMode.FILTER_TRILERP
        texeff.texture_clamping  = NifFormat.TexClampMode.WRAP_S_WRAP_T
        texeff.texture_type = NifFormat.EffectType.EFFECT_ENVIRONMENT_MAP
        texeff.coordinate_generation_type = NifFormat.CoordGenType.CG_SPHERE_MAP
        if mtex:
            texeff.source_texture = self.export_source_texture(mtex.tex)
            if self.EXPORT_VERSION == 'Morrowind':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return self.register_block(texeff)

    def export_bounding_box(self, obj, block_parent, bsbound=False):
        """Export a Morrowind or Oblivion bounding box."""
        # calculate bounding box extents
        objbbox = obj.getBoundBox()
        minx = min(vert[0] for vert in objbbox)
        miny = min(vert[1] for vert in objbbox)
        minz = min(vert[2] for vert in objbbox)
        maxx = max(vert[0] for vert in objbbox)
        maxy = max(vert[1] for vert in objbbox)
        maxz = max(vert[2] for vert in objbbox)

        if bsbound:
            bbox = self.create_block("BSBound")
            # ... the following incurs double scaling because it will be added in
            # both the extra data list and in the old extra data sequence!!!
            #block_parent.add_extra_data(bbox)
            # quick hack (better solution would be to make apply_scale non-recursive)
            block_parent.num_extra_data_list += 1
            block_parent.extra_data_list.update_size()
            block_parent.extra_data_list[-1] = bbox
            
            # set name, center, and dimensions
            bbox.name = "BBX"
            bbox.center.x = (minx + maxx) * 0.5
            bbox.center.y = (miny + maxy) * 0.5
            bbox.center.z = (minz + maxz) * 0.5
            bbox.dimensions.x = (maxx - minx) * 0.5
            bbox.dimensions.y = (maxy - miny) * 0.5
            bbox.dimensions.z = (maxz - minz) * 0.5
        else:
            bbox = self.create_ninode()
            block_parent.add_child(bbox)
            # set name, flags, translation, and radius
            bbox.name = "Bounding Box"
            bbox.flags = 4
            bbox.translation.x = (minx + maxx) * 0.5 + obj.LocX
            bbox.translation.y = (minx + maxx) * 0.5 + obj.LocY
            bbox.translation.z = (minx + maxx) * 0.5 + obj.LocZ
            bbox.rotation.set_identity()
            bbox.has_bounding_box = True
            # weirdly, bounding box center (bbox.bounding_box.translation)
            # is specified relative to the *parent* (not relative to bbox!)
            bbox.bounding_box.translation.deepcopy(bbox.translation)
            bbox.bounding_box.rotation.set_identity()
            bbox.bounding_box.radius.x = (maxx - minx) * 0.5
            bbox.bounding_box.radius.y = (maxy - miny) * 0.5
            bbox.bounding_box.radius.z = (maxz - minz) * 0.5

    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[self.EXPORT_VERSION]:
            shadername = self.EXTRA_SHADER_TEXTURES[shaderindex]
            trishape.add_integer_extra_data(shadername, shaderindex)

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

    def export_range_lod_data(self, n_node, b_obj):
        """Export range lod data for for the children of b_obj, as a
        NiRangeLODData block on n_node.
        """
        # create range lod data object
        n_range_data = self.create_block("NiRangeLODData", b_obj)
        n_node.lod_level_data = n_range_data
        # get the children
        b_children = self.get_b_children(b_obj)
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

    def exportEgm(self, keyblocks):
        self.egmdata = EgmFormat.Data(num_vertices=len(keyblocks[0].data))
        for keyblock in keyblocks:
            if keyblock.name.startswith("EGM SYM"):
                morph = self.egmdata.add_sym_morph()
            elif keyblock.name.startswith("EGM ASYM"):
                morph = self.egmdata.add_asym_morph()
            else:
                continue
            self.logger.info("Exporting morph %s to egm" % keyblock.name)
            relative_vertices = []
            # note: keyblocks[0] is base key
            for vert, key_vert in izip(keyblocks[0].data, keyblock.data):
                relative_vertices.append(key_vert - vert)
            morph.set_relative_vertices(relative_vertices)

def config_callback(**config):
    """Called when config script is done. Starts and times import."""
    starttime = Blender.sys.time()
    # run exporter
    exporter = NifExport(**config)
    # finish export
    exporter.logger.info('Finished in %.2f seconds'
                         % (Blender.sys.time() - starttime))
    Blender.Window.WaitCursor(0)

def fileselect_callback(filename):
    """Called once file is selected. Starts config GUI."""
    global _CONFIG
    _CONFIG.run(NifConfig.TARGET_EXPORT, filename, config_callback)

if __name__ == '__main__':
    # use global config variable so gui elements don't go out of skope
    _CONFIG = NifConfig()
    # open file selector window, and then call fileselect_callback
    Blender.Window.FileSelector(
        fileselect_callback, "Export NIF/KF", _CONFIG.config["EXPORT_FILE"])
