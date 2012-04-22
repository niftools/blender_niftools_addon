Properties
==========

* Most Nif :class:`~pyffi.formats.nif.NifFormat.NiProperty` are mapped to some part of Blender's Material System.
* The following section goes through those Blender material settings and how they relate to those properties.
* Unless otherwise stated your mesh needs to have a material.

Example
~~~~~~~

#. :ref:`Create a single sided cube <features-example-geometry>` as explained before.
#. In the **Properties** panel, in the *Material* tab
   click **New** to create a new material.

Notes
~~~~~

Every :class:`~bpy.types.Material` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.

* The nif format only supports a single material per :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* A multimaterial mesh will be exported as multiple :class:`~pyffi.formats.nif.NifFormat.NiTriShape`, one for each material.



NiMaterialProperty
------------------

.. _properties-material:

Diffuse
+++++++

   
#. Under **Diffuse**, click on the color, and set it to completely white
   (**R**, **G**, and **B** should each say 1.000,
   whereas the default is 0.800).


Emissive
++++++++


   
NiSpecularProperty
------------------
   :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty`,

- Under **Specular**, set **Intensity** to whatever values, 
- Setting the **Intensity** will to disable specularity and a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.

#. Now you will want to :ref:`add a texture <features-example-texture>`.


NiAlphaProperty
---------------
   :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty`,
   
   
NiWireFrameProperty
-------------------

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`,

NiStencilProperty
-----------------

:class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`,
