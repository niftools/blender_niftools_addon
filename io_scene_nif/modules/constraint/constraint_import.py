"""Script to import/export constraints."""

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

from pyffi.formats.nif import NifFormat

import mathutils

from io_scene_nif.modules import collision, armature
from io_scene_nif.utility.nif_logging import NifLog


class Constraint():

    def __init__(self):
        self.HAVOK_SCALE = collision.HAVOK_SCALE

    def import_bhk_constraints(self):
        for hkbody in collision.DICT_HAVOK_OBJECTS:
            self.import_constraint(hkbody)

    def import_constraint(self, hkbody):
        """Imports a bone havok constraint as Blender object constraint."""
        assert (isinstance(hkbody, NifFormat.bhkRigidBody))

        # check for constraints
        if not hkbody.constraints:
            return

        # find objects
        if len(collision.DICT_HAVOK_OBJECTS[hkbody]) != 1:
            NifLog.warn("Rigid body with no or multiple shapes, constraints skipped")
            return

        b_hkobj = collision.DICT_HAVOK_OBJECTS[hkbody][0]

        NifLog.info("Importing constraints for %s" % b_hkobj.name)

        # now import all constraints
        for hkconstraint in hkbody.constraints:

            # check constraint entities
            if not hkconstraint.num_entities == 2:
                NifLog.warn("Constraint with more than 2 entities, skipped")
                continue
            if not hkconstraint.entities[0] is hkbody:
                NifLog.warn("First constraint entity not self, skipped")
                continue
            if not hkconstraint.entities[1] in collision.DICT_HAVOK_OBJECTS:
                NifLog.warn("Second constraint entity not imported, skipped")
                continue

            # get constraint descriptor
            if isinstance(hkconstraint, NifFormat.bhkRagdollConstraint):
                hk_descriptor = hkconstraint.ragdoll
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkLimitedHingeConstraint):
                hk_descriptor = hkconstraint.limited_hinge
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkHingeConstraint):
                hk_descriptor = hkconstraint.hinge
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkMalleableConstraint):
                if hkconstraint.type == 7:
                    hk_descriptor = hkconstraint.ragdoll
                    b_hkobj.rigid_body.enabled = False
                elif hkconstraint.type == 2:
                    hk_descriptor = hkconstraint.limited_hinge
                    b_hkobj.rigid_body.enabled = False
                else:
                    NifLog.warn("Unknown malleable type ({0}), skipped".format(str(hkconstraint.type)))
                # extra malleable constraint settings
                # TODO [constraint][flag] Damping parameters not yet in Blender Python API
                # TODO [constraint][flag] tau (force between bodies) not supported by Blender
            else:
                NifLog.warn("Unknown constraint type ({0}), skipped".format(hkconstraint.__class__.__name__))
                continue

            # add the constraint as a rigid body joint
            b_constr = b_hkobj.constraints.new('RIGID_BODY_JOINT')
            b_constr.name = b_hkobj.name
            b_constr.show_pivot = True

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
            b_constr.target = \
                collision.DICT_HAVOK_OBJECTS[hkconstraint.entities[1]][0]
            # set rigid body type (generic)
            b_constr.pivot_type = 'GENERIC_6_DOF'
            # limiting parameters (limit everything)
            b_constr.use_angular_limit_x = True
            b_constr.use_angular_limit_y = True
            b_constr.use_angular_limit_z = True

            # get pivot point
            pivot = mathutils.Vector((hk_descriptor.pivot_a.x * self.HAVOK_SCALE,
                                      hk_descriptor.pivot_a.y * self.HAVOK_SCALE,
                                      hk_descriptor.pivot_a.z * self.HAVOK_SCALE))

            # get z- and x-axes of the constraint
            # (also see export_nif.py NifImport.export_constraints)
            if isinstance(hk_descriptor, NifFormat.RagdollDescriptor):
                b_constr.pivot_type = 'CONE_TWIST'
                # for ragdoll, take z to be the twist axis (central axis of the
                # cone, that is)
                axis_z = mathutils.Vector((hk_descriptor.twist_a.x,
                                           hk_descriptor.twist_a.y,
                                           hk_descriptor.twist_a.z))
                # for ragdoll, let x be the plane vector
                axis_x = mathutils.Vector((hk_descriptor.plane_a.x,
                                           hk_descriptor.plane_a.y,
                                           hk_descriptor.plane_a.z))
                # set the angle limits
                # (see http://niftools.sourceforge.net/wiki/Oblivion/Bhk_Objects/Ragdoll_Constraint
                # for a nice picture explaining this)
                b_constr.limit_angle_min_x = hk_descriptor.plane_min_angle
                b_constr.limit_angle_max_x = hk_descriptor.plane_max_angle

                b_constr.limit_angle_min_y = -hk_descriptor.cone_max_angle
                b_constr.limit_angle_max_y = hk_descriptor.cone_max_angle

                b_constr.limit_angle_min_z = hk_descriptor.twist_min_angle
                b_constr.limit_angle_max_z = hk_descriptor.twist_max_angle

                b_hkobj.niftools_constraint.LHMaxFriction = hk_descriptor.max_friction

            elif isinstance(hk_descriptor, NifFormat.LimitedHingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector((hk_descriptor.perp_2_axle_in_a_1.x,
                                           hk_descriptor.perp_2_axle_in_a_1.y,
                                           hk_descriptor.perp_2_axle_in_a_1.z))
                # for hinge, take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.Vector((hk_descriptor.axle_a.x,
                                           hk_descriptor.axle_a.y,
                                           hk_descriptor.axle_a.z))
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector((hk_descriptor.perp_2_axle_in_a_2.x,
                                           hk_descriptor.perp_2_axle_in_a_2.y,
                                           hk_descriptor.perp_2_axle_in_a_2.z))
                # they should form a orthogonal basis
                if (mathutils.Vector.cross(axis_x, axis_y) - axis_z).length > 0.01:
                    # either not orthogonal, or negative orientation
                    if (mathutils.Vector.cross(-axis_x, axis_y) - axis_z).length > 0.01:
                        NifLog.warn("Axes are not orthogonal in {0}.\nArbitrary orientation has been chosen".format(hk_descriptor.__class__.__name__))
                        axis_z = mathutils.Vector.cross(axis_x, axis_y)
                    else:
                        # fix orientation
                        NifLog.warn("X axis flipped in {0} to fix orientation".format(hk_descriptor.__class__.__name__))
                        axis_x = -axis_x
                # getting properties with no blender constraint
                # equivalent and setting as obj properties
                b_constr.limit_angle_max_x = hk_descriptor.max_angle
                b_constr.limit_angle_min_x = hk_descriptor.min_angle
                b_hkobj.niftools_constraint.LHMaxFriction = hk_descriptor.max_friction

                if hasattr(hkconstraint, "tau"):
                    b_hkobj.niftools_constraint.tau = hkconstraint.tau
                    b_hkobj.niftools_constraint.damping = hkconstraint.damping

            elif isinstance(hk_descriptor, NifFormat.HingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector((hk_descriptor.perp_2_axle_in_a_1.x,
                                           hk_descriptor.perp_2_axle_in_a_1.y,
                                           hk_descriptor.perp_2_axle_in_a_1.z))
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector((hk_descriptor.perp_2_axle_in_a_2.x,
                                           hk_descriptor.perp_2_axle_in_a_2.y,
                                           hk_descriptor.perp_2_axle_in_a_2.z))
                # take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.Vector.cross(axis_y, axis_z)
                b_hkobj.niftools_constraint.LHMaxFriction = hk_descriptor.max_friction
            else:
                raise ValueError("unknown descriptor %s" % hk_descriptor.__class__.__name__)

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
                transform = mathutils.Quaternion((hkbody.rotation.w,
                                                  hkbody.rotation.x,
                                                  hkbody.rotation.y,
                                                  hkbody.rotation.z)).to_matrix()
                transform.resize_4x4()
                # set translation
                transform[0][3] = hkbody.translation.x * self.HAVOK_SCALE
                transform[1][3] = hkbody.translation.y * self.HAVOK_SCALE
                transform[2][3] = hkbody.translation.z * self.HAVOK_SCALE
                # apply transform
                pivot = pivot * transform
                transform = transform.to_3x3()
                axis_z = axis_z * transform
                axis_x = axis_x * transform

            # next, cancel out bone matrix correction
            # note that B' = X * B with X = armature.DICT_BONES_EXTRA_MATRIX[B]
            # so multiply with the inverse of X
            for niBone in armature.DICT_BONES_EXTRA_MATRIX:
                if niBone.collision_object and niBone.collision_object.body is hkbody:
                    transform = mathutils.Matrix(armature.DICT_BONES_EXTRA_MATRIX[niBone])
                    transform.invert()
                    pivot = pivot * transform
                    transform = transform.to_3x3()
                    axis_z = axis_z * transform
                    axis_x = axis_x * transform
                    break

            # cancel out bone tail translation
            if b_hkobj.parent_bone:
                pivot[1] -= b_hkobj.parent.data.bones[b_hkobj.parent_bone].length

            # cancel out object transform
            transform = mathutils.Matrix(b_hkobj.matrix_local)
            transform.invert()
            pivot = pivot * transform
            transform = transform.to_3x3()
            axis_z = axis_z * transform
            axis_x = axis_x * transform

            # set pivot point
            b_constr.pivot_x = pivot[0]
            b_constr.pivot_y = pivot[1]
            b_constr.pivot_z = pivot[2]

            # set euler angles
            constr_matrix = mathutils.Matrix((axis_x,
                                              mathutils.Vector.cross(axis_z, axis_x),
                                              axis_z))
            constr_euler = constr_matrix.to_euler()
            b_constr.axis_x = constr_euler.x
            b_constr.axis_y = constr_euler.y
            b_constr.axis_z = constr_euler.z
            # DEBUG
            assert ((axis_x - mathutils.Vector((1, 0, 0)) * constr_matrix).length < 0.0001)
            assert ((axis_z - mathutils.Vector((0, 0, 1)) * constr_matrix).length < 0.0001)

            # the generic rigid body type is very buggy... so for simulation
            # purposes let's transform it into ball and hinge
            if isinstance(hk_descriptor, NifFormat.RagdollDescriptor):
                # cone_twist
                b_constr.pivot_type = 'CONE_TWIST'
            elif isinstance(hk_descriptor, (NifFormat.LimitedHingeDescriptor, NifFormat.HingeDescriptor)):
                # (limited) hinge
                b_constr.pivot_type = 'HINGE'
            else:
                raise ValueError("unknown descriptor %s" % hk_descriptor.__class__.__name__)
