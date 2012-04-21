Features
========

.. todo::

   It would be a good habit to document every feature we have,
   and quick instructions for how to use them.
   
   Split this up into seperate files mimicing test framework structure.

Geometry
--------

.. _features-example-geometry:

Example
~~~~~~~

#. Start blender with an empty scene.
#. Add a cube primitive: **Add > Mesh > Cube**.
#. Select whether the mesh should be Double-sided:
   in the *Properties* panel, in the *Object Data* tab,
   untick **Double Sided**.
#. Export the file: **File > Export > NetImmerse/Gamebryo**.

Notes
~~~~~

* Each :class:`~bpy.types.Mesh` is exported to one or more :class:`~pyffi.formats.nif.NifFormat.NiTriShape`\ s.

* The nif format only supports triangle based geometry.
* Blender quads are exported as triangles, which may lead to differences in geometry rendered.

* Strips (:class:`~pyffi.formats.nif.NifFormat.NiTriStrips`\ s) not supported due to the fact that they are
`unnecessary for current hardware <http://tomsdxfaq.blogspot.com/2005_12_01_archive.html>`_.

Materials
---------

.. _features-example-material:

Example
~~~~~~~

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.
#. In the *Properties* panel, in the *Material* tab,
   click **New** to create a new material.
#. Under **Diffuse**, click on the color, and set it to completely white
   (**R**, **G**, and **B** should each say 1.000,
   whereas the default is 0.800).
#. Under **Specular**, set **Intensity** to 0.000, to disable specularity
   (this will prevent a NiSpecularProperty being exported,
   which is usually what you want).
#. Now you will want to :ref:`add a texture <features-example-texture>`.

Notes
~~~~~

Every :class:`~bpy.types.Material` is exported to a
:class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.

The nif format only supports a single material per
:class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
hence for this purpose, a multimaterial mesh will
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

.. _features-example-texture:

Example
~~~~~~~

#. :ref:`Create a single sided cube <features-example-geometry>`.
#. :ref:`Add a material <features-example-material>`.
#. In the *Properties* panel, in the *Texture* tab,
   click **New** to create a new material texture slot.
#. Under **Type**, select **Image or Movie**.
#. Next to **Image**, click **Open**,
   and select the desired texture image.
#. Under **Mapping > Coordinates**, select **UV**.
#. Under **Influence > Diffuse**,
   make sure **Color** is selected,
   and nothing else.
#. Go back to the 3D view, and switch to edit mode
   (press ``TAB``).
#. Press ``U``, select **Unwrap > Smart UV Project**.
#. Switch back to object mode
   (press ``TAB`` again).
#. Again in the *Texture* tab,
   under **Mapping > Layer**,
   click on the empty field,
   and select ``UVTex``.
#. Now export as usual.

Notes
~~~~~

The nif format only supports UV mapped textures,
so only those will be exported.

Currently, only the base texture is exported.

.. todo::

   Describe required settings for each texture slot.

Vertex Color
------------

.. _features-example-vertexcolor:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.
#. Switch to Vertex Paint mode, 
   this automatically adds a base vertex color layer.
#. Apply the desired vertex colors evenly to the vertex.
#. Ensure you have added a material.
#. Now export as usual.

Notes
~~~~~

* The nif format only supports a single color per vertex, whereas Blender vertex color per face vertex.
* Blender treats the vertex as if the faces had been split apart. 
* Eg. A vertex in a cube is shared by four faces. Even though they share that vertex, each of those face can have a different color for that vertex.
* On export the scripts will take an average of colors. 

.. warning::
   alpha values currently are not written.

.. todo::
   Write up workflow for alpha layer once implemented.

Collision
---------

.. warning::

   Collisions are in the process of being ported. This section is incomplete and will change.

Example
~~~~~~~

.. _features-example-collisions:

#. To indicate the physics properties for an object, switch to the **Blender Game** tab. (Default tab is **Blender Render**)
#. With the collision object selected, switch to the **Physics** tab
#. Click **Collision Bounds** and select **Box** as **Bounds**
#. If you would like to define your own settings for havok physics, click **Use Blender Properties**.    
#. Define the fields **Havok Material**, **Motion System**, **Oblivion Layer**, **Quality Type** and **Col Filter** accordingly.
#. If you want the exporter to define the havok physics properties for you, make sure **Use Blender Properties** is not clicked.
#. Now you can continue editing the mesh until you are ready to export. 

.. todo::
   Should "Use Blender Properties" usage be reversed?
   i.e "Use Blender Property" uses default values, else define your own. Also should that there are defined by user else user default.

Notes
~~~~~

To indicate that a mesh is to be exported as a collision object,
rather than say a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
select the blender **Game Engine** renderer, select the object's physics
tab, enable the **Collision Bounds** option, and select the desired
**Bounds**. For Oblivion, Fallout 3, and Fallout NV, blender's
collision types map to the following nif types:

+--------------------------------------------+------------------------+
| Blender                                    | Nif                    |
+============================================+========================+
| :ref:`Box <features-example-box-collison>` | bhkBoxShape            |
+--------------------------------------------+------------------------+
| Sphere                                     | bhkSphereShape         |
+--------------------------------------------+------------------------+
| Cylinder                                   | bhkCapsuleShape        |
+--------------------------------------------+------------------------+
| Capsule                                    | bhkCapsuleShape        |
+--------------------------------------------+------------------------+
| Convex Hull                                | bhkConvexVerticesShape |
+--------------------------------------------+------------------------+
| Triangle Mesh                              | bhkMoppByTreeShape     |
+--------------------------------------------+------------------------+

For Morrowind, we have:

============= =================
blender       nif
============= =================
Triangle Mesh RootCollisionNode
============= =================

.. todo::

   Where do we store material, layer, quality type, motion system, etc.?
   
Box Collision
~~~~~~~~~~~~~
.. _features-example-box-collison:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Box Collision Notes
+++++++++++++++++++

Test

Sphere Collisions
~~~~~~~~~~~~~~~~~

.. _features-examples-sphere-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Sphere Collision Notes
++++++++++++++++++++++

Cylinder Collisions
~~~~~~~~~~~~~~~~~~~

.. _features-examples-cylinder-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Cylinder Collision Notes
++++++++++++++++++++++++

Capsule Collisions
~~~~~~~~~~~~~~~~~~

.. _features-examples-capsule-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Capsule Collision Notes
+++++++++++++++++++++++

Convex Hull Collisions
~~~~~~~~~~~~~~~~~~~~~~

.. _features-examples-convex-hull-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Convex Hull Collision Notes
+++++++++++++++++++++++++++

Triangle Mesh Collisions
~~~~~~~~~~~~~~~~~~~~~~~~

.. _features-examples-triangle-mesh-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <features-example-collisions>`.

Triangle Mesh Collision Notes
+++++++++++++++++++++++++++++

Bounding Box
------------

.. todo::

   Write.
