import Blender, Config
from Blender import Draw, BGL, sys
from Blender.Mathutils import *
#from GUI import *

#try:
#    import psyco
#    psyco.full()
#except:
#    print 'no psyco for you!'

try:
    from PyFFI.NIF import NifFormat
except:
    err = """--------------------------
ERROR\nThis script requires the Python File Format Interface (PyFFI).
Make sure that PyFFI resides in your Python path or in your Blender scripts folder.
If you do not have it: http://pyffi.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|PyFFI not found, check console for details")
    raise

#
# Configuration
#

_CONFIG = {}

# Retrieves the stored configuration
def loadConfig():
    global _CONFIG
    reload(Config)
    Config.load()
    _CONFIG = Config._CONFIG
    
# Stores the altered configuration
def saveConfig():
    Config._CONFIG = _CONFIG
    Config.save()
    
loadConfig()

#
# Global variables.
#


# Sets the amount of generated debug output
_VERBOSITY = _CONFIG["VERBOSITY"]

# Sets the resolution used for float comparisons
_EPSILON = _CONFIG["EPSILON"]

# All UI elements are kept in this dictionary to make sure they never go out of scope
_GUI_ELEMENTS = {}
# To avoid confusion with event ID handling I register them all in a list
_GUI_EVENTS = []

_LOGO_PATH = sys.sep.join((Blender.Get('scriptsdir'), "bpymodules", "nifImEx", "niftools_logo.png"))
_LOGO_IMAGE = Blender.Image.Load(_LOGO_PATH)
_SCRIPT_VERSION = "2.0.4"
_BLOCK_COUNT = 0
_READ_PROGRESS = 0.0
_BLOCKS_READ = 0.0

# dictionary of texture files, to reuse textures
_TEXTURES = {}

# dictionary of materials, to reuse materials
_MATERIALS = {}

# dictionary of names, to map NIF blocks to correct Blender names
_NAMES = {}

# dictionary of bones, maps Blender name to NIF block
_BLOCKS = {}

# dictionary of bones, maps Blender bone name to matrix that maps the
# NIF bone matrix on the Blender bone matrix
# B' = X * B, where B' is the Blender bone matrix, and B is the NIF bone matrix
_BONES_EXTRA_MATRIX = {}

# dictionary of bones that belong to a certain armature
# maps NIF armature name to list of NIF bone name
_ARMATURES = {}

# correction matrices list, the order is +X, +Y, +Z, -X, -Y, -Z
_BONE_CORRECTION_MATRICES = (\
            Matrix([ 0.0,-1.0, 0.0],[ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 1.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0],[ 0.0,-1.0, 0.0]),\
            Matrix([ 0.0, 1.0, 0.0],[-1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([-1.0, 0.0, 0.0],[ 0.0,-1.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0,-1.0],[ 0.0, 1.0, 0.0]))

# identity matrix, for comparisons
_IDENTITY44 = Matrix([ 1.0,0.0, 0.0, 0.0],\
            [ 0.0, 1.0, 0.0, 0.0],\
            [ 0.0, 0.0, 1.0, 0.0],\
            [ 0.0, 0.0, 0.0, 1.0])

# some variables

_R2D = 3.14159265358979/180.0 # radians to degrees conversion constant
_D2R = 180.0/3.14159265358979 # degrees to radians conversion constant

_SCENE = Blender.Scene.GetCurrent() #Blender scene, to avoid redundant code
_FPS = _SCENE.getRenderingContext().framesPerSec() #frames per second

def addEvent(evName = "NO_NAME"):
    global _GUI_EVENTS
    eventId = len(_GUI_EVENTS)
    if eventId >= 16383:
        raise "Maximum number of events exceeded"
        return None
    _GUI_EVENTS.append(evName)
    return eventId

def guiText(str = "", xpos = 0, ypos = 0):
    # To draw text on the screen I have to position its start point first
    BGL.glRasterPos2i( xpos, ypos)
    Draw.Text(str)
    
def gui():
    global _GUI_ELEMENTS, _GUI_EVENTS, _CONFIG, _LOGO_IMAGE
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
    nifFilePath = sys.sep.join((_CONFIG["NIF_IMPORT_PATH"], _CONFIG["NIF_IMPORT_FILE"]))
    skfilepath = ""
    E["NIF_FILE_PATH"]      = Draw.String("",             addEvent("NIF_FILE_PATH"),  50, H-150, 390, 20, nifFilePath, 350, '')
    E["BROWSE_FILE_PATH"]   = Draw.PushButton('...',      addEvent("BROWSE_FILE_PATH"), 440, H-150, 30, 20, 'browse')
    E["ADVANCED"]           = Draw.PushButton('advanced', addEvent("ADVANCED"), 410, H-225, 100, 20)
    E["CANCEL"]             = Draw.PushButton('cancel',   addEvent("CANCEL"), 160, H-225, 100, 20)
    E["IMPORT"]             = Draw.PushButton('import',   addEvent("IMPORT"),  50, H-225, 100, 20)
    E["TXT_NIF_FILE_PATH"]  = guiText("NIF file path", 50, H-125)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(evt):
    """
    Event handler for buttons
    """
    global _GUI_EVENTS
    evName = _GUI_EVENTS[evt]
    if evName == "IMPORT":
        # import and close
        print "todo: add checks for file input box"
        exitGUI() #closes the GUI
        nifFilePath = sys.sep.join((_CONFIG["NIF_IMPORT_PATH"], _CONFIG["NIF_IMPORT_FILE"]))
        import_nif(nifFilePath)
    elif evName == "CANCEL":
        # cancel
        exitGUI()
    elif evName == "ADVANCED":
        # advanced
        exitGUI()
        Config.openGUI("Import")
    elif evName == "BROWSE_FILE_PATH":
        # browse file
        #nifFilePath = sys.sep.join((_CONFIG["NIF_IMPORT_PATH"], _CONFIG["NIF_IMPORT_FILE"]))
        #Blender.Window.FileSelector(selectFile, "import .nif", nifFilePath)
        openFileSelector()

def event(evt, val):
    """
    Event handler for GUI elements
    """
    #print  "event(%i,%i)"%(arg1,arg2)
    if evt == Draw.ESCKEY:
        exitGUI()

def openFileSelector():
    nifFilePath = sys.sep.join((_CONFIG["NIF_IMPORT_PATH"], _CONFIG["NIF_IMPORT_FILE"]))
    Blender.Window.FileSelector(selectFile, "import .nif", nifFilePath)
        
def selectFile(nifFilePath):
    global _CONFIG
    if nifFilePath == '' or not sys.exists(nifFilePath):
        Draw.PupMenu('No file selected or file does not exist%t|Ok')
    else:
        _CONFIG["NIF_IMPORT_PATH"] = sys.dirname(nifFilePath)
        _CONFIG["NIF_IMPORT_FILE"] = sys.basename(nifFilePath)
        saveConfig()
    exitGUI()
    openGUI()

def openGUI():
    """
    Opens the import GUI
    """
    loadConfig()
    Draw.Register(gui, event, buttonEvent)

def exitGUI():
    """
    Closes the config GUI
    """
    saveConfig()
    Draw.Exit()
    Draw.Redraw(1)


# Little wrapper for debug messages
def msg(message='-', level=2):
    if _VERBOSITY and level <= _VERBOSITY:
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
    global _SCRIPT_VERSION
    try: # catch NIFImportErrors
        print "NIFTools NIF import script version %s" % (_SCRIPT_VERSION)
        Blender.Window.DrawProgressBar(0.0, "Initializing")
        # read the NIF file
        f = open(filename, "rb")
        version, user_version = NifFormat.getVersion(f)
        if version >= 0:
                msg("Nif file version: 0x%08X" % (version), 2)
                Blender.Window.DrawProgressBar(0.33, "Reading file")
                root_blocks = NifFormat.read(version, user_version, f, verbose = 0)
                Blender.Window.DrawProgressBar(0.66, "Importing data")
                for block in root_blocks:
                    # hack for corrupt better bodies meshes
                    root = block
                    for b in [b for b in block.tree() if isinstance(b, NifFormat.NiGeometry)]:
                        if b.isSkin():
                            if root in [c for c in b.skinInstance.skeletonRoot.children]:
                                root = b.skinInstance.skeletonRoot
                    msg("root block: %s" % (root.name), 3)
                    import_main(root, version)
        elif version == -1:
            raise NIFImportError("Unsupported NIF version.")
        else:
            raise NIFImportError("Not a NIF file.")
    except NIFImportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Import Failed")
        print 'NIFImportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return
    Blender.Window.DrawProgressBar(1.0, "Finished")



#
# Main import function.
#
def import_main(root_block, version):
    # scene info
    # used to control the progress bar
    global _SCENE, _CONFIG, _BLOCK_COUNT, _BLOCKS_READ, _READ_PROGRESS
    #_BLOCK_COUNT = NiObject_NumObjectsInMemory() 
    _READ_PROGRESS = 0.0
    _BLOCKS_READ = 0.0
    # preprocessing:

    # 4.0.0.2 nifs tend to be nasty: in the next piece of code
    # the skeleton roots are merged and a rest position is fixed
    # this does not quite work well for files that have non-identity
    # skindata transforms, which is common in oblivion;
    # but oblivion files have well behaved skeletons, so we only do this
    # for morrowind files
    if version == 0x04000002:
        for niBlock in root_block.tree():
            if not isinstance(niBlock, NifFormat.NiGeometry): continue
            if not niBlock.isSkin(): continue
            merged, failed = niBlock.mergeSkeletonRoots()
            if merged:
                print
                msg('reparented following blocks to skeleton root of ' + niBlock.name + ':', 2)
                msg([node.name for node in merged], 3)
            if failed:
                msg('WARNING: failed to reparent following blocks ' + niBlock.name + ':', 2)
                msg([node.name for node in failed], 3)

        # find reference geometries for each skeleton root, i.e. geometry with largest number of bones
        skelrootrefgeom = {}
        for niBlock in root_block.tree():
            if not isinstance(niBlock, NifFormat.NiGeometry): continue
            if not niBlock.isSkin(): continue
            skelroot = niBlock.skinInstance.skeletonRoot
            numbones = len(niBlock.skinInstance.bones)
            if skelrootrefgeom.has_key(skelroot):
                if numbones > len(skelrootrefgeom[skelroot].skinInstance.bones):
                    skelrootrefgeom[skelroot] = niBlock
            else:
                skelrootrefgeom[skelroot] = niBlock

        # fix rest pose
        for skelroot, niBlock in skelrootrefgeom.iteritems():
            merged, failed = niBlock.mergeBoneRestPositions(force = True)
            msg('fixing rest position of skeleton root ' + skelroot.name, 2)
            if merged:
                msg('merging rest position of ' + niBlock.name + ' with following geometries:', 2)
                msg([node.name for node in merged], 3)
            if failed: # should not happen if force = True
                msg('WARNING: failed to merge rest position of ' + niBlock.name + ' with following geometries:', 2)
                msg([node.name for node in failed], 3)
    
    # sets the root block parent to None, so that when crawling back the script won't barf
    root_block._parent = None
    
    # set the block parent through the tree, to ensure I can always move backward
    set_parents(root_block)
    
    # scale tree
    root_block.applyScale(_CONFIG['IMPORT_SCALE_CORRECTION'])
    
    # mark armature nodes and bones
    mark_armatures_bones(root_block)
    
    # read the NIF tree
    if not is_armature_root(root_block):
        msg("%s is not an armature root" % (root_block.name), 3)
        if root_block.children:
            # yes, we'll process all children of the root node
            # (this prevents us having to create an empty as a root)
            blocks = root_block.children
            # import the extras
            textkey = find_extra(root_block, NifFormat.NiTextKeyExtraData)
            if textkey:
                fb_textkey(textkey)
        else:
            # this fixes an issue with nifs where the first block is a NiTriShape
            blocks = [ root_block ]
        for niBlock in blocks:
            b_obj = read_branch(niBlock)
    else:
        b_obj = read_branch(root_block)
    # store bone matrix offsets for re-export
    if len(_BONES_EXTRA_MATRIX.keys()) > 0: fb_bonemat()
    # store original names for re-export
    if len(_NAMES) > 0: fb_fullnames()
    _SCENE.update(1) # do a full update to make sure all transformations get applied
    #fit_view()
    #_SCENE.getCurrentCamera()
    
# Reads the content of the current NIF tree branch to Blender recursively
def read_branch(niBlock):
    # used to control the progress bar
    global _BLOCK_COUNT, _BLOCKS_READ, _READ_PROGRESS
    _BLOCKS_READ += 1.0
    if (_BLOCKS_READ/(_BLOCK_COUNT+1.0)) >= (_READ_PROGRESS + 0.1):
        _READ_PROGRESS = _BLOCKS_READ/(_BLOCK_COUNT+1.0)
        Blender.Window.DrawProgressBar(_READ_PROGRESS, "Importing data")
    if niBlock:
        if isinstance(niBlock, NifFormat.NiTriBasedGeom):
            # it's a shape node
            msg("building mesh in read_branch",3)
            return fb_mesh(niBlock)
        elif isinstance(niBlock, NifFormat.NiNode):
            children = niBlock.children
            if children:
                # it's a parent node
                # import object + children
                if is_armature_root(niBlock):
                    # the whole bone branch is imported by fb_armature as well
                    b_obj = fb_armature(niBlock)
                    # now also do the meshes
                    read_armature_branch(b_obj, niBlock, niBlock)
                else:
                    # it's a grouping node
                    b_obj = fb_empty(niBlock)
                    b_children_list = []
                    children = niBlock.children
                    for child in children:
                        b_child_obj = read_branch(child)
                        if b_child_obj:
                            b_children_list.append(b_child_obj)
                    b_obj.makeParent(b_children_list)
                b_obj.setMatrix(fb_matrix(niBlock))
                # import the animations
                if _CONFIG['IMPORT_ANIMATION']:
                    set_animation(niBlock, b_obj)
                # import the extras
                textkey = find_extra(niBlock, NifFormat.NiTextKeyExtraData)
                if textkey:
                    fb_textkey(textkey)
                return b_obj
        # all else is currently discarded
        print "todo: add cameras, lights and particle systems"
        return None

def read_armature_branch(b_armature, niArmature, niBlock):
    """
    Reads the content of the current NIF tree branch to Blender
    recursively, as meshes parented to a given armature. Note that
    niBlock must have been imported previously as an armature, along
    with all its bones. This function only imports meshes.
    """
    # check if the block is non-null
    if niBlock:
        # bone or group node?
        # is it an AParentNode?
        # mesh?
        if isinstance(niBlock, NifFormat.NiTriBasedGeom):
            msg("building mesh %s in read_armature_branch" % (niBlock.name),3)
            return fb_mesh(niBlock)
        else:
            children = niBlock.children
            if children:
                # I need this to work out the transform in armaturespace
                armature_matrix_inverse = fb_global_matrix(niArmature)
                armature_matrix_inverse.invert()
                niArmature._invMatrix = armature_matrix_inverse
                for child in children:
                    b_mesh = read_armature_branch(b_armature, niArmature, child)
                    if b_mesh:
                        # add a vertex group if it's parented to a bone
                        par_bone = get_closest_bone(child)
                        if par_bone:
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
                                groupName = _NAMES[par_bone]
                                b_meshData.addVertGroup(groupName)
                                b_meshData.assignVertsToGroup(groupName, verts, 1.0, Blender.Mesh.AssignModes.REPLACE)
                        # make it parent of the armature
                        b_armature.makeParentDeform([b_mesh])
    # anything else: throw away
    return None



#
# Get unique name for an object, preserving existing names
#
def fb_name(niBlock, max_length=22):
    """
    Get unique name for an object, preserving existing names
    The maximum name length defaults to 22, since this is the
    maximum for Blender objects, but bone names can reach 32.
    The task of catching errors is left to the user
    """
    global _NAMES, _BLOCKS

    # find unique name for Blender to use
    uniqueInt = 0
    #niName = niBlock["Name"].asString()
    niName = niBlock.name
    # remove the "Tri " prefix; this will help when exporting the model again
    if niName[:4] == "Tri ":
        niName = niName[4:]
    shortName = niName[:max_length-1] # Blender has a rather small name buffer
    try:
        while Blender.Object.Get(name):
            shortName = '%s.%02d' % (niName[:max_length-4], uniqueInt)
            uniqueInt += 1
    except:
        pass
    # save mapping
    _NAMES[niBlock] = shortName
    _BLOCKS[shortName] = niBlock
    return shortName
    
# Retrieves a niBlock's transform matrix as a Mathutil.Matrix
def fb_matrix(niBlock):
    """Retrieves a niBlock's transform matrix as a Mathutil.Matrix"""
    return Matrix(*niBlock.getTransform().asList())

# Retrieves a block's global transform matrix
def fb_global_matrix(niBlock):
    """Retrieves a block's global transform matrix"""
    b_matrix = fb_matrix(niBlock)
    if niBlock._parent:
        return b_matrix * fb_global_matrix(niBlock._parent) # yay, recursion
    return b_matrix


# Decompose Blender transform matrix as a scale, rotation matrix, and translation vector
def decompose_srt(m):
    # get scale components
    #_EPSILON = _CONFIG["EPSILON"]
    b_scale_rot = m.rotationPart()
    b_scale_rot_T = Matrix(b_scale_rot)
    b_scale_rot_T.transpose()
    b_scale_rot_2 = b_scale_rot * b_scale_rot_T
    b_scale = Vector(b_scale_rot_2[0][0] ** 0.5,\
                     b_scale_rot_2[1][1] ** 0.5,\
                     b_scale_rot_2[2][2] ** 0.5)
    # and fix their sign
    if (b_scale_rot.determinant() < 0): b_scale.negate()
    # only uniform scaling
    assert(abs(b_scale[0]-b_scale[1])<_EPSILON)
    assert(abs(b_scale[1]-b_scale[2])<_EPSILON)
    b_scale = b_scale[0]
    # get rotation matrix
    b_rot = b_scale_rot * (1.0/b_scale)
    # get translation
    b_trans = m.translationPart()
    # done!
    return b_scale, b_rot, b_trans


    

# Creates and returns a grouping empty
def fb_empty(niBlock):
    global _SCENE
    shortName = fb_name(niBlock,22)
    b_empty = Blender.Object.New("Empty", shortName)
    b_empty.properties['longName'] = niBlock.name
    _SCENE.objects.link(b_empty)
    return b_empty

# Scans an armature hierarchy, and returns a whole armature.
# This is done outside the normal node tree scan to allow for positioning of
# the bones.
def fb_armature(niArmature):
    global _SCENE
    armature_name = fb_name(niArmature,22)
    armature_matrix_inverse = fb_global_matrix(niArmature)
    armature_matrix_inverse.invert()
    # store the matrix inverse within the niArmature, so that we won't have to recalculate it
    niArmature._invMatrix = armature_matrix_inverse
    b_armature = Blender.Object.New('Armature', armature_name)
    b_armatureData = Blender.Armature.Armature()
    b_armatureData.name = armature_name
    b_armatureData.makeEditable()
    b_armatureData.drawAxes = True
    b_armatureData.envelopes = False
    b_armatureData.vertexGroups = True
    b_armatureData.drawType = Blender.Armature.STICK
    #b_armatureData.drawType = Blender.Armature.ENVELOPE
    #b_armatureData.drawType = Blender.Armature.OCTAHEDRON
    b_armature.link(b_armatureData)
    b_armatureData.makeEditable()
    niChildBones = [child for child in niArmature.children if is_bone(child)]  
    for niBone in niChildBones:
        fb_bone(niBone, b_armature, b_armatureData, niArmature)
    b_armatureData.update()
    _SCENE.objects.link(b_armature)

    # The armature has been created in editmode,
    # now we are ready to set the bone keyframes.
    if _CONFIG['IMPORT_ANIMATION']:
        # create an action
        action = Blender.Armature.NLA.NewAction()
        action.setActive(b_armature)
        # go through all armature pose bones (http://www.elysiun.com/forum/viewtopic.php?t=58693)
        progress = 0.0
        bone_count = len(b_armature.getPose().bones)
        Blender.Window.DrawProgressBar(progress, 'Importing Animations')
        for bone_idx, (bone_name, b_posebone) in enumerate(b_armature.getPose().bones.items()):
            # denote progress
            if (bone_idx*1.0)/bone_count > (progress + 0.1):
                progress += 0.1
                Blender.Window.DrawProgressBar(progress, 'Animation: %s' % bone_name)
            #if (progress < 0.85): progress += 0.1
            #else: progress = 0.1
            
            msg('Importing animation for bone %s' % bone_name, 4)
            # get bind matrix (NIF format stores full transformations in keyframes,
            # but Blender wants relative transformations, hence we need to know
            # the bind position for conversion). Since
            # [ SRchannel 0 ]    [ SRbind 0 ]   [ SRchannel * SRbind         0 ]   [ SRtotal 0 ]
            # [ Tchannel  1 ] *  [ Tbind  1 ] = [ Tchannel  * SRbind + Tbind 1 ] = [ Ttotal  1 ]
            # with
            # 'total' the transformations as stored in the NIF keyframes,
            # 'bind' the Blender bind pose, and
            # 'channel' the Blender IPO channel,
            # it follows that
            # Schannel = Stotal / Sbind
            # Rchannel = Rtotal * inverse(Rbind)
            # Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
            niBone = _BLOCKS[bone_name]
            bone_bm = fb_matrix(niBone) # base pose
            niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = decompose_srt(bone_bm)
            niBone_bind_rot_inv = Matrix(niBone_bind_rot)
            niBone_bind_rot_inv.invert()
            niBone_bind_quat_inv = niBone_bind_rot_inv.toQuat()
            # we also need the conversion of the original matrix to the new bone matrix, say X,
            # B' = X * B
            # (with B' the Blender matrix and B the NIF matrix) because we need that
            # C' * B' = X * C * B
            # and therefore
            # C' = X * C * B * inverse(B') = X * C * inverse(X), where X = B' * inverse(B)
            # In detail:
            # [ SRX 0 ]   [ SRC 0 ]            [ SRX 0 ]
            # [ TX  1 ] * [ TC  1 ] * inverse( [ TX  1 ] ) =
            # [ SRX * SRC       0 ]   [ inverse(SRX)         0 ]
            # [ TX * SRC + TC   1 ] * [ -TX * inverse(SRX)   1 ] =
            # [ SRX * SRC * inverse(SRX)              0 ]
            # [ (TX * SRC + TC - TX) * inverse(SRX)   1 ]
            # Hence
            # SC' = SX * SC / SX = SC
            # RC' = RX * RC * inverse(RX)
            # TC' = (TX * SC * RC + TC - TX) * inverse(RX) / SX
            extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = decompose_srt(_BONES_EXTRA_MATRIX[niBone])
            extra_matrix_quat = extra_matrix_rot.toQuat()
            extra_matrix_rot_inv = Matrix(extra_matrix_rot)
            extra_matrix_rot_inv.invert()
            extra_matrix_quat_inv = extra_matrix_rot_inv.toQuat()
            # now import everything
            # ##############################
            kfc = find_controller(niBone, NifFormat.NiKeyframeController)
            if kfc:
                # get keyframe data
                kfd = kfc.data
                assert(isinstance(kfd, NifFormat.NiKeyframeData))
                translations = kfd.translations
                scales = kfd.scales
                # if we have translation keys, we make a dictionary of
                # rot_keys and scale_keys, this makes the script work MUCH faster
                # in most cases
                if translations:
                    scale_keys_dict = {}
                    rot_keys_dict = {}
                # add the keys
                msg('Scale keys...', 4)
                for scaleKey in scales.keys:
                    frame = 1+int(scaleKey.time * _FPS) # time 0.0 is frame 1
                    sizeVal = scaleKey.value
                    size = sizeVal / niBone_bind_scale # Schannel = Stotal / Sbind
                    b_posebone.size = Blender.Mathutils.Vector(size, size, size)
                    b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE]) # this is very slow... :(
                    # fill optimizer dictionary
                    if translations:
                        scale_keys_dict[frame] = size
                
                # detect the type of rotation keys
                rotationType = kfd.rotationType
                if rotationType == 4:
                    # uses xyz rotation
                    msg('Rotation keys...(euler)', 4)
                    xyzRotations = kfd.xyzRotations
                    for key in xyzRotations:
                        frame = 1+int(quatKey.time * _FPS) # time 0.0 is frame 1
                        keyVal = key.value
                        euler = Blender.Mathutils.Euler([keyVal.x, keyVal.y, keyVal.z])
                        quat = euler.toQuat()
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        quatVal = CrossQuats(niBone_bind_quat_inv, quatKey) # Rchannel = Rtotal * inverse(Rbind)
                        rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                        b_posebone.quat = rot
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
                        # fill optimizer dictionary
                        if translations:
                            rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot)                
                else:
                    # uses quaternions
                    msg('Rotation keys...(quaternions)', 4)
                    quaternionKeys = kfd.quaternionKeys
                    for key in quaternionKeys:
                        frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
                        keyVal = key.value
                        quat = Blender.Mathutils.Quaternion([keyVal.w, keyVal.x, keyVal.y, keyVal.z])
                        # beware, CrossQuats takes arguments in a counter-intuitive order:
                        # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                        quatVal = CrossQuats(niBone_bind_quat_inv, quat) # Rchannel = Rtotal * inverse(Rbind)
                        rot = CrossQuats(CrossQuats(extra_matrix_quat_inv, quatVal), extra_matrix_quat) # C' = X * C * inverse(X)
                        b_posebone.quat = rot
                        b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
                        # fill optimizer dictionary
                        if translations:
                            rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot)
    
                msg('Translation keys...', 4)
                for key in translations.keys:
                    frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
                    keyVal = key.value
                    trans = Blender.Mathutils.Vector(keyVal.x, keyVal.y, keyVal.z)
                    locVal = (trans - niBone_bind_trans) * niBone_bind_rot_inv * (1.0/niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                    # we need the rotation matrix at this frame (that's why we inserted the other keys first)
                    if rot_keys_dict:
                        try:
                            rot = rot_keys_dict[frame].toMatrix()
                        except KeyError:
                            # fall back on slow method
                            ipo = action.getChannelIpo(bone_name)
                            quat = Blender.Mathutils.Quaternion()
                            quat.x = ipo.getCurve('QuatX').evaluate(frame)
                            quat.y = ipo.getCurve('QuatY').evaluate(frame)
                            quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                            quat.w = ipo.getCurve('QuatW').evaluate(frame)
                            rot = quat.toMatrix()
                    else:
                        rot = Blender.Mathutils.Matrix([1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])
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
                    size = Blender.Mathutils.Matrix([sizeVal, 0.0, 0.0], [0.0, sizeVal, 0.0], [0.0, 0.0, sizeVal])
                    # now we can do the final calculation
                    loc = (extra_matrix_trans * size * rot + locVal - extra_matrix_trans) * extra_matrix_rot_inv * (1.0/extra_matrix_scale) # C' = X * C * inverse(X)
                    b_posebone.loc = loc
                    b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
                if translations:
                    del scale_keys_dict
                    del rot_keys_dict
    return b_armature


# Adds a bone to the armature in edit mode.
def fb_bone(niBlock, b_armature, b_armatureData, niArmature):
    global _BONES_EXTRA_MATRIX, _BONE_CORRECTION_MATRICES
    #_EPSILON = _CONFIG["EPSILON"]
    armature_matrix_inverse = niArmature._invMatrix
    # bone length for nubs and zero length bones
    nub_length = 5.0
    scale = _CONFIG["IMPORT_SCALE_CORRECTION"]
    realign_enabled = _CONFIG['REALIGN_BONES']
    # bone name
    bone_name = fb_name(niBlock, 32)
    niChildBones = [child for child in niBlock.children if is_bone(child)]
    if is_bone(niBlock):
        # create bones here...
        b_bone = Blender.Armature.Editbone()
        # head: get position from niBlock
        #armature_space_matrix = fb_global_matrix(niBlock) * armature_matrix_inverse
        armature_space_matrix = getattr(niBlock, '_bindMatrix', fb_global_matrix(niBlock) * armature_matrix_inverse)
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
            m_correction = find_correction_matrix(niBlock, niArmature)
            #child_matrices = [(fb_global_matrix(child) * armature_matrix_inverse) for child in niChildBones]
            child_matrices = [getattr(child, '_bindMatrix', fb_global_matrix(child) * armature_matrix_inverse) for child in niChildBones]
            b_bone_tail_x = sum([child_matrix[3][0] for child_matrix in child_matrices]) / len(child_matrices)
            b_bone_tail_y = sum([child_matrix[3][1] for child_matrix in child_matrices]) / len(child_matrices)
            b_bone_tail_z = sum([child_matrix[3][2] for child_matrix in child_matrices]) / len(child_matrices)
            # checking bone length
            dx = b_bone_head_x - b_bone_tail_x
            dy = b_bone_head_y - b_bone_tail_y
            dz = b_bone_head_z - b_bone_tail_z
            is_zero_length = abs(dx + dy + dz) * 200 < _EPSILON
        elif realign_enabled:
            # the correction matrix value is based on the children's head position
            # If these are missing I just set it as the same as the parent's
            m_correction = find_correction_matrix(niBlock._parent, niArmature)
        
        if is_zero_length:
            # this is a 0 length bone, to avoid it being removed I set a default minimum length
            if realign_enabled or not is_bone(niBlock._parent):
                # no parent bone, or bone is realigned with correction. I just set one random direction.
                b_bone_tail_x = b_bone_head_x + (nub_length * scale)
            else:
                # to keep things neat if bones aren't realigned on import I try and orient it as the vector between this
                # bone's head and the parent's tail
                parent_tail = b_armatureData.bones[_NAMES[niBlock._parent]].tail
                dx = b_bone_head_x - parent_tail[0]
                dy = b_bone_head_y - parent_tail[1]
                dz = b_bone_head_z - parent_tail[2]
                if abs(dx + dy + dz) * 200 < _EPSILON:
                    # no offset from the parent, we follow the parent's orientation
                    parent_head = b_armatureData.bones[_NAMES[niBlock._parent]].head
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
        
        if realign_enabled:
            # applies the corrected matrix explicitly
            b_bone.matrix = m_correction.resize4x4() * armature_space_matrix
                
        # set bone name and store the niBlock for future reference
        b_armatureData.bones[bone_name] = b_bone
        # calculate bone difference matrix; we will need this when importing animation
        old_bone_matrix_inv = Blender.Mathutils.Matrix(armature_space_matrix)
        old_bone_matrix_inv.invert()
        new_bone_matrix = Blender.Mathutils.Matrix(b_bone.matrix)
        new_bone_matrix.resize4x4()
        new_bone_matrix[3][0] = b_bone_head_x
        new_bone_matrix[3][1] = b_bone_head_y
        new_bone_matrix[3][2] = b_bone_head_z
        # stores any correction or alteration applied to the bone matrix
        _BONES_EXTRA_MATRIX[niBlock] = new_bone_matrix * old_bone_matrix_inv # new * inverse(old)
        # set bone children
        for niBone in niChildBones:
            b_child_bone =  fb_bone(niBone, b_armature, b_armatureData, niArmature)
            b_child_bone.parent = b_bone
        return b_bone
    return None


def find_correction_matrix(niBlock, niArmature):
    """
    Returns the correction matrix for a bone
    """
    armature_matrix_inverse = niArmature._invMatrix
    m_correction = _IDENTITY44.rotationPart()
    if _CONFIG['REALIGN_BONES'] and is_bone(niBlock):
        armature_space_matrix = getattr(niBlock, '_bindMatrix', fb_global_matrix(niBlock) * armature_matrix_inverse)
        niChildBones = [child for child in niBlock.children if is_bone(child)]
        (sum_x, sum_y, sum_z, dummy) = armature_space_matrix[3]
        if len(niChildBones) > 0:
            child_local_matrices = [fb_matrix(child) for child in niChildBones]
            sum_x = sum([cm[3][0] for cm in child_local_matrices])
            sum_y = sum([cm[3][1] for cm in child_local_matrices])
            sum_z = sum([cm[3][2] for cm in child_local_matrices])
        listXYZ = [int(c * 200) for c in (sum_x, sum_y, sum_z, -sum_x, -sum_y, -sum_z)]
        idx_correction = listXYZ.index(max(listXYZ))
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
            m_correction = _BONE_CORRECTION_MATRICES[idx_correction]
    return m_correction


def fb_texture(niSourceTexture):
    """
    Returns a Blender Texture object, and stores it in the global TEXTURES dictionary
    """
    global _TEXTURES, _CONFIG
    
    if niSourceTexture:
        
        try:
            return _TEXTURES[niSourceTexture]
        except:
            pass
        
        b_image = None
        
        if niSourceTexture.useExternal:
            # the texture uses an external image file
            fn = niSourceTexture.fileName
            fn = fn.replace( '\\', Blender.sys.sep )
            fn = fn.replace( '/', Blender.sys.sep )
            # go searching for it
            textureFile = None
            searchPathList = [_CONFIG["NIF_IMPORT_PATH"], _CONFIG["BASE_TEXTURE_FOLDER"]] + _CONFIG["TEXTURE_SEARCH_PATH"]
            # if it looks like a Morrowind style path, use common sense to guess texture path
            meshes_index = _CONFIG["NIF_IMPORT_PATH"].lower().find("meshes")
            if meshes_index != -1:
                searchPathList.append(_CONFIG["NIF_IMPORT_PATH"][:meshes_index] + 'textures')
            for texdir in searchPathList:
                texdir = texdir.replace( '\\', Blender.sys.sep )
                texdir = texdir.replace( '/', Blender.sys.sep )
                 # now a little trick, to satisfy many Morrowind mods
                if (fn[:9].lower() == 'textures' + Blender.sys.sep) and (texdir[-9:].lower() == Blender.sys.sep + 'textures'):
                    tex = Blender.sys.join( texdir, fn[9:] ) # strip one of the two 'textures' from the path
                else:
                    tex = Blender.sys.join( texdir, fn )
                msg("Searching %s" % tex, 3)
                if Blender.sys.exists(tex) == 1:
                    # tries to load the file
                    b_image = Blender.Image.Load(tex)
                    # Blender 2.41 will return an image object even if the file format isn't supported,
                    # so to check if the image is actually loaded I need to force an error, hence the
                    # dummy = b_image.size line.
                    try:
                        dummy = b_image.size
                        # file format is supported
                        msg( "Found %s" % tex, 3 )
                        del dummy
                        break
                    except:
                        b_image = None # not supported, delete image object
                # file format is not supported or file was not found, therefore
                # we try to load alternative texture
                base=tex[:-4]
                for ext in ('.DDS','.dds','.PNG','.png','.TGA','.tga','.BMP','.bmp','.JPG','.jpg'):
                    alt_tex = base+ext
                    if Blender.sys.exists(alt_tex) == 1:
                        b_image = None
                        try:
                            b_image = Blender.Image.Load(alt_tex)
                            dummy = b_image.size
                            msg( "Found alternate %s" % alt_tex, 3 )
                            del dummy
                            break
                        except:
                            b_image = None # not supported, delete image object
            if b_image == None:
                msg("Texture %s not found and no alternate available" % fn, 2)
                b_image = Blender.Image.New(tex, 1, 1, 24) # create a stub
                b_image.filename = tex
        else:
            # the texture image is packed inside the nif -> extract it
            niPixelData = niSourceTexture.pixelData
            
            # we only load the first mipmap
            width = niPixelData.mipmaps[0].width
            height = niPixelData.mipmaps[0].height
            
            if niPixelData.pixelFormat == NifFormat.PixelFormat.PX_FMT_RGBA8:
                bpp = 24
            elif niPixelData.pixelFormat == NifFormat.PixelFormat.PX_FMT_RGB8:
                bpp = 32
            else:
                bpp = None

            if bpp == None: msg("unknown pixel format (%i), cannot extract texture"%niPixelData.pixelFormat, 1)

            if bpp != None:
                b_image = Blender.Image.New( "TexImg", width, height, bpp )
                
                pixels = niPixelData.pixelData.data
                pixeloffset = 0
                a = 0xff
                for y in xrange( height ):
                    Blender.Window.DrawProgressBar( float( y + 1 ) / float( height ), "Image Extraction")
                    for x in xrange( width ):
                        # TODO delegate color extraction to generator in PyFFI/NIF
                        r = pixels[pixeloffset]
                        g = pixels[pixeloffset+1]
                        b = pixels[pixeloffset+2]
                        if bpp == 32:
                            a = pixels[pixeloffset+3]
                        b_image.setPixelI( x, (height-1)-y, ( r, g, b, a ) )
                        pixeloffset += bpp/8
        
        if b_image != None:
            # create a texture using the loaded image
            b_texture = Blender.Texture.New()
            b_texture.setType( 'Image' )
            b_texture.setImage( b_image )
            b_texture.imageFlags |= Blender.Texture.ImageFlags.INTERPOL
            b_texture.imageFlags |= Blender.Texture.ImageFlags.MIPMAP
            _TEXTURES[niSourceTexture] = b_texture
            return b_texture
        else:
            _TEXTURES[niSourceTexture] = None
            return None
    return None



# Creates and returns a material
def fb_material(matProperty, textProperty, alphaProperty, specProperty):
    global _MATERIALS
    #_EPSILON = _CONFIG["EPSILON"]
    # First check if material has been created before.
    try:
        material = _MATERIALS[(matProperty, textProperty, alphaProperty, specProperty)]
        return material
    except KeyError:
        pass
    # use the material property for the name, other properties usually have
    # no name
    name = fb_name(matProperty)
    material = Blender.Material.New(name)
    # Sets the material colors
    # Specular color
    spec = matProperty.specularColor
    material.setSpecCol([spec.r, spec.g, spec.b])
    material.setSpec(1.0) # Blender multiplies specular color with this value
    # Diffuse color
    diff = matProperty.diffuseColor
    material.setRGBCol([diff.r, diff.g, diff.b])
    # Ambient & emissive color
    # We assume that ambient & emissive are fractions of the diffuse color.
    # If it is not an exact fraction, we average out.
    amb = matProperty.ambientColor
    emit = matProperty.emissiveColor
    b_amb = 0.0
    b_emit = 0.0
    b_n = 0
    if (diff.r > _EPSILON):
        b_amb += amb.r/diff.r
        b_emit += emit.r/diff.r
        b_n += 1
    if (diff.g > _EPSILON):
        b_amb += amb.g/diff.g
        b_emit += emit.g/diff.g
        b_n += 1
    if (diff.b > _EPSILON):
        b_amb += amb.b/diff.b
        b_emit += emit.b/diff.b
        b_n += 1
    if (b_n > 0):
        b_amb /= b_n
        b_emit /= b_n
    if (b_amb > 1.0): b_amb = 1.0
    if (b_emit > 1.0): b_emit = 1.0
    material.setAmb(b_amb)
    material.setEmit(b_emit)
    # glossiness
    glossiness = matProperty.glossiness
    hardness = int(glossiness * 4) # just guessing really
    if hardness < 1: hardness = 1
    if hardness > 511: hardness = 511
    material.setHardness(hardness)
    # Alpha
    alpha = matProperty.alpha
    material.setAlpha(alpha)
    baseTexture = None
    glowTexture = None
    if textProperty:
        baseTextureDesc = textProperty.baseTexture
        if baseTextureDesc:
            baseTexture = fb_texture(baseTextureDesc.source)
            if baseTexture:
                # Sets the texture to use face UV coordinates.
                texco = Blender.Texture.TexCo.UV
                # Maps the texture to the base color channel.
                mapto = Blender.Texture.MapTo.COL
                # Sets the texture for the material
                material.setTexture(0, baseTexture, texco, mapto)
                mbaseTexture = material.getTextures()[0]
        glowTextureDesc = textProperty.glowTexture
        if glowTextureDesc:
            glowTexture = fb_texture(glowTextureDesc.source)
            if glowTexture:
                # glow maps use alpha from rgb intensity
                glowTexture.imageFlags |= Blender.Texture.ImageFlags.CALCALPHA
                # Sets the texture to use face UV coordinates.
                texco = Blender.Texture.TexCo.UV
                # Maps the texture to the base color channel.
                mapto = Blender.Texture.MapTo.COL | Blender.Texture.MapTo.EMIT
                # Sets the texture for the material
                material.setTexture(1, glowTexture, texco, mapto)
                mglowTexture = material.getTextures()[1]
    # check transparency
    if alphaProperty:
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
    if not specProperty:
        # no specular property: specular color is ignored
        # we do this by setting specularity zero
        material.setSpec(0.0)

    _MATERIALS[(matProperty, textProperty, alphaProperty, specProperty)] = material
    return material

# Creates and returns a raw mesh
def fb_mesh(niBlock):
    global _SCENE
    assert(isinstance(niBlock, NifFormat.NiTriBasedGeom))
    # Mesh name -> must be unique, so tag it if needed
    b_name = fb_name(niBlock, 22)
    b_meshData = Blender.Mesh.New(b_name)
    b_meshData.properties['longName'] = niBlock.name
    #b_mesh = _SCENE.objects.new(b_meshData, b_name)
    b_mesh = Blender.Object.New("Mesh", b_name)
    b_mesh.link(b_meshData)
    
    # Sets the mesh as one-sided. This fixes some issue with normals
    b_meshData.mode = 0
   
    _SCENE.objects.link(b_mesh)
    
    # Mesh hidden flag
    if niBlock.flags & 1 == 1:
        b_mesh.setDrawType(2) # hidden: wire
    else:
        b_mesh.setDrawType(4) # not hidden: shaded

    # Mesh transform matrix, sets the transform matrix for the object.
    meshBindMatrix = getattr(niBlock, '_bindMatrix', fb_matrix(niBlock))
    b_mesh.setMatrix(meshBindMatrix)
    
    # Mesh geometry data. From this I can retrieve all geometry info
    niData = niBlock.data
    if not niData:
        raise NIFImportError("no ShapeData returned. Node name: %s " % b_name)
        
    # Vertices
    verts = niData.vertices
    
    # Faces
    tris = []
    if isinstance(niData, NifFormat.NiTriShapeData):
        tris = niData.triangles
    elif isinstance(niData, NifFormat.NiTriStripsData):
        msg("---loading tristrips",3)
        for face in niData.getTriangles():
            tri = NifFormat.Triangle()
            tri.v1 = face[0]
            tri.v2 = face[1]
            tri.v3 = face[2]
            tris.append(tri)
    
    # "Sticky" UV coordinates. these are transformed in Blender UV's
    # only the first UV set is loaded right now
    uvco = niData.uvSets
        
    # Vertex normals
    norms = niData.normals

    v_map = [0]*len(verts) # pre-allocate memory, for faster performance
    print "todo: add option for seams import"
    _SEAMS_IMPORT = True
    if not _SEAMS_IMPORT:
        # Fast method: don't care about any seams!
        for i, v in enumerate(verts):
            v_map[i] = i # NIF vertex i maps to blender vertex i
            b_meshData.verts.extend(v.x, v.y, v.z) # add the vertex
            # adds normal info if present.
            # Blender doesn't calculate these quite properly when importing strips
            if norms:
                mv = b_meshData.verts[i]
                n = norms[i]
                mv.no = Blender.Mathutils.Vector(n.x, n.y, n.z)
    else:
        # Slow method, but doesn't introduce unwanted cracks in UV seams:
        # Construct vertex map to get unique vertex / normal pair list.
        # We use a Python dictionary to remove doubles and to keep track of indices.
        # While we are at it, we also add vertices while constructing the map.
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
            if not n_map_k:
                # not added: new vertex / normal pair
                n_map[k] = i         # unique vertex / normal pair with key k was added, with NIF index i
                v_map[i] = b_v_index # NIF vertex i maps to blender vertex b_v_index
                b_meshData.verts.extend(v.x, v.y, v.z) # add the vertex
                # adds normal info if present.
                # Blender doesn't calculate these quite properly when importing strips
                if norms:
                    mv = b_meshData.verts[b_v_index]
                    n = norms[i]
                    mv.no = Blender.Mathutils.Vector(n.x, n.y, n.z)
                b_v_index += 1
            else:
                # already added
                v_map[i] = v_map[n_map_k] # NIF vertex i maps to Blender v_map[vertex n_map_nk]
        # release memory
        del n_map

    # Adds the faces to the mesh
    f_map = [None]*len(tris)
    b_f_index = 0
    for i, f in enumerate(tris):
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
    vcol = niData.vertexColors
    
    if vcol: # empty list is false
        b_meshData.vertexColors = 1
        for i, f in enumerate(tris):
            if f_map[i] == None: continue
            b_face = b_meshData.faces[f_map[i]]
            # make sure we get the order right
            if (v_map[f.v1] == b_face.verts[0].index):
                v1_index = 0
                v2_index = 1
                v3_index = 2
            elif (v_map[f.v1] == b_face.verts[1].index):
                v3_index = 0
                v1_index = 1
                v2_index = 2
            elif (v_map[f.v1] == b_face.verts[2].index):
                v2_index = 0
                v3_index = 1
                v1_index = 2
            else:
                raise NIFImportError("Invalid face index (BUG?)")
            # now set the vertex colors
            vc = vcol[f.v1]
            b_face.col[v1_index].r = int(vc.r * 255)
            b_face.col[v1_index].g = int(vc.g * 255)
            b_face.col[v1_index].b = int(vc.b * 255)
            b_face.col[v1_index].a = int(vc.a * 255)
            vc = vcol[f.v2]
            b_face.col[v2_index].r = int(vc.r * 255)
            b_face.col[v2_index].g = int(vc.g * 255)
            b_face.col[v2_index].b = int(vc.b * 255)
            b_face.col[v2_index].a = int(vc.a * 255)
            vc = vcol[f.v3]
            b_face.col[v3_index].r = int(vc.r * 255)
            b_face.col[v3_index].g = int(vc.g * 255)
            b_face.col[v3_index].b = int(vc.b * 255)
            b_face.col[v3_index].a = int(vc.a * 255)
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

    for uvSet in uvco:
        # Sets the face UV's for the mesh on. The NIF format only supports vertex UV's,
        # but Blender only allows explicit editing of face UV's, so I'll load vertex UV's like face UV's
        b_meshData.faceUV = 1
        b_meshData.vertexUV = 0
        for i, f in enumerate(tris):
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
                    uv=uvSet[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            elif (v_map[f.v1] == b_meshData.faces[f_map[i]].verts[1].index):
                # vertex 3 was added first
                for v in (f.v3, f.v1, f.v2):
                    uv=uvSet[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            elif (v_map[f.v1] == b_meshData.faces[f_map[i]].verts[2].index):
                # vertex 2 was added first
                for v in (f.v2, f.v3, f.v1):
                    uv=uvSet[v]
                    uvlist.append(Vector(uv.u, 1.0 - uv.v))
                b_meshData.faces[f_map[i]].uv = tuple(uvlist)
            else:
                raise NIFImportError("Invalid face index (BUG?)")
    
    # Sets the material for this mesh. NIF files only support one material for each mesh.
    matProperty = find_property(niBlock, NifFormat.NiMaterialProperty)
    if matProperty:
        # Texture
        textProperty = None
        if uvco:
            textProperty = find_property(niBlock, NifFormat.NiTexturingProperty)
        
        # Alpha
        alphaProperty = find_property(niBlock, NifFormat.NiAlphaProperty)
        
        # Specularity
        specProperty = find_property(niBlock, NifFormat.NiSpecularProperty)
        
        # create material and assign it to the mesh
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
    skinInstance = niBlock.skinInstance
    if skinInstance:
        skinData = skinInstance.data
        bones = skinInstance.bones
        boneWeights = skinData.boneList
        for idx, bone in enumerate(bones):
            vertexWeights =boneWeights[idx].vertexWeights
            groupName = _NAMES[bone]
            b_meshData.addVertGroup(groupName)
            for skinWeight in vertexWeights:
                vert = skinWeight.index
                weight = skinWeight.weight
                b_meshData.assignVertsToGroup(groupName, [v_map[vert]], weight, Blender.Mesh.AssignModes.REPLACE)
    
    # this doesn't quite work as well as it ought to
    #b_meshData.calcNormals() # let Blender calculate vertex normals

    # new implementation, uses Mesh instead
    if _CONFIG['IMPORT_ANIMATION']:
        morphCtrl = find_controller(niBlock, NifFormat.NiGeomMorpherController)
        if morphCtrl:
            morphData = morphCtrl.data
            if morphData.numMorphs:
                # insert base key at frame 1
                b_meshData.insertKey( 1, 'absolute' )
                baseverts = morphData.morphs[0].vectors
                b_ipo = Blender.Ipo.New( 'Key' , 'KeyIpo' )
                b_meshData.key.ipo = b_ipo
                for idxMorph in xrange(1, morphData.numMorphs):
                    morphverts = morphData.morphs[idxMorph].vectors
                    # for each vertex calculate the key position from base pos + delta offset
                    for i in xrange(morphData.numVertices):
                        x = baseverts[i].x
                        y = baseverts[i].y
                        z = baseverts[i].z
                        dx = morphverts[i].x
                        dy = morphverts[i].y
                        dz = morphverts[i].z
                        b_meshData.verts[v_map[i]].co[0] = x + dx
                        b_meshData.verts[v_map[i]].co[1] = y + dy
                        b_meshData.verts[v_map[i]].co[2] = z + dz
                    # update the mesh and insert key
                    b_meshData.insertKey(idxMorph, 'relative')
                    # set up the ipo key curve
                    b_curve = b_ipo.addCurve('Key %i' % idxMorph)
                    # dunno how to set up the bezier triples -> switching to linear instead
                    b_curve.setInterpolation('Linear')
                    # select extrapolation
                    if ( morphCtrl.flags == 0x000c ):
                        b_curve.setExtrapolation( 'Constant' )
                    elif ( morphCtrl.flags == 0x0008 ):
                        b_curve.setExtrapolation( 'Cyclic' )
                    else:
                        msg( 'dunno which extrapolation to use: using constant instead', 2 )
                        b_curve.setExtrapolation( 'Constant' )
                    # set up the curve's control points
                    morphkeys = morphData.morphs[idxMorph].keys
                    for key in morphkeys:
                        x =  key.value
                        frame =  1+int(key.time * _FPS)
                        b_curve.addBezier( ( frame, x ) )
                    # finally: return to base position
                    for i in xrange(morphData.numVertices):
                        x = baseverts[i].x
                        y = baseverts[i].y
                        z = baseverts[i].z
                        b_meshData.verts[v_map[i]].co[0] = x
                        b_meshData.verts[v_map[i]].co[1] = y
                        b_meshData.verts[v_map[i]].co[2] = z
                # assign ipo to mesh
                
    return b_mesh



# import animation groups
def fb_textkey(niBlock):
    """
    Stores the text keys that define animation start and end in a text buffer,
    so that they can be re-exported.
    Since the text buffer is cleared on each import only the last import will be exported
    correctly
    """
    if isinstance(niBlock, NifFormat.NiTextKeyExtraData) and niBlock.textKeys:
        # get animation text buffer, and clear it if it already exists
        try:
            animtxt = [txt for txt in Blender.Text.Get() if txt.getName() == "Anim"][0]
            animtxt.clear()
        except:
            animtxt = Blender.Text.New("Anim")
        
        frame = 1
        for key in niBlock.textKeys:
            newkey = str(key.value).replace('\r\n', '/').rstrip('/')
            frame = 1 + int(key.time * _FPS) # time 0.0 is frame 1
            animtxt.write('%i/%s\n'%(frame, newkey))
        
        # set start and end frames
        _SCENE.getRenderingContext().startFrame(1)
        _SCENE.getRenderingContext().endFrame(frame)
    
def fb_bonemat():
    """
    Stores correction matrices in a text buffer so that the original alignment can be re-exported.
    In order for this to work it is necessary to mantain the imported names unaltered
    Since the text buffer is cleared on each import only the last import will be exported
    correctly
    """
    try:
        bonetxt = [txt for txt in Blender.Text.Get() if txt.getName() == "BoneExMat"][0]
        bonetxt.clear()
    except:
        bonetxt = Blender.Text.New("BoneExMat")
    for niBone in _BONES_EXTRA_MATRIX.keys():
        ln=''
        for row in _BONES_EXTRA_MATRIX[niBone]:
            ln='%s;%s,%s,%s,%s' % (ln, row[0],row[1],row[2],row[3])
        # print '%s/%s/%s\n' % (a, b, ln[1:])
        bonetxt.write('%s/%s\n' % (niBone.name, ln[1:]))
    

def fb_fullnames():
    """
    Stores the original, long object names so that they can be re-exported.
    In order for this to work it is necessary to mantain the imported names unaltered.
    Since the text buffer is cleared on each import only the last import will be exported
    correctly
    """
    global _NAMES
    # get the names text buffer
    try:
        namestxt = [txt for txt in Blender.Text.Get() if txt.getName() == "FullNames"][0]
        namestxt.clear()
    except:
        namestxt = Blender.Text.New("FullNames")
    for niBlock in _NAMES.keys():
        namestxt.write('%s;%s\n'% (_NAMES[niBlock], niBlock.name))
    
# find a controller
def find_controller(niBlock, controllerType):
    """
    Finds a controller
    """
    ctrl = niBlock.controller
    while ctrl:
        if isinstance(ctrl, controllerType):
            break
        ctrl = ctrl.nextController
    return ctrl

# find a property
def find_property(niBlock, propertyType):
    """
    Finds a controller
    """
    prop = [p for p in niBlock.properties if isinstance(p, propertyType)]
    if prop:
        return prop[0]
    return None


# find extra data
def find_extra(niBlock, extratype):
    # pre-10.x.x.x system: extra data chain
    extra = niBlock.extraData
    while extra:
        if isinstance(extra, extratype):
            break
        extra = extra.nextExtraData
    if extra:
        return extra

    # post-10.x.x.x system: extra data list
    for extra in niBlock.extraDataList:
        if isinstance(extra, extratype):
            return extra
    return None

# sets the parent block recursively through the tree, to allow me to crawl back as needed
def set_parents(niBlock):
    if isinstance(niBlock, NifFormat.NiNode):
        # list of non-null children
        children = [child for child in niBlock.children if child]
        for child in children:
            child._parent = niBlock
            set_parents(child)

# mark armatures and bones by peeking into NiSkinInstance blocks
# also stores the bind position matrix for correct import of skinning info
def mark_armatures_bones(niBlock):
    global _ARMATURES 

    # search for all NiTriShape or NiTriStrips blocks...
    if isinstance(niBlock, NifFormat.NiTriBasedGeom):
        # yes, we found one, get its skin instance
        if niBlock.isSkin():
            msg("skin found on block '%s'" % niBlock.name,3)
            # it has a skin instance, so get the skeleton root
            # which is an armature only if it's not a skinning influence
            # so mark the node to be imported as an armature
            skininst = niBlock.skinInstance
            skindata = skininst.data
            skelroot = skininst.skeletonRoot
            if not _ARMATURES.has_key(skelroot):
                if _ARMATURES.keys():
                    raise NIFImportError('models with multiple skeleton roots not yet supported')
                _ARMATURES[skelroot] = []
                msg("'%s' is an armature" % skelroot.name,3)
            
            # stores the mesh bind position for later use
            # note that this matrix is relative to the skeleton root
            #geomBindMatrix = Matrix(*(skindata.getTransform().getInverse().asList()))
            #geomBindMatrix = Matrix(*((skindata.getTransform() * niBlock.getTransform(skelroot)).asList()))
            geomBindMatrix = Matrix(*(niBlock.getTransform(skelroot).asList()))
            niBlock._bindMatrix = geomBindMatrix
            
            #if geomBindMatrix != _IDENTITY44:
            
            #is_identity = True
            #for row in range(4):
            #    for col in range(4):
            #        if geomBindMatrix[row][col] - _IDENTITY44[row][col] > _EPSILON:
            #            is_identity = False
            #if not is_identity:
            #    print 'geometry bind matrix is not identity'
            #    print geomBindMatrix
            #geomBindMatrixInverse = Matrix(geomBindMatrix)
            #geomBindMatrixInverse.invert()
            for i, boneBlock in enumerate(skininst.bones):
                skinbonedata = skindata.boneList[i]
                boneBindMatrix = Matrix(*((skindata.getTransform() * skinbonedata.getTransform()).getInverse().asList()))
                # sets the rest position for the affected skin
                boneBlock._bindMatrix = boneBindMatrix
                # add them, if we haven't already
                if not boneBlock in _ARMATURES[skelroot]:
                    _ARMATURES[skelroot].append(boneBlock)
                    msg("'%s' is a bone of armature '%s'" % (boneBlock.name, skelroot.name), 3)
                else:
                    # ensure that rest position is unique
                    # ... hmmm Blender docs say matrix comparison works
                    # but apparently it doesn't so commented out for now ...
                    #if Matrix(*boneRestPos.asList()) != boneBlock._bindMatrix:
                    tmp = 0.0
                    for v in boneBindMatrix - boneBlock._bindMatrix:
                        tmp += v.length
                    if tmp > _EPSILON:
                        print 'warning for bone', boneBlock.name
                        print Matrix(*boneRestPos.asList())
                        print boneBlock._bindMatrix
                        print 'multiple geometries influenced by the same bone with different rest poses'
                # now we "attach" the bone to the armature:
                # we make sure all NiNodes from this bone all the way
                # down to the armature NiNode are marked as bones
                complete_bone_tree(boneBlock, skelroot)

    # heuristic for importing skeleton.nif files: mark Bip01 as armature
    if isinstance(niBlock, NifFormat.NiNode) and niBlock.name == "Bip01":
        if not _ARMATURES.has_key(niBlock):
            if _ARMATURES.keys():
                raise NIFImportError('models with multiple skeleton roots not yet supported')
            _ARMATURES[niBlock] = []
        # add bones
        for bone in niBlock.tree():
            if not isinstance(bone, NifFormat.NiNode): continue
            if bone.name[:6] == "Bip01 ":
                _ARMATURES[niBlock].append(bone)
                complete_bone_tree(bone, niBlock)

    # continue down the tree
    for child in niBlock.getRefs():
        mark_armatures_bones(child)

# this function helps to make sure that the bones actually form a tree,
# all the way down to the armature node
# just call it on all bones of a skin instance
def complete_bone_tree(bone, skelroot):
    global _ARMATURES
    # we must already have marked this one as a bone
    assert _ARMATURES.has_key(skelroot) # debug
    assert bone in _ARMATURES[skelroot] # debug
    # get the node parent, this should be marked as an armature or as a bone
    boneparent = bone._parent
    if boneparent != skelroot:
        # parent is not the skeleton root
        if not boneparent in _ARMATURES[skelroot]:
            # neither is it marked as a bone: so mark the parent as a bone
            _ARMATURES[skelroot].append(boneparent)
            # store the coordinates for realignement autodetection 
            msg("'%s' is a bone of armature '%s'"%(boneparent.name, skelroot.name),3)
        # now the parent is marked as a bone
        # recursion: complete the bone tree,
        # this time starting from the parent bone
        complete_bone_tree(boneparent, skelroot)

# Tests a NiNode to see if it's a bone.
def is_bone(niBlock):
    if not niBlock : return False
    if niBlock.name[:6] == "Bip01 ": return True # heuristics
    for bones in _ARMATURES.values():
        if niBlock in bones:
            return True
    return False

# Tests a block to see if it's an armature.
def is_armature_root(niBlock):
    if isinstance(niBlock, NifFormat.NiNode):
        return  _ARMATURES.has_key(niBlock)
    return False
    
# Detect closest bone ancestor.
def get_closest_bone(niBlock):
    par = niBlock._parent
    while par:
        if is_bone(par):
            return par
        par = par._parent
    return par


# Main KFM import function. (BROKEN)
def import_kfm(filename):
    Blender.Window.DrawProgressBar(0.0, "Initializing")
    try: # catch NIFImportErrors
        # read the KFM file
        kfm = Kfm()
        ver = kfm.Read(filename)
        if ( ver == VER_INVALID ):
            raise NIFImportError("Not a KFM file.")
        elif ( ver == VER_UNSUPPORTED ):
            raise NIFImportError("Unsupported KFM version.")
        # import the NIF tree
        import_main(kfm.MergeActions(Blender.sys.dirname(filename)))
    except NIFImportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Import Failed")
        print 'NIFImportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return

    Blender.Window.DrawProgressBar(1.0, "Finished")






# Loads basic animation info for this object
def set_animation(niBlock, b_obj):
    progress = 0.1
    kfc = find_controller(niBlock, NifFormat.NiKeyframeController)
    if kfc and kfc.data:
        # create an Ipo for this object
        b_ipo = b_obj.getIpo()
        if b_ipo == None:
            b_ipo = Blender.Ipo.New('Object', b_obj.name)
            b_obj.setIpo(b_ipo)
        # denote progress
        Blender.Window.DrawProgressBar(progress, "Animation")
        if (progress < 0.85): progress += 0.1
        else: progress = 0.1
        # get keyframe data
        kfd = kfc.data
        assert(isinstance(kfd, NifFormat.NiKeyframeData))
        #get the animation keys
        translations = kfd.translations
        scales = kfd.scales
        # add the keys
        msg('Scale keys...', 4)
        for key in scales.keys:
            frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            size = key.value
            b_obj.SizeX = size
            b_obj.SizeY = size
            b_obj.SizeZ = size
            b_obj.insertIpoKey(Blender.Object.SIZE)

        # detect the type of rotation keys
        rotationType = kfd.rotationType
        if rotationType == 4:
            # uses xyz rotation
            xyzRotations = kfd.xyzRotations
            msg('Rotation keys...(euler)', 4)
            for key in xyzRotations:
                frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                keyValue = key.value
                rot = (keyValue.x, keyValue.y, keyValue.z)
                b_obj.RotX = rot.x * _R2D
                b_obj.RotY = rot.y * _R2D
                b_obj.RotZ = rot.z * _R2D
                b_obj.insertIpoKey(Blender.Object.ROT)           
        else:
            # uses quaternions
            quaternionKeys = kfd.quaternionKeys
            msg('Rotation keys...(quaternions)', 4)
            for key in quaternionKeys:
                frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                keyValue = key.value
                rot = Blender.Mathutils.Quaternion(keyValue.w, keyValue.x, keyValue.y, keyValue.z).toEuler()
                b_obj.RotX = rot.x * _R2D
                b_obj.RotY = rot.y * _R2D
                b_obj.RotZ = rot.z * _R2D
                b_obj.insertIpoKey(Blender.Object.ROT)
        
        msg('Translation keys...', 4)
        for key in translations.keys:
            frame = 1+int(key.time * _FPS) # time 0.0 is frame 1
            Blender.Set('curframe', frame)
            loc = key.value
            b_obj.LocX = loc.x
            b_obj.LocY = loc.y
            b_obj.LocZ = loc.z
            b_obj.insertIpoKey(Blender.Object.LOC)
            
        Blender.Set('curframe', 1)
