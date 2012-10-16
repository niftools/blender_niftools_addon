'''Script to import/export all the skeleton related objects.'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#	* Redistributions of source code must retain the above copyright
#	  notice, this list of conditions and the following disclaimer.
# 
#	* Redistributions in binary form must reproduce the above
#	  copyright notice, this list of conditions and the following
#	  disclaimer in the documentation and/or other materials provided
#	  with the distribution.
# 
#	* Neither the name of the NIF File Format Library and Tools
#	  project nor the names of its contributors may be used to endorse
#	  or promote products derived from this software without specific
#	  prior written permission.
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

import os

import bpy
import mathutils

from pyffi.formats.nif import NifFormat

class armature_import():
	
		# correction matrices list, the order is +X, +Y, +Z, -X, -Y, -Z
	BONE_CORRECTION_MATRICES = (
		mathutils.Matrix([[ 0.0, -1.0, 0.0], [ 1.0, 0.0, 0.0], [ 0.0, 0.0, 1.0]]),
		mathutils.Matrix([[ 1.0, 0.0, 0.0], [ 0.0, 1.0, 0.0], [ 0.0, 0.0, 1.0]]),
		mathutils.Matrix([[ 1.0, 0.0, 0.0], [ 0.0, 0.0, 1.0], [ 0.0, -1.0, 0.0]]),
		mathutils.Matrix([[ 0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [ 0.0, 0.0, 1.0]]),
		mathutils.Matrix([[-1.0, 0.0, 0.0], [ 0.0, -1.0, 0.0], [ 0.0, 0.0, 1.0]]),
		mathutils.Matrix([[ 1.0, 0.0, 0.0], [ 0.0, 0.0, -1.0], [ 0.0, 1.0, 0.0]]))

	# identity matrix, for comparisons
	IDENTITY44 = mathutils.Matrix([[ 1.0, 0.0, 0.0, 0.0],
								   [ 0.0, 1.0, 0.0, 0.0],
								   [ 0.0, 0.0, 1.0, 0.0],
								   [ 0.0, 0.0, 0.0, 1.0]])
	
	def __init__(self, parent):
		self.nif_common = parent
	
	def import_armature(self, niArmature):
		"""Scans an armature hierarchy, and returns a whole armature.
		This is done outside the normal node tree scan to allow for positioning
		of the bones before skins are attached."""
		armature_name = self.import_name(niArmature)

		b_armatureData = Blender.Armature.Armature()
		b_armatureData.name = armature_name
		b_armatureData.drawAxes = True
		b_armatureData.envelopes = False
		b_armatureData.vertexGroups = True
		b_armatureData.draw_type = 'STICK'
		b_armature = self.context.scene.objects.new(b_armatureData, armature_name)

		# make armature editable and create bones
		b_armatureData.makeEditable()
		niChildBones = [child for child in niArmature.children
						if self.is_bone(child)]
		for niBone in niChildBones:
			self.import_bone(
				niBone, b_armature, b_armatureData, niArmature)
		b_armatureData.update()

		# TODO: Move to Animation.py

		# The armature has been created in editmode,
		# now we are ready to set the bone keyframes.
		if self.nif_common.properties.animation:
			# create an action
			action = Blender.Armature.NLA.NewAction()
			action.setActive(b_armature)
			# go through all armature pose bones
			# see http://www.elysiun.com/forum/viewtopic.php?t=58693
			self.nif_common.info('Importing Animations')
			for bone_name, b_posebone in b_armature.getPose().bones.items():
				# denote progress
				self.nif_common.debug('Importing animation for bone %s' % bone_name)
				niBone = self.nif_common.blocks[bone_name]

				# get bind matrix (NIF format stores full transformations in keyframes,
				# but Blender wants relative transformations, hence we need to know
				# the bind position for conversion). Since
				# [ SRchannel 0 ]	[ SRbind 0 ]   [ SRchannel * SRbind		 0 ]   [ SRtotal 0 ]
				# [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel  * SRbind + Tbind 1 ] = [ Ttotal  1 ]
				# with
				# 'total' the transformations as stored in the NIF keyframes,
				# 'bind' the Blender bind pose, and
				# 'channel' the Blender IPO channel,
				# it follows that
				# Schannel = Stotal / Sbind
				# Rchannel = Rtotal * inverse(Rbind)
				# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
				bone_bm = self.nif_common.import_matrix(niBone) # base pose
				niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = self.decompose_srt(bone_bm)
				niBone_bind_rot_inv = mathutils.Matrix(niBone_bind_rot)
				niBone_bind_rot_inv.invert()
				niBone_bind_quat_inv = niBone_bind_rot_inv.toQuat()
				# we also need the conversion of the original matrix to the
				# new bone matrix, say X,
				# B' = X * B
				# (with B' the Blender matrix and B the NIF matrix) because we
				# need that
				# C' * B' = X * C * B
				# and therefore
				# C' = X * C * B * inverse(B') = X * C * inverse(X),
				# where X = B' * inverse(B)
				#
				# In detail:
				# [ SRX 0 ]   [ SRC 0 ]			[ SRX 0 ]
				# [ TX  1 ] * [ TC  1 ] * inverse( [ TX  1 ] ) =
				# [ SRX * SRC	   0 ]   [ inverse(SRX)		 0 ]
				# [ TX * SRC + TC   1 ] * [ -TX * inverse(SRX)   1 ] =
				# [ SRX * SRC * inverse(SRX)			  0 ]
				# [ (TX * SRC + TC - TX) * inverse(SRX)   1 ]
				# Hence
				# SC' = SX * SC / SX = SC
				# RC' = RX * RC * inverse(RX)
				# TC' = (TX * SC * RC + TC - TX) * inverse(RX) / SX
				extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = self.decompose_srt(self.bones_extra_matrix[niBone])
				extra_matrix_quat = extra_matrix_rot.toQuat()
				extra_matrix_rot_inv = mathutils.Matrix(extra_matrix_rot)
				extra_matrix_rot_inv.invert()
				extra_matrix_quat_inv = extra_matrix_rot_inv.toQuat()
				# now import everything
				# ##############################

				# get controller, interpolator, and data
				# note: the NiKeyframeController check also includes
				#	   NiTransformController (see hierarchy!)
				kfc = self.find_controller(niBone,
										   NifFormat.NiKeyframeController)
				# old style: data directly on controller
				kfd = kfc.data if kfc else None
				# new style: data via interpolator
				kfi = kfc.interpolator if kfc else None
				# next is a quick hack to make the new transform
				# interpolator work as if it is an old style keyframe data
				# block parented directly on the controller
				if isinstance(kfi, NifFormat.NiTransformInterpolator):
					kfd = kfi.data
					# for now, in this case, ignore interpolator
					kfi = None

				# B-spline curve import
				if isinstance(kfi, NifFormat.NiBSplineInterpolator):
					times = list(kfi.get_times())
					translations = list(kfi.get_translations())
					scales = list(kfi.get_scales())
					rotations = list(kfi.get_rotations())

					# if we have translation keys, we make a dictionary of
					# rot_keys and scale_keys, this makes the script work MUCH
					# faster in most cases
					if translations:
						scale_keys_dict = {}
						rot_keys_dict = {}

					# scales: ignore for now, implement later
					#		 should come here
					scales = None

					# rotations
					if rotations:
						self.nif_common.debug(
							'Rotation keys...(bspline quaternions)')
						for time, quat in zip(times, rotations):
							frame = 1 + int(time * self.nif_common.fps + 0.5)
							quat = mathutils.Quaternion(
								[quat[0], quat[1], quat[2], quat[3]])
							# beware, CrossQuats takes arguments in a
							# counter-intuitive order:
							# q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
							quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
							rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
							b_posebone.quat = rot
							b_posebone.insertKey(b_armature, frame,
												 [Blender.Object.Pose.ROT])
							# fill optimizer dictionary
							if translations:
								rot_keys_dict[frame] = mathutils.Quaternion(rot)

					# translations
					if translations:
						self.nif_common.debug('Translation keys...(bspline)')
						for time, translation in zip(times, translations):
							# time 0.0 is frame 1
							frame = 1 + int(time * self.nif_common.fps + 0.5)
							trans = mathutils.Vector(*translation)
							locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0 / niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
							# the rotation matrix is needed at this frame (that's
							# why the other keys are inserted first)
							if rot_keys_dict:
								try:
									rot = rot_keys_dict[frame].toMatrix()
								except KeyError:
									# fall back on slow method
									ipo = action.getChannelIpo(bone_name)
									quat = mathutils.Quaternion()
									quat.x = ipo.getCurve('QuatX').evaluate(frame)
									quat.y = ipo.getCurve('QuatY').evaluate(frame)
									quat.z = ipo.getCurve('QuatZ').evaluate(frame)
									quat.w = ipo.getCurve('QuatW').evaluate(frame)
									rot = quat.toMatrix()
							else:
								rot = mathutils.Matrix([[1.0, 0.0, 0.0],
														[0.0, 1.0, 0.0],
														[0.0, 0.0, 1.0]])
							# we also need the scale at this frame
							if scale_keys_dict:
								try:
									sizeVal = scale_keys_dict[frame]
								except KeyError:
									ipo = action.getChannelIpo(bone_name)
									if ipo.getCurve('SizeX'):
										sizeVal = ipo.getCurve('SizeX').evaluate(frame) # assume uniform scale
									else:
										sizeVal = 1.0
							else:
								sizeVal = 1.0
							size = mathutils.Matrix([[sizeVal, 0.0, 0.0],
													 [0.0, sizeVal, 0.0],
													 [0.0, 0.0, sizeVal]])
							# now we can do the final calculation
							loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0 / extra_matrix_scale) # C' = X * C * inverse(X)
							b_posebone.loc = loc
							b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])

					# delete temporary dictionaries
					if translations:
						del scale_keys_dict
						del rot_keys_dict

				# NiKeyframeData and NiTransformData import
				elif isinstance(kfd, NifFormat.NiKeyframeData):

					translations = kfd.translations
					scales = kfd.scales
					# if we have translation keys, we make a dictionary of
					# rot_keys and scale_keys, this makes the script work MUCH
					# faster in most cases
					if translations:
						scale_keys_dict = {}
						rot_keys_dict = {}
					# add the keys

					# Scaling
					if scales.keys:
						self.nif_common.debug('Scale keys...')
					for scaleKey in scales.keys:
						# time 0.0 is frame 1
						frame = 1 + int(scaleKey.time * self.nif_common.fps + 0.5)
						sizeVal = scaleKey.value
						size = sizeVal / niBone_bind_scale # Schannel = Stotal / Sbind
						b_posebone.size = mathutils.Vector(size, size, size)
						b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE]) # this is very slow... :(
						# fill optimizer dictionary
						if translations:
							scale_keys_dict[frame] = size

					# detect the type of rotation keys
					rotation_type = kfd.rotation_type

					# Euler Rotations
					if rotation_type == 4:
						# uses xyz rotation
						if kfd.xyz_rotations[0].keys:
							self.nif_common.debug('Rotation keys...(euler)')
						for xkey, ykey, zkey in zip(kfd.xyz_rotations[0].keys,
													 kfd.xyz_rotations[1].keys,
													 kfd.xyz_rotations[2].keys):
							# time 0.0 is frame 1
							# XXX it is assumed that all the keys have the
							# XXX same times!!!
							if (abs(xkey.time - ykey.time) > self.nif_common.properties.epsilon
								or abs(xkey.time - zkey.time) > self.nif_common.properties.epsilon):
								self.nif_common.warning(
									"xyz key times do not correspond, "
									"animation may not be correctly imported")
							frame = 1 + int(xkey.time * self.nif_common.fps + 0.5)
							euler = mathutils.Euler(
								[xkey.value * 180.0 / math.pi,
								 ykey.value * 180.0 / math.pi,
								 zkey.value * 180.0 / math.pi])
							quat = euler.toQuat()

							# beware, CrossQuats takes arguments in a counter-intuitive order:
							# q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()

							quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
							rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
							b_posebone.quat = rot
							b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
							# fill optimizer dictionary
							if translations:
								rot_keys_dict[frame] = mathutils.Quaternion(rot) 

					# Quaternion Rotations
					else:
						# TODO take rotation type into account for interpolation
						if kfd.quaternion_keys:
							self.nif_common.debug('Rotation keys...(quaternions)')
						quaternion_keys = kfd.quaternion_keys
						for key in quaternion_keys:
							frame = 1 + int(key.time * self.nif_common.fps + 0.5)
							keyVal = key.value
							quat = mathutils.Quaternion([keyVal.w, keyVal.x, keyVal.y, keyVal.z])
							# beware, CrossQuats takes arguments in a
							# counter-intuitive order:
							# q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
							quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
							rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
							b_posebone.quat = rot
							b_posebone.insertKey(b_armature, frame,
												 [Blender.Object.Pose.ROT])
							# fill optimizer dictionary
							if translations:
								rot_keys_dict[frame] = mathutils.Quaternion(rot)
						#else:
						#	print("Rotation keys...(unknown)" + 
						#		  "WARNING: rotation animation data of type" +
						#		  " %i found, but this type is not yet supported; data has been skipped""" % rotation_type)						
		
					# Translations
					if translations.keys:
						self.nif_common.debug('Translation keys...')
					for key in translations.keys:
						# time 0.0 is frame 1
						frame = 1 + int(key.time * self.nif_common.fps + 0.5)
						keyVal = key.value
						trans = mathutils.Vector(keyVal.x, keyVal.y, keyVal.z)
						locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0 / niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
						# the rotation matrix is needed at this frame (that's
						# why the other keys are inserted first)
						if rot_keys_dict:
							try:
								rot = rot_keys_dict[frame].toMatrix()
							except KeyError:
								# fall back on slow method
								ipo = action.getChannelIpo(bone_name)
								quat = mathutils.Quaternion()
								quat.x = ipo.getCurve('QuatX').evaluate(frame)
								quat.y = ipo.getCurve('QuatY').evaluate(frame)
								quat.z = ipo.getCurve('QuatZ').evaluate(frame)
								quat.w = ipo.getCurve('QuatW').evaluate(frame)
								rot = quat.toMatrix()
						else:
							rot = mathutils.Matrix([[1.0, 0.0, 0.0],
													[0.0, 1.0, 0.0],
													[0.0, 0.0, 1.0]])
						# we also need the scale at this frame
						if scale_keys_dict:
							try:
								sizeVal = scale_keys_dict[frame]
							except KeyError:
								ipo = action.getChannelIpo(bone_name)
								if ipo.getCurve('SizeX'):
									sizeVal = ipo.getCurve('SizeX').evaluate(frame) # assume uniform scale
								else:
									sizeVal = 1.0
						else:
							sizeVal = 1.0
						size = mathutils.Matrix([[sizeVal, 0.0, 0.0],
												 [0.0, sizeVal, 0.0],
												 [0.0, 0.0, sizeVal]])
						# now we can do the final calculation
						loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0 / extra_matrix_scale) # C' = X * C * inverse(X)
						b_posebone.loc = loc
						b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
					if translations:
						del scale_keys_dict
						del rot_keys_dict
				# set extend mode for all ipo curves
				if kfc:
					try:
						ipo = action.getChannelIpo(bone_name)
					except ValueError:
						# no channel for bone_name
						pass
					else:
						for b_curve in ipo:
							b_curve.extend = self.nif_common.get_extend_from_flags(kfc.flags)

		# constraints (priority)
		# must be done outside edit mode hence after calling
		for bone_name, b_posebone in b_armature.getPose().bones.items():
			# find bone nif block
			niBone = self.nif_common.blocks[bone_name]
			# store bone priority, if applicable
			if niBone.name in self.nif_common.bone_priorities:
				constr = b_posebone.constraints.append(
					bpy.types.Constraint.NULL)
				constr.name = "priority:%i" % self.nif_common.bone_priorities[niBone.name]

		return b_armature  

	def import_bone(self, niBlock, b_armature, b_armatureData, niArmature):
		"""Adds a bone to the armature in edit mode."""
		# check that niBlock is indeed a bone
		if not self.is_bone(niBlock):
			return None

		# bone length for nubs and zero length bones
		nub_length = 5.0
		scale = 1 / self.nif_common.properties.scale_correction
		# bone name
		bone_name = self.import_name(niBlock, 32)
		niChildBones = [ child for child in niBlock.children
						 if self.is_bone(child) ]
		# create a new bone
		b_bone = Blender.Armature.Editbone()
		# head: get position from niBlock
		armature_space_matrix = self.import_matrix(niBlock,
												   relative_to=niArmature)

		b_bone_head_x = armature_space_matrix[3][0]
		b_bone_head_y = armature_space_matrix[3][1]
		b_bone_head_z = armature_space_matrix[3][2]
		# temporarily sets the tail as for a 0 length bone
		b_bone_tail_x = b_bone_head_x
		b_bone_tail_y = b_bone_head_y
		b_bone_tail_z = b_bone_head_z
		is_zero_length = True
		# tail: average of children location
		if len(niChildBones) > 0:
			m_correction = self.find_correction_matrix(niBlock, niArmature)
			child_matrices = [ self.import_matrix(child,
												  relative_to=niArmature)
							   for child in niChildBones ]
			b_bone_tail_x = sum(child_matrix[3][0]
								for child_matrix
								in child_matrices) / len(child_matrices)
			b_bone_tail_y = sum(child_matrix[3][1]
								for child_matrix
								in child_matrices) / len(child_matrices)
			b_bone_tail_z = sum(child_matrix[3][2]
								for child_matrix
								in child_matrices) / len(child_matrices)
			# checking bone length
			dx = b_bone_head_x - b_bone_tail_x
			dy = b_bone_head_y - b_bone_tail_y
			dz = b_bone_head_z - b_bone_tail_z
			is_zero_length = abs(dx + dy + dz) * 200 < self.nif_common.properties.epsilon
		elif self.nif_common.IMPORT_REALIGN_BONES == 2:
			# The correction matrix value is based on the childrens' head
			# positions.
			# If there are no children then set it as the same as the
			# parent's correction matrix.
			m_correction = self.find_correction_matrix(niBlock._parent,
													   niArmature)
		
		if is_zero_length:
			# this is a 0 length bone, to avoid it being removed
			# set a default minimum length
			if (self.nif_common.IMPORT_REALIGN_BONES == 2) \
			   or not self.is_bone(niBlock._parent):
				# no parent bone, or bone is realigned with correction
				# set one random direction
				b_bone_tail_x = b_bone_head_x + (nub_length * scale)
			else:
				# to keep things neat if bones aren't realigned on import
				# orient it as the vector between this
				# bone's head and the parent's tail
				parent_tail = b_armatureData.bones[
					self.nif_common.names[niBlock._parent]].tail
				dx = b_bone_head_x - parent_tail[0]
				dy = b_bone_head_y - parent_tail[1]
				dz = b_bone_head_z - parent_tail[2]
				if abs(dx + dy + dz) * 200 < self.nif_common.properties.epsilon:
					# no offset from the parent: follow the parent's
					# orientation
					parent_head = b_armatureData.bones[
						self.nif_common.names[niBlock._parent]].head
					dx = parent_tail[0] - parent_head[0]
					dy = parent_tail[1] - parent_head[1]
					dz = parent_tail[2] - parent_head[2]
				direction = Vector(dx, dy, dz)
				direction.normalize()
				b_bone_tail_x = b_bone_head_x + (direction[0] * nub_length * scale)
				b_bone_tail_y = b_bone_head_y + (direction[1] * nub_length * scale)
				b_bone_tail_z = b_bone_head_z + (direction[2] * nub_length * scale)
				
		# sets the bone heads & tails
		b_bone.head = Vector(b_bone_head_x, b_bone_head_y, b_bone_head_z)
		b_bone.tail = Vector(b_bone_tail_x, b_bone_tail_y, b_bone_tail_z)
		
		if self.nif_common.IMPORT_REALIGN_BONES == 2:
			# applies the corrected matrix explicitly
			b_bone.matrix = m_correction.resize4x4() * armature_space_matrix
		elif self.nif_common.IMPORT_REALIGN_BONES == 1:
			# do not do anything, keep unit matrix
			pass
		else:
			# no realign, so use original matrix
			b_bone.matrix = armature_space_matrix

		# set bone name and store the niBlock for future reference
		b_armatureData.bones[bone_name] = b_bone
		# calculate bone difference matrix; we will need this when
		# importing animation
		old_bone_matrix_inv = mathutils.Matrix(armature_space_matrix)
		old_bone_matrix_inv.invert()
		new_bone_matrix = mathutils.Matrix(b_bone.matrix)
		new_bone_matrix.resize4x4()
		new_bone_matrix[3][0] = b_bone_head_x
		new_bone_matrix[3][1] = b_bone_head_y
		new_bone_matrix[3][2] = b_bone_head_z
		# stores any correction or alteration applied to the bone matrix
		# new * inverse(old)
		self.bones_extra_matrix[niBlock] = new_bone_matrix * old_bone_matrix_inv
		# set bone children
		for niBone in niChildBones:
			b_child_bone = self.import_bone(
				niBone, b_armature, b_armatureData, niArmature)
			b_child_bone.parent = b_bone

		return b_bone


	def find_correction_matrix(self, niBlock, niArmature):
		"""Returns the correction matrix for a bone."""
		m_correction = self.IDENTITY44.rotationPart()
		if (self.nif_common.IMPORT_REALIGN_BONES == 2) and self.is_bone(niBlock):
			armature_space_matrix = self.nif_common.import_matrix(niBlock,
													   relative_to=niArmature)

			niChildBones = [ child for child in niBlock.children
							 if self.is_bone(child) ]
			(sum_x, sum_y, sum_z, dummy) = armature_space_matrix[3]
			if len(niChildBones) > 0:
				child_local_matrices = [ self.nif_common.import_matrix(child)
										 for child in niChildBones ]
				sum_x = sum(cm[3][0] for cm in child_local_matrices)
				sum_y = sum(cm[3][1] for cm in child_local_matrices)
				sum_z = sum(cm[3][2] for cm in child_local_matrices)
			list_xyz = [ int(c * 200)
						 for c in (sum_x, sum_y, sum_z,
								   - sum_x, -sum_y, -sum_z) ]
			idx_correction = list_xyz.index(max(list_xyz))
			alignment_offset = 0.0
			if (idx_correction == 0 or idx_correction == 3) and abs(sum_x) > 0:
				alignment_offset = float(abs(sum_y) + abs(sum_z)) / abs(sum_x)
			elif (idx_correction == 1 or idx_correction == 4) and abs(sum_y) > 0:
				alignment_offset = float(abs(sum_z) + abs(sum_x)) / abs(sum_y)
			elif abs(sum_z) > 0:
				alignment_offset = float(abs(sum_x) + abs(sum_y)) / abs(sum_z)
			# if alignment is good enough, use the (corrected) NIF matrix
			# this gives nice ortogonal matrices
			if alignment_offset < 0.25:
				m_correction = self.BONE_CORRECTION_MATRICES[idx_correction]
		return m_correction
	   

	def append_armature_modifier(self, b_obj, b_armature):
		"""Append an armature modifier for the object."""
		b_mod = b_obj.modifiers.append(
			Blender.Modifier.Types.ARMATURE)
		b_mod[Blender.Modifier.Settings.OBJECT] = b_armature
		b_mod[Blender.Modifier.Settings.ENVELOPES] = False
		b_mod[Blender.Modifier.Settings.VGROUPS] = True


	def mark_armatures_bones(self, niBlock):
		"""Mark armatures and bones by peeking into NiSkinInstance blocks."""
		# case where we import skeleton only,
		# or importing an Oblivion or Fallout 3 skeleton:
		# do all NiNode's as bones
		if self.nif_common.properties.skeleton == "SKELETON_ONLY" or (
			self.nif_common.data.version in (0x14000005, 0x14020007) and
			(os.path.basename(self.nif_common.properties.filepath).lower()
			 in ('skeleton.nif', 'skeletonbeast.nif'))):

			if not isinstance(niBlock, NifFormat.NiNode):
				raise NifImportError(
					"cannot import skeleton: root is not a NiNode")
			# for morrowind, take the Bip01 node to be the skeleton root
			if self.nif_common.data.version == 0x04000002:
				skelroot = niBlock.find(block_name='Bip01',
										block_type=NifFormat.NiNode)
				if not skelroot:
					skelroot = niBlock
			else:
				skelroot = niBlock
			if skelroot not in self.nif_common.armatures:
				self.nif_common.armatures[skelroot] = []
			self.nif_common.info("Selecting node '%s' as skeleton root"
							 % skelroot.name)
			# add bones
			for bone in skelroot.tree():
				if bone is skelroot:
					continue
				if not isinstance(bone, NifFormat.NiNode):
					continue
				if self.nif_common.is_grouping_node(bone):
					continue
				if bone not in self.nif_common.armatures[skelroot]:
					self.nif_common.armatures[skelroot].append(bone)
			return # done!

		# attaching to selected armature -> first identify armature and bones
		elif self.nif_common.properties.skeleton == "GEOMETRY_ONLY" and not self.nif_common.armatures:
			skelroot = niBlock.find(block_name=self.nif_common.selected_objects[0].name)
			if not skelroot:
				raise NifImportError(
					"nif has no armature '%s'" % self.nif_common.selected_objects[0].name)
			self.nif_common.debug("Identified '%s' as armature" % skelroot.name)
			self.nif_common.armatures[skelroot] = []
			for bone_name in self.nif_common.selected_objects[0].data.bones.keys():
				# blender bone naming -> nif bone naming
				nif_bone_name = self.nif_common.get_bone_name_for_nif(bone_name)
				# find a block with bone name
				bone_block = skelroot.find(block_name=nif_bone_name)
				# add it to the name list if there is a bone with that name
				if bone_block:
					self.nif_common.info(
						"Identified nif block '%s' with bone '%s' "
						"in selected armature" % (nif_bone_name, bone_name))
					self.nif_common.names[bone_block] = bone_name
					self.nif_common.armatures[skelroot].append(bone_block)
					self.complete_bone_tree(bone_block, skelroot)

		# search for all NiTriShape or NiTriStrips blocks...
		if isinstance(niBlock, NifFormat.NiTriBasedGeom):
			# yes, we found one, get its skin instance
			if niBlock.is_skin():
				self.nif_common.debug("Skin found on block '%s'" % niBlock.name)
				# it has a skin instance, so get the skeleton root
				# which is an armature only if it's not a skinning influence
				# so mark the node to be imported as an armature
				skininst = niBlock.skin_instance
				skelroot = skininst.skeleton_root
				if self.nif_common.properties.skeleton == "EVERYTHING":
					if skelroot not in self.nif_common.armatures:
						self.nif_common.armatures[skelroot] = []
						self.nif_common.debug("'%s' is an armature"
										  % skelroot.name)
				elif self.nif_common.properties.skeleton == "GEOMETRY_ONLY":
					if skelroot not in self.nif_common.armatures:
						raise NifImportError(
							"nif structure incompatible with '%s' as armature:"
							" node '%s' has '%s' as armature"
							% (self.nif_common.selected_objects[0].name, niBlock.name,
							   skelroot.name))

				for i, boneBlock in enumerate(skininst.bones):
					# boneBlock can be None; see pyffi issue #3114079
					if not boneBlock:
						continue
					if boneBlock not in self.nif_common.armatures[skelroot]:
						self.nif_common.armatures[skelroot].append(boneBlock)
						self.nif_common.debug(
							"'%s' is a bone of armature '%s'"
							% (boneBlock.name, skelroot.name))
					# now we "attach" the bone to the armature:
					# we make sure all NiNodes from this bone all the way
					# down to the armature NiNode are marked as bones
					self.complete_bone_tree(boneBlock, skelroot)

				# mark all nodes as bones if asked
				if self.nif_common.IMPORT_EXTRANODES:
					# add bones
					for bone in skelroot.tree():
						if bone is skelroot:
							continue
						if not isinstance(bone, NifFormat.NiNode):
							continue
						if isinstance(bone, NifFormat.NiLODNode):
							# LOD nodes are never bones
							continue
						if self.nif_common.is_grouping_node(bone):
							continue
						if bone not in self.nif_common.armatures[skelroot]:
							self.nif_common.armatures[skelroot].append(bone)
							self.nif_common.debug(
								"'%s' marked as extra bone of armature '%s'"
								% (bone.name, skelroot.name))
							# we make sure all NiNodes from this bone
							# all the way down to the armature NiNode
							# are marked as bones
							self.complete_bone_tree(bone, skelroot)

		# continue down the tree
		for child in niBlock.get_refs():
			if not isinstance(child, NifFormat.NiAVObject): continue # skip blocks that don't have transforms
			self.mark_armatures_bones(child)

	def complete_bone_tree(self, bone, skelroot):
		"""Make sure that the bones actually form a tree all the way
		down to the armature node. Call this function on all bones of
		a skin instance.
		"""
		# we must already have marked this one as a bone
		assert skelroot in self.nif_common.armatures # debug
		assert bone in self.nif_common.armatures[skelroot] # debug
		# get the node parent, this should be marked as an armature or as a bone
		boneparent = bone._parent
		if boneparent != skelroot:
			# parent is not the skeleton root
			if boneparent not in self.nif_common.armatures[skelroot]:
				# neither is it marked as a bone: so mark the parent as a bone
				self.nif_common.armatures[skelroot].append(boneparent)
				# store the coordinates for realignement autodetection 
				self.nif_common.debug("'%s' is a bone of armature '%s'"
								  % (boneparent.name, skelroot.name))
			# now the parent is marked as a bone
			# recursion: complete the bone tree,
			# this time starting from the parent bone
			self.complete_bone_tree(boneparent, skelroot)

	def is_bone(self, niBlock):
		"""Tests a NiNode to see if it's a bone."""
		if not niBlock :
			return False
		for bones in self.nif_common.armatures.values():
			if niBlock in bones:
				return True
		return False

	def is_armature_root(self, niBlock):
		"""Tests a block to see if it's an armature."""
		if isinstance(niBlock, NifFormat.NiNode):
			return  niBlock in self.nif_common.armatures
		return False
		
	def get_closest_bone(self, niBlock, skelroot):
		"""Detect closest bone ancestor."""
		par = niBlock._parent
		while par:
			if par == skelroot:
				return None
			if self.is_bone(par):
				return par
			par = par._parent
		return par

	def get_blender_object(self, niBlock):
		"""Retrieves the Blender object or Blender bone matching the block."""
		if self.is_bone(niBlock):
			boneName = self.nif_common.names[niBlock]
			armatureName = None
			for armatureBlock, boneBlocks in self.nif_common.armatures.items():
				if niBlock in boneBlocks:
					armatureName = self.nif_common.names[armatureBlock]
					break
				else:
					raise NifImportError("cannot find bone '%s'" % boneName)
			armatureObject = Blender.Object.Get(armatureName)
			return armatureObject.data.bones[boneName]
		else:
			return Blender.Object.Get(self.nif_common.names[niBlock])
		   
	def decompose_srt(self, matrix):
		"""Decompose Blender transform matrix as a scale, rotation matrix, and translation vector."""
		# get scale components
		"""b_scale_rot = m.rotationPart()
		b_scale_rot_T = mathutils.Matrix(b_scale_rot)
		b_scale_rot_T.transpose()
		b_scale_rot_2 = b_scale_rot * b_scale_rot_T
		b_scale = mathutils.Vector(b_scale_rot_2[0][0] ** 0.5,\
								   b_scale_rot_2[1][1] ** 0.5,\
								   b_scale_rot_2[2][2] ** 0.5)
		# and fix their sign
		if (b_scale_rot.determinant() < 0): b_scale.negate()
		# only uniform scaling
		if (abs(b_scale[0]-b_scale[1]) >= self.properties.epsilon
			or abs(b_scale[1]-b_scale[2]) >= self.properties.epsilon):
			self.warning(
				"Corrupt rotation matrix in nif: geometry errors may result.")
		b_scale = b_scale[0]
		# get rotation matrix
		b_rot = b_scale_rot * (1.0/b_scale)
		# get translation
		b_trans = m.translationPart()"""
		b_trans_vec, b_rot_quat, b_scale_vec = matrix.decompose()
		# done!
		return [b_trans_vec, b_rot_quat, b_scale_vec]
	
	def store_bones_extra_matrix(self):
		"""Stores correction matrices in a text buffer so that the original
		alignment can be re-exported. In order for this to work it is necessary
		to mantain the imported names unaltered. Since the text buffer is
		cleared on each import only the last import will be exported
		correctly."""
		# clear the text buffer, or create new buffer
		try:
			bonetxt = bpy.data.texts["BoneExMat"]
		except KeyError:
			bonetxt = bpy.data.texts.new("BoneExMat")
		bonetxt.clear()
		# write correction matrices to text buffer
		for niBone, correction_matrix in self.nif_common.bones_extra_matrix.items():
			# skip identity transforms
			if sum(sum(abs(x) for x in row)
				   for row in (correction_matrix - self.IDENTITY44)) \
				< self.nif_common.properties.epsilon:
				continue
			# 'pickle' the correction matrix
			line = ''
			for row in correction_matrix:
				line = '%s;%s,%s,%s,%s' % (line, row[0], row[1], row[2], row[3])
			# we write the bone names with their blender name!
			blender_bone_name = self.nif_common.names[niBone] # NOT niBone.name !!
			# write it to the text buffer
			bonetxt.write('%s/%s\n' % (blender_bone_name, line[1:]))
		
	def store_names(self):
		"""Stores the original, long object names so that they can be
		re-exported. In order for this to work it is necessary to mantain the
		imported names unaltered. Since the text buffer is cleared on each
		import only the last import will be exported correctly."""
		# clear the text buffer, or create new buffer
		try:
			namestxt = bpy.data.texts["FullNames"]
		except KeyError:
			namestxt = bpy.data.texts.new("FullNames")
		namestxt.clear()
		# write the names to the text buffer
		for block, shortname in self.nif_common.names.items():
			if block.name and shortname != block.name:
				namestxt.write('%s;%s\n' % (shortname, block.name))
