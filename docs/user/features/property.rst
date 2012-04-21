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

   Document these bad boys:
   :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`,
   :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`,
   any others?