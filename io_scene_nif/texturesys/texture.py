"""This script contains helper methods to import/export textures."""

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

import os.path
from functools import reduce 
import operator

import bpy

from pyffi.formats.nif import NifFormat

class texture_import():
	

	def __init__(self, parent):
		self.nif_common = parent
		# dictionary of texture files, to reuse textures
		self.textures = {}

	def get_texture_hash(self, source):
		"""Helper function for import_texture. Returns a key that uniquely
		identifies a texture from its source (which is either a
		NiSourceTexture block, or simply a path string).
		"""
		if not source:
			return None
		elif isinstance(source, NifFormat.NiSourceTexture):
			return source.get_hash()
		elif isinstance(source, str):
			return source.lower()
		else:
			raise TypeError("source must be NiSourceTexture block or string")

	def import_texture(self, source):
		"""Convert a NiSourceTexture block, or simply a path string,
		to a Blender Texture object, return the Texture object and
		stores it in the self.textures dictionary to avoid future
		duplicate imports.
		"""

		# if the source block is not linked then return None
		if not source:
			return None

		# calculate the texture hash key
		texture_hash = self.get_texture_hash(source)

		try:
			# look up the texture in the dictionary of imported textures
			# and return it if found
			return self.textures[texture_hash]
		except KeyError:
			pass

		b_image = None
		
		if (isinstance(source, NifFormat.NiSourceTexture)
			and not source.use_external):
			# find a file name (but avoid overwriting)
			n = 0
			while True:
				fn = "image%03i.dds" % n
				tex = os.path.join(
					os.path.dirname(self.properties.filepath), fn)
				if not os.path.exists(tex):
					break
				n += 1
			if self.IMPORT_EXPORTEMBEDDEDTEXTURES:
				# save embedded texture as dds file
				stream = open(tex, "wb")
				try:
					self.nif_common.info("Saving embedded texture as %s" % tex)
					source.pixel_data.save_as_dds(stream)
				except ValueError:
					# value error means that the pixel format is not supported
					b_image = None
				else:
					# saving dds succeeded so load the file
					b_image = bpy.ops.image.open(tex)
					# Blender will return an image object even if the
					# file format is not supported,
					# so to check if the image is actually loaded an error
					# is forced via "b_image.size"
					try:
						b_image.size
					except: # RuntimeError: couldn't load image data in Blender
						b_image = None # not supported, delete image object
				finally:
					stream.close()
			else:
				b_image = None
		else:
			# the texture uses an external image file
			if isinstance(source, NifFormat.NiSourceTexture):
				fn = source.file_name.decode()
			elif isinstance(source, str):
				fn = source
			else:
				raise TypeError(
					"source must be NiSourceTexture or str")
			fn = fn.replace( '\\', os.sep )
			fn = fn.replace( '/', os.sep )
			# go searching for it
			importpath = os.path.dirname(self.nif_common.properties.filepath)
			searchPathList = [importpath]
			if self.nif_common.context.user_preferences.filepaths.texture_directory:
				searchPathList.append(
					self.nif_common.context.user_preferences.filepaths.texture_directory)
			# if it looks like a Morrowind style path, use common sense to
			# guess texture path
			meshes_index = importpath.lower().find("meshes")
			if meshes_index != -1:
				searchPathList.append(importpath[:meshes_index] + 'textures')
			# if it looks like a Civilization IV style path, use common sense
			# to guess texture path
			art_index = importpath.lower().find("art")
			if art_index != -1:
				searchPathList.append(importpath[:art_index] + 'shared')
			# go through all texture search paths
			for texdir in searchPathList:
				texdir = texdir.replace( '\\', os.sep )
				texdir = texdir.replace( '/', os.sep )
				# go through all possible file names, try alternate extensions
				# too; for linux, also try lower case versions of filenames
				texfns = reduce(operator.add,
								[ [ fn[:-4]+ext, fn[:-4].lower()+ext ]
								  for ext in ('.DDS','.dds','.PNG','.png',
											 '.TGA','.tga','.BMP','.bmp',
											 '.JPG','.jpg') ] )
				texfns = [fn, fn.lower()] + list(set(texfns))
				for texfn in texfns:
					# now a little trick, to satisfy many Morrowind mods
					if (texfn[:9].lower() == 'textures' + os.sep) \
					   and (texdir[-9:].lower() == os.sep + 'textures'):
						# strip one of the two 'textures' from the path
						tex = os.path.join( texdir[:-9], texfn )
					else:
						tex = os.path.join( texdir, texfn )
					# "ignore case" on linux
					tex = bpy.path.resolve_ncase(tex)
					self.nif_common.debug("Searching %s" % tex)
					if os.path.exists(tex):
						# tries to load the file
						b_image = bpy.data.images.load(tex)
						# Blender will return an image object even if the
						# file format is not supported,
						# so to check if the image is actually loaded an error
						# is forced via "b_image.size"
						try:
							b_image.size
						except: # RuntimeError: couldn't load image data in Blender
							b_image = None # not supported, delete image object
						else:
							# file format is supported
							self.nif_common.debug("Found '%s' at %s" % (fn, tex))
							break
				if b_image:
					break
			else:
				tex = os.path.join(searchPathList[0], fn)

		# create a stub image if the image could not be loaded
		if not b_image:
			self.nif_common.warning(
				"Texture '%s' not found or not supported"
				" and no alternate available"
				% fn)
			b_image = bpy.data.images.new(
				name=fn, width=1, height=1, alpha=False)
			# TODO is this still needed? commented out for now
			# b_image.filepath = tex

		# create a texture
		b_texture = bpy.data.textures.new(name="Tex", type='IMAGE')
		b_texture.image = b_image
		b_texture.use_interpolation = True
		b_texture.use_mipmap = True

		# save texture to avoid duplicate imports, and return it
		self.textures[texture_hash] = b_texture
		return b_texture
