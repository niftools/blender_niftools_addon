#!BPY

"""
Name: 'NetImmerse 4.0.0.2 (.nif)'
Blender: 237
Group: 'Export'
Tip: 'Export the selected objects, along with their parents and children, to a NIF file.'
"""

__author__ = ["amorilia@gamebox.net"]
__url__ = ("http://niftools.sourceforge.net/", "blender", "elysiun")
__version__ = "1.1"
__bpydoc__ = """\
This script exports Netimmerse (the version used by Morrowind) .NIF files (version 4.0.0.2).

Usage:

Select the meshes you wish to export and run this script from "File->Export" menu. All parents and children of the selected meshes will be exported as well.
"""

# --------------------------------------------------------------------------
# NIF Export v1.1 by Amorilia ( amorilia@gamebox.net )
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

import Blender, struct, re, nif4
from math import sqrt



# 
# Some constants.
# 
epsilon = 0.005       # used for checking equality of floats
show_progress = 1     # 0 = off, 1 = basic, 2 = advanced (but slows down the exporter)
scale_correction = 10 # 1 blender unit = 10 nif units
force_dds = 0         # 0 = use original texture file extension, 1 = force dds extension
strip_texpath = 2     # 0 = use full texture file path (obsolete?)
                      # 1 = basedir/filename.ext (strip 'data files' prefix for morrowind)
                      # 2 = filename.ext (original morrowind style)
vertex_opt = 0        # 0 = minimum vertex array optimization (fast)
                      # 1 = remove double vertices on the fly (slow, generates smallest nif possible)



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
        if show_progress >= 1: Blender.Window.DrawProgressBar(0.0, "Preparing Export")

        # strip extension from filename
        root_name, fileext = Blender.sys.splitext(Blender.sys.basename(filename))
        
        # get the root object from selected object
        if (Blender.Object.GetSelected() == None):
            raise NIFExportError("Please select the object(s) that you wish to export, and run this script again.")
        root_objects = []
        for root_object in Blender.Object.GetSelected():
            while (root_object.getParent() != None):
                root_object = root_object.getParent()
            if ((root_object.getType() != 'Empty') and (root_object.getType() != 'Mesh')):
                raise NIFExportError("Root object (%s) must be an 'Empty' or a 'Mesh' object."%root_object.getName())
            if (root_objects.count(root_object) == 0): root_objects.append(root_object)

        # check for animation groups definition in a text buffer called 'Anim'
        animtxt = None
        for txt in Blender.Text.Get():
            if txt.getName() == "Anim":
                animtxt = txt
                break
        
        # export nif:
        #------------
        if show_progress >= 1: Blender.Window.DrawProgressBar(0.33, "Converting to NIF")
        
        # create a nif object
        nif = nif4.NIF()
        
        # export the root node (note that transformation is ignored on the root node)
        nif = export_node(None, 'none', -1, 1.0, root_name, nif)
        # export objects
        for root_object in root_objects:
            # export the root objects as a NiNodes; their children are exported as well
            # note that localspace = worldspace, because root objects have no children
            nif = export_node(root_object, 'localspace', 0, scale_correction, root_object.getName(), nif)

        # export animation groups
        if (animtxt):
            nif = export_animgroups(animtxt, 1, nif) # we link the animation extra data to the first root_object node
            
        # write the file:
        #----------------
        if show_progress >= 1: Blender.Window.DrawProgressBar(0.66, "Writing NIF file")
        print nif # debug

        # make sure we have the right file extension
        if ((fileext != '.nif') and (fileext != '.NIF')):
            filename += '.nif'
        file = open(filename, "wb")
        try:
            nif.write(file)
        finally:
            # clean up: close file
            file.close()



        if (animtxt):
            # for some reason we must also have "x*.kf" and "x*.nif" files
            # x*.kf  contains a copy of the nif animation groups, the keyframes; it also has references to the animated nodes
            # x*.nif contains a copy of everything except for the animation groups and the keyframes

            # export xnif:
            #-------------
            xnif = export_xnif(nif)
            
            # write the file:
            #----------------
            xnif_filename = Blender.sys.join( Blender.sys.dirname( filename ), 'x' + root_name + '.nif' )
            file = open( xnif_filename, "wb" )
            try:
                xnif.write(file)
            finally:
                # clean up: close file
                file.close()
                
            # export xkf:
            #------------
            xkf = export_xkf(nif)
            
            # write the file:
            #----------------
            xkf_filename = Blender.sys.join( Blender.sys.dirname( filename ), 'x' + root_name + '.kf' )
            file = open( xkf_filename, "wb" )
            try:
                xkf.write(file)
            finally:
                # clean up: close file
                file.close()

        
        
    except NIFExportError, e: # in that case, we raise a menu instead of an exception
        if show_progress >= 1: Blender.Window.DrawProgressBar(1.0, "Export Failed")
        print 'NIFExportError: ' + e.value
        Blender.Draw.PupMenu('ERROR%t|' + e.value)
        return

    if show_progress >= 1: Blender.Window.DrawProgressBar(1.0, "Finished")
    
    # no export error, but let's double check: try reading the file(s) we just wrote
    # we can probably remove these lines once the exporter is stable
    try:
        nif = nif4.NIF()
        file = open(filename, "rb")
        nif.read(file)
        file.close()
    except:
        Blender.Draw.PupMenu("WARNING%t|Exported NIF file may not be valid: double check failed! This is probably due to an unknown bug in the exporter code.")
        raise # re-raise the exception



# 
# Export a mesh/empty object ob, child of nif block parent_block_id, as a
# NiNode block. Export also all children of ob, and return the updated
# nif.
#
# - space is 'none', 'worldspace', or 'localspace', and determines
#   relative to what object the transformation should be stored.
# - parent_block_id is the block index of the parent of the object (-1
#   for the root node)
# - for the root node, ob is None, and node_name is usually the base
#   filename (either with or without extension)
#
def export_node(ob, space, parent_block_id, parent_scale, node_name, nif):
    ipo = None
    ob_block_id = nif.header.nblocks # the block index number of the to be created block
    assert(ob_block_id == len(nif.blocks)) # debug

    # determine the block type, and append a new node to the nif block list
    if (ob == None):
        # -> root node
        assert(space == 'none')
        assert(parent_block_id == -1) # debug
        assert(nif.header.nblocks == 0) # debug
        nif.blocks.append(nif4.NiNode())
    else:
        assert((ob.getType() == 'Empty') or (ob.getType() == 'Mesh')) # debug
        assert(parent_block_id >= 0) # debug
        assert(nif.header.nblocks >= 1) # debug
        ipo = ob.getIpo() # get animation data
        if (ob.getName() == 'RootCollisionNode'):
            # -> root collision node
            # we export the root collision node as a child of the root node
            parent_block_id = 0
            space = 'worldspace'
            node_name = ''
            if (ipo != None):
                raise NIFExportError('ERROR%t|RootCollisionNode should not be animated.')
            nif.blocks.append(nif4.RootCollisionNode())
        else:
            # -> static or animated object
            nif.blocks.append(nif4.NiNode())
    
    nif.header.nblocks += 1

    # make it child of its parent in the nif, if it has one
    if (parent_block_id >= 0):
        nif.blocks[parent_block_id].children.indices.append(ob_block_id)
        nif.blocks[parent_block_id].children.num_indices += 1
    
    # and fill in this node's non-trivial values
    nif.blocks[ob_block_id].name = nif4.mystring(node_name)
    if (ob == None):
        nif.blocks[ob_block_id].flags = 0x000C # ? this seems pretty standard for the root node
    elif (ob.getName() == 'RootCollisionNode'):
        nif.blocks[ob_block_id].flags = 0x0003 # ? this seems pretty standard for the root collision node
    else:
        nif.blocks[ob_block_id].flags = 0x000C # ? this seems pretty standard for static and animated ninodes

    # if scale of NiNodes is not 1.0, then the engine does a bit
    # weird... let's play safe and require it to be 1.0
    nif.blocks[ob_block_id].translation, \
    nif.blocks[ob_block_id].rotation, \
    scale, \
    nif.blocks[ob_block_id].velocity  \
    = export_matrix(ob, space)
    nif.blocks[ob_block_id].scale = 1.0; # scale is taken into account under export_trishapes and export_children below
    # take care of the parent scale
    nif.blocks[ob_block_id].translation.x *= parent_scale
    nif.blocks[ob_block_id].translation.y *= parent_scale
    nif.blocks[ob_block_id].translation.z *= parent_scale

    if (ob != None):
        # export animation
        if (ipo != None):
            nif = export_keyframe(ob, space, ob_block_id, parent_scale, nif)
    
        # if it is a mesh, export the mesh as trishape children of this ninode
        # (we assume scale.x == scale.y == scale.z)
        if (ob.getType() == 'Mesh'):
            nif = export_trishapes(ob, 'none', ob_block_id, parent_scale * scale.x, nif) # the transformation of the mesh is already in the ninode block (except for scaling)

        # export all children of this empty/mesh object as children of this NiNode
        return export_children(ob, ob_block_id, parent_scale * scale.x, nif)
    else:
        return nif



#
# Export the animation of blender object ob as keyframe controller and keyframe data
#
def export_keyframe(ob, space, parent_block_id, parent_scale, nif):
    # -> get keyframe information
    
    assert(space == 'localspace') # we don't support anything else (yet)
    assert(nif.blocks[parent_block_id].block_type.value == "NiNode") # make sure the parent is of the right type
    
    # get frame start and frame end, and the number of frames per second
    scn = Blender.Scene.GetCurrent()
    context = scn.getRenderingContext()
 
    fspeed = 1.0 / context.framesPerSec()
    fstart = context.startFrame()
    fend = context.endFrame()

    # merge the animation curves into a rotation vector and translation vector curve
    ipo = ob.getIpo()
    assert(ipo != None) # debug
    rot_curve = {}
    trans_curve = {}
    for curve in ipo.getCurves():
        for btriple in curve.getPoints():
            knot = btriple.getPoints()
            frame = knot[0]
            ftime = (frame - 1) * fspeed
            if (curve.getName() == 'RotX') or (curve.getName() == 'RotY') or (curve.getName() == 'RotZ'):
                rot_curve[ftime] = Blender.Mathutils.Euler([10*ipo.getCurve('RotX').evaluate(frame), 10*ipo.getCurve('RotY').evaluate(frame), 10*ipo.getCurve('RotZ').evaluate(frame)]).toQuat()
            if (curve.getName() == 'LocX') or (curve.getName() == 'LocY') or (curve.getName() == 'LocZ'):
                trans_curve[ftime] = nif4.vec3()
                trans_curve[ftime].x = ipo.getCurve('LocX').evaluate(frame) * parent_scale
                trans_curve[ftime].y = ipo.getCurve('LocY').evaluate(frame) * parent_scale
                trans_curve[ftime].z = ipo.getCurve('LocZ').evaluate(frame) * parent_scale

    # -> now comes the real export

    # export keyframe stuff
    last_id = nif.header.nblocks - 1

    # add a keyframecontroller block, and refer to this block in the parent's time controller
    keyframectrl_id = last_id + 1
    last_id = keyframectrl_id
    assert(keyframectrl_id == len(nif.blocks)) # debug
    nif.blocks.append(nif4.NiKeyframeController()) # this should be block[keyframectrl_id]
    assert(nif.blocks[parent_block_id].controller == -1) # make sure we don't overwrite anything
    nif.blocks[parent_block_id].controller = keyframectrl_id
    nif.header.nblocks += 1

    # fill in the non-trivial values
    nif.blocks[keyframectrl_id].flags = 0x0008
    nif.blocks[keyframectrl_id].frequency = 1.0
    nif.blocks[keyframectrl_id].phase = 0.0
    nif.blocks[keyframectrl_id].start_time = (fstart - 1) * fspeed
    nif.blocks[keyframectrl_id].stop_time = (fend - fstart) * fspeed
    nif.blocks[keyframectrl_id].target_node = parent_block_id

    # add the keyframe data
    keyframedata_id = last_id + 1
    last_id = keyframedata_id
    assert(keyframedata_id == len(nif.blocks)) # debug
    nif.blocks.append(nif4.NiKeyframeData()) # this should be block[keyframedata_id]
    nif.blocks[keyframectrl_id].data = keyframedata_id
    nif.header.nblocks += 1

    nif.blocks[keyframedata_id].rotation_type = 1
    print dir(nif.blocks[keyframedata_id])
    ftimes = rot_curve.keys()
    ftimes.sort()
    for ftime in ftimes:
        rot_frame = nif4.keyrotation(nif.blocks[keyframedata_id].rotation_type)
        rot_frame.time = ftime
        rot_frame.quat.w = rot_curve[ftime].w
        rot_frame.quat.x = rot_curve[ftime].x
        rot_frame.quat.y = rot_curve[ftime].y
        rot_frame.quat.z = rot_curve[ftime].z
        nif.blocks[keyframedata_id].rotations.append(rot_frame)
    nif.blocks[keyframedata_id].num_rotations = len(nif.blocks[keyframedata_id].rotations)

    trans_count = 0
    nif.blocks[keyframedata_id].translation_type = 1
    ftimes = trans_curve.keys()
    ftimes.sort()
    for ftime in ftimes:
        trans_frame = nif4.keyvec3(nif.blocks[keyframedata_id].translation_type)
        trans_frame.time = ftime
        trans_frame.pos.x = trans_curve[ftime].x
        trans_frame.pos.y = trans_curve[ftime].y
        trans_frame.pos.z = trans_curve[ftime].z
        nif.blocks[keyframedata_id].translations.append(trans_frame)
    nif.blocks[keyframedata_id].num_translations = len(nif.blocks[keyframedata_id].translations)

    return nif



#
# parse the animation groups buffer and write an extra string data block,
# parented to the root block
#
def export_animgroups(animtxt, block_parent_id, nif):
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
    # 000/Idle: Start/Idle: Stop/Idle2: Start/Idle2: Loop Start
    # 050/Idle2: Stop/Idle3: Start
    # 100/Idle3: Loop Start/Idle3: Stop

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
        print 'frame %d'%f + ' -> \'%s\''%d # debug
        flist.append(f)
        dlist.append(d)
    
    # -> now comes the real export
    last_id = nif.header.nblocks - 1
    
    # add a NiTextKeyExtraData block, and refer to this block in the
    # parent node (we choose the root block)
    textextra_id = last_id + 1
    last_id = textextra_id
    assert(textextra_id == len(nif.blocks)) # debug
    nif.blocks.append(nif4.NiTextKeyExtraData())
    assert(nif.blocks[block_parent_id].extra_data == -1) # make sure we don't overwrite anything
    nif.blocks[block_parent_id].extra_data = textextra_id
    nif.header.nblocks += 1
    
    # create a NiTextKey for each frame descriptor
    nif.blocks[textextra_id].num_text_keys = len( flist )
    for i in range(len(flist)):
        nif.blocks[textextra_id].text_keys.append( nif4.keystring() )
        nif.blocks[textextra_id].text_keys[i].time = fspeed * (flist[i]-1);
        nif.blocks[textextra_id].text_keys[i].name = nif4.mystring(dlist[i]);
    
    return nif



#
# Export a blender object ob of the type mesh, child of nif block
# parent_block_id, as NiTriShape and NiTriShapeData blocks, possibly
# along with some NiTexturingProperty, NiSourceTexture,
# NiMaterialProperty, and NiAlphaProperty blocks. We export one
# trishape block per mesh material.
# 
def export_trishapes(ob, space, parent_block_id, parent_scale, nif):
    assert(ob.getType() == 'Mesh')

    # get mesh from ob
    mesh = Blender.NMesh.GetRaw(ob.data.name)

    # get the mesh's materials
    mesh_mats = mesh.getMaterials(1) # the argument guarantees that the material list agrees with the face material indices
    
    # if the mesh has no materials, all face material indices should be 0, so it's ok to fake one material in the material list
    if (mesh_mats == []):
        mesh_mats = [ None ]
    
    # let's now export one trishape for every mesh material
    
    materialIndex = 0 # material index of the current mesh material
    for mesh_mat in mesh_mats:
        # -> first, extract valuable info from our ob
        
        mesh_base_tex = None
        mesh_base_tex_alpha = 0 # set to 1 if the texture alpha channel overrides the material alpha value
        mesh_hasalpha = 0
        mesh_hastex = 0
        mesh_hasvcol = mesh.hasVertexColours()
        if (mesh_mat != None):
            mesh_hasvcol = mesh_hasvcol or (mesh_mat.mode & Blender.Material.Modes.VCOL_PAINT) # read the Blender Python API documentation to understand this hack
            mesh_mat_ambient = mesh_mat.getAmb()             # 'Amb' scrollbar in blender (MW -> 1.0 1.0 1.0)
            mesh_mat_diffuse_colour = mesh_mat.getRGBCol()   # 'Col' colour in Blender (MW -> 1.0 1.0 1.0)
            mesh_mat_specular_colour = mesh_mat.getSpecCol() # 'Spe' colour in Blender (MW -> 0.0 0.0 0.0)
            mesh_mat_emissive = mesh_mat.getEmit()           # 'Emit' scrollbar in Blender (MW -> 0.0 0.0 0.0)
            mesh_mat_shininess = mesh_mat.getSpec() / 2.0    # 'Spec' scrollbar in Blender, takes values between 0.0 and 2.0 (MW -> 0.0)
            mesh_mat_transparency = mesh_mat.getAlpha()      # 'A(lpha)' scrollbar in Blender (MW -> 1.0)
            mesh_hasalpha = (abs(mesh_mat_transparency - 1.0) > epsilon) \
                            or (mesh_mat.getIpo() != None and mesh_mat.getIpo().getCurve('Alpha'))
            # the base texture = first material texture
            # note that most morrowind files only have a base texture, so let's for now only support single textured materials
            for mtex in mesh_mat.getTextures():
                if (mtex != None):
                    if (mesh_base_tex == None):
                        if (mtex.texco != Blender.Texture.TexCo.UV):
                            # nif only support UV-mapped textures
                            raise NIFExportError("Non-UV texture in mesh '%s', material '%s'. Either delete all non-UV textures, or in the Shading Panel, under Material Buttons, set texture 'Map Input' to 'UV'."%(ob.getName(),mesh_mat.getName()))
                        if ((mtex.mapto & Blender.Texture.MapTo.COL) == 0):
                            # it should map to colour
                            raise NIFExportError("Non-COL-mapped texture in mesh '%s', material '%s', these cannot be exported to NIF. Either delete all non-COL-mapped textures, or in the Shading Panel, under Material Buttons, set texture 'Map To' to 'COL'."%(mesh.getName(),mesh_mat.getName()))
                        # got the base texture
                        mesh_base_tex = mtex.tex
                        # check if alpha channel is enabled for this texture; if so, set everything ready to override material alpha by texture alpha channel
                        if ((mesh_base_tex.imageFlags & Blender.Texture.ImageFlags.USEALPHA) and (mtex.mapto & Blender.Texture.MapTo.ALPHA)):
                            if (mesh_mat_transparency > epsilon):
                                raise NIFExportError("Alpha enabled textures can only be correctly exported with material alpha value 0.0")
                            mesh_mat_transparency = 0.0
                            mesh_hasalpha = 1
                            mesh_base_tex_alpha = 1
                    else:
                        raise NIFExportError("Multiple textures in mesh '%s', material '%s', this is not supported. Delete all textures, except for the base texture."%(mesh.getName(),mesh_mat.getName()))

        # note: we can be in any of the following three situations
        # material + base texture       -> normal object
        # material, but no base texture -> uniformly coloured object
        # no material                   -> typically, collision mesh

        # -> now comes the real export
        last_id = nif.header.nblocks - 1
        
        # add a trishape block, and refer to this block in the parent's children list
        trishape_id = last_id + 1
        last_id = trishape_id
        assert(trishape_id == len(nif.blocks)) # debug
        nif.blocks.append(nif4.NiTriShape()) # this should be block[trishape_id]
        nif.blocks[parent_block_id].children.indices.append(trishape_id)
        nif.blocks[parent_block_id].children.num_indices += 1
        nif.header.nblocks += 1
        
        # fill in the NiTriShape's non-trivial values
        if (nif.blocks[parent_block_id].name.value != ""):
            nif.blocks[trishape_id].name = nif4.mystring("Tri " + nif.blocks[parent_block_id].name.value + " %i"%(nif.blocks[parent_block_id].children.num_indices-1)) # Morrowind's child naming convention
        nif.blocks[trishape_id].flags = 0x0004 # ? this seems standard
        nif.blocks[trishape_id].translation, \
        nif.blocks[trishape_id].rotation, \
        scale, \
        nif.blocks[trishape_id].velocity \
        = export_matrix(ob, space)
        # scale correction
        nif.blocks[trishape_id].translation.x *= parent_scale
        nif.blocks[trishape_id].translation.y *= parent_scale
        nif.blocks[trishape_id].translation.z *= parent_scale
        # scaling is applied on vertices... here we put it on 1.0
        nif.blocks[trishape_id].scale = 1.0;
        final_scale = parent_scale * scale.x;
        
        if (mesh_base_tex != None):
            # add NiTriShape's texturing property
            tritexprop_id = last_id + 1
            last_id = tritexprop_id
            assert(tritexprop_id == len(nif.blocks)) # debug
            nif.blocks.append(nif4.NiTexturingProperty())
            nif.blocks[trishape_id].properties.indices.append(tritexprop_id)
            nif.blocks[trishape_id].properties.num_indices += 1
            nif.header.nblocks += 1
            
            nif.blocks[tritexprop_id].flags = 0x0001 # standard?
            nif.blocks[tritexprop_id].apply_mode = 2 # modulate?
            nif.blocks[tritexprop_id].texture_count = 7 # standard?
            
            nif.blocks[tritexprop_id].has_base_texture = 1
            nif.blocks[tritexprop_id].base_texture.clamp_mode = 3 # wrap in both directions
            nif.blocks[tritexprop_id].base_texture.filtermode = 2 # standard?
            nif.blocks[tritexprop_id].base_texture.texture_set = 0 # ? standard
            nif.blocks[tritexprop_id].base_texture.ps2_l = 0 # ? standard 
            nif.blocks[tritexprop_id].base_texture.ps2_k = 0xFFB5 # ? standard
            nif.blocks[tritexprop_id].base_texture.unknown = 0x0101 # ? standard
            
            # add NiTexturingProperty's texture source
            tritexsrc_id = last_id + 1
            last_id = tritexsrc_id
            assert(tritexsrc_id == len(nif.blocks)) # debug
            nif.blocks.append(nif4.NiSourceTexture())
            nif.blocks[tritexprop_id].base_texture.source = tritexsrc_id
            nif.header.nblocks += 1
            
            nif.blocks[tritexsrc_id].use_external = 1
            if ( strip_texpath == 2 ):
                # strip texture file path (original morrowind style)
                nif.blocks[tritexsrc_id].file_name = nif4.mystring(Blender.sys.basename(mesh_base_tex.image.getFilename()))
            elif ( strip_texpath == 1 ):
                # strip the data files prefix from the texture's file name
                tfn = mesh_base_tex.image.getFilename().lower()
                idx = tfn.find( "data files" )
                if ( idx >= 0 ):
                    tfn = tfn[idx+10:len(tfn)]
                    tfn = tfn.strip( '/\\' )
                    #print "Texture: %s"%tfn
                    nif.blocks[tritexsrc_id].file_name = nif4.mystring(tfn)
                else:
                    nif.blocks[tritexsrc_id].file_name = nif4.mystring(Blender.sys.basename(mesh_base_tex.image.getFilename()))
            else:
                # export full texture path
                nif.blocks[tritexsrc_id].file_name = nif4.mystring(mesh_base_tex.image.getFilename())
            # force dds extension, if requested
            if force_dds:
                nif.blocks[tritexsrc_id].file_name.value = nif.blocks[tritexsrc_id].file_name.value[:-4] + '.dds'
            nif.blocks[tritexsrc_id].pixel_layout = 5 # default
            nif.blocks[tritexsrc_id].use_mipmaps = 2  # default
            # choose alpha mapping
            # if ALPHA_DEFAULT is selected the texture alpha channel overides the material settings
            # if ALPHA_NONE is selected the material alpha setting is used
            if ( mesh_base_tex_alpha ):
                nif.blocks[tritexsrc_id].alpha_format = 3 # ALPHA_DEFAULT
            else:
                nif.blocks[tritexsrc_id].alpha_format = 0 # ALPHA_NONE
            nif.blocks[tritexsrc_id].unknown2 = 1 # ?

            # check for texture flip definition
            txtlist = Blender.Text.Get()
            for fliptxt in txtlist:
                if fliptxt.getName() == mesh_base_tex.getName():
                    break
                else:
                    fliptxt = None

            if fliptxt != None:
                tlist = fliptxt.asLines()

                # create a NiFlipController
                flip_id = last_id + 1
                last_id = flip_id
                assert(flip_id == len(nif.blocks)) # debug
                nif.blocks.append(nif4.NiFlipController())
                nif.blocks[tritexprop_id].next_controller = flip_id
                nif.header.nblocks += 1

                # get frame start and frame end, and the number of frames per second
                fspeed = 1.0 / Blender.Scene.GetCurrent().getRenderingContext().framesPerSec()
                fstart = Blender.Scene.GetCurrent().getRenderingContext().startFrame()
                fend = Blender.Scene.GetCurrent().getRenderingContext().endFrame()

                # fill in NiFlipController's values
                nif.blocks[flip_id].target_node = tritexprop_id
                nif.blocks[flip_id].flags = 0x0008
                nif.blocks[flip_id].frequency = 1.0
                nif.blocks[flip_id].start_time = 0.0
                nif.blocks[flip_id].stop_time = ( fend - fstart ) * fspeed
                nif.blocks[flip_id].flip_id = []
                #nif.blocks[flip_id].flip_id.append( tritexsrc_id )
                for t in tlist:
                    if len( t ) == 0:   # skip empty lines
                        continue
                    # create a NiSourceTexture for each flip
                    tsrc_id = last_id + 1
                    last_id = tsrc_id
                    nif.blocks.append( nif4.NiSourceTexture() )
                    nif.header.nblocks += 1
                    nif.blocks[tsrc_id].use_external = 1
                    nif.blocks[tsrc_id].file_name = nif4.mystring(t)
                    nif.blocks[tsrc_id].pixel_layout = nif.blocks[tritexsrc_id].pixel_layout
                    nif.blocks[tsrc_id].use_mipmaps  = nif.blocks[tritexsrc_id].use_mipmaps
                    nif.blocks[tsrc_id].alpha        = nif.blocks[tritexsrc_id].alpha
                    nif.blocks[tsrc_id].unknown2     = nif.blocks[tritexsrc_id].unknown2
                    nif.blocks[flip_id].sources.indices.append( tsrc_id )
                nif.blocks[flip_id].sources.num_indices = len( nif.blocks[flip_id].sources.indices )
                nif.blocks[flip_id].delta = nif.blocks[flip_id].stop_time / nif.blocks[flip_id].sources.num_indices
                
            
        if (mesh_hasalpha):
            # add NiTriShape's alpha propery (this is de facto an automated version of Detritus's method, see http://detritus.silgrad.com/alphahex.html)
            trialphaprop_id = last_id + 1
            last_id = trialphaprop_id
            assert(trialphaprop_id == len(nif.blocks))
            nif.blocks.append(nif4.NiAlphaProperty())
            nif.header.nblocks += 1
            
            nif.blocks[trialphaprop_id].flags   = 0x00ED
            nif.blocks[trialphaprop_id].unknown = 0
            
            # refer to the alpha property in the trishape block
            nif.blocks[trishape_id].properties.indices.append(trialphaprop_id)
            nif.blocks[trishape_id].properties.num_indices += 1

        if (mesh_mat != None):
            # add NiTriShape's specular property
            if ( mesh_mat_shininess > epsilon ):
                trispecprop_id = last_id + 1
                last_id = trispecprop_id
                assert(trispecprop_id == len(nif.blocks))
                nif.blocks.append(nif4.NiSpecularProperty())
                nif.header.nblocks += 1
                
                nif.blocks[trispecprop_id].flags = 0x0001
            
                # refer to the specular property in the trishape block
                nif.blocks[trishape_id].properties.indices.append(trispecprop_id)
                nif.blocks[trishape_id].properties.num_indices += 1
            
            # add NiTriShape's material property
            trimatprop_id = last_id + 1
            last_id = trimatprop_id
            assert(trimatprop_id == len(nif.blocks))
            nif.blocks.append(nif4.NiMaterialProperty())
            nif.header.nblocks += 1
            
            nif.blocks[trimatprop_id].name = nif4.mystring(mesh_mat.getName())
            nif.blocks[trimatprop_id].flags = 0x0001 # ? standard
            nif.blocks[trimatprop_id].ambient_color.r = mesh_mat_ambient * mesh_mat_diffuse_colour[0]
            nif.blocks[trimatprop_id].ambient_color.g = mesh_mat_ambient * mesh_mat_diffuse_colour[1]
            nif.blocks[trimatprop_id].ambient_color.b = mesh_mat_ambient * mesh_mat_diffuse_colour[2]
            nif.blocks[trimatprop_id].diffuse_color.r = mesh_mat_diffuse_colour[0]
            nif.blocks[trimatprop_id].diffuse_color.g = mesh_mat_diffuse_colour[1]
            nif.blocks[trimatprop_id].diffuse_color.b = mesh_mat_diffuse_colour[2]
            nif.blocks[trimatprop_id].specular_color.r = mesh_mat_specular_colour[0]
            nif.blocks[trimatprop_id].specular_color.g = mesh_mat_specular_colour[1]
            nif.blocks[trimatprop_id].specular_color.b = mesh_mat_specular_colour[2]
            nif.blocks[trimatprop_id].emissive_color.r = mesh_mat_emissive * mesh_mat_diffuse_colour[0]
            nif.blocks[trimatprop_id].emissive_color.g = mesh_mat_emissive * mesh_mat_diffuse_colour[1]
            nif.blocks[trimatprop_id].emissive_color.b = mesh_mat_emissive * mesh_mat_diffuse_colour[2]
            nif.blocks[trimatprop_id].glossiness = mesh_mat_shininess
            nif.blocks[trimatprop_id].alpha = mesh_mat_transparency
            
            # refer to the material property in the trishape block
            nif.blocks[trishape_id].properties.indices.append(trimatprop_id)
            nif.blocks[trishape_id].properties.num_indices += 1
        

            # material animation
            ipo = mesh_mat.getIpo()
            a_curve = None
            alphactrl_id = -1
            if ( ipo != None ):
                a_curve = ipo.getCurve( 'Alpha' )
                # get frame start and the number of frames per second
                scn = Blender.Scene.GetCurrent()
                context = scn.getRenderingContext()
                fspeed = 1.0 / context.framesPerSec()
                fstart = context.startFrame()
            
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
                alphactrl_id = last_id + 1
                last_id = alphactrl_id
                assert(alphactrl_id == len(nif.blocks)) # debug
                nif.blocks.append(nif4.NiAlphaController()) # this should be block[matcolctrl_id]
                assert(nif.blocks[trimatprop_id].controller == -1) # make sure we don't overwrite anything
                nif.blocks[trimatprop_id].controller = alphactrl_id
                nif.blocks[alphactrl_id].target_node = trimatprop_id
                nif.header.nblocks += 1

                # select extrapolation mode
                if ( a_curve.getExtrapolation() == "Cyclic" ):
                    nif.blocks[alphactrl_id].flags = 0x0008
                elif ( a_curve.getExtrapolation() == "Constant" ):
                    nif.blocks[alphactrl_id].flags = 0x000c
                else:
                    print "extrapolation \"%s\" for alpha curve not supported using \"cycle reverse\" instead"%a_curve.getExtrapolation()
                    nif.blocks[alphactrl_id].flags = 0x000a

                # fill in timing values
                nif.blocks[alphactrl_id].frequency = 1.0
                nif.blocks[alphactrl_id].phase = 0.0
                nif.blocks[alphactrl_id].start_time = ftimes[0]
                nif.blocks[alphactrl_id].stop_time = ftimes[len(ftimes)-1]

                # add the alpha data
                alphadata_id = last_id + 1
                last_id = alphadata_id
                assert(alphadata_id == len(nif.blocks)) # debug
                nif.blocks.append(nif4.NiFloatData())
                nif.blocks[alphactrl_id].data = alphadata_id
                nif.header.nblocks += 1

                # select interpolation mode and export the alpha curve data
                if ( a_curve.getInterpolation() == "Linear" ):
                    nif.blocks[alphadata_id].key_type = 1
                elif ( a_curve.getInterpolation() == "Bezier" ):
                    nif.blocks[alphadata_id].key_type = 2
                else:
                    raise NIFExportError( 'interpolation %s for alpha curve not supported use linear or bezier instead'%a_curve.getInterpolation() )

                for ftime in ftimes:
                    a_frame = nif4.keyfloat( nif.blocks[alphadata_id].key_type )
                    a_frame.time = ftime
                    a_frame.value = alpha[ftime]
                    a_frame.forward = 0.0 # ?
                    a_frame.backward = 0.0 # ?
                    nif.blocks[alphadata_id].keys.append(a_frame)
                nif.blocks[alphadata_id].num_keys = len(nif.blocks[alphadata_id].keys)

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
                matcolctrl_id = last_id + 1
                last_id = matcolctrl_id
                assert(matcolctrl_id == len(nif.blocks)) # debug
                nif.blocks.append(nif4.NiMaterialColorController()) # this should be block[matcolctrl_id]
                if ( alphactrl_id == -1 ):
                    assert(nif.blocks[trimatprop_id].controller == -1) # make sure we don't overwrite anything
                    nif.blocks[trimatprop_id].controller = matcolctrl_id
                else:
                    assert(nif.blocks[alphactrl_id].next_controller == -1)
                    nif.blocks[alphactrl_id].next_controller = matcolctrl_id
                nif.header.nblocks += 1

                # fill in the non-trivial values
                nif.blocks[matcolctrl_id].flags = 0x0008 # using cycle loop for now
                nif.blocks[matcolctrl_id].frequency = 1.0
                nif.blocks[matcolctrl_id].phase = 0.0
                nif.blocks[matcolctrl_id].start_time = ftimes[0]
                nif.blocks[matcolctrl_id].stop_time = ftimes[len(ftimes)-1]
                nif.blocks[matcolctrl_id].target_node = trimatprop_id

                # add the material color data
                matcoldata_id = last_id + 1
                last_id = matcoldata_id
                assert(matcoldata_id == len(nif.blocks)) # debug
                nif.blocks.append(nif4.NiColorData())
                nif.blocks[matcolctrl_id].data = matcoldata_id
                nif.header.nblocks += 1

                # export the resulting rgba curve
                for ftime in ftimes:
                    rgba_frame = nif4.keyrgba()
                    rgba_frame.time = ftime
                    rgba_frame.rgba = rgba_curve[ftime]
                    nif.blocks[matcoldata_id].keys.indices.append(rgba_frame)
                nif.blocks[matcoldata_id].keys.num_indices = len(nif.blocks[matcoldata_id].keys)
                nif.blocks[matcoldata_id].dunno = 1

        # add NiTriShape's data
        tridata_id = last_id + 1
        last_id = tridata_id
        assert(tridata_id == len(nif.blocks))
        nif.blocks.append(nif4.NiTriShapeData())
        nif.blocks[trishape_id].data = tridata_id
        nif.header.nblocks += 1
        
        # set faces, vertices, uv-vertices, and normals
        nif.blocks[tridata_id].has_vertices = 1
        nif.blocks[tridata_id].has_vertex_colors = mesh_hasvcol
        if (mesh_hastex):
            nif.blocks[tridata_id].has_uv = 1
            nif.blocks[tridata_id].num_uv_sets = 1 # for now, we only have one texture for this trishape
        else:
            nif.blocks[tridata_id].has_uv = 0
            nif.blocks[tridata_id].num_uv_sets = 0
        if (mesh_mat != None):
            nif.blocks[tridata_id].has_normals = 1 # if we have a material, we should add normals for proper lighting
        else:
            nif.blocks[tridata_id].has_normals = 0
        nif.blocks[tridata_id].uv_sets = [ [] ] * nif.blocks[tridata_id].num_uv_sets # uv_sets now has num_uv_sets elements, namely, an empty list of uv vertices for each set of uv coordinates

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
        count = 0
        for f in mesh.faces:
            if show_progress >= 2: Blender.Window.DrawProgressBar(0.33 * float(count)/len(mesh.faces), "Converting to NIF (%s)"%ob.getName())
            count += 1
            # does the face belong to this trishape?
            if (mesh_mat != None): # we have a material
                if (f.materialIndex != materialIndex): # but this face has another material
                    continue # so skip this face
            f_numverts = len(f.v)
            if (f_numverts < 3): continue # ignore degenerate faces
            assert((f_numverts == 3) or (f_numverts == 4)) # debug
            if (nif.blocks[tridata_id].has_uv):
                if (len(f.uv) != len(f.v)): # make sure we have UV data
                    raise NIFExportError('ERROR%t|Create a UV map for every texture, and run the script again.')
            # find (vert, uv-vert, normal, vcol) quad, and if not found, create it
            f_index = [ -1 ] * f_numverts
            for i in range(f_numverts):
                fv = nif4.vec3()
                fv.x = f.v[i][0] * final_scale
                fv.y = f.v[i][1] * final_scale
                fv.z = f.v[i][2] * final_scale
                # get vertex normal for lighting (smooth = Blender vertex normal, non-smooth = Blender face normal)
                fn = nif4.vec3()
                if nif.blocks[tridata_id].has_normals:
                    if f.smooth:
                        fn.x = f.v[i].no[0]
                        fn.y = f.v[i].no[1]
                        fn.z = f.v[i].no[2]
                    else:
                        fn.x = f.no[0]
                        fn.y = f.no[1]
                        fn.z = f.no[2]
                else:
                    fn = None
                if (nif.blocks[tridata_id].has_uv):
                    fuv = nif4.vec2()
                    fuv.u = f.uv[i][0]
                    fuv.v = 1.0 - f.uv[i][1] # NIF flips the texture V-coordinate (OpenGL standard)
                else:
                    fuv = None
                if (nif.blocks[tridata_id].has_vertex_colors):
                    fcol = nif4.rgba()
                    fcol.r = f.col[i].r / 255.0 # NIF stores the colour values as floats
                    fcol.g = f.col[i].g / 255.0
                    fcol.b = f.col[i].b / 255.0
                    fcol.a = f.col[i].a / 255.0
                else:
                    fcol = None
                    
                vertquad = ( fv, fuv, fn, fcol )

                # do we already have this quad? (optimized by m4444x)
                f_index[i] = len(vertquad_list)
                v_index = f.v[i].index
                if ( vertex_opt == 0 ):
                    if vertmap[v_index]:
                        # iterate only over vertices with the same vertex index
                        # and check if they have the same uvs, normals and colors (wow is that fast!)
                        for j in vertmap[v_index]:
                            if abs(vertquad[0].x - vertquad_list[j][0].x) > epsilon: continue # obsolete?
                            if abs(vertquad[0].y - vertquad_list[j][0].y) > epsilon: continue # obsolete?
                            if abs(vertquad[0].z - vertquad_list[j][0].z) > epsilon: continue # obsolete?
                            if nif.blocks[tridata_id].has_uv:
                                if abs(vertquad[1].u - vertquad_list[j][1].u) > epsilon: continue
                                if abs(vertquad[1].v - vertquad_list[j][1].v) > epsilon: continue
                            if nif.blocks[tridata_id].has_normals:
                                if abs(vertquad[2].x - vertquad_list[j][2].x) > epsilon: continue
                                if abs(vertquad[2].y - vertquad_list[j][2].y) > epsilon: continue
                                if abs(vertquad[2].z - vertquad_list[j][2].z) > epsilon: continue
                            if nif.blocks[tridata_id].has_vertex_colors:
                                if abs(vertquad[3].r - vertquad_list[j][3].r) > epsilon: continue
                                if abs(vertquad[3].g - vertquad_list[j][3].g) > epsilon: continue
                                if abs(vertquad[3].b - vertquad_list[j][3].b) > epsilon: continue
                                if abs(vertquad[3].a - vertquad_list[j][3].a) > epsilon: continue
                            # all tests passed: so yes, we already have it!
                            f_index[i] = j
                            break
                else:
                    # iterate over all vertices exported so far and check if one is matching
                    for j in range(len(vertquad_list)):
                        if abs(vertquad[0].x - vertquad_list[j][0].x) > epsilon: continue
                        if abs(vertquad[0].y - vertquad_list[j][0].y) > epsilon: continue
                        if abs(vertquad[0].z - vertquad_list[j][0].z) > epsilon: continue
                        if nif.blocks[tridata_id].has_uv:
                            if abs(vertquad[1].u - vertquad_list[j][1].u) > epsilon: continue
                            if abs(vertquad[1].v - vertquad_list[j][1].v) > epsilon: continue
                        if nif.blocks[tridata_id].has_normals:
                            if abs(vertquad[2].x - vertquad_list[j][2].x) > epsilon: continue
                            if abs(vertquad[2].y - vertquad_list[j][2].y) > epsilon: continue
                            if abs(vertquad[2].z - vertquad_list[j][2].z) > epsilon: continue
                        if nif.blocks[tridata_id].has_vertex_colors:
                            if abs(vertquad[3].r - vertquad_list[j][3].r) > epsilon: continue
                            if abs(vertquad[3].g - vertquad_list[j][3].g) > epsilon: continue
                            if abs(vertquad[3].b - vertquad_list[j][3].b) > epsilon: continue
                            if abs(vertquad[3].a - vertquad_list[j][3].a) > epsilon: continue
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
                    nif.blocks[tridata_id].vertices.append(fv)
                    # and add the vertex normal
                    if (nif.blocks[tridata_id].has_normals):
                        nif.blocks[tridata_id].normals.append(fn)
                    # for each texture set, add the uv-vertex
                    if (nif.blocks[tridata_id].has_uv):
                        for texset in range(nif.blocks[tridata_id].num_uv_sets):
                            nif.blocks[tridata_id].uv_sets[texset].append(fuv)
                    # add the vertex colour
                    if (nif.blocks[tridata_id].has_vertex_colors):
                        nif.blocks[tridata_id].vertex_colors.append(fcol)
            # now add the (hopefully, convex) face, in triangles
            for i in range(f_numverts - 2):
                f_indexed = nif4.face()
                f_indexed.v1 = f_index[0]
                if (final_scale > 0):
                    f_indexed.v2 = f_index[1+i]
                    f_indexed.v3 = f_index[2+i]
                else:
                    f_indexed.v2 = f_index[2+i]
                    f_indexed.v3 = f_index[1+i]
                nif.blocks[tridata_id].faces.append(f_indexed)

        # update the counters
        nif.blocks[tridata_id].num_vertices = len(vertquad_list)
        nif.blocks[tridata_id].num_faces = len(nif.blocks[tridata_id].faces)
        nif.blocks[tridata_id].num_faces_x3 = nif.blocks[tridata_id].num_faces * 3

        # center
        count = 0
        for v in mesh.verts:
            if show_progress >= 2: Blender.Window.DrawProgressBar(0.33 + 0.33 * float(count)/len(mesh.verts), "Converting to NIF (%s)"%ob.getName())
            count += 1
            nif.blocks[tridata_id].center.x += v[0]
            nif.blocks[tridata_id].center.y += v[1]
            nif.blocks[tridata_id].center.z += v[2]
        assert(len(mesh.verts) > 0) # debug
        nif.blocks[tridata_id].center.x /= len(mesh.verts)
        nif.blocks[tridata_id].center.y /= len(mesh.verts)
        nif.blocks[tridata_id].center.z /= len(mesh.verts)
        
        # radius
        count = 0
        for v in mesh.verts:
            if show_progress >= 2: Blender.Window.DrawProgressBar(0.66 + 0.33 * float(count)/len(mesh.verts), "Converting to NIF (%s)"%ob.getName())
            count += 1
            r = get_distance(v, nif.blocks[tridata_id].center)
            if (r > nif.blocks[tridata_id].radius):
                nif.blocks[tridata_id].radius = r

        # correct scale
        nif.blocks[tridata_id].center.x *= final_scale
        nif.blocks[tridata_id].center.y *= final_scale
        nif.blocks[tridata_id].center.z *= final_scale
        nif.blocks[tridata_id].radius *= final_scale

        materialIndex += 1 # ...and process the next material

    # return updated nif
    return nif



#
# EXPERIMENTAL: Export texture effect.
# 
def export_textureeffect(ob, parent_block_id, parent_scale, nif):
    assert(ob.getType() == 'Empty')
    last_id = nif.header.nblocks - 1
    
    # add a trishape block, and refer to this block in the parent's children list
    texeff_id = last_id + 1
    last_id = texeff_id
    assert(texeff_id == len(nif.blocks)) # debug
    nif.blocks.append(nif4.NiTextureEffect()) # this should be block[texeff_id]
    nif.blocks[parent_block_id].children.indices.append(texeff_id)
    nif.blocks[parent_block_id].children.num_indices += 1
    nif.blocks[parent_block_id].effects.indices.append(texeff_id)
    nif.blocks[parent_block_id].effects.num_indices += 1
    nif.header.nblocks += 1
        
    # fill in the NiTextureEffect's non-trivial values
    nif.blocks[texeff_id].flags = 0x0004
    nif.blocks[texeff_id].translation, \
    nif.blocks[texeff_id].rotation, \
    scale, \
    nif.blocks[texeff_id].velocity \
    = export_matrix(ob, 'none')
    # scale correction
    nif.blocks[texeff_id].translation.x *= parent_scale
    nif.blocks[texeff_id].translation.y *= parent_scale
    nif.blocks[texeff_id].translation.z *= parent_scale
    # ... not sure what scaling does to a texture effect
    nif.blocks[texeff_id].scale = 1.0;
    
    # guessing
    nif.blocks[texeff_id].unknown2[0] = 1.0
    nif.blocks[texeff_id].unknown2[1] = 0.0
    nif.blocks[texeff_id].unknown2[2] = 0.0
    nif.blocks[texeff_id].unknown2[3] = 0.0
    nif.blocks[texeff_id].unknown2[4] = 1.0
    nif.blocks[texeff_id].unknown2[5] = 0.0
    nif.blocks[texeff_id].unknown2[6] = 0.0
    nif.blocks[texeff_id].unknown2[7] = 0.0
    nif.blocks[texeff_id].unknown2[8] = 1.0
    nif.blocks[texeff_id].unknown2[9] = 0.0
    nif.blocks[texeff_id].unknown2[10] = 0.0
    nif.blocks[texeff_id].unknown2[11] = 0.0
    nif.blocks[texeff_id].unknown3[0] = 2
    nif.blocks[texeff_id].unknown3[1] = 3
    nif.blocks[texeff_id].unknown3[2] = 2
    nif.blocks[texeff_id].unknown3[3] = 2
    nif.blocks[texeff_id].unknown4 = 0
    nif.blocks[texeff_id].unknown5[0] = 1.0
    nif.blocks[texeff_id].unknown5[1] = 0.0
    nif.blocks[texeff_id].unknown5[2] = 0.0
    nif.blocks[texeff_id].unknown5[3] = 0.0
    nif.blocks[texeff_id].ps2_l = 0
    nif.blocks[texeff_id].ps2_k = 0xFFB5
    nif.blocks[texeff_id].unknown6 = 0

    # add NiTextureEffect's texture source
    nif.blocks[texeff_id].source_id = 91

    texsrc_id = last_id + 1
    last_id = texsrc_id
    assert(texsrc_id == len(nif.blocks)) # debug
    nif.blocks.append(nif4.NiSourceTexture())
    nif.blocks[texeff_id].source = texsrc_id
    nif.header.nblocks += 1
            
    nif.blocks[texsrc_id].use_external = 1
    nif.blocks[texsrc_id].file_name = nif4.mystring('enviro 01.TGA') # ?
    nif.blocks[texsrc_id].pixel_layout = 5 # default?
    nif.blocks[texsrc_id].mipmap = 1 # default?
    nif.blocks[texsrc_id].alpha = 3 # default?
    nif.blocks[texsrc_id].unknown2 = 1 # ?

    return nif

# 
# Export all children of blender object ob, already stored in
# nif.blocks[ob_block_id], and return the updated nif.
# 
def export_children(ob, ob_block_id, parent_scale, nif):
    # loop over all ob's children
    for ob_child in Blender.Object.Get():
        if (ob_child.getParent() == ob):
            # we found a child! try to add it to ob's children
            # is it a texture effect node?
            if ((ob_child.getType() == 'Empty') and (ob_child.getName()[:13] == 'TextureEffect')):
                nif = export_textureeffect(ob_child, ob_block_id, parent_scale, nif)
            # is it a regular node?
            elif (ob_child.getType() == 'Mesh') or (ob_child.getType() == 'Empty'):
                nif = export_node(ob_child, 'localspace', ob_block_id, parent_scale, ob_child.getName(), nif)

    # return updated nif
    return nif

#
# Convert an object's transformation matrix to a niflib quadrupple ( translate, rotate, scale, velocity ).
# The scale is a vector; but non-uniform scaling is not supported by the nif format, so for these we'll have to apply the transformation
# when exporting the vertex coordinates... ?
#
def export_matrix(ob, space):
    global epsilon
    nt = nif4.vec3()
    nr = nif4.mat3x3()
    ns = nif4.vec3()
    nv = nif4.vec3()
    
    # decompose
    bs, br, bt = getObjectSRT(ob, space)
    
    # and fill in the values
    nt.x = bt[0]
    nt.y = bt[1]
    nt.z = bt[2]
    nr.x.x = br[0][0]
    nr.x.y = br[1][0]
    nr.x.z = br[2][0]
    nr.y.x = br[0][1]
    nr.y.y = br[1][1]
    nr.y.z = br[2][1]
    nr.z.x = br[0][2]
    nr.z.y = br[1][2]
    nr.z.z = br[2][2]
    ns.x = bs[0]
    ns.y = bs[1]
    ns.z = bs[2]
    nv.x = 0.0
    nv.y = 0.0
    nv.z = 0.0

    # for now, we don't support non-uniform scaling
    if abs(ns.x - ns.y) + abs(ns.y - ns.z) > epsilon:
        raise NIFExportError('ERROR%t|non-uniformly scaled objects not yet supported; apply size and rotation (CTRL-A in Object Mode) and try again.')

    # return result
    return (nt, nr, ns, nv)



# Find scale, rotation, and translation components of an
# object. Returns a triple (bs, br, bt), where bs is a scale vector,
# br is a 3x3 rotation matrix, and bt is a translation vector. It
# should hold that "ob.getMatrix(space) == bs * br * bt".
def getObjectSRT(ob, space):
    global epsilon
    if (space == 'none'):
        bs = Blender.Mathutils.Vector([1.0, 1.0, 1.0])
        br = Blender.Mathutils.Matrix()
        br.identity()
        bt = Blender.Mathutils.Vector([0.0, 0.0, 0.0])
        return (bs, br, bt)
    assert((space == 'worldspace') or (space == 'localspace'))
    mat = ob.getMatrix('worldspace')
    # localspace bug fix:
    if (space == 'localspace'):
        if (ob.getParent() != None):
            matparentinv = ob.getParent().getMatrix('worldspace')
            matparentinv.invert()
            mat = mat * matparentinv
    
    # get translation
    bt = mat.translationPart()
    
    # get the rotation part, this is scale * rotation
    bsr = mat.rotationPart()
    
    # get the squared scale matrix
    bsrT = Blender.Mathutils.CopyMat(bsr)
    bsrT.transpose()
    bs2 = bsr * bsrT # bsr * bsrT = bs * br * brT * bsT = bs^2
    # debug: br2's off-diagonal elements must be zero!
    assert(abs(bs2[0][1]) + abs(bs2[0][2]) \
        + abs(bs2[1][0]) + abs(bs2[1][2]) \
        + abs(bs2[2][0]) + abs(bs2[2][1]) < epsilon)
    
    # get scale components
    bs = Blender.Mathutils.Vector(\
         [ sqrt(bs2[0][0]), sqrt(bs2[1][1]), sqrt(bs2[2][2]) ])
    # and fix their sign
    if (bsr.determinant() < 0): bs.negate()
    
    # get the rotation matrix
    br = Blender.Mathutils.Matrix(\
        [ bsr[0][0]/bs[0], bsr[0][1]/bs[0], bsr[0][2]/bs[0] ],\
        [ bsr[1][0]/bs[1], bsr[1][1]/bs[1], bsr[1][2]/bs[1] ],\
        [ bsr[2][0]/bs[2], bsr[2][1]/bs[2], bsr[2][2]/bs[2] ])
    
    # debug: rotation matrix must have determinant 1
    assert(abs(br.determinant() - 1.0) < epsilon)

    # debug: rotation matrix must satisfy orthogonality constraint
    for i in range(3):
        for j in range(3):
            sum = 0.0
            for k in range(3):
                sum += br[k][i] * br[k][j]
            if (i == j): assert(abs(sum - 1.0) < epsilon)
            if (i != j): assert(abs(sum) < epsilon)
    
    # debug: the product of the scaling values must be equal to the determinant of the blender rotation part
    assert(abs(bs[0]*bs[1]*bs[2] - bsr.determinant()) < epsilon)
    
    # TODO: debug: check that indeed bm == bs * br * bt

    return (bs, br, bt)



# calculate distance between two vectors
def get_distance(v, w):
    return sqrt((v[0]-w.x)*(v[0]-w.x) + (v[1]-w.y)*(v[1]-w.y) + (v[2]-w.z)*(v[2]-w.z))



# (WARNING this function changes it's argument, you should only call this after writing <root_name>.nif and x<root_name>.nif)
def export_xkf(nif):
    xkf = nif4.NIF()
    xkf.blocks.append( nif4.NiSequenceStreamHelper() )
    xkf.header.nblocks += 1

    controller_id = []

    # save extra text data
    for block in nif.blocks:
        if (block.block_type.value == 'NiTextKeyExtraData'):
            xkf.blocks.append(block) # we can do this: it does not contain any references
            xkf.blocks[0].extra_data = xkf.header.nblocks
            last_extra_id = xkf.header.nblocks
            xkf.header.nblocks += 1
            break
    else:
        assert(0) # debug, we must break from the above loop

    # find nodes with keyframe controller
    for block in nif.blocks:
        if (block.block_type.value == "NiNode"):
            if (block.controller >= 0):
                controller_id.append( block.controller )
                # link to the original node with a NiStringExtraData
                xkf.blocks[last_extra_id].extra_data = xkf.header.nblocks
                last_extra_id = xkf.header.nblocks + 1
                stringextra = nif4.NiStringExtraData()
                stringextra.string_data = block.name
                stringextra.bytes_remaining = 4 + len(stringextra.string_data.value)
                xkf.blocks.append(stringextra)
                xkf.header.nblocks += 1

    # copy keyframe controllers and keyframe datas
    if (len(controller_id) == 0): raise NIFExportError("Animation groups defined, but no meshes are animated.")
    last_controller_id = 0
    for cid in controller_id:
        # get the keyframe controller block from nif
        kfcontroller = nif.blocks[ cid ]
        xkf.blocks.append( nif.blocks[ cid ] ) # copy it
        xkf.blocks[ last_controller_id ].next_controller = xkf.header.nblocks # refer to it
        last_controller_id = xkf.header.nblocks
        xkf.header.nblocks += 1

        assert(kfcontroller.data >= 0) # debug
        xkf.blocks.append( nif.blocks[ kfcontroller.data ] )

        # now "fix" the references
        xkf.blocks[ last_controller_id ].target_node = -1
        xkf.blocks[ last_controller_id ].data = xkf.header.nblocks
        xkf.header.nblocks += 1
    
    return xkf



def export_xnif(nif):
    # TODO delete keyframe controllers and keyframe data
    # but apparently it still works if we leave everything in place
    # so we make it ourselves very easy
    return nif

# start blender file selector for export
Blender.Window.FileSelector(export_nif, "Export NIF")
