"""This script exports Netimmerse and Gamebryo .nif files from Blender."""

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

from io_scene_nif.animationsys.animation_export import AnimationHelper
from io_scene_nif.collisionsys.collision_export import bhkshape_export, bound_export
from io_scene_nif.armaturesys.armature_export import Armature
from io_scene_nif.propertysys.property_export import PropertyHelper
from io_scene_nif.constraintsys.constraint_export import constraint_export
from io_scene_nif.texturesys.texture_export import TextureHelper
from io_scene_nif.objectsys.object_export import ObjectHelper

import os.path

import mathutils
import bpy

import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat
from pyffi.formats.egm import EgmFormat

# main export class
class NifExport(NifCommon):


    IDENTITY44 = NifFormat.Matrix44()
    IDENTITY44.set_identity()
    FLOAT_MIN = -3.4028234663852886e+38
    FLOAT_MAX = +3.4028234663852886e+38
    
    # TODO: - Expose via properties
    
    EXPORT_OPTIMIZE_MATERIALS = True
    EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES = False
    
    EXPORT_BHKLISTSHAPE = False
    EXPORT_OB_BSXFLAGS = 2
    EXPORT_OB_MASS = 10.0
    EXPORT_OB_SOLID = True
    EXPORT_OB_MOTIONSYSTEM = 7, # MO_SYS_FIXED
    EXPORT_OB_UNKNOWNBYTE1 = 1
    EXPORT_OB_UNKNOWNBYTE2 = 1
    EXPORT_OB_QUALITYTYPE = 1 # MO_QUAL_FIXED
    EXPORT_OB_WIND = 0
    EXPORT_OB_LAYER = 1 # static
    EXPORT_OB_MATERIAL = 9 # wood
    EXPORT_OB_PRN = "NONE" # Todo with location on character. For weapons, rings, helmets, Sheilds ect
    

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)
    
        # Helper systems
        self.bhkshapehelper = bhkshape_export(parent=self)
        self.boundhelper = bound_export(parent=self)
        self.armaturehelper = Armature(parent=self)
        self.animationhelper = AnimationHelper(parent=self)
        self.propertyhelper = PropertyHelper(parent=self)
        self.constrainthelper = constraint_export(parent=self)
        self.texturehelper = TextureHelper(parent=self)
        self.objecthelper = ObjectHelper(parent=self)
        
    def execute(self):
        """Main export function."""
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        self.info("exporting {0}".format(self.properties.filepath))

        # TODO:
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

        self.dict_armatures = {}
        self.dict_bones_extra_matrix = {}
        self.dict_bones_extra_matrix_inv = {}
        self.dict_bone_priorities = {}
        self.dict_havok_objects = {}
        self.dict_names = {}
        self.dict_blocks = {}
        self.dict_block_names = []
        self.dict_materials = {}
        self.dict_textures = {}
        self.dict_mesh_uvlayers = []
        
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


                if b_obj.type == 'MESH':
                    b_armature_modifier = None
                    b_obj_name = b_obj.name
                    if b_obj.parent:
                        for b_mod in bpy.data.objects[b_obj_name].modifiers:
                            if b_mod.type == 'ARMATURE':
                                b_armature_modifier = b_mod.name
                                if b_mod.use_bone_envelopes:
                                    raise nif_utils.NifError(
                                            "'%s': Cannot export envelope skinning."
                                            " If you have vertex groups,"
                                            " turn off envelopes. If you don't have vertex"
                                            " groups, select the bones one by one press W"
                                            " to convert their envelopes to vertex weights,"
                                            " and turn off envelopes."
                                            % b_obj.name)
                        if not b_armature_modifier:
                            raise nif_utils.NifError(
                                    "'%s': is parented but does not have"
                                    " the armature modifier set. This will"
                                    " cause animations to fail."
                                    % b_obj.name)

                # check for non-uniform transforms
                # (lattices are not exported so ignore them as they often tend
                # to have non-uniform scaling)
                if b_obj.type != 'LATTICE':
                    scale = b_obj.matrix_local.to_scale()
                    if (abs(scale.x - scale.y) > self.properties.epsilon
                        or abs(scale.y - scale.z) > self.properties.epsilon):

                        raise nif_utils.NifError(
                            "Non-uniform scaling not supported."
                            " Workaround: apply size and rotation (CTRL-A)"
                            " on '%s'." % b_obj.name)

            root_name = filebase
            # get the root object from selected object
            # only export empties, meshes, and armatures
            if not self.context.selected_objects:
                raise nif_utils.NifError(
                    "Please select the object(s) to export,"
                    " and run this script again.")
            root_objects = set()
            export_types = ('EMPTY', 'MESH', 'ARMATURE')
            for root_object in [b_obj for b_obj in self.context.selected_objects
                                if b_obj.type in export_types]:
                while root_object.parent:
                    root_object = root_object.parent
                if (self.properties.game
                    in ('CIVILIZATION_IV', 'OBLIVION', 'FALLOUT_3')):
                    if (root_object.type == 'ARMATURE') or (root_object.name.lower() == "bip01"):
                        root_name = 'Scene Root'
                if root_object.type not in export_types:
                    raise nif_utils.NifError(
                        "Root object (%s) must be an 'EMPTY', 'MESH',"
                        " or 'ARMATURE' object."
                        % root_object.name)
                root_objects.add(root_object)

            # version checking to help avoid errors
            # due to invalid settings
            b_scene = bpy.context.scene
            nif_ver_hex = b_scene.niftools.nif_version
            for gname in NifFormat.games:
                gname_trans = self.get_game_to_trans(gname)
                if gname_trans == self.properties.game:
                    if nif_ver_hex not in NifFormat.games[gname]:
                        raise nif_utils.NifError(
                        "Version for export not found: %s"
                        % str(nif_ver_hex))
                    break

            # smoothen seams of objects
            if self.properties.smooth_object_seams:
                self.objecthelper.mesh_helper.smooth_mesh_seams(self.context.scene.objects)
                
                
            # TODO: use Blender actions for animation groups
            # check for animation groups definition in a text buffer 'Anim'
            try:
                animtxt = None #Changed for testing needs fix bpy.data.texts["Anim"]
            except NameError:
                animtxt = None

            # rebuild the bone extra matrix dictionary from the 'BoneExMat' text buffer
            self.armaturehelper.rebuild_bones_extra_matrices()

            # rebuild the full name dictionary from the 'FullNames' text buffer
            self.objecthelper.rebuild_full_names()

            # export nif:
            # -----------
            self.info("Exporting")

            # create a nif object

            # export the root node (the name is fixed later to avoid confusing the
            # exporter with duplicate names)
            root_block = self.objecthelper.export_node(None, 'none', None, '')

            # export objects
            self.info("Exporting objects")
            for root_object in root_objects:
                if self.properties.game in ('SKYRIM'):
                    if root_object.niftools_bs_invmarker:
                        for extra_item in root_block.extra_data_list:
                            if isinstance(extra_item, NifFormat.BSInvMarker):
                                raise nif_utils.NifError(
                                    "Multiple Items have Inventory marker data"
                                    " only one item may contain this data")
                        else:
                            n_extra_list = NifFormat.BSInvMarker()
                            n_extra_list.name = root_object.niftools_bs_invmarker[0].name.encode()
                            n_extra_list.rotation_x = root_object.niftools_bs_invmarker[0].bs_inv_x
                            n_extra_list.rotation_y = root_object.niftools_bs_invmarker[0].bs_inv_y
                            n_extra_list.rotation_z = root_object.niftools_bs_invmarker[0].bs_inv_z
                            n_extra_list.zoom = root_object.niftools_bs_invmarker[0].bs_inv_zoom
                             
                            root_block.add_extra_data(n_extra_list)
                    
                    
                # export the root objects as a NiNodes; their children are
                # exported as well
                # note that localspace = worldspace, because root objects have
                # no parents
                self.objecthelper.export_node(root_object, 'localspace',
                                 root_block, root_object.name)

            # post-processing:
            # ----------------

            # if we exported animations, but no animation groups are defined,
            # define a default animation group
            self.info("Checking animation groups")
            if not animtxt:
                has_controllers = False
                for block in self.dict_blocks:
                    # has it a controller field?
                    if isinstance(block, NifFormat.NiObjectNET):
                        if block.controller:
                            has_controllers = True
                            break
                if has_controllers:
                    self.info("Defining default animation group.")
                    # write the animation group text buffer
                    animtxt = bpy.data.texts.new("Anim")
                    animtxt.write("%i/Idle: Start/Idle: Loop Start\n%i/Idle: Loop Stop/Idle: Stop" %
                                  (self.context.scene.frame_start, self.context.scene.frame_end))

            # animations without keyframe animations crash the TESCS
            # if we are in that situation, add a trivial keyframe animation
            self.info("Checking controllers")
            if animtxt and self.properties.game == 'MORROWIND':
                has_keyframecontrollers = False
                for block in self.dict_blocks:
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
                for block in self.dict_blocks:
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
            if self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM') \
                and filebase.lower() in ('skeleton', 'skeletonbeast'):
                # here comes everything that is Oblivion skeleton export
                # specific
                self.info(
                    "Adding controllers and interpolators for skeleton")
                for block in list(self.dict_blocks.keys()):
                    if isinstance(block, NifFormat.NiNode) \
                        and block.name.decode() == "Bip01":
                        for bone in block.tree(block_type = NifFormat.NiNode):
                            ctrl = self.objecthelper.create_block("NiTransformController")
                            interp = self.objecthelper.create_block("NiTransformInterpolator")

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
                    # TODO: removed temorarily to process bseffectshader export
                    anim_textextra = None #self.animationhelper.export_anim_groups(animtxt, root_block)
                else:
                    anim_textextra = None

            # oblivion and Fallout 3 furniture markers
            if (self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM')
                and filebase[:15].lower() == 'furnituremarker'):
                # exporting a furniture marker for Oblivion/FO3
                try:
                    furniturenumber = int(filebase[15:])
                except ValueError:
                    raise nif_utils.NifError(
                        "Furniture marker has invalid number (%s)."
                        " Name your file 'furnituremarkerxx.nif'"
                        " where xx is a number between 00 and 19."
                        % filebase[15:])
                # name scene root name the file base name
                root_name = filebase

                # create furniture marker block
                furnmark = self.objecthelper.create_block("BSFurnitureMarker")
                furnmark.name = "FRN"
                furnmark.num_positions = 1
                furnmark.positions.update_size()
                furnmark.positions[0].position_ref_1 = furniturenumber
                furnmark.positions[0].position_ref_2 = furniturenumber

                # create extra string data sgoKeep
                sgokeep = self.objecthelper.create_block("NiStringExtraData")
                sgokeep.name = "UPB" # user property buffer
                sgokeep.string_data = "sgoKeep=1 ExportSel = Yes" # Unyielding = 0, sgoKeep=1ExportSel = Yes

                # add extra blocks
                root_block.add_extra_data(furnmark)
                root_block.add_extra_data(sgokeep)

            # FIXME:
            self.info("Checking collision")
            # activate oblivion/Fallout 3 collision and physics
            if self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                hascollision = False
                for b_obj in bpy.data.objects:
                    if b_obj.game.use_collision_bounds == True:
                        hascollision = True
                        break
                if hascollision:
                    # enable collision
                    bsx = self.objecthelper.create_block("BSXFlags")
                    bsx.name = 'BSX'
                    bsx.integer_data = b_obj.niftools.bsxflags
                    root_block.add_extra_data(bsx)

                    # many Oblivion nifs have a UPB, but export is disabled as
                    # they do not seem to affect anything in the game
                    if b_obj.niftools.upb:
                        upb = self.objecthelper.create_block("NiStringExtraData")
                        upb.name = 'UPB'
                        if(b_obj.niftools.upb == ''):
                            upb.string_data = 'Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n'
                        else:
                            upb.string_data = b_obj.niftools.upb.encode()
                        root_block.add_extra_data(upb)

                # update rigid body center of gravity and mass
                if self.EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES:
                    # we are not using blender properties to set the mass
                    # so calculate mass automatically
                    # first calculate distribution of mass
                    total_mass = 0
                    for block in self.dict_blocks:
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
                    for block in self.dict_blocks:
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
                    for block in self.dict_blocks:
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
            # note: self.dict_blocks changes during iteration, so need list copy
            for block in list(self.dict_blocks):
                if isinstance(block, NifFormat.bhkListShape):
                    for i, sub_shape in enumerate(block.sub_shapes):
                        if isinstance(sub_shape, NifFormat.bhkConvexVerticesShape):
                            coltf = self.objecthelper.create_block("bhkConvexTransformShape")
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
            for b_obj in self.objecthelper.get_exported_objects():
                if isinstance(b_obj, bpy.types.Object) and b_obj.constraints:
                    self.constrainthelper.export_constraints(b_obj, root_block)

            # export weapon location
            if self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                if self.EXPORT_OB_PRN != "NONE":
                    # add string extra data
                    prn = self.objecthelper.create_block("NiStringExtraData")
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

            # FIXME:
            """
            if self.EXPORT_FLATTENSKIN:
                # (warning: trouble if armatures parent other armatures or
                # if bones parent geometries, or if object is animated)
                # flatten skins
                skelroots = set()
                affectedbones = []
                for block in self.dict_blocks:
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
            if abs(self.properties.scale_correction_export) > self.properties.epsilon:
                self.info("Applying scale correction %f"
                                 % self.properties.scale_correction_export)
                data = NifFormat.Data()
                data.roots = [root_block]
                toaster = pyffi.spells.nif.NifToaster()
                toaster.scale = self.properties.scale_correction_export
                pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()
                # also scale egm
                if self.egmdata:
                    self.egmdata.apply_scale(self.properties.scale_correction_export)

            # generate mopps (must be done after applying scale!)
            if self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                for block in self.dict_blocks:
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
                # remove root_block from self.dict_blocks
                self.dict_blocks.pop(root_block)
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
                
            self.root_ninode = None
            for root_obj in root_objects:
                if root_obj.niftools.rootnode == 'BSFadeNode':
                    self.root_ninode = 'BSFadeNode'
                elif self.root_ninode == None:
                    self.root_ninode = 'NiNode'
            # making root block a fade node
            if (self.properties.game in ('FALLOUT_3', 'SKYRIM') and self.root_ninode == 'BSFadeNode'):
                self.info("Making root block a BSFadeNode")
                fade_root_block = NifFormat.BSFadeNode().deepcopy(root_block)
                fade_root_block.replace_global_node(root_block, fade_root_block)
                root_block = fade_root_block

            # set user version and user version 2 for export
            b_scene = bpy.context.scene

            if b_scene.niftools.user_version == 0:
                if self.properties.game == 'OBLIVION':
                    NIF_USER_VERSION = 11
                elif self.properties.game == 'FALLOUT_3':
                    NIF_USER_VERSION = 11
                elif self.properties.game == 'DIVINITY_2':
                    NIF_USER_VERSION = 131072
                else:
                    NIF_USER_VERSION = 0
            else:
                NIF_USER_VERSION = b_scene.niftools.user_version
                    
            if b_scene.niftools.user_version_2 == 0:
                if self.properties.game == 'OBLIVION':
                    NIF_USER_VERSION_2 = 11
                elif self.properties.game == 'FALLOUT_3':
                    NIF_USER_VERSION_2 = 34
                else:
                    NIF_USER_VERSION_2 = 0
            else:
                NIF_USER_VERSION_2 = b_scene.niftools.user_version_2

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
                                      user_version_2=NIF_USER_VERSION_2)
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
                    kf_root = self.objecthelper.create_block("NiSequenceStreamHelper")
                    kf_root.add_extra_data(anim_textextra)
                    # reparent controller tree
                    for node, ctrls in node_kfctrls.items():
                        for ctrl in ctrls:
                            # create node reference by name
                            nodename_extra = self.objecthelper.create_block(
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
                    kf_root = self.objecthelper.create_block("NiControllerSequence")
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
                                if not node.name in self.dict_bone_priorities or self.EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES:
                                    if self.EXPORT_ANIMPRIORITY != 0:
                                        priority = self.EXPORT_ANIMPRIORITY
                                    else:
                                        priority = 26
                                        self.warning(
                                            "No priority set for bone %s, "
                                            "falling back on default value (%i)"
                                            % (node.name, priority))
                                else:
                                    priority = self.dict_bone_priorities[node.name]
                                controlledblock.priority = priority
                                # set palette, and node and controller type
                                # names, and variables
                                controlledblock.string_palette = kf_root.string_palette
                                controlledblock.set_node_name(node.name)
                                controlledblock.set_controller_type(ctrl.__class__.__name__)
                                if variable_2:
                                    controlledblock.set_variable_2(variable_2)
                else:
                    raise nif_utils.NifError(
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
                                      user_version_2=NIF_USER_VERSION_2)
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
                                      user_version_2=NIF_USER_VERSION_2)
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
        # TODO: remove the space argument, always do local space
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
                        self.armaturehelper.get_bone_extra_matrix_inv(bone_parent_name))
                    extra.invert()
                    matrix = matrix * extra
                except KeyError:
                    # no extra local transform
                    pass
        else:
            # bones, get the rest matrix
            matrix = self.armaturehelper.get_bone_rest_matrix(b_obj, 'BONESPACE')

        try:
            return nif_utils.decompose_srt(matrix)
        except nif_utils.NifError: # non-uniform scaling
            self.debug(str(matrix))
            raise nif_utils.NifError(
                "Non-uniform scaling on bone '%s' not supported."
                " This could be a bug... No workaround. :-( Post your blend!"
                % b_obj.name)


    def export_collision(self, b_obj, parent_block):
        """Main function for adding collision object b_obj to a node."""
        if self.properties.game == 'MORROWIND':
            if b_obj.game.collision_bounds_type != 'TRIANGLE_MESH':
                raise nif_utils.NifError(
                     "Morrowind only supports"
                     " Triangle Mesh collisions.")
            node = self.objecthelper.create_block("RootCollisionNode", b_obj)
            parent_block.add_child(node)
            node.flags = 0x0003 # default
            self.export_matrix(b_obj, 'localspace', node)
            self.objecthelper.mesh_helper.export_tri_shapes(b_obj, 'none', node)

        elif self.properties.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):

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
                node = self.objecthelper.create_ninode(b_obj)
                node.set_transform(self.IDENTITY44)
                node.name = 'collisiondummy%i' % parent_block.num_children
                if b_obj.niftools.objectflags != 0:
                    node_flag_hex = hex(b_obj.niftools.objectflags)
                else:
                    node_flag_hex = 0x000E # default
                node.flags = node_flag_hex
                parent_block.add_child(node)
                self.bhkshapehelper.export_collision_helper(b_obj, node)

        else:
            self.warning(
                "Only Morrowind, Oblivion, and Fallout 3"
                " collisions are supported, skipped collision object '%s'"
                % b_obj.name)
            
    
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
    # TODO: get default path from config registry
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

