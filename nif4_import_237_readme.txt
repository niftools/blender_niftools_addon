Turn Word Wrap on to read this file.

nif_import_237.py version 1.0.6
--------------------------------------------------------------------------
***** BEGIN LICENSE BLOCK *****

BSD License

Copyright (c) 2005, NIF File Format Library and Tools
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the NIF File Format Library and Tools projectmay not be
   used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

***** END LICENCE BLOCK *****
Note: Versions of this script previous to 1.0.6 were released under the GPL license
The script includes small portions of code obtained in the public domain, in particular
the binary conversion functions. Every attempt to contact (or actually identify!) the
original author has so far been fruitless.
I have no claim of ownership these functions and will remove and replace them with
a (probably less efficient) version if the original author ever will ask me to.
--------------------------------------------------------------------------

Credits:
Portions of this programs are (were) derived (through the old tested method of cut'n paste)
from the obj import script obj_import.py: OBJ Import v0.9 by Campbell Barton (AKA Ideasman)
(No more. I rewrote the lot. Nevertheless I wouldn't have been able to start this without Ideasman's
script to read from!)
Binary conversion functions are courtesy of SJH. Couldn't find the full name, and couldn't find any
license info, I got the code for these from http://projects.blender.org/pipermail/bf-python/2004-July/001676.html
The file reading strategy was 'inspired' by the NifToPoly script included with the 
DAOC mapper, which used to be available at http://www.randomly.org/projects/mapper/ and was written and 
is copyright 2002 of Oliver Jowett. His domain and e-mail address are however no longer reacheable.
No part of the original code is included here, as I pretty much rewrote everything, hence this is the 
only mention of the original copyright. An updated version of the script is included with the DAOC Mappergui
application, available at http://nathrach.republicofnewhome.org/mappergui.html

Thanks go to:
Campbell Barton (AKA Ideasman, Cambo) for making code clear enough to be used as a learning resource.
Hey, this is my first ever python script!
SJH for the binary conversion functions. Got the code off a forum somewhere, posted by Ideasman, I suppose it's allright to use it
Lars Rinde (AKA Taharez), for helping me a lot with the file format, and with some debugging even though he doesn't 'do Python'
Timothy Wakeham (AKA timmeh), for taking some of his time to help me get to terms with the way the UV maps work in Blender
Amorilia (don't know your name buddy), for bugfixes and testing.

Installation:
Copy this script in your Blender scripts folder when installing Blender under Windows this is by default Windows C:\Program Files\Blender Foundation\Blender\.blender\scripts.
Either reload Blender or in the folders setup menu select "Re-evaluate scripts registration in menus", and the option to "Import NetImmerse 4.0.0.2" will appear in the File-Import menu.
IMPORTANT:
The script needs a full python installation, as it uses regular expressions and the 'struct' class, can't do without them, I am sorry.
The version of Python installed must also be compatible with Blender, or the script just won't run. It's not my mistake, and you will see that several other scripts bundled with Blender won't run properly or at all unless you have a full compatible Python installation, the Nendo import script for example.
At the time of writing this the latest 'stable' version of Blender is Blender 2.36, and it was compiled with bindings for Python 2.3x. You won't need to uninstall Python 2.4 in order to get the script running, but you need to install python 2.35 as well (you can get it from http://www.python.org/2.3.5/).
Restart Blender and everything should work fine.
If you still have problems, check out this LOOOONG thread on the elysiun board: http://www.elysiun.com/forum/viewtopic.php?t=7723
The latest pages will be the ones you will find more useful, as the thread started several Blender versions back.

Use:
Launch the script, select the .NIF file you wish to import, and you are set.
Actually, no, that's not it if you also want to load the textures.
Blender does not support the loading of .DDS textures, so in order to load these you must provide an alternative file with the same filename, but with the extension .TGA, .PNG, .BMP or .JPG.
Also, selecting a base folder for the textures has proved to be an impossible task, so the script looks for them in the same folder as the .NIF file.
However, as part of the filepath info is also stored within the .NIF file itself, you should copy the whole subpath from the Morrowind "Data Files" folder.
This means that if your NIF file is, say, "C:\Morrowind\Data Files\Meshes\deadparrot.nif" and the texture is "C:\Morrowind\Data Files\Textures\parrot\dead.dds" you should convert the texture and move it to "C:\Morrowind\Data Files\Meshes\Textures\parrot\dead.tga".
This is also in order to keep the texture file path consistent for the time we'll be able to export the modified meshes from Blender.

Limitations:
At the moment the script only loads the pure geometry data, some material info, and the first texture found on every mesh.
This should normally match the base texture, but the file format allows for 'unordered' textures, so some models might import badly.
Also, the script doesn't import animation, particle effects, multiple UV channels.... the list is too long. Working on it.
That little 'a' after the version number means: do not expect any support whatsoever. I might give you some, but for all purposes, try and act as if I didn't exist.
The script loads the armature and vertex groups-weights of the skinned meshes properly, but carences in Blender 2.37 armature python API do not allow me to apply this skinnining info to the mesh from the script.
On top of that, bugs in the armature python API make it impossible to save the armature as it is loaded in a .blend file.
These matters are being looked into by the Blender developers, and a new armature system and API should be included with the next Blender release.


changelog (starting from 1.5a):

1.5a:
fixed a bug where texture files with trailing null characters would crash the importer

1.6a:
changed the material handling, now doesn't generate duplicate materials
changed the mesh creation method. Now it builds hierarchical relations generating empties as correspondences to NiNodes

1.7a:
got rid of a couple of matrix operations, now I apply the transforms to the mesh container rather than to the vertices, so there is no data loss.
The root node is scaled down to 1/10th of the original size and rotated -90# along the Z axis, but this is the only change introduced by the importer.
Now not only all the hierarchies are stored, but the empties that act as grouping widgets are moved to the correct relative coordinates, so we might start to think about animations.

1.8a:
I did some little optimization, fixed a few things.
Now the root node is no longer rotated along the Z axis, as I realized that I completely forgot that I should apply his transform matrix to the root node as well.
It is only scaled down to 10% of the original size, and as all his children inherit this transformation the meshes are much easier to handle.
I have also added a much better support for textures and materials, that are now only parsed once and reused if identical (obtained from the same node).
I couldn't notice any speed improvement, because on my machine the import is pretty much istantaneous anyway, but I believe that this wastes less memory.

1.9a:
Not published, it didn't really introduce much change to what was already there.

2.0a:
Big things afoot, now I got bones! The script now will load single or multiple armatures, and build each armature's bone tree in the rest position. The bone head position is correct, the tail is approximated and the rotation is botched. The trouble is that Blender's bone API is a little bit messy. Let's say very messy.
The NIF bones store their orientation and origin as a matrix relative to the parent node, while in Blender all coordinates are relative to the armature node.And on top of that while I have a getRestMatrix method I don't have an equivalent setRestMatrix one. 
I am still working on this, but I already have a couple of ideas on what I can to to get these damn thing working properly.
I still don't have the skinning info, so moving the bones about won't change the pose of the model. But if you want to help me out have a look at the NiSkinInstance and NiSkinData nodes, NiSkinData in particular. NiSkinInstance holds a list of bones that influence the mesh, the class is already defined in the script, even though it isn't used
In the smaller updates, if the script can't find a full Python installation it will print a customized error showing the Python version Blender was compiled with. This is not necessarily the Python version you need, but is sure to work. At this time the correct version is Python 2.3.5

1.0.1
I took the occasion of a new Blender version out and changed my versioning convention. Sorry about the confusion
Fixed a bug that would hang the script on Blender 2.37
Now bones are 'a' proper length (NIF bone systems don't report a bone length), and are aligned properly, well, within 1 degree of their roll position

1.0.2
A few (quite a few actually) bugfixes by Amorilia (whoopee, another python coder onboard!).
Now the script won't crash with larger NIFs. And read the right number of blocks. And won't overwrite existing meshes etc.. 

1.0.3
Added a new way to roll bones to their proper position, might save a few cycles, tho sometimes it still needs to approximate the result
Changed the way the nif format is detected. The script now also detects the file version and can test against a list of different file versions.
It also allows for longer headers, like in the case of "Zoo Thycoon 2" NIF files.
Zoo Thycoon 2 files are way too different from Morrowind's files to be imported, though.

1.0.4
Removed a bunch of debug messages to speed up things a little.
Added vertex groups to the imported info, but the skinning doesn't work yet. To work properly both the meshes and the armature should share the same coordinates system apparently, and the nested transformations that are applied to both are making it very difficult to come up with a working system. I really ran out of ideas, I am afraid.
Meshes now are imported as an "object" wrapped by a NiNode, and therefore the outliner tree is a little simpler. This also loses a little transform info, but nothing you will notice on the screen anyway as the transform matrix of the NiNode and NiTriShape are combined while importing.

1.0.5
Fixed a few typos and a couple of mistakes that Amorilia pointed out. Still incomplete, by far, but seems to be approaching the "usable" state.

1.0.6
Added Amorilia's corrections to the import of UV seams. Changed the name of the file to reflect the fact that the importer is version specific.
As of this version the licensing is under a BSD license, to avoid confusion when distributing together with Amorilia's export script. However, copyright on the two script is still with the respective authors.
Also, all previous versions of this script are still to be considered as governed by the GPL license.
I also removed a small portion of the readme regarding python setup, as it was confusing, redundant and most likely just wrong. For the moment I'll rely on the Blender's user forums, until I can come up with a decent tutorial on setting up python properly.