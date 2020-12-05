"""Script to import/export constraints."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

import mathutils
from pyffi.formats.nif import NifFormat

from io_scene_niftools.modules.nif_import import collision
from io_scene_niftools.utils.singleton import NifData
from io_scene_niftools.utils.logging import NifLog


class Constraint:

    def __init__(self):
        # TODO [collision][havok][property] Need better way to set this, maybe user property
        if NifData.data._user_version_value_._value == 12 and NifData.data._user_version_2_value_._value == 83:
            self.HAVOK_SCALE = collision.HAVOK_SCALE * 10
        else:
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

        NifLog.info(f"Importing constraints for b_hkobj.name")

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
                hkdescriptor = hkconstraint.ragdoll
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkLimitedHingeConstraint):
                hkdescriptor = hkconstraint.limited_hinge
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkHingeConstraint):
                hkdescriptor = hkconstraint.hinge
                b_hkobj.rigid_body.enabled = True
            elif isinstance(hkconstraint, NifFormat.bhkMalleableConstraint):
                if hkconstraint.type == 7:
                    hkdescriptor = hkconstraint.ragdoll
                    b_hkobj.rigid_body.enabled = False
                elif hkconstraint.type == 2:
                    hkdescriptor = hkconstraint.limited_hinge
                    b_hkobj.rigid_body.enabled = False
                else:
                    NifLog.warn(f"Unknown malleable type ({hkconstraint.type:s}), skipped")
                # TODO [constraint][flag] Damping parameters not yet in Blender Python API
                # TODO [constraint][flag] tau (force between bodies) not supported by Blender
            else:
                NifLog.warn(f"Unknown constraint type ({hkconstraint.__class__.__name__}), skipped")
                continue

            # todo [constraints] the following is no longer possible, fixme
            return

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
            b_constr.target = collision.DICT_HAVOK_OBJECTS[hkconstraint.entities[1]][0]
            # set rigid body type (generic)
            b_constr.pivot_type = 'GENERIC_6_DOF'
            # limiting parameters (limit everything)
            b_constr.use_angular_limit_x = True
            b_constr.use_angular_limit_y = True
            b_constr.use_angular_limit_z = True

            # get pivot point
            pivot = mathutils.Vector((hkdescriptor.pivot_b.x,
                                      hkdescriptor.pivot_b.y,
                                      hkdescriptor.pivot_b.z)) * self.HAVOK_SCALE

            # get z- and x-axes of the constraint
            # (also see export_nif.py NifImport.export_constraints)
            if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                b_constr.pivot_type = 'CONE_TWIST'
                # for ragdoll, take z to be the twist axis (central axis of the
                # cone, that is)
                axis_z = mathutils.Vector((hkdescriptor.twist_a.x,
                                           hkdescriptor.twist_a.y,
                                           hkdescriptor.twist_a.z))
                # for ragdoll, let x be the plane vector
                axis_x = mathutils.Vector((hkdescriptor.plane_a.x,
                                           hkdescriptor.plane_a.y,
                                           hkdescriptor.plane_a.z))
                # set the angle limits
                # (see http://niftools.sourceforge.net/wiki/Oblivion/Bhk_Objects/Ragdoll_Constraint
                # for a nice picture explaining this)
                b_constr.limit_angle_min_x = hkdescriptor.plane_min_angle
                b_constr.limit_angle_max_x = hkdescriptor.plane_max_angle

                b_constr.limit_angle_min_y = -hkdescriptor.cone_max_angle
                b_constr.limit_angle_max_y = hkdescriptor.cone_max_angle

                b_constr.limit_angle_min_z = hkdescriptor.twist_min_angle
                b_constr.limit_angle_max_z = hkdescriptor.twist_max_angle

                b_hkobj.niftools_constraint.LHMaxFriction = hkdescriptor.max_friction

            elif isinstance(hkdescriptor, NifFormat.LimitedHingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector((hkdescriptor.perp_2_axle_in_a_1.x,
                                           hkdescriptor.perp_2_axle_in_a_1.y,
                                           hkdescriptor.perp_2_axle_in_a_1.z))
                # for hinge, take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.Vector((hkdescriptor.axle_a.x,
                                           hkdescriptor.axle_a.y,
                                           hkdescriptor.axle_a.z))
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector((hkdescriptor.perp_2_axle_in_a_2.x,
                                           hkdescriptor.perp_2_axle_in_a_2.y,
                                           hkdescriptor.perp_2_axle_in_a_2.z))
                # they should form a orthogonal basis
                if (mathutils.Vector.cross(axis_x, axis_y) - axis_z).length > 0.01:
                    # either not orthogonal, or negative orientation
                    if (mathutils.Vector.cross(-axis_x, axis_y) - axis_z).length > 0.01:
                        NifLog.warn(f"Axes are not orthogonal in {hkdescriptor.__class__.__name__}; Arbitrary orientation has been chosen")
                        axis_z = mathutils.Vector.cross(axis_x, axis_y)
                    else:
                        # fix orientation
                        NifLog.warn(f"X axis flipped in {hkdescriptor.__class__.__name__} to fix orientation")
                        axis_x = -axis_x
                # getting properties with no blender constraint equivalent and setting as obj properties
                b_constr.limit_angle_max_x = hkdescriptor.max_angle
                b_constr.limit_angle_min_x = hkdescriptor.min_angle
                b_hkobj.niftools_constraint.LHMaxFriction = hkdescriptor.max_friction

                if hasattr(hkconstraint, "tau"):
                    b_hkobj.niftools_constraint.tau = hkconstraint.tau
                    b_hkobj.niftools_constraint.damping = hkconstraint.damping

            elif isinstance(hkdescriptor, NifFormat.HingeDescriptor):
                # for hinge, y is the vector on the plane of rotation defining
                # the zero angle
                axis_y = mathutils.Vector((hkdescriptor.perp_2_axle_in_a_1.x,
                                           hkdescriptor.perp_2_axle_in_a_1.y,
                                           hkdescriptor.perp_2_axle_in_a_1.z))
                # for hinge, z is the vector on the plane of rotation defining
                # the positive direction of rotation
                axis_z = mathutils.Vector((hkdescriptor.perp_2_axle_in_a_2.x,
                                           hkdescriptor.perp_2_axle_in_a_2.y,
                                           hkdescriptor.perp_2_axle_in_a_2.z))
                # take x to be the the axis of rotation
                # (this corresponds with Blender's convention for hinges)
                axis_x = mathutils.Vector.cross(axis_y, axis_z)
                b_hkobj.niftools_constraint.LHMaxFriction = hkdescriptor.max_friction
            else:
                raise ValueError("Unknown descriptor {0}".format(hkdescriptor.__class__.__name__))

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
                # pivot = pivot * transform
                transform = transform.to_3x3()
                axis_z = axis_z * transform
                axis_x = axis_x * transform

            # TODO [armature] update this to use the new bone system
            # next, cancel out bone matrix correction
            # note that B' = X * B with X = self.nif_import.dict_bones_extra_matrix[B]
            # so multiply with the inverse of X
            # for niBone in self.nif_import.dict_bones_extra_matrix:
            # if niBone.collision_object \
            # and niBone.collision_object.body is hkbody:
            # transform = mathutils.Matrix(
            # self.nif_import.dict_bones_extra_matrix[niBone])
            # transform.invert()
            # pivot = pivot * transform
            # transform = transform.to_3x3()
            # axis_z = axis_z * transform
            # axis_x = axis_x * transform
            # break

            # # cancel out bone tail translation
            # if b_hkobj.parent_bone:
            #     pivot[1] -= b_hkobj.parent.data.bones[
            #         b_hkobj.parent_bone].length

            # cancel out object transform
            transform = mathutils.Matrix(b_hkobj.matrix_local)
            transform.invert()
            # pivot = pivot * transform
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

            # the generic rigid body type is very buggy... so for simulation purposes let's transform it into ball and hinge
            if isinstance(hkdescriptor, NifFormat.RagdollDescriptor):
                # cone_twist
                b_constr.pivot_type = 'CONE_TWIST'
            elif isinstance(hkdescriptor, (NifFormat.LimitedHingeDescriptor, NifFormat.HingeDescriptor)):
                # (limited) hinge
                b_constr.pivot_type = 'HINGE'
            else:
                raise ValueError("Unknown descriptor {0}".format(hkdescriptor.__class__.__name__))
