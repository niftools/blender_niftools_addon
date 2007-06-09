import Blender, Config
from Blender import Draw, BGL, sys

import tempfile

try:
    from NifFormat.NifFormat import NifFormat
except:
    err = """--------------------------
ERROR\nThis script requires the NifFormat Python library.
Make sure the NifFormat module resides in your Python path or in your Blender scripts folder.
If you do not have it: http://niftools.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|NifFormat not found, check console for details")
    raise

#
# Global variables.
#

_NIF_BLOCKS = [] # keeps track of all exported blocks
_NIF_TEXTURES = {} # keeps track of all exported textures
_NIF_MATERIALS = {} # keeps track of all exported materials
_NAMES = {} # maps Blender names to imported names if present
_NIF_BLOCK_NAMES = [] # keeps track of block names, to make sure they are unique

# dictionary of bones, maps Blender bone name to matrix that maps the
# NIF bone matrix on the Blender bone matrix
# Recall from the import script
#   B' = X * B,
# where B' is the Blender bone matrix, and B is the NIF bone matrix,
# both in armature space. So to restore the NIF matrices we need to do
#   B = X^{-1} * B'
# Hence, we will restore the X's, invert them, and store those inverses in the
# following dictionary.
_BONES_EXTRA_MATRIX_INV = {}


# configuration default values
_CONFIG = {}
_VERBOSE = True # Enables debug output
_EPSILON = 0.005 # used for checking equality with floats
_EXPORT_SCALE_CORRECTION = 10.0

APPLY_SCALE = True
FORCE_DDS = False
STRIP_TEXPATH = False
EXPORT_DIR = ''
NIF_VERSION_STR = '20.0.0.5'
NIF_VERSION = 0x14000005
ADD_BONE_NUB = False

_IDENTITY44 = NifFormat.Matrix44()
_IDENTITY44.setIdentity()

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
# To avoid confusion with event ID handling I register them all in a list
_GUI_EVENTS = []

_LOGO_PATH = sys.sep.join((Blender.Get('scriptsdir'),"bpymodules","nifImEx","niftools_logo.png"))
_LOGO_IMAGE = Blender.Image.Load(_LOGO_PATH)
_SCRIPT_VERSION = "1.9.0a"
_NIF_VERSION_DICT = {}



def __init__():
    global _CONFIG, _VERBOSE, _EPSILON, _EXPORT_SCALE_CORRECTION
    reload(Config)
    _CONFIG = Config._CONFIG
    _EPSILON = _CONFIG['EPSILON'] # used for checking equality with floats
    _VERBOSE = _CONFIG['VERBOSE'] # Enables debug output


def addEvent(evName = "NO_NAME"):
    global _GUI_EVENTS
    eventId = len(_GUI_EVENTS)
    if eventId >= 16383:
        raise "Maximum number of events exceeded"
        return None
    _GUI_EVENTS.append(evName)
    return eventId

    
def gui():
    global _GUI_ELEMENTS, _GUI_EVENTS, _CONFIG, _LOGO_IMAGE, _WINDOW_SIZE
    del _GUI_EVENTS[:]
    # These are to save me some typing
    H = Blender.Window.GetAreaSize()[1]
    E = {}
    # Draw NifTools logo
    BGL.glEnable(BGL.GL_BLEND ) # enable alpha blending
    # The odd scale and clip values seem necessary to avoid image artifacts
    Draw.Image(_LOGO_IMAGE, 50.0, H-100.0, 1.0001, 1.0001)
    #Draw.Image(logoImg, 50, H-100, 1.0, 1.0, 1.0, 0)
    # Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)
    nifFilePath = sys.sep.join((_CONFIG["NIF_EXPORT_PATH"], _CONFIG["NIF_EXPORT_FILE"]))
    E["NIF_FILE_PATH"]       = Draw.String("",              addEvent("NIF_FILE_PATH"),  50, H-150, 390, 20, nifFilePath, 350, '')
    E["BROWSE_FILE_PATH"]    = Draw.PushButton('...',       addEvent("BROWSE_FILE_PATH"), 440, H-150, 30, 20, 'browse')
    E["ADVANCED"]            = Draw.PushButton('advanced',  addEvent("ADVANCED"), 410, H-225, 100, 20)
    E["CANCEL"]              = Draw.PushButton('cancel',    addEvent("CANCEL"), 160, H-225, 100, 20)
    E["EXPORT"]              = Draw.PushButton('export',    addEvent("EXPORT"),  50, H-225, 100, 20)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(evt):
    """
    Event handler for buttons
    """
    global _CONFIG, _GUI_EVENTS
    evName = _GUI_EVENTS[evt]
    
    if evName == "EXPORT":
        # import and close
        exitGUI() #closes the GUI
        nifFilePath = sys.sep.join((_CONFIG["NIF_EXPORT_PATH"], _CONFIG["NIF_EXPORT_FILE"]))
        export_nif(nifFilePath)
    elif  evName == "CANCEL":
        # cancel
        exitGUI()
    elif  evName == "ADVANCED":
        # advanced
        exitGUI()
        Config.openGUI("Export")
    elif evName == "BROWSE_FILE_PATH":
        # browse file
        nifFilePath = sys.sep.join((_CONFIG["NIF_EXPORT_PATH"], _CONFIG["NIF_EXPORT_FILE"]))
        Blender.Window.FileSelector(selectFile, "export .nif", nifFilePath)

def selectFile(nifFilePath):
    global _CONFIG
    if nifFilePath == '':
        Draw.PupMenu('No file name selected')
    else:
        _CONFIG["NIF_EXPORT_PATH"] = sys.dirname(nifFilePath)
        _CONFIG["NIF_EXPORT_FILE"] = sys.basename(nifFilePath)
        Config._CONFIG = _CONFIG
        Config.save()



def event(evt, val):
    """
    Event handler for GUI elements
    """
    #print  "event(%i,%i)"%(arg1,arg2)
    if evt == Draw.ESCKEY:
        exitGUI()

def openGUI():
    """
    Opens the import GUI
    """
    global _CONFIG
    reload(Config)
    Config.load()
    _CONFIG = Config._CONFIG
    Draw.Register(gui, event, buttonEvent)

def exitGUI():
    """
    Closes the config GUI
    """
    global _CONFIG
    Config._CONFIG = _CONFIG
    Config.save()
    Draw.Exit()
    Draw.Redraw(1)




#
# A simple custom exception class.
#
class NIFExportError(StandardError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#
# Utility function to parse the Bone extra data buffer
#
def rebuild_bone_extra_data():
    global _BONES_EXTRA_MATRIX_INV
    try:
        bonetxt = Blender.Text.Get('BoneExMat')
    except:
        return
    # Blender bone names are unique so we can use them as keys.
    # TODO: restore the node names as well
    for ln in bonetxt.asLines():
        #print ln
        if len(ln)>0:
            b, m = ln.split('/')
            # Matrices are stored inverted for easier math later on.
            try:
                mat = Blender.Mathutils.Matrix(*[[float(f) for f in row.split(',')] for row in m.split(';')])
            except:
                raise NIFExportError('Syntax error in BoneExMat buffer.')
            mat.invert()
            _BONES_EXTRA_MATRIX_INV[b] = mat # X^{-1}


def rebuild_full_name_map():
    """
    Recovers the full object names from the text buffer and rebuilds
    the names dictionary
    """
    global _NAMES
    try:
        namestxt = Blender.Text.Get('FullNames')
    except:
        return
    for ln in namestxt.asLines():
        if len(ln)>0:
            name, fullname = ln.split(';')
            _NAMES[name] = fullname


def get_unique_name(blender_name):
    """
    Returns an unique name
    """
    global _NIF_BLOCK_NAMES
    unique_name = "default_name"
    if blender_name != None:
        unique_name = blender_name
    if unique_name in _NIF_BLOCK_NAMES:
        unique_int = 0
        old_name = unique_name
        while unique_name in _NIF_BLOCK_NAMES:
            # since the name length is an unsigned int I think I can avoid setting a maximum length
            #unique_name = '%s.%02d' % (old_name[:max_length-4], unique_int)
            unique_name = '%s.%02d' % (old_name, unique_int)
            unique_int +=1
    _NIF_BLOCK_NAMES.append(unique_name)
    return unique_name

def get_full_name(blender_name):
    """
    Returns the original imported name if present
    """
    global _NAMES, NIFOBJECT_NAMES
    try:
        return get_unique_name(_NAMES[blender_name])
    except KeyError:
        return get_unique_name(blender_name)

#
# Main export function.
#
def export_nif(filename):
    try: # catch NIFExportErrors
        
        # preparation:
        #--------------
        print "NIFTools NIF export script version %s" % (_SCRIPT_VERSION)
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
and turn off envelopes."""%ob.getName()
                    raise NIFExportError("'%s': Cannot export envelope skinning. Check console for instructions."%ob.getName())
        
        # extract some useful scene info
        scn = Blender.Scene.GetCurrent()
        context = scn.getRenderingContext()
        fspeed = 1.0 / context.framesPerSec()
        fstart = context.startFrame()
        fend = context.endFrame()
        
        # strip extension from filename
        filedir = Blender.sys.dirname(filename)
        root_name, fileext = Blender.sys.splitext(Blender.sys.basename(filename))
        
        # get the root object from selected object
        # only export empties, meshes, and armatures
        if (Blender.Object.GetSelected() == None):
            raise NIFExportError("Please select the object(s) that you wish to export, and run this script again.")
        root_objects = set()
        export_types = ('Empty','Mesh','Armature')
        for root_object in [ob for ob in Blender.Object.GetSelected() if ob.getType() in export_types]:
            while (root_object.getParent() != None):
                root_object = root_object.getParent()
            if root_object.getType() not in export_types:
                raise NIFExportError("Root object (%s) must be an 'Empty', 'Mesh', or 'Armature' object."%root_object.getName())
            root_objects.add(root_object)

        ## TODO use Blender actions for animation groups
        # check for animation groups definition in a text buffer called 'Anim'
        animtxt = None
        for txt in Blender.Text.Get():
            if txt.getName() == "Anim":
                animtxt = txt
                break
                
        # rebuilds the bone extra data dictionaries from the 'BoneExMat' text buffer
        rebuild_bone_extra_data()
        
        # rebuilds the full name dictionary from the 'FullNames' text buffer 
        rebuild_full_name_map()
        
        # export nif:
        #------------
        Blender.Window.DrawProgressBar(0.33, "Converting to NIF")
        
        # create a nif object
        
        # export the root node (note that transformation is ignored on the root node)
        root_block = export_node(None, 'none', None, root_name)
        
        # export objects
        if _VERBOSE: print "Exporting objects"
        for root_object in root_objects:
            # export the root objects as a NiNodes; their children are exported as well
            # note that localspace = worldspace, because root objects have no parents
            export_node(root_object, 'localspace', root_block, root_object.getName())

        # post-processing:
        #-----------------
        
        # if we exported animations, but no animation groups are defined, define a default animation group
        if _VERBOSE: print "Checking animation groups"
        if (animtxt == None):
            has_controllers = False
            for block in _NIF_BLOCKS:
                if isinstance(block, NifFormat.NiObjectNET): # has it a controller field?
                    if block.controller:
                        has_controllers = True
                        break
            if has_controllers:
                if _VERBOSE: print "Defining default animation group"
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
        if _VERBOSE: print "Checking controllers"
        if (animtxt):
            has_keyframecontrollers = False
            for block in _NIF_BLOCKS:
                if type(block) is NifFormat.NiKeyframeController:
                    has_keyframecontrollers = True
                    break
            if has_keyframecontrollers:
                if _VERBOSE: print "Defining dummy keyframe controller"
                # add a trivial keyframe controller on the scene root
                export_keyframe(None, 'localspace', root_block)
        
        # export animation groups
        if (animtxt):
            export_animgroups(animtxt, root_block)
            #export_animgroups(animtxt, root_block["Children"].asLinkList()[0]) # we link the animation extra data to the first root_object node

        # apply scale
        if APPLY_SCALE:
            root_block.applyScale(_EXPORT_SCALE_CORRECTION)

        # write the file:
        #----------------
        if _VERBOSE: print "Writing NIF file"
        Blender.Window.DrawProgressBar(0.66, "Writing NIF file(s)")

        # make sure we have the right file extension
        if (fileext.lower() != '.nif'):
            filename += '.nif'
        # TODO: sort this out later
        #if ( NIF_VERSION == 0x04000002 ): # assume Morrowind
        #    WriteFileGroup(filename, root_block, NIF_VERSION, EXPORT_NIF_KF, KF_MW)
        #elif ( NIF_VERSION == 0x14000004 ): # assume Civ4
        #    WriteFileGroup(filename, root_block, NIF_VERSION, EXPORT_NIF, KF_CIV4)
        #else: # default: simply write the NIF tree
        #    WriteNifTree(filename, root_block, NIF_VERSION)
        NIF_USER_VERSION = 0 if NIF_VERSION != 0x14000005 else 11
        f = open(filename, "wb")
        try:
            NifFormat.write(NIF_VERSION, NIF_USER_VERSION, f, [root_block])
        finally:
            f.close()

        
        
    except NIFExportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Export Failed")
        print 'NIFExportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return

    Blender.Window.DrawProgressBar(1.0, "Finished")
    
    # no export error, but let's double check: try reading the file(s) we just wrote
    # we can probably remove these lines once the exporter is stable
    try:
        f = open(filename, "rb")
        try:
            NifFormat.read(NIF_VERSION, NIF_USER_VERSION, f)
            f_tmp = tempfile.TemporaryFile()
            try:
                NifFormat.write(NIF_VERSION, NIF_USER_VERSION, f_tmp, [root_block])
                f.seek(2,0)
                f_tmp.seek(2,0)
                if f.tell() != f_tmp.tell(): # comparing the files will usually be different because blocks may have been written back in a different order, so cheaply just compare file sizes
                    raise NifExportError('write check failed: file sizes differ')
            finally:
                f_tmp.close()
        finally:
            f.close()
    except:
        Blender.Draw.PupMenu("WARNING%t|Exported NIF file may not be valid: double check failed! This is probably due to an unknown bug in the exporter code.")
        raise # re-raise the exception




# 
# Export a mesh/armature/empty object ob as child of parent_block.
# Export also all children of ob.
#
# - space is 'none', 'worldspace', or 'localspace', and determines
#   relative to what object the transformation should be stored.
# - parent_block is the parent nif block of the object (None for the root node)
# - for the root node, ob is None, and node_name is usually the base
#   filename (either with or without extension)
#
def export_node(ob, space, parent_block, node_name):
    if _VERBOSE: print "Exporting NiNode %s"%node_name

    # ob_type: determine the block type (None, 'Mesh', 'Empty' or 'Armature')
    # ob_ipo:  object animation ipo
    # node:    contains new NifFormat.NiNode instance
    if (ob == None):
        # -> root node
        assert(parent_block == None) # debug
        node = create_block("NiNode")
        ob_type = None
        ob_ipo = None
    else:
        # -> empty, mesh, or armature
        ob_type = ob.getType()
        assert(ob_type in ['Empty', 'Mesh', 'Armature']) # debug
        assert(parent_block) # debug
        ob_ipo = ob.getIpo() # get animation data
        ob_children = [child for child in Blender.Object.Get() if child.parent == ob]
        
        if (node_name == 'RootCollisionNode'):
            # -> root collision node (can be mesh or empty)
            node = create_block("RootCollisionNode")
        elif ob_type == 'Mesh':
            # -> mesh data.
            # If this has children or animations or more than one material
            # it gets wrapped in a purpose made NiNode.
            has_ipo = ob_ipo and len(ob_ipo.getCurves()) > 0
            has_children = len(ob_children) > 0
            is_multimaterial = len(set([f.mat for f in ob.data.faces])) > 1
            if has_ipo or has_children or is_multimaterial:
                # -> mesh ninode for the hierarchy to work out
                node = create_block('NiNode')
            else:
                # don't create intermediate ninode for this guy
                export_trishapes(ob, space, parent_block, node_name)
                # we didn't create a ninode, return nothing
                return None
        else:
            # -> everything else (empty/armature) is a regular node
            node = create_block("NiNode")

    # set transform on trishapes rather than on NiNode for skinned meshes
    # this fixes an issue with clothing slots
    if ob_type == 'Mesh':
        ob_parent = ob.getParent()
        if ob_parent and ob_parent.getType() == 'Armature':
            trishape_space = space
            space = 'none'
        else:
            trishape_space = 'none'

    # make it child of its parent in the nif, if it has one
    if (parent_block):
        parent_block.addChild(node)
    
    # and fill in this node's non-trivial values
    node.name = get_full_name(node_name)
    if (ob == None):
        node.flags = 0x000C # ? this seems pretty standard for the root node
    elif (node_name == 'RootCollisionNode'):
        node.flags = 0x0003 # ? this seems pretty standard for the root collision node
    else:
        node.flags = 0x000C # ? this seems pretty standard for static and animated ninodes

    export_matrix(ob, space, node)

    # set object bind position
    if ob != None and ob.getParent():
        pass
        # TODO
        #bbind_mat = ob.getMatrix('worldspace') # TODO: cancel out all IPO's
        #bind_mat = Matrix44(
        #    bbind_mat[0][0], bbind_mat[0][1], bbind_mat[0][2], bbind_mat[0][3],
        #    bbind_mat[1][0], bbind_mat[1][1], bbind_mat[1][2], bbind_mat[1][3],
        #    bbind_mat[2][0], bbind_mat[2][1], bbind_mat[2][2], bbind_mat[2][3],
        #    bbind_mat[3][0], bbind_mat[3][1], bbind_mat[3][2], bbind_mat[3][3])
        #node.SetWorldBindPos(bind_mat)

    if (ob != None):
        # export animation
        if (ob_ipo != None):
            export_keyframe(ob_ipo, space, node)
    
        # if it is a mesh, export the mesh as trishape children of this ninode
        if (ob.getType() == 'Mesh'):
            export_trishapes(ob, trishape_space, node) # see definition of trishape_space above
            
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
# bind_mat is the original Blender bind matrix (the B' matrix below)
# extra_mat_inv is the inverse matrix which transforms the Blender bone matrix
# to the NIF bone matrix (the inverse of the X matrix below)
#
# Explanation of extra transformations:
# Final transformation matrix is vec * Rchannel * Tchannel * Rbind * Tbind
# So we export:
# [ SRchannel 0 ]    [ SRbind 0 ]   [ SRchannel * SRbind        0 ]
# [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel * SRbind + Tbind 1 ]
# or, in detail,
# Stotal = Schannel * Sbind
# Rtotal = Rchannel * Rbind
# Ttotal = Tchannel * Sbind * Rbind + Tbind
# We also need the conversion of the new bone matrix to the original matrix, say X,
# B' = X * B
# (with B' the Blender matrix and B the NIF matrix) because we need that
# C' * B' = X * C * B
# and therefore
# C * B = inverse(X) * C' * B'
# (we need to write out C * B, the NIF format stores total transformation in keyframes).
# In detail:
#          [ SRX 0 ]     [ SRC' 0 ]   [ SRB' 0 ]
# inverse( [ TX  1 ] ) * [ TC'  1 ] * [ TB'  1 ] =
# [ inverse(SRX)         0 ]   [ SRC' * SRB'         0 ]
# [ -TX * inverse(SRX)   1 ] * [ TC' * SRB' + TB'    1 ] =
# [ inverse(SRX) * SRC' * SRB'                       0 ]
# [ (-TX * inverse(SRX) * SRC' + TC') * SRB' + TB'    1 ]
# Hence
# S = SC' * SB' / SX
# R = inverse(RX) * RC' * RB'
# T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
#
# Finally, note that
# - TX * inverse(RX) / SX = translation part of inverse(X)
# inverse(RX) = rotation part of inverse(X)
# 1 / SX = scale part of inverse(X)
# so having inverse(X) around saves on calculations
def export_keyframe(ipo, space, parent_block, bind_mat = None, extra_mat_inv = None):
    if _VERBOSE: print "Exporting keyframe %s"%parent_block.name
    # -> get keyframe information
    
    assert(space == 'localspace') # we don't support anything else (yet)
    assert(isinstance(parent_block, NifFormat.NiNode)) # make sure the parent is of the right type
    
    # some calculations
    if bind_mat:
        bind_scale, bind_rot, bind_trans = decompose_srt(bind_mat)
        bind_quat = bind_rot.toQuat()
    else:
        bind_scale = 1.0
        bind_rot = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
        bind_quat = Blender.Mathutils.Quaternion(1,0,0,0)
        bind_trans = Blender.Mathutils.Vector(0,0,0)
    if extra_mat_inv:
        extra_scale_inv, extra_rot_inv, extra_trans_inv = decompose_srt(extra_mat_inv)
        extra_quat_inv = extra_rot_inv.toQuat()
    else:
        extra_scale_inv = 1.0
        extra_rot_inv = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
        extra_quat_inv = Blender.Mathutils.Quaternion(1,0,0,0)
        extra_trans_inv = Blender.Mathutils.Vector(0,0,0)

    # get frame start and frame end, and the number of frames per second
    scn = Blender.Scene.GetCurrent()
    context = scn.getRenderingContext()
 
    fspeed = 1.0 / context.framesPerSec()
    fstart = context.startFrame()
    fend = context.endFrame()

    # sometimes we need to export an empty keyframe... this will take care of that
    if (ipo == None):
        scale_curve = {}
        rot_curve = {}
        trans_curve = {}
    # the usual case comes now...
    else:
        # merge the animation curves into a rotation vector and translation vector curve
        scale_curve = {}
        rot_curve = {}
        trans_curve = {}
        for curve in ipo.getCurves():
            for btriple in curve.getPoints():
                knot = btriple.getPoints()
                frame = knot[0]
                if (frame < fstart) or (frame > fend): continue
                if (curve.getName() == 'SizeX') or (curve.getName() == 'SizeY') or (curve.getName() == 'SizeZ'):
                    scale_curve[frame] = ( ipo.getCurve('SizeX').evaluate(frame)\
                                        + ipo.getCurve('SizeY').evaluate(frame)\
                                        + ipo.getCurve('SizeZ').evaluate(frame) ) / 3.0 # support only uniform scaling... take the mean
                    scale_curve[frame] = scale_curve[frame] * bind_scale * extra_scale_inv # SC' * SB' / SX
                if (curve.getName() == 'RotX') or (curve.getName() == 'RotY') or (curve.getName() == 'RotZ'):
                    rot_curve[frame] = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toQuat()
                    # beware, CrossQuats takes arguments in a counter-intuitive order:
                    # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                    rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                elif (curve.getName() == 'QuatX') or (curve.getName() == 'QuatY') or (curve.getName() == 'QuatZ') or  (curve.getName() == 'QuatW'):
                    rot_curve[frame] = Blender.Mathutils.Quaternion()
                    rot_curve[frame].x = ipo.getCurve('QuatX').evaluate(frame)
                    rot_curve[frame].y = ipo.getCurve('QuatY').evaluate(frame)
                    rot_curve[frame].z = ipo.getCurve('QuatZ').evaluate(frame)
                    rot_curve[frame].w = ipo.getCurve('QuatW').evaluate(frame)
                    # beware, CrossQuats takes arguments in a counter-intuitive order:
                    # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                    rot_curve[frame] = Blender.Mathutils.CrossQuats(Blender.Mathutils.CrossQuats(bind_quat, rot_curve[frame]), extra_quat_inv) # inverse(RX) * RC' * RB'
                if (curve.getName() == 'LocX') or (curve.getName() == 'LocY') or (curve.getName() == 'LocZ'):
                    trans_curve[frame] = Blender.Mathutils.Vector([ipo.getCurve('LocX').evaluate(frame), ipo.getCurve('LocY').evaluate(frame), ipo.getCurve('LocZ').evaluate(frame)])
                    # T = - TX * inverse(RX) * RC' * RB' * SC' * SB' / SX + TC' * SB' * RB' + TB'
                    trans_curve[frame] *= bind_scale
                    trans_curve[frame] *= bind_rot
                    trans_curve[frame] += bind_trans
                    # we need RC' and SC'
                    if ipo.getCurve('RotX'):
                        rot_c = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toMatrix()
                    elif ipo.getCurve('QuatX'):
                        rot_c = Blender.Mathutils.Quaternion()
                        rot_c.x = ipo.getCurve('QuatX').evaluate(frame)
                        rot_c.y = ipo.getCurve('QuatY').evaluate(frame)
                        rot_c.z = ipo.getCurve('QuatZ').evaluate(frame)
                        rot_c.w = ipo.getCurve('QuatW').evaluate(frame)
                        rot_c = rot_c.toMatrix()
                    else:
                        rot_c = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
                    if ipo.getCurve('SizeX'):
                        scale_c = ( ipo.getCurve('SizeX').evaluate(frame)\
                                  + ipo.getCurve('SizeY').evaluate(frame)\
                                  + ipo.getCurve('SizeZ').evaluate(frame) ) / 3.0 # support only uniform scaling... take the mean
                    else:
                        scale_c = 1.0
                    trans_curve[frame] += extra_trans_inv * rot_c * bind_rot * scale_c * bind_scale

    # -> now comes the real export

    # add a keyframecontroller block, and refer to this block in the parent's time controller
    kfc = create_block("NiKeyframeController")
    add_controller(parent_block, kfc)

    # fill in the non-trivial values
    kfc.flags = 0x0008
    kfc.frequency = 1.0
    kfc.phase = 0.0
    kfc.startTime = (fstart - 1) * fspeed
    kfc.stopTime = (fend - fstart) * fspeed

    # add the keyframe data
    kfd = create_block("NiKeyframeData")
    kfc.data = kfd

    frames = rot_curve.keys()
    frames.sort()
    kfd.rotationType = NifFormat.KeyType.LINEAR_KEY
    kfd.numRotationKeys = len(frames)
    kfd.quaternionKeys.updateSize()
    for i, frame in enumerate(frames):
        rot_frame = kfd.quaternionKeys[i]
        rot_frame.time = (frame - 1) * fspeed
        rot_frame.value.w = rot_curve[frame].w
        rot_frame.value.x = rot_curve[frame].x
        rot_frame.value.y = rot_curve[frame].y
        rot_frame.value.z = rot_curve[frame].z

    frames = trans_curve.keys()
    frames.sort()
    kfd.translations.interpolation = NifFormat.KeyType.LINEAR_KEY
    kfd.translations.numKeys = len(frames)
    kfd.translations.keys.updateSize()
    for i, frame in enumerate(frames):
        trans_frame = kfd.translations.keys[i]
        trans_frame.time = (frame - 1) * fspeed
        trans_frame.value.x = trans_curve[frame][0]
        trans_frame.value.y = trans_curve[frame][1]
        trans_frame.value.z = trans_curve[frame][2]

    frames = scale_curve.keys()
    frames.sort()
    kfd.scales.interpolation = NifFormat.KeyType.LINEAR_KEY
    kfd.scales.numKeys = len(frames)
    kfd.scales.keys.updateSize()
    for frame in frames:
        scale_frame = kfd.scales.keys[i]
        scale_frame.time = (frame - 1) * fspeed
        scale_frame.value = scale_curve[frame]



def export_vcolprop(vertex_mode, lighting_mode):
    if _VERBOSE: print "Exporting NiVertexColorProperty"
    # create new vertex color property block
    vcolprop = create_block("NiVertexColorProperty")
    
    # make it a property of the root node
    _NIF_BLOCKS[0]["Children"].AddLink(vcolprop)

    # and now export the parameters
    vcolprop["Vertex Mode"] = vertex_mode
    vcolprop["Lighting Mode"] = lighting_mode



#
# parse the animation groups buffer and write an extra string data block,
# parented to the root block
#
def export_animgroups(animtxt, block_parent):
    if _VERBOSE: print "Exporting animation groups"
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
    textextra.numTextKeys = len(flist)
    textextra.textKeys.updateSize()
    for i in range(len(flist)):
        key = textextra.textKeys[i]
        key.time = fspeed * (flist[i]-1)
        key.value = dlist[i]



#
# export a NiSourceTexture
#
# texture is the texture object in blender to be exported
# filename is the full or relative path to the texture file ( used by NiFlipController )
#
# Returns block of the exported NiSourceTexture
#
def export_sourcetexture(texture, filename = None):
    global _NIF_TEXTURES
    
    if _VERBOSE: print "Exporting source texture %s"%texture.getName()
    # texture must be of type IMAGE
    if ( texture.type != Blender.Texture.Types.IMAGE ):
        raise NIFExportError( "Error: Texture '%s' must be of type IMAGE"%texture.getName())
    
    # check if the texture is already exported
    if filename != None:
        texid = filename
    else:
        texid = texture.image.getFilename()
    if _NIF_TEXTURES.has_key(texid):
        return _NIF_TEXTURES[texid]

    # add NiSourceTexture
    srctex = create_block("NiSourceTexture")
    srctex.useExternal = not texture.getImage().packed
    if srctex.useExternal:
        if filename != None:
            tfn = filename
        else:
            tfn = texture.image.getFilename()
        if ( STRIP_TEXPATH == 1 ):
            # strip texture file path (original morrowind style)
            srctex.fileName = Blender.sys.basename(tfn)
        elif ( STRIP_TEXPATH == 0 ):
            # strip the data files prefix from the texture's file name
            tfn = tfn.lower()
            idx = tfn.find( "textures" )
            if ( idx >= 0 ):
                tfn = tfn[idx:]
                tfn = tfn.replace(Blender.sys.sep, '\\') # for linux
                srctex.fileName = tfn
            else:
                srctex.fileName = Blender.sys.basename(tfn)
        # try and find a DDS alternative, force it if required
        ddsFile = "%s%s" % (srctex.fileName[:-4], '.dds')
        if Blender.sys.exists(ddsFile) == 1 or FORCE_DDS:
            srctex.fileName = ddsFile

    else:   # if the file is not external
        if filename != None:
            try:
                image = Blender.Image.Load( filename )
            except:
                raise NIFExportError( "Error: Cannot pack texture '%s'; Failed to load image '%s'"%(texture.getName(),filename) )
        else:
            image = texture.image
        
        w, h = image.getSize()
        if ( w <= 0 ) or ( h <= 0 ):
            image.reload()
        if ( w <= 0 ) or ( h <= 0 ):
            raise NIFExportError( "Error: Cannot pack texture '%s'; Failed to load image '%s'"%(texture.getName(),image.getFilename()) )
        
        depth = image.getDepth()
        if image.getDepth() == 32:
            pixelformat = PX_FMT_RGBA8
        elif image.getDepth() == 24:
            pixelformat = PX_FMT_RGB8
        else:
            raise NIFExportError( "Error: Cannot pack texture '%s' image '%s'; Unsupported image depth %i"%(texture.getName(),image.getFilename(),image.getDepth()) )
        
        colors = []
        for y in range( h ):
            for x in range( w ):
                r, g, b, a = image.getPixelF( x, (h-1)-y )
                colors.append( Color4( r, g, b, a ) )
        
        pixeldata = create_block("NiPixelData")
        ipdata = QueryPixelData( pixeldata )
        ipdata.Reset( w, h, pixelformat )
        ipdata.SetColors( colors, texture.imageFlags & Blender.Texture.ImageFlags.MIPMAP != 0 )
        srctex["Texture Source"] = pixeldata

    # fill in default values
    srctex.pixelLayout = 5
    srctex.useMipmaps = 2
    srctex.alphaFormat = 3
    srctex.unknownByte = 1
    srctex.unknownByte2 = 1

    # save for future reference
    _NIF_TEXTURES[texid] = srctex
    
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
    if _VERBOSE: print "Exporting NiFlipController for texture %s"%texture.getName()
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
    flip["Texture Slot"] = target_tex
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
# The parameter trishape_name passes on the name for meshes that
# should be exported as a single mesh.
# 
def export_trishapes(ob, space, parent_block, trishape_name = None):
    if _VERBOSE: print "Exporting NiTriShapes for %s"%ob.getName()
    assert(ob.getType() == 'Mesh')

    # get mesh from ob
    mesh_orig = Blender.NMesh.GetRaw(ob.data.name) # original non-subsurfed mesh
    
    # get the mesh's materials, this updates the mesh material list
    mesh_mats = mesh_orig.getMaterials(1) # the argument guarantees that the material list agrees with the face material indices
    # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
    if (mesh_mats == []):
        mesh_mats = [ None ]

    # get mesh with modifiers, such as subsurfing; we cannot update the mesh after calling this function
    try:
        mesh = Blender.NMesh.GetRawFromObject(ob.name) # subsurf modifiers
    except:
        mesh = mesh_orig
    mesh = mesh_orig
    
    # let's now export one trishape for every mesh material
    
    for materialIndex, mesh_mat in enumerate( mesh_mats ):
        # -> first, extract valuable info from our ob
        
        mesh_base_tex = None
        mesh_glow_tex = None
        mesh_hasalpha = False # mesh has transparency
        mesh_hastex = False   # mesh has at least one texture
        mesh_hasspec = False  # mesh has specular properties
        mesh_hasvcol = False
        mesh_hasnormals = False
        if (mesh_mat != None):
            mesh_hasnormals = True # for proper lighting
            # for non-textured materials, vertex colors are used to color the mesh
            # for textured materials, they represent lighting details
            # strange: mesh.hasVertexColours() only returns true if the mesh has no texture coordinates
            mesh_hasvcol = mesh.hasVertexColours() or ((mesh_mat.mode & Blender.Material.Modes.VCOL_LIGHT != 0) or (mesh_mat.mode & Blender.Material.Modes.VCOL_PAINT != 0))
            # read the Blender Python API documentation to understand this hack
            mesh_mat_ambient = mesh_mat.getAmb()            # 'Amb' scrollbar in blender (MW -> 1.0 1.0 1.0)
            mesh_mat_diffuse_color = mesh_mat.getRGBCol()   # 'Col' colour in Blender (MW -> 1.0 1.0 1.0)
            mesh_mat_specular_color = mesh_mat.getSpecCol() # 'Spe' colour in Blender (MW -> 0.0 0.0 0.0)
            specval = mesh_mat.getSpec()                    # 'Spec' slider in Blender
            mesh_mat_specular_color[0] *= specval
            mesh_mat_specular_color[1] *= specval
            mesh_mat_specular_color[2] *= specval
            if mesh_mat_specular_color[0] > 1.0: mesh_mat_specular_color[0] = 1.0
            if mesh_mat_specular_color[1] > 1.0: mesh_mat_specular_color[1] = 1.0
            if mesh_mat_specular_color[2] > 1.0: mesh_mat_specular_color[2] = 1.0
            if ( mesh_mat_specular_color[0] > _EPSILON ) \
                or ( mesh_mat_specular_color[1] > _EPSILON ) \
                or ( mesh_mat_specular_color[2] > _EPSILON ):
                mesh_hasspec = True
            mesh_mat_emissive = mesh_mat.getEmit()              # 'Emit' scrollbar in Blender (MW -> 0.0 0.0 0.0)
            mesh_mat_glossiness = mesh_mat.getHardness() / 4.0  # 'Hardness' scrollbar in Blender, takes values between 1 and 511 (MW -> 0.0 - 128.0)
            mesh_mat_transparency = mesh_mat.getAlpha()         # 'A(lpha)' scrollbar in Blender (MW -> 1.0)
            mesh_hasalpha = (abs(mesh_mat_transparency - 1.0) > _EPSILON) \
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
                            mesh_hastex = True # flag that we have textures, and that we should export UV coordinates
                            # check if alpha channel is enabled for this texture
                            if (mesh_base_tex.imageFlags & Blender.Texture.ImageFlags.USEALPHA != 0) and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                # in this case, Blender replaces the texture transparant parts with the underlying material color...
                                # in NIF, material alpha is multiplied with texture alpha channel...
                                # how can we emulate the NIF alpha system (simply multiplying material alpha with texture alpha) when MapTo.ALPHA is turned on?
                                # require the Blender material alpha to be 0.0 (no material color can show up), and use the "Var" slider in the texture blending mode tab!
                                # but...
                                if (mesh_mat_transparency > _EPSILON):
                                    raise NIFExportError("Cannot export this type of transparency in material '%s': instead, try to set alpha to 0.0 and to use the 'Var' slider in the 'Map To' tab under the material buttons."%mesh_mat.getName())
                                if (mesh_mat.getIpo() and mesh_mat.getIpo().getCurve('Alpha')):
                                    raise NIFExportError("Cannot export animation for this type of transparency in material '%s': remove alpha animation, or turn off MapTo.ALPHA, and try again."%mesh_mat.getName())
                                mesh_mat_transparency = mtex.varfac # we must use the "Var" value
                                mesh_hasalpha = True
                        else:
                            raise NIFExportError("Multiple base textures in mesh '%s', material '%s', this is not supported. Delete all textures, except for the base texture."%(mesh.name,mesh_mat.getName()))
                    else:
                        # MapTo EMIT is checked -> glow map
                        if ( mesh_glow_tex == None ):
                            # check if calculation of alpha channel is enabled for this texture
                            if (mesh_base_tex.imageFlags & Blender.Texture.ImageFlags.CALCALPHA != 0) and (mtex.mapto & Blender.Texture.MapTo.ALPHA != 0):
                                raise NIFExportError("In mesh '%s', material '%s': glow texture must have CALCALPHA flag set, and must have MapTo.ALPHA enabled."%(ob.getName(),mesh_mat.getName()))
                            # got the glow tex
                            mesh_glow_tex = mtex.tex
                            mesh_hastex = True
                        else:
                            raise NIFExportError("Multiple glow textures in mesh '%s', material '%s'. Make sure there is only one texture with MapTo.EMIT"%(mesh.name,mesh_mat.getName()))

        # -> now comes the real export
        
        # We now extract vertices, uv-vertices, normals, and vertex
        # colors from the mesh's face list. NIF has one uv vertex and
        # one normal per vertex, unlike blender's uv vertices and
        # normals per face... therefore some vertices must be
        # duplicated. The following algorithm extracts all unique
        # (vert, uv-vert, normal, vcol) quads, and uses this list to
        # produce the list of vertices, uv-vertices, normals, vertex
        # colors, and face indices.

        # Blender only supports one set of uv coordinates per mesh;
        # therefore, we shall have trouble when importing
        # multi-textured trishapes in blender. For this export script,
        # no problem: we must simply duplicate the uv vertex list.

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
        for f in mesh.faces:
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
                fv = f.v[i].co
                # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                if mesh_hasnormals:
                    if f.smooth:
                        fn = f.v[i].no
                    else:
                        fn = f.no
                else:
                    fn = None
                if (mesh_hastex):
                    fuv = f.uv[i]
                else:
                    fuv = None
                if (mesh_hasvcol):
                    if (len(f.col) == 0):
                        raise NIFExportError('ERROR%t|Vertex color painting/lighting enabled, but mesh has no vertex color data.')
                    # NIF stores the colour values as floats
                    fcol = f.col[i]
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
                            if abs(vertquad[1][0] - vertquad_list[j][1][0]) > _EPSILON: continue
                            if abs(vertquad[1][1] - vertquad_list[j][1][1]) > _EPSILON: continue
                        if mesh_hasnormals:
                            if abs(vertquad[2][0] - vertquad_list[j][2][0]) > _EPSILON: continue
                            if abs(vertquad[2][1] - vertquad_list[j][2][1]) > _EPSILON: continue
                            if abs(vertquad[2][2] - vertquad_list[j][2][2]) > _EPSILON: continue
                        if mesh_hasvcol:
                            if abs(vertquad[3].r - vertquad_list[j][3].r) > _EPSILON: continue
                            if abs(vertquad[3].g - vertquad_list[j][3].g) > _EPSILON: continue
                            if abs(vertquad[3].b - vertquad_list[j][3].b) > _EPSILON: continue
                            if abs(vertquad[3].a - vertquad_list[j][3].a) > _EPSILON: continue
                        # all tests passed: so yes, we already have it!
                        f_index[i] = j
                        break

                if f_index[i] > 65535:
                    raise NIFExportError('ERROR%t|Too many vertices. Decimate your mesh and try again.')
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
                if True: #TODO: #(ob_scale > 0):
                    f_indexed = (f_index[0], f_index[1+i], f_index[2+i])
                else:
                    f_indexed = (f_index[0], f_index[2+i], f_index[1+i])
                trilist.append(f_indexed)

        if len(trilist) > 65535:
            raise NIFExportError('ERROR%t|Too many faces. Decimate your mesh and try again.')
        if len(vertlist) == 0:
            continue # m4444x: skip 'empty' material indices
        
        # note: we can be in any of the following five situations
        # material + base texture        -> normal object
        # material + base tex + glow tex -> normal glow mapped object
        # material + glow texture        -> (needs to be tested)
        # material, but no texture       -> uniformly coloured object
        # no material                    -> typically, collision mesh

        # add a trishape block, and refer to this block in the parent's children list
        trishape = create_block("NiTriShape")
        parent_block.addChild(trishape)
        
        # fill in the NiTriShape's non-trivial values
        if (parent_block.name != ""):
            if len(mesh_mats) > 1:
                if (trishape_name == None):
                    trishape_name = "Tri " + parent_block.name + " %i"%materialIndex # Morrowind's child naming convention
                else:
                    # This should take care of "manually merged" meshes. 
                    trishape_name = trishape_name + " %i"%materialIndex
            else:
                # this is a hack for single materialed meshes
                assert(materialIndex == 0)
                if (trishape_name == None):
                    trishape_name = "Tri " + parent_block.name
        trishape.name = get_full_name(trishape_name)
        if ob.getDrawType() != 2: # not wire
            trishape.flags = 0x0004 # use triangles as bounding box
        else:
            trishape.flags = 0x0005 # use triangles as bounding box + hide

        export_matrix(ob, space, trishape)
        
        if (mesh_base_tex != None or mesh_glow_tex != None):
            # add NiTriShape's texturing property
            tritexprop = create_block("NiTexturingProperty")
            trishape.addProperty(tritexprop)

            tritexprop.flags = 0x0001 # standard
            tritexprop.applyMode = NifFormat.ApplyMode.APPLY_MODULATE
            tritexprop.textureCount = 7

            if ( mesh_base_tex != None ):
                tritexprop.hasBaseTexture = True
                basetex = tritexprop.baseTexture
                basetex.isUsed = True
                
                # check for texture flip definition
                txtlist = Blender.Text.Get()
                for fliptxt in txtlist:
                    if fliptxt.getName() == mesh_base_tex.getName():
                        export_flipcontroller( fliptxt, mesh_base_tex, tritexprop, BASE_MAP )
                        break
                    else:
                        fliptxt = None
                else:
                    basetex.source = export_sourcetexture(mesh_base_tex)

            if ( mesh_glow_tex != None ):
                glowtex = TexDesc()
                glowtex.isUsed = 1

                # check for texture flip definition
                txtlist = Blender.Text.Get()
                for fliptxt in txtlist:
                    if fliptxt.getName() == mesh_glow_tex.getName():
                        export_flipcontroller( fliptxt, mesh_glow_tex, tritexprop, GLOW_MAP )
                        break
                    else:
                        fliptxt = None
                else:
                    glowtex.source = export_sourcetexture(mesh_glow_tex)
                
                itritexprop.SetTexture(GLOW_MAP, glowtex)
        
        if (mesh_hasalpha):
            # add NiTriShape's alpha propery (this is de facto an automated version of Detritus's method, see http://detritus.silgrad.com/alphahex.html)
            trialphaprop = create_block("NiAlphaProperty")
            trialphaprop["Flags"] = 0x00ED
            
            # refer to the alpha property in the trishape block
            trishape["Properties"].AddLink(trialphaprop)

        if (mesh_mat != None):
            # add NiTriShape's specular property
            if ( mesh_hasspec ):
                trispecprop = create_block("NiSpecularProperty")
                trispecprop.flags = 0x0001
            
                # refer to the specular property in the trishape block
                trishape.addProperty(trispecprop)
            
            # add NiTriShape's material property
            trimatprop = create_block("NiMaterialProperty")
            
            trimatprop.name = get_full_name(mesh_mat.getName())
            trimatprop.flags = 0x0001 # ? standard
            trimatprop.ambientColor.r = mesh_mat_ambient_color[0]
            trimatprop.ambientColor.g = mesh_mat_ambient_color[1]
            trimatprop.ambientColor.b = mesh_mat_ambient_color[2]
            trimatprop.diffuseColor.r = mesh_mat_diffuse_color[0]
            trimatprop.diffuseColor.g = mesh_mat_diffuse_color[1]
            trimatprop.diffuseColor.b = mesh_mat_diffuse_color[2]
            trimatprop.specularColor.r = mesh_mat_specular_color[0]
            trimatprop.specularColor.g = mesh_mat_specular_color[1]
            trimatprop.specularColor.b = mesh_mat_specular_color[2]
            trimatprop.emissiveColor.r = mesh_mat_emissive_color[0]
            trimatprop.emissiveColor.g = mesh_mat_emissive_color[1]
            trimatprop.emissiveColor.b = mesh_mat_emissive_color[2]
            trimatprop.glossiness = mesh_mat_glossiness
            trimatprop.alpha = mesh_mat_transparency
            
            # refer to the material property in the trishape block
            trishape.addProperty(trimatprop)


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
                add_controller( trimatprop, alphac )

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
                add_controller(trimatprop, matcolc)

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
                    rgba_frame = Key_Color4()
                    rgba_frame.time = ftime
                    rgba_frame.data.r = rgba_curve[ftime][0]
                    rgba_frame.data.g = rgba_curve[ftime][1]
                    rgba_frame.data.b = rgba_curve[ftime][2]
                    rgba_frame.data.a = rgba_curve[ftime][3]
                    rgba_keys.append(rgba_frame)
                imatcold.SetKeys(rgba_keys)

        # add NiTriShape's data
        # NIF flips the texture V-coordinate (OpenGL standard)
        tridata = create_block("NiTriShapeData")
        trishape.data = tridata

        tridata.numVertices = len(vertlist)
        tridata.hasVertices = True
        tridata.vertices.updateSize()
        for i, v in enumerate(tridata.vertices):
            v.x = vertlist[i][0]
            v.y = vertlist[i][1]
            v.z = vertlist[i][2]
        tridata.updateCenterRadius()
        
        if mesh_hasnormals:
            tridata.hasNormals = True
            tridata.normals.updateSize()
            for i, v in enumerate(tridata.normals):
                v.x = normlist[i][0]
                v.y = normlist[i][1]
                v.z = normlist[i][2]
            
        if mesh_hasvcol:
            tridata.hasVertexColors = True
            tridata.vertexColors.updateSize()
            for i, v in enumerate(tridata.vertexColors):
                v.r = vcollist[i].r / 255.0
                v.g = vcollist[i].g / 255.0
                v.b = vcollist[i].b / 255.0
                v.a = vcollist[i].a / 255.0

        if mesh_hastex:
            tridata.numUvSets = 1
            tridata.hasUv = True
            tridata.uvSets.updateSize()
            for i, uv in enumerate(tridata.uvSets[0]):
                uv.u = uvlist[i][0]
                uv.v = 1.0 - uvlist[i][1] # opengl standard

        tridata.numTriangles = len(trilist)
        tridata.numTrianglePoints = 3*len(trilist)
        tridata.hasTriangles = True
        tridata.triangles.updateSize()
        for i, v in enumerate(tridata.triangles):
            v.v1 = trilist[i][0]
            v.v2 = trilist[i][1]
            v.v3 = trilist[i][2]

        # update tangent space
        if NIF_VERSION >= 0x14000005:
            trishape.updateTangentSpace()

        # now export the vertex weights, if there are any
        vertgroups = ob.data.getVertGroupNames()
        bonenames = []
        if ob.getParent():
            if ob.getParent().getType() == 'Armature':
                ob_armature = ob.getParent()
                armaturename = ob_armature.getName()
                bonenames = ob_armature.getData().bones.keys()
                boneobjects = ob_armature.getData().bones
                # the vertgroups that correspond to bonenames are bones that influence the mesh
                boneinfluences = []
                for bone in bonenames:
                    if bone in vertgroups:
                        boneinfluences.append(bone)
                if boneinfluences: # yes we have skinning!
                    # create new skinning instance block and link it
                    skininst = create_block("NiSkinInstance")
                    trishape.skinInstance = skininst
                    for block in _NIF_BLOCKS:
                        if isinstance(block, NifFormat.NiNode):
                            if block.name == armaturename:
                                skininst.skeletonRoot = block
                                break
                    else:
                        raise NIFExportError("Skeleton root '%s' not found."%armaturename)
                    skininst.numBones = len(boneinfluences)
                    skininst.bones.updateSize()
        
                    # create skinning data and link it
                    skindata = create_block("NiSkinData")
                    skininst.data = skindata
        
                    skindata.numBones = len(boneinfluences)
                    skindata.boneList.updateSize()
                    skindata.hasVertexWeights = True
                    # fix geometry rest pose: transform relative to skeleton root
                    skindata.setTransform(get_object_matrix(ob, 'localspace').getInverse())
        
                    # add vertex weights
                    # first find weights and normalization factors
                    vert_list = {}
                    vert_norm = {}
                    for bone in boneinfluences:
                        vert_list[bone] = ob.data.getVertsFromGroup(bone, 1)
                        for v in vert_list[bone]:
                            if vert_norm.has_key(v[0]):
                                vert_norm[v[0]] += v[1]
                            else:
                                vert_norm[v[0]] = v[1]
                    
                    # for each bone, first we get the bone block
                    # then we get the vertex weights
                    # and then we add it to the NiSkinData
                    vert_added = [False] * len(vertlist) # allocate memory for faster performance
                    for bone_index, bone in enumerate(boneinfluences):
                        # find bone in exported blocks
                        for block in _NIF_BLOCKS:
                            if isinstance(block, NifFormat.NiNode):
                                if block.name == bone:
                                    bone_block = block
                                    skininst.bones[bone_index] = bone_block
                                    break
                        else:
                            raise NIFExportError("Bone '%s' not found."%bone)
                        # find vertex weights
                        vert_weights = {}
                        for v in vert_list[bone]:
                            # v[0] is the original vertex index
                            # v[1] is the weight
                            
                            # vertmap[v[0]] is the set of vertices (indices) to which v[0] was mapped
                            # so we simply export the same weight as the original vertex for each new vertex
        
                            # write the weights
                            if vertmap[v[0]] and vert_norm[v[0]]: # extra check for multi material meshes
                                for vert_index in vertmap[v[0]]:
                                    vert_weights[vert_index] = v[1] / vert_norm[v[0]]
                                    vert_added[vert_index] = True
                        # add bone as influence, but only if there were actually any vertices influenced by the bone
                        if vert_weights:
                            skinbonedata = skindata.boneList[bone_index]
                            # set rest pose
                            skinbonedata.setTransform(bmatrix_to_matrix(get_bone_restmatrix(boneobjects[bone], 'ARMATURESPACE')).getInverse())
                            # set vertex weights
                            skinbonedata.numVertices = len(vert_weights)
                            skinbonedata.vertexWeights.updateSize()
                            for i, (vert_index, vert_weight) in enumerate(vert_weights.iteritems()):
                                skinbonedata.vertexWeights[i].index = vert_index
                                skinbonedata.vertexWeights[i].weight = vert_weight
        
                    # each vertex must have been assigned to at least one vertex group
                    # or the model doesn't display correctly in the TESCS
                    # here we cover that case: we attach them to the armature
                    vert_weights = {}
                    for vert_index, added in enumerate(vert_added):
                        if not added:
                            vert_weights[vert_index] = 1.0
                    if vert_weights:
                        # add armature as bone (TODO add bone functions to NifFormat)
                        bone_index = len(boneinfluences)
                        skininst.numBones = bone_index+1
                        skininst.bones.updateSize()
                        skininst.bones[bone_index] = skininst.skeletonRoot
                        skindata.numBones = bone_index+1
                        skindata.boneList.updateSize()
                        skinbonedata = skindata.boneList[bone_index]
                        # set rest pose
                        skinbonedata.setTransform(_IDENTITY44)
                        # set vertex weights
                        skinbonedata.numVertices = len(vert_weights)
                        skinbonedata.vertexWeights.updateSize()
                        for i, (vert_index, vert_weight) in enumerate(vert_weights.iteritems()):
                            skinbonedata.vertexWeights[i].index = vert_index
                            skinbonedata.vertexWeights[i].weight = vert_weight

            # clean up
            del vert_weights
            del vert_added

        
        # shape key morphing
        key = mesh.getKey()
        if key:
            if len( key.getBlocks() ) > 1:
                # yes, there is a key object attached
                # FIXME: check if key object contains relative shape keys
                keyipo = key.getIpo()
                if keyipo:
                    # yes, there is a shape ipo too
                    
                    # get frame start and the number of frames per second
                    scn = Blender.Scene.GetCurrent()
                    context = scn.getRenderingContext()
                    fspeed = 1.0 / context.framesPerSec()
                    fstart = context.startFrame()
                    fend = context.endFrame()
                    
                    # create geometry morph controller
                    morphctrl = create_block("NiGeomMorpherController")
                    add_controller( trishape, morphctrl )
                    morphctrl["Frequency"] = 1.0
                    morphctrl["Phase"] = 0.0
                    ctrlStart = 1000000.0
                    ctrlStop = 0.0
                    ctrlFlags = 0x000c
                    
                    # create geometry morph data
                    morphdata = create_block("NiMorphData")
                    morphctrl["Data"] = morphdata
                    morphdata["Unknown Byte"] = 0x01
                    imorphdata = QueryMorphData(morphdata)
                    imorphdata.SetVertexCount( len( vertlist ) );
                    imorphdata.SetMorphCount( len( key.getBlocks() ) )
                    
                    for keyblocknum, keyblock in enumerate( key.getBlocks() ):
                        # export morphed vertices
                        morphverts = [ None ] * len( vertlist )
                        for vert in keyblock.data:
                            if ( vertmap[ vert.index ] ):
                                mv = Vector3( *(vert.co) )
                                if keyblocknum > 0:
                                    mv.x -= mesh.verts[vert.index].co.x
                                    mv.y -= mesh.verts[vert.index].co.y
                                    mv.z -= mesh.verts[vert.index].co.z
                                for vert_index in vertmap[ vert.index ]:
                                    morphverts[ vert_index ] = mv
                        imorphdata.SetMorphVerts( keyblocknum, morphverts )
                        
                        # export ipo shape key curve
                        #curve = keyipo.getCurve( 'Key %i'%keyblocknum ) # FIXME
                        # workaround
                        curve = None
                        if ( keyblocknum - 1 ) in range( len( keyipo.getCurves() ) ):
                            curve = keyipo.getCurves()[keyblocknum-1]
                        # base key has no curve all other keys should have one
                        if curve:
                            if _VERBOSE: print "exporting morph curve %i"%keyblocknum
                            if ( curve.getExtrapolation() == "Constant" ):
                                ctrlFlags = 0x000c
                            elif ( curve.getExtrapolation() == "Cyclic" ):
                                ctrlFlags = 0x0008
                            keys = []
                            for btriple in curve.getPoints():
                                kfloat = Key_float()
                                knot = btriple.getPoints()
                                kfloat.time = (knot[0] - fstart) * fspeed
                                kfloat.data = curve.evaluate( knot[0] )
                                kfloat.forward_tangent = 0.0 # ?
                                kfloat.backward_tangent = 0.0 # ?
                                keys.append(kfloat)
                                if kfloat.time < ctrlStart:
                                    ctrlStart = kfloat.time
                                if kfloat.time > ctrlStop:
                                    ctrlStop = kfloat.time
                            imorphdata.SetMorphKeys( keyblocknum, keys )
                    morphctrl["Flags"] = ctrlFlags
                    morphctrl["Start Time"] = ctrlStart
                    morphctrl["Stop Time"] = ctrlStop

def export_bones(arm, parent_block):
    if _VERBOSE: print "Exporting bones for armature %s"%arm.getName()
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
        if _VERBOSE: print "Exporting NiNode for bone %s"%bone.name
        node = create_block("NiNode")
        bones_node[bone.name] = node # doing this now makes linkage very easy in second run

        # add the node and the keyframe for this bone
        node.name = get_full_name(bone.name)
        node.flags = 0x0002 # ? this seems pretty standard for bones
        export_matrix(bone, 'localspace', node) # rest pose
        
        # bone rotations are stored in the IPO relative to the rest position
        # so we must take the rest position into account
        bonerestmat = get_bone_restmatrix(bone, 'BONESPACE', extra = False) # we need the original one, without extra transforms
        try:
            #bonexmat_inv = _BONES_EXTRA_MATRIX_INV[bone.name]
            raise KeyError # (TODO: check maths with brandano)
        except KeyError:
            bonexmat_inv = Blender.Mathutils.Matrix()
            bonexmat_inv.identity()
        if bones_ipo.has_key(bone.name):
            export_keyframe(bones_ipo[bone.name], 'localspace', node, bind_mat = bonerestmat, extra_mat_inv = bonexmat_inv)

    # now fix the linkage between the blocks
    for bone in bones.values():
        # link the bone's children to the bone
        if bone.children:
            if _VERBOSE: print "Linking children of bone %s"%bone.name
            for child in bone.children:
                if child.parent.name == bone.name: # bone.children returns also grandchildren etc... we only want immediate children of course
                    bones_node[bone.name].addChild(bones_node[child.name])
        else:
            if False: # *** disabled for now *** #if ADD_BONE_NUB:
                # no children: export dummy NiNode to preserve tail position
                if _VERBOSE: print "Bone %s has no children: adding dummy child for tail."%bone.name
                mat = get_bone_restmatrix(bone, 'ARMATURESPACE')
                mat.invert()
                tail = bone.tail['ARMATURESPACE'] * mat.rotationPart() + mat.translationPart()
                dummy = CreateBlock("NiNode")
                dummy["Rotation"] = Matrix33(1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0)
                dummy["Velocity"]    = Float3(0.0,0.0,0.0)
                dummy["Scale"]       = 1.0
                dummy["Translation"] = Float3(tail[0], tail[1], tail[2])
                bbind_mat = get_bone_restmatrix(bone, 'ARMATURESPACE')
                tail = Blender.Mathutils.Vector(bone.tail['ARMATURESPACE'])
                bind_mat = Matrix44(\
                    bbind_mat[0][0], bbind_mat[0][1], bbind_mat[0][2], 0.0,\
                    bbind_mat[1][0], bbind_mat[1][1], bbind_mat[1][2], 0.0,\
                    bbind_mat[2][0], bbind_mat[2][1], bbind_mat[2][2], 0.0,\
                    tail[0], tail[1], tail[2], 1.0)
                idummy = QueryNode(dummy)
                idummy.SetWorldBindPos(bind_mat)
                bones_node[bone.name]["Children"].AddLink(dummy)
        # if it is a root bone, link it to the armature
        if not bone.parent:
            parent_block.addChild(bones_node[bone.name])

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
    export_matrix(ob, 'none', texeff)
    
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

    texsrcdata = TexSource()
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
    for ob_child in [cld  for cld in Blender.Object.Get() if cld.getParent() == ob]:
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
                    for block in _NIF_BLOCKS:
                        if block.GetBlockType() == "NiNode":
                            if block["Name"].asString() == parent_bone_name:
                                export_node(ob_child, 'localspace', block, ob_child.getName())
                                break
                    else:
                        assert(False) # BUG!



#
# Set a block's transform matrix to an object's
# transformation matrix (rest pose)
#
def export_matrix(ob, space, block):
    # decompose
    bs, br, bt = get_object_srt(ob, space)
    
    # and fill in the values
    block.translation.x = bt[0]
    block.translation.y = bt[1]
    block.translation.z = bt[2]
    block.rotation.m11 = br[0][0]
    block.rotation.m12 = br[0][1]
    block.rotation.m13 = br[0][2]
    block.rotation.m21 = br[1][0]
    block.rotation.m22 = br[1][1]
    block.rotation.m23 = br[1][2]
    block.rotation.m31 = br[2][0]
    block.rotation.m32 = br[2][1]
    block.rotation.m33 = br[2][2]
    block.velocity.x = 0.0
    block.velocity.y = 0.0
    block.velocity.z = 0.0
    block.scale = bs

    return bs, br, bt

#
# Get an object's matrix
#
def get_object_matrix(ob, space):
    bs, br, bt = get_object_srt(ob, space)
    m = NifFormat.Matrix44()
    
    m.m41 = bt[0]
    m.m42 = bt[1]
    m.m43 = bt[2]

    m.m11 = br[0][0]*bs
    m.m12 = br[0][1]*bs
    m.m13 = br[0][2]*bs
    m.m21 = br[1][0]*bs
    m.m22 = br[1][1]*bs
    m.m23 = br[1][2]*bs
    m.m31 = br[2][0]*bs
    m.m32 = br[2][1]*bs
    m.m33 = br[2][2]*bs

    m.m14 = 0.0
    m.m24 = 0.0
    m.m34 = 0.0
    m.m44 = 1.0
    
    return m

#
# Convert blender matrix to NifFormat.Matrix44
#
def bmatrix_to_matrix(bm):
    m = NifFormat.Matrix44()
    
    m.m41 = bm[3][0]
    m.m42 = bm[3][1]
    m.m43 = bm[3][2]

    m.m11 = bm[0][0]*bm[3][3]
    m.m12 = bm[0][1]*bm[3][3]
    m.m13 = bm[0][2]*bm[3][3]
    m.m21 = bm[1][0]*bm[3][3]
    m.m22 = bm[1][1]*bm[3][3]
    m.m23 = bm[1][2]*bm[3][3]
    m.m31 = bm[2][0]*bm[3][3]
    m.m32 = bm[2][1]*bm[3][3]
    m.m33 = bm[2][2]*bm[3][3]

    m.m14 = 0.0
    m.m24 = 0.0
    m.m34 = 0.0
    m.m44 = 1.0
    
    return m

# 
# Find scale, rotation, and translation components of an object in
# the rest pose. Returns a triple (bs, br, bt), where bs
# is a scale float, br is a 3x3 rotation matrix, and bt is a
# translation vector. It should hold that "ob.getMatrix(space) == bs *
# br * bt".
# 
def get_object_srt(ob, space):
    # handle the trivial case first
    if (space == 'none'):
        bs = 1.0
        br = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
        bt = Blender.Mathutils.Vector([0, 0, 0])
        return (bs, br, bt)
    
    assert((space == 'worldspace') or (space == 'localspace'))

    # now write out spaces
    if (not type(ob) is Blender.Armature.Bone):
        # get world matrix
        mat = get_object_restmatrix(ob, 'worldspace')
        # handle localspace: L * Ba * B * P = W
        # (with L localmatrix, Ba bone animation channel, B bone rest matrix (armature space), P armature parent matrix, W world matrix)
        # so L = W * P^(-1) * (Ba * B)^(-1)
        if (space == 'localspace'):
            if (ob.getParent() != None):
                matparentinv = get_object_restmatrix(ob.getParent(), 'worldspace')
                matparentinv.invert()
                mat *= matparentinv
                if (ob.getParent().getType() == 'Armature'):
                    # the object is parented to the armature... we must get the matrix relative to the bone parent
                    bone_parent_name = ob.getParentBoneName()
                    if bone_parent_name:
                        bone_parent = ob.getParent().getData().bones[bone_parent_name]
                        # get bone parent matrix
                        matparentbone = get_bone_restmatrix(bone_parent, 'ARMATURESPACE') # bone matrix in armature space
                        matparentboneinv = Blender.Mathutils.Matrix(matparentbone)
                        matparentboneinv.invert()
                        mat *= matparentboneinv
    else: # bones, get the rest matrix
        assert(space == 'localspace') # in this function, we only need bones in localspace
        mat = get_bone_restmatrix(ob, 'BONESPACE')
    
    return decompose_srt(mat)



# Decompose Blender transform matrix as a scale, rotation matrix, and translation vector
def decompose_srt(m):
    # get scale components
    b_scale_rot = m.rotationPart()
    b_scale_rot_T = Blender.Mathutils.Matrix(b_scale_rot)
    b_scale_rot_T.transpose()
    b_scale_rot_2 = b_scale_rot * b_scale_rot_T
    b_scale = Blender.Mathutils.Vector(\
        b_scale_rot_2[0][0] ** 0.5,\
        b_scale_rot_2[1][1] ** 0.5,\
        b_scale_rot_2[2][2] ** 0.5)
    # and fix their sign
    if (b_scale_rot.determinant() < 0): b_scale.negate()
    # only uniform scaling
    if abs(b_scale[0]-b_scale[1]) + abs(b_scale[1]-b_scale[2]) > _EPSILON:
        raise NIFExportError("Non-uniform scaling not supported. Workaround: apply size and rotation (CTRL-A).")
    b_scale = b_scale[0]
    # get rotation matrix
    b_rot = b_scale_rot * (1.0/b_scale)
    # get translation
    b_trans = m.translationPart()
    # done!
    return b_scale, b_rot, b_trans



# 
# Get bone matrix in rest position ("bind pose"). Space can be
# ARMATURESPACE or BONESPACE. This returns also a 4x4 matrix if space
# is BONESPACE (translation is bone head plus tail from parent bone).
# 
def get_bone_restmatrix(bone, space, extra = True):
    # Retrieves the offset from the original NIF matrix, if existing
    corrmat = Blender.Mathutils.Matrix()
    if extra:
        try:
            corrmat = _BONES_EXTRA_MATRIX_INV[bone.name]
        except:
            corrmat.identity()
    else:
        corrmat.identity()
    if (space == 'ARMATURESPACE'):
        return corrmat * Blender.Mathutils.Matrix(bone.matrix['ARMATURESPACE'])
    elif (space == 'BONESPACE'):
        if bone.parent:
            parinv = get_bone_restmatrix(bone.parent,'ARMATURESPACE')
            parinv.invert()
            return (corrmat * bone.matrix['ARMATURESPACE']) * parinv
        else:
            return corrmat * Blender.Mathutils.Matrix(bone.matrix['ARMATURESPACE'])
    else:
        assert(False) # bug!



# get the object's rest matrix
# space can be 'localspace' or 'worldspace'
def get_object_restmatrix(ob, space, extra = True):
    mat = Blender.Mathutils.Matrix(ob.getMatrix('worldspace')) # TODO cancel out IPO's
    if (space == 'localspace'):
        par = ob.getParent()
        if par:
            parinv = get_object_restmatrix(par, 'worldspace')
            parinv.invert()
            mat *= parinv
    return mat



#
# Calculate distance between two vectors.
#
def get_distance(v, w):
    return ((v.x-w[0])**2 + (v.y-w[1])**2 + (v.z-w[2])**2) ** 0.5



#
# Helper function to add a controller to a controllable block.
#
def add_controller(block, ctrl):
    if block.controller == None:
        block.controller = ctrl
    else:
        lastctrl = block.controller
        while lastctrl.nextController != None:
            lastctrl = lastctrl.nextController
        lastctrl.nextController = ctrl



#
# Helper function to add extra data
#
def add_extra_data(block, xtra):
    if NIF_VERSION < 0x0A000100:
        # the extra data chain paradigm
        if not block.extraData:
            block.extraData = xtra
        else:
            lastxtra = block.extraData
            while lastxtra.extraData:
                lastxtra = lastxtra.extraData
            lastxtra.extraData = xtra
    else:
        # the extra data list paradigm
        block.extraDataList.addLink(xtra) # TODO: add function in NifFormat lib



#
# Helper function to create a new block and add it to the list of exported blocks.
#
def create_block(blocktype):
    global _NIF_BLOCKS
    if _VERBOSE: print "creating '%s'"%blocktype # DEBUG
    try:
        block = getattr(NifFormat, blocktype)()
    except AttributeError:
        raise NIFExportError("'%s': Unknown block type (this is probably a bug).")
    _NIF_BLOCKS.append(block)
    return block
