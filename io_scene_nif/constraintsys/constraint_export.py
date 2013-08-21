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
        self.nif_export = parent
        self.properties = parent.properties
        
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
                if self.properties.game not in ('OBLIVION', 'FALLOUT_3'):
                    self.nif_export.warning(
                        "Only Oblivion/Fallout 3 rigid body constraints"
                        " can be exported: skipped %s." % b_constr)
                    continue
                # check that the object is a rigid body
                for otherbody, otherobj in self.nif_export.blocks.items():
                    if isinstance(otherbody, NifFormat.bhkRigidBody) \
                        and otherobj is b_obj:
                        hkbody = otherbody
                        break
                else:
                    # no collision body for this object
                    raise nif_utils.NifExportError(
                        "Object %s has a rigid body constraint,"
                        " but is not exported as collision object"
                        % b_obj.name)
                # yes there is a rigid body constraint
                # is it of a type that is supported?
                if b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 1:
                    # ball
                    if not self.properties.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.nif_export.objecthelper.create_block(
                            "bhkRagdollConstraint", b_constr)
                    else:
                        hkconstraint = self.nif_export.objecthelper.create_block(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 7
                    hkdescriptor = hkconstraint.ragdoll
                elif b_constr[Blender.Constraint.Settings.CONSTR_RB_TYPE] == 2:
                    # hinge
                    if not self.properties.EXPORT_OB_MALLEABLECONSTRAINT:
                        hkconstraint = self.nif_export.objecthelper.create_block(
                            "bhkLimitedHingeConstraint", b_constr)
                    else:
                        hkconstraint = self.nif_export.objecthelper.create_block(
                            "bhkMalleableConstraint", b_constr)
                        hkconstraint.type = 2
                    hkdescriptor = hkconstraint.limited_hinge
                else:
                    raise nif_utils.NifExportError(
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
                    if self.properties.game == 'FALLOUT_3':
                        max_friction = 100
                    else: # oblivion
                        max_friction = 10
                for prop in b_obj.getAllProperties():
                    if (prop.name == 'LimitedHinge_MaxAngle'
                        and prop.type == "FLOAT"):
                        max_angle = prop.data
                    if (prop.name == 'LimitedHinge_MinAngle'
                        and prop.type == "FLOAT"):
                        min_angle = prop.data
                    if (prop.name == 'LimitedHinge_MaxFriction'
                        and prop.type == "FLOAT"):
                        max_friction = prop.data

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
                    self.warning("Constraint %s has no target, skipped")
                    continue
                # find target's bhkRigidBody
                for otherbody, otherobj in self.nif_export.blocks.items():
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
                pivot = mathutils.Vector([
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVX],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVY],
                    b_constr[Blender.Constraint.Settings.CONSTR_RB_PIVZ],
                    ])
                constr_matrix = mathutils.Euler(
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
                transform = mathutils.Matrix(
                    self.get_object_matrix(b_obj, 'localspace').as_list())
                pivot = pivot * transform
                constr_matrix = constr_matrix * transform.rotationPart()

                # export hkdescriptor pivot point
                hkdescriptor.pivot_a.x = pivot[0] / self.HAVOK_SCALE
                hkdescriptor.pivot_a.y = pivot[1] / self.HAVOK_SCALE
                hkdescriptor.pivot_a.z = pivot[2] / self.HAVOK_SCALE
                # export hkdescriptor axes and other parameters
                # (also see import_nif.py NifImport.import_bhk_constraints)
                axis_x = mathutils.Vector([1,0,0]) * constr_matrix
                axis_y = mathutils.Vector([0,1,0]) * constr_matrix
                axis_z = mathutils.Vector([0,0,1]) * constr_matrix
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

