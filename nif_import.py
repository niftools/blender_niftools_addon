#!BPY

""" Registration info for Blender menus:
Name: 'NetImmerse/Gamebryo (.nif & .kf)...'
Blender: 241
Group: 'Import'
Tip: 'Import NIF File Format (.nif & .kf)'
"""

__author__ = "The NifTools team, http://niftools.sourceforge.net/"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__version__ = "1.4"
__bpydoc__ = """\
This script imports Netimmerse (the version used by Morrowind) .NIF files to Blender.
So far the script has been tested with 4.0.0.2 format files (Morrowind, Freedom Force).
There is a know issue with the import of .NIF files that have an armature; the file will import, but the meshes will be somewhat misaligned.

Usage:

Run this script from "File->Import" menu and then select the desired NIF file.

Options:

Scale Correction: How many NIF units is one Blender unit?

Vertex Duplication (Fast): Fast but imperfect: may introduce unwanted cracks in UV seams.

Vertex Duplication (Slow): Perfect but slow, this is the preferred method if the model you are importing is not too large.

Smoothing Flag (Slow): Import seams and convert them to "the Blender way", is slow and imperfect, unless model was created by Blender and had no duplicate vertices.

Tex Path: Semi-colon separated list of texture directories.
"""

# nif_import.py version 1.4
# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****
# Note: Versions of this script previous to 1.0.6 were released under the GPL license
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
#   Hey, this is my first ever python script!
# SJH for the binary conversion functions. Got the code off a forum somewhere, posted by Ideasman,
#   I suppose it's allright to use it
# Lars Rinde (AKA Taharez), for helping me a lot with the file format, and with some debugging even
#   though he doesn't 'do Python'
# Timothy Wakeham (AKA timmeh), for taking some of his time to help me get to terms with the way
#   the UV maps work in Blender
# Amorilia (don't know your name buddy), for bugfixes and testing.



try:
    import types
except:
    err = """--------------------------
ERROR\nThis script requires a full Python 2.4 installation to run.
--------------------------""" % sys.version
    print err
    Draw.PupMenu("ERROR%t|Python installation not found, check console for details")
    raise

import Blender, sys
from Blender import BGL
from Blender import Draw
from Blender.Mathutils import *

try:
    from niflib import *
except:
    err = """--------------------------
ERROR\nThis script requires the NIFLIB Python SWIG wrapper, niflib.py & _niflib.dll.
Make sure these files reside in your Python path or in your Blender scripts folder.
If you don't have them: http://niftools.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|NIFLIB not found, check console for details")
    raise

# dictionary of texture files, to reuse textures
TEXTURES = {}

# dictionary of materials, to reuse materials
MATERIALS = {}

# dictionary of names, to map NIF names to correct Blender names
NAMES = {}

# dictionary of armatures
ARMATURES = {}

# dictionary of bones that belong to a certain armature
BONE_LIST = {}

# some variables

USE_GUI = 0 # BROKEN, don't set to 1, we will design a GUI for importer & exporter jointly
EPSILON = 0.005 # used for checking equality with floats, NOT STORED IN CONFIG
MSG_LEVEL = 2 # verbosity level

# 
# Process config files.
# 

# configuration default values
TEXTURES_DIR = 'C:\\Program Files\\Bethesda\\Morrowind\\Data Files\\Textures' # Morrowind: this will work on a standard installation
IMPORT_DIR = ''
SEAMS_IMPORT = 1

# tooltips
tooltips = {
    'TEXTURES_DIR': "Texture directory.",
    'IMPORT_DIR': "Default import directory.",
    'SEAMS_IMPORT': "How to handle seams?"
}

# bounds
limits = {
    'SEAMS_IMPORT': [0, 2]
}

# update registry
def update_registry():
    # populate a dict with current config values:
    d = {}
    d['TEXTURES_DIR'] = TEXTURES_DIR
    d['IMPORT_DIR'] = IMPORT_DIR
    d['SEAMS_IMPORT'] = SEAMS_IMPORT
    d['limits'] = limits
    d['tooltips'] = tooltips
    # store the key
    Blender.Registry.SetKey('nif_import', d, True)
    read_registry()

# Now we check if our key is available in the Registry or file system:
def read_registry():
    global TEXTURES_DIR, IMPORT_DIR, SEAMS_IMPORT
    regdict = Blender.Registry.GetKey('nif_import', True)
    # If this key already exists, update config variables with its values:
    if regdict:
        try:
            TEXTURES_DIR = regdict['TEXTURES_DIR'] 
            IMPORT_DIR = regdict['IMPORT_DIR']
            SEAMS_IMPORT = regdict['SEAMS_IMPORT']
            tmp_limits = regdict['limits']     # just checking if it's there
            tmp_tooltips = regdict['tooltips'] # just checking if it's there
        # if data was corrupted (or a new version of the script changed
        # (expanded, removed, renamed) the config vars and users may have
        # the old config file around):
        except: update_registry() # rewrite it
    else: # if the key doesn't exist yet, use our function to create it:
        update_registry()

read_registry()



# check export script config key for scale correction

SCALE_CORRECTION = 10.0 # same default value as in export script

rd = Blender.Registry.GetKey('nif_export', True)
if rd:
    try:
        SCALE_CORRECTION = rd['SCALE_CORRECTION']
    except: pass

# check General scripts config key for default behaviors

VERBOSE = True
CONFIRM_OVERWRITE = True

rd = Blender.Registry.GetKey('General', True)
if rd:
    try:
        VERBOSE = rd['verbose']
        CONFIRM_OVERWRITE = rd['confirm_overwrite']
    except: pass

# Little wrapper for debug messages
def msg(message='-', level=2):
    if VERBOSE:
        if level <= MSG_LEVEL:
            print message

#
# A simple custom exception class.
#
class NIFImportError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


#
# Emulates the act of pressing the "home" key
#
def fit_view():
    Draw.Redraw(1)
    winid = Blender.Window.GetScreenInfo(Blender.Window.Types.VIEW3D)[0]['id']
    Blender.Window.SetKeyQualifiers(0)
    Blender.Window.QAdd(winid, Draw.HOMEKEY, 1)
    Blender.Window.QHandle(winid)
    Blender.Window.QAdd(winid, Draw.HOMEKEY, 0)
    Draw.Redraw(1)
    
#
# Main import function.
#
def import_nif(filename):
    try: # catch NIFImportErrors
        global NIF_DIR, TEX_DIR
        NIF_DIR = Blender.sys.dirname(filename)
        # Morrowind smart texture dir
        idx = NIF_DIR.lower().find('meshes')
        if ( idx >= 0 ):
            TEX_DIR = NIF_DIR[:idx] + 'textures'
        else:
            TEX_DIR = None
        # scene info
        global b_scene
        b_scene = Blender.Scene.GetCurrent()
        # read the NIF file
        root_block = ReadNifTree(filename)
        # used to control the progress bar
        global block_count, blocks_read, read_progress
        block_count = BlocksInMemory()
        read_progress = 0.0
        blocks_read = 0.0
        # preprocessing:
        # mark armature nodes and bones
        # and merge armatures that are bones of others armatures
        mark_armatures_bones(root_block)
        merge_armatures()
        if VERBOSE and MSG_LEVEL >= 3:
            for arm_name in BONE_LIST.keys():
                print "armature '%s':"%arm_name
                for bone_name in BONE_LIST[arm_name]:
                    print "  bone '%s'"%bone_name
        # read the NIF tree
        if not is_armature_root(root_block):
            blocks = root_block["Children"].asLinkList()
            for niBlock in blocks:
                b_obj = read_branch(niBlock)
                if b_obj:
                    b_obj.setMatrix(b_obj.getMatrix() * fb_scale_mat())
        else:
            b_obj = read_branch(root_block)
            b_obj.setMatrix(b_obj.getMatrix() * fb_scale_mat())
        b_scene.update(1) # do a full update to make sure all transformations get applied
        #fit_view()
        #b_scene.getCurrentCamera()
        
    except NIFImportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Import Failed")
        print 'NIFImportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return

    Blender.Window.DrawProgressBar(1.0, "Finished")
    
# Reads the content of the current NIF tree branch to Blender recursively
def read_branch(niBlock):
    # used to control the progress bar
    global block_count, blocks_read, read_progress
    blocks_read += 1.0
    if (blocks_read/block_count) >= (read_progress + 0.1):
        read_progress = blocks_read/block_count
        Blender.Window.DrawProgressBar(read_progress, "Reading NIF file")
    if not niBlock.is_null():
        btype = niBlock.GetBlockType()
        if btype == "NiTriShape" or btype == "NiTriStrips":
            # it's a shape node
            return fb_mesh(niBlock)
        elif not niBlock["Children"].is_null():
            # it's a parent node
            niChildren = niBlock["Children"].asLinkList()
            b_obj = None
            if is_armature_root(niBlock):
                # the whole bone branch is imported by fb_armature as well
                b_obj = fb_armature(niBlock)
                # now also do the meshes
                read_armature_branch(b_obj, niBlock, niBlock)
            else:
                b_obj = fb_empty(niBlock)
                b_children_list = []
                for child in niChildren:
                    b_child_obj = read_branch(child)
                    if b_child_obj: b_children_list.append(b_child_obj)
                b_obj.makeParent(b_children_list)
            b_obj.setMatrix(fb_matrix(niBlock))
            return b_obj
        else:
            return None

# Reads the content of the current NIF tree branch to Blender
# recursively, as meshes parented to a given armature. Note that
# niBlock must have been imported previously as an armature, along
# with all its bones. This function only imports meshes.
def read_armature_branch(b_armature, niArmature, niBlock):
    # used to control the progress bar
    global block_count, blocks_read, read_progress
    blocks_read += 1.0
    if (blocks_read/block_count) >= (read_progress + 0.1):
        read_progress = blocks_read/block_count
        Blender.Window.DrawProgressBar(read_progress, "Reading NIF file")
    # check if the child is non-null
    if not niBlock.is_null():
        btype = niBlock.GetBlockType()
        # bone or group node?
        # is it an AParentNode?
        if not niBlock["Children"].is_null():
            niChildren = niBlock["Children"].asLinkList()
            for niChild in niChildren:
                b_mesh = read_armature_branch(b_armature, niArmature, niChild)
                if b_mesh:
                    # correct the transform
                    # it's parented to the armature!
                    armature_matrix_inverse = fb_global_matrix(niArmature)
                    armature_matrix_inverse.invert()
                    b_mesh.setMatrix(fb_global_matrix(niChild) * armature_matrix_inverse)
                    # add a vertex group if it's parented to a bone
                    par_bone = get_closest_bone(niChild)
                    if not par_bone.is_null():
                        # set vertex index 1.0 for all vertices that don't yet have a vertex weight
                        # this will mimick the fact that the mesh is parented to the bone
                        b_meshData = b_mesh.getData(mesh=True)
                        verts = [ v.index for v in b_meshData.verts ] # copy vertices, as indices
                        for groupName in b_meshData.getVertGroupNames():
                            for v in b_meshData.getVertsFromGroup(groupName):
                                try:
                                    verts.remove(v)
                                except ValueError: # remove throws value-error if vertex was already removed previously
                                    pass
                        if verts:
                            groupName = NAMES[par_bone["Name"].asString()]
                            b_meshData.addVertGroup(groupName)
                            b_meshData.assignVertsToGroup(groupName, verts, 1.0, Blender.Mesh.AssignModes.REPLACE)
                    # make it parent of the armature
                    b_armature.makeParentDeform([b_mesh])
        # mesh?
        elif btype == "NiTriShape" or btype == "NiTriStrips":
            return fb_mesh(niBlock)
        # anything else: throw away
        else:
            return None

#
# Get unique name for an object, preserving existing names
#
def fb_name(niBlock):
    global NAMES

    # find unique name for Blender to use
    uniqueInt = 0
    niName = niBlock["Name"].asString()
    name = niName[:19] # Blender has a rather small name buffer
    try:
        while Blender.Object.Get(name):
            name = '%s.%02d' % (niName[:15], uniqueInt)
            uniqueInt +=1
    except:
        pass

    # save mapping
    NAMES[niName] = name

    return name

# Retrieves a niBlock's transform matrix as a Mathutil.Matrix
def fb_matrix(niBlock):
    inode=QueryNode(niBlock)
    m=inode.GetLocalBindPos() # remind: local bind position != local transform
    b_matrix = Matrix([m[0][0],m[0][1],m[0][2],m[0][3]],\
                      [m[1][0],m[1][1],m[1][2],m[1][3]],\
                      [m[2][0],m[2][1],m[2][2],m[2][3]],\
                      [m[3][0],m[3][1],m[3][2],m[3][3]])
    return b_matrix

def fb_global_matrix(niBlock):
    inode=QueryNode(niBlock)
    m=inode.GetWorldBindPos() # remind: local bind position != local transform
    b_matrix = Matrix([m[0][0],m[0][1],m[0][2],m[0][3]],\
                      [m[1][0],m[1][1],m[1][2],m[1][3]],\
                      [m[2][0],m[2][1],m[2][2],m[2][3]],\
                      [m[3][0],m[3][1],m[3][2],m[3][3]])
    return b_matrix

# Returns the scale correction matrix. A bit silly to calculate it all the time,
# but the overhead is minimal and when the GUI will work again this will be useful.
def fb_scale_mat():
    s = 1.0/SCALE_CORRECTION 
    return Matrix([s,0,0,0],[0,s,0,0],[0,0,s,0],[0,0,0,1])

# Creates and returns a grouping empty
def fb_empty(niBlock):
    global b_scene
    b_empty = Blender.Object.New("Empty", fb_name(niBlock))
    b_scene.link(b_empty)
    return b_empty

# scans an armature hierarchy, and returns a whole armature.
# This is done outside the normal node tree scan to allow for positioning of the bones
def fb_armature(niBlock):
    global b_scene
    global ARMATURES
    
    armature_name = fb_name(niBlock)
    armature_matrix_inverse = fb_global_matrix(niBlock)
    armature_matrix_inverse.invert()
    b_armature = Blender.Object.New('Armature', fb_name(niBlock))
    b_armatureData = Blender.Armature.Armature()
    b_armatureData.name = armature_name
    b_armatureData.drawAxes = True
    #b_armatureData.drawType = Blender.Armature.STICK
    #b_armatureData.drawType = Blender.Armature.ENVELOPE
    #b_armatureData.drawType = Blender.Armature.OCTAHEDRON
    b_armature.link(b_armatureData)
    b_armatureData.makeEditable()
    #read_bone_chain(niBlock, b_armature)
    niChildren = niBlock["Children"].asLinkList()
    niChildBones = [child for child in niChildren if is_bone(child)]  
    for niBone in niChildBones:
        # Ok, possibly forwarding the inverse of the armature matrix through all the bone chain is silly,
        # but I believe it saves some processing time compared to making it global or recalculating it all the time.
        # And serves the purpose fine
        fb_bone(niBone, b_armature, b_armatureData, armature_matrix_inverse)
    ARMATURES[niBlock] = b_armature
    b_armatureData.update()
    b_scene.link(b_armature)
    return b_armature

def fb_bone(niBlock, b_armature, b_armatureData, armature_matrix_inverse):
    bone_name = fb_name(niBlock)
    niChildren = niBlock["Children"].asLinkList()
    niChildNodes = [child for child in niChildren if child.GetBlockType() == "NiNode"]  
    niChildBones = [child for child in niChildNodes if is_bone(child)]  
    if is_bone(niBlock):
        # create bones here...
        b_bone = Blender.Armature.Editbone()
        # head: get position from niBlock
        armature_space_matrix = fb_global_matrix(niBlock) * armature_matrix_inverse
        b_bone_head_x = armature_space_matrix[3][0]
        b_bone_head_y = armature_space_matrix[3][1]
        b_bone_head_z = armature_space_matrix[3][2]
        # tail: average of children location
        child_matrices = [(fb_global_matrix(child)*armature_matrix_inverse) for child in niChildNodes]
        if len(niChildNodes) > 0:
            b_bone_tail_x = sum([child_matrix[3][0] for child_matrix in child_matrices]) / len(child_matrices)
            b_bone_tail_y = sum([child_matrix[3][1] for child_matrix in child_matrices]) / len(child_matrices)
            b_bone_tail_z = sum([child_matrix[3][2] for child_matrix in child_matrices]) / len(child_matrices)
        else:
            # no children... continue bone sequence in the same direction as parent, with the same length
            # this seems to work fine
            parent = niBlock.GetParent()
            parent_matrix = fb_global_matrix(parent) * armature_matrix_inverse
            b_parent_head_x = parent_matrix[3][0]
            b_parent_head_y = parent_matrix[3][1]
            b_parent_head_z = parent_matrix[3][2]
            b_bone_tail_x = 2 * b_bone_head_x - b_parent_head_x
            b_bone_tail_y = 2 * b_bone_head_y - b_parent_head_y
            b_bone_tail_z = 2 * b_bone_head_z - b_parent_head_z
        # sets the bone heads & tails
        b_bone.head = Vector(b_bone_head_x, b_bone_head_y, b_bone_head_z)
        b_bone.tail = Vector(b_bone_tail_x, b_bone_tail_y, b_bone_tail_z)
        # now we set the matrix; this has the following consequences:
        # - head is preserved
        # - bone length is preserved
        # - tail is lost (up to bone length)
        # also, we must transform y into x to comply with Blender's armature conventions: m_correct does that
        ### NOTE: don't import matrix at all, works even better!
        ### m_correct = RotationMatrix(-90.0, 3, 'z') # y -> x; we probably want an import option for this transform
        ### b_bone.matrix = m_correct * armature_space_matrix.rotationPart()
        b_armatureData.bones[bone_name] = b_bone
        for niBone in niChildBones:
            b_child_bone =  fb_bone(niBone, b_armature, b_armatureData, armature_matrix_inverse)
            if b_child_bone:
                b_child_bone.parent = b_bone
        return b_bone
    return None


def fb_texture( niSourceTexture ):
    global TEXTURES
    
    # This won't work due to the way Niflib works
    #if TEXTURES.has_key( niSourceTexture ):
    #    return TEXTURES[ niSourceTexture ]
    # Alternative:
    try:
        return TEXTURES[niSourceTexture]
    except:
        pass
    #for t in TEXTURES.keys():
    #    if t == niSourceTexture: # invokes Niflib's block equality operator...
    #        return TEXTURES[t]

    b_image = None
    
    niTexSource = niSourceTexture["Texture Source"].asTexSource()
    
    if niTexSource.useExternal:
        # the texture uses an external image file
        fn = niTexSource.fileName
        # go searching for it
        textureFile = None
        for texdir in TEXTURES_DIR.split(";") + [NIF_DIR, TEX_DIR]:
            if texdir == None: continue
            texdir.replace( '\\', Blender.sys.sep )
            texdir.replace( '/', Blender.sys.sep )
             # now a little trick, to satisfy many Morrowind mods
            if (fn[:9].lower() == 'textures\\') and (texdir[-9:].lower() == '\\textures'):
                tex = Blender.sys.join( texdir, fn[9:] ) # strip one of the two 'textures' from the path
            else:
                tex = Blender.sys.join( texdir, fn )
            if ( tex[-4:].lower() != ".dds" ) and Blender.sys.exists(tex) == 1: # Blender does not support .DDS
                textureFile = tex
                msg("Found %s" % textureFile, 3)
            else:
                # try other formats
                base=tex[:-4]
                for ext in ('.PNG','.png','.TGA','.tga','.BMP','.bmp','.JPG','.jpg'): # Blender does not support .DDS
                    if Blender.sys.exists(base+ext) == 1:
                        textureFile = base+ext
                        msg( "Found %s" % textureFile, 3 )
                        break
            if textureFile:
                b_image = Blender.Image.Load( textureFile )
                break
        else:
            print "texture %s not found"%niTexSource.fileName
    else:
        # the texture image is packed inside the nif -> extract it
        niPixelData = niSourceTexture["Texture Source"].asLink()
        iPixelData = QueryPixelData( niPixelData )
        
        width = iPixelData.GetWidth()
        height = iPixelData.GetHeight()
        
        if iPixelData.GetPixelFormat() == PX_FMT_RGB8:
            bpp = 24
        elif iPixelData.GetPixelFormat() == PX_FMT_RGBA8:
            bpp = 32
        else:
            bpp = None
        
        if bpp != None:
            b_image = Blender.Image.New( "TexImg", width, height, bpp )
            
            pixels = iPixelData.GetColors()
            for x in range( width ):
                Blender.Window.DrawProgressBar( float( x + 1 ) / float( width ), "Image Extraction")
                for y in range( height ):
                    pix = pixels[y*height+x]
                    b_image.setPixelF( x, (height-1)-y, ( pix.r, pix.g, pix.b, pix.a ) )
    
    if b_image != None:
        # create a texture using the loaded image
        b_texture = Blender.Texture.New()
        b_texture.setType( 'Image' )
        b_texture.setImage( b_image )
        b_texture.imageFlags |= Blender.Texture.ImageFlags.INTERPOL
        b_texture.imageFlags |= Blender.Texture.ImageFlags.MIPMAP
        TEXTURES[ niSourceTexture ] = b_texture
        return b_texture
    else:
        TEXTURES[ niSourceTexture ] = None
        return None



# Creates and returns a material
def fb_material(matProperty, textProperty, alphaProperty, specProperty):
    global MATERIALS
    
    # First check if material has been created before.
    # Won't work due to way that Niflib works...
    #try:
    #    material = MATERIALS[(matProperty, textProperty, alphaProperty, specProperty)]
    #    return material
    #except KeyError:
    #    pass
    # Alternative:
    for m in MATERIALS.keys():
        # TODO: more clever way of comparing blocks.
        # Sometimes blocks are unnecessarily repeated in a NIF file.
        # This will result in material duplication.
        # (invoke Niflib's block equality operator)
        if ( matProperty == m[0] ) \
        and ( textProperty == m[1] ) \
        and ( alphaProperty.is_null() == m[2].is_null() ) \
        and ( specProperty.is_null() == m[3].is_null() ):
            return MATERIALS[m]
    # use the material property for the name, other properties usually have
    # no name
    name = fb_name(matProperty)
    material = Blender.Material.New(name)
    # Sets the material colors
    # Specular color
    spec = matProperty["Specular Color"].asFloat3()
    material.setSpecCol([spec[0],spec[1],spec[2]])
    material.setSpec(1.0) # Blender multiplies specular color with this value
    # Diffuse color
    diff = matProperty["Diffuse Color"].asFloat3()
    material.setRGBCol([diff[0],diff[1],diff[2]])
    # Ambient & emissive color
    # We assume that ambient & emissive are fractions of the diffuse color.
    # If it is not an exact fraction, we average out.
    amb = matProperty["Ambient Color"].asFloat3()
    emit = matProperty["Emissive Color"].asFloat3()
    b_amb = 0.0
    b_emit = 0.0
    b_n = 0
    if (diff[0] > EPSILON):
        b_amb += amb[0]/diff[0]
        b_emit += emit[0]/diff[0]
        b_n += 1
    if (diff[1] > EPSILON):
        b_amb += amb[1]/diff[1]
        b_emit += emit[1]/diff[1]
        b_n += 1
    if (diff[2] > EPSILON):
        b_amb += amb[2]/diff[2]
        b_emit += emit[2]/diff[2]
        b_n += 1
    if (b_n > 0):
        b_amb /= b_n
        b_emit /= b_n
    if (b_amb > 1.0): b_amb = 1.0
    if (b_emit > 1.0): b_emit = 1.0
    material.setAmb(b_amb)
    material.setEmit(b_emit)
    # glossiness
    glossiness = matProperty["Glossiness"].asFloat()
    hardness = int(glossiness * 4) # just guessing really
    if hardness < 1: hardness = 1
    if hardness > 511: hardness = 511
    material.setHardness(hardness)
    # Alpha
    alpha = matProperty["Alpha"].asFloat()
    material.setAlpha(alpha)
    baseTexture = None
    glowTexture = None
    if textProperty.is_null() == False:
        iTextProperty = QueryTexturingProperty(textProperty)
        BaseTextureDesc = iTextProperty.GetTexture(BASE_MAP)
        if BaseTextureDesc.isUsed:
            baseTexture = fb_texture(BaseTextureDesc.source)
            if baseTexture:
                # Sets the texture to use face UV coordinates.
                texco = Blender.Texture.TexCo.UV
                # Maps the texture to the base color channel. Not necessarily true.
                mapto = Blender.Texture.MapTo.COL
                # Sets the texture for the material
                material.setTexture(0, baseTexture, texco, mapto)
                mbaseTexture = material.getTextures()[0]
        GlowTextureDesc = iTextProperty.GetTexture(GLOW_MAP)
        if GlowTextureDesc.isUsed:
            glowTexture = fb_texture(GlowTextureDesc.source)
            if glowTexture:
                # glow maps use alpha from rgb intensity
                glowTexture.imageFlags |= Blender.Texture.ImageFlags.CALCALPHA
                # Sets the texture to use face UV coordinates.
                texco = Blender.Texture.TexCo.UV
                # Maps the texture to the base color channel. Not necessarily true.
                mapto = Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT
                # Sets the texture for the material
                material.setTexture(1, glowTexture, texco, mapto)
                mglowTexture = material.getTextures()[1]
    # check transparency
    if alphaProperty.is_null() == False:
        material.mode |= Blender.Material.Modes.ZTRANSP # enable z-buffered transparency
        # if the image has an alpha channel => then this overrides the material alpha value
        if baseTexture:
            if baseTexture.image.depth == 32: # ... crappy way to check for alpha channel in texture
                baseTexture.imageFlags |= Blender.Texture.ImageFlags.USEALPHA # use the alpha channel
                mbaseTexture.mapto |=  Blender.Texture.MapTo.ALPHA # and map the alpha channel to transparency
                # for proper display in Blender, we must set the alpha value
                # to 0 and the "Var" slider in the texture Map To tab to the
                # NIF material alpha value
                material.setAlpha(0.0)
                mbaseTexture.varfac = alpha
        # non-transparent glow textures have their alpha calculated from RGB
        # not sure what to do with glow textures that have an alpha channel
        # for now we ignore those alpha channels
    else:
        # no alpha property: force alpha 1.0 in Blender
        material.setAlpha(1.0)
    # check specularity
    if specProperty.is_null() == True:
        # no specular property: specular color is ignored
        # we do this by setting specularity zero
        material.setSpec(0.0)

    MATERIALS[(matProperty, textProperty, alphaProperty, specProperty)] = material
    return material

# Creates and returns a NiNode wrapped mesh. These happen in rigged geometries
def fb_wrapped_mesh(niBlock):
    global b_scene
    niGeometry = niBlock["Children"].asLinkList()[0]
    b_mesh = fb_mesh(niGeometry)
    b_mesh.name = fb_name(niBlock)
    b_mesh.setMatrix(b_mesh.getMatrix()*fb_matrix(niBlock))
    # the mesh is linked at creation
    # b_scene.link(b_mesh)
    return b_mesh

# Creates and returns a raw mesh
def fb_mesh(niBlock):
    global b_scene
    # Mesh name -> must be unique, so tag it if needed
    b_name=fb_name(niBlock)
    # we mostly work directly on Blender's objects (b_meshData)
    # but for some tasks we must use the Python wrapper (b_nmeshData), see further
    b_meshData = Blender.Mesh.New(b_name)
    b_mesh = Blender.Object.New("Mesh", b_name)
    b_mesh.link(b_meshData)
    b_scene.link(b_mesh)

    # Mesh transform matrix, sets the transform matrix for the object.
    b_mesh.setMatrix(fb_matrix(niBlock))
    # Mesh geometry data. From this I can retrieve all geometry info
    data_blk = niBlock["Data"].asLink();
    iShapeData = QueryShapeData(data_blk)
    iTriShapeData = QueryTriShapeData(data_blk)
    iTriStripsData = QueryTriStripsData(data_blk)
    #vertices
    if not iShapeData:
        raise NIFImportError("no iShapeData returned. Node name: %s " % b_name)
    verts = iShapeData.GetVertices()
    # Faces
    if iTriShapeData:
        faces = iTriShapeData.GetTriangles()
    elif iTriStripsData:
        faces = iTriStripsData.GetTriangles()
    else:
        raise NIFImportError("no iTri*Data returned. Node name: %s " % b_name)
    # "Sticky" UV coordinates. these are transformed in Blender UV's
    # only the first UV set is loaded right now
    uvco = None
    if iShapeData.GetUVSetCount()>0:
        uvco = iShapeData.GetUVSet(0)
    # Vertex colors
    vcols = iShapeData.GetColors()
    # Vertex normals
    norms = iShapeData.GetNormals()

    v_map = [0]*len(verts) # pre-allocate memory, for faster performance
    if SEAMS_IMPORT == 0:
        # Fast method: don't care about any seams!
        for i, v in enumerate(verts):
            v_map[i] = i # NIF vertex i maps to blender vertex i
            b_meshData.verts.extend(v.x, v.y, v.z) # add the vertex
    elif SEAMS_IMPORT == 1:
        # Slow method, but doesn't introduce unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
        # Normals are calculated by Blender.
        n_map = {}
        b_v_index = 0
        for i, v in enumerate(verts):
            # The key k identifies unique vertex /normal pairs.
            # We use a tuple of ints for key, this works MUCH faster than a
            # tuple of floats.
            if norms:
                n = norms[i]
                k = (int(v.x*200),int(v.y*200),int(v.z*200),\
                     int(n.x*200),int(n.y*200),int(n.z*200))
            else:
                k = (int(v.x*200),int(v.y*200),int(v.z*200))
            # see if we already added this guy, and if so, what index
            try:
                n_map_k = n_map[k] # this is the bottle neck... can we speed this up?
            except KeyError:
                n_map_k = None
            if n_map_k == None:
                # not added: new vertex / normal pair
                n_map[k] = i         # unique vertex / normal pair with key k was added, with NIF index i
                v_map[i] = b_v_index # NIF vertex i maps to blender vertex b_v_index
                b_meshData.verts.extend(v.x, v.y, v.z) # add the vertex
                b_v_index += 1
            else:
                # already added
                v_map[i] = v_map[n_map_k] # NIF vertex i maps to Blender v_map[vertex n_map_nk]
        # release memory
        del n_map

    # Adds the faces to the mesh
    f_map = [None]*len(faces)
    b_f_index = 0
    for i, f in enumerate(faces):
        if f.v1 != f.v2 and f.v1 != f.v3 and f.v2 != f.v3:
            v1=b_meshData.verts[v_map[f.v1]]
            v2=b_meshData.verts[v_map[f.v2]]
            v3=b_meshData.verts[v_map[f.v3]]
            if (v1 == v2) or (v2 == v3) or (v3 == v1):
                continue # we get a ValueError on faces.extend otherwise
            tmp1 = len(b_meshData.faces)
            # extend checks for duplicate faces
            # see http://www.blender3d.org/documentation/240PythonDoc/Mesh.MFaceSeq-class.html
            b_meshData.faces.extend(v1, v2, v3)
            if tmp1 == len(b_meshData.faces): continue # duplicate face!
            f_map[i] = b_f_index # keep track of added faces, mapping NIF face index to Blender face index
            b_f_index += 1
    # at this point, deleted faces (degenerate or duplicate)
    # satisfy f_map[i] = None
    
    # Sets face smoothing and material
    if norms:
        for f in b_meshData.faces:
            f.smooth = 1
            f.mat = 0
    else:
        for f in b_meshData.faces:
            f.smooth = 0 # no normals, turn off smoothing
            f.mat = 0

    # vertex colors
    vcol = iShapeData.GetColors()
    if len( vcol ) == 0:
        vcol = None
    else:
        b_meshData.vertexColors = 1
        for i, f in enumerate(faces):
            if f_map[i] == None: continue
            b_face = b_meshData.faces[f_map[i]]
            
            vc = vcol[f.v1]
            b_face.col[0].r = int(vc.r * 255)
            b_face.col[0].g = int(vc.g * 255)
            b_face.col[0].b = int(vc.b * 255)
            b_face.col[0].a = int(vc.a * 255)
            vc = vcol[f.v2]
            b_face.col[1].r = int(vc.r * 255)
            b_face.col[1].g = int(vc.g * 255)
            b_face.col[1].b = int(vc.b * 255)
            b_face.col[1].a = int(vc.a * 255)
            vc = vcol[f.v3]
            b_face.col[2].r = int(vc.r * 255)
            b_face.col[2].g = int(vc.g * 255)
            b_face.col[2].b = int(vc.b * 255)
            b_face.col[2].a = int(vc.a * 255)
        # vertex colors influence lighting...
        # so now we have to set the VCOL_LIGHT flag on the material
        # see below
        
    # UV coordinates
    # Nif files only support 'sticky' UV coordinates, and duplicates vertices to emulate hard edges and UV seams.
    # Essentially whenever an hard edge or an UV seam is present the mesh this is converted to an open mesh.
    # Blender also supports 'per face' UV coordinates, this could be a problem when exporting.
    # Also, NIF files support a series of texture sets, each one with its set of texture coordinates. For example
    # on a single "material" I could have a base texture, with a decal texture over it mapped on another set of UV
    # coordinates. I don't know if Blender can do the same.

    if uvco:
        # Sets the face UV's for the mesh on. The NIF format only supports vertex UV's,
        # but Blender only allows explicit editing of face UV's, so I'll load vertex UV's like face UV's
        b_meshData.faceUV = 1
        b_meshData.vertexUV = 0
        for i, f in enumerate(faces):
            if f_map[i] == None: continue
            uvlist = []
            # We have to be careful here... another Blender pitfall:
            # faces.extend sometimes adds face vertices in different order than
            # the order of it's arguments, here we detect how it was added, and
            # hopefully this works in all cases :-)
            # (note: we assume that faces.extend does not change the orientation)
            if (v_map[f.v1] == b_meshData.faces[f_map[i]].verts[0].index):
                # this is how it "should" be
                for v in (f.v1, f.v2, f.v3):
                    uv=uvco[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            elif (v_map[f.v1] == b_meshData.faces[f_map[i]].verts[1].index):
                # vertex 3 was added first
                for v in (f.v3, f.v1, f.v2):
                    uv=uvco[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            elif (v_map[f.v1] == b_meshData.faces[f_map[i]].verts[2].index):
                # vertex 2 was added first
                for v in (f.v2, f.v3, f.v1):
                    uv=uvco[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            else:
                raise NIFImportError("Invalid UV index (BUG?)")
    
    # Sets the material for this mesh. NIF files only support one material for each mesh.
    matProperty = niBlock["Properties"].FindLink("NiMaterialProperty" )
    if matProperty.is_null() == False:
        # create material and assign it to the mesh
        textProperty = niBlock["Properties"].FindLink( "NiTexturingProperty" )
        alphaProperty = niBlock["Properties"].FindLink("NiAlphaProperty")
        specProperty = niBlock["Properties"].FindLink("NiSpecularProperty")
        material = fb_material(matProperty, textProperty, alphaProperty, specProperty)
        b_meshData.materials = [material]

        # fix up vertex colors depending on whether we had textures in the material
        mbasetex = material.getTextures()[0]
        mglowtex = material.getTextures()[1]
        if b_meshData.vertexColors == 1:
            if mbasetex or mglowtex:
                material.mode |= Blender.Material.Modes.VCOL_LIGHT # textured material: vertex colors influence lighting
            else:
                material.mode |= Blender.Material.Modes.VCOL_PAINT # non-textured material: vertex colors incluence color

        # if there's a base texture assigned to this material sets it to be displayed in Blender's 3D view
        # but only if we have UV coordinates...
        if mbasetex and uvco:
            TEX = Blender.Mesh.FaceModes['TEX'] # face mode bitfield value
            imgobj = mbasetex.tex.getImage()
            if imgobj:
                for f in b_meshData.faces:
                    f.mode = TEX
                    f.image = imgobj

    # Skinning info, for meshes affected by bones. Adding groups to a mesh can be done only after this is already
    # linked to an object.
    skinInstance = niBlock["Skin Instance"].asLink()
    if skinInstance.is_null() == False:
        skinData = skinInstance["Data"].asLink()
        iSkinData = QuerySkinData(skinData)
        bones = iSkinData.GetBones()
        for idx, bone in enumerate(bones):
            weights = iSkinData.GetWeights(bone)
            groupName = NAMES[bone["Name"].asString()]
            b_meshData.addVertGroup(groupName)
            for vert, weight in weights.iteritems():
                b_meshData.assignVertsToGroup(groupName, [v_map[vert]], weight, Blender.Mesh.AssignModes.REPLACE)

    b_meshData.calcNormals() # let Blender calculate vertex normals
    
    # geometry morphing: here we need the NMesh b_nmeshData
    # the Mesh object has no vertex key Python API (yet?)
    b_nmeshData = Blender.NMesh.GetRaw(b_meshData.name)
    morphCtrl = find_controller(niBlock, "NiGeomMorpherController")
    if morphCtrl.is_null() == False:
        morphData = morphCtrl["Data"].asLink()
        if ( morphData.is_null() == False ):
            iMorphData = QueryMorphData(morphData)
            if ( iMorphData.GetMorphCount() > 0 ):
                # insert base key
                b_nmeshData.insertKey( 0, 'relative' )
                baseverts = iMorphData.GetMorphVerts( 0 )
                ipo = Blender.Ipo.New( 'Key', 'KeyIpo' )
                # iterate through the list of other morph keys
                for key in range(1,iMorphData.GetMorphCount()):
                    morphverts = iMorphData.GetMorphVerts( key )
                    # for each vertex calculate the key position from base pos + delta offset
                    for count in range( iMorphData.GetVertexCount() ):
                        x = baseverts[count].x
                        y = baseverts[count].y
                        z = baseverts[count].z
                        dx = morphverts[count].x
                        dy = morphverts[count].y
                        dz = morphverts[count].z
                        b_nmeshData.verts[v_map[count]].co[0] = x + dx
                        b_nmeshData.verts[v_map[count]].co[1] = y + dy
                        b_nmeshData.verts[v_map[count]].co[2] = z + dz
                    # update the mesh and insert key
                    b_nmeshData.update(recalc_normals=1) # recalculate normals
                    b_nmeshData.insertKey(key, 'relative')
                    # set up the ipo key curve
                    curve = ipo.addCurve( 'Key %i'%key )
                    # dunno how to set up the bezier triples -> switching to linear instead
                    curve.setInterpolation( 'Linear' )
                    # select extrapolation
                    if ( morphCtrl["Flags"].asInt() == 0x000c ):
                        curve.setExtrapolation( 'Constant' )
                    elif ( morphCtrl["Flags"].asInt() == 0x0008 ):
                        curve.setExtrapolation( 'Cyclic' )
                    else:
                        msg( 'dunno which extrapolation to use: using constant instead', 2 )
                        curve.setExtrapolation( 'Constant' )
                    # set up the curve's control points
                    morphkeys = iMorphData.GetMorphKeys(key)
                    for count in range(len(morphkeys)):
                        morphkey = morphkeys[count]
                        time = morphkey.time
                        x = morphkey.data
                        frame = time * Blender.Scene.getCurrent().getRenderingContext().framesPerSec() + 1
                        curve.addBezier( ( frame, x ) )
                    # finally: return to base position
                    for count in range( iMorphData.GetVertexCount() ):
                        x = baseverts[count].x
                        y = baseverts[count].y
                        z = baseverts[count].z
                        b_nmeshData.verts[v_map[count]].co[0] = x
                        b_nmeshData.verts[v_map[count]].co[1] = y
                        b_nmeshData.verts[v_map[count]].co[2] = z
                    b_nmeshData.update(recalc_normals=1) # recalculate normals
                # assign ipo to mesh
                b_nmeshData.key.ipo = ipo

    return b_mesh



# find a controller
def find_controller(block, controllertype):
    ctrl = block["Controller"].asLink()
    while ctrl.is_null() == False:
        if ctrl.GetBlockType() == controllertype:
            break
        ctrl = ctrl["Next Controller"].asLink()
    return ctrl



# mark armatures and bones by peeking into NiSkinInstance blocks
# probably we will eventually have to use this
# since that the "is skinning influence" flag is not reliable
def mark_armatures_bones(block):
    global BONE_LIST
    # search for all NiTriShape or NiTriStrips blocks...
    if block.GetBlockType() == "NiTriShape" or block.GetBlockType() == "NiTriStrips":
        # yes, we found one, get its skin instance
        skininst = block["Skin Instance"].asLink()
        if skininst.is_null() == False:
            msg("Skin instance found on block '%s'"%block["Name"].asString(),3)
            # it has a skin instance, so get the skeleton root
            # which is an armature only if it's not a skinning influence
            # so mark the node to be imported as an armature
            skelroot = skininst["Skeleton Root"].asLink()
            skelroot_name = skelroot["Name"].asString()
            if not BONE_LIST.has_key(skelroot_name):
                BONE_LIST[skelroot_name] = []
                msg("'%s' is an armature"%skelroot_name,3)
            # now get the skinning data interface to retrieve the list of bones
            skindata = skininst["Data"].asLink()
            iskindata = QuerySkinData(skindata)
            for bone in iskindata.GetBones():
                # add them, if we haven't already
                bone_name = bone["Name"].asString()
                if not bone_name in BONE_LIST[skelroot_name]:
                    BONE_LIST[skelroot_name].append(bone_name)
                    msg("'%s' is a bone of armature '%s'"%(bone_name,skelroot_name),3)
                # now we "attach" the bone to the armature:
                # we make sure all NiNodes from this bone all the way
                # down to the armature NiNode are marked as bones
                complete_bone_tree(bone, skelroot_name)
    else:
        # nope, it's not a NiTriShape or NiTriStrips
        # so if it's a NiNode
        if not block["Children"].is_null():
            # search for NiTriShapes or NiTriStrips in the list of children
            for child in block["Children"].asLinkList():
                mark_armatures_bones(child)



# this function helps to make sure that the bones actually form a tree,
# all the way down to the armature node
# just call it on all bones of a skin instance
def complete_bone_tree(bone, skelroot_name):
    global BONE_LIST
    # we must already have marked this one as a bone
    bone_name = bone["Name"].asString()
    assert BONE_LIST.has_key(skelroot_name) # debug
    assert bone_name in BONE_LIST[skelroot_name] # debug
    # get the node parent, this should be marked as an armature or as a bone
    boneparent = bone.GetParent()
    boneparent_name = boneparent["Name"].asString()
    if boneparent_name != skelroot_name:
        # parent is not the skeleton root
        if not boneparent_name in BONE_LIST[skelroot_name]:
            # neither is it marked as a bone: so mark the parent as a bone
            BONE_LIST[skelroot_name].append(boneparent_name)
            msg("'%s' is a bone of armature '%s'"%(boneparent_name, skelroot_name),3)
        # now the parent is marked as a bone
        # recursion: complete the bone tree,
        # this time starting from the parent bone
        complete_bone_tree(boneparent, skelroot_name)



# merge armatures that are bones of other armatures
def merge_armatures():
    global BONE_LIST
    for arm_name, bones in BONE_LIST.items():
        for arm_name2, bones2 in BONE_LIST.items():
            if arm_name2 in bones and BONE_LIST.has_key(arm_name):
                msg("merging armature '%s' into armature '%s'"%(arm_name2,arm_name),3)
                # arm_name2 is in BONE_LIST[arm_name]
                # so add every bone2 in BONE_LIST[arm_name2] too
                for bone2 in bones2:
                    if not bone2 in bones:
                        BONE_LIST[arm_name].append(bone2)
                # remove merged armature
                del BONE_LIST[arm_name2]



# Tests a NiNode to see if it's a bone.
def is_bone(niBlock):
    if niBlock["Name"].asString()[:6] == "Bip01 ": return True # heuristics
    for bones in BONE_LIST.values():
        if niBlock["Name"].asString() in bones:
            #print "%s is a bone" % niBlock["Name"].asString()
            return True
    #print "%s is not a bone" % niBlock["Name"].asString()
    return False

# Tests a NiNode to see if it's an armature.
def is_armature_root(niBlock):
    return BONE_LIST.has_key(niBlock["Name"].asString())
    
# Detect closest bone ancestor.
def get_closest_bone(niBlock):
    par = niBlock.GetParent()
    while not par.is_null():
        if is_bone(par):
            return par
        par = par.GetParent()
    return par

#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
#-------- Run importer GUI.
#----------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
# global dictionary of GUI elements to keep them allocated
gui_elem={}
def gui_draw():
    global SCALE_CORRECTION, FORCE_DDS, STRIP_TEXPATH, SEAMS_IMPORT, LAST_IMPORTED, TEXTURES_DIR
    
    BGL.glClearColor(0.753, 0.753, 0.753, 0.0)
    BGL.glClear(BGL.GL_COLOR_BUFFER_BIT)

    BGL.glColor3f(0.000, 0.000, 0.000)
    BGL.glRasterPos2i(8, 92)
    gui_elem["label_0"] = Draw.Text('Tex Path:')
    BGL.glRasterPos2i(8, 188)
    gui_elem["label_1"] = Draw.Text('Seams:')

    gui_elem["bt_browse"] = Draw.Button('Browse', 1, 8, 48, 55, 23, '')
    gui_elem["bt_import"] = Draw.Button('Import NIF', 2, 8, 8, 87, 23, '')
    gui_elem["bt_cancel"] = Draw.Button('Cancel', 3, 208, 8, 71, 23, '')
    gui_elem["tg_smooth_0"] = Draw.Toggle('Smoothing Flag (Slow)', 6, 88, 112, 191, 23, SEAMS_IMPORT == 2, 'Import seams and convert them to "the Blender way", is slow and imperfect, unless model was created by Blender and had no duplicate vertices.')
    gui_elem["tg_smooth_1"] = Draw.Toggle('Vertex Duplication (Slow)', 7, 88, 144, 191, 23, SEAMS_IMPORT == 1, 'Perfect but slow, this is the preferred method if the model you are importing is not too large.')
    gui_elem["tg_smooth_2"] = Draw.Toggle('Vertex Duplication (Fast)', 8, 88, 176, 191, 23, SEAMS_IMPORT == 0, 'Fast but imperfect: may introduce unwanted cracks in UV seams')
    gui_elem["tx_texpath"] = Draw.String('', 4, 72, 80, 207, 23, TEXTURES_DIR, 512, 'Semi-colon separated list of texture directories.')
    gui_elem["tx_last"] = Draw.String('', 5, 72, 48, 207, 23, LAST_IMPORTED, 512, '')
    gui_elem["sl_scale"] = Draw.Slider('Scale Correction: ', 9, 8, 208, 271, 23, SCALE_CORRECTION, 0.01, 100, 0, 'How many NIF units is one Blender unit?')

def gui_select(filename):
    global LAST_IMPORTED
    LAST_IMPORTED = filename
    Draw.Redraw(1)
    
def gui_evt_key(evt, val):
    if (evt == Draw.QKEY and not val):
        Draw.Exit()

def gui_evt_button(evt):
    global SEAMS_IMPORT
    global SCALE_CORRECTION, force_dds, strip_texpath, SEAMS_IMPORT, LAST_IMPORTED, TEXTURES_DIR
    
    if evt == 6: #Toggle3
        SEAMS_IMPORT = 2
        Draw.Redraw(1)
    elif evt == 7: #Toggle2
        SEAMS_IMPORT = 1
        Draw.Redraw(1)
    elif evt == 8: #Toggle1
        SEAMS_IMPORT = 0
        Draw.Redraw(1)
    elif evt == 1: # Browse
        Blender.Window.FileSelector(gui_select, 'Select')
        Draw.Redraw(1)
    elif evt == 4: # TexPath
        TEXTURES_DIR = gui_elem["tx_texpath"].val
    elif evt == 5: # filename
        LAST_IMPORTED = gui_elem["tx_last"].val
    elif evt == 9: # scale
        SCALE_CORRECTION = gui_elem["sl_scale"].val
    elif evt == 2: # Import NIF
        # Stop GUI.
        gui_elem = None
        Draw.Exit()
        gui_import()
    elif evt == 3: # Cancel
        gui_elem = None
        Draw.Exit()

def gui_import():
    global SEAMS_IMPORT
    # Save options for next time.
    update_registry()
    # Import file.
    if SEAMS_IMPORT == 2:
        msg("Smoothing import not implemented yet, selecting slow vertex duplication method instead.", 1)
        SEAMS_IMPORT = 1
    import_nif(LAST_IMPORTED)

if USE_GUI:
    Draw.Register(gui_draw, gui_evt_key, gui_evt_button)
else:
    if IMPORT_DIR:
        Blender.Window.FileSelector(import_nif, 'Import NIF', IMPORT_DIR)
    else:
        Blender.Window.FileSelector(import_nif, 'Import NIF')
