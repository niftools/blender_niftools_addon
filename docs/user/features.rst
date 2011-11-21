Features
========

.. todo::

   It would be a good habit to document every feature we have,
   and quick instructions for how to use them.

Geometry
--------

Each :class:`~bpy.types.Mesh` is exported to
one or more :class:`~pyffi.formats.nif.NifFormat.NiTriShape`\ s.

The nif format only supports triangle based geometry,
so beware that blender quads are exported as triangles,
which may lead to small differences in how the geometry is rendered.

.. note::

   Strips (:class:`~pyffi.formats.nif.NifFormat.NiTriStrips`\ s)
   are not supported due to the fact that they are
   `unnecessary for current hardware
   <http://tomsdxfaq.blogspot.com/2005_12_01_archive.html>`_.

Materials
---------

Every :class:`~bpy.types.Material` is exported to a
:class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.

The nif format only supports a single material per
:class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
whence for this purpose, a multimaterial mesh will
be exported as multiple
:class:`~pyffi.formats.nif.NifFormat.NiTriShape`\ s,
one for each material.

.. todo::

   Document these guys:
   :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`,
   any others?

Textures
--------

The nif format only supports UV mapped textures,
so only those will be exported.

Currently, only the base texture is exported.

.. todo::

   Describe required settings for each texture slot.

Collision
---------

.. warning::

   Collisions have not actually been ported yet. This is just a stub
   documenting how things might be implemented.

To indicate that a mesh is to be exported as a collision object,
rather than say a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
select the blender **Game Engine** renderer, select the object's physics
tab, enable the **Collision Bounds** option, and select the desired
**Bounds**. For Oblivion, Fallout 3, and Fallout NV, blender's
collision types map to the following nif types:

============= ======================
blender       nif
============= ======================
Box           bhkBoxShape
Sphere        bhkSphereShape
Cylinder      bhkCapsuleShape
Capsule       bhkCapsuleShape
Convex Hull   bhkConvexVerticesShape
Triangle Mesh bhkMoppBvTreeShape
============= ======================

For Morrowind, we have:

============= =================
blender       nif
============= =================
Triangle Mesh RootCollisionNode
============= =================

.. todo::

   Where do we store material, layer, quality type, motion system, etc.?

Bounding Box
------------

.. todo::

   Write.
