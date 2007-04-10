import Blender
import Config
reload (Config)
from Blender import Draw, BGL, sys
from Blender.Mathutils import *

try:
    import pyniflib
    from pyniflib import *
except:
    err = """--------------------------
ERROR\nThis script requires the PYNIFLIB Python SWIG wrapper, pyniflib.py & niflib.dll.
Make sure these files reside in your Python path or in your Blender scripts folder.
If you don't have them: http://niftools.sourceforge.net/
--------------------------"""
    print err
    Blender.Draw.PupMenu("ERROR%t|PYNIFLIB not found, check console for details")
    raise


#
# Global variables.
#

_CONFIG = {}
_GUI_ELEMENTS = {}
_WINDOW_SIZE = Blender.Window.GetAreaSize()
_LOGO_PATH = sys.sep.join((Blender.Get('scriptsdir'),"bpymodules","nifImEx","niftools_logo.png"))
_LOGO_IMAGE = Blender.Image.Load(_LOGO_PATH)
_SCRIPT_VERSION = "1.9.0a"
_BLOCK_COUNT = 0
_READ_PROGRESS = 0.0
_BLOCKS_READ = 0.0

# dictionary of texture files, to reuse textures
_TEXTURES = {}

# dictionary of materials, to reuse materials
_MATERIALS = {}

# dictionary of names, to map NIF names to correct Blender names
_NAMES = {}

# dictionary of bones, maps Blender bone name to NIF block
_BONES = {}

# dictionary of bones, maps Blender bone name to matrix that maps the
# NIF bone matrix on the Blender bone matrix
# B' = X * B, where B' is the Blender bone matrix, and B is the NIF bone matrix
_BONES_EXTRA_MATRIX = {}

# dictionary of bones that belong to a certain armature
# maps NIF armature name to list of NIF bone name
_BONE_LIST = {}

# correction matrices list, the order is +X, +Y, +Z, -X, -Y, -Z
_BONE_CORRECTION_MATRICES = (\
            Matrix([ 0.0,-1.0, 0.0],[ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 1.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0],[ 0.0,-1.0, 0.0]),\
            Matrix([ 0.0, 1.0, 0.0],[-1.0, 0.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([-1.0, 0.0, 0.0],[ 0.0,-1.0, 0.0],[ 0.0, 0.0, 1.0]),\
            Matrix([ 1.0, 0.0, 0.0],[ 0.0, 0.0,-1.0],[ 0.0, 1.0, 0.0]))

# some variables

_EPSILON = 0.005 # used for checking equality with floats, NOT STORED IN CONFIG
_IMPORT_SCALE_CORRECTION = 0.1
_MSG_LEVEL = 2 # verbosity level

_R2D = 3.14159265358979/180.0 # radians to degrees conversion constant
_D2R = 180.0/3.14159265358979 # degrees to radians conversion constant

_SCENE = Blender.Scene.GetCurrent() #Blender scene, to avoid redundant code
_FPS = _SCENE.getRenderingContext().framesPerSec() #frames per second


# check General scripts config key for default behaviors
_VERBOSE = True



def __init__():
    global _CONFIG, _VERBOSE, _EPSILON, _IMPORT_SCALE_CORRECTION
    reload(Config)
    _CONFIG = Config._CONFIG
    _EPSILON = _CONFIG['_EPSILON'] # used for checking equality with floats, NOT STORED IN CONFIG
    _IMPORT_SCALE_CORRECTION = _CONFIG['_IMPORT_SCALE_CORRECTION']
    _VERBOSE = _CONFIG['_VERBOSE']


def gui():
    global _GUI_ELEMENTS, _CONFIG, _LOGO_IMAGE, _WINDOW_SIZE
    # These are to save me some typing
    #W = _WINDOW_SIZE[0]
    H = _WINDOW_SIZE[1]
    E = {}
    # Draw NifTools logo
    BGL.glEnable(BGL.GL_BLEND ) # enable alpha blending
    # The odd scale and clip values seem necessary to avoid image artifacts
    Draw.Image(_LOGO_IMAGE, 50.0, H-100.0, 1.0001, 1.0001)
    #Draw.Image(logoImg, 50, H-100, 1.0, 1.0, 1.0, 0)
    # Draw.String(name, event, x, y, width, height, initial, length, tooltip=None)
    nifFilePath = sys.sep.join((_CONFIG["_NIF_IMPORT_PATH"], _CONFIG["_NIF_IMPORT_FILE"]))
    E["_NIF_FILE_PATH"]       = Draw.String("",             150,  50, H-150, 390, 20, nifFilePath, 350, '')
    E["_BROWSE_FILE_PATH"]    = Draw.PushButton('...',   155, 440, H-150, 30, 20, 'browse')
    E["_ADVANCED"]            = Draw.PushButton('advanced', 250, 410, H-225, 100, 20)
    E["_CANCEL"]              = Draw.PushButton('cancel',   260, 160, H-225, 100, 20)
    E["_IMPORT"]              = Draw.PushButton('import',   270,  50, H-225, 100, 20)
    _GUI_ELEMENTS = E
    Draw.Redraw(1)

def buttonEvent(evt):
    """
    Event handler for buttons
    """
    global _CONFIG
    if evt == 270:
        # import and close
        exit() #closes the GUI
        nifFilePath = sys.sep.join((_CONFIG["_NIF_IMPORT_PATH"], _CONFIG["_NIF_IMPORT_FILE"]))
        import_nif(nifFilePath)
    elif  evt == 260:
        # cancel
        exit()
    elif  evt == 250:
        # advanced
        exit()
        Config.open("Import")
    elif evt == 155:
        # browse file
        nifFilePath = sys.sep.join((_CONFIG["_NIF_IMPORT_PATH"], _CONFIG["_NIF_IMPORT_FILE"]))
        Blender.Window.FileSelector(select, "import .nif", nifFilePath)
        Draw.Redraw(1)
    else:
        Draw.Redraw(1)

def select(nifFilePath):
    global _GUI_ELEMENTS, _CONFIG
    if nifFilePath == '' or  sys.exists(nifFilePath) != 1:
        Draw.PupMenu('No file selected or file does not exist%t|Ok')
    else:
        _CONFIG["_NIF_IMPORT_PATH"] = sys.dirname(nifFilePath)
        _CONFIG["_NIF_IMPORT_FILE"] = sys.basename(nifFilePath)
        Config._CONFIG = _CONFIG
        Config.save()
    Draw.Redraw(1)



def event(evt, val):
    """
    Event handler for GUI elements
    """
    #print  "event(%i,%i)"%(arg1,arg2)
    if evt == Draw.ESCKEY:
        exit()

def open():
    """
    Opens the import GUI
    """
    global _WINDOW_SIZE
    _WINDOW_SIZE = Blender.Window.GetAreaSize()
    reload(Config)
    Config.clean()
    global _CONFIG
    _CONFIG = Config._CONFIG
    Draw.Register(gui, event, buttonEvent)

def exit():
    """
    Closes the config GUI
    """
    Draw.Exit()






# Little wrapper for debug messages
def msg(message='-', level=2):
    if _VERBOSE:
        if level <= _MSG_LEVEL:
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
        ver = pyniflib.GetNifVersion(filename)
        if ( ver == VER_INVALID ):
            raise NIFImportError("Not a NIF file.")
        elif ( ver == VER_UNSUPPORTED ):
            raise NIFImportError("Unsupported NIF version.")
        Blender.Window.DrawProgressBar(0.33, "Reading file")
        root_block = ReadNifTree(filename)
        Blender.Window.DrawProgressBar(0.66, "Importing data")
        import_main(root_block)
    except NIFImportError, e: # in that case, we raise a menu instead of an exception
        Blender.Window.DrawProgressBar(1.0, "Import Failed")
        print 'NIFImportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return
    Blender.Window.DrawProgressBar(1.0, "Finished")



#
# Main import function.
#
def import_main(root_block):
    # scene info
    # used to control the progress bar
    global _SCENE, _CONFIG, _BLOCK_COUNT, _BLOCKS_READ, _READ_PROGRESS
    _BLOCK_COUNT = BlocksInMemory()
    _READ_PROGRESS = 0.0
    _BLOCKS_READ = 0.0
    # preprocessing:
    # scale tree
    scale_tree(root_block, 1.0/SCALE_CORRECTION)
    # mark armature nodes and bones
    # and merge armatures that are bones of others armatures
    mark_armatures_bones(root_block)
    merge_armatures()
    if _VERBOSE and _MSG_LEVEL >= 3:
        for arm_name in _BONE_LIST.keys():
            print "armature '%s':"%arm_name
            for bone_name in _BONE_LIST[arm_name]:
                print "  bone '%s'"%bone_name
    # read the NIF tree
    if not is_armature_root(root_block):
        if not root_block["Children"].is_null(): # it's a ninode?
            # yes, we'll process all children of the root node
            # (this prevents us having to create an empty as a root)
            blocks = root_block["Children"].asLinkList()
            # import the extras
            textkey = find_extra(root_block, "NiTextKeyExtraData")
            if not textkey.is_null(): fb_textkey(textkey)
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
    if not niBlock.is_null():
        btype = niBlock.GetBlockType()
        if btype == "NiTriShape" or btype == "NiTriStrips":
            # it's a shape node
            return fb_mesh(niBlock)
        elif not niBlock["Children"].is_null():
            # it's a parent node
            # import object + children
            niChildren = niBlock["Children"].asLinkList()
            b_obj = None
            if is_armature_root(niBlock):
                # the whole bone branch is imported by fb_armature as well
                b_obj = fb_armature(niBlock)
                # now also do the meshes
                read_armature_branch(b_obj, niBlock, niBlock)
            else:
                # it's a grouping node
                b_obj = fb_empty(niBlock)
                b_children_list = []
                for child in niChildren:
                    b_child_obj = read_branch(child)
                    if b_child_obj: b_children_list.append(b_child_obj)
                b_obj.makeParent(b_children_list)
            b_obj.setMatrix(fb_matrix(niBlock))
            # import the animations
            set_animation(niBlock, b_obj)
            # import the extras
            textkey = find_extra(niBlock, "NiTextKeyExtraData")
            if not textkey.is_null(): fb_textkey(textkey)
            return b_obj
        else:
            return None

# Reads the content of the current NIF tree branch to Blender
# recursively, as meshes parented to a given armature. Note that
# niBlock must have been imported previously as an armature, along
# with all its bones. This function only imports meshes.
def read_armature_branch(b_armature, niArmature, niBlock):
    """
    Reads the content of the current NIF tree branch to Blender
    recursively, as meshes parented to a given armature. Note that
    niBlock must have been imported previously as an armature, along
    with all its bones. This function only imports meshes.
    """
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
                            groupName = _NAMES[par_bone["Name"].asString()]
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
# hash functions, for object comparison and dictionary keys
#
def float_hash(x):
    return int(x*200)

def float3_hash(x):
    return (float_hash(x[0]), float_hash(x[1]), float_hash(x[2]))

# blk_ref hash
def block_hash(b):
    if b.is_null():
        return None
    else:
        return b.GetBlockNum()

# NiSourceTexture hash
def texsource_hash(texsource):
    return (\
        block_hash(texsource["Controller"].asLink()),\
        str(texsource["Texture Source"].asTexSource().fileName),\
        texsource["Pixel Layout"].asInt(),\
        texsource["Use Mipmaps"].asInt(),\
        texsource["Alpha Format"].asInt()\
    )

# TexDesc hash
def texdesc_hash(texdesc):
    if texdesc.isUsed:
        return (texdesc.clampMode, texdesc.filterMode, texsource_hash(texdesc.source))
    else:
        return None

# "material" property hash
def material_hash(matProperty, textProperty, alphaProperty, specProperty):
    if not matProperty.is_null():
        mathash = (\
            block_hash(matProperty["Controller"].asLink()),\
            matProperty["Flags"].asInt(),\
            float3_hash(matProperty["Ambient Color"].asFloat3()),\
            float3_hash(matProperty["Diffuse Color"].asFloat3()),\
            float3_hash(matProperty["Specular Color"].asFloat3()),\
            float3_hash(matProperty["Emissive Color"].asFloat3()),\
            float_hash(matProperty["Glossiness"].asFloat()),\
            float_hash(matProperty["Alpha"].asFloat())\
        )
    else:
        mathash = None
    if not textProperty.is_null():
        itexprop = QueryTexturingProperty(textProperty)
        bastex = itexprop.GetTexture(0)
        glowtex = itexprop.GetTexture(4)
        texthash = (\
            block_hash(textProperty["Controller"].asLink()),\
            textProperty["Flags"].asInt(),\
            itexprop.GetApplyMode(),\
            texdesc_hash(bastex),\
            texdesc_hash(glowtex)\
        )
    else:
        texthash = None
    if not alphaProperty.is_null():
        alphahash = block_hash(alphaProperty["Controller"].asLink())
    else:
        alphahash = None
    if not specProperty.is_null():
        spechash = block_hash(specProperty["Controller"].asLink())
    else:
        spechash = None
    return (mathash, texthash, alphahash, spechash)



#
# Get unique name for an object, preserving existing names
#
def fb_name(niBlock,max_length=22):
    """
    Get unique name for an object, preserving existing names
    The maximum name length defaults to 22, since this is the
    maximum for Blender objects, but bone names can reach 32.
    The task of catching errors is left to the user
    """
    global _NAMES

    # find unique name for Blender to use
    uniqueInt = 0
    niName = niBlock["Name"].asString()
    # remove the "Tri " prefix; this will help when exporting the model again
    if niName[:4] == "Tri ":
        niName = niName[4:]
    name = niName[:max_length-1] # Blender has a rather small name buffer
    try:
        while Blender.Object.Get(name):
            name = '%s.%02d' % (niName[:max_length-4], uniqueInt)
            uniqueInt +=1
    except:
        pass

    # save mapping
    _NAMES[niName] = name

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



# Decompose Blender transform matrix as a scale, rotation matrix, and translation vector
def decompose_srt(m):
    # get scale components
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
    b_empty = Blender.Object.New("Empty", fb_name(niBlock,22))
    _SCENE.objects.link(b_empty)
    return b_empty

# Scans an armature hierarchy, and returns a whole armature.
# This is done outside the normal node tree scan to allow for positioning of
# the bones.
def fb_armature(niBlock):
    global _SCENE
    armature_name = fb_name(niBlock,)
    armature_matrix_inverse = fb_global_matrix(niBlock)
    armature_matrix_inverse.invert()
    b_armature = Blender.Object.New('Armature', fb_name(niBlock,22))
    b_armatureData = Blender.Armature.Armature()
    b_armatureData.name = armature_name
    b_armatureData.drawAxes = True
    b_armatureData.envelopes = False
    b_armatureData.vertexGroups = True
    #b_armatureData.drawType = Blender.Armature.STICK
    #b_armatureData.drawType = Blender.Armature.ENVELOPE
    #b_armatureData.drawType = Blender.Armature.OCTAHEDRON
    b_armature.link(b_armatureData)
    b_armatureData.makeEditable()
    niChildren = niBlock["Children"].asLinkList()
    niChildBones = [child for child in niChildren if is_bone(child)]  
    for niBone in niChildBones:
        # Ok, possibly forwarding the inverse of the armature matrix through all the bone chain is silly,
        # but I believe it saves some processing time compared to making it global or recalculating it all the time.
        # And serves the purpose fine
        fb_bone(niBone, b_armature, b_armatureData, armature_matrix_inverse)
    b_armatureData.update()
    _SCENE.objects.link(b_armature)

    # The armature has been created in editmode,
    # now we are ready to set the bone keyframes.

    # create an action
    action = Blender.Armature.NLA.NewAction()
    action.setActive(b_armature)
    # go through all armature pose bones (http://www.elysiun.com/forum/viewtopic.php?t=58693)
    progress = 0.0
    bone_count = len(b_armature.getPose().bones)
    Blender.Window.DrawProgressBar(progress, 'Importing Animations')
    for bone_idx, (bone_name, b_posebone) in enumerate(b_armature.getPose().bones.items()):
        # denote progress
        if (bone_idx*1.0)/(bone_count*1.0) > (progress + 0.1):
            progress += 0.1
            Blender.Window.DrawProgressBar(progress, 'Animation: %s'%bone_name)
        #if (progress < 0.85): progress += 0.1
        #else: progress = 0.1
        
        msg('Importing animation for bone %s'%bone_name, 4)
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
        niBone = _BONES[bone_name]
        niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = decompose_srt(fb_matrix(niBone))
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
        extra_matrix_scale, extra_matrix_rot, extra_matrix_trans = decompose_srt(_BONES_EXTRA_MATRIX[bone_name])
        extra_matrix_quat = extra_matrix_rot.toQuat()
        extra_matrix_rot_inv = Matrix(extra_matrix_rot)
        extra_matrix_rot_inv.invert()
        extra_matrix_quat_inv = extra_matrix_rot_inv.toQuat()
        # now import everything
        kfc = find_controller(niBone, "NiKeyframeController")
        if not kfc.is_null():
            # get keyframe data
            kfd = kfc["Data"].asLink()
            assert(kfd.GetBlockType() == "NiKeyframeData")
            ikfd = QueryKeyframeData(kfd)
            rot_keys = ikfd.GetRotateKeys()
            trans_keys = ikfd.GetTranslateKeys()
            scale_keys = ikfd.GetScaleKeys()
            # if we have translation keys, we make a dictionary of
            # rot_keys and scale_keys, this makes the script work MUCH faster
            # in most cases
            if trans_keys:
                scale_keys_dict = {}
                rot_keys_dict = {}
            # add the keys
            msg('Scale keys...', 4)
            for scale_key in scale_keys:
                frame = 1+int(scale_key.time * _FPS) # time 0.0 is frame 1
                scale_total = scale_key.data
                scale_channel = scale_total / niBone_bind_scale # Schannel = Stotal / Sbind
                b_posebone.size = Blender.Mathutils.Vector(scale_channel, scale_channel, scale_channel)
                b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.SIZE])
                # fill optimizer dictionary
                if trans_keys:
                    scale_keys_dict[frame] = scale_channel
            msg('Rotation keys...', 4)
            for rot_key in rot_keys:
                frame = 1+int(rot_key.time * _FPS) # time 0.0 is frame 1
                #rot_total = Blender.Mathutils.Quaternion([rot_key.data.w, rot_key.data.x, rot_key.data.y, rot_key.data.z]).toMatrix()
                #rot_channel = rot_total * niBone_bind_rot_inv # Rchannel = Rtotal * inverse(Rbind)
                #rot_channel = extra_matrix_rot * rot_channel * extra_matrix_rot_inv # C' = X * C * inverse(X)
                # faster alternative below
                # beware, CrossQuats takes arguments in a counter-intuitive order:
                # q1.toMatrix() * q2.toMatrix() == CrossQuats(q2, q1).toMatrix()
                rot_total = Blender.Mathutils.Quaternion([rot_key.data.w, rot_key.data.x, rot_key.data.y, rot_key.data.z])
                rot_channel = CrossQuats(niBone_bind_quat_inv, rot_total) # Rchannel = Rtotal * inverse(Rbind)
                rot_channel = CrossQuats(CrossQuats(extra_matrix_quat_inv, rot_channel), extra_matrix_quat) # C' = X * C * inverse(X)
                
                b_posebone.quat = rot_channel
                b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.ROT]) # this is very slow... :(
                # fill optimizer dictionary
                if trans_keys:
                    rot_keys_dict[frame] = Blender.Mathutils.Quaternion(rot_channel)
            msg('Translation keys...', 4)
            for trans_key in trans_keys:
                frame = 1+int(trans_key.time * _FPS) # time 0.0 is frame 1
                trans_total = Blender.Mathutils.Vector(trans_key.data.x, trans_key.data.y, trans_key.data.z)
                trans_channel = (trans_total - niBone_bind_trans) * niBone_bind_rot_inv * (1.0/niBone_bind_scale)# Tchannel = (Ttotal - Tbind) * inverse(Rbind) / Sbind
                # we need the rotation matrix at this frame (that's why we inserted the other keys first)
                if rot_keys_dict:
                    try:
                        rot_channel = rot_keys_dict[frame].toMatrix()
                    except KeyError:
                        # fall back on slow method
                        ipo = action.getChannelIpo(bone_name)
                        quat = Blender.Mathutils.Quaternion()
                        quat.x = ipo.getCurve('QuatX').evaluate(frame)
                        quat.y = ipo.getCurve('QuatY').evaluate(frame)
                        quat.z = ipo.getCurve('QuatZ').evaluate(frame)
                        quat.w = ipo.getCurve('QuatW').evaluate(frame)
                        rot_channel = quat.toMatrix()
                else:
                    rot_channel = Blender.Mathutils.Matrix([1,0,0],[0,1,0],[0,0,1])
                # we also need the scale at this frame
                if scale_keys_dict:
                    try:
                        scale_channel = scale_keys_dict[frame]
                    except KeyError:
                        ipo = action.getChannelIpo(bone_name)
                        if ipo.getCurve('SizeX'):
                            scale_channel = ipo.getCurve('SizeX').evaluate(frame) # assume uniform scale
                        else:
                            scale_channel = 1.0
                else:
                    scale_channel = 1.0
                # now we can do the final calculation
                trans_channel = (extra_matrix_trans * scale_channel * rot_channel + trans_channel - extra_matrix_trans) * extra_matrix_rot_inv * (1.0/extra_matrix_scale) # C' = X * C * inverse(X)
                b_posebone.loc = trans_channel
                b_posebone.insertKey(b_armature, frame, [Blender.Object.Pose.LOC])
            if trans_keys:
                del scale_keys_dict
                del rot_keys_dict
    return b_armature


# Adds a bone to the armature in edit mode.
def fb_bone(niBlock, b_armature, b_armatureData, armature_matrix_inverse):
    global _BONES, _BONES_EXTRA_MATRIX, _BONE_CORRECTION_MATRICES
    
    bone_name = fb_name(niBlock, 32)
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
        if len(niChildNodes) > 0:
            child_matrices = [(fb_global_matrix(child)*armature_matrix_inverse) for child in niChildNodes]
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
        is_zero_length = (int(sum([b_bone_head_x-b_bone_tail_x, b_bone_head_y-b_bone_tail_y, b_bone_head_z-b_bone_tail_z])*200) == 0)
        if is_zero_length:
            # this is a 0 length bone, to avoid it being removed I set a default minimum length
            # Since we later set the matrix explicitly any axis will do here.
            # TO DO: Compensate for scale
            b_bone_tail_x = b_bone_head_x + 0.5
        # sets the bone heads & tails
        b_bone.head = Vector(b_bone_head_x, b_bone_head_y, b_bone_head_z)
        b_bone.tail = Vector(b_bone_tail_x, b_bone_tail_y, b_bone_tail_z)
        if is_zero_length:
            # Can't test zero length bones, we keep the original alignment
            # with no further correction
            b_bone.matrix = armature_space_matrix.rotationPart()
        else:
            # here we explicitly try to set the matrix from the NIF matrix; this has the following consequences:
            # - head is preserved
            # - bone length is preserved
            # - tail is lost (up to bone length)
            (sum_x, sum_y, sum_z, dummy) = fb_matrix(niBlock)[3]
            if len(niChildNodes) > 0:
                child_local_matrices = [fb_matrix(child) for child in niChildNodes]
                sum_x = sum([cm[3][0] for cm in child_local_matrices])
                sum_y = sum([cm[3][1] for cm in child_local_matrices])
                sum_z = sum([cm[3][2] for cm in child_local_matrices])
            listXYZ = [int(c*200) for c in (sum_x, sum_y, sum_z, -sum_x, -sum_y, -sum_z)]
            idx_correction = listXYZ.index(max(listXYZ))
            alignment_offset = 0.0
            if idx_correction == 0 or idx_correction == 3:
                alignment_offset = float(abs(sum_y) + abs(sum_z)) / abs(sum_x)
            elif idx_correction == 1 or idx_correction == 4:
                alignment_offset = float(abs(sum_z) + abs(sum_x)) / abs(sum_y)
            else:
                alignment_offset = float(abs(sum_x) + abs(sum_y)) / abs(sum_z)
            # if alignment is good enough, use the (corrected) NIF matrix
            if alignment_offset < 0.25:
                m_correction = _BONE_CORRECTION_MATRICES[idx_correction]
                b_bone.matrix = m_correction * armature_space_matrix.rotationPart()
        # set bone name and store the niBlock for future reference
        b_armatureData.bones[bone_name] = b_bone
        _BONES[bone_name] = niBlock
        # calculate bone difference matrix; we will need this when importing animation
        old_bone_matrix_inv = Blender.Mathutils.Matrix(armature_space_matrix)
        old_bone_matrix_inv.invert()
        new_bone_matrix = Blender.Mathutils.Matrix(b_bone.matrix)
        new_bone_matrix.resize4x4()
        new_bone_matrix[3][0] = b_bone_head_x
        new_bone_matrix[3][1] = b_bone_head_y
        new_bone_matrix[3][2] = b_bone_head_z
        _BONES_EXTRA_MATRIX[bone_name] = new_bone_matrix * old_bone_matrix_inv # new * inverse(old)
        # set bone children
        for niBone in niChildBones:
            b_child_bone =  fb_bone(niBone, b_armature, b_armatureData, armature_matrix_inverse)
            if b_child_bone:
                b_child_bone.parent = b_bone
        return b_bone
    return None



def fb_texture( niSourceTexture ):
    """
    Returns a Blender Texture object, and stores it in the global TEXTURES dictionary
    """
    global _TEXTURES
    
    try:
        return _TEXTURES[texsource_hash(niSourceTexture)]
    except:
        pass
    
    b_image = None
    
    niTexSource = niSourceTexture["Texture Source"].asTexSource()
    
    if niTexSource.useExternal:
        # the texture uses an external image file
        fn = niTexSource.fileName
        # go searching for it
        textureFile = None
        for texdir in _TEXTURES_DIR.split(";") + [NIF_DIR, TEX_DIR]:
            if texdir == None: continue
            texdir.replace( '\\', Blender.sys.sep )
            texdir.replace( '/', Blender.sys.sep )
             # now a little trick, to satisfy many Morrowind mods
            if (fn[:9].lower() == 'textures\\') and (texdir[-9:].lower() == '\\textures'):
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
            for ext in ('.PNG','.png','.TGA','.tga','.BMP','.bmp','.JPG','.jpg'):
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
                        pass
        if b_image == None:
            print "Texture %s not found and no alternate available" % niTexSource.fileName
            b_image = Blender.Image.New(tex, 1, 1, 24) # create a stub
            b_image.filename = tex
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
        _TEXTURES[ texsource_hash(niSourceTexture) ] = b_texture
        return b_texture
    else:
        _TEXTURES[ texsource_hash(niSourceTexture) ] = None
        return None



# Creates and returns a material
def fb_material(matProperty, textProperty, alphaProperty, specProperty):
    global _MATERIALS
    
    # First check if material has been created before.
    try:
        material = _MATERIALS[material_hash(matProperty, textProperty, alphaProperty, specProperty)]
        return material
    except KeyError:
        pass
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
    if (diff[0] > _EPSILON):
        b_amb += amb[0]/diff[0]
        b_emit += emit[0]/diff[0]
        b_n += 1
    if (diff[1] > _EPSILON):
        b_amb += amb[1]/diff[1]
        b_emit += emit[1]/diff[1]
        b_n += 1
    if (diff[2] > _EPSILON):
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

    _MATERIALS[material_hash(matProperty, textProperty, alphaProperty, specProperty)] = material
    return material

# Creates and returns a raw mesh
def fb_mesh(niBlock):
    global _SCENE
    # Mesh name -> must be unique, so tag it if needed
    b_name=fb_name(niBlock,22)
    # we mostly work directly on Blender's objects (b_meshData)
    # but for some tasks we must use the Python wrapper (b_nmeshData), see further
    b_meshData = Blender.Mesh.New(b_name)
    b_mesh = _SCENE.objects.new(b_meshData, b_name)
    b_mesh = Blender.Object.New("Mesh", b_name)
    b_mesh.link(b_meshData)
   
    _SCENE.objects.link(b_mesh)
    

    # Mesh hidden flag
    if niBlock["Flags"].asInt() & 1 == 1:
        b_mesh.setDrawType(2) # hidden: wire
    else:
        b_mesh.setDrawType(4) # not hidden: shaded

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
    if not _SEAMS_IMPORT:
        # Fast method: don't care about any seams!
        for i, v in enumerate(verts):
            v_map[i] = i # NIF vertex i maps to blender vertex i
            b_meshData.verts.extend(v.x, v.y, v.z) # add the vertex
    else:
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
        if uvco:
            material = fb_material(matProperty, textProperty, alphaProperty, specProperty)
        else:
            # no UV coordinates: no texture
            material = fb_material(matProperty, blk_ref(), alphaProperty, specProperty)
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
            groupName = _NAMES[bone["Name"].asString()]
            b_meshData.addVertGroup(groupName)
            for vert, weight in weights.iteritems():
                b_meshData.assignVertsToGroup(groupName, [v_map[vert]], weight, Blender.Mesh.AssignModes.REPLACE)

    b_meshData.calcNormals() # let Blender calculate vertex normals

    # new implementation, uses Mesh instead
    morphCtrl = find_controller(niBlock, "NiGeomMorpherController")
    if morphCtrl.is_null() == False:
        morphData = morphCtrl["Data"].asLink()
        if ( morphData.is_null() == False ):
            iMorphData = QueryMorphData(morphData)
            if ( iMorphData.GetMorphCount() > 0 ):
                # insert base key at frame 1
                b_meshData.insertKey( 1, 'absolute' )
                baseverts = iMorphData.GetMorphVerts( 0 )
                b_ipo = Blender.Ipo.New( 'Key' , 'KeyIpo' )
                b_meshData.key.ipo = b_ipo
                for idxMorph in xrange(1,iMorphData.GetMorphCount()):
                    morphverts = iMorphData.GetMorphVerts(idxMorph)
                    # for each vertex calculate the key position from base pos + delta offset
                    for count in range( iMorphData.GetVertexCount() ):
                        x = baseverts[count].x
                        y = baseverts[count].y
                        z = baseverts[count].z
                        dx = morphverts[count].x
                        dy = morphverts[count].y
                        dz = morphverts[count].z
                        b_meshData.verts[v_map[count]].co[0] = x + dx
                        b_meshData.verts[v_map[count]].co[1] = y + dy
                        b_meshData.verts[v_map[count]].co[2] = z + dz
                    # update the mesh and insert key
                    b_meshData.insertKey(idxMorph, 'relative')
                    # set up the ipo key curve
                    b_curve = b_ipo.addCurve('Key %i' % idxMorph)
                    # dunno how to set up the bezier triples -> switching to linear instead
                    b_curve.setInterpolation('Linear')
                    # select extrapolation
                    if ( morphCtrl["Flags"].asInt() == 0x000c ):
                        b_curve.setExtrapolation( 'Constant' )
                    elif ( morphCtrl["Flags"].asInt() == 0x0008 ):
                        b_curve.setExtrapolation( 'Cyclic' )
                    else:
                        msg( 'dunno which extrapolation to use: using constant instead', 2 )
                        b_curve.setExtrapolation( 'Constant' )
                    # set up the curve's control points
                    morphkeys = iMorphData.GetMorphKeys(idxMorph)
                    for morphkey in morphkeys:
                        x =  morphkey.data
                        frame =  1+int(morphkey.time * _FPS)
                        b_curve.addBezier( ( frame, x ) )
                    # finally: return to base position
                    for count in xrange( iMorphData.GetVertexCount() ):
                        x = baseverts[count].x
                        y = baseverts[count].y
                        z = baseverts[count].z
                        b_meshData.verts[v_map[count]].co[0] = x
                        b_meshData.verts[v_map[count]].co[1] = y
                        b_meshData.verts[v_map[count]].co[2] = z
                # assign ipo to mesh
                
    return b_mesh



# import animation groups
def fb_textkey(block):
    """
    Stores the text keys that define animation start and end in a text buffer,
    so that they can be re-exported.
    Since the text buffer is cleared on each import only the last import will be exported
    correctly
    """
    # get animation text buffer, and clear it if it already exists
    try:
        animtxt = [txt for txt in Blender.Text.Get() if txt.getName() == "Anim"][0]
        animtxt.clear()
    except:
        animtxt = Blender.Text.New("Anim")
    #animtxt = None
    #for txt in Blender.Text.Get():
    #    if txt.getName() == "Anim":
    #        txt.clear()
    #        animtxt = txt
    #        break
    #if not animtxt:
    #    animtxt = Blender.Text.New("Anim")

    # store keys in the animation text buffer
    itextkey = QueryTextKeyExtraData(block)
    frame = 1
    for key in itextkey.GetKeys():
        newkey = key.data.replace('\r\n', '/').rstrip('/')
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
    global _BONES_EXTRA_MATRIX
    # get the bone extra matrix text buffer
    #bonetxt = None
    #for txt in Blender.Text.Get():
    #    if txt.getName() == "BoneExMat":
    #        txt.clear()
    #        bonetxt = txt
    #        break
    try:
        bonetxt = [txt for txt in Blender.Text.Get() if txt.getName() == "BoneExMat"][0]
        bonetxt.clear()
    except:
        bonetxt = Blender.Text.New("BoneExMat")
    for b in _BONES_EXTRA_MATRIX.keys():
        ln=''
        for row in _BONES_EXTRA_MATRIX[b]:
            ln='%s;%s,%s,%s,%s' % (ln, row[0],row[1],row[2],row[3])
        # print '%s/%s/%s\n' % (a, b, ln[1:])
        bonetxt.write('%s/%s\n' % (b, ln[1:]))
    

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
    for n in _NAMES.keys():
        namestxt.write('%s;%s\n'% (_NAMES[n], n))
    
# find a controller
def find_controller(block, controllertype):
    """
    Finds a controller
    """
    ctrl = block["Controller"].asLink()
    while ctrl.is_null() == False:
        if ctrl.GetBlockType() == controllertype:
            break
        ctrl = ctrl["Next Controller"].asLink()
    return ctrl



# find extra data
def find_extra(block, extratype):
    # pre-10.x.x.x system: extra data chain
    extra = block["Extra Data"].asLink()
    while not extra.is_null():
        if extra.GetBlockType() == extratype:
            break
        extra = extra["Next Extra Data"].asLink()
    if not extra.is_null():
        return extra

    # post-10.x.x.x system: extra data list
    for extra in block["Extra Data List"].asLinkList():
        if extra.GetBlockType() == extratype:
            return extra

    return blk_ref() # return empty block


# mark armatures and bones by peeking into NiSkinInstance blocks
# probably we will eventually have to use this
# since that the "is skinning influence" flag is not reliable
def mark_armatures_bones(block):
    global _BONE_LIST
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
            if not _BONE_LIST.has_key(skelroot_name):
                _BONE_LIST[skelroot_name] = []
                msg("'%s' is an armature"%skelroot_name,3)
            # now get the skinning data interface to retrieve the list of bones
            skindata = skininst["Data"].asLink()
            iskindata = QuerySkinData(skindata)
            for bone in iskindata.GetBones():
                # add them, if we haven't already
                bone_name = bone["Name"].asString()
                if not bone_name in _BONE_LIST[skelroot_name]:
                    _BONE_LIST[skelroot_name].append(bone_name)
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
    global _BONE_LIST
    # we must already have marked this one as a bone
    bone_name = bone["Name"].asString()
    assert _BONE_LIST.has_key(skelroot_name) # debug
    assert bone_name in _BONE_LIST[skelroot_name] # debug
    # get the node parent, this should be marked as an armature or as a bone
    boneparent = bone.GetParent()
    boneparent_name = boneparent["Name"].asString()
    if boneparent_name != skelroot_name:
        # parent is not the skeleton root
        if not boneparent_name in _BONE_LIST[skelroot_name]:
            # neither is it marked as a bone: so mark the parent as a bone
            _BONE_LIST[skelroot_name].append(boneparent_name)
            # store the coordinates for realignement autodetection 
            msg("'%s' is a bone of armature '%s'"%(boneparent_name, skelroot_name),3)
        # now the parent is marked as a bone
        # recursion: complete the bone tree,
        # this time starting from the parent bone
        complete_bone_tree(boneparent, skelroot_name)



# merge armatures that are bones of other armatures
def merge_armatures():
    global _BONE_LIST
    for arm_name, bones in _BONE_LIST.items():
        for arm_name2, bones2 in _BONE_LIST.items():
            if arm_name2 in bones and _BONE_LIST.has_key(arm_name):
                msg("merging armature '%s' into armature '%s'"%(arm_name2,arm_name),3)
                # arm_name2 is in _BONE_LIST[arm_name]
                # so add every bone2 in _BONE_LIST[arm_name2] too
                for bone2 in bones2:
                    if not bone2 in bones:
                        _BONE_LIST[arm_name].append(bone2)
                # remove merged armature
                del _BONE_LIST[arm_name2]



# Tests a NiNode to see if it's a bone.
def is_bone(niBlock):
    if niBlock["Name"].asString()[:6] == "Bip01 ": return True # heuristics
    for bones in _BONE_LIST.values():
        if niBlock["Name"].asString() in bones:
            #print "%s is a bone" % niBlock["Name"].asString()
            return True
    #print "%s is not a bone" % niBlock["Name"].asString()
    return False

# Tests a NiNode to see if it's an armature.
def is_armature_root(niBlock):
    return _BONE_LIST.has_key(niBlock["Name"].asString())
    
# Detect closest bone ancestor.
def get_closest_bone(niBlock):
    par = niBlock.GetParent()
    while not par.is_null():
        if is_bone(par):
            return par
        par = par.GetParent()
    return par

#
# Main KFM import function. (BROKEN)
#
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



#
# Loads basic animation info for this object
#
def set_animation(niBlock, b_obj):
    global _SCENE
    global SCALE_CORRECTION
    global SCALE_MATRIX
    progress = 0.1
    kfc = find_controller(niBlock, "NiKeyframeController")
    if not kfc.is_null():
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
        kfd = kfc["Data"].asLink()
        assert(kfd.GetBlockType() == "NiKeyframeData")
        ikfd = QueryKeyframeData(kfd)
        if 1: #---------------------------------------------------------------------------------------------
            rot_keys = ikfd.GetRotateKeys()
            trans_keys = ikfd.GetTranslateKeys()
            scale_keys = ikfd.GetScaleKeys()
            # add the keys
            msg('Scale keys...', 4)
            for scale_key in scale_keys:
                frame = 1+int(scale_key.time * _FPS) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                size_value = scale_key.data
                b_obj.SizeX = size_value
                b_obj.SizeY = size_value
                b_obj.SizeZ = size_value
                b_obj.insertIpoKey(Blender.Object.SIZE)
            msg('Rotation keys...', 4)
            for rot_key in rot_keys:
                frame = 1+int(rot_key.time * _FPS) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                rot = Blender.Mathutils.Quaternion(rot_key.data.w, rot_key.data.x, rot_key.data.y, rot_key.data.z).toEuler()
                # b_obj.RotX = rot.x * 3.14159265358979 / 180.0
                # b_obj.RotY = rot.y * 3.14159265358979 / 180.0
                # b_obj.RotZ = rot.z * 3.14159265358979 / 180.0
                b_obj.RotX = rot.x * _R2D
                b_obj.RotY = rot.y * _R2D
                b_obj.RotZ = rot.z * _R2D
                b_obj.insertIpoKey(Blender.Object.ROT)
            msg('Translation keys...', 4)
            for trans_key in trans_keys:
                frame = 1+int(trans_key.time * _FPS) # time 0.0 is frame 1
                Blender.Set('curframe', frame)
                b_obj.LocX = trans_key.data.x
                b_obj.LocY = trans_key.data.y
                b_obj.LocZ = trans_key.data.z
                b_obj.insertIpoKey(Blender.Object.LOC)
            Blender.Set('curframe', 1)
        else:
            rot_keys = ikfd.GetRotateKeys()
            if rot_keys:
                RotX = b_ipo.addCurve("RotX")
                RotY = b_ipo.addCurve("RotY")
                RotZ = b_ipo.addCurve("RotZ")
                for rot_key in rot_keys:
                    time = 1.0+(rot_key.time * _FPS)
                    rot = Blender.Mathutils.Quaternion(rot_key.data.w, rot_key.data.x, rot_key.data.y, rot_key.data.z).toEuler()
                    RotX.addBezier((time, rot.x * _R2D))
                    RotY.addBezier((time, rot.y * _R2D))
                    RotZ.addBezier((time, rot.z * _R2D))
            loc_keys = ikfd.GetTranslateKeys()
            if loc_keys:
                LocX = b_ipo.addCurve("LocX")
                LocY = b_ipo.addCurve("LocY")
                LocZ = b_ipo.addCurve("LocZ")
                for loc_key in loc_keys:
                    time = 1.0+(loc_key.time * _FPS)
                    LocX.addBezier((time, loc_key.data.x))
                    LocY.addBezier((time, loc_key.data.y))
                    LocZ.addBezier((time, loc_key.data.z))
            size_keys = ikfd.GetScaleKeys()
            if size_keys:
                SizeX = b_ipo.addCurve("SizeX")
                SizeY = b_ipo.addCurve("SizeY")
                SizeZ = b_ipo.addCurve("SizeZ")
                for size_key in size_keys:
                    time = 1.0+(size_key.time * _FPS)
                    size = size_key.data
                    SizeX.addBezier((time, size))
                    SizeY.addBezier((time, size))
                    SizeZ.addBezier((time, size))



# 
# Scale NIF file.
# 
def scale_tree(block, scale):
    inode = QueryNode(block)
    if inode: # is it a node?
        # NiNode transform scale
        t = block["Translation"].asFloat3()
        t[0] *= scale
        t[1] *= scale
        t[2] *= scale
        block["Translation"] = t

        # NiNode bind position transform scale
        mat = inode.GetWorldBindPos()
        mat[3][0] *= scale
        mat[3][1] *= scale
        mat[3][2] *= scale
        inode.SetWorldBindPos(mat)
        
        # Controller data block scale
        ctrl = block["Controller"].asLink()
        while not ctrl.is_null():
            if ctrl.GetBlockType() == "NiKeyframeController":
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
            elif ctrl.GetBlockType() == "NiGeomMorpherController":
                gmd = ctrl["Data"].asLink()
                assert(not gmd.is_null())
                assert(gmd.GetBlockType() == "NiMorphData")
                igmd = QueryMorphData(gmd)
                for key in range( igmd.GetMorphCount() ):
                    verts = igmd.GetMorphVerts( key )
                    for v in range( len( verts ) ):
                        verts[v].x *= scale
                        verts[v].y *= scale
                        verts[v].z *= scale
                    igmd.SetMorphVerts( key, verts )
            ctrl = ctrl["Next Controller"].asLink()
        # Child block scale
        if not block["Children"].is_null(): # block has children
            for child in block["Children"].asLinkList():
                scale_tree(child, scale)
        elif not block["Data"].is_null(): # block has data
            scale_tree(block["Data"].asLink(), scale) # scale the data

    ishapedata = QueryShapeData(block)
    if ishapedata: # is it a shape?
        # Scale all vertices
        vertlist = ishapedata.GetVertices()
        if vertlist:
            for vert in vertlist:
                vert.x *= scale
                vert.y *= scale
                vert.z *= scale
            ishapedata.SetVertices(vertlist)

