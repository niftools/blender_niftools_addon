#!BPY

"""
Name: 'Morph Copy'
Blender: 245
Group: 'MESH'
Tooltip: 'Copy morph vectors from 1 mesh, to all other selected meshes.'
"""

__author__ = "Amorilia"
__url__ = ("blender", "elysiun", "http://niftools.sourceforge.net/")
__version__ = "1.0"
__bpydoc__ = """\

Morph Copy

This script is used to copy morphs from 1 mesh with weights (the
source mesh) to many (the target meshes). Morphs are copied from 1
mesh to another based on how close they are together.

For normal operation, select 1 source mesh with morphs and any number
of unmorphed meshes that overlap the source mesh. Then run this script
using default options and check the new morphs.

A different way to use this script is to update the morphs on an
already morphed mesh. This is done using the "Copy to Selected" option
enabled and works a bit differently, With the target mesh, select the
verts you want to update. Since all meshes have morphs we can't just
use the morphed mesh as the source, so the Active Object is used for
the source mesh. Run the script and the selected verts on all non
active meshes will be updated.
"""

# -------------------------------------------------------------------------- 
# Morph Copy 1.0 by Amorilia 
# -------------------------------------------------------------------------- 
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2005-2011, NIF File Format Library and Tools
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
# -------------------------------------------------------------------------- 

# credits:
# - Scanti for his conformulator
# - ideasman42 for his bone weight copy script, which is quite similar
#   to this script



import Blender
from Blender import Window, sys

SMALL_NUM = 0.000001

def get_snap_idx(seek_vec, vecs, PREF_NO_XCROSS):
    """Returns the closest vec in vecs to seek_vec."""
    
    # First seek the closest Z axis vert idx/v
    seek_vec_x, seek_vec_y, seek_vec_z = seek_vec
    
    from_vec_idx = 0
    
    len_vecs = len(vecs)
    
    upidx = len_vecs - 1
    loidx = 0
    
    # find first vertex which has z coordinate larger than seek_vec
    while from_vec_idx < len_vecs and vecs[from_vec_idx][1].z < seek_vec_z:
        from_vec_idx += 1
    
    # clamp if we overstepped.
    if from_vec_idx  >= len_vecs:
        from_vec_idx -= 1
    
    close_dist = (vecs[from_vec_idx][1]-seek_vec).length
    close_idx = vecs[from_vec_idx][0]
    
    upidx = from_vec_idx+1
    loidx = from_vec_idx-1
    
    # Set uselo/useup. This means we can keep seeking up/down.
    useup = (upidx < len_vecs)
    uselo = (loidx >= 0)
    
    # Seek up/down to find the closest v to seek vec.
    while uselo or useup:
        if useup:
            if upidx >= len_vecs:
                useup = False
            else:
                i, v = vecs[upidx]
                if (not PREF_NO_XCROSS) or ((v.x >= -SMALL_NUM and seek_vec_x >= -SMALL_NUM) or (v.x <= SMALL_NUM and seek_vec_x <= SMALL_NUM)): # enfoce  xcrossing
                    if v.z - seek_vec_z > close_dist:
                        # the verticle distance is greater then the best distance sofar. we can stop looking up.
                        useup = False
                    elif abs(seek_vec_y-v.y) < close_dist and abs(seek_vec_x-v.x) < close_dist:
                        # This is in the limit measure it.
                        dist = (seek_vec-v).length
                        if dist < close_dist:
                            close_dist = dist
                            close_idx = i
                upidx+=1
        
        if uselo:
            if loidx < 0:
                uselo = False
            else:
                i, v = vecs[loidx]
                if (not PREF_NO_XCROSS) or ((v.x >= -SMALL_NUM and seek_vec_x >= -SMALL_NUM) or (v.x <= SMALL_NUM and seek_vec_x  <= SMALL_NUM)): # enfoce  xcrossing
                    if seek_vec_z - v.z > close_dist:
                        # the verticle distance is greater then the best distance sofar. we can stop looking up.
                        uselo = False
                    elif abs(seek_vec_y-v.y) < close_dist and abs(seek_vec_x-v.x) < close_dist:
                        # This is in the limit measure it.
                        dist = (seek_vec-v).length
                        if dist < close_dist:
                            close_dist = dist
                            close_idx = i
                loidx -= 1
            
    return close_idx

def copy_morphs(_from, _to, PREF_SEL_ONLY, PREF_NO_XCROSS):
    ob_from, me_from, world_verts_from, from_morph_key = _from
    ob_to, me_to, world_verts_to, dummy = _to   
    del dummy

    # insert base key at frame 1, using relative keys
    me_to.insertKey(1, 'relative')

    # list of snap indices
    snap_indices = [get_snap_idx(co, world_verts_from, PREF_NO_XCROSS)
                    for idx, co in world_verts_to]

    # create keys
    for i, from_key_block in enumerate(me_from.key.blocks[1:]):

        # report progress
        Window.DrawProgressBar(0.01
                               + 0.98 * (i/float(len(me_from.key.blocks) - 1)),
                               'Copy "%s" -> "%s" '
                               % (ob_from.name, ob_to.name))

        # get deformation
        morph = [vec_new - vec_old
                 for (vec_new, vec_old) in zip(from_key_block.data,
                                                me_from.key.blocks[0].data)]
        
        # deform me_to
        for me_to_vert, me_to_vert_base, snap_idx in zip(me_to.vertices, me_to.key.blocks[0].data, snap_indices):
            me_to_vert.co[0] = me_to_vert_base[0] + morph[snap_idx][0]
            me_to_vert.co[1] = me_to_vert_base[1] + morph[snap_idx][1]
            me_to_vert.co[2] = me_to_vert_base[2] + morph[snap_idx][2]

        # insert shape key
        me_to.insertKey(1, 'relative')
        me_to.key.blocks[-1].name = from_key_block.name

    # reset mesh to base morph
    for me_to_vert, me_to_vert_base in zip(me_to.vertices, me_to.key.blocks[0].data):
        me_to_vert.co[0] = me_to_vert_base[0]
        me_to_vert.co[1] = me_to_vert_base[1]
        me_to_vert.co[2] = me_to_vert_base[2]

    # copy ipo if there is one
    if me_from.key.ipo:
        me_to.key.ipo = me_from.key.ipo

    me_to.update()

def worldspace_verts(me, ob):
    """Return vertices in world space."""
    mat = ob.matrixWorld
    return [(i, vert.co * mat) for i, vert in enumerate(me.vertices)]

def worldspace_verts_zsort(me, ob):
    """Return vertices in world space, sorted along the Z axis so we
    can optimize get_snap_idx.
    """
    verts_zsort = worldspace_verts(me, ob)
    verts_zsort.sort(key=lambda a: a[1].z)
    return verts_zsort

def subdiv_mesh(me, subdivs):
    """Subdivide the faces of the mesh.

    Note: this function is broken for the moment, because it kills morphs!
    """
    # XXX note: me.subdivide kills morphs!
    # XXX for this reason, the quality option is disabled below...
    # XXX todo: fix this in blender
    oldmode = Mesh.Mode()
    Mesh.Mode(Mesh.SelectModes['FACE'])
    me.sel = 1
    for i in range(subdivs):
        me.subdivide(0)
    Mesh.Mode(oldmode)

def main(arg):
    print('\nStarting morph copy...')

    # get selected meshes
    scn = Blender.Scene.GetCurrent()
    obs = [ob for ob in self.context.selected_objects if ob.type == 'MESH']
    if not obs:
        Blender.Draw.PupMenu('Error%t|2 or more mesh objects need to be selected.|aborting.')
        return
        
    PREF_QUALITY = Blender.Draw.Create(0)
    PREF_NO_XCROSS = Blender.Draw.Create(0)
    PREF_SEL_ONLY = Blender.Draw.Create(0)
    
    pup_block = [
        ('Quality:', PREF_QUALITY, 0, 4,
         'Generate interpolated verts for a higher quality result.'),
    ('No X Crossing', PREF_NO_XCROSS,
         'Do not snap across the zero X axis'),
        '',
        '"Update Selected" copies',
        'active object weights to',
        'selected verts on the other',
        'selected mesh objects.',
        ('Update Selected', PREF_SEL_ONLY,
         'Only copy new morphs to selected verts on the target mesh. '
         '(use active object as source)'),
    ]
    
    
    if not Blender.Draw.PupBlock("Copy morphs for %i meshes" % len(obs), pup_block):
        return
    
    PREF_SEL_ONLY = PREF_SEL_ONLY.val
    PREF_NO_XCROSS = PREF_NO_XCROSS.val
    PREF_QUALITY =  PREF_QUALITY.val

    # XXX quality ignored for now due to bug in subdivide
    if PREF_QUALITY:
        print('\tQuality not yet implemented due to subdivide bug in Blender.')
        print('\tFalling back on quality level 0.')
        PREF_QUALITY = 0
    
    act_ob = scn.objects.active
    if PREF_SEL_ONLY and (act_ob is None):
        Blender.Draw.PupMenu('Error%t|When dealing with 2 or more meshes with morphs|There must be an active object|to be used as a source|aborting.')
        return

    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Window.EditMode()
    Window.EditMode(0)    
    Window.WaitCursor(1)
    t = sys.time()
    
    sel = []
    from_data = None
    
    for ob in obs:
        me = ob.getData(mesh=1)
        morph_key = me.key
        
        # If this is the only mesh with a morph key OR if its one of
        # many, but its active.
        if (morph_key and
            ((ob is act_ob and PREF_SEL_ONLY) or (not PREF_SEL_ONLY))):
            if from_data:
                Blender.Draw.PupMenu(
                    'More then 1 mesh has morphs, only select 1 mesh with '
                    'morphs. Aborting.')
                return
            else:
                # This uses worldspace_verts_idx which gets (idx,co)
                # pairs, then zsorts.
                if PREF_QUALITY:
                    for _ob in obs:
                        _ob.sel = 0
                    ob.sel = 1
                    Object.Duplicate(mesh=1)
                    ob = scn.objects.active
                    me = ob.getData(mesh=1)
                    # morphs will be the same
                    print(('\tGenerating higher %ix quality weights.'
                          % PREF_QUALITY))
                    subdivMesh(me, PREF_QUALITY)
                    scn.unlink(ob)
                from_data= (ob, me, worldspace_verts_zsort(me, ob), morph_key)
                
        else:
            data = (ob, me, worldspace_verts(me, ob), morph_key)
            sel.append(data)
    
    if not from_data:
        Blender.Draw.PupMenu('Error%t|No mesh with morphs found.')
        return
    
    if not sel:
        Blender.Draw.PupMenu('Error%t|Select 2 or more mesh objects, aborting.')
        # We can't unlink the mesh, but at least remove its data.
        if PREF_QUALITY:
            from_data[1].vertices = None
        return
    
    # Now do the copy.
    print(('\tCopying from "%s" to %i other mesh(es).'
          % (from_data[0].name, len(sel))))
    for data in sel:
        copy_morphs(from_data, data, PREF_SEL_ONLY, PREF_NO_XCROSS)
    
    # We can't unlink the mesh, but at least remove its data.
    if PREF_QUALITY:
        from_data[1].vertices= None
    
    print(('Morph copy finished in %.2f seconds' % (sys.time()-t)))
    Window.DrawProgressBar(1.0, '')
    Window.WaitCursor(0)
    if is_editmode:
        Window.EditMode(1)
    
if __name__ == '__main__':
    main(__script__['arg'])
