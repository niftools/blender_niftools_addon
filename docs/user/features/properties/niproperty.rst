
.. _properties-niproperty:

NiProperty
==========

The following is an overview of what the addon will export Blender settings are mapped to.


.. _properties-nimaterial:

NiMaterialProperty
------------------

The following section is for nifs which use :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.
* Every :class:`~bpy.types.Material` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.


.. _properties-nispecular:

NiSpecularProperty
------------------

* Setting the **Intensity** to **0** will disable specularity; a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.

.. _properties-nialpha:

NiAlphaProperty
---------------

* An :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty` is exported for Materials or Texture have Alpha value.
   
   
.. _properties-niwireframe:

NiWireFrameProperty
-------------------

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`

.. _properties-stencil:

NiStencilProperty
-----------------

The NiStencilProperty ignores the face normal and renders both sides of the mesh.

#. In the **Object Tab -> Double-Sided**, enable/disable.

* This will export a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`



.. 
   todo::
   
   Document these bad boys once implemented
   
   NiVertexColorProperty 
