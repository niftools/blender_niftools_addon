"""This script exports Netimmerse and Gamebryo .nif files from Blender."""

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


from io_scene_nif.nif_common import NifCommon

from io_scene_nif.animationsys.animation_export import AnimationHelper
from io_scene_nif.collisionsys.collision_export import bhkshape_export, bound_export
from io_scene_nif.armaturesys.armature_export import Armature
from io_scene_nif.propertysys.property_export import PropertyHelper
from io_scene_nif.constraint.constraint_export import Constraint


import logging
import os.path

import mathutils
import bpy

import pyffi.spells.nif
import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat



class NifExportError(Exception):
    """A simple custom exception class for export errors."""
    pass

# main export class
class NifExport(NifCommon):


    IDENTITY44 = NifFormat.Matrix44()
    IDENTITY44.set_identity()
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38


    

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

    def get_unique_name(self, blender_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object.

        :param blender_name: Name of object as in blender.
        :type blender_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        unique_name = "unnamed"
        if blender_name:
            unique_name = blender_name
        # blender bone naming -> nif bone naming
        unique_name = self.get_bone_name_for_nif(unique_name)
        # ensure uniqueness
        if unique_name in self.block_names or unique_name in list(self.names.values()):
            unique_int = 0
            old_name = unique_name
            while unique_name in self.block_names or unique_name in list(self.names.values()):
                unique_name = "%s.%02d" % (old_name, unique_int)
                unique_int += 1
        self.block_names.append(unique_name)
        self.names[blender_name] = unique_name
        return unique_name

    def get_full_name(self, blender_name):
        """Returns the original imported name if present, or the name by which
        the object was exported already.

        :param blender_name: Name of object as in blender.
        :type blender_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        try:
            return self.names[blender_name]
        except KeyError:
            return self.get_unique_name(blender_name)

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

    def execute(self):
        """Main export function."""

        # Helper systems
        # Store references to subsystems as needed.
        self.boundhelper = bound_export(parent=self)
        self.bhkshapehelper = bhkshape_export(parent=self)
        self.armaturehelper = Armature(parent=self)
        self.animationhelper = AnimationHelper(parent=self)
        self.propertyhelper = PropertyHelper(parent=self)
        self.constrainthelper = Constraint(parent=self)

        self.info("exporting {0}".format(self.properties.filepath))

        # TODO
        '''
        if self.properties.animation == 'ALL_NIF_XNIF_XKF' and self.properties.game == 'MORROWIND':
            # if exporting in nif+xnif+kf mode, then first export
            # the nif with geometry + animation, which is done by:
            self.properties.animation = 'ALL_NIF'
        '''

        # extract directory, base name, extension
        directory = os.path.dirname(self.properties.filepath)
        filebase, fileext = os.path.splitext(
            os.path.basename(self.properties.filepath))

        # variables
        # dictionary mapping exported blocks to either None or to an
        # associated Blender object
        self.blocks = {}
        # maps Blender names to previously imported names from the FullNames
        # buffer (see self.rebuild_full_names())
        self.names = {}
        # keeps track of names of exported blocks, to make sure they are unique
        self.block_names = []

        # store bone priorities (from NULL constraints) as the armature bones
        # are parsed, so they are available when writing the kf file
        # maps bone NiNode to priority value
        self.bone_priorities = {}

        # if an egm is exported, this will contain the data
        self.egmdata = None

        try: # catch export errors

            # find nif version to write
            self.version = self.operator.version[self.properties.game]
            self.info("Writing NIF version 0x%08X" % self.version)

            if self.properties.animation == 'ALL_NIF':
                self.info("Exporting geometry and animation")
            elif self.properties.animation == 'GEOM_NIF':
                # for morrowind: everything except keyframe controllers
                self.info("Exporting geometry only")
            elif self.properties.animation == 'ANIM_KF':
                # for morrowind: only keyframe controllers
                self.info("Exporting animation only (as .kf file)")

            for b_obj in bpy.data.objects:
                # armatures should not be in rest position
                if b_obj.type == 'ARMATURE':
                    # ensure we get the mesh vertices in animation mode,
                    # and not in rest position!
                    b_obj.data.pose_position = 'POSE'
                    if (b_obj.data.use_deform_envelopes):
                        return self.error(
                            "'%s': Cannot export envelope skinning."
                            " If you have vertex groups,"
                            " turn off envelopes. If you don't have vertex"
                            " groups, select the bones one by one press W"
                            " to convert their envelopes to vertex weights,"
                            " and turn off envelopes."
                            % b_obj.name)

                # check for non-uniform transforms
                # (lattices are not exported so ignore them as they often tend
                # to have non-uniform scaling)
                if b_obj.type != 'LATTICE':
                    scale = b_obj.matrix_local.to_scale()
                    if (abs(scale.x - scale.y) > self.properties.epsilon
                        or abs(scale.y - scale.z) > self.properties.epsilon):

                        return self.error(
                            "Non-uniform scaling not supported."
                            " Workaround: apply size and rotation (CTRL-A)"
                            " on '%s'." % b_obj.name)

            # oblivion, Fallout 3 and civ4
            if (self.properties.game
                in ('CIVILIZATION_IV', 'OBLIVION', 'FALLOUT_3')):
                root_name = 'Scene Root'
            # other games
            else:
                root_name = filebase

            # get the root object from selected object
            # only export empties, meshes, and armatures
            if not self.context.selected_objects:
                raise NifExportError(
                    "Please select the object(s) to export,"
                    " and run this script again.")
            root_objects = set()
            export_types = ('EMPTY', 'MESH', 'ARMATURE')
            for root_object in [b_obj for b_obj in self.context.selected_objects
                                if b_obj.type in export_types]:
                while root_object.parent:
                    root_object = root_object.parent
                if root_object.type not in export_types:
                    raise NifExportError(
                        "Root object (%s) must be an 'EMPTY', 'MESH',"
                        " or 'ARMATURE' object."
                        % root_object.name)
                root_objects.add(root_object)

            # smoothen seams of objects
            if self.properties.smooth_object_seams:
                # get shared vertices
                self.info("Smoothing seams between objects...")
                vdict = {}
                for b_obj in [b_obj for b_obj in self.context.scene.objects
                           if b_obj.type == 'MESH']:
                    mesh = b_obj.data
                    # for v in mesh.vertices:
                    #    v.sel = False
                    for f in mesh.faces:
                        for v_index in f.vertices:
                            v = mesh.vertices[v_index]
                            vkey = (int(v.co[0]*self.VERTEX_RESOLUTION),
                                    int(v.co[1]*self.VERTEX_RESOLUTION),
                                    int(v.co[2]*self.VERTEX_RESOLUTION))
                            try:
                                vdict[vkey].append((v, f, mesh))
                            except KeyError:
                                vdict[vkey] = [(v, f, mesh)]
                # set normals on shared vertices
                nv = 0
                for vlist in vdict.values():
                    if len(vlist) <= 1: continue # not shared
                    meshes = set([mesh for v, f, mesh in vlist])
                    if len(meshes) <= 1: continue # not shared
                    # take average of all face normals of faces that have this
                    # vertex
                    norm = mathutils.Vector()
                    for v, f, mesh in vlist:
                        norm += f.normal
                    norm.normalize()
                    # remove outliers (fixes better bodies issue)
                    # first calculate fitness of each face
                    fitlist = [f.normal.dot(norm)
                               for v, f, mesh in vlist]
                    bestfit = max(fitlist)
                    # recalculate normals only taking into account
                    # well-fitting faces
                    norm = mathutils.Vector()
                    for (v, f, mesh), fit in zip(vlist, fitlist):
                        if fit >= bestfit - 0.2:
                            norm += f.normal
                    norm.normalize()
                    # save normal of this vertex
                    for v, f, mesh in vlist:
                        v.normal = norm
                        # v.sel = True
                    nv += 1
                self.info("Fixed normals on %i vertices." % nv)

            # TODO use Blender actions for animation groups
            # check for animation groups definition in a text buffer 'Anim'
            try:
                animtxt = None #Changed for testing needs fix bpy.data.texts["Anim"]
            except NameError:
                animtxt = None

            # rebuild the bone extra matrix dictionary from the 'BoneExMat' text buffer
            self.armaturehelper.rebuild_bones_extra_matrices()

            # rebuild the full name dictionary from the 'FullNames' text buffer
            self.rebuild_full_names()

            # export nif:
            # -----------
            self.info("Exporting")

            # create a nif object

            # export the root node (the name is fixed later to avoid confusing the
            # exporter with duplicate names)
            root_block = self.export_node(None, 'none', None, '')

            # export objects
            self.info("Exporting objects")
            for root_object in root_objects:
                # export the root objects as a NiNodes; their children are
                # exported as well
                # note that localspace = worldspace, because root objects have
                # no parents
                self.export_node(root_object, 'localspace',
                                 root_block, root_object.name)

            # post-processing:
            # ----------------

            # if we exported animations, but no animation groups are defined,
            # define a default animation group
            self.info("Checking animation groups")
            if not animtxt:
                has_controllers = False
                for block in self.blocks:
                    # has it a controller field?
                    if isinstance(block, NifFormat.NiObjectNET):
                        if block.controller:
                            has_controllers = True
                            break
                if has_controllers:
                    self.info("Defining default animation group.")
                    # write the animation group text buffer
                    animtxt = Blender.Text.New("Anim")
                    animtxt.write("%i/Idle: Start/Idle: Loop Start\n%i/Idle: Loop Stop/Idle: Stop" %
                                  (self.context.scene.frame_start, self.context.scene.frame_end))

            # animations without keyframe animations crash the TESCS
            # if we are in that situation, add a trivial keyframe animation
            self.info("Checking controllers")
            if animtxt and self.properties.game == 'MORROWIND':
                has_keyframecontrollers = False
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiKeyframeController):
                        has_keyframecontrollers = True
                        break
                if ((not has_keyframecontrollers)
                    and (not self.properties.bs_animation_node)):
                    self.info("Defining dummy keyframe controller")
                    # add a trivial keyframe controller on the scene root
                    self.animationhelper.export_keyframes(None, 'localspace', root_block)
            if (self.properties.bs_animation_node
                and self.properties.game == 'MORROWIND'):
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
            if self.properties.game in ('OBLIVION', 'FALLOUT_3') \
                and filebase.lower() in ('skeleton', 'skeletonbeast'):
                # here comes everything that is Oblivion skeleton export
                # specific
                self.info(
                    "Adding controllers and interpolators for skeleton")
                for block in list(self.blocks.keys()):
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
                    anim_textextra = self.animationhelper.export_anim_groups(animtxt, root_block)
                else:
                    anim_textextra = None

            # oblivion and Fallout 3 furniture markers
            if (self.properties.game in ('OBLIVION', 'FALLOUT_3')
                and filebase[:15].lower() == 'furnituremarker'):
                # exporting a furniture marker for Oblivion/FO3
                try:
                    furniturenumber = int(filebase[15:])
                except ValueError:
                    raise NifExportError(
                        "Furniture marker has invalid number (%s)."
                        " Name your file 'furnituremarkerxx.nif'"
                        " where xx is a number between 00 and 19."
                        % filebase[15:])
                # name scene root name the file base name
                root_name = filebase

                # create furniture marker block
                furnmark = self.create_block("BSFurnitureMarker")
                furnmark.name = "FRN"
                furnmark.num_positions = 1
                furnmark.positions.update_size()
                furnmark.positions[0].position_ref_1 = furniturenumber
                furnmark.positions[0].position_ref_2 = furniturenumber

                # create extra string data sgoKeep
                sgokeep = self.create_block("NiStringExtraData")
                sgokeep.name = "UPB" # user property buffer
                sgokeep.string_data = "sgoKeep=1 ExportSel = Yes" # Unyielding = 0, sgoKeep=1ExportSel = Yes

                # add extra blocks
                root_block.add_extra_data(furnmark)
                root_block.add_extra_data(sgokeep)

            # FIXME
            self.info("Checking collision")
            # activate oblivion/Fallout 3 collision and physics
            if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
                hascollision = False
                for b_obj in bpy.data.objects:
                    if b_obj.game.use_collision_bounds == True:
                        hascollision = True
                        break
                if hascollision:
                    # enable collision
                    bsx = self.create_block("BSXFlags")
                    bsx.name = 'BSX'
                    bsx.integer_data = b_obj.niftools.bsxflags
                    root_block.add_extra_data(bsx)

                    # many Oblivion nifs have a UPB, but export is disabled as
                    # they do not seem to affect anything in the game
                    upb = self.create_block("NiStringExtraData")
                    upb.name = 'UPB'
                    if(b_obj.niftools.upb != ''):
                        upb.string_data = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                    else:
                        upb.string_data = b_obj.niftools.upb
                    root_block.add_extra_data(upb)

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

            # bhkConvexVerticesShape of children of bhkListShapes
            # need an extra bhkConvexTransformShape
            # (see issue #3308638, reported by Koniption)
            # note: self.blocks changes during iteration, so need list copy
            for block in list(self.blocks):
                if isinstance(block, NifFormat.bhkListShape):
                    for i, sub_shape in enumerate(block.sub_shapes):
                        if isinstance(sub_shape, NifFormat.bhkConvexVerticesShape):
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
                if isinstance(b_obj, bpy.types.Object) and b_obj.constraints:
                    self.export_constraints(b_obj, root_block)

            # export weapon location
            if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
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
            if self.properties.game in ('CIVILIZATION_IV', 'SID_MEIER_S_RAILROADS'):
                self.propertyhelper.object_property.export_vertex_color_property(root_block)
                self.propertyhelper.object_property.export_z_buffer_property(root_block)
            elif self.properties.game in ('EMPIRE_EARTH_II',):
                self.propertyhelper.object_property.export_vertex_color_property(root_block)
                self.propertyhelper.object_property.export_z_buffer_property(root_block, flags=15, function=1)

            # FIXME
            """
            if self.EXPORT_FLATTENSKIN:
                # (warning: trouble if armatures parent other armatures or
                # if bones parent geometries, or if object is animated)
                # flatten skins
                skelroots = set()
                affectedbones = []
                for block in self.blocks:
                    if isinstance(block, NifFormat.NiGeometry) and block.is_skin():
                        self.info("Flattening skin on geometry %s"
                                         % block.name)
                        affectedbones.extend(block.flatten_skin())
                        skelroots.add(block.skin_instance.skeleton_root)
                # remove NiNodes that do not affect skin
                for skelroot in skelroots:
                    self.info("Removing unused NiNodes in '%s'"
                                     % skelroot.name)
                    skelrootchildren = [child for child in skelroot.children
                                        if ((not isinstance(child,
                                                            NifFormat.NiNode))
                                            or (child in affectedbones))]
                    skelroot.num_children = len(skelrootchildren)
                    skelroot.children.update_size()
                    for i, child in enumerate(skelrootchildren):
                        skelroot.children[i] = child
            """

            # apply scale
            if abs(self.properties.scale_correction) > self.properties.epsilon:
                self.info("Applying scale correction %f"
                                 % self.properties.scale_correction)
                data = NifFormat.Data()
                data.roots = [root_block]
                toaster = pyffi.spells.nif.NifToaster()
                toaster.scale = self.properties.scale_correction
                pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()
                # also scale egm
                if self.egmdata:
                    self.egmdata.apply_scale(self.properties.scale_correction)

            # generate mopps (must be done after applying scale!)
            if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
                for block in self.blocks:
                    if isinstance(block, NifFormat.bhkMoppBvTreeShape):
                       self.info("Generating mopp...")
                       block.update_mopp()
                       #print "=== DEBUG: MOPP TREE ==="
                       #block.parse_mopp(verbose = True)
                       #print "=== END OF MOPP TREE ==="
                       # warn about mopps on non-static objects
                       if any(sub_shape.layer != 1
                              for sub_shape in block.shape.sub_shapes):
                           self.warning(
                               "Mopps for non-static objects may not function"
                               " correctly in-game. You may wish to use"
                               " simple primitives for collision.")

            # delete original scene root if a scene root object was already defined
            if ((root_block.num_children == 1)
                and ((root_block.children[0].name in ['Scene Root', 'Bip01']) or root_block.children[0].name[-3:] == 'nif')):
                if root_block.children[0].name[-3:] == 'nif':
                    root_block.children[0].name = filebase
                self.info(
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
            if (self.properties.game == 'FALLOUT_3' and self.EXPORT_FO3_FADENODE):
                self.info("Making root block a BSFadeNode")
                fade_root_block = NifFormat.BSFadeNode().deepcopy(root_block)
                fade_root_block.replace_global_node(root_block, fade_root_block)
                root_block = fade_root_block

            # figure out user version and user version 2
            if self.properties.game == 'OBLIVION':
                NIF_USER_VERSION = 11
                NIF_USER_VERSION2 = 11
            elif self.properties.game == 'FALLOUT_3':
                NIF_USER_VERSION = 11
                NIF_USER_VERSION2 = 34
            elif self.properties.game == 'DIVINITY_2':
                NIF_USER_VERSION = 131072
                NIF_USER_VERSION = 0
            else:
                NIF_USER_VERSION = 0
                NIF_USER_VERSION2 = 0

            # export nif file:
            # ----------------

            if self.properties.animation != 'ANIM_KF':
                if self.properties.game == 'EMPIRE_EARTH_II':
                    ext = ".nifcache"
                else:
                    ext = ".nif"
                self.info("Writing %s file" % ext)

                # make sure we have the right file extension
                if (fileext.lower() != ext):
                    self.warning(
                        "Changing extension from %s to %s on output file"
                        % (fileext, ext))
                niffile = os.path.join(directory, filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version_2=NIF_USER_VERSION2)
                data.roots = [root_block]
                if self.properties.game == 'NEOSTEAM':
                    data.modification = "neosteam"
                elif self.properties.game == 'ATLANTICA':
                    data.modification = "ndoors"
                elif self.properties.game == 'HOWLING_SWORD':
                    data.modification = "jmihs1"
                with open(niffile, "wb") as stream:
                    data.write(stream)

            # create and export keyframe file and xnif file:
            # ----------------------------------------------

            # convert root_block tree into a keyframe tree
            if self.properties.animation == 'ANIM_KF' or self.properties.animation == 'ALL_NIF_XNIF_XKF':
                self.info("Creating keyframe tree")
                # find all nodes and relevant controllers
                node_kfctrls = {}
                for node in root_block.tree():
                    if not isinstance(node, NifFormat.NiAVObject):
                        continue
                    # get list of all controllers for this node
                    ctrls = node.get_controllers()
                    for ctrl in ctrls:
                        if self.properties.game == 'MORROWIND':
                            # morrowind: only keyframe controllers
                            if not isinstance(ctrl,
                                              NifFormat.NiKeyframeController):
                                continue
                        if not node in node_kfctrls:
                            node_kfctrls[node] = []
                        node_kfctrls[node].append(ctrl)
                # morrowind
                if self.properties.game in ('MORROWIND', 'FREEDOM_FORCE'):
                    # create kf root header
                    kf_root = self.create_block("NiSequenceStreamHelper")
                    kf_root.add_extra_data(anim_textextra)
                    # reparent controller tree
                    for node, ctrls in node_kfctrls.items():
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
                elif self.properties.game in ('OBLIVION', 'FALLOUT_3',
                                             'CIVILIZATION_IV', 'ZOO_TYCOON_2',
                                             'FREEDOM_FORCE_VS_THE_3RD_REICH'):
                    # create kf root header
                    kf_root = self.create_block("NiControllerSequence")
                    if self.EXPORT_ANIMSEQUENCENAME:
                        kf_root.name = self.EXPORT_ANIMSEQUENCENAME
                    else:
                        kf_root.name = filebase
                    kf_root.unknown_int_1 = 1
                    kf_root.weight = 1.0
                    kf_root.text_keys = anim_textextra
                    kf_root.cycle_type = NifFormat.CycleType.CYCLE_CLAMP
                    kf_root.frequency = 1.0
                    kf_root.start_time =(self.context.scene.frame_start - 1) * self.context.scene.render.fps
                    kf_root.stop_time = (self.context.scene.frame_end - self.context.scene.frame_start) * self.context.scene.render.fps
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
                        in zip(iter(node_kfctrls.keys()),
                                iter(node_kfctrls.values())):
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
                            for interpolator, variable_2 in zip(interpolators,
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
                                        self.warning(
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
                        % self.properties.game)

                # write kf (and xnif if asked)
                prefix = "" if (self.properties.animation != 'ALL_NIF_XNIF_XKF') else "x"

                ext = ".kf"
                self.info("Writing %s file" % (prefix + ext))

                kffile = os.path.join(directory, prefix + filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version2=NIF_USER_VERSION2)
                data.roots = [kf_root]
                data.neosteam = (self.properties.game == 'NEOSTEAM')
                stream = open(kffile, "wb")
                try:
                    data.write(stream)
                finally:
                    stream.close()

            if self.properties.animation == 'ALL_NIF_XNIF_XKF':
                self.info("Detaching keyframe controllers from nif")
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

                self.info("Detaching animation text keys from nif")
                # detach animation text keys
                if root_block.extra_data is not anim_textextra:
                    raise RuntimeError(
                        "Oops, you found a bug! Animation extra data"
                        " wasn't where expected...")
                root_block.extra_data = None

                prefix = "x" # we are in morrowind 'nifxnifkf mode'
                ext = ".nif"
                self.info("Writing %s file" % (prefix + ext))

                xniffile = os.path.join(directory, prefix + filebase + ext)
                data = NifFormat.Data(version=self.version,
                                      user_version=NIF_USER_VERSION,
                                      user_version2=NIF_USER_VERSION2)
                data.roots = [root_block]
                data.neosteam = (self.properties.game == 'NEOSTEAM')
                stream = open(xniffile, "wb")
                try:
                    data.write(stream)
                finally:
                    stream.close()

            # export egm file:
            #-----------------

            if self.egmdata:
                ext = ".egm"
                self.info("Writing %s file" % ext)

                egmfile = os.path.join(directory, filebase + ext)
                stream = open(egmfile, "wb")
                try:
                    self.egmdata.write(stream)
                finally:
                    stream.close()
        finally:
            # clear progress bar
            self.info("Finished")

        # save exported file (this is used by the test suite)
        self.root_blocks = [root_block]

        return {'FINISHED'}

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
            # -> empty, mesh, or armature
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
                            self.get_bone_name_for_nif(b_obj.name)
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
                    self.export_tri_shapes(b_obj, space, parent_block, node_name)
                    # we didn't create a ninode, return nothing
                    return None
            else:
                # -> everything else (empty/armature) is a regular node
                node = self.create_ninode(b_obj)
                # does node have priority value in NULL constraint?
                for constr in b_obj.constraints:
                    if constr.name[:9].lower() == "priority:":
                        self.bone_priorities[
                            self.get_bone_name_for_nif(b_obj.name)
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
        node.name = self.get_full_name(node_name).encode()

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

        self.export_matrix(b_obj, space, node)

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
                self.export_tri_shapes(b_obj, trishape_space, node)

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

    def export_tri_shapes(self, b_obj, space, parent_block, trishape_name = None):
        self.info("Exporting %s" % b_obj)

        assert(b_obj.type == 'MESH')

        # get mesh from b_obj
        mesh = b_obj.data # get mesh data

        # getVertsFromGroup fails if the mesh has no vertices
        # (this happens when checking for fallout 3 body parts)
        # so quickly catch this (rare!) case
        if not b_obj.data.vertices:
            # do not export anything
            self.warning("%s has no vertices, skipped." % b_obj)
            return

        # get the mesh's materials, this updates the mesh material list
        if not isinstance(parent_block, NifFormat.RootCollisionNode):
            mesh_materials = mesh.materials
        else:
            # ignore materials on collision trishapes
            mesh_materials = []
        # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
        if not mesh_materials:
            mesh_materials = [None]

        # is mesh double sided?
        mesh_doublesided = mesh.show_double_sided

        #vertex color check
        mesh_hasvcol = False
        mesh_hasvcola = False

        if(mesh.vertex_colors):
            mesh_hasvcol = True

            #vertex alpha check
            if(len(mesh.vertex_colors) == 1):
                self.warning("Mesh only has one Vertex Color layer"
                             " default alpha values will be written\n"
                             " - For Alpha values add a second vertex layer, "
                             " greyscale only"
                             )
                mesh_hasvcola = False
            else:
                #iterate over colorfaces
                for b_meshcolor in mesh.vertex_colors[1].data:
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
        for materialIndex, mesh_material in enumerate(mesh_materials):
            # -> first, extract valuable info from our b_obj

            mesh_base_mtex = None
            mesh_glow_mtex = None
            mesh_bump_mtex = None
            mesh_normal_mtex = None
            mesh_gloss_mtex = None
            mesh_dark_mtex = None
            mesh_detail_mtex = None
            mesh_texeff_mtex = None
            mesh_ref_mtex = None
            mesh_texture_alpha = False #texture has transparency

            mesh_uvlayers = []    # uv layers used by this material
            mesh_hasalpha = False # mesh has transparency
            mesh_haswire = False  # mesh rendered as wireframe
            mesh_hasspec = False  # mesh specular property

            mesh_hasnormals = False
            if mesh_material is not None:
                mesh_hasnormals = True # for proper lighting

                #ambient mat
                mesh_mat_ambient_color = [1.0, 1.0, 1.0]

                #diffuse mat
                mesh_mat_diffuse_color = [1.0, 1.0, 1.0]
                '''
                TODO_3.0 - If needed where ambient should not be defaulted

                #ambient mat
                mesh_mat_ambient_color[0] = mesh_material.niftools.ambient_color[0] * mesh_material.niftools.ambient_factor
                mesh_mat_ambient_color[1] = mesh_material.niftools.ambient_color[1] * mesh_material.niftools.ambient_factor
                mesh_mat_ambient_color[2] = mesh_material.niftools.ambient_color[2] * mesh_material.niftools.ambient_factor

                #diffuse mat
                mest_mat_diffuse_color[0] = mesh_material.niftools.diffuse_color[0] * mesh_material.niftools.diffuse_factor
                mest_mat_diffuse_color[1] = mesh_material.niftools.diffuse_color[1] * mesh_material.niftools.diffuse_factor
                mest_mat_diffuse_color[2] = mesh_material.niftools.diffuse_color[2] * mesh_material.niftools.diffuse_factor
                '''

                #emissive mat
                mesh_mat_emissive_color = [0.0, 0.0, 0.0]
                mesh_mat_emitmulti = 1.0 # default
                if self.properties.game != 'FALLOUT_3':
                    #old code
                    #mesh_mat_emissive_color = mesh_material.diffuse_color * mesh_material.emit
                    mesh_mat_emissive_color = mesh_material.niftools.emissive_color * mesh_material.emit

                else:
                    # special case for Fallout 3 (it does not store diffuse color)
                    # if emit is non-zero, set emissive color to diffuse
                    # (otherwise leave the color to zero)
                    if mesh_material.emit > self.properties.epsilon:

                        #old code
                        #mesh_mat_emissive_color = mesh_material.diffuse_color
                        mesh_mat_emissive_color = mesh_material.niftools.emissive_color
                        mesh_mat_emitmulti = mesh_material.emit * 10.0

                #specular mat
                mesh_mat_specular_color = mesh_material.specular_color
                if mesh_material.specular_intensity > 1.0:
                    mesh_material.specular_intensity = 1.0

                mesh_mat_specular_color[0] *= mesh_material.specular_intensity
                mesh_mat_specular_color[1] *= mesh_material.specular_intensity
                mesh_mat_specular_color[2] *= mesh_material.specular_intensity

                if ( mesh_mat_specular_color[0] > self.properties.epsilon ) \
                    or ( mesh_mat_specular_color[1] > self.properties.epsilon ) \
                    or ( mesh_mat_specular_color[2] > self.properties.epsilon ):
                    mesh_hasspec = True

                #gloss mat
                #'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
                mesh_mat_gloss = mesh_material.specular_hardness / 4.0

                #alpha mat
                mesh_hasalpha = False
                mesh_mat_transparency = mesh_material.alpha
                if(mesh_material.use_transparency):
                    if(abs(mesh_mat_transparency - 1.0)> self.properties.epsilon):
                        mesh_hasalpha = True
                elif(mesh_hasvcola):
                    mesh_hasalpha = True
                elif(mesh_material.animation_data and mesh_material.animation_data.action.fcurves['Alpha']):
                    mesh_hasalpha = True

                #wire mat
                mesh_haswire = (mesh_material.type == 'WIRE')

                # the base texture = first material texture
                # note that most morrowind files only have a base texture, so let's for now only support single textured materials
                for b_mat_texslot in mesh_material.texture_slots:
                    if not b_mat_texslot or not b_mat_texslot.use:
                        # skip unused texture slots
                        continue

                    # check REFL-mapped textures
                    # (used for "NiTextureEffect" materials)
                    if b_mat_texslot.texture_coords == 'REFLECTION':
                        # of course the user should set all kinds of other
                        # settings to make the environment mapping come out
                        # (MapTo "COL", blending mode "Add")
                        # but let's not care too much about that
                        # only do some simple checks
                        if not b_mat_texslot.use_map_color_diffuse:
                            # it should map to colour
                            raise NifExportError(
                                "Non-COL-mapped reflection texture in mesh '%s', material '%s',"
                                " these cannot be exported to NIF.\n"
                                "Either delete all non-COL-mapped reflection textures,"
                                " or in the Shading Panel, under Material Buttons,"
                                " set texture 'Map To' to 'COL'."
                                % (b_obj.name,mesh_material.name))
                        if b_mat_texslot.blend_type != 'ADD':
                            # it should have "ADD" blending mode
                            self.warning(
                               "Reflection texture should have blending"
                               " mode 'Add' on texture"
                               " in mesh '%s', material '%s')."
                               % (b_obj.name,mesh_material.name))
                            # an envmap image should have an empty... don't care
                        mesh_texeff_mtex = b_mat_texslot

                    # check UV-mapped textures
                    elif b_mat_texslot.texture_coords == 'UV':
                        # update set of uv layers that must be exported
                        if not b_mat_texslot.uv_layer in mesh_uvlayers:
                            mesh_uvlayers.append(b_mat_texslot.uv_layer)

                        #glow tex
                        if b_mat_texslot.use_map_emit:
                            #multi-check
                            if mesh_glow_mtex:
                                raise NifExportError(
                                    "Multiple glow textures in mesh '%s', material '%s'.\n"
                                    "Make sure Texture -> Influence -> Shading -> Emit is disabled"
                                    %(mesh.name,mesh_material.name))
                            '''
                            TODO_3.0 - Fallout3 + specific.
                            Check if these are still possible
                            # check if calculation of alpha channel is enabled
                            # for this texture
                            if b_mat_texslot.texture.use_calculate_alpha and b_mat_texslot.use_map_alpha:
                                self.warning(
                                    "In mesh '%s', material '%s': glow texture must have"
                                    " CALCALPHA flag set, and must have MapTo.ALPHA enabled."
                                    %(b_obj.name,mesh_material.name))
                            '''

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            mesh_glow_mtex = b_mat_texslot

                        #specular
                        elif b_mat_texslot.use_map_specular:
                            #multi-check
                            if mesh_gloss_mtex:
                                raise NifExportError(
                                    "Multiple gloss textures in"
                                    " mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.SPEC"
                                    %(mesh.name,mesh_material.name))

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            # got the gloss map
                            mesh_gloss_mtex = b_mat_texslot

                        #bump map
                        elif b_mat_texslot.use_map_normal:
                            #multi-check
                            if mesh_bump_mtex:
                                raise NifExportError(
                                    "Multiple bump/normal textures"
                                    " in mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.NOR"
                                    %(mesh.name,mesh_material.name))

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True

                            mesh_bump_mtex = b_mat_texslot

                        #darken
                        elif b_mat_texslot.use_map_color_diffuse and \
                             b_mat_texslot.blend_type == 'DARKEN' and \
                             not mesh_dark_mtex:

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            # got the dark map
                            mesh_dark_mtex = b_mat_texslot

                        #diffuse
                        elif b_mat_texslot.use_map_color_diffuse and \
                             not mesh_base_mtex:

                            mesh_base_mtex = b_mat_texslot

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True

                                '''
                                # in this case, Blender replaces the texture transparant parts with the underlying material color...
                                # in NIF, material alpha is multiplied with texture alpha channel...
                                # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                                # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                                # but...

                                if mesh_mat_transparency > self.properties.epsilon:
                                    raise NifExportError(
                                        "Cannot export this type of"
                                        " transparency in material '%s': "
                                        " instead, try to set alpha to 0.0"
                                        " and to use the 'Var' slider"
                                        " in the 'Map To' tab under the"
                                        " material buttons."
                                        %mesh_material.name)
                                if (mesh_material.animation_data and mesh_material.animation_data.action.fcurves['Alpha']):
                                    raise NifExportError(
                                        "Cannot export animation for"
                                        " this type of transparency"
                                        " in material '%s':"
                                        " remove alpha animation,"
                                        " or turn off MapTo.ALPHA,"
                                        " and try again."
                                        %mesh_material.name)

                                mesh_mat_transparency = b_mat_texslot.varfac # we must use the "Var" value
                                '''

                        #normal map
                        elif b_mat_texslot.use_map_normal and b_mat_texslot.texture.use_normal_map:
                            if mesh_normal_mtex:
                                raise NifExportError(
                                    "Multiple bump/normal textures"
                                    " in mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.NOR"
                                    %(mesh.name,mesh_material.name))
                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            mesh_normal_mtex = b_mat_texslot

                        #detail
                        elif b_mat_texslot.use_map_color_diffuse and \
                             not mesh_detail_mtex:
                            # extra diffuse consider as detail texture

                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            mesh_detail_mtex = b_mat_texslot

                        #reflection
                        elif b_mat_texslot.mapto & Blender.Texture.MapTo.REF:
                            # got the reflection map
                            if mesh_ref_mtex:
                                raise NifExportError(
                                    "Multiple reflection textures"
                                    " in mesh '%s', material '%s'."
                                    " Make sure there is only one texture"
                                    " with MapTo.REF"
                                    %(mesh.name,mesh_material.name))
                            # check if alpha channel is enabled for this texture
                            if(b_mat_texslot.use_map_alpha):
                                mesh_hasalpha = True
                            mesh_ref_mtex = b_mat_texslot

                        # unsupported map
                        else:
                            raise NifExportError(
                                "Do not know how to export texture '%s',"
                                " in mesh '%s', material '%s'."
                                " Either delete it, or if this texture"
                                " is to be your base texture,"
                                " go to the Shading Panel,"
                                " Material Buttons, and set texture"
                                " 'Map To' to 'COL'."
                                % (b_mat_texslot.texture.name,b_obj.name,mesh_material.name))

                    # nif only support UV-mapped textures
                    else:
                        raise NifExportError(
                            "Non-UV texture in mesh '%s', material '%s'."
                            " Either delete all non-UV textures,"
                            " or in the Shading Panel,"
                            " under Material Buttons,"
                            " set texture 'Map Input' to 'UV'."
                            %(b_obj.name,mesh_material.name))

            # list of body part (name, index, vertices) in this mesh
            bodypartgroups = []
            for bodypartgroupname in NifFormat.BSDismemberBodyPartType().get_editor_keys():
                vertex_group = b_obj.vertex_groups.get(bodypartgroupname)
                if vertex_group:
                    self.debug("Found body part %s" % bodypartgroupname)
                    bodypartgroups.append(
                        [bodypartgroupname,
                         getattr(NifFormat.BSDismemberBodyPartType,
                                 bodypartgroupname),
                         # FIXME how do you get the vertices in the group???
                         #set(vertex_group.vertices)])
                         {}])

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

            vertquad_list = [] # (vertex, uv coordinate, normal, vertex color) list
            vertmap = [None for i in range(len(mesh.vertices))] # blender vertex -> nif vertices
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
                if (mesh_material != None): # we have a material
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
                    if not mesh.uv_textures:
                        raise NifExportError(
                            "ERROR%t|Create a UV map for every texture,"
                            " and run the script again.")
                # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
                f_index = [ -1 ] * f_numverts
                for i, fv_index in enumerate(f.vertices):
                    fv = mesh.vertices[fv_index].co
                    # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                    if mesh_hasnormals:
                        if f.use_smooth:
                            fn = mesh.vertices[fv_index].normal
                        else:
                            fn = f.normal
                    else:
                        fn = None
                    fuv = []
                    for uvlayer in mesh_uvlayers:
                        fuv.append(
                            getattr(mesh.uv_textures[uvlayer].data[f.index],
                                    "uv%i" % (i + 1)))

                    fcol = None

                    '''TODO: Need to map b_verts -> n_verts'''
                    if mesh_hasvcol:
                        vertcol = []
                        #check for an alpha layer
                        b_meshcolor = mesh.vertex_colors[0].data[f.index]
                        b_color = getattr(b_meshcolor, "color%s" % (i + 1))
                        if(mesh_hasvcola):
                            b_meshcoloralpha = mesh.vertex_colors[1].data[f.index]
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
                for face in mesh.faces:
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

            # note: we can be in any of the following five situations
            # material + base texture        -> normal object
            # material + base tex + glow tex -> normal glow mapped object
            # material + glow texture        -> (needs to be tested)
            # material, but no texture       -> uniformly coloured object
            # no material                    -> typically, collision mesh

            # create a trishape block
            if not self.properties.stripify:
                trishape = self.create_block("NiTriShape", b_obj)
            else:
                trishape = self.create_block("NiTriStrips", b_obj)

            # add texture effect block (must be added as preceeding child of
            # the trishape)
            if self.properties.game == 'MORROWIND' and mesh_texeff_mtex:
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
                trishape.name = b""
            elif not trishape_name:
                if parent_block.name:
                    trishape.name = b"Tri " + str(parent_block.name.decode()).encode()
                else:
                    trishape.name = b"Tri " + str(b_obj.name).encode()
            else:
                trishape.name = trishape_name.encode()

            if len(mesh_materials) > 1:
                # multimaterial meshes: add material index
                # (Morrowind's child naming convention)
                b_name = trishape.name.decode() + ":%i" % materialIndex
                trishape.name = b_name.encode()
            trishape.name = self.get_full_name(trishape.name.decode()).encode()

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

            self.export_matrix(b_obj, space, trishape)

            if mesh_base_mtex or mesh_glow_mtex:
                # add NiTriShape's texturing property
                if self.properties.game == 'FALLOUT_3':
                    trishape.add_property(self.export_bs_shader_property(
                        basemtex = mesh_base_mtex,
                        glowmtex = mesh_glow_mtex,
                        normalmtex = mesh_normal_mtex))
                        #glossmtex = mesh_gloss_mtex,
                        #darkmtex = mesh_dark_mtex,
                        #detailmtex = mesh_detail_mtex))
                else:
                    if self.properties.game in self.USED_EXTRA_SHADER_TEXTURES:
                        # sid meier's railroad and civ4:
                        # set shader slots in extra data
                        self.add_shader_integer_extra_datas(trishape)
                    trishape.add_property(self.export_texturing_property(
                        flags=0x0001, # standard
                        applymode=self.get_n_apply_mode_from_b_blend_type(
                            mesh_base_mtex.blend_type
                            if mesh_base_mtex else 'MIX'),
                        uvlayers=mesh_uvlayers,
                        basemtex=mesh_base_mtex,
                        glowmtex=mesh_glow_mtex,
                        bumpmtex=mesh_bump_mtex,
                        normalmtex=mesh_normal_mtex,
                        glossmtex=mesh_gloss_mtex,
                        darkmtex=mesh_dark_mtex,
                        detailmtex=mesh_detail_mtex,
                        refmtex=mesh_ref_mtex))

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
                    self.export_alpha_property(flags=alphaflags,
                                             threshold=alphathreshold))

            if mesh_haswire:
                # add NiWireframeProperty
                trishape.add_property(self.export_wireframe_property(flags=1))

            if mesh_doublesided:
                # add NiStencilProperty
                trishape.add_property(self.export_stencil_property())

            if mesh_material:
                # add NiTriShape's specular property
                # but NOT for sid meier's railroads and other extra shader
                # games (they use specularity even without this property)
                if (mesh_hasspec
                    and (self.properties.game
                         not in self.USED_EXTRA_SHADER_TEXTURES)):
                    # refer to the specular property in the trishape block
                    trishape.add_property(
                        self.export_specular_property(flags=0x0001))

                # add NiTriShape's material property
                trimatprop = self.export_material_property(
                    name=self.get_full_name(mesh_material.name),
                    flags=0x0001, # TODO - standard flag, check?
                    ambient=mesh_mat_ambient_color,
                    diffuse=mesh_mat_diffuse_color,
                    specular=mesh_mat_specular_color,
                    emissive=mesh_mat_emissive_color,
                    gloss=mesh_mat_gloss,
                    alpha=mesh_mat_transparency,
                    emitmulti=mesh_mat_emitmulti)

                # refer to the material property in the trishape block
                trishape.add_property(trimatprop)


                # material animation
                self.animationhelper.material_helper.export_material_controllers(
                    b_material=mesh_material, n_geom=trishape)

            # add NiTriShape's data
            # NIF flips the texture V-coordinate (OpenGL standard)
            if isinstance(trishape, NifFormat.NiTriShape):
                tridata = self.create_block("NiTriShapeData", b_obj)
            else:
                tridata = self.create_block("NiTriStripsData", b_obj)
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
                    or (self.properties.game in self.USED_EXTRA_SHADER_TEXTURES)):
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
                            skininst = self.create_block("BSDismemberSkinInstance", b_obj)
                        else:
                            skininst = self.create_block("NiSkinInstance", b_obj)
                        trishape.skin_instance = skininst
                        for block in self.blocks:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == self.get_full_name(armaturename).encode():
                                    skininst.skeleton_root = block
                                    break
                        else:
                            raise NifExportError(
                                "Skeleton root '%s' not found."
                                % armaturename)

                        # create skinning data and link it
                        skindata = self.create_block("NiSkinData", b_obj)
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
                            for v in mesh.vertices:
                                v.select = False    
                            
                            for b_vert in unassigned_verts:
                                b_obj.data.vertices[b_vert.index].select = True
                                
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
                            for block in self.blocks:
                                if isinstance(block, NifFormat.NiNode):
                                    if block.name == self.get_full_name(bone).encode():
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

                        if (self.version >= 0x04020100
                            and self.properties.skin_partition):
                            self.info("Creating skin partition")
                            lostweight = trishape.update_skin_partition(
                                maxbonesperpartition=self.properties.bones_per_partition,
                                maxbonespervertex=self.properties.bones_per_vertex,
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
                               if self.properties.bones_per_partition < 18:
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
            key = mesh.shape_keys
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
                                    mv.x -= mesh.vertices[b_v_index].co.x
                                    mv.y -= mesh.vertices[b_v_index].co.y
                                    mv.z -= mesh.vertices[b_v_index].co.z
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
                            if self.properties.animation == 'GEOM_NIF' or not curve:
                                continue

                            # note: we set data on morph for older nifs
                            # and on floatdata for newer nifs
                            # of course only one of these will be actually
                            # written to the file
                            self.info("Exporting morph %s: curve"
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



    

    

   

    def export_matrix(self, b_obj, space, block):
        """Set a block's transform matrix to an object's
        transformation matrix in rest pose."""
        # decompose
        n_scale, n_rot_mat33, n_trans_vec = self.get_object_srt(b_obj, space)

        # and fill in the values
        block.translation.x = n_trans_vec[0]
        block.translation.y = n_trans_vec[1]
        block.translation.z = n_trans_vec[2]
        block.rotation.m_11 = n_rot_mat33[0][0]
        block.rotation.m_21 = n_rot_mat33[0][1]
        block.rotation.m_31 = n_rot_mat33[0][2]
        block.rotation.m_12 = n_rot_mat33[1][0]
        block.rotation.m_22 = n_rot_mat33[1][1]
        block.rotation.m_32 = n_rot_mat33[1][2]
        block.rotation.m_13 = n_rot_mat33[2][0]
        block.rotation.m_23 = n_rot_mat33[2][1]
        block.rotation.m_33 = n_rot_mat33[2][2]
        block.velocity.x = 0.0
        block.velocity.y = 0.0
        block.velocity.z = 0.0
        block.scale = n_scale

        return n_scale, n_rot_mat33, n_trans_vec

    def get_object_matrix(self, b_obj, space):
        """Get an object's matrix as NifFormat.Matrix44

        Note: for objects parented to bones, this will return the transform
        relative to the bone parent head in nif coordinates (that is, including
        the bone correction); this differs from getMatrix which
        returns the transform relative to the armature."""
        n_scale, n_rot_mat33, n_trans_vec = self.get_object_srt(b_obj, space)
        matrix = NifFormat.Matrix44()

        matrix.m_11 = n_rot_mat33[0][0] * n_scale
        matrix.m_21 = n_rot_mat33[0][1] * n_scale
        matrix.m_31 = n_rot_mat33[0][2] * n_scale
        matrix.m_12 = n_rot_mat33[1][0] * n_scale
        matrix.m_22 = n_rot_mat33[1][1] * n_scale
        matrix.m_32 = n_rot_mat33[1][2] * n_scale
        matrix.m_13 = n_rot_mat33[2][0] * n_scale
        matrix.m_23 = n_rot_mat33[2][1] * n_scale
        matrix.m_33 = n_rot_mat33[2][2] * n_scale
        matrix.m_14 = n_trans_vec[0]
        matrix.m_24 = n_trans_vec[1]
        matrix.m_34 = n_trans_vec[2]

        matrix.m_41 = 0.0
        matrix.m_42 = 0.0
        matrix.m_43 = 0.0
        matrix.m_44 = 1.0

        return matrix

    def get_object_srt(self, b_obj, space = 'localspace'):
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
                     mathutils.Matrix([[1,0,0],[0,1,0],[0,0,1]]),
                     mathutils.Vector([0, 0, 0]) )

        assert(space == 'localspace')

        # now write out spaces
        if not isinstance(b_obj, bpy.types.Bone):
            matrix = b_obj.matrix_local.copy()
            bone_parent_name = b_obj.parent_bone
            # if there is a bone parent then the object is parented
            # then get the matrix relative to the bone parent head
            if bone_parent_name:
                # so v * O * T * B' = v * Z * B
                # where B' is the Blender bone matrix in armature
                # space, T is the bone tail translation, O is the object
                # matrix (relative to the head), and B is the nif bone matrix;
                # we wish to find Z

                # b_obj.getMatrix('localspace')
                # gets the object local transform matrix, relative
                # to the armature!! (not relative to the bone)
                # so at this point, matrix = O * T * B'
                # hence it must hold that matrix = Z * B,
                # or equivalently Z = matrix * B^{-1}

                # now, B' = X * B, so B^{-1} = B'^{-1} * X
                # hence Z = matrix * B'^{-1} * X

                # first multiply with inverse of the Blender bone matrix
                bone_parent = b_obj.parent.data.bones[
                    bone_parent_name]
                boneinv = mathutils.Matrix(
                    bone_parent.matrix['ARMATURESPACE'])
                boneinv.invert()
                matrix = matrix * boneinv
                # now multiply with the bone correction matrix X
                try:
                    extra = mathutils.Matrix(
                        self.get_bone_extra_matrix_inv(bone_parent_name))
                    extra.invert()
                    matrix = matrix * extra
                except KeyError:
                    # no extra local transform
                    pass
        else:
            # bones, get the rest matrix
            matrix = self.armaturehelper.get_bone_rest_matrix(b_obj, 'BONESPACE')

        try:
            return self.decompose_srt(matrix)
        except NifExportError: # non-uniform scaling
            self.debug(str(matrix))
            raise NifExportError(
                "Non-uniform scaling on bone '%s' not supported."
                " This could be a bug... No workaround. :-( Post your blend!"
                % b_obj.name)


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
            self.info("Exporting %s block"%block.__class__.__name__)
        else:
            self.info("Exporting %s as %s block"
                     % (b_obj, block.__class__.__name__))
        self.blocks[block] = b_obj
        return block

        #Aaron1178 collision export stuff
        '''
            def export_bsx_upb_flags(self, b_obj, parent_block):
                """Gets BSXFlags prop and creates BSXFlags node

                @param b_obj: The blender Object
                @param parent_block: The nif parent block
                """

                if not b_obj.nifcollision.bsxFlags or not b_obj.nifcollision.upb:
                    return

                bsxNode = self.create_block("BSXFlags", b_obj)
                bsxNode.name = "BSX"
                bsxNode.integer_data = b_obj.nifcollision.bsxFlags
                parent_block.add_extra_data(bsxNode)

                upbNode = self.create_block("NiStringExtraData", b_obj)
                upbNode.name = "UPB"
                upbNode.string_data = b_obj.nifcollision.upb
                parent_block.add_extra_data(upbNode)
        '''

    def export_collision(self, b_obj, parent_block):
        """Main function for adding collision object b_obj to a node."""
        if self.properties.game == 'MORROWIND':
             if b_obj.game.collision_bounds_type != 'TRIANGLE_MESH':
                 raise NifExportError(
                     "Morrowind only supports"
                     " Triangle Mesh collisions.")
             node = self.create_block("RootCollisionNode", b_obj)
             parent_block.add_child(node)
             node.flags = 0x0003 # default
             self.export_matrix(b_obj, 'localspace', node)
             self.export_tri_shapes(b_obj, 'none', node)

        elif self.properties.game in ('OBLIVION', 'FALLOUT_3'):

            nodes = [ parent_block ]
            nodes.extend([ block for block in parent_block.children
                           if block.name[:14] == 'collisiondummy' ])
            for node in nodes:
                try:
                    self.bhkshapehelper.export_collision_helper(b_obj, node)
                    break
                except ValueError: # adding collision failed
                    continue
            else: # all nodes failed so add new one
                node = self.create_ninode(b_obj)
                node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy%i' % parent_block.num_children
                node.flags = 0x000E # default
                parent_block.add_child(node)
                self.bhkshapehelper.export_collision_helper(b_obj, node)

        else:
            self.warning(
                "Only Morrowind, Oblivion, and Fallout 3"
                " collisions are supported, skipped collision object '%s'"
                % b_obj.name)

    
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

        # no wire property with given flag found, so create new one
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
        if self.properties.game == 'FALLOUT_3':
            stencilprop.flags = 19840
        return stencilprop

    def export_material_property(self, name='', flags=0x0001,
                                 ambient=(1.0, 1.0, 1.0), diffuse=(1.0, 1.0, 1.0),
                                 specular=(0.0, 0.0, 0.0), emissive=(0.0, 0.0, 0.0),
                                 gloss=10.0, alpha=1.0, emitmulti=1.0):
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
        if self.properties.game in ('OBLIVION', 'FALLOUT_3'):
            for specialname in specialnames:
                if (name.lower() == specialname.lower()
                    or name.lower().startswith(specialname.lower() + ".")):
                    if name != specialname:
                        self.warning("Renaming material '%s' to '%s'"
                                            % (name, specialname))
                    name = specialname

        # clear noname materials
        if name.lower().startswith("noname"):
            self.warning("Renaming material '%s' to ''" % name)
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
        matprop.glossiness = gloss
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
                self.warning(
                    "Merging materials '%s' and '%s'"
                    " (they are identical in nif)"
                    % (matprop.name, block.name))
                return block

        # no material property with given settings found, so use and register
        # the new one
        return self.register_block(matprop)

    def export_tex_desc(self, texdesc=None, uvlayers=None, b_mat_texslot=None):
        """Helper function for export_texturing_property to export each texture
        slot."""
        try:
            texdesc.uv_set = uvlayers.index(b_mat_texslot.uv_layer) if b_mat_texslot.uv_layer else 0
        except ValueError: # mtex.uv_layer not in uvlayers list
            self.warning(
                "Bad uv layer name '%s' in texture '%s'."
                " Falling back on first uv layer"
                % (b_mat_texslot.uv_layer, b_mat_texslot.texture.name))
            texdesc.uv_set = 0 # assume 0 is active layer

        texdesc.source = self.export_source_texture(b_mat_texslot.texture)

    def export_texturing_property(
        self, flags=0x0001, applymode=None, uvlayers=None,
        basemtex=None, glowmtex=None, bumpmtex=None, normalmtex=None, glossmtex=None,
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

        # export extra shader textures
        if self.properties.game == 'SID_MEIER_S_RAILROADS':
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

        elif self.properties.game == 'CIVILIZATION_IV':
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
                                 b_mat_texslot = basemtex)
            # check for texture flip definition
            try:
                fliptxt = Blender.Text.Get(basemtex.texture.name)
            except NameError:
                pass
            else:
                # texture slot 0 = base
                self.animationhelper.texture_animation.export_flip_controller(fliptxt, basemtex.texture, texprop, 0)

        if glowmtex:
            texprop.has_glow_texture = True
            self.export_tex_desc(texdesc = texprop.glow_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = glowmtex)

        if bumpmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_bump_map_texture = True
                self.export_tex_desc(texdesc = texprop.bump_map_texture,
                                     uvlayers = uvlayers,
                                     b_mat_texslot = bumpmtex)
                texprop.bump_map_luma_scale = 1.0
                texprop.bump_map_luma_offset = 0.0
                texprop.bump_map_matrix.m_11 = 1.0
                texprop.bump_map_matrix.m_12 = 0.0
                texprop.bump_map_matrix.m_21 = 0.0
                texprop.bump_map_matrix.m_22 = 1.0

        if normalmtex:
                shadertexdesc = texprop.shader_textures[1]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=normalmtex.texture)

        if glossmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                texprop.has_gloss_texture = True
                self.export_tex_desc(texdesc = texprop.gloss_texture,
                                     uvlayers = uvlayers,
                                     b_mat_texslot = glossmtex)
            else:
                shadertexdesc = texprop.shader_textures[2]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=glossmtex.texture)

        if darkmtex:
            texprop.has_dark_texture = True
            self.export_tex_desc(texdesc = texprop.dark_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = darkmtex)

        if detailmtex:
            texprop.has_detail_texture = True
            self.export_tex_desc(texdesc = texprop.detail_texture,
                                 uvlayers = uvlayers,
                                 b_mat_texslot = detailmtex)

        if refmtex:
            if self.properties.game not in self.USED_EXTRA_SHADER_TEXTURES:
                self.warning(
                    "Cannot export reflection texture for this game.")
                #texprop.hasRefTexture = True
                #self.export_tex_desc(texdesc = texprop.refTexture,
                #                     uvlayers = uvlayers,
                #                     mtex = refmtex)
            else:
                shadertexdesc = texprop.shader_textures[3]
                shadertexdesc.is_used = True
                shadertexdesc.texture_data.source = \
                    self.export_source_texture(texture=refmtex.texture)

        # search for duplicate
        for block in self.blocks:
            if isinstance(block, NifFormat.NiTexturingProperty) \
               and block.get_hash() == texprop.get_hash():
                return block

        # no texturing property with given settings found, so use and register
        # the new one
        return self.register_block(texprop)

    def export_bs_shader_property(
        self, basemtex=None, normalmtex=None, glowmtex=None):
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
            texset.textures[0] = self.export_texture_filename(basemtex.texture)
        if normalmtex:
            texset.textures[1] = self.export_texture_filename(normalmtex.texture)
        if glowmtex:
            texset.textures[2] = self.export_texture_filename(glowmtex.texture)

        # search for duplicates
        # DISABLED: the Fallout 3 engine cannot handle them
        #for block in self.blocks:
        #    if (isinstance(block, NifFormat.BSShaderPPLightingProperty)
        #        and block.get_hash() == bsshader.get_hash()):
        #        return block

        # no duplicate found, so use and register new one
        return self.register_block(bsshader)

    def export_texture_effect(self, b_mat_texslot = None):
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
        if b_mat_texslot:
            texeff.source_texture = self.export_source_texture(b_mat_texslot.texture)
            if self.properties.game == 'MORROWIND':
                texeff.num_affected_node_list_pointers += 1
                texeff.affected_node_list_pointers.update_size()
        texeff.unknown_vector.x = 1.0
        return self.register_block(texeff)

    def add_shader_integer_extra_datas(self, trishape):
        """Add extra data blocks for shader indices."""
        for shaderindex in self.USED_EXTRA_SHADER_TEXTURES[self.properties.game]:
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

    def exportEgm(self, keyblocks):
        self.egmdata = EgmFormat.Data(num_vertices=len(keyblocks[0].data))
        for keyblock in keyblocks:
            if keyblock.name.startswith("EGM SYM"):
                morph = self.egmdata.add_sym_morph()
            elif keyblock.name.startswith("EGM ASYM"):
                morph = self.egmdata.add_asym_morph()
            else:
                continue
            self.info("Exporting morph %s to egm" % keyblock.name)
            relative_vertices = []
            # note: keyblocks[0] is base key
            for vert, key_vert in zip(keyblocks[0].data, keyblock.data):
                relative_vertices.append(key_vert - vert)
            morph.set_relative_vertices(relative_vertices)

def menu_func(self, context):
    """Export operator for the menu."""
    # TODO get default path from config registry
    #default_path = bpy.data.filename.replace(".blend", ".nif")
    default_path = "export.nif"
    self.layout.operator(
        NifExport.bl_idname,
        text="NetImmerse/Gamebryo (.nif & .kf & .egm)"
        ).filepath = default_path

def register():
    """Register nif export operator."""
    bpy.types.register(NifExport)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    """Unregister nif export operator."""
    bpy.types.unregister(NifExport)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == '__main__':
    """Register nif import, when starting Blender."""
    register()
