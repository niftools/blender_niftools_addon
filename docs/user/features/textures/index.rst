Textures
--------

.. _textures:

* A texture refers to a generic image.
* A maps refer to image which has specific properties which will influence the renderer. 
* Textures/Maps allow us to alter how the geometry is rendered, such as adding additional detail, affecting light, etc.

Notes
~~~~~

* The nif format only supports UV mapped textures, so only those will be exported.
* GLSL mode is enabled on import/export, but should be enabled manually otherwise to give correct viewport preview.
* Relative paths for textures are often used, eg. \Texture\..\.. which should be adjusted so Blender can render in the viewport.

Requirements
~~~~~~~~~~~~
* In order to add textures we need the following:

#. :ref:`A Mesh-object <geometry-mesh>`.
#. The Mesh-object needs to be :ref:`uv-unwrapped <geometry-uv>`.
#. That Mesh-object requires :ref:`a Material <properties-material>`.


Creating a Texture Slot
~~~~~~~~~~~~~~~~~~~~~~~

A Texture slot is used to hold a texture.
* In the **Texture tab**, Click **New** to create **Texture Slot**.

Creating a texture slot will create a texture in that slot by default. 

We set the texture to use the UV coordinates.
* Under **Mapping > Coordinates**, select **UV**.

The UV layer that was :ref:`create previously<geometry-uv>` needs to be selected for this texture.
* In the **Texture** tab, under **Mapping > Layer**, click on the empty field, and select ``UVTex``.

Each Texture should be of type **Image or Movie** or **Enviromental**
* Under **Type**, select **Image or Movie**or **Enviromental**

We load an image to use as our texture
* Next to **Image**, click **Open**, and select the desired texture image.

Texture Maps
~~~~~~~~~~~~

* Each Texture Map affects different properties of how the geometry is rendered

.. toctree::
   :maxdepth: 1
   
   texture_maps
   

 

