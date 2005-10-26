#!BPY

""" Registration info for Blender menus:
Name: 'Netimmerse 4.0.0.2 (.nif)'
Blender: 237
Group: 'Import'
Tip: 'Load a Netimmerse File'
"""

__author__ = "Alessandro Garosi (AKA Brandano) -- tdo_brandano@hotmail.com"
__url__ = ("blender", "elysiun",
"development group at http://games.groups.yahoo.com/group/NIFLA/")
__version__ = "1.0.7"

__bpydoc__ = """\
This script imports Netimmerse (the version used by Morrowind) .NIF files to Blender
So far the script has been tested with 4.0.0.2 format files (Morrowind, Freedom Force)

Usage:

Run this script from "File->Import" menu and then select the desired NIF file.
"""
# nif4_import_237.py version 1.0.7
# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
#BSD License
#
#Copyright (c) 2005, NIF File Format Library and Tools
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met:
#1. Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#3. The name of the NIF File Format Library and Tools project may not be
#   used to endorse or promote products derived from this software
#   without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****
# Note: Versions of this script previous to 1.0.6 were released under the GPL license
# The script includes small portions of code obtained in the public domain, in particular
# the binary conversion functions. Every attempt to contact (or actually identify!) the
# original author has so far been fruitless.
# I have no claim of ownership these functions and will remove and replace them with
# a (probably less efficient) version if the original author ever will ask me to.
# --------------------------------------------------------------------------
#
# Credits:
# Portions of this programs are (were) derived (through the old tested method of cut'n paste)
# from the obj import script obj_import.py: OBJ Import v0.9 by Campbell Barton (AKA Ideasman)
# (No more. I rewrote the lot. Nevertheless I wouldn't have been able to start this without Ideasman's
# script to read from!)
# Binary conversion functions are courtesy of SJH. Couldn't find the full name, and couldn't find any
# license info, I got the code for these from http://projects.blender.org/pipermail/bf-python/2004-July/001676.html
# The file reading strategy was 'inspired' by the NifToPoly script included with the 
# DAOC mapper, which used to be available at http://www.randomly.org/projects/mapper/ and was written and 
# is copyright 2002 of Oliver Jowett. His domain and e-mail address are however no longer reacheable.
# No part of the original code is included here, as I pretty much rewrote everything, hence this is the 
# only mention of the original copyright. An updated version of the script is included with the DAOC Mappergui
# application, available at http://nathrach.republicofnewhome.org/mappergui.html
#
# Thanks go to:
# Campbell Barton (AKA Ideasman, Cambo) for making code clear enough to be used as a learning resource.
#	Hey, this is my first ever python script!
# SJH for the binary conversion functions. Got the code off a forum somewhere, posted by Ideasman,
#	I suppose it's allright to use it
# Lars Rinde (AKA Taharez), for helping me a lot with the file format, and with some debugging even
#	though he doesn't 'do Python'
# Timothy Wakeham (AKA timmeh), for taking some of his time to help me get to terms with the way
#   the UV maps work in Blender
# Amorilia (don't know your name buddy), for bugfixes and testing.

import Blender, sys

from Blender import Scene, Object, NMesh, Armature, Image, Texture, Material

from Blender.Mathutils import *

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Missing python installation warning
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
try:
	import re, struct, math
except:
	err = """--------------------------
ERROR\nThis script requires a full Python installation to run.
Python minimum required version:
%s
--------------------------""" % sys.version
	print err
	Blender.Draw.PupMenu("ERROR%t|Python installation not found, check console for details")
	raise

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Constants and global variables
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

# Texture folders
global textureFolders
textureFolders = []
# first try the nif location
textureFolders.append( "NIFDIR" )
# then be smart and have a guess
textureFolders.append( "SMARTGUESS" )
# if you have installed morrowind uncomment the following two lines
#textureFolders.append( "C:\\Program Files\\Bethesda\\Morrowind\\Data Files\\Textures" )
#textureFolders.append( "C:\\Program Files\\Bethesda\\Morrowind\\Data Files" )
# if you have additional texture foldes put them here
#textureFolders.append( "E:\\Data Files\\Textures" )
#textureFolders.append( "E:\\Data Files" )
# if you like to use the textures on the TESCS CD uncomment the following two line
#textureFolders.append( "D:\\Data Files\\Textures" )
#textureFolders.append( "D:\\Data Files" )
# NOTE:
# all original morrowind nifs use 'name.ext' only for addressing the textures
# but most mods use something like 'textures\[subdir\]name.ext'
# this is due to a 'feature' in morrowind's resource manager:
# it loads 'name.ext', 'textures/name.ext' and 'textures/subdir/name.ext' but NOT 'subdir/name.ext'
# by putting both 'data files' and 'data files/textures' in here
# we make sure all textures are found

global nifdir
nifdir = ''
global texdir
texdir = ''


# list of NiObject blocks
global NiObjects
NiObjects = []
# dictionary of texture files
global textures
textures = {}
# dictionary of materials
global materials
materials = {}
# Controls how many debug messages are dumped to the console
verbose = 2
# Two regular expressions. They are used within several loops, so there is no need to
# recompile them all the time.
# The DOTALL flag has the '.' operator match newline characters too. So I have 4 generic 
# bytes, followed by the letters Ni and an uppercase letter within A-Z
# RootCollisionNode is probably a Bethseda extension # amorilia
re_nameStart = re.compile('.{4}(Ni[A-Z]|RootCollisionNode)', re.DOTALL) # amorilia
# The 'r' before the regexp forces the use of a raw string, so that I don't need to
# escape the character \. Way to save on a keystroke. Helps readability, though
re_name = re.compile(r'^(Ni[A-Z][\w\s]*|RootCollisionNode)$') # amorilia
# This matches a three digits versioned name (ie Material.001)
re_versioned = re.compile(r'^.*\.[0-9]{3}$')
# This matches a '.dds' file extension
re_ddsExt = re.compile(r'^\.dds$', re.IGNORECASE)
# Geometries within the NIF files are stored with a size and/or orentation that are unpractical
# for editing within blender. These matrices allow me to scale the mesh on import
# to be more suitable for editing, and to do the inverse operation when exporting.
nifToBlendXform = Matrix( # Scale x 0.1
	[ 0.1,  0.0,  0.0,  0.0],
	[ 0.0,  0.1,  0.0,  0.0],
	[ 0.0,  0.0,  0.1,  0.0],
	[ 0.0,  0.0,  0.0,  1.0])
epsilon = 0.005 # used for checking equality of floats

#Blender 'invert()' method modifies the original matrix rather than returning a new one. 
def invert(mat):
	out = CopyMat(mat)
	out.invert()
	return out

# inverse of the import matrix, scales things back x 10
blendToNifXform = invert(nifToBlendXform)

#Identity matrix, does nothing
nullXform = Matrix()
nullXform.identity()


#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Miscellaneous utilities
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

# This section of the code is taken nearly verbatim off Ideasman's OBJ importer,
# and replaces the function written by Amorilia. It offers a slight increase in performance
#===========================================================================#
# Returns unique name of object/mesh (preserve overwriting existing meshes) #
#===========================================================================#
def getUniqueName(name):
	uniqueInt = 0
	while 1:
		try:
			ob = Object.Get(name)
			# Okay, this is working, so lets make a new name
			name = '%s.%02d' % (name, uniqueInt)
			uniqueInt +=1
		except:
			if name not in NMesh.GetNames():
				return name
			else:
				name = '%s.%02d' % (name, uniqueInt)
				uniqueInt +=1


# Little wrapper for debug messages
def debugMsg(message='-', level=2):
	if verbose >= level:
		print message

# Applies a transform matrix to a coordinate
def pointTransform(point, matrix):
	(x, y, z) = point
	m = CopyMat(matrix)
	m.resize4x4() 
	outX = x*m[0][0] + y*m[1][0] + z*m[2][0] + m[3][0]
	outY = x*m[0][1] + y*m[1][1] + z*m[2][1] + m[3][1]
	outZ = x*m[0][2] + y*m[1][2] + z*m[2][2] + m[3][2]
	return [outX, outY, outZ]

# Returns the distance between two sets of coordinates, as long as they share the same coordinates system
def distance(pa, pb):
	dx = pa[0]-pb[0]
	dy = pa[1]-pb[1]
	dz = pa[2]-pb[2]
	return math.sqrt(dx*dx + dy*dy + dz*dz)

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Binary conversion functions (binary_pack_unpack.py, created by SJH)
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
nybblechr_to_01_dqs={'-':'-','0':'0000', '1':'0001', '2':'0010', '3':'0011', '4':'0100', '5':'0101', '6':'0110', '7':'0111', '8':'1000', '9':'1001', 'A':'1010', 'B':'1011', 'C':'1100', 'D':'1101', 'E':'1110', 'F':'1111', 'a':'1010', 'b':'1011', 'c':'1100', 'd':'1101', 'e':'1110', 'f':'1111'}

# Into to binary
def i2b(j, wd=0):
	return ''.join(map(nybblechr_to_01_dqs.__getitem__, '%02X' % j))[-wd:].zfill(wd)      # SJH 07/29/2004 20:26:03

# Char to binary
def c2b(c, wd=0):
	return ''.join(map(nybblechr_to_01_dqs.__getitem__, '%02X' % ord(c)))[-wd:].zfill(wd) # SJH 07/29/2004 20:26:03

# String to binary
def s2b(s, wd=0):
	return ''.join(map(nybblechr_to_01_dqs.__getitem__, '%02X'*len(s) % tuple(map(ord, s))))[-wd:].zfill(wd) # SJH 07/29/2004 20:26:03

# Binary to char
def b2c(b):
	chr(int(b,2))

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- File parsing functions. These read the layout of the file
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
# this function finds the first occurrence of a Nif Block in a block of data, and returns
# the index and the type of the node. It's a bit experimental. I look for the 'Ni' string,
# followed by an uppercase character, then check if I have a reasonable name length before it
# Nothing new, Taharez was already there ages ago.
def findNextBlock(data, offset):
	"""
		Finds the first occourrence of a Nif Block in the block of data passed as a parameter, and returns
		the node type and its start index
	"""
	# Offset is an index from the start of data for reading the various bits and bobs
	name = None
	while offset < len(data):
		match = re_nameStart.search(data[offset : ])
		# There is no chance to find a node here, nothing matches a node start
		# so I'll break, leave the node at None and set the offset to the end of the block
		if not match:
			offset = len(data)
			break
		# This could be a node, so I'll test if it fulfils a node name's requirements
		# first I'll extract the name
		offset += match.start()
		# I won't be overwriting the offset with a new value here, this might not be a
		# node, hence the dummy
		name, dummy =readString(data, offset)
		# Then comes the test. If the name is short enough and only uses standard
		# characters it's a wrap
		if len(name) < 65 and re_name.match(name):
			break
		# Else I'll have to skip this match and try for the next. 7 is the length
		# of the string matched by the regexp
		offset += 7
	# It's unlikely, but in the case I found something that looks like a block name but isn't one
	# I might end up consuming the datablock and leaving the function with an offset bigger than
	# its length
	if offset > len(data):
		offset = len(data)
	return name, offset
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- File reading functions. You don't need me to explain these
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
# Reads a vertex block
def readVerts(data):
	"""
		Reads the vertices from a chunk of vertex data.
	"""
	vertCount=len(data)/12
	offset = 0
	verts = [None] * vertCount
	debugMsg('Reading vertex block', 3)
	for i in range(vertCount):
		# Ok, struct.unpack always returns a tuple, even if it returns oly the one value.
		# So I'll just use the behaviour and unpack all three coordinates at once
		# Writing '<3f' is the same as writing '<fff', three little endian floats
		x, y, z = struct.unpack('<3f', data[ offset : offset + 12 ])
		offset += 12
		debugMsg('x= %06f; y=%06f; z=%06f' % (x, y, z), 3)
		verts[i] = [x, y, z]
	return verts

# Reads a vertex normals block
def readVertexNormals(data):
	"""
		Reads the vertex Normals from a chunk of normal data.
	"""
	normCount=len(data)/12
	offset = 0
	vertNormals = [None] * normCount
	debugMsg('Reading vertex normals block', 3)
	for i in range(normCount):
		# Same job as in ReadVerts
		(x, y, z) = struct.unpack('<3f', data[ offset : offset + 12 ])
		offset += 12
		debugMsg('x= %06f; y=%06f; z=%06f' % (x, y, z), 3)
		vertNormals[i] = [x, y, z]
	return vertNormals

# Reads a vertex color data block
def readVertColor(data):
	"""
		Reads the vertex colors from a chunk of vertex color data.
	"""
	vertColCount=len(data)/16
	offset = 0
	vertColor = [None] * vertColCount
	debugMsg('Reading vertex colors block', 3)
	for i in range(vertColCount):
		(r, g, b, a) = struct.unpack('<4f', data[ offset : offset + 16 ])
		offset += 16
		debugMsg('r= %06f; g=%06f; b=%06f; a=%06f' % (r, g, b, a), 3)
		vertColor[i] = [r, g, b, a]
	return vertColor

# Reads a faces block
def readFaces(data):
	"""
		Reads the faces from a chunk of face data.
	"""
	facesCount=len(data)/6
	offset = 0
	faces = [None] * facesCount
	debugMsg('Reading faces block', 3)
	for i in range(facesCount):
		# Same story as the vertex reader function. the vertices are the
		# indices of the vertices array
		(v1, v2, v3) = struct.unpack('<3H', data[ offset : offset + 6 ])
		offset += 6
		debugMsg('v1=%04i; v2=%04i; v3=%04i' % (v1, v2, v3), 3)
		faces[i] = [v1, v2, v3]
	return faces

# Reads an UV mapping coordinates block
def readUVMap(data):
	UVMapCount=len(data)/8
	offset=0
	UVMap= [None] * UVMapCount
	debugMsg('Reading UV Mapping coordinates block', 3)
	for i in range(UVMapCount):
		(u, v) = struct.unpack('<2f', data[ offset : offset + 8])
		offset += 8
		# Blender stores UV coordinates starting from the lower left, so I complement the value of v
		# at 1 to find the Blender equivalent
		v= 1-v
		debugMsg('u=%06f; v=%06f' % (u, v), 3)
		UVMap[i] = [u, v]
	return UVMap

# Reads a 2 byte flags field, and returns its content as a binary string
def readFlags(data, offset):
	newOffset = offset+2
	outFlags = s2b(data[offset : newOffset])
	return outFlags, newOffset

# Reads a 4 bytes integer
def readInt(data, offset):
	# unpack converts binary C structures into python types, according to the format indicated
	# in this case '<I' = little endian unsigned int
	# unpack always returns a tuple, hence this strange assignment. It works though
	newOffset = offset + 4
	(outInt,) = struct.unpack('<i', data[ offset : newOffset ])
	return outInt, newOffset

# Reads a 4 bytes float
def readFloat(data, offset):
	#'<f' little endian float
	newOffset = offset + 4
	(outFloat,) = struct.unpack('<f', data[ offset : newOffset ])
	return outFloat, newOffset

# Reads a 2 bytes short integer
def readShort(data, offset):
	newOffset = offset + 2
	#'<H' shortint
	(outShort,) = struct.unpack('<h', data[ offset : newOffset ])
	return outShort, newOffset

# Reads a 2 bytes unsigned short integer
def readUShort(data, offset):
	newOffset = offset + 2
	(outShort,) = struct.unpack('<H', data[ offset : newOffset ])
	return outShort, newOffset

# Reads a 1 byte boolean value
def readBool(data, offset):
	newOffset = offset + 1
	#'<B' Unsigned Char. Returns an int value
	(outBool,) = struct.unpack('<B', data[ offset : newOffset ])
	return (outBool==1), newOffset

# Reads a transform matrix
def readXform(data, offset):
	temp=[None]*16
	for i in range(16):
		elem, offset = readFloat(data, offset)
		temp[i]=elem
	xform = Matrix(
		[temp[ 3], temp[ 6], temp[ 9], temp[15]],
		[temp[ 4], temp[ 7], temp[10], temp[14]],
		[temp[ 5], temp[ 8], temp[11], temp[13]],
		[temp[ 0], temp[ 1], temp[ 2], temp[12]])
	return xform, offset

# Reads a rotation matrix (3*3 floats)
def readMatrix(data, offset):
	temp=[None]*9
	for i in range(9):
		elem, offset = readFloat(data, offset)
		temp[i]=elem
	mat = Matrix(
		[temp[ 0], temp[ 1], temp[ 2]],
		[temp[ 3], temp[ 4], temp[ 5]],
		[temp[ 6], temp[ 7], temp[ 8]])
	# I'll resize this to a 4*4 matrix anyway,
	# for ease of use in matrix calculations
	mat.resize4x4()
	return mat, offset

# Reads a list of integers preceded by a list length
def readIntList(data, offset):
	count, offset = readInt(data, offset)
	list = [None] * count
	for i in range(count):
		list[i], offset = readInt(data, offset)
	return list, offset

# Reads a string preceded by a string length
def readString(data, offset):
	length, offset = readInt(data, offset)
	value = data[ offset : offset + length ]
	offset += length
	return value, offset

# Reads the file version number, and returns it like a string
def readVersion(data, offset):
	newOffset = offset + 4
	versBytes = data[offset: newOffset]
	(min3, min2, min1, maj) = struct.unpack('<4B', versBytes)
	return (maj, min1, min2, min3), newOffset
	
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Document blocks. Each of these classes represents a section of the NIF file
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
# I got enough methods that I want in every class that I might as well set up a base class from wich 
# I can derive all the other blocks, at least the script won't crash because a defauly method (like getType)
# isn't defined
class NiObject(object):
	"""
		Base class for the definition of a NIF block
	"""
	data = None
	type = None
	id = None
	parentId = None
	properties = []
	resources = []
	global NiObjects
	# Constructor
	def __init__(self, data, id):
		# Byte content of the block.
		self.data = data
		# Id of the block
		self.id = id
		# I read the byte content from the start of the data block using the
		# variable offset like a cursor
		offset = 0
		# This is the type of the node.
		if len(data) > 0:
			self.type, offset = readString(self.data, offset)
		return offset
	# returns the raw byte content of the block
	def getData(self):
		return self.data
	# returns the id of the block
	def getId(self):
		return self.id
	# So that external functions iterating through the nodes can find out what this node is.
	def getType(self):
		return self.type
	# Sets the index of the block parent
	def setParentId(self, parentId):
		self.parentId = parentId
	# Returns the index of the block parent, can be None for properties or resources.
	def getParentId(self):
		return self.parentId
	# returns the parent node
	def getParent(self):
		parentId = self.parentId
		if parentId != None:
			return NiObjects[parentId]
		return None
	# Returns the properties list, for most blocks is empty
	def getProperties(self):
		return self.properties
	# Returns blocks bound as resources, for most blocks is empty
	def getResources(self):
		return self.resources

class NiNode(NiObject):
	"""
		NiNode block
	"""
	xform = nullXform
	role = None
	children = []
	def __init__(self, data, id):
		# I must first initiate the base class constructor, otherwise the type
		# and the ID's will be left undefined. I need these.
		# Offset is the cursor I use to read the byte content of the class
		offset = NiObject.__init__(self, data, id)
		# This is the name of the node.
		# Some nodes have a different header, so they need a different constructor
		self.name, offset = readString(self.data, offset)
		# ID of the bound NiExtraData block
		self.NiExtraDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiExtraDataId)
		# ID of the bound TimeController block
		self.NiTimeControllerId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTimeControllerId)
		# Flags. Most of these are unknown, field 5 distinguishes between a grouping
		# node and a bone
		self.flags, offset = readFlags(data, offset)
		# Next is a 4*4 transform matrix, apparently. There's another like
		# this one in NiTriShape. I believe the transform matrix should be
		# applied to all the children of this NiNode to place them correctly
		# in the root node. By this I mean that all coordinates should be
		# relative to the parent node. This is pure speculation, though.
		# This differs a bit from the description made in the file format
		# document, but makes all transformation operations easier, as they
		# end up being a multiplication of matrices. This covers up everything
		# up to and including velocity.
		self.xform, offset = readXform(self.data, offset)
		# Properties list. These are the ID's of property nodes linked to this node
		self.properties, offset = readIntList(self.data, offset)
		# hasBoundingBox, if non 0 bounding box info follows
		self.hasBoundingBox, offset = readInt(self.data, offset)
		if self.hasBoundingBox != 0:
			#Bounding box info 64 bytes of it, will fix later
			offset += 64
		# List of child nodes
		self.children, offset = readIntList(self.data, offset)
		# List of effect nodes
		self.effects, offset = readIntList(self.data, offset)
		# Sets the role for the node. For bones I need to check the children list
		if self.flags[4:5] == '0':
			if len(self.children) > 0:
				self.role = 'bone'
				debugMsg('%s is a bone' % self.name, 3)
			else:
				self.role = 'nub'
				debugMsg('%s is a bone nub' % self.name, 3)
	# Returns the node name
	def getName(self):
		return self.name
	# Returns the transform matrix
	def getMatrix(self, space = 'local'):
		matrix = self.xform
		if space == 'world':
			block = self
			while block.getParent() != None:
				block = block.getParent()
				matrix = matrix * block.getMatrix()
		return matrix
	# Returns the flags string
	def getFlags(self):
		return self.flags
	# Returns the role of the node.
	def getRole(self):
		return self.role
	# Sets the role of the node
	def setRole(self, role):
		self.role = role
	# Returns a list of child blocks
	def getChildren(self):
		# Hmm, list comprehension... a bit hard to read, but so much more performing...
		childBlocks = [NiObjects[id] for id in self.children if id != -1]
		return childBlocks
	# Returns a list of all the NiNode blocks within this  branch
	def getBranch(self):
		blocks = [self]
		for child in [obj for obj in self.getChildren() if obj.getType() == 'NiNode']:
			blocks.extend(child.getBranch())
		return blocks


class NiTriShape(NiObject):
	"""
		Representation of a NiTriShape block, contains a reference to NiTriShapeData 
	"""
	global NiObjects
	xform = nullXform
	NiTriShapeDataId = None
	SkinInstanceId = None
	# Refer to the comment on NiNode for most of what's happening here.
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# This is the name of the node.
		# Some nodes have a different header, so they need a different constructor
		self.name, offset = readString(self.data, offset)
		# ID of the bound NiExtraData block
		self.NiExtraDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiExtraDataId)
		# ID of the bound TimeController block
		self.NiTimeControllerId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTimeControllerId)
		# Flags. Will need to XOR them to make any sense of them
		self.flags, offset = readShort(self.data, offset)
		# Tansform matrix, same as in NiNode
		self.xform, offset = readXform(self.data, offset)
		# Properties list. These are the ID's of property nodes linked to this node
		self.properties, offset = readIntList(self.data, offset)
		# hasBoundingBox, if non 0 bounding box info follows
		self.hasBoundingBox, offset = readInt(self.data, offset)
		if self.hasBoundingBox != 0:
			#Bounding box info 64 bytes of it, will fix later
			offset += 64
		# ID of the bound NiTriShapeData block
		self.NiTriShapeDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTriShapeDataId)
		# ID of the bound SkinInstance block
		self.NiSkinInstanceId, offset = readInt(self.data, offset)
		self.resources.append(self.NiSkinInstanceId)
	# Returns the node name
	def getName(self):
		return self.name
	# Returns the transform matrix
	def getMatrix(self, space = 'local'):
		matrix = self.xform
		if space == 'world':
			block = self
			while block.getParent() != None:
				matrix = matrix * block.getParent().getMatrix()
		return matrix
	# Returns the attributes list
	def getProperties(self):
		return self.properties
	# Returns the ID of the bound NiTriShapeData block
	def getNiTriShapeDataId(self):
		return self.NiTriShapeDataId
	# Returns the bound NiTriShapeData block
	def getNiTriShapeData(self):
		return NiObjects[self.NiTriShapeDataId]
	# Returns the ID of the bound NiSkinInstance block
	def getNiSkinInstanceId(self):
		return self.NiSkinInstanceId
	# Returns the bound NiSkinInstance block
	def getNiSkinInstance(self):
		if self.NiSkinInstanceId != -1:
			return NiObjects[self.NiSkinInstanceId]
		else:
			return None
	# Returns a NiAlphaProperty (there should be only one per mesh)
	def getNiAlphaProperty(self):
		for propId in self.properties:
			propBlock = NiObjects[propId]
			if propBlock != None and propBlock.getType() == 'NiAlphaProperty':
				return propBlock
		return None
	# Returns a NiTexturingProperty (there should be only one per mesh)
	def getNiTexturingProperty(self):
		for propId in self.properties:
			propBlock = NiObjects[propId]
			if propBlock != None and propBlock.getType() == 'NiTexturingProperty':
				return propBlock
		return None
	# Returns a NiMaterialProperty (there should be only one per mesh)
	def getNiMaterialProperty(self):
		for propId in self.properties:
			propBlock = NiObjects[propId]
			if propBlock != None and propBlock.getType() == 'NiMaterialProperty':
				return propBlock
		return None
	# Returns the bound NiGeomMorpherController block
	def getNiGeomMorpherController(self):
		if self.NiTimeControllerId != -1:
			ctrlBlock = NiObjects[self.NiTimeControllerId]
			if ctrlBlock != None and ctrlBlock.getType() == 'NiGeomMorpherController':
				return ctrlBlock
		return None
		


# NiTriShapeData block. This differs from the base block by several points, so I build it
# as a standalone object
class NiTriShapeData(NiObject):
	"""
		Representation of a NiTriShapeData block, contains mesh data
	"""
	vertNormals = []
	verts = []
	vertsUV = []
	vertCol = []
	faces = []
	# Again, for most of what is happening here refer to the comments on the NiNode class
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# ID of the bound NiExtraData block
		self.vertCount, offset = readUShort(self.data, offset)
		debugMsg('found %04i vertices' % self.vertCount, 3)
		# unknown, 0 for 0 vertex mesh. Some sort of crc or counter?
		self.hasVerts, offset = readInt(self.data, offset)
		debugMsg('hasVerts (if 0 no vertex data) = %i' % self.hasVerts, 3)
		if self.hasVerts != 0 :
			# vertex coordinates as (x, y, z)
			self.verts = readVerts(self.data[ offset : offset + (self.vertCount * 12) ])
			offset += (self.vertCount * 12)
		# unknown, if different from 0 the mesh contains normals data
		self.hasVertexNormals, offset = readInt(data, offset)
		debugMsg('hasVertexNormals (if 0 no normals data) = %i' % self.hasVertexNormals, 3)
		if self.hasVertexNormals != 0 :
			self.vertNormals = readVertexNormals(self.data[ offset : offset + (self.vertCount * 12) ])
			offset += (self.vertCount * 12)
		# Bounding Sphere info. I'll keep the bounding sphere info in a single tuple, as (x, y, z, radius)
		self.boundingSphere = struct.unpack('<4f',self.data[ offset : offset + 16 ])
		offset += 16
		# unknown, if different from 0 the mesh contains vertex color data
		self.hasVertColor, offset = readInt(self.data, offset)
		debugMsg('hasVertColor (if 0 no vertex color data) = %i' % self.hasVertColor, 3)
		if self.hasVertColor != 0 :
			self.vertCol = readVertColor(self.data[ offset : offset + (self.vertCount * 16) ])
			offset += (self.vertCount * 16)
		# number of the texture sets
		self.numTextureSets, offset = readShort(self.data, offset)
		# UV Mapping information. There is one set for each texture set, each one
		# long 2*4 * number of vertices, so I store them in arrays
		self.hasUVMaps, offset = readInt(self.data, offset)
		self.vertsUV = [None] * self.numTextureSets
		for i in range(self.numTextureSets):
			dataLength = self.vertCount * 8
			UVdata = self.data[ offset : offset + dataLength ]
			self.vertsUV[i] = readUVMap(self.data[ offset : offset + dataLength ])
			offset += dataLength
		# number of faces
		self.numFaces, offset = readUShort(self.data, offset)
		debugMsg('found %04i faces' % self.numFaces, 3)
		# number of faces times 3, we can throw this away
		dummy, offset = readInt(self.data, offset)
		self.faces = readFaces(self.data[offset : offset + (self.numFaces * 6) ])
		offset += (self.numFaces * 6)
		# ok, here follows more data. Possibly links between the vertices and the texture sets,
		# or links between the faces and the texture sets
	# Returns the vertices array. Number of vertices can be obtained from this
	def getVerts(self):
		return self.verts
	# Returns the normals array
	def getVertNorms(self):
		return self.vertNormals
	# Returns the UV mapping information. Number of texture sets can be obtained from this
	def getVertUV(self):
		return self.vertsUV
	# Returns the Vertex Color Array
	def getVertCol(self):
		return self.vertCol
	# Returns the faces array
	def getFaces(self):
		return self.faces

class NiTexturingProperty(NiObject):
	"""
		Representation of a NiTexturingProperty block, contains a reference to a NiSourceTexture block
	"""
	NiSourceTextureId = None
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# Apparently this node could store a name length, though its length is usually 0
		# If I were to find a block with the name this would take care of it
		self.name, offset = readString(self.data, offset)
		# ID of the bound NiExtraData block
		self.NiExtraDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiExtraDataId)
		# ID of the bound TimeController block
		self.NiTimeControllerId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTimeControllerId)
		# Flags. Will need to XOR them to make any sense of them
		self.flags, offset = readShort(self.data, offset)
		# Apply mode. Ranges from 0 to 4, with the following decodification:
		# 0: APPLY_REPLACE
		# 1: APPLY_DECAL
		# 2: APPLY_MODULATE
		# 3: APPLY_HILIGHT
		# 4: APPLY_HILIGHT2
		# Modes 3 and 4 are for PS2 only
		self.applyMode, offset = readInt(self.data, offset)
		# Ok, I'll skip a lot of data here. ATM I am more interested in getting the name of the base texture
		# file than all of the other stuff. Probably it's info about material properties, blending modes and such
		offset += 8
		#bound NiSourceTexture ID
		self.NiSourceTextureId, offset = readInt(self.data, offset)
		self.resources.append(self.NiSourceTextureId)
		#there's more following, I'll bother later
	# Returns the bound NiSourceTexture ID
	def getNiSourceTextureId(self):
		return self.NiSourceTextureId
	# Returns the bound NiSourceTexture
	def getNiSourceTexture(self):
		return NiObjects[self.NiSourceTextureId]

class NiSourceTexture(NiObject):
	"""
		Representation of a NiSourceTexture block
	"""
	texturePath = None
	global textures
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# Same as NiTexturingProperty, the
		self.name, offset = readString(self.data, offset)
		# ID of the bound NiExtraData block
		self.NiExtraDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiExtraDataId)
		# ID of the bound TimeController block
		self.NiTimeControllerId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTimeControllerId)
		# Has external textures. For morrowind files this is usually true, otherwise the texture
		# data will be kept in a NiPixelData block. 1 byte value, I read it as a boolean
		self.hasExternalTextures, offset = readBool(self.data, offset)
		debugMsg('hasExternalTextures = %s' % self.hasExternalTextures, 3)
		if self.hasExternalTextures:
			self.texturePath, offset = readString(data, offset)
	# Returns the texture filepath
	def getTextureFile(self):
		textureFile = self.texturePath
		textureFile = textureFile.strip('\x00')
		textureFile = textureFile.lower() # fixes problems with case sensitivity of file names under linux # amorilia
		textureFile = textureFile.replace('\\', Blender.sys.sep)
		textureFile = textureFile.replace('/', Blender.sys.sep)
		# textureFile = textureFile.lstrip(Blender.sys.sep)
		return textureFile

class NiMaterialProperty(NiObject):
	"""
		Representation of a NiMaterialProperty block
	"""
	name = None
	colors = [None]*4
	surface = [None]*2
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# Same as NiTexturingProperty, the
		self.name, offset = readString(self.data, offset)
		# ID of the bound NiExtraData block
		self.NiExtraDataId, offset = readInt(self.data, offset)
		self.resources.append(self.NiExtraDataId)
		# ID of the bound TimeController block
		self.NiTimeControllerId, offset = readInt(self.data, offset)
		self.resources.append(self.NiTimeControllerId)
		# Flags. Will need to XOR them to make any sense of them
		self.flags, offset = readShort(self.data, offset)
		# Material colors list. the order is: ambient, diffuse, specular, emissive
		# RGB triplets from 0 to 255
		for i in range(4):
			R, offset = readInt(self.data, offset)
			G, offset = readInt(self.data, offset)
			B, offset = readInt(self.data, offset)
			self.colors[i]=[R, G, B]
		# Shininess, 0-255 value 
		shine, offset = readFloat(self.data, offset)
		# Transparency, 0-255 value 
		alpha, offset = readFloat(self.data, offset)
		# fills the surface properties list
		self.surface = [shine, alpha]
	# Returns the node name
	def getName(self):
		return self.name
	# Returns the colors list
	def getColors(self):
		return self.colors
	# Returns the surface properties list
	def getSurface(self):
		return self.surface

class NiSkinInstance(NiObject):
	"""
		Representation of a NiSkinInstance block
	"""
	bones = []
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# ID of the bound NiSkinData block
		self.NiSkinDataId, offset = readInt(self.data, offset)
		# Id of the root NiNode, usually the Scene Root. All the bone rest positions are relative to this node
		self.RootNodeId, offset = readInt(self.data, offset)
		# Bones list. A bone count, followed by the list of bone node ID's
		self.boneIds, offset = readIntList(self.data, offset)
	# Returns a list of bone ID's
	def getBoneIds(self):
		return self.boneIds
	# Returns a list of NiNode objects representing bones
	def getBones(self):
		bones = [None] * len(self.boneIds)
		for i, boneId in enumerate(self.boneIds):
			if boneId != -1:
				bones[i] = NiObjects[boneId]
		return bones
	# Returns the ID of the bound NiSkinData block
	def getNiSkinDataId(self):
		return self.NiSkinDataId
	# Returns the bound NiSkinData block
	def getNiSkinData(self):
		return NiObjects[self.NiSkinDataId]

class NiSkinData(NiObject):
	"""
		Representation of a NiSkinData block
	"""
	xform = nullXform
	def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		"""
		#Description of the NiSkinData format provided by brick_013
		matrix m - global rotation? (for all bones)
		float[3] unknown
		float unknown = 1
		int boneCount - bones, matches count in NiSkinInstance
		int unknown = -1
		foreach boneCount - bones
		{
			matrix unknown - local rotation?
			float[3] unknown
			float unknown = 1
			float[4] unknown
			
			short weightCount - number of vertex weights
			foreach weightCount
			{
				short vertex - vertex number
				float weight
			}
		}
		"""
		# A rotation matrix, unknown. Possibly part of the reference coordinates?
		# Not a normal netimmerse matrix, tho, as there's no translation data, only rotation
		self.mat1, offset = readMatrix(self.data, offset)
		# Four more floats, possibly the translation part of the matrix above? The 4th seems to be always one.
		offset += 16 
		# Bone count
		self.boneCount, offset = readInt(self.data, offset)
		# An int, unknown, always -1, possibly a reference to a non-existent node?
		self.i1, offset = readInt(self.data, offset)
		# List of bone data. I'll handle this as a list of tuples for the moment
		self.weights = [None] * self.boneCount
		for bone in range(self.boneCount):
			# Seventeen floats, unknown
			offset +=  68
			# Length of the weights list, should match the number of vertices for the mesh,
			# but we can also assume that any vertices missing from this list have weight 0 for this bone
			vertices, offset = readShort(self.data, offset)
			self.weights[bone] = [None] * vertices
			for vert in range(vertices):
				# Id of the vertex the weight belongs to
				vertexId, offset = readShort(self.data, offset)
				# Weight value
				weight, offset = readFloat(self.data, offset)
				self.weights[bone][vert] = (vertexId, weight)
	# Returns the list of weights
	def getWeights(self):
		return self.weights

class NiController(NiObject):
    """
                Representation of a generic Controller block
    """
    def __init__(self, data, id):
		# Base class constructor
		offset = NiObject.__init__(self, data, id)
		# ID of the next Controller ID
		self.NextControllerId, offset = readInt(self.data, offset)
                # usually 0x000C
                self.Flags, offset = readShort(self.data, offset)
                # usually 1.0
                self.Frequency, offset = readFloat(self.data, offset)
                # usually 0.0
                self.Phase, offset = readFloat(self.data, offset)
                # when does the controller start?
                self.StartTime, offset = readFloat(self.data, offset)
                # when does the controller end?
                self.StopTime, offset = readFloat(self.data, offset)
                # index of the parent that owns this time controller block
		self.ParentId, offset = readInt(self.data, offset)
		return offset
    def getNextControllerId(self):
                return self.NextControllerId
    def getParentId(self):
                return self.ParentId
    
class NiGeomMorpherController(NiController):
	"""
		Representation of a NiGeomMorpherController block
	"""
	def __init__(self, data, id):
		# Base class constructor
		offset = NiController.__init__(self, data, id)
		# ID of the bound NiMorphData block
		self.NiMorphDataId, offset = readInt(self.data, offset)
	# Returns the ID of the bound NiSkinData block
	def getNiMorphDataId(self):
		return self.NiMorphDataId
	# Returns the bound NiSkinData block
	def getNiMorphData(self):
		return NiObjects[self.NiMorphDataId]

class NiMorphData(NiObject):
    """
        	Representation of a NiMorphData block
    """
    def __init__(self, data, id):
                # Base class constructor
                offset = NiObject.__init__(self, data, id)
                # Number of morph targets
                self.NumMorphBlocks, offset = readInt(self.data, offset)
                # Number of vertices
                self.NumVertices, offset = readInt(self.data, offset)
                print self.NumMorphBlocks
                print self.NumVertices
                offset += 1
                self.MorphBlocks = [ None ] * self.NumMorphBlocks
                for count in range( self.NumMorphBlocks ):
                    frameCnt, offset = readInt(self.data, offset)
                    frameType, offset = readInt(self.data, offset)
                    frames = [ None ] * frameCnt
                    for fcount in range( frameCnt ):
                        time, offset = readFloat(self.data, offset)
                        x, offset = readFloat(self.data, offset)
                        y, offset = readFloat(self.data, offset)
                        z, offset = readFloat(self.data, offset)
                        frames[fcount] = ( time, x, y, z )
                    verts = readVerts(self.data[ offset : offset + (self.NumVertices * 12) ])
                    offset += (self.NumVertices * 12)
                    self.MorphBlocks[count] = ( frameCnt, frameType, frames, verts )
                
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Main document class. This will hold the whole structure of the file and provide access
#-------- methods
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
class NifDocument(object):
	"""
		Representation of a NIF document.
	"""
	blockMap = []
	data = None
	rootBlock = None
	blocksToSkip = []
	def __init__(self, data):
		global NiObjects, materials, textures
		NiObjects = []
		self.data = data
		# The version string is a fixed value
		#self.headerString = 'NetImmerse File Format, Version 4.0.0.2\x0A\x02\x00\x00\x04' # amorilia
		self.headerString = data[0:data[0:50].find('\x0A')]
		# Offset is an index from the start of data for reading the various bits and bobs
		offset = len(self.headerString) + 1
		# The version appears to be here as a list of 4 chars, in reverse order respect to the header string.
		# I'll store it as a tuple
		self.version, offset = readVersion(self.data, offset)
		debugMsg( 'file version is %s.%s.%s.%s' % self.version, 2)
		# This value matches the number of nodes within the file # amorilia: now it really does :)
		self.blockCount, offset = readInt(self.data, offset)
		# the % operand operates a substitution in the string
		# with the 2nd parameter, where the formatting is defined
		# by the %code in the string itself.
		# In this case %i=signed integer 
		debugMsg('Block count = %i' % self.blockCount, 1)
		debugMsg('File size = %i bytes' % len(self.data), 1)
		# the limit set on count should be plenty enough for the biggest NIF file,
		# but it can be increased if needed. It's just there to avoid the script hanging
		# on a shortloop if something goes horribly wrong
		count = 0
		# This function fills in a list with the node types and their position within the file
		while offset < len(self.data) and count < 10000 :
			type, offset = findNextBlock(self.data, offset)
			if type != None :
				self.blockMap.append((type, offset, None))
				offset += len(type) + 4
				count += 1
			else:
				break
		#I size the list of nodes to that of the temporary blocks map
		NiObjects = [None]*len(self.blockMap)
		# Now I update the values to include the block length, and load the block in the blocks
		# list if it is one of those I can decode.
		err = ''
		if len(self.blockMap) > 0:
			for i in range(len(self.blockMap)):
				(type, offset, dummy) = self.blockMap[i]
				if i+1 < len(self.blockMap):
					(dummy, nextBlock, dummy) = self.blockMap[i+1]
					length = nextBlock - offset
				else:
					length = len(self.data) - offset
				debugMsg('found block %04i, at %06i, length = %06i, type = %s' % (i, offset, length, type),3)
				self.blockMap[i]=(type, offset, length)
			# The blockMap is complete.
		else:
			err = 'The node list is empty!'
		if err != '':
			print err
			Blender.Draw.PupMenu("ERROR%t|"+err)
			raise
		for blockId in range(len(self.blockMap)):
			(blockType, blockOffset, blockLength) = self.blockMap[blockId]
			blockData = self.data[blockOffset : blockOffset + blockLength]
			block = None
			if blockType == 'NiNode' or blockType == 'RootCollisionNode':
				block = NiNode(blockData, blockId)
			elif blockType == 'NiTriShape':
				block = NiTriShape(blockData, blockId)
			elif blockType == 'NiTriShapeData':
				block = NiTriShapeData(blockData, blockId)
			elif blockType == 'NiTexturingProperty':
				block = NiTexturingProperty(blockData, blockId)
			elif blockType == 'NiSourceTexture':
				block = NiSourceTexture(blockData, blockId)
			elif blockType == 'NiMaterialProperty':
				block = NiMaterialProperty(blockData, blockId)
			elif blockType == 'NiSkinInstance':
				block = NiSkinInstance(blockData, blockId)
			elif blockType == 'NiSkinData':
				block = NiSkinData(blockData, blockId)
			elif blockType == 'NiGeomMorpherController':
                                block = NiGeomMorpherController(blockData, blockId)
                        elif blockType == 'NiMorphData':
                                block = NiMorphData(blockData, blockId)
			else:
				# In case the node isn't one of the parsed ones I'll just assign it the base class
				# so that at least I can mantain the tree structure
				block = NiObject(blockData, blockId)
			# The block has been built, and can be added to the document's nodes collection
			NiObjects[blockId] = block
		# Now I'll update all the parent ID's in the child blocks for all blocks in the list.
		# could make it easier to navigate the tree later on.
		for block in [obj for obj in NiObjects if obj.getType() == 'NiNode']:
			for child in block.getChildren():
				#if (child != None): # amorilia #Not needed anymore, children lists now only return valid blocks
				child.setParentId(block.getId()) # amorilia
		# temporarily sets the root block to the first block found
		self.rootBlock = NiObjects[0]
		# finds the root block
		for block in [obj for obj in NiObjects if obj.getType() == 'NiNode' and obj.getParent() == None]:
			self.rootBlock = block
			break
		debugMsg('using block %s (%s) as root' % (self.rootBlock.getId(), self.rootBlock.getName()), 2)
		self.rootBlock.setRole('root')
		# finds armature nodes. These are regular NiNodes, so to detect them as armatures I look for a node
		# that is not the root and is the parent to a bone
		for block in [obj for obj in NiObjects if obj.getType() == 'NiNode' and obj.getRole() == 'bone' and obj.getParent() != None and obj.getParent().getRole() != 'bone']:
			debugMsg('%s is an armature' % block.getParent().getName(), 2)
			block.getParent().setRole('armature')
		# NiNode blocks are roughly equivalent to Blender Objects. Some seem to have only the role of "wrapper" around meshes,
		# and throw off the import of rigged structures. I'll mark the role on these as 'mesh'
		for block in [obj for obj in NiObjects if obj.getType() == 'NiNode' and len(obj.getChildren()) == 1 and obj.getChildren()[0].getType() == 'NiTriShape']:
			block.setRole('mesh')
			self.blocksToSkip.append(block.getChildren()[0].getId())
		# Adds the bones to the list of blocks to be ignored when writing. These are handled by the armature.
		self.blocksToSkip.extend([block.getId() for block in NiObjects if block.getType() == 'NiNode' and block.getRole() == 'bone'])
	# Recursive function, writes the content of the NIF document to Blender. Must be fed with the root block to start
	# reading the hierarchy tree
	def writeObjs(self, block, scene):
		if block.getId() not in self.blocksToSkip:
			blockType= block.getType()
			if blockType == 'NiNode':
				role= block.getRole()
				if role == 'armature':
					armObj =  createArmature(block)
					scene.link(armObj)
					childObjList = []
					for child in block.getChildren():
						childObj = self.writeObjs(child, scene)
						if childObj: childObjList.append(childObj)
					armObj.makeParent(childObjList)
					#xform = block.getMatrix('world') * nifToBlendXform
					xform = block.getMatrix('world')
					armObj.setMatrix(xform)
					return armObj
				elif role == 'mesh':
					meshObj = createMesh(block)
					# xform = block.getMatrix('world') * nifToBlendXform
					#xform = block.getMatrix()
					#meshObj.setMatrix(xform)
					return meshObj
				else:
					emptyObj = Blender.Object.New('Empty', block.getName())
					scene.link(emptyObj)
					childObjList = []
					for child in block.getChildren():
						childObj = self.writeObjs(child, scene)
						if childObj: childObjList.append(childObj)
					emptyObj.makeParent(childObjList)
					xform = block.getMatrix()
					emptyObj.setMatrix(xform)
					return emptyObj
			elif blockType == 'NiTriShape':
				return createMesh(block)
			else:
				debugMsg("skipping %s" % blockType, 2)
		return None
		
	# Function to write the meshes to blender, feeds the root node to the writeObjs function.
	# Applies a corrective factor to the root node so that the scene can be handled better within Blender.
	# Morrowind seems to be ignoring the scaling values set on the root node anyway.
	def writeToBlender(self):
		# get the root block
		debugMsg("root block= %s, type= %s, parent= %s " % (self.rootBlock.getId(), self.rootBlock.getType(), self.rootBlock.getParentId()),3)
		rootObj = self.writeObjs(self.rootBlock, Scene.GetCurrent())
		# sets size and position of the root node
		xform = self.rootBlock.getMatrix() * nifToBlendXform
		rootObj.setMatrix(xform)
		# cleanup
		materials = None
		textures = None
		# finalize
		Blender.Redraw(-1)

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Interface to Blender. Here is where the data gets put on screen
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

# Creates and returns a Blender armature. Takes care of all bones linked to the armature as well
def createArmature(block):
	scene = Scene.GetCurrent()
	# Bones are aligned along the y axis in Blender, along the X axis in Netimmerse
	# so to work out the roll I must align the matrices first
	bones = {}
	armObj = Blender.Object.New('Armature', block.getName())
	# Armature data
	armData = Blender.Armature.New()
	armData.name = block.getName()
	armData.drawAxes(1)
	# Inverse of the armature's world coordinates transform matrix
	armatureMat = block.getMatrix('world')
	armatureInvMat = invert(armatureMat)
	# List of descendants from this block. It's still recursive,
	# I just shifted the recursion to the getBranch method.
	branch = block.getBranch()
	# 1st pass, add all the bones to the armature. Gee, Blender API for armatures sucks.
	# I can't set a bone parent unless the parent is already linked to the armature
	for leaf in branch:
		# this skips childs that are not bones
		if leaf.getType() == 'NiNode' and leaf.getRole() == 'bone':
			name = leaf.getName()
			bone = Blender.Armature.Bone.New(name)
			armData.addBone(bone)
			bones[leaf.getId()] = bone
			leafLocMat = leaf.getMatrix('world') * armatureInvMat
			# NIF bones are aligned a long the X axis, and their coordinates are relative to their parent
			# so the X value of the translation part is the same as the length
			tailBlock = leaf.getChildren()[0]
			length = tailBlock.getMatrix().translationPart()[0]
			head = leafLocMat.translationPart()
			tail = pointTransform((length, 0.0, 0.0), leafLocMat)
			bone.setHead(*head)
			bone.setTail(*tail)

	# 2nd pass, family reunion. This is why I have a dictionary of bones indexed by node ID's.
	# I still think it's a nasty hack, but I  don't see another way to do this. I also set the roll here.
	# Other nasty hack, but Blender really seems to be a mess when dealing with armatures
	for leaf in branch:
		leafParent = leaf.getParent()
		if leaf.getType() == 'NiNode' and leaf.getRole() == 'bone' and leafParent.getRole() == 'bone':
			name = leaf.getName()
			childBone = bones[leaf.getId()]
			parentBone = bones[leafParent.getId()]
			childBone.setParent(parentBone)
			# Wheee, let's roll. Ok, I'll fix this
			leafLocMat = leaf.getMatrix('world') * armatureInvMat
			head = leafLocMat.translationPart()
			tgtRef = pointTransform((0.0, 1.0, 0.0), leafLocMat)
			boneRef = pointTransform((0.0, 0.0, 1.0), childBone.getRestMatrix('worldspace'))
			# this is the roll angle I get from my maths
			angle = storedAngle = getRads(head, boneRef, tgtRef)
			# these are the bounds I use to define the bone as aligned
			ubound = ((0.5/180)*math.pi)
			lbound = -1.0*ubound
			# let's try the simple way first
			if angle > ubound or angle < lbound:
				childBone.setRoll(angle)
			else:
				debugMsg('%s was aligned already' % name, 3)
			# then we see if it worked, and if it didn't we try the other way
			boneRef = pointTransform((0.0, 0.0, 1.0), childBone.getRestMatrix('worldspace'))
			angle = getRads(head, boneRef, tgtRef)
			if angle > ubound or angle < lbound:
				childBone.setRoll((math.pi/2) - angle)
			else:
				debugMsg('%s was aligned on the 1st passage' % name, 3)
			# sometimes the angle will not be the correct one to align the bone, so I just approximate it. Probably I can
			# fix this to work a little better. In most cases the following part is skipped
			boneRef = pointTransform((0.0, 0.0, 1.0), childBone.getRestMatrix('worldspace'))
			angle = getRads(head, boneRef, tgtRef)
			if angle > ubound or angle < lbound:
				deg = 0
				while (angle > ubound or angle < lbound) and deg < 360:
					deg = deg+1
					roll = ((deg*1.0)/180)*math.pi
					childBone.setRoll(roll)
					boneRef = pointTransform((0.0, 0.0, 1.0), childBone.getRestMatrix('worldspace'))
					angle = getRads(head, boneRef, tgtRef)
				debugMsg('%s was aligned on the 3rd passage' % name, 3)
			else:
				debugMsg('%s was aligned on the 2nd passage' % name, 3)
	"""
	#showing the roll offset, for debug
	dbgMesh = Blender.NMesh.GetRaw()
	for leaf in branch:
		if leaf.getType() == 'NiNode' and leaf.getRole() == 'bone':
			bone = bones[leaf.getId()]
			name = leaf.getName()
			leafLocMat = leaf.getMatrix('world') * armatureInvMat
			head = leafLocMat.translationPart()
			tgtRef = pointTransform((0.0, 1.0, 0.0), leafLocMat)
			boneRef = pointTransform((0.0, 0.0, 1.0), bone.getRestMatrix('worldspace'))
			v1 = Blender.NMesh.Vert(*head)
			v2 = Blender.NMesh.Vert(*tgtRef)
			v3 = Blender.NMesh.Vert(*boneRef)
			dbgMesh.verts.extend([v1,v2,v3])
			f1 = Blender.NMesh.Face()
			f1.v = [v1,v2,v3]
			dbgMesh.faces.append(f1)
			#bone.setRoll(getRads(tgtRef, boneRef)/4)
	Blender.NMesh.PutRaw(dbgMesh, name, 1)
	meshObj = Blender.Object.GetSelected()[0]
	meshObj.setMatrix(armatureMat*nifToBlendXform)
	"""
	armObj.link(armData)
	return armObj

# returns an angle between two vectors in radians.
# I define the two vectors as 3 points: an origin and two 'heads'
def getRads(pt_0, pt_1, pt_2):
	vec_1 = Vector( *[ pt_1[i] - pt_0[i] for i in range(3)] ) 
	vec_2 = Vector( *[ pt_2[i] - pt_0[i] for i in range(3)] ) 
	return vecAngle(vec_1, vec_2)
		
#to be used in place of the mathutils buggy implementation, returns a value in radians
def vecAngle(vec_1, vec_2):
	dp = DotVecs(vec_1, vec_2)
	if dp > 1:
		return 0.0
	elif dp < -1:
		return math.pi
	# while I am at it I might as well save a little processor time. No point in making an unneeded acos
	elif dp == 0.0:
		return math.pi/2
	else:
		return math.acos(dp)

# Returns a Blender texture. Textures obtained this way are stored in a general dictionary of textures
def createTexture(NiSourceTexture):
	textureName = NiSourceTexture.getTextureFile()
	textureId = NiSourceTexture.getId()
	texture = None
	# If I looked earlier for this texture it will be stored in my dictionary of textures
	if textures.has_key(textureId):
		debugMsg("Reusing \"%s\"" % textureName, 3) # amorilia
		#if textures[textureId] != "err": # amorilia
		texture = textures[textureId] # amorilia
	else:
		# Find the right texture:
		debugMsg("Searching for \"%s\"" % textureName, 2)
		# Let's start by assuming the file isn't there
		textureFile = None
		# crawl through the texture folders
		# (this may look a bit akward but it ensures that tga, png, etc are prefered
		#  and if there is no alternative the dds is loaded)
		for dir in textureFolders:
			dir.replace( '\\', Blender.sys.sep )
			dir.replace( '/', Blender.sys.sep )
			if ( dir == 'NIFDIR' ):
				dir = nifdir
			elif ( dir == 'SMARTGUESS' ):
				dir = texdir
			debugMsg( "Looking in \"%s\""%dir, 2 )
			tex = Blender.sys.join( dir, textureName )
			if Blender.sys.exists(tex) == 1:
				textureFile = tex
				debugMsg("Found %s" % textureFile, 3)
			# if texture is dds try other formats
			if re_ddsExt.match(tex[-4:]):
				base=tex[:-4]
				for ext in ('.PNG','.png','.TGA','.tga','.BMP','.bmp','.JPG','.jpg'):
					if Blender.sys.exists(base+ext) == 1:
						textureFile = base+ext
						debugMsg( "Found %s" % textureFile, 3 )
						break
			if textureFile and not re_ddsExt.match(textureFile[-4:]):
				break
		if textureFile and Blender.sys.exists(textureFile) == 1:
			# If the file exist the texture can be created and added to the textures list
			debugMsg( "Using %s" % textureFile, 2 )
			texture = Texture.New()
			texture.type = Texture.Types.IMAGE
			image = Image.Load(textureFile)
			texture.setImage(image)
			texture.imageFlags = Blender.Texture.ImageFlags.INTERPOL + Blender.Texture.ImageFlags.MIPMAP
			textures[textureId] = texture
		else:
			debugMsg('%s does not exist, skipping texture (valid formats are .TGA, .PNG, .BMP and .JPG)' % (textureName[:-4]+".*"), 2)
			textures[textureId] = "err"
			texture = "err"
	return texture

# Creates and returns a material
def createMaterial(NiMaterialProperty, NiTexturingProperty):
	#First I check if the material already exists
	name = NiMaterialProperty.getName()
	material = None
	#The same material could be used with different textures
	if NiTexturingProperty:
		name = "%s.%s" % (name, NiTexturingProperty.getId())
	try:
		material = Material.Get(name)
		debugMsg("reusing material: %s " % name, 3)
		return material
	except:
		debugMsg('creating material: %s' % name, 2)
		material = Material.New(name)
	# Sets the material colors
	colors = NiMaterialProperty.getColors()
	# Specular color
	[R, G, B] = colors[2]
	material.setSpecCol(float(R)/256,float(G)/256,float(B)/256)
	# Diffuse color
	[R, G, B] = colors[1]
	material.setRGBCol(float(R)/256,float(G)/256,float(B)/256)
	# 'Mirror' color, ambient color in Max.
	[R, G, B] = colors[0]
	material.setMirCol(float(R)/256,float(G)/256,float(B)/256)
	# Emissive color, converted to a 'glow' factor
	# Same as ambient color
	[R, G, B] = colors[3]
	material.setEmit(float(R+G+B)/768)
	# Sets the material surface properties
	surface = NiMaterialProperty.getSurface()
	# Shininess
	material.setHardness(int(surface[0]*256))
	# Alpha
	material.setAlpha(surface[1])
	textures = []
	if NiTexturingProperty:
		NiSourceTexture = NiTexturingProperty.getNiSourceTexture()
		texture = createTexture(NiSourceTexture)
		if texture != 'err':
			# Sets the texture to use face UV coordinates.
			texco = Texture.TexCo.UV
			# Maps the texture to the base color channel. Not necessarily true.
			mapto = Texture.MapTo.COL
			# Sets the texture for the material
			material.setTexture(0, texture, texco, mapto)
	return material

# creates a group of meshes aligned along the 3 axis
def createWidget(name = '', size = 1.0):
	arrows = []
	lst = [('x',255,1,1,255),
		('y',1,255,1,255),
		('z',1,1,255,255)]
	for (axis, R, G, B, A) in lst:
		arrowName = '%s.%s.arrw' % (name, axis)
		arrows.append(createArrow(arrowName, axis, (R, G, B, A), size))
	widget = Blender.Object.New('Empty', name)
	widget.makeParent(arrows)
	return widget

# creates a mesh in a "arrow" shape, a debug tool for bones
def createArrow(name = '', axis = 'x', color = (200, 200, 200, 255), size = 1.0,):
	meshData = Blender.NMesh.GetRaw()
	verts = []
	if axis == 'x':
		verts = [
			(     0.0,     0.0,     0.0),
			(  size/4,  size/8,     0.0),
			(    size,     0.0,     0.0),
			(  size/4, -size/8,     0.0),
			(  size/4,     0.0,  size/8),
			(  size/4,     0.0, -size/8)]
	elif axis == 'y':
		verts = [
			(     0.0,     0.0,     0.0),
			(  size/8,  size/4,     0.0),
			(     0.0,    size,     0.0),
			( -size/8,  size/4,     0.0),
			(     0.0,  size/4,  size/8),
			(     0.0,  size/4, -size/8)]
	else:
		verts = [
			(     0.0,     0.0,     0.0),
			(     0.0,  size/8,  size/4),
			(     0.0,     0.0,    size),
			(     0.0, -size/8,  size/4),
			(  size/8,     0.0,  size/4),
			( -size/8,     0.0,  size/4)]
	meshData.verts = [None] * len(verts)
	for i, vert in enumerate(verts):
		meshData.verts[i] = Blender.NMesh.Vert(*vert)
	faces = [
		(0,1,2,3),
		(0,4,2,5)]
	meshData.faces = [None] * len(faces)
	meshData.hasVertexColours(1)
	col = Blender.NMesh.Col(*color)
	for i, (v1, v2, v3, v4) in enumerate(faces):
		meshData.faces[i] = Blender.NMesh.Face()
		meshData.faces[i].v = [meshData.verts[v1],meshData.verts[v2],meshData.verts[v3],meshData.verts[v4]]
		meshData.faces[i].col= [col, col, col, col]
	Blender.NMesh.PutRaw(meshData, name, 1)
	meshObj = Blender.Object.GetSelected()[0]
	return meshObj

	
# Creates and returns a mesh
def createMesh(block):
	meshData = Blender.NMesh.GetRaw()
	# Mesh name -> must be unique, so tag it if needed
	name = getUniqueName(block.getName())
	#name = versioned_name(triShape.getName()) # amorilia
	triShape = None
	# Mesh transform matrix
	xform = block.getMatrix()
	if block.getType() == 'NiNode':
		triShape = block.getChildren()[0]
		xform = xform * triShape.getMatrix()
	else:
		triShape = block
	# Mesh geometry data. From this I can retrieve all geometry info
	triShapeData = triShape.getNiTriShapeData()
	# Vertices
	verts = triShapeData.getVerts()
	# Faces
	faces = triShapeData.getFaces()
	# "Sticky" UV coordinates. these atr transformed in Blender UV's
	vertUV = triShapeData.getVertUV()
	# Vertex colors
	vertCol = triShapeData.getVertCol()
	# Vertex normals
	vertNorms = triShapeData.getVertNorms()
	# Set of booleans for later checks
	hasVertexUV = len(vertUV)>0
	hasVertexCol = len(vertCol)>0
	hasVertexNormals = len(vertNorms)>0
	# amorilia: let's only duplicate vertices that have different
	# normals (to simulate sharp edges), so we build list of unique
	# (vertex, normal) pairs
	vertpairs = []
	vertmap = []
	for i in range(len(verts)):
		x, y, z = verts[i]
		if hasVertexNormals:
			nx, ny, nz = vertNorms[i]
		found = 0
		for j, vertpair in enumerate(vertpairs):
			if abs(x - vertpair[0][0]) > epsilon: continue
			if abs(y - vertpair[0][1]) > epsilon: continue
			if abs(z - vertpair[0][2]) > epsilon: continue
			if hasVertexNormals:
				if abs(nx - vertpair[1][0]) > epsilon: continue
				if abs(ny - vertpair[1][1]) > epsilon: continue
				if abs(nz - vertpair[1][2]) > epsilon: continue
			vertmap.append(j) # vertmap[i] = j
		       	found = 1
		       	break
		if found == 0:
			if hasVertexNormals:
				vertpairs.append( ( verts[i], vertNorms[i] ) )
			else:
				vertpairs.append( ( verts[i], None ) )
			vertmap.append(len(vertpairs) - 1) # vertmap[i] = len(vertpairs) - 1
	# amorilia: now import them
	for i, vertpair in enumerate(vertpairs):
		x, y, z = vertpair[0]
		meshData.verts.append(Blender.NMesh.Vert(x, y, z))
		# amorilia: let Blender calculate the vertex normals when doing meshData.update
		#if hasVertexNormals:
		#	nx, ny, nz = vertpair[1]
		#	meshData.verts[i].no[0] = nx
		#	meshData.verts[i].no[1] = ny
		#	meshData.verts[i].no[2] = nz
	for f in faces:
		v1, v2, v3 = f 
		face = Blender.NMesh.Face()
		# face.v.append(mesh.verts[v1])
		# face.v.append(mesh.verts[v2])
		# face.v.append(mesh.verts[v3])
		face.v = [meshData.verts[vertmap[v1]], meshData.verts[vertmap[v2]], meshData.verts[vertmap[v3]]]
		face.smooth = 1
		face.mat = 0
		meshData.faces.append(face)
	# amorilia: done!
	
	# Vertex colors. For both this and UV mapping info I rely on the order of the faces matching that of the lists
	# passed as parameter to the function. Nasty but effective
	if hasVertexCol:
		meshData.hasVertexColours(1)
		for i, f in enumerate(faces):
			v1, v2, v3 = f
			for v in (v1, v2, v3):
				R, G, B, A = vertCol[v]
				R = int(R * 255)
				G = int(G * 255)
				B = int(B * 255)
				A = int(A * 255)
				meshData.faces[i].col.append(Blender.NMesh.Col(R, G, B, A))
		# vertex colors influence lighting...
		# so now we have to set the VCOL_LIGHT flag on the material
		# see below

	# Nif files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seams.
	# Essentially whenever an hard edge or an UV seam is present the mesh this is converted to an open mesh.
	# Blender also supports 'per face' UV coordinates, this could be a problem when exporting.
	# Also, NIF files support a series of texture sets, each one with its set of texture coordinates. For example
	# on a single "material" I could have a base texture, with a decal texture over it mapped on another set of UV
	# coordinates. I don't know if Blender can do the same.
	if hasVertexUV:
		# Sets the face UV's for the mesh on. The NIF format only supports vertex UV's,
		# but Blender only allows explicit editing of face UV's, so I'll load vertex UV's like face UV's
		meshData.hasFaceUV(1)
		meshData.hasVertexUV(0)
		for i in range(len(meshData.faces)):
			v1, v2, v3 = faces[i]
			meshData.faces[i].uv = []
			for v in (v1, v2, v3):
				(U, V) = vertUV[0][v]
				meshData.faces[i].uv.append((U, V))
	recalcNormals = 1
	if len(vertNorms) > 0:
		recalcNormals = 0
	
	# Texturing property. From this I can retrieve texture info
	texProperty = triShape.getNiTexturingProperty()
	# Material Property, from this I can retrieve material info
	matProperty = triShape.getNiMaterialProperty()
	# Sets the material for this mesh. NIF files only support one material for each mesh
	if matProperty:
		material = createMaterial(matProperty, texProperty)
		# Alpha property
		alphaProperty = triShape.getNiAlphaProperty()
		# Texture. Only supports one atm
		mtex = material.getTextures()[0]
		# if the mesh has an alpha channel
		if alphaProperty:
			material.mode |= Material.Modes.ZTRANSP # enable z-buffered transparency
			# if the image has an alpha channel => then this overrides the material alpha value
			if mtex and mtex.tex.image.depth == 32: # ... crappy way to check for alpha channel in texture
				mtex.tex.imageFlags |= Blender.Texture.ImageFlags.USEALPHA # use the alpha channel
				mtex.mapto |=  Texture.MapTo.ALPHA # and map the alpha channel to transparency
				material.setAlpha(0.0) # for proper display in Blender, we must set the alpha value to 0 and the "Val" slider in the texture Map To tab to the NIF material alpha value (but we do not have access to that button yet... we have to wait until it gets supported by the Blender Python API...)
		else:
			# no alpha property: force alpha 1.0 in Blender
			material.setAlpha(1.0)
		if hasVertexCol:
			if mtex:
				material.mode |= Material.Modes.VCOL_LIGHT # textured material: vertex colors influence lighting
			else:
				material.mode |= Material.Modes.VCOL_PAINT # non-textured material: vertex colors incluence color
		meshData.addMaterial(material)
		#If there's a texture assigned to this material sets it to be displayed in Blender's 3D view
		if mtex:
			imgobj = mtex.tex.getImage()
			for f in meshData.faces: 
				f.image = imgobj
				
	# Put the object in blender
	meshObj = Blender.NMesh.PutRaw(meshData, name, recalcNormals) # amorilia
	# Name the object linked to the mesh
	meshObj.name = name # amorilia
	# sets the transform matrix for the object.
	meshObj.setMatrix(xform)
	# Skinning info, for meshes affected by bones. Adding groups to a mesh can be done only after this is already
	# linked to an object
	skinInstance = triShape.getNiSkinInstance()
	if skinInstance:
		skinData = skinInstance.getNiSkinData()
		weights = skinData.getWeights()
		for idx, bone in enumerate(skinInstance.getBones()):
			if bone:
				groupName = bone.getName()
				meshData.addVertGroup(groupName)
				for vert, weight in weights[idx]:
					vert2 = vertmap[vert]
					meshData.assignVertsToGroup(groupName, [vert2], weight, 'replace')
	meshData.update(1) # amorilia: let Blender calculate vertex normals

	# morphing
	morphCtrl = triShape.getNiGeomMorpherController()
	if morphCtrl:
		morphData = morphCtrl.getNiMorphData()
		if morphData and ( morphData.NumMorphBlocks > 0 ):
			# insert base key
			meshData.insertKey( 0, 'relative' )
			frameCnt, frameType, frames, baseverts = morphData.MorphBlocks[0]
			ipo = Blender.Ipo.New( 'Key', 'KeyIpo' )
			# iterate through the list of other morph keys
			for key in range( 1, morphData.NumMorphBlocks ):
				frameCnt, frameType, frames, verts = morphData.MorphBlocks[key]
				# for each vertex calculate the key position from base pos + delta offset
				for count in range( morphData.NumVertices ):
					x, y, z = baseverts[count]
					dx, dy, dz = verts[count]
					meshData.verts[vertmap[count]].co[0] = x + dx
					meshData.verts[vertmap[count]].co[1] = y + dy
					meshData.verts[vertmap[count]].co[2] = z + dz
				# update the mesh and insert key
				meshData.update(1) # recalculate normals
				meshData.insertKey(key, 'relative')
				# set up the ipo key curve
				curve = ipo.addCurve( 'Key %i'%key )
				# dunno how to set up the bezier triples -> switching to linear instead
				curve.setInterpolation( 'Linear' )
				# select extrapolation
				if ( morphCtrl.Flags == 0x000c ):
					curve.setExtrapolation( 'Constant' )
				elif ( morphCtrl.Flags == 0x0008 ):
					curve.setExtrapolation( 'Cyclic' )
				else:
					debugMsg( 'dunno which extrapolation to use: using constant instead' );
					curve.setExtrapolation( 'Constant' )
				# set up the curve's control points
				for count in range( frameCnt ):
					time, x, y, z = frames[count]
					frame = time * Blender.Scene.getCurrent().getRenderingContext().framesPerSec() + 1
					curve.addBezier( ( frame, x ) )
				# finally: return to base position
				for count in range( morphData.NumVertices ):
					x, y, z = baseverts[count]
					meshData.verts[vertmap[count]].co[0] = x
					meshData.verts[vertmap[count]].co[1] = y
					meshData.verts[vertmap[count]].co[2] = z
				meshData.update(1) # recalculate normals
			# assign ipo to mesh (not supported by Blender API?)
			#meshData.setIpo( ipo )
				
	return meshObj

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Main function, everything starts here
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
# This loads data from a .NIF file, decodes the
# version, creates the corresponding object and
# loads the information from the object in Blender
def readFile(filename):
	debugMsg("-----\nLoading %s" % filename, 2)
	versList = ('4.0.0.2') # for further extension
	# detect morrowind texture path
	global nifdir
	global texdir
	nifdir = Blender.sys.dirname(filename)
	texdir = nifdir
	idx = texdir.lower().find('meshes')
	if ( idx >= 0 ): texdir = texdir[:idx] + 'textures'
	# opens the file in "rb" modality, read only, binary mode
	file = open(filename, "rb")
	# Reads the content of the file in the data variable, to python purposes, a string
	data = file.read()
	file.close()
	fileTypeString = 'NetImmerse File Format' 
	if data[0 : len(fileTypeString)] != fileTypeString:
		msg = 'This does not appear to be a Netimmerse file'
		Blender.Draw.PupMenu("ERROR%t|"+msg)
	else:
		headerString = data[0:data[0:50].find('\x0A')]
		version, dummy = readVersion(data, len(headerString)+1)
		versionString = '%s.%s.%s.%s' % version
		nifObject = None
		if versionString in versList:
			# Selects the base texture folder.
			# Argh, the fileselector doesn't return folders!
			# I'll set up a gui for this
			#Blender.Window.FileSelector(setTextureFolder, 'SELECT TEXTURE FOLDER')
			# Reads in memory the file content
			nifObject = NifDocument(data)
		else:
			debugMsg('NIF version not supported:\n\t%s' % headerString,2)
			msg = 'This file format is not (yet?) supported'
			Blender.Draw.PupMenu("ERROR%t|"+msg)
			return
		# Free memory (I hope)
		data = None
		# ok, let's try and write the meshes to Blender
		nifObject.writeToBlender()
	return

# Not implemented yet, but I'll make a GUI version sometime
def drawGui():
	pass

Blender.Window.FileSelector(readFile, 'LOAD FILE')
