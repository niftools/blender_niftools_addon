'''Script to import/export constraints.'''

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

import pyffi
from pyffi.formats.nif import NifFormat

import bpy
import mathutils

class Constraint():

    def __init__(self, parent):
        self.nif_common = parent
        self.havok_objects = {}
        
    def set_havok_objects(self, havok_dict):
        self.havok_objects = havok_dict
    
    def import_bhk_constraints(self):
        for hkbody in self.havok_objects:
            self.import_constraint(hkbody)
        
    def import_constraint(self, hkbody):
        """Imports a bone havok constraint as Blender object constraint."""
        assert(isinstance(hkbody, NifFormat.bhkRigidBody))

        # check for constraints
        if not hkbody.constraints:
            return

        # find objects
        if len(self.havok_objects[hkbody]) != 1:
            self.nif_common.warning(
                "Rigid body with no or multiple shapes, constraints skipped")
            return

        b_hkobj = self.havok_objects[hkbody][0]

        self.nif_common.info("Importing constraints for %s" % b_hkobj.name)

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
                    self.nif_common.warning("Unknown malleable type (%i), skipped"
                                        % hkconstraint.type)
                # extra malleable constraint settings
                ### damping parameters not yet in Blender Python API
                ### tau (force between bodies) not supported by Blender
            else:
                self.nif_common.warning("Unknown constraint type (%s), skipped"
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
                        self.nif_common.warning(
                            "Axes are not orthogonal in %s;"
                            " arbitrary orientation has been chosen"
                            % hkdescriptor.__class__.__name__)
                        axis_z = mathutils.CrossVecs(axis_x, axis_y)
                    else:
                        # fix orientation
                        self.nif_common.warning(
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
            for niBone in self.nif_common.armaturehelper.bones_extra_matrix:
                if niBone.collision_object \
                   and niBone.collision_object.body is hkbody:
                    transform = mathutils.Matrix(
                        self.nif_common.armaturehelper.bones_extra_matrix[niBone])
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

