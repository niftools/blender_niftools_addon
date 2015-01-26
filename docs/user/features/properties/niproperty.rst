NiProperty
==========
.. _properties-niproperty:

The following is a overview of what the Nif Plugin will export Blender settings are mapped to.


NiMaterialProperty
------------------
.. _properties-nimaterial:

The following section is for nifs which use :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.
* Every :class:`~bpy.types.Material` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.


NiSpecularProperty
------------------

.. _properties-nispecular:


* Setting the **Intensity** to **0** will disable specularity; a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.

NiAlphaProperty
---------------

.. _properties-nialpha:

* An :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty` is exported for Materials or Texture have Alpha value.
   
   
NiWireFrameProperty
-------------------
.. _properties-niwireframe:

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`

NiStencilProperty
-----------------
.. _properties-stencil:

The NiStencilProperty ignores the face normal and renders both sides of the mesh.

#. In the **Object Tab -> Double-Sided**, enable/disable.

* This will export a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`



.. todo::
   
   Document these bad boys once implemented
   
   NiVertexColorProperty 
