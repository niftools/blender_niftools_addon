'''Script to import/export all the skeleton related objects.'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.nif_logging import NifLog

class Armature():
	
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
		self.nif_import = parent
		self.properties = parent.properties
		
	def import_armature(self, niArmature):
		"""Scans an armature hierarchy, and returns a whole armature.
		This is done outside the normal node tree scan to allow for positioning
		of the bones before skins are attached."""
		armature_name = self.nif_import.import_name(niArmature)

		b_armatureData = bpy.data.armatures.new(armature_name)
		#b_armatureData.use_vertex_groups = True
		#b_armatureData.use_bone_envelopes = False
		b_armatureData.show_names = True
		b_armatureData.show_axes = True
		b_armatureData.draw_type = 'STICK'
		b_armature = bpy.data.objects.new(armature_name, b_armatureData)
		b_armature.select = True
		b_armature.show_x_ray = True
		
		#Link object to scene
		scn = bpy.context.scene
		scn.objects.link(b_armature)
		scn.objects.active = b_armature
		scn.update()
		
		# make armature editable and create bones
		bpy.ops.object.mode_set(mode='EDIT',toggle=False)
		niChildBones = [child for child in niArmature.children
						if self.is_bone(child)]
		for niBone in niChildBones:
			self.import_bone(
				niBone, b_armature, b_armatureData, niArmature)
			
		bpy.ops.object.mode_set(mode='OBJECT',toggle=False)
		scn = bpy.context.scene
		scn.objects.active = b_armature
		scn.update()

		# The armature has been created in editmode,
		# now we are ready to set the bone keyframes.
		if self.properties.animation:
			self.nif_import.animationhelper.armature_animation.import_armature_animation(b_armature)
			
		# constraints (priority)
		# must be done outside edit mode hence after calling
		for bone_name, b_posebone in b_armature.pose.bones.items():
			# find bone nif block
			if bone_name.startswith("InvMarker"):
				bone_name = "InvMarker"
			niBone = self.nif_import.dict_blocks[bone_name]
			# store bone priority, if applicable
			if niBone.name in self.nif_import.dict_bone_priorities:
				constr = b_posebone.constraints.append(
					bpy.types.ConstraintNULL)
				constr.name = "priority:%i" % self.nif_import.dict_bone_priorities[niBone.name]
		
		bpy.ops.object.mode_set(mode='EDIT',toggle=False)
		bpy.ops.object.mode_set(mode='OBJECT',toggle=False)
		
		scn = bpy.context.scene
		scn.objects.active = b_armature
		scn.update()
		return b_armature  

	def import_bone(self, niBlock, b_armature, b_armatureData, niArmature):
		"""Adds a bone to the armature in edit mode."""
		bpy.ops.object.mode_set(mode='EDIT',toggle=False)
		# check that niBlock is indeed a bone
		if not self.is_bone(niBlock):
			return None

		# bone length for nubs and zero length bones
		nub_length = 5.0
		scale = self.properties.scale_correction_import
		# bone name
		bone_name = self.nif_import.import_name(niBlock)
		niChildBones = [ child for child in niBlock.children
						 if self.is_bone(child) ]
		# create a new bone
		b_bone = b_armatureData.edit_bones.new(bone_name)
		#Sets active so edit bones are marked selected after import
		b_armatureData.edit_bones.active = b_bone
		# head: get position from niBlock
		armature_space_matrix = nif_utils.import_matrix(niBlock,
												   relative_to=niArmature)

		b_bone_head_x = armature_space_matrix[0][3]
		b_bone_head_y = armature_space_matrix[1][3]
		b_bone_head_z = armature_space_matrix[2][3]
		# temporarily sets the tail as for a 0 length bone
		b_bone_tail_x = b_bone_head_x
		b_bone_tail_y = b_bone_head_y
		b_bone_tail_z = b_bone_head_z
		is_zero_length = True
		# tail: average of children location
		if len(niChildBones) > 0:
			m_correction = self.find_correction_matrix(niBlock, niArmature)
			child_matrices = [ nif_utils.import_matrix(child,
												  relative_to=niArmature)
							   for child in niChildBones ]
			b_bone_tail_x = sum(child_matrix[0][3]
								for child_matrix
								in child_matrices) / len(child_matrices)
			b_bone_tail_y = sum(child_matrix[1][3]
								for child_matrix
								in child_matrices) / len(child_matrices)
			b_bone_tail_z = sum(child_matrix[2][3]
								for child_matrix
								in child_matrices) / len(child_matrices)
			# checking bone length
			dx = b_bone_head_x - b_bone_tail_x
			dy = b_bone_head_y - b_bone_tail_y
			dz = b_bone_head_z - b_bone_tail_z
			is_zero_length = abs(dx + dy + dz) * 200 < self.properties.epsilon
		elif self.properties.import_realign_bones == 2:
			# The correction matrix value is based on the childrens' head
			# positions.
			# If there are no children then set it as the same as the
			# parent's correction matrix.
			m_correction = self.find_correction_matrix(niBlock._parent,
													   niArmature)
		
		if is_zero_length:
			# this is a 0 length bone, to avoid it being removed
			# set a default minimum length
			if (self.properties.import_realign_bones == 2) \
			   or not self.is_bone(niBlock._parent):
				# no parent bone, or bone is realigned with correction
				# set one random direction
				b_bone_tail_x = b_bone_head_x + (nub_length * scale)
			else:
				# to keep things neat if bones aren't realigned on import
				# orient it as the vector between this
				# bone's head and the parent's tail
				parent_tail = b_armatureData.edit_bones[
					self.nif_import.dict_names[niBlock._parent]].tail
				dx = b_bone_head_x - parent_tail[0]
				dy = b_bone_head_y - parent_tail[1]
				dz = b_bone_head_z - parent_tail[2]
				if abs(dx + dy + dz) * 200 < self.properties.epsilon:
					# no offset from the parent: follow the parent's
					# orientation
					parent_head = b_armatureData.edit_bones[
						self.nif_import.dict_names[niBlock._parent]].head
					dx = parent_tail[0] - parent_head[0]
					dy = parent_tail[1] - parent_head[1]
					dz = parent_tail[2] - parent_head[2]
				direction = mathutils.Vector((dx, dy, dz))
				direction.normalize()
				b_bone_tail_x = b_bone_head_x + (direction[0] * nub_length * scale)
				b_bone_tail_y = b_bone_head_y + (direction[1] * nub_length * scale)
				b_bone_tail_z = b_bone_head_z + (direction[2] * nub_length * scale)
				
		# sets the bone heads & tails
		b_bone.head = mathutils.Vector((b_bone_head_x, b_bone_head_y, b_bone_head_z))
		b_bone.tail = mathutils.Vector((b_bone_tail_x, b_bone_tail_y, b_bone_tail_z))
		
		# set bone name and store the niBlock for future reference
		bpy.ops.object.mode_set(mode='OBJECT',toggle=False)
		b_bone = b_armatureData.bones[bone_name]
		
		if self.properties.import_realign_bones == 2:
			# applies the corrected matrix explicitly
			b_bone.matrix_local = m_correction.resize_4x4() * armature_space_matrix
		elif self.properties.import_realign_bones == 1:
			# do not do anything, keep unit matrix
			pass
		else:
			# no realign, so use original matrix
			b_bone.matrix_local = armature_space_matrix
		
		# calculate bone difference matrix; we will need this when
		# importing animation
		old_bone_matrix_inv = mathutils.Matrix(armature_space_matrix)
		old_bone_matrix_inv.invert()
		new_bone_matrix = mathutils.Matrix(b_bone.matrix)
		new_bone_matrix.resize_4x4()
		new_bone_matrix[0][3] = b_bone_head_x
		new_bone_matrix[1][3] = b_bone_head_y
		new_bone_matrix[2][3] = b_bone_head_z
		# stores any correction or alteration applied to the bone matrix
		# new * inverse(old)
		self.nif_import.dict_bones_extra_matrix[niBlock] = new_bone_matrix * old_bone_matrix_inv
		# set bone children
		for niBone in niChildBones:
			b_child_bone = self.import_bone(
				niBone, b_armature, b_armatureData, niArmature)
			bpy.ops.object.mode_set(mode='EDIT',toggle=False)
			b_bone = b_armatureData.edit_bones[bone_name]
			b_child_bone = b_armatureData.edit_bones[b_child_bone.name]
			b_child_bone.parent = b_bone
			bpy.ops.object.mode_set(mode='OBJECT',toggle=False)
			b_bone = b_armatureData.bones[bone_name]


		
		return b_bone


	def find_correction_matrix(self, niBlock, niArmature):
		"""Returns the correction matrix for a bone."""
		m_correction = self.IDENTITY44.to_3x3()
		if (self.properties.import_realign_bones == 2) and self.is_bone(niBlock):
			armature_space_matrix = nif_utils.import_matrix(niBlock,
													   relative_to=niArmature)

			niChildBones = [ child for child in niBlock.children
							 if self.is_bone(child) ]
			(sum_x, sum_y, sum_z, dummy) = armature_space_matrix[3]
			if len(niChildBones) > 0:
				child_local_matrices = [ nif_utils.import_matrix(child)
										 for child in niChildBones ]
				sum_x = sum(cm[0][3] for cm in child_local_matrices)
				sum_y = sum(cm[1][3] for cm in child_local_matrices)
				sum_z = sum(cm[2][3] for cm in child_local_matrices)
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
		armature_name = b_armature.name
		b_mod = b_obj.modifiers.new(armature_name,'ARMATURE')
		b_mod.object = b_armature
		b_mod.use_bone_envelopes = False
		b_mod.use_vertex_groups = True


	def mark_armatures_bones(self, niBlock):
		"""Mark armatures and bones by peeking into NiSkinInstance blocks."""
		# case where we import skeleton only,
		# or importing an Oblivion or Fallout 3 skeleton:
		# do all NiNode's as bones
		if self.properties.skeleton == "SKELETON_ONLY" or (
			self.nif_import.data.version in (0x14000005, 0x14020007) and
			(os.path.basename(self.properties.filepath).lower()
			 in ('skeleton.nif', 'skeletonbeast.nif'))):

			if not isinstance(niBlock, NifFormat.NiNode):
				raise nif_utils.NifError(
					"cannot import skeleton: root is not a NiNode")
			# for morrowind, take the Bip01 node to be the skeleton root
			if self.nif_import.data.version == 0x04000002:
				skelroot = niBlock.find(block_name='Bip01',
										block_type=NifFormat.NiNode)
				if not skelroot:
					skelroot = niBlock
			else:
				skelroot = niBlock
			if skelroot not in self.nif_import.dict_armatures:
				self.nif_import.dict_armatures[skelroot] = []
			NifLog.info("Selecting node '%s' as skeleton root".format(skelroot.name))
			# add bones
			for bone in skelroot.tree():
				if bone is skelroot:
					continue
				if not isinstance(bone, NifFormat.NiNode):
					continue
				if self.nif_import.is_grouping_node(bone):
					continue
				if bone not in self.nif_import.dict_armatures[skelroot]:
					self.nif_import.dict_armatures[skelroot].append(bone)
			return # done!

		# attaching to selected armature -> first identify armature and bones
		elif self.properties.skeleton == "GEOMETRY_ONLY" and not self.nif_import.dict_armatures:
			skelroot = niBlock.find(
							block_name=self.nif_import.selected_objects[0].name)
			if not skelroot:
				raise nif_utils.NifError("nif has no armature '%s'" % 
									self.nif_import.selected_objects[0].name)
			NifLog.debug("Identified '{0}' as armature".format(skelroot.name))
			self.nif_import.dict_armatures[skelroot] = []
			for bone_name in self.nif_import.selected_objects[0].data.bones.keys():
				# blender bone naming -> nif bone naming
				nif_bone_name = self.nif_import.get_bone_name_for_nif(bone_name)
				# find a block with bone name
				bone_block = skelroot.find(block_name=nif_bone_name)
				# add it to the name list if there is a bone with that name
				if bone_block:
					NifLog.info("Identified nif block '{0}' with bone '{1}' in selected armature".format(nif_bone_name, bone_name))
					self.nif_import.dict_names[bone_block] = bone_name
					self.nif_import.dict_armatures[skelroot].append(bone_block)
					self.complete_bone_tree(bone_block, skelroot)

		# search for all NiTriShape or NiTriStrips blocks...
		if isinstance(niBlock, NifFormat.NiTriBasedGeom):
			# yes, we found one, get its skin instance
			if niBlock.is_skin():
				NifLog.debug("Skin found on block '{0}'".format(niBlock.name))
				# it has a skin instance, so get the skeleton root
				# which is an armature only if it's not a skinning influence
				# so mark the node to be imported as an armature
				skininst = niBlock.skin_instance
				skelroot = skininst.skeleton_root
				if self.properties.skeleton == "EVERYTHING":
					if skelroot not in self.nif_import.dict_armatures:
						self.nif_import.dict_armatures[skelroot] = []
						NifLog.debug("'{0}' is an armature".format(skelroot.name))
				elif self.properties.skeleton == "GEOMETRY_ONLY":
					if skelroot not in self.nif_import.dict_armatures:
						raise nif_utils.NifError(
							"nif structure incompatible with '%s' as armature:"
							" node '%s' has '%s' as armature"
							% (self.nif_import.selected_objects[0].name, niBlock.name,
							   skelroot.name))

				for boneBlock in skininst.bones:
					# boneBlock can be None; see pyffi issue #3114079
					if not boneBlock:
						continue
					if boneBlock not in self.nif_import.dict_armatures[skelroot]:
						self.nif_import.dict_armatures[skelroot].append(boneBlock)
						NifLog.debug("'{0}' is a bone of armature '{1}'".format(boneBlock.name, skelroot.name))
					# now we "attach" the bone to the armature:
					# we make sure all NiNodes from this bone all the way
					# down to the armature NiNode are marked as bones
					self.complete_bone_tree(boneBlock, skelroot)

				# mark all nodes as bones if asked
				if self.nif_import.IMPORT_EXTRANODES:
					# add bones
					for bone in skelroot.tree():
						if bone is skelroot:
							continue
						if not isinstance(bone, NifFormat.NiNode):
							continue
						if isinstance(bone, NifFormat.NiLODNode):
							# LOD nodes are never bones
							continue
						if self.nif_import.is_grouping_node(bone):
							continue
						if bone not in self.nif_import.dict_armatures[skelroot]:
							self.nif_import.dict_armatures[skelroot].append(bone)
							NifLog.debug("'{0}' marked as extra bone of armature '{1}'".format(bone.name, skelroot.name))
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
		assert skelroot in self.nif_import.dict_armatures # debug
		assert bone in self.nif_import.dict_armatures[skelroot] # debug
		# get the node parent, this should be marked as an armature or as a bone
		boneparent = bone._parent
		if boneparent != skelroot:
			# parent is not the skeleton root
			if boneparent not in self.nif_import.dict_armatures[skelroot]:
				# neither is it marked as a bone: so mark the parent as a bone
				self.nif_import.dict_armatures[skelroot].append(boneparent)
				# store the coordinates for realignement autodetection 
				NifLog.debug("'{0}' is a bone of armature '{1}'".format(boneparent.name, skelroot.name))
			# now the parent is marked as a bone
			# recursion: complete the bone tree,
			# this time starting from the parent bone
			self.complete_bone_tree(boneparent, skelroot)

	def is_bone(self, niBlock):
		"""Tests a NiNode to see if it's a bone."""
		if not niBlock :
			return False
		for bones in self.nif_import.dict_armatures.values():
			if niBlock in bones:
				return True
		return False

	def is_armature_root(self, niBlock):
		"""Tests a block to see if it's an armature."""
		if isinstance(niBlock, NifFormat.NiNode):
			return  niBlock in self.nif_import.dict_armatures
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
			bone_name = self.nif_import.dict_names[niBlock]
			armatureName = None
			for armatureBlock, boneBlocks in self.nif_import.dict_armatures.items():
				if niBlock in boneBlocks:
					armatureName = self.nif_import.dict_names[armatureBlock]
					break
				else:
					raise nif_utils.NifError("cannot find bone '%s'" % bone_name)
			armatureObject = bpy.types.Object(armatureName)
			return armatureObject.data.bones[bone_name]
		else:
			return bpy.types.Object(self.nif_import.dict_names[niBlock])
		

	def decompose_srt(self, matrix):
		"""Decompose Blender transform matrix as a scale, rotation matrix, and translation vector."""
		# get scale components
		trans_vec, rot_quat, scale_vec = matrix.decompose()
		scale_rot = rot_quat.to_matrix()
		b_scale = mathutils.Vector((scale_vec[0] ** 0.5,\
                         			scale_vec[1] ** 0.5,\
                            		scale_vec[2] ** 0.5))
		# and fix their sign
		if (scale_rot.determinant() < 0): b_scale.negate()
		# only uniform scaling
		if (abs(scale_vec[0]-scale_vec[1]) >= self.properties.epsilon
			or abs(scale_vec[1]-scale_vec[2]) >= self.properties.epsilon):
			NifLog.warn("Corrupt rotation matrix in nif: geometry errors may result.")
		b_scale = b_scale[0]
		# get rotation matrix
		b_rot = scale_rot * b_scale
		# get translation
		b_trans = trans_vec
		# done!
		return [b_scale, b_rot, b_trans]
	
	
	def store_bones_extra_matrix(self):
		"""Stores correction matrices in a text buffer so that the original
		alignment can be re-exported. In order for this to work it is necessary
		to mantain the imported names unaltered. Since the text buffer is
		cleared on each import only the last import will be exported
		correctly."""
		# clear the text buffer, or create new buffer
		try:
			bonetxt = bpy.data.texts["BoneExMat"]
			bonetxt.clear()
		except KeyError:
			bonetxt = bpy.data.texts.new("BoneExMat")
		# write correction matrices to text buffer
		for niBone, correction_matrix in self.nif_import.dict_bones_extra_matrix.items():
			# skip identity transforms
			if sum(sum(abs(x) for x in row)
				   for row in (correction_matrix - self.IDENTITY44)) \
				< self.properties.epsilon:
				continue
			# 'pickle' the correction matrix
			line = ''
			for row in correction_matrix:
				line = '%s;%s,%s,%s,%s' % (line, row[0], row[1], row[2], row[3])
			# we write the bone names with their blender name!
			blender_bone_name = self.nif_import.dict_names[niBone] # NOT niBone.name !!
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
			namestxt.clear()
		except KeyError:
			namestxt = bpy.data.texts.new("FullNames")
			
		# write the names to the text buffer
		for block, shortname in self.nif_import.dict_names.items():
			block_name = block.name.decode()
			if block_name and shortname != block_name:
				namestxt.write('%s;%s\n' % (shortname, block_name))
				
				