Turn Word Wrap on to read this file.

nif_import_237.py version 1.0.6
Copyright (C) 2005 Alessandro Garosi, (AKA Brandano) -- tdo_brandano@hotmail.com
--------------------------------------------------------------------------
***** BEGIN GPL LICENSE BLOCK *****

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

***** END GPL LICENCE BLOCK *****
--------------------------------------------------------------------------
Credits:
Portions of this programs are derived (through the old tested method of cut'n paste) from the obj import script obj_import.py: OBJ Import v0.9 by Campbell Barton (AKA Ideasman).
Not really, I started the script like that, but I pretty much replaced every bit taken from it with my own code. Not that mine is any better, though!

Thanks go to:
Campbell Barton (AKA Ideasman) for making code clear enough to be used as a learning resource. Hey, this is my first ever python script!
Lars Rinde (AKA Taharez), for helping me a lot with the file format, and with some debugging even though he doesn't 'do Python'
Timothy Wakeham (AKA timmeh), for taking some of his time to help me get to terms with the way the UV maps work in Blender
--------------------------------------------------------------------------

Installation:
Copy this script in your Blender scripts folder when installing Blender under Windows this is by default Windows C:\Program Files\Blender Foundation\Blender\.blender\scripts.
Either reload Blender or in the folders setup menu select "Re-evaluate scripts registration in menus", and the option to "Import NetImmerse 4.0.0.2" will appear in the File-Import menu.
IMPORTANT:
The script needs a full python installation, as it uses regular expressions and the 'struct' class, can't do without them, I am sorry.
The version of Python installed must also be compatible with Blender, or the script just won't run. It's not my mistake, and you will see that several other scripts bundled with Blender won't run properly or at all unless you have a full compatible Python installation, the Nendo import script for example.
At the time of writing this the latest 'stable' version of Blender is Blender 2.36, and it was compiled with bindings for Python 2.3x. You won't need to uninstall Python 2.4 in order to get the script running, but you need to install python 2.35 as well (you can get it from http://www.python.org/2.3.5/).
Then, to get everything running properly you need to open the Blender configuration panel (just drag down the lower border of the toolbar at the top of the screen), select the "File Paths" button, click on the folder icon near to the Python path box, and browse to the 'lib' subfolder of your Python 2.35 installation (for example c:\Python23\lib).
This is by far the easiest way, a more complex (but more flexible) one would be to set a PYTHONPATH environment variable that points to the location of the blender 'lib' folder and also all other libraries that you want to use with it.
You can even write a batch script (or shell script, if you are using Linux) to set the PYTHONPATH right before running blender, so that it will be set for Blender only and leave the rest of the system alone, but I'd leave that to the techies.
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
Now bones are 'a' proper length (NIF bone syystems don't report a bone length), and are aligned properly, well, within 1 degree of their roll position

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