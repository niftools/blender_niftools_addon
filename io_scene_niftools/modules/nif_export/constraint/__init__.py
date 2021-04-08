"""Script to export constraints."""

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

from pyffi.formats.nif import NifFormat

import bpy
import mathutils

import io_scene_niftools.utils.logging
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math, consts
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.singleton import NifOp


class Constraint:

    def __init__(self):
        self.HAVOK_SCALE = consts.HAVOK_SCALE

    def export_constraints(self, b_obj, root_block):
        """Export the constraints of an object.

        @param b_obj: The object whose constraints to export.
        @param root_block: The root of the nif tree (required for update_a_b)."""
        if isinstance(b_obj, bpy.types.Bone):
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
            if b_constr.type == 'RIGID_BODY_JOINT':
                if bpy.context.scene.niftools_scene.game not in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    NifLog.warn(f"Only Oblivion/Fallout/Skyrim rigid body constraints currently supported: Skipping {b_constr}.")
                    continue
                # check that the object is a rigid body
                for otherbody, otherobj in block_store.block_to_obj.items():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) and otherobj is b_obj:
                        hkbody = otherbody
                        break
                else:
                    # no collision body for this object
                    raise io_scene_niftools.utils.logging.NifError(f"Object {b_obj.name} has a rigid body constraint, but is not exported as collision object")

                # yes there is a rigid body constraint
                # is it of a type that is supported?
                if b_constr.pivot_type == 'CONE_TWIST':
                    # ball
                    if b_obj.rigid_body.enabled:
                        n_bhkconstraint = block_store.create_block("bhkRagdollConstraint", b_constr)
                    else:
                        n_bhkconstraint = block_store.create_block("bhkMalleableConstraint", b_constr)
                        n_bhkconstraint.type = 7
                    n_bhkdescriptor = n_bhkconstraint.ragdoll
                elif b_constr.pivot_type == 'HINGE':
                    # hinge
                    if b_obj.rigid_body.enabled:
                        n_bhkconstraint = block_store.create_block("bhkLimitedHingeConstraint", b_constr)
                    else:
                        n_bhkconstraint = block_store.create_block("bhkMalleableConstraint", b_constr)
                        n_bhkconstraint.type = 2
                    n_bhkdescriptor = n_bhkconstraint.limited_hinge
                else:
                    raise io_scene_niftools.utils.logging.NifError(f"Unsupported rigid body joint type ({b_constr.type}), only ball and hinge are supported.")

                # defaults and getting object properties for user settings (should use constraint properties,
                # but blender does not have those...)
                if b_constr.limit_angle_max_x != 0:
                    max_angle = b_constr.limit_angle_max_x
                else:
                    max_angle = 1.5
                if b_constr.limit_angle_min_x != 0:
                    min_angle = b_constr.limit_angle_min_x
                else:
                    min_angle = 0.0

                # friction: again, just picking a reasonable value if no real value given
                if b_obj.niftools_constraint.LHMaxFriction != 0:
                    max_friction = b_obj.niftools_constraint.LHMaxFriction
                else:
                    if isinstance(n_bhkconstraint, NifFormat.bhkMalleableConstraint):
                        # malleable typically have 0 (perhaps because they have a damping parameter)
                        max_friction = 0
                    else:
                        # non-malleable typically have 10
                        if bpy.context.scene.niftools_scene.game == 'FALLOUT_3':
                            max_friction = 100
                        else:  # oblivion
                            max_friction = 10

                # parent constraint to hkbody
                hkbody.num_constraints += 1
                hkbody.constraints.update_size()
                hkbody.constraints[-1] = n_bhkconstraint

                # export n_bhkconstraint settings
                n_bhkconstraint.num_entities = 2
                n_bhkconstraint.entities.update_size()
                n_bhkconstraint.entities[0] = hkbody
                # is there a target?
                targetobj = b_constr.target
                if not targetobj:
                    NifLog.warn(f"Constraint {b_constr} has no target, skipped")
                    continue
                # find target's bhkRigidBody
                for otherbody, otherobj in block_store.block_to_obj.items():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) and otherobj == targetobj:
                        n_bhkconstraint.entities[1] = otherbody
                        break
                else:
                    # not found
                    raise io_scene_niftools.utils.logging.NifError(f"Rigid body target not exported in nif tree - check that {targetobj} is selected during export.")

                # priority
                n_bhkconstraint.priority = 1
                # extra malleable constraint settings
                if isinstance(n_bhkconstraint, NifFormat.bhkMalleableConstraint):
                    # unknowns
                    n_bhkconstraint.unknown_int_2 = 2
                    n_bhkconstraint.unknown_int_3 = 1
                    # force required to keep bodies together
                    n_bhkconstraint.tau = b_obj.niftools_constraint.tau
                    n_bhkconstraint.damping = b_obj.niftools_constraint.damping

                # calculate pivot point and constraint matrix
                pivot = mathutils.Vector([b_constr.pivot_x,
                                          b_constr.pivot_y,
                                          b_constr.pivot_z]) / self.HAVOK_SCALE
                constr_matrix = mathutils.Euler((b_constr.axis_x,
                                                 b_constr.axis_y,
                                                 b_constr.axis_z))
                constr_matrix = constr_matrix.to_matrix()

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
                transform = mathutils.Matrix(b_obj.matrix_local)
                # pivot = pivot * transform
                constr_matrix = constr_matrix * transform.to_3x3()

                # export n_bhkdescriptor pivot point
                # n_bhkdescriptor.pivot_a.x = pivot[0]
                # n_bhkdescriptor.pivot_a.y = pivot[1]
                # n_bhkdescriptor.pivot_a.z = pivot[2]
                # export n_bhkdescriptor axes and other parameters
                # (also see import_nif.py NifImport.import_bhk_constraints)
                axis_x = mathutils.Vector([1, 0, 0]) * constr_matrix
                axis_y = mathutils.Vector([0, 1, 0]) * constr_matrix
                axis_z = mathutils.Vector([0, 0, 1]) * constr_matrix

                if isinstance(n_bhkdescriptor, NifFormat.RagdollDescriptor):
                    # z axis is the twist vector
                    n_bhkdescriptor.twist_a.x = axis_z[0]
                    n_bhkdescriptor.twist_a.y = axis_z[1]
                    n_bhkdescriptor.twist_a.z = axis_z[2]
                    # x axis is the plane vector
                    n_bhkdescriptor.plane_a.x = axis_x[0]
                    n_bhkdescriptor.plane_a.y = axis_x[1]
                    n_bhkdescriptor.plane_a.z = axis_x[2]
                    # angle limits
                    # take them twist and plane to be 45 deg (3.14 / 4 = 0.8)

                    n_bhkdescriptor.plane_min_angle = b_constr.limit_angle_min_x
                    n_bhkdescriptor.plane_max_angle = b_constr.limit_angle_max_x

                    n_bhkdescriptor.cone_max_angle = b_constr.limit_angle_max_y

                    n_bhkdescriptor.twist_min_angle = b_constr.limit_angle_min_z
                    n_bhkdescriptor.twist_max_angle = b_constr.limit_angle_max_z

                    # same for maximum cone angle
                    n_bhkdescriptor.max_friction = max_friction

                elif isinstance(n_bhkdescriptor, NifFormat.LimitedHingeDescriptor):
                    # y axis is the zero angle vector on the plane of rotation
                    n_bhkdescriptor.perp_2_axle_in_a_1.x = axis_y[0]
                    n_bhkdescriptor.perp_2_axle_in_a_1.y = axis_y[1]
                    n_bhkdescriptor.perp_2_axle_in_a_1.z = axis_y[2]
                    # x axis is the axis of rotation
                    n_bhkdescriptor.axle_a.x = axis_x[0]
                    n_bhkdescriptor.axle_a.y = axis_x[1]
                    n_bhkdescriptor.axle_a.z = axis_x[2]
                    # z is the remaining axis determining the positive direction of rotation
                    n_bhkdescriptor.perp_2_axle_in_a_2.x = axis_z[0]
                    n_bhkdescriptor.perp_2_axle_in_a_2.y = axis_z[1]
                    n_bhkdescriptor.perp_2_axle_in_a_2.z = axis_z[2]
                    # angle limits typically, the constraint on one side is defined by the z axis
                    n_bhkdescriptor.min_angle = min_angle
                    # the maximum axis is typically about 90 degrees
                    # 3.14 / 2 = 1.5
                    n_bhkdescriptor.max_angle = max_angle
                    # friction
                    n_bhkdescriptor.max_friction = max_friction
                else:
                    raise ValueError(f"unknown descriptor {n_bhkdescriptor.__class__.__name__}")

                # do AB
                n_bhkconstraint.update_a_b(root_block)
                n_bhkdescriptor.pivot_b.x = pivot[0]
                n_bhkdescriptor.pivot_b.y = pivot[1]
                n_bhkdescriptor.pivot_b.z = pivot[2]
