#!BPY

""" Registration info for Blender menus:
Name: 'NetImmerse/Gamebryo (.nif & .kf)...'
Blender: 239
Group: 'Export'
Tip: 'Export selected meshes to NIF (.nif) format.'
"""

__author__ = "amorilia@gamebox.net"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__version__ = "1.2"
__bpydoc__ = """\
This script exports selected meshes, along with parents, children, and
armatures, to a .nif file. If animation is present,  X***.NIF and a X***.KF
files are written as well.

Supported:<br>
    Vertex weight skinning.<br>
    Animation of bones, material colors, and transparency.<br>
    Animation groups ("Anim" text buffer).<br>
    Texture flipping (via text buffer named to the texture).

Missing:<br>
    Particle effects, cameras, lights.<br>
    Actions (for animation groups) are ignored. Workaround: define actions in
text buffer called "Anim".<br>
    Texture packing has temporarily been dropped (sorry!), next release
will include it again.

Known issues:<br>
    Ambient and emit colors are obtained by multiplication with the diffuse
color.<br>
    Blender double sided faces will be one sided in the NIF file (workaround:
duplicate faces).<br>
    Direct animation of meshes is buggy unless you parent
without parent inverse (CTRL-SHIFT-P). Workaround: don't animate meshes
directly; instead, parent meshes to bones and animate the bones.

Config options (Scripts->System->Scripts Config Editor->Export):<br>
    force dds: Force textures to be exported with a .DDS extension? Usually,
you can leave this disabled.<br>
    strip texpath: Strip texture path in NIF file? You should leave this
disabled, especially when this model's textures are stored in a subdirectory
of the Data Files\Textures folder.<br>
    scale correction: How many NIF units is one Blender unit?<br>
    nif version: the NIF version to write (EXPERIMENTAL, only 4.0.0.2 has been
tested)<br>
    export dir: default directory to open when script starts
"""

# --------------------------------------------------------------------------
# NIF Export v1.2 by Amorilia ( amorilia@gamebox.net )
# --------------------------------------------------------------------------
# ***** BEGIN BSD LICENSE BLOCK *****
#
# Copyright (c) 2005, NIF File Format Library and Tools
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
# ***** END BSD LICENCE BLOCK *****
# --------------------------------------------------------------------------

import Blender, sys
from Blender import BGL
from Blender import Draw

try:
    from niflib import *
except:
    err = """--------------------------
ERROR\nThis script requires the NIFLIB Python SWIG wrapper, niflib.py & _niflib.dll.
Download it from http://niftools.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|NIFLIB not found, check console for details")
    raise



#
# Global variables.
#

DEBUG = False # set to True for more output when exporting

NIF_BLOCKS = [] # keeps track of all exported blocks
NIF_TEXTURES = {} # keeps track of all exported textures
NIF_MATERIALS = {} # keeps track of all exported materials

NIF_VERSION_DICT = {}
NIF_VERSION_DICT['4.0.0.2']  = 0x04000002
NIF_VERSION_DICT['4.1.0.12'] = 0x0401000C
NIF_VERSION_DICT['4.2.0.2']  = 0x04020002
NIF_VERSION_DICT['4.2.1.0']  = 0x04020100
NIF_VERSION_DICT['4.2.2.0']  = 0x04020200
NIF_VERSION_DICT['10.0.1.0'] = 0x0A000100
NIF_VERSION_DICT['10.1.0.0'] = 0x0A010000
NIF_VERSION_DICT['10.2.0.0'] = 0x0A020000
NIF_VERSION_DICT['20.0.0.4'] = 0x14000004

# configuration default values
EPSILON = 0.005 # used for checking equality with floats, NOT STORED IN CONFIG
SCALE_CORRECTION = 10.0
FORCE_DDS = False
STRIP_TEXPATH = False
EXPORT_DIR = ''
NIF_VERSION_STR = '4.0.0.2'

# tooltips
tooltips = {
    'SCALE_CORRECTION': "How many NIF units is one Blender unit?",
    'FORCE_DDS': "Force textures to be exported with a .DDS extension? Usually, you can leave this disabled.",
    'STRIP_TEXPATH': "Strip texture path in NIF file. You should leave this disabled, especially when this model's textures are stored in a subdirectory of the Data Files\Textures folder.",
    'EXPORT_DIR': "Default export directory.",
    'NIF_VERSION': "The NIF version to write (EXPERIMENTAL, only 4.0.0.2 tested)."
}

# bounds
limits = {
    'SCALE_CORRECTION': [0.01, 100.0]
}



# 
# Process config files.
# 

# update registry
def update_registry():
    # populate a dict with current config values:
    d = {}
    d['SCALE_CORRECTION'] = SCALE_CORRECTION
    d['FORCE_DDS'] = FORCE_DDS
    d['STRIP_TEXPATH'] = STRIP_TEXPATH
    d['EXPORT_DIR'] = EXPORT_DIR
    d['NIF_VERSION'] = NIF_VERSION_STR
    d['tooltips'] = tooltips
    d['limits'] = limits
    # store the key
    Blender.Registry.SetKey('nif_export', d, True)

# Now we check if our key is available in the Registry or file system:
regdict = Blender.Registry.GetKey('nif_export', True)
# If this key already exists, update config variables with its values:
if regdict:
    try:
        SCALE_CORRECTION = regdict['SCALE_CORRECTION']
        FORCE_DDS = regdict['FORCE_DDS']
        STRIP_TEXPATH = regdict['STRIP_TEXPATH']
        EXPORT_DIR = regdict['EXPORT_DIR']
        NIF_VERSION_STR = regdict['NIF_VERSION']
        try:
            NIF_VERSION = NIF_VERSION_DICT[NIF_VERSION_STR]
        except:
            print "Warning: NIF version %s not supported; exporting version 4.0.0.2 instead."%NIF_VERSION_STR
            NIF_VERSION_STR = '4.0.0.2'
            NIF_VERSION = NIF_VERSION_DICT[NIF_VERSION_STR]
            raise # data was corrupted, reraise exception
    # if data was corrupted (or a new version of the script changed
    # (expanded, removed, renamed) the config vars and users may have
    # the old config file around):
    except: update_registry() # rewrite it
else: # if the key doesn't exist yet, use our function to create it:
    update_registry()

VERBOSE = True
CONFIRM_OVERWRITE = True

# check General scripts config key for default behaviors
rd = Blender.Registry.GetKey('General', True)
if rd:
    try:
        VERBOSE = rd['verbose']
        CONFIRM_OVERWRITE = rd['confirm_overwrite']
    except: pass



#
# A simple custom exception class.
#
class NIFExportError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)



#
# Main export function.
#
def export_nif(filename):    
    try: # catch NIFExportErrors
        
        # preparation:
        #--------------
        Blender.Window.DrawProgressBar(0.0, "Preparing Export")
        
        # armatures should not be in rest position
        for ob in Blender.Object.Get():
            if ob.getType() == 'Armature':
                ob.data.restPosition = False # ensure we get the mesh vertices in animation mode, and not in rest position!
                if (ob.data.envelopes):
                    print """'%s': Cannot export envelope skinning.
If you have vertex groups, turn off envelopes.
If you don't have vertex groups, select the bones one by one
press W to convert their envelopes to vertex weights,
and turn off envelopes."%ob.getName())"""%ob.getName()
                    raise NIFExportError("'%s': Cannot export envelope skinning. Check console for instructions."%ob.getName())
        
        # extract some useful scene
        scn = Blender.Scene.GetCurrent()
        context = scn.getRenderingContext()
        fspeed = 1.0 / context.framesPerSec()
        fstart = context.startFrame()
        fend = context.endFrame()
        
        # set everything in the first frame of animation
        context.currentFrame(fstart)
        scn.update(1)
        
        # strip extension from filename
        root_name, fileext = Blender.sys.splitext(Blender.sys.basename(filename))
        
        # get the root object from selected object
        if (Blender.Object.GetSelected() == None):
            raise NIFExportError("Please select the object(s) that you wish to export, and run this script again.")
        root_objects = []
        for root_object in Blender.Object.GetSelected():
            while (root_object.getParent() != None):
                root_object = root_object.getParent()
            if ((root_object.getType() != 'Empty') and (root_object.getType() != 'Mesh') and (root_object.getType() != 'Armature')):
                raise NIFExportError("Root object (%s) must be an 'Empty', 'Mesh', or 'Armature' object."%root_object.getName())
            if (root_objects.count(root_object) == 0): root_objects.append(root_object)

        ## TODO use Blender actions for animation groups
        # check for animation groups definition in a text buffer called 'Anim'
        animtxt = None
        for txt in Blender.Text.Get():
            if txt.getName() == "Anim":
                animtxt = txt
                break
        
        # export nif:
        #------------
        Blender.Window.DrawProgressBar(0.33, "Converting to NIF")
        
        # create a nif object
        
        # export the root node (note that transformation is ignored on the root node)
        root_block = export_node(None, 'none', None, root_name)
        
        # export objects
        if DEBUG: print "Exporting objects"
        for root_object in root_objects:
            # export the root objects as a NiNodes; their children are exported as well
            # note that localspace = worldspace, because root objects have no parents
            export_node(root_object, 'localspace', root_block, root_object.getName())

        # post-processing:
        #-----------------
        
        # if we exported animations, but no animation groups are defined, define a default animation group
        if DEBUG: print "Checking animation groups"
        if (animtxt == None):
            has_controllers = 0
            for block in NIF_BLOCKS:
                if block.IsControllable():
                    if ( not block["Controller"].asLink().is_null() ):
                        has_controllers = 1
                        break
            if has_controllers:
                if DEBUG: print "Defining default animation group"
                # get frame start and frame end
                scn = Blender.Scene.GetCurrent()
                context = scn.getRenderingContext()
                fstart = context.startFrame()
                fend = context.endFrame()
                # write the animation group text buffer
                animtxt = Blender.Text.New("Anim")
                animtxt.write("%i/Idle: Start/Idle: Loop Start\n%i/Idle: Loop Stop/Idle: Stop"%(fstart,fend))

        # animations without keyframe animations crash the TESCS
        # if we are in that situation, add a trivial keyframe animation
        if DEBUG: print "Checking controllers"
        if (animtxt):
            has_keyframecontrollers = 0
            for block in NIF_BLOCKS:
                if block.GetBlockType() == "NiKeyframeController":
                    has_keyframecontrollers = 1
                    break
            if has_keyframecontrollers == 0:
                if DEBUG: print "Defining dummy keyframe controller"
                # add a trivial keyframe controller on the scene root
                export_keyframe(None, 'localspace', root_block)
        
        # export animation groups
        if (animtxt):
            export_animgroups(animtxt, root_block)
            #export_animgroups(animtxt, root_block["Children"].asLinkList()[0]) # we link the animation extra data to the first root_object node

        # scale the NIF model
        scale_tree(root_block, SCALE_CORRECTION)

        # write the file:
        #----------------
        if DEBUG: print "Writing NIF file(s)"
        Blender.Window.DrawProgressBar(0.66, "Writing NIF file(s)")

        # make sure we have the right file extension
        if ((fileext != '.nif') and (fileext != '.NIF')):
            filename += '.nif'
        WriteNifTree(filename, root_block, NIF_VERSION)

        
        
    except NIFExportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Export Failed")
        print 'NIFExportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return

    Blender.Window.DrawProgressBar(1.0, "Finished")
    
    # no export error, but let's double check: try reading the file(s) we just wrote
    # we can probably remove these lines once the exporter is stable
    try:
        ReadNifTree(filename)
    except:
        Blender.Draw.PupMenu("WARNING%t|Exported NIF file may not be valid: double check failed! This is probably due to an unknown bug in the exporter code.")
        raise # re-raise the exception



# 
# Export a mesh/empty object ob as child of parent_block.
# Export also all children of ob.
#
# - space is 'none', 'worldspace', or 'localspace', and determines
#   relative to what object the transformation should be stored.
# - parent_block is the parent nif block of the object (None for the root node)
# - for the root node, ob is None, and node_name is usually the base
#   filename (either with or without extension)
#
def export_node(ob, space, parent_block, node_name):
    if DEBUG: print "Exporting NiNode %s"%node_name
    ipo = None

    # determine the block type, and append a new node to the nif block list
    if (ob == None):
        # -> root node
        assert(space == 'none')
        assert(parent_block == None) # debug
        node = create_block("NiNode")
    else:
        assert((ob.getType() == 'Empty') or (ob.getType() == 'Mesh') or (ob.getType() == 'Armature')) # debug
        assert(parent_block) # debug
        ipo = ob.getIpo() # get animation data
        if (node_name == 'RootCollisionNode'):
            # -> root collision node
            node = create_block("RootCollisionNode")
        else:
            # -> regular node (static or animated object)
            node = create_block("NiNode")
    
    # make it child of its parent in the nif, if it has one
    if (parent_block):
        parent_block["Children"].AddLink(node)
    
    # and fill in this node's non-trivial values
    node["Name"] = node_name
    if (ob == None):
        node["Flags"] = 0x000C # ? this seems pretty standard for the root node
    elif (node_name == 'RootCollisionNode'):
        node["Flags"] = 0x0003 # ? this seems pretty standard for the root collision node
    else:
        node["Flags"] = 0x000C # ? this seems pretty standard for static and animated ninodes

    ob_translation, \
    ob_rotation, \
    ob_scale, \
    ob_velocity \
    = export_matrix(ob, space)
    node["Rotation"]    = ob_rotation
    node["Velocity"]    = ob_velocity
    node["Scale"]       = ob_scale[0]
    node["Translation"] = ob_translation

    # set object bind position, in armature space (this should work)
    if ob != None and ob.getParent() and ob.getParent().getType() == 'Armature':
        if ipo:
            raise NIFExportError('%s: animated meshes parented to armatures are unsupported, animate the armature instead'%ob.getName())
        arm_mat_inv = Blender.Mathutils.Matrix(ob.getParent().getMatrix('worldspace'))
        arm_mat_inv.invert()
        bbind_mat = ob.getMatrix('worldspace') * arm_mat_inv
        bind_mat = Matrix44(
            bbind_mat[0][0], bbind_mat[0][1], bbind_mat[0][2], bbind_mat[0][3],
            bbind_mat[1][0], bbind_mat[1][1], bbind_mat[1][2], bbind_mat[1][3],
            bbind_mat[2][0], bbind_mat[2][1], bbind_mat[2][2], bbind_mat[2][3],
            bbind_mat[3][0], bbind_mat[3][1], bbind_mat[3][2], bbind_mat[3][3])
        inode = QueryNode(node)
        inode.SetBindPosition(bind_mat)

    if (ob != None):
        # export animation
        if (ipo != None):
            export_keyframe(ipo, space, node)
    
        # if it is a mesh, export the mesh as trishape children of this ninode
        if (ob.getType() == 'Mesh'):
            export_trishapes(ob, 'none', node) # the transformation of the mesh is already in the NiNode

        # if it is an armature, export the bones as ninode children of this ninode
        elif (ob.getType() == 'Armature'):
            export_bones(ob, node)

        # export all children of this empty/mesh/armature/bone object as children of this NiNode
        export_children(ob, node)

    return node



#
# Export the animation of blender Ipo as keyframe controller and
# keyframe data. Extra quaternion is multiplied prior to keyframe
# rotation, and dito for translation. These extra fields come in handy
# when exporting bone ipo's, which are relative to the rest pose, so
# we can pass the rest pose through these extra transformations.
#
def export_keyframe(ipo, space, parent_block, extra_trans = None, extra_quat = None):
    if DEBUG: print "Exporting keyframe %s"%parent_block["Name"].asString()
    # -> get keyframe information
    
    assert(space == 'localspace') # we don't support anything else (yet)
    assert(parent_block.GetBlockType() == "NiNode") # make sure the parent is of the right type
    
    # get frame start and frame end, and the number of frames per second
    scn = Blender.Scene.GetCurrent()
    context = scn.getRenderingContext()
 
    fspeed = 1.0 / context.framesPerSec()
    fstart = context.startFrame()
    fend = context.endFrame()

    # sometimes we need to export an empty keyframe... this will take care of that
    if (ipo == None):
        rot_curve = {}
        trans_curve = {}
    # the usual case comes now...
    else:
        # merge the animation curves into a rotation vector and translation vector curve
        rot_curve = {}
        trans_curve = {}
        for curve in ipo.getCurves():
            for btriple in curve.getPoints():
                knot = btriple.getPoints()
                frame = knot[0]
                ftime = (frame - 1) * fspeed
                if (curve.getName() == 'RotX') or (curve.getName() == 'RotY') or (curve.getName() == 'RotZ'):
                    rot_curve[ftime] = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toQuat()
                    if extra_quat: # extra quaternion rotation
                        rot_curve[ftime] = Blender.Mathutils.CrossQuats(rot_curve[ftime], extra_quat)
                elif (curve.getName() == 'QuatX') or (curve.getName() == 'QuatY') or (curve.getName() == 'QuatZ') or  (curve.getName() == 'QuatW'):
                    rot_curve[ftime] = Blender.Mathutils.Quaternion()
                    rot_curve[ftime].x = ipo.getCurve('QuatX').evaluate(frame)
                    rot_curve[ftime].y = ipo.getCurve('QuatY').evaluate(frame)
                    rot_curve[ftime].z = ipo.getCurve('QuatZ').evaluate(frame)
                    rot_curve[ftime].w = ipo.getCurve('QuatW').evaluate(frame)
                    if extra_quat: # extra quaternion rotation
                        rot_curve[ftime] = Blender.Mathutils.CrossQuats(rot_curve[ftime], extra_quat)
                if (curve.getName() == 'LocX') or (curve.getName() == 'LocY') or (curve.getName() == 'LocZ'):
                    trans_curve[ftime] = Vector3()
                    trans_curve[ftime].x = ipo.getCurve('LocX').evaluate(frame)
                    trans_curve[ftime].y = ipo.getCurve('LocY').evaluate(frame)
                    trans_curve[ftime].z = ipo.getCurve('LocZ').evaluate(frame)
                    if extra_trans: # extra translation
                        trans_curve[ftime].x += extra_trans[0]
                        trans_curve[ftime].y += extra_trans[1]
                        trans_curve[ftime].z += extra_trans[2]

    # -> now comes the real export

    # add a keyframecontroller block, and refer to this block in the parent's time controller
    kfc = create_block("NiKeyframeController")
    add_controller(parent_block, kfc)

    # fill in the non-trivial values
    kfc["Flags"] = 0x0008
    kfc["Frequency"] = 1.0
    kfc["Phase"] = 0.0
    kfc["Start Time"] = (fstart - 1) * fspeed
    kfc["Stop Time"] = (fend - fstart) * fspeed

    # add the keyframe data
    kfd = create_block("NiKeyframeData")
    kfc["Data"] = kfd

    ikfd = QueryKeyframeData(kfd)
    ikfd.SetRotateType(LINEAR_KEY)
    ftimes = rot_curve.keys()
    ftimes.sort()
    rot_keys = []
    for ftime in ftimes:
        rot_frame = Key_Quaternion()
        rot_frame.time = ftime
        rot_frame.data.w = rot_curve[ftime].w
        rot_frame.data.x = rot_curve[ftime].x
        rot_frame.data.y = rot_curve[ftime].y
        rot_frame.data.z = rot_curve[ftime].z
        rot_keys.append(rot_frame)
    ikfd.SetRotateKeys(rot_keys)

    ikfd.SetTranslateType(LINEAR_KEY)
    ftimes = trans_curve.keys()
    ftimes.sort()
    trans_keys = []
    for ftime in ftimes:
        trans_frame = Key_Vector3()
        trans_frame.time = ftime
        trans_frame.data.x = trans_curve[ftime].x
        trans_frame.data.y = trans_curve[ftime].y
        trans_frame.data.z = trans_curve[ftime].z
        trans_keys.append(trans_frame)
    ikfd.SetTranslateKeys(trans_keys)



def export_vcolprop(vertex_mode, lighting_mode):
    if DEBUG: print "Exporting NiVertexColorProperty"
    # create new vertex color property block
    vcolprop = create_block("NiVertexColorProperty")
    
    # make it a property of the root node
    NIF_BLOCKS[0]["Children"].AddLink(vcolprop)

    # and now export the parameters
    vcolprop["Vertex Mode"] = vertex_mode
    vcolprop["Lighting Mode"] = lighting_mode



#
# parse the animation groups buffer and write an extra string data block,
# parented to the root block
#
def export_animgroups(animtxt, block_parent):
    if DEBUG: print "Exporting animation groups"
    # -> get animation groups information

    # get frame start and frame end, and the number of frames per second
    scn = Blender.Scene.GetCurrent()
    context = scn.getRenderingContext()
 
    fspeed = 1.0 / context.framesPerSec()
    fstart = context.startFrame()
    fend = context.endFrame()

    # parse the anim text descriptor
    
    # the format is:
    # frame/string1[/string2[.../stringN]]
    
    # example:
    # 001/Idle: Start/Idle: Stop/Idle2: Start/Idle2: Loop Start
    # 051/Idle2: Stop/Idle3: Start
    # 101/Idle3: Loop Start/Idle3: Stop

    slist = animtxt.asLines()
    flist = []
    dlist = []
    for s in slist:
        if ( s == '' ): continue # ignore empty lines
        t = s.split('/')
        if (len(t) < 2): raise NIFExportError("Syntax error in Anim buffer ('%s')"%s)
        f = int(t[0])
        if ((f < fstart) or (f > fend)): raise NIFExportError("Error in Anim buffer: frame out of range (%i not in [%i, %i])"%(f, fstart, fend))
        d = t[1].strip(' ')
        for i in range(2, len(t)):
            d = d + '\r\n' + t[i].strip(' ')
        #print 'frame %d'%f + ' -> \'%s\''%d # debug
        flist.append(f)
        dlist.append(d)
    
    # -> now comes the real export
    
    # add a NiTextKeyExtraData block, and refer to this block in the
    # parent node (we choose the root block)
    textextra = create_block("NiTextKeyExtraData")
    add_extra_data(block_parent, textextra)
    
    # create a NiTextKey for each frame descriptor
    keys = []
    for i in range(len(flist)):
        key = Key_string()
        key.time = fspeed * (flist[i]-1);
        key.data = dlist[i];
        keys.append(key)
    itextextra = QueryTextKeyExtraData(textextra)
    itextextra.SetKeys(keys)



#
# export a NiSourceTexture
#
# texture is the texture object in blender to be exported
# filename is the full or relative path to the texture file ( used by NiFlipController )
#
# Returns block of the exported NiSourceTexture
#
# TODO: packed textures
# 
def export_sourcetexture(texture, filename = None):
    global NIF_TEXTURES
    
    if DEBUG: print "Exporting source texture %s"%texture.getName()
    # texture must be of type IMAGE
    if ( texture.type != Blender.Texture.Types.IMAGE ):
        raise NIFExportError( "Error: Texture '%s' must be of type IMAGE"%texture.getName())
    
    # check if the texture is already exported
    if filename != None:
        texid = filename
    else:
        texid = texture.image.getFilename()
    if NIF_TEXTURES.has_key(texid):
        return NIF_TEXTURES[texid]

    # add NiSourceTexture
    srctex = create_block("NiSourceTexture")
    srctexdata = TextureSource()
    srctexdata.useExternal = ( texture.getName()[:4] != "pack" )
    
    # TODO port this code
    if not srctexdata.useExternal:
        raise NIFExportError("Packed textures not yet supported.")
##        if filename != None:
##            try:
##                image = Blender.Image.Load( filename )
##            except:
##                raise NIFExportError( "Error: Cannot pack texture '%s'; Failed to load image '%s'"%(texture.getName(),filename) )
##        else:
##            image = texture.image
##        w, h = image.getSize()
##        if ( w <= 0 ) or ( h <= 0 ):
##            image.reload()
##        if ( w <= 0 ) or ( h <= 0 ):
##            raise NIFExportError( "Error: Cannot pack texture '%s'; Failed to load image '%s'"%(texture.getName(),image.getFilename()) )
##        depth = image.getDepth()
##        if depth == 32:
##            rmask = 0x000000ff
##            gmask = 0x0000ff00
##            bmask = 0x00ff0000
##            amask = 0xff000000
##            bytes = 4
##        elif depth == 24:
##            rmask = 0x000000ff
##            gmask = 0x0000ff00
##            bmask = 0x00ff0000
##            amask = 0x00000000
##            bytes = 3
##        else:
##            raise NIFExportError( "Error: Cannot pack texture '%s' image '%s'; Unsupported image depth %i"%(texture.getName(),image.getFilename(),image.getDepth()) )
##
##        # now pack the image
##        data = []
##        mipmaps = []
##        if VERBOSE: print "packing %s -> width %i, height %i"%(Blender.sys.basename(image.getFilename()),w,h)
##        mipmaps.append( [ w, h, 0 ] )
##        for y in range( h ):
##            for x in range( w ):
##                r,g,b,a = image.getPixelF( x, (h-1)-y ) # nif flips y coordinate
##                if ( depth == 32 ):
##                    data.append( int( r * 255 ) )
##                    data.append( int( g * 255 ) )
##                    data.append( int( b * 255 ) )
##                    data.append( int( a * 255 ) )
##                elif ( depth == 24 ):
##                    data.append( int( r * 255 ) )
##                    data.append( int( g * 255 ) )
##                    data.append( int( b * 255 ) )
##
##        # filter mipmaps
##        sx = 2
##        sy = 2
##        lastOffset = 0
##        while ( texture.imageFlags & Blender.Texture.ImageFlags.MIPMAP != 0 ):
##            offset = len(data)
##            if VERBOSE: print "packing %s mipmap %i -> width %i, height %i, offset %i"%(Blender.sys.basename(image.getFilename()),len(mipmaps),w/sx,h/sy,offset)
##            mipmaps.append( [ w/sx, h/sy, offset ] )
##            for y in range( 0, h, sy ):
##                for x in range( 0, w, sx ):
##                    rgba = [ 0, 0, 0, 0 ]
##                    for fy in range( 2 ):
##                        for fx in range( 2 ):
##                            for fd in range( bytes ):
##                                rgba[fd] += data[lastOffset+((y/sy*2+fy)*w/sx*2+(x/sx*2+fx))*bytes+fd]
##                    for fd in range( bytes ):
##                        rgba[fd] = rgba[fd] / 4
##                        data.append( rgba[fd] )
##            lastOffset = offset
##            if ( sx == w ) and ( sy == h ):
##                break # now more mipmap levels left
##            if ( sx < w ):
##                sx = sx * 2
##            if ( sy < h ):
##                sy = sy * 2
##            if ( sx > w ) or ( sy > h ):
##                raise NIFExportError( "Error: Cannot pack texture '%s' image '%s'; Image dimensions must be power of two"%(texture.getName(),image.getFilename()) )
##        
##        # add NiPixelData
##        pixel_id = nif.header.nblocks
##        assert(pixel_id == len(nif.blocks)) # debug
##        nif.blocks.append(nif4.NiPixelData())
##        nif.header.nblocks += 1
##        nif.blocks[pixel_id].rmask = rmask
##        nif.blocks[pixel_id].gmask = gmask
##        nif.blocks[pixel_id].bmask = bmask
##        nif.blocks[pixel_id].amask = amask
##        nif.blocks[pixel_id].bpp = depth
##        nif.blocks[pixel_id].bytespp = nif.blocks[pixel_id].bpp / 8
##        nif.blocks[pixel_id].mipmaps = mipmaps
##        nif.blocks[pixel_id].num_mipmaps = len( nif.blocks[pixel_id].mipmaps )
##        nif.blocks[pixel_id].data = data
##        nif.blocks[pixel_id].data_size = len(nif.blocks[pixel_id].data)
##        if ( depth == 24 ):
##            nif.blocks[pixel_id].unknown2 = [ 96, 8, 130, 0, 0, 65, 0, 0 ] # ?? copy values from original files
##        elif ( depth == 32 ):
##            nif.blocks[pixel_id].unknown2 = [ 129, 8, 130, 32, 0, 65, 12, 0 ]
##        nif.blocks[tsrc_id].pixel_data = pixel_id
##        nif.blocks[tsrc_id].unknown1 = 1
    # if the file is external
    else:
        if filename != None:
            tfn = filename
        else:
            tfn = texture.image.getFilename()
        if ( STRIP_TEXPATH == 1 ):
            # strip texture file path (original morrowind style)
            srctexdata.fileName = Blender.sys.basename(tfn)
        elif ( STRIP_TEXPATH == 0 ):
            # strip the data files prefix from the texture's file name
            tfn = tfn.lower()
            idx = tfn.find( "textures" )
            if ( idx >= 0 ):
                tfn = tfn[idx:]
                tfn = tfn.replace(Blender.sys.sep, '\\') # for my linux fellows
                srctexdata.fileName = tfn
            else:
                srctexdata.fileName = Blender.sys.basename(tfn)
        # force dds extension, if requested
        if FORCE_DDS:
            srctexdata.fileName = srctexdata.fileName[:-4] + '.dds'

    # fill in default values
    srctex["Texture Source"] = srctexdata
    srctex["Pixel Layout"] = 5
    srctex["Use Mipmaps"]  = 2
    srctex["Alpha Format"] = 3
    srctex["Unknown Byte"] = 1

    # save for future reference
    NIF_TEXTURES[texid] = srctex
    
    return srctex



## TODO port code to use native Blender texture flipping system
#
# export a NiFlipController
#
# fliptxt is a blender text object containing the flip definitions
# texture is the texture object in blender ( texture is used to checked for pack and mipmap flags )
# target is the NiTexturingProperty
# target_tex is the texture to flip ( 0 = base texture, 4 = glow texture )
#
# returns exported NiFlipController
# 
def export_flipcontroller( fliptxt, texture, target, target_tex ):
    if DEBUG: print "Exporting NiFlipController for texture %s"%texture.getName()
    tlist = fliptxt.asLines()

    # create a NiFlipController
    flip = create_block("NiFlipController")
    add_controller(target, flip)

    # get frame start and frame end, and the number of frames per second
    fspeed = 1.0 / Blender.Scene.GetCurrent().getRenderingContext().framesPerSec()
    fstart = Blender.Scene.GetCurrent().getRenderingContext().startFrame()
    fend = Blender.Scene.GetCurrent().getRenderingContext().endFrame()

    # fill in NiFlipController's values
    # flip["Target"] automatically calculated
    flip["Flags"] = 0x0008
    flip["Frequency"] = 1.0
    flip["Start Time"] = (fstart - 1) * fspeed
    flip["Stop Time"] = ( fend - fstart ) * fspeed
    flip["Unknown Int 1"] = target_tex
    count = 0
    for t in tlist:
        if len( t ) == 0: continue  # skip empty lines
        # create a NiSourceTexture for each flip
        tex = export_sourcetexture(texture, t)
        flip["Sources"].AddLink(tex)
        count += 1
    if count < 2:
        raise NIFExportError("Error in Texture Flip buffer '%s': Must define at least two textures"%fliptxt.getName())
    flip["Delta"] = (flip["Stop Time"].asFloat() - flip["Start Time"].asFloat()) / count



#
# Export a blender object ob of the type mesh, child of nif block
# parent_block, as NiTriShape and NiTriShapeData blocks, possibly
# along with some NiTexturingProperty, NiSourceTexture,
# NiMaterialProperty, and NiAlphaProperty blocks. We export one
# trishape block per mesh material. We also export vertex weights.
# 
def export_trishapes(ob, space, parent_block):
    if DEBUG: print "Exporting NiTriShapes for %s"%ob.getName()
    assert(ob.getType() == 'Mesh')

    # get mesh from ob
    mesh_orig = Blender.NMesh.GetRaw(ob.data.name) # original non-subsurfed mesh
    
    # get the mesh's materials, this updates the mesh material list
    mesh_mats = mesh_orig.getMaterials(1) # the argument guarantees that the material list agrees with the face material indices
    # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
    if (mesh_mats == []):
        mesh_mats = [ None ]

    # get subsurfed mesh, we cannot update the mesh after calling this function
    try:
        mesh = Blender.NMesh.GetRawFromObject(ob.name) # subsurf
    except:
        mesh = mesh_orig
    
    # let's now export one trishape for every mesh material
    
    materialIndex = 0 # material index of the current mesh material
    for mesh_mat in mesh_mats:
        # -> first, extract valuable info from our ob
        
        mesh_base_tex = None
        mesh_glow_tex = None
        mesh_hasalpha = 0 # non-zero if we have alpha properties
        mesh_hastex = 0 # non-zero if we have at least one texture
        mesh_hasvcol = 0
        mesh_hasnormals = 0
        if (mesh_mat != None):
            mesh_hasnormals = 1 # for proper lighting
            # for non-textured materials, vertex colors are used to color the mesh
            # for textured materials, they represent lighting details
            mesh_hasvcol = mesh.hasVertexColours() and ((mesh_mat.mode & Blender.Material.Modes.VCOL_LIGHT != 0) or (mesh_mat.mode & Blender.Material.Modes.VCOL_PAINT != 0))
            # read the Blender Python API documentation to understand this hack
            mesh_mat_ambient = mesh_mat.getAmb()            # 'Amb' scrollbar in blender (MW -> 1.0 1.0 1.0)
            mesh_mat_diffuse_color = mesh_mat.getRGBCol()   # 'Col' colour in Blender (MW -> 1.0 1.0 1.0)
            mesh_mat_specular_color = mesh_mat.getSpecCol() # 'Spe' colour in Blender (MW -> 0.0 0.0 0.0)
            mesh_mat_emissive = mesh_mat.getEmit()          # 'Emit' scrollbar in Blender (MW -> 0.0 0.0 0.0)
            mesh_mat_glossiness = mesh_mat.getSpec() / 2.0  # 'Spec' scrollbar in Blender, takes values between 0.0 and 2.0 (MW -> 0.0)
            mesh_mat_transparency = mesh_mat.getAlpha()     # 'A(lpha)' scrollbar in Blender (MW -> 1.0)
            mesh_hasalpha = (abs(mesh_mat_transparency - 1.0) > EPSILON) \
                            or (mesh_mat.getIpo() != None and mesh_mat.getIpo().getCurve('Alpha'))
            mesh_mat_ambient_color = [0.0,0.0,0.0]
            mesh_mat_ambient_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_ambient
            mesh_mat_ambient_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_ambient
            mesh_mat_ambient_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_ambient
            mesh_mat_emissive_color = [0.0,0.0,0.0]
            mesh_mat_emissive_color[0] = mesh_mat_diffuse_color[0] * mesh_mat_emissive
            mesh_mat_emissive_color[1] = mesh_mat_diffuse_color[1] * mesh_mat_emissive
            mesh_mat_emissive_color[2] = mesh_mat_diffuse_color[2] * mesh_mat_emissive
            # the base texture = first material texture
            # note that most morrowind files only have a base texture, so let's for now only support single textured materials
            for mtex in mesh_mat.getTextures():
                if (mtex != None):
                    if (mtex.texco != Blender.Texture.TexCo.UV):
                        # nif only support UV-mapped textures
                        raise NIFExportError("Non-UV texture in mesh '%s', material '%s'. Either delete all non-UV textures, or in the Shading Panel, under Material Buttons, set texture 'Map Input' to 'UV'."%(ob.getName(),mesh_mat.getName()))
                    if ((mtex.mapto & Blender.Texture.MapTo.COL) == 0):
                        # it should map to colour
                        raise NIFExportError("Non-COL-mapped texture in mesh '%s', material '%s', these cannot be exported to NIF. Either delete all non-COL-mapped textures, or in the Shading Panel, under Material Buttons, set texture 'Map To' to 'COL'."%(ob.getName(),mesh_mat.getName()))
                    if ((mtex.mapto & Blender.Texture.MapTo.EMIT) == 0):
                        if (mesh_base_tex == None):
                            # got the base texture
                            mesh_base_tex = mtex.tex
                            mesh_hastex = 1 # flag that we have textures, and that we should export UV coordinates
                            # check if alpha channel is enabled for this texture
                            if (mesh_base_tex.imageFlags & Blender.Texture.ImageFlags.USEALPHA != 0) and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                # in this case, Blender replaces the texture transparant parts with the underlying material color...
                                # in NIF, material alpha is multiplied with texture alpha channel...
                                # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                                # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                                # but...
                                if (mesh_mat_transparency > EPSILON):
                                    raise NIFExportError("Cannot export this type of transparency in material '%s': set alpha to 0.0, or turn off MapTo.ALPHA, and try again."%mesh_mat.getName())
                                if (mesh_mat.getIpo() and mesh_mat.getIpo().getCurve('Alpha')):
                                    raise NIFExportError("Cannot export animation for this type of transparency in material '%s': remove alpha animation, or turn off MapTo.ALPHA, and try again."%mesh_mat.getName())
                                mesh_mat_transparency = 1.0 # aargh! we should use the "Var" value, but we cannot yet access the texture blending properties in this version of Blender... we set it to 1.0
                                mesh_hasalpha = 1
                        else:
                            raise NIFExportError("Multiple base textures in mesh '%s', material '%s', this is not supported. Delete all textures, except for the base texture."%(mesh.name,mesh_mat.getName()))
                    else:
                        # MapTo EMIT is checked -> glow map
                        if ( mesh_glow_tex == None ):
                            # got the glow tex
                            mesh_glow_tex = mtex.tex
                            mesh_hastex = 1
                        else:
                            raise NIFExportError("Multiple glow textures in mesh '%s', material '%s'. Make sure there is only one texture with MapTo.EMIT"%(mesh.name,mesh_mat.getName()))

        # -> now comes the real export
        
        # note: we can be in any of the following five situations
        # material + base texture        -> normal object
        # material + base tex + glow tex -> normal glow mapped object
        # material + glow texture        -> (needs to be tested)
        # material, but no texture       -> uniformly coloured object
        # no material                    -> typically, collision mesh

        # add a trishape block, and refer to this block in the parent's children list
        trishape = create_block("NiTriShape")
        parent_block["Children"].AddLink(trishape)
        
        # fill in the NiTriShape's non-trivial values
        if (parent_block["Name"].asString() != ""):
            trishape["Name"] = "Tri " + parent_block["Name"].asString() + " %i"%materialIndex # Morrowind's child naming convention
        trishape["Flags"] = 0x0004 # ? this seems standard
        ob_translation, \
        ob_rotation, \
        ob_scale, \
        ob_velocity \
        = export_matrix(ob, space)
        trishape["Translation"] = ob_translation
        trishape["Rotation"]    = ob_rotation
        trishape["Scale"]       = ob_scale[0]
        trishape["Velocity"]    = ob_velocity
        
        # set trishape bind position, in armature space (this should work)
        if ob != None and ob.getParent() and ob.getParent().getType() == 'Armature':
            if ob.getIpo():
                raise NIFExportError('%s: animated meshes parented to armatures are unsupported, animate the armature instead'%ob.getName())
            arm_mat_inv = Blender.Mathutils.Matrix(ob.getParent().getMatrix('worldspace'))
            arm_mat_inv.invert()
            bbind_mat = ob.getMatrix('worldspace') * arm_mat_inv # if ob has no ipo, then this is effectively relative to the rest matrix
            bind_mat = Matrix44(
                bbind_mat[0][0], bbind_mat[0][1], bbind_mat[0][2], bbind_mat[0][3],
                bbind_mat[1][0], bbind_mat[1][1], bbind_mat[1][2], bbind_mat[1][3],
                bbind_mat[2][0], bbind_mat[2][1], bbind_mat[2][2], bbind_mat[2][3],
                bbind_mat[3][0], bbind_mat[3][1], bbind_mat[3][2], bbind_mat[3][3])
            inode = QueryNode(trishape)
            inode.SetBindPosition(bind_mat)

        if (mesh_base_tex != None or mesh_glow_tex != None):
            # add NiTriShape's texturing property
            tritexprop = create_block("NiTexturingProperty")
            trishape["Properties"].AddLink(tritexprop)
            
            tritexprop["Flags"] = 0x0001 # standard?
            tritexprop["Apply Mode"] = 2 # modulate?
            tritexprop["Texture Count?"] = 7 # standard?

            if ( mesh_base_tex != None ):
                basetex = Texture()
                basetex.isUsed = 1
                tritexprop["Base Texture"] = basetex
                
                # check for texture flip definition
                txtlist = Blender.Text.Get()
                for fliptxt in txtlist:
                    if fliptxt.getName() == mesh_base_tex.getName():
                        export_flipcontroller( fliptxt, mesh_base_tex, tritexprop, 0 )
                        break
                    else:
                        fliptxt = None
                else:
                    basetexsrc = export_sourcetexture(mesh_base_tex)
                    tritexprop["Base Texture"] = basetexsrc # isn't this confusing?

            if ( mesh_glow_tex != None ):
                glowtex = Texture()
                glowtex.isUsed = 1
                tritexprop["Glow Texture"] = glowtex

                # check for texture flip definition
                txtlist = Blender.Text.Get()
                for fliptxt in txtlist:
                    if fliptxt.getName() == mesh_glow_tex.getName():
                        export_flipcontroller( fliptxt, mesh_glow_tex, tritexprop, 4 )
                        break
                    else:
                        fliptxt = None
                else:
                    glowtexsrc = export_sourcetexture(mesh_glow_tex)
                    tritexprop["Glow Texture"] = glowtexsrc # ...
        
        if (mesh_hasalpha):
            # add NiTriShape's alpha propery (this is de facto an automated version of Detritus's method, see http://detritus.silgrad.com/alphahex.html)
            trialphaprop = create_block("NiAlphaProperty")
            trialphaprop["Flags"] = 0x00ED
            
            # refer to the alpha property in the trishape block
            trishape["Properties"].AddLink(trialphaprop)

        if (mesh_mat != None):
            # add NiTriShape's specular property
            if ( mesh_mat_glossiness > EPSILON ):
                trispecprop = create_block("NiSpecularProperty")
                trispecprop["Flags"] = 0x0001
            
                # refer to the specular property in the trishape block
                trishape["Properties"].AddLink(trispecprop)
            
            # add NiTriShape's material property
            trimatprop = create_block("NiMaterialProperty")
            
            trimatprop["Name"] = mesh_mat.getName()
            trimatprop["Flags"] = 0x0001 # ? standard
            trimatprop["Ambient Color"] = Float3(*mesh_mat_ambient_color)
            trimatprop["Diffuse Color"] = Float3(*mesh_mat_diffuse_color)
            trimatprop["Specular Color"] = Float3(*mesh_mat_specular_color)
            trimatprop["Emissive Color"] = Float3(*mesh_mat_emissive_color)
            trimatprop["Glossiness"] = mesh_mat_glossiness
            trimatprop["Alpha"] = mesh_mat_transparency
            
            # refer to the material property in the trishape block
            trishape["Properties"].AddLink(trimatprop)

        

            # material animation
            ipo = mesh_mat.getIpo()
            a_curve = None
            if ( ipo != None ):
                a_curve = ipo.getCurve( 'Alpha' )
                # get frame start and the number of frames per second
                scn = Blender.Scene.GetCurrent()
                context = scn.getRenderingContext()
                fspeed = 1.0 / context.framesPerSec()
                fstart = context.startFrame()
                fend = context.endFrame()
            
            if ( a_curve != None ):
                # get the alpha keyframes from blender's ipo curve
                alpha = {}
                for btriple in a_curve.getPoints():
                    knot = btriple.getPoints()
                    frame = knot[0]
                    ftime = (frame - fstart) * fspeed
                    alpha[ftime] = ipo.getCurve( 'Alpha' ).evaluate(frame)

                ftimes = alpha.keys()
                ftimes.sort()
                assert( ( ftimes ) > 0 )

                # add a alphacontroller block, and refer to this in the parent material
                alphac = create_block("NiAlphaController")
                assert(trimatprop["Controller"].asLink().is_null()) # make sure we don't overwrite anything
                trimatprop["Controller"] = alphac

                # select extrapolation mode
                if ( a_curve.getExtrapolation() == "Cyclic" ):
                    alphac["Flags"] = 0x0008
                elif ( a_curve.getExtrapolation() == "Constant" ):
                    alphac["Flags"] = 0x000c
                else:
                    if VERBOSE: print "extrapolation \"%s\" for alpha curve not supported using \"cycle reverse\" instead"%a_curve.getExtrapolation()
                    alphac["Flags"] = 0x000a

                # fill in timing values
                alphac["Frequency"] = 1.0
                alphac["Phase"] = 0.0
                alphac["Start Time"] = (fstart - 1) * fspeed
                alphac["Stop Time"]  = (fend - fstart) * fspeed

                # add the alpha data
                alphad = create_block("NiFloatData")
                alphac["Data"] = alphad

                # select interpolation mode and export the alpha curve data
                ialphad = QueryFloatData(alphad)
                if ( a_curve.getInterpolation() == "Linear" ):
                    ialphad.SetKeyType(LINEAR_KEY)
                elif ( a_curve.getInterpolation() == "Bezier" ):
                    ialphad.SetKeyType(QUADRATIC_KEY)
                else:
                    raise NIFExportError( 'interpolation %s for alpha curve not supported use linear or bezier instead'%a_curve.getInterpolation() )

                a_keys = []
                for ftime in ftimes:
                    a_frame = Key_float()
                    a_frame.time = ftime
                    a_frame.data = alpha[ftime]
                    a_frame.forward_tangent = 0.0 # ?
                    a_frame.backward_tangent = 0.0 # ?
                    a_keys.append(a_frame)
                ialphad.SetKeys(a_keys)

            # export animated material colors
            if ( ipo != None and ( ipo.getCurve( 'R' ) != None or ipo.getCurve( 'G' ) != None or ipo.getCurve( 'B' ) != None ) ):
                # merge r, g, b curves into one rgba curve
                rgba_curve = {}
                for curve in ipo.getCurves():
                    for btriple in curve.getPoints():
                        knot = btriple.getPoints()
                        frame = knot[0]
                        ftime = (frame - fstart) * fspeed
                        if (curve.getName() == 'R') or (curve.getName() == 'G') or (curve.getName() == 'B'):
                            rgba_curve[ftime] = nif4.NiRGBA()
                            if ( ipo.getCurve( 'R' ) != None):
                                rgba_curve[ftime].r = ipo.getCurve('R').evaluate(frame)
                            else:
                                rgba_curve[ftime].r = mesh_mat_diffuse_colour[0]
                            if ( ipo.getCurve( 'G' ) != None):
                                rgba_curve[ftime].g = ipo.getCurve('G').evaluate(frame)
                            else:
                                rgba_curve[ftime].g = mesh_mat_diffuse_colour[1]
                            if ( ipo.getCurve( 'B' ) != None):
                                rgba_curve[ftime].b = ipo.getCurve('B').evaluate(frame)
                            else:
                                rgba_curve[ftime].b = mesh_mat_diffuse_colour[2]
                            rgba_curve[ftime].a = mesh_mat_transparency # alpha ignored?

                ftimes = rgba_curve.keys()
                ftimes.sort()
                assert( len( ftimes ) > 0 )

                # add a materialcolorcontroller block
                matcolc = create_block("NiMaterialColorController")
                set_controller(trimatprop, matcolc)

                # fill in the non-trivial values
                matcolc["Flags"] = 0x0008 # using cycle loop for now
                matcolc["Frequency"] = 1.0
                matcolc["Phase"] = 0.0
                matcolc["Start Time"] =  (fstart - 1) * fspeed
                matcolc["Stop Time"] = (fend - fstart) * fspeed

                # add the material color data
                matcold = create_block("NiColorData")
                matcolc["Data"] = matcold

                # export the resulting rgba curve
                imatcold = QueryColorData(matcold)
                rgba_keys = []
                for ftime in ftimes:
                    rgba_frame = Key_Color()
                    rgba_frame.time = ftime
                    rgba_frame.data.r = rgba_curve[ftime][0]
                    rgba_frame.data.g = rgba_curve[ftime][1]
                    rgba_frame.data.b = rgba_curve[ftime][2]
                    rgba_frame.data.a = rgba_curve[ftime][3]
                    rgba_keys.append(rgba_frame)
                imatcold.SetKeys(rgba_keys)

        # add NiTriShape's data
        tridata = create_block("NiTriShapeData")
        trishape["Data"] = tridata
        ishapedata = QueryShapeData(tridata)
        itridata = QueryTriShapeData(tridata)
        
        # Blender only supports one set of uv coordinates per mesh;
        # therefore, we shall have trouble when importing
        # multi-textured trishapes in blender. For this export script,
        # no problem: we must simply duplicate the uv vertex list.

        # We now extract vertices, uv-vertices, normals, and vertex
        # colors from the mesh's face list. NIF has one uv vertex and
        # one normal per vertex, unlike blender's uv vertices and
        # normals per face... therefore some vertices must be
        # duplicated. The following algorithm extracts all unique
        # (vert, uv-vert, normal, vcol) quads, and uses this list to
        # produce the list of vertices, uv-vertices, normals, vertex
        # colors, and face indices.

        # NIF uses the normal table for lighting. So, smooth faces
        # should use Blender's vertex normals, and solid faces should
        # use Blender's face normals.
        
        vertquad_list = [] # (vertex, uv coordinate, normal, vertex color) list
        vertmap = [ None ] * len( mesh.verts ) # blender vertex -> nif vertices
            # this map will speed up the exporter to a great degree (may be useful too when exporting NiMorphData)
        vertlist = []
        normlist = []
        vcollist = []
        uvlist = []
        trilist = []
        count = 0
        for f in mesh.faces:
            #slows down too myuch #if VERBOSE: Blender.Window.DrawProgressBar(0.33 * float(count)/len(mesh.faces), "Converting to NIF (%s)"%ob.getName())
            count += 1
            # does the face belong to this trishape?
            if (mesh_mat != None): # we have a material
                if (f.materialIndex != materialIndex): # but this face has another material
                    continue # so skip this face
            f_numverts = len(f.v)
            if (f_numverts < 3): continue # ignore degenerate faces
            assert((f_numverts == 3) or (f_numverts == 4)) # debug
            if (mesh_hastex): # if we have uv coordinates
                if (len(f.uv) != len(f.v)): # make sure we have UV data
                    raise NIFExportError('ERROR%t|Create a UV map for every texture, and run the script again.')
            # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
            f_index = [ -1 ] * f_numverts
            for i in range(f_numverts):
                fv = Vector3(*(f.v[i].co))
                # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                if mesh_hasnormals:
                    if f.smooth:
                        fn = Vector3(*(f.v[i].no))
                    else:
                        fn = Vector3(*(f.no))
                else:
                    fn = None
                if (mesh_hastex):
                    fuv = TexCoord(*(f.uv[i]))
                    fuv.v = 1.0 - fuv.v # NIF flips the texture V-coordinate (OpenGL standard)
                else:
                    fuv = None
                if (mesh_hasvcol):
                    fcol = Color(0.0,0.0,0.0,0.0)
                    fcol.r = f.col[i].r / 255.0 # NIF stores the colour values as floats
                    fcol.g = f.col[i].g / 255.0 # NIF stores the colour values as floats
                    fcol.b = f.col[i].b / 255.0 # NIF stores the colour values as floats
                    fcol.a = f.col[i].a / 255.0 # NIF stores the colour values as floats
                else:
                    fcol = None
                    
                vertquad = ( fv, fuv, fn, fcol )

                # do we already have this quad? (optimized by m4444x)
                f_index[i] = len(vertquad_list)
                v_index = f.v[i].index
                if vertmap[v_index]:
                    # iterate only over vertices with the same vertex index
                    # and check if they have the same uvs, normals and colors (wow is that fast!)
                    for j in vertmap[v_index]:
                        if mesh_hastex:
                            if abs(vertquad[1].u - vertquad_list[j][1].u) > EPSILON: continue
                            if abs(vertquad[1].v - vertquad_list[j][1].v) > EPSILON: continue
                        if mesh_hasnormals:
                            if abs(vertquad[2].x - vertquad_list[j][2].x) > EPSILON: continue
                            if abs(vertquad[2].y - vertquad_list[j][2].y) > EPSILON: continue
                            if abs(vertquad[2].z - vertquad_list[j][2].z) > EPSILON: continue
                        if mesh_hasvcol:
                            if abs(vertquad[3].r - vertquad_list[j][3].r) > EPSILON: continue
                            if abs(vertquad[3].g - vertquad_list[j][3].g) > EPSILON: continue
                            if abs(vertquad[3].b - vertquad_list[j][3].b) > EPSILON: continue
                            if abs(vertquad[3].a - vertquad_list[j][3].a) > EPSILON: continue
                        # all tests passed: so yes, we already have it!
                        f_index[i] = j
                        break
                    
                if (f_index[i] == len(vertquad_list)):
                    # first: add it to the vertex map
                    if not vertmap[v_index]:
                        vertmap[v_index] = []
                    vertmap[v_index].append( len(vertquad_list) )
                    # new (vert, uv-vert, normal, vcol) quad: add it
                    vertquad_list.append(vertquad)
                    # add the vertex
                    vertlist.append(vertquad[0])
                    if ( mesh_hasnormals ): normlist.append(vertquad[2])
                    if ( mesh_hasvcol ):    vcollist.append(vertquad[3])
                    if ( mesh_hastex ):     uvlist.append(vertquad[1])
            # now add the (hopefully, convex) face, in triangles
            for i in range(f_numverts - 2):
                f_indexed = Triangle()
                f_indexed.v1 = f_index[0]
                if (ob_scale[0] > 0):
                    f_indexed.v2 = f_index[1+i]
                    f_indexed.v3 = f_index[2+i]
                else:
                    f_indexed.v2 = f_index[2+i]
                    f_indexed.v3 = f_index[1+i]
                trilist.append(f_indexed)

        ishapedata.SetVertexCount(len(vertlist))
        ishapedata.SetVertices(vertlist)
        if mesh_hasnormals: ishapedata.SetNormals(normlist)
        if mesh_hasvcol:    ishapedata.SetColors(vcollist)
        if mesh_hastex:
            ishapedata.SetUVSetCount(1)
            ishapedata.SetUVSet(0, uvlist)
        itridata.SetTriangleCount(len(trilist))
        itridata.SetTriangles(trilist)

        # center
        count = 0
        center = Float3()
        for v in vertlist:
            #slows down too much #if VERBOSE: Blender.Window.DrawProgressBar(0.33 + 0.33 * float(count)/len(mesh.verts), "Converting to NIF (%s)"%ob.getName())
            count += 1
            center[0] += v.x
            center[1] += v.y
            center[2] += v.z
        assert(len(vertlist) > 0) # debug
        center[0] /= len(vertlist)
        center[1] /= len(vertlist)
        center[2] /= len(vertlist)
        
        # radius
        count = 0
        radius = 0.0
        for v in vertlist:
            #slows down too much #if VERBOSE: Blender.Window.DrawProgressBar(0.66 + 0.33 * float(count)/len(mesh.verts), "Converting to NIF (%s)"%ob.getName())
            count += 1
            r = get_distance(v, center)
            if (r > radius): radius = r

        tridata["Center"] = center
        tridata["Radius"] = radius

        # now export the vertex weights, if there are any
        vertgroups = ob.data.getVertGroupNames()
        bonenames = []
        if ob.getParent():
            if ob.getParent().getType() == 'Armature':
                bonenames = ob.getParent().getData().bones.keys()
        # the vertgroups that correspond to bonenames are bones that influence the mesh
        boneinfluences = []
        for bone in bonenames:
            if bone in vertgroups:
                boneinfluences.append(bone)
        if boneinfluences: # yes we have skinning!
            # create new skinning instance block and link it
            skininst = create_block("NiSkinInstance")
            trishape["Skin Instance"] = skininst
            # skininst["Skeleton Root"] = automatically calculated
            # skininst["Bones"] = automatically calculated

            # create skinning data and link it
            skindata = create_block("NiSkinData")
            skininst["Data"] = skindata
            iskindata = QuerySkinData(skindata)

            # add vertex weights
            # for each bone, first we get the bone block
            # then we get the vertex weights
            # and then we add it to the NiSkinData
            for bone in boneinfluences:
                # find bone in exported blocks
                for block in NIF_BLOCKS:
                    if block.GetBlockType() == "NiNode":
                        if block["Name"].asString() == bone:
                            bone_block = block
                            break
                else:
                    raise NIFExportError("Bone '%s' not found."%bone)
                # find vertex weights
                vert_list = ob.data.getVertsFromGroup(bone,1)
                vert_weights = {}
                for v in vert_list:
                    # v[0] is the original vertex index
                    # vertmap[v[0]] is the set of vertices (indices) to which v[0] was mapped
                    # so we simply export the same weight as the original vertex for each new vertex

                    # get normalizing factor
                    #infl_list = ob.data.getVertexInfluences(v[0]) # aargh! a blender bug prevents this from working
                    # alternative code:
                    norm = 0.0
                    for bone2 in boneinfluences:
                        tmp = ob.data.getVertsFromGroup(bone2, 1, [v[0]])
                        if tmp:
                            norm += tmp[0][1]

                    # write the weights
                    for vert_index in vertmap[v[0]]:
                        vert_weights[vert_index] = v[1] / norm
                iskindata.AddBone(bone_block, vert_weights)

        materialIndex += 1 # ...and process the next material



def export_bones(arm, parent_block):
    if DEBUG: print "Exporting bones for armature %s"%arm.getName()
    # the armature was already exported as a NiNode
    # now we must export the armature's bones
    assert( arm.getType() == 'Armature' )

    # find the root bones
    bones = dict(arm.getData().bones.items()) # dictionary of bones (name -> bone)
    root_bones = []
    for root_bone in bones.values():
        while root_bone.parent in bones.values():
            root_bone = root_bone.parent
        if root_bones.count(root_bone) == 0:
            root_bones.append(root_bone)

    if (arm.getAction()):
        bones_ipo = arm.getAction().getAllChannelIpos() # dictionary of Bone Ipos (name -> ipo)
    else:
        bones_ipo = {} # no ipos

    bones_node = {} # maps bone names to NiNode blocks

    # here we add all the bones; it's a bit ugly but hopefully it works
    # first we create all bones with their keyframes
    # and then we fix the links in a second run

    # ok, let's create the bone NiNode blocks
    for bone in bones.values():
        # create a new block for this bone
        if DEBUG: print "Exporting NiNode for bone %s"%bone.name
        node = create_block("NiNode")
        bones_node[bone.name] = node # doing this now makes linkage very easy in second run

        # add the node and the keyframe for this bone
        node["Name"] = bone.name
        node["Flags"] = 0x0002 # ? this seems pretty standard for bones
        ob_translation, \
        ob_rotation, \
        ob_scale, \
        ob_velocity \
        = export_matrix(bone, 'localspace') # first frame of animation!
        node["Rotation"]    = ob_rotation
        node["Velocity"]    = ob_velocity
        node["Scale"]       = ob_scale[0]
        node["Translation"] = ob_translation
        
        # bone rotations are stored in the IPO relative to the rest position
        # so we must take the rest position into account
        bonerestmat = get_bone_restmatrix(bone, 'BONESPACE')
        xq = bonerestmat.rotationPart().toQuat()
        xt = bonerestmat.translationPart()
        if bones_ipo.has_key(bone.name):
            export_keyframe(bones_ipo[bone.name], 'localspace', node, extra_trans = xt, extra_quat = xq)

        # Set the bind pose relative to the armature coordinate
        # system; this should work, if we do the same for the trishape
        # children. We should bind to the first frame of animation
        # since the mesh vertices have been transformed into the first
        # frame of animation as well.
        bbind_mat = get_bone_matrix(bone, 'ARMATURESPACE')
        bind_mat = Matrix44(
            bbind_mat[0][0], bbind_mat[0][1], bbind_mat[0][2], bbind_mat[0][3],
            bbind_mat[1][0], bbind_mat[1][1], bbind_mat[1][2], bbind_mat[1][3],
            bbind_mat[2][0], bbind_mat[2][1], bbind_mat[2][2], bbind_mat[2][3],
            bbind_mat[3][0], bbind_mat[3][1], bbind_mat[3][2], bbind_mat[3][3])
        inode = QueryNode(node)
        inode.SetBindPosition(bind_mat)
    
    # now fix the linkage between the blocks
    for bone in bones.values():
        if DEBUG: print "Linking children of bone %s"%bone.name
        # link the bone's children to the bone
        if bone.children:
            for child in bone.children:
                if child.parent.name == bone.name: # bone.children returns also grandchildren etc... we only want immediate children of course
                    bones_node[bone.name]["Children"].AddLink(bones_node[child.name])
        # if it is a root bone, link it to the armature
        if not bone.parent:
            parent_block["Children"].AddLink(bones_node[bone.name])

    # that's it!!!



#
# EXPERIMENTAL: Export texture effect.
# 
def export_textureeffect(ob, parent_block):
    assert(ob.getType() == 'Empty')
    
    # add a trishape block, and refer to this block in the parent's children list
    texeff = create_block("NiTextureEffect")
    parent_block["Children"].AddLink(texeff)
    parent_block["Effects"].AddLink(texeff)
        
    # fill in the NiTextureEffect's non-trivial values
    texeff["Flags"] = 0x0004
    t, r, s = export_matrix(ob, 'none')
    texeff["Translation"] = t
    texeff["Rotation"] = r
    texeff["Scale"] = s[0]
    
    # guessing
    texeff["Unknown Float 1"] = 1.0
    texeff["Unknown Float 2"] = 0.0
    texeff["Unknown Float 3"] = 0.0
    texeff["Unknown Float 4"] = 0.0
    texeff["Unknown Float 5"] = 1.0
    texeff["Unknown Float 6"] = 0.0
    texeff["Unknown Float 7"] = 0.0
    texeff["Unknown Float 8"] = 0.0
    texeff["Unknown Float 9"] = 1.0
    texeff["Unknown Float 10"] = 0.0
    texeff["Unknown Float 11"] = 0.0
    texeff["Unknown Float 12"] = 0.0
    texeff["Unknown Int 1"] = 2
    texeff["Unknown Int 2"] = 3
    texeff["Unknown Int 3"] = 2
    texeff["Unknown Int 4"] = 2
    texeff["Unknown Byte"] = 0
    texeff["Unknown Float 13"] = 1.0
    texeff["Unknown Float 14"] = 0.0
    texeff["Unknown Float 15"] = 0.0
    texeff["Unknown Float 16"] = 0.0
    texeff["PS2 L"] = 0
    texeff["PS2 K"] = 0xFFB5
    texeff["Unknown Short"] = 0

    # add NiTextureEffect's texture source
    texsrc = create_block("NiSourceTexture")
    texeff["Source Texture"] = texsrc

    texsrcdata = TextureSource()
    texsrcdata.useExternal = True
    texsrcdata.fileName = "enviro 01.TGA" # ?
    
    srctex["Texture Source"] = srctexdata
    srctex["Pixel Layout"] = 5
    srctex["Use Mipmaps"]  = 1
    srctex["Alpha Format"] = 3
    srctex["Unknown Byte"] = 1
    
    # done!



# 
# Export all children of blender object ob as children of parent_block.
# 
def export_children(ob, parent_block):
    # loop over all ob's children
    for ob_child in Blender.Object.Get():
        if (ob_child.getParent() == ob):
            # we found a child! try to add it to ob's children
            # is it a texture effect node?
            if ((ob_child.getType() == 'Empty') and (ob_child.getName()[:13] == 'TextureEffect')):
                export_textureeffect(ob_child, parent_block)
            # is it a regular node?
            elif (ob_child.getType() == 'Mesh') or (ob_child.getType() == 'Empty') or (ob_child.getType() == 'Armature'):
                if (ob.getType() != 'Armature'): # not parented to an armature...
                    export_node(ob_child, 'localspace', parent_block, ob_child.getName())
                else: # oh, this object is parented to an armature
                    # we should check whether it is really parented to the armature using vertex weights
                    # or whether it is parented to some bone of the armature
                    parent_bone_name = ob_child.getParentBoneName()
                    if parent_bone_name == None:
                        export_node(ob_child, 'localspace', parent_block, ob_child.getName())
                    else:
                        # we should parent the object to the bone instead of to the armature
                        # so let's find that bone!
                        for block in NIF_BLOCKS:
                            if block.GetBlockType() == "NiNode":
                                if block["Name"].asString() == parent_bone_name:
                                    export_node(ob_child, 'localspace', block, ob_child.getName())
                                    break
                        else:
                            assert(False) # BUG!



#
# Convert an object's transformation matrix on the first frame of
# animation to a niflib quadrupple ( translate, rotate, scale,
# velocity ). The scale is a vector; but non-uniform scaling is not
# supported by the nif format, so for these we'll have to apply the
# transformation when exporting the vertex coordinates... ?
#
def export_matrix(ob, space):
    nt = Float3()
    nr = Matrix33()
    ns = Float3()
    nv = Float3()
    
    # decompose
    bs, br, bt = getObjectSRT(ob, space)
    
    # and fill in the values
    nt[0] = bt[0]
    nt[1] = bt[1]
    nt[2] = bt[2]
    nr[0][0] = br[0][0]
    nr[1][0] = br[1][0]
    nr[2][0] = br[2][0]
    nr[0][1] = br[0][1]
    nr[1][1] = br[1][1]
    nr[2][1] = br[2][1]
    nr[0][2] = br[0][2]
    nr[1][2] = br[1][2]
    nr[2][2] = br[2][2]
    ns[0] = bs[0]
    ns[1] = bs[1]
    ns[2] = bs[2]
    nv[0] = 0.0
    nv[1] = 0.0
    nv[2] = 0.0

    # for now, we don't support non-uniform scaling
    if abs(ns[0] - ns[1]) + abs(ns[1] - ns[2]) > EPSILON:
        raise NIFExportError('ERROR%t|non-uniformly scaled objects not yet supported; apply size and rotation (CTRL-A in Object Mode) and try again.')

    # return result
    return (nt, nr, ns, nv)



# 
# Find scale, rotation, and translation components of an object in
# current frame of animation. Returns a triple (bs, br, bt), where bs
# is a scale vector, br is a 3x3 rotation matrix, and bt is a
# translation vector. It should hold that "ob.getMatrix(space) == bs *
# br * bt".
# 
def getObjectSRT(ob, space):
    # handle the trivial case first
    if (space == 'none'):
        bs = Blender.Mathutils.Vector([1.0, 1.0, 1.0])
        br = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
        bt = Blender.Mathutils.Vector([0.0, 0.0, 0.0])
        return (bs, br, bt)
    
    assert((space == 'worldspace') or (space == 'localspace'))

    # now write out spaces
    if (not type(ob) is Blender.Armature.BoneType):
        # get world matrix in first frame of animation
        mat = Blender.Mathutils.Matrix(ob.getMatrix('worldspace'))
        # handle localspace: L * Ba * B * P = W
        # (with L localmatrix, Ba bone animation channel, B bone rest matrix (armature space), P armature parent matrix, W world matrix)
        # so L = W * P^(-1) * (Ba * B)^(-1)
        if (space == 'localspace'):
            if (ob.getParent() != None):
                matparentinv = Blender.Mathutils.Matrix(ob.getParent().getMatrix('worldspace'))
                matparentinv.invert()
                mat = mat * matparentinv
                if (ob.getParent().getType() == 'Armature'):
                    # the object is parented to the armature... we must get the matrix relative to the bone parent, of course
                    bone_parent_name = ob.getParentBoneName()
                    if bone_parent_name:
                        bone_parent = ob.getParent().getData().bones[bone_parent_name]
                        # get bone parent matrix
                        matparentbone = get_bone_matrix(bone_parent, 'ARMATURESPACE') # bone matrix in armature space, first frame of animation
                        matparentboneinv = Blender.Mathutils.Matrix(matparentbone)
                        matparentboneinv.invert()
                        mat = mat * matparentboneinv
        # get translation
        bt = mat.translationPart()        
        # get the rotation part, this is scale * rotation
        bsr = mat.rotationPart()
    else: # bones, get the matrix of the first frame of animation
        assert(space == 'localspace') # in this function, we only need bones in localspace
        mat = get_bone_matrix(ob, 'BONESPACE')
        bsr = mat.rotationPart()
        bt = mat.translationPart()
    
    # get the squared scale matrix
    bsrT = Blender.Mathutils.Matrix(bsr)
    bsrT.transpose()
    bs2 = bsr * bsrT # bsr * bsrT = bs * br * brT * bsT = bs^2
    # debug: br2's off-diagonal elements must be zero!
    assert(abs(bs2[0][1]) + abs(bs2[0][2]) \
        + abs(bs2[1][0]) + abs(bs2[1][2]) \
        + abs(bs2[2][0]) + abs(bs2[2][1]) < EPSILON)
    
    # get scale components
    bs = Blender.Mathutils.Vector(\
         [ (bs2[0][0]) ** 0.5, (bs2[1][1]) ** 0.5, (bs2[2][2]) ** 0.5 ])
    # and fix their sign
    if (bsr.determinant() < 0): bs.negate()
    
    # get the rotation matrix
    br = Blender.Mathutils.Matrix(\
        [ bsr[0][0]/bs[0], bsr[0][1]/bs[0], bsr[0][2]/bs[0] ],\
        [ bsr[1][0]/bs[1], bsr[1][1]/bs[1], bsr[1][2]/bs[1] ],\
        [ bsr[2][0]/bs[2], bsr[2][1]/bs[2], bsr[2][2]/bs[2] ])
    
    # debug: rotation matrix must have determinant 1
    assert(abs(br.determinant() - 1.0) < EPSILON)

    # debug: rotation matrix must satisfy orthogonality constraint
    for i in range(3):
        for j in range(3):
            sum = 0.0
            for k in range(3):
                sum += br[k][i] * br[k][j]
            if (i == j): assert(abs(sum - 1.0) < EPSILON)
            if (i != j): assert(abs(sum) < EPSILON)
    
    # debug: the product of the scaling values must be equal to the determinant of the blender rotation part
    assert(abs(bs[0]*bs[1]*bs[2] - bsr.determinant()) < EPSILON)
    
    # TODO: debug: check that indeed bm == bs * br * bt

    return (bs, br, bt)



# 
# Get bone matrix in 1st frame of animation. Space can be
# ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
# is BONESPACE (also see get_bone_restmatrix).
# 
def get_bone_matrix(bone, space):
    # channels are applied in bone space, so let's start with BONESPACE
    mat = get_bone_restmatrix(bone, 'BONESPACE')
    # and multiply with bone parent ipo matrix, if there is one
    ipo = None
    for arm in Blender.Object.Get(): # Blender.Armature.Get() crashes Blender alpha release
        if arm.getType() == 'Armature' and arm.getAction():
            try:
                ipo = arm.getAction().getChannelIpo(bone.name)
                break
            except: pass
    if ipo:
        quat = Blender.Mathutils.Quaternion()
        quat.x = ipo.getCurve('QuatX').evaluate(1) # first frame
        quat.y = ipo.getCurve('QuatY').evaluate(1)
        quat.z = ipo.getCurve('QuatZ').evaluate(1)
        quat.w = ipo.getCurve('QuatW').evaluate(1)
        qmat = quat.toMatrix() * mat.rotationPart()
        # channel quat only affects the rotation part, it does not affect the head (translation) of the bone
        mat[0][0] = qmat[0][0]
        mat[0][1] = qmat[0][1]
        mat[0][2] = qmat[0][2]
        mat[1][0] = qmat[1][0]
        mat[1][1] = qmat[1][1]
        mat[1][2] = qmat[1][2]
        mat[2][0] = qmat[2][0]
        mat[2][1] = qmat[2][1]
        mat[2][2] = qmat[2][2]
        
    if (space == 'BONESPACE'):
        return mat
    elif (space == 'ARMATURESPACE'):
        if (not bone.parent):
            return mat
        else:
            return mat * get_bone_matrix(bone.parent, 'ARMATURESPACE')
    else:
        assert(False) # bug!



# 
# Get bone matrix in rest position ("bind pose"). Space can be
# ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
# is BONESPACE (translation is bone head plus tail from parent bone).
# 
def get_bone_restmatrix(bone, space):
    if (space == 'ARMATURESPACE'):
        return Blender.Mathutils.Matrix(bone.matrix['ARMATURESPACE']) # return a copy, not the wrapper
    elif (space == 'BONESPACE'):
        if bone.parent:
            parinv = Blender.Mathutils.Matrix(bone.parent.matrix['ARMATURESPACE'])
            parinv.invert()
            return bone.matrix['ARMATURESPACE'] * parinv
        else:
            return Blender.Mathutils.Matrix(bone.matrix['ARMATURESPACE'])
    else:
        assert(False) # bug!



#
# Calculate distance between two vectors.
#
def get_distance(v, w):
    return ((v.x-w[0])**2 + (v.y-w[1])**2 + (v.z-w[2])**2) ** 0.5



#
# Helper function to add a controller to a controllable block.
#
def add_controller(block, ctrl):
    if block["Controller"].asLink().is_null():
        block["Controller"] = ctrl
    else:
        lastctrl = block["Controller"].asLink()
        while not lastctrl["Next Controller"].asLink().is_null():
            lastctrl = lastctrl["Next Controller"].asLink()
        lastctrl["Next Controller"] = ctrl



#
# Helper function to add extra data
#
def add_extra_data(block, xtra):
    if block["Extra Data"].asLink().is_null():
        block["Extra Data"] = xtra
    else:
        lastxtra = block["Extra Data"].asLink()
        while not lastxtra["Extra Data"].asLink().is_null():
            lastxtra = lastxtra["Extra Data"].asLink()
        lastxtra["Extra Data"] = xtra



#
# Helper function to create a new block and add it to the list of exported blocks.
#
def create_block(blocktype):
    global NIF_BLOCKS
    if DEBUG: print "creating '%s'"%blocktype # DEBUG
    block = CreateBlock(blocktype)
    NIF_BLOCKS.append(block)
    return block



# 
# Scale NIF file and ensure that all scale values are 1.0 (fixes problem with TESCS selection box).
# 
def scale_tree(block, scale):
    if block.GetBlockType() in ["NiNode", "NiTriShape", "RootCollisionNode"]:
        # Scale factor removed from this block, which we must pass on children.
        s = block["Scale"].asFloat()
        # NiNode transform scale
        t = block["Translation"].asFloat3()
        t[0] *= scale
        t[1] *= scale
        t[2] *= scale
        block["Translation"] = t
        block["Scale"] = block["Scale"].asFloat() / s
        # NiNode bind position transform scale
        inode = QueryNode(block)
        mat = inode.GetBindPosition()
        mat[0][0] /= s
        mat[0][1] /= s
        mat[0][2] /= s
        mat[1][0] /= s
        mat[1][1] /= s
        mat[1][2] /= s
        mat[2][0] /= s
        mat[2][1] /= s
        mat[2][2] /= s
        mat[3][0] *= scale
        mat[3][1] *= scale
        mat[3][2] *= scale
        inode.SetBindPosition(mat)
        # Controller data block scale
        ctrl = block["Controller"].asLink()
        if not ctrl.is_null():
            kfd = ctrl["Data"].asLink()
            assert(not kfd.is_null())
            assert(kfd.GetBlockType() == "NiKeyframeData") # just to make sure, NiNode/NiTriShape controllers should have keyframe data
            ikfd = QueryKeyframeData(kfd)
            trans_keys = ikfd.GetTranslateKeys()
            if trans_keys:
                for key in trans_keys:
                    key.data.x *= scale
                    key.data.y *= scale
                    key.data.z *= scale
                ikfd.SetTranslateKeys(trans_keys)
            scale_keys = ikfd.GetScaleKeys()
            if scale_keys:
                for key in scale_keys:
                    key.data /= s
                ikfd.SetScaleKeys(scale_keys)
        # Child block scale
        if block.GetBlockType() != "NiTriShape": # scale the children
            for child in block["Children"].asLinkList():
                scale_tree(child, scale * s)
        else:
            scale_tree(block["Data"].asLink(), scale * s) # scale the NiTriShapeData
    elif block.GetBlockType() == "NiTriShapeData":
        # Scale all vertices
        ishapedata = QueryShapeData(block)
        vertlist = ishapedata.GetVertices()
        if vertlist:
            for vert in vertlist:
                vert.x *= scale
                vert.y *= scale
                vert.z *= scale
            ishapedata.SetVertices(vertlist)
        center = block["Center"].asFloat3()
        center[0] *= scale
        center[1] *= scale
        center[2] *= scale
        block["Radius"] = block["Radius"].asFloat() * scale

if EXPORT_DIR:
    Blender.Window.FileSelector(export_nif, 'Export NIF', EXPORT_DIR)
else:
    Blender.Window.FileSelector(export_nif, 'Export NIF')
