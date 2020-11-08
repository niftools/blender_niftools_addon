Textures
========
.. _textures:

A texture refers to a generic image.
A map refer to an image which has specific properties which will influence
the renderer.
Textures/Maps allow us to alter how the geometry is rendered, such as adding
additional detail, affecting light, etc.

Notes
~~~~~

* The nif format only supports UV mapped textures, so only those will be
  exported.
* GLSL mode is enabled on import/export but should be enabled manually
  otherwise to give correct viewport preview.
* Relative paths for textures are often used, eg. /Texture/../.. which should
  be adjusted so Blender can render in the viewport.

Requirements
~~~~~~~~~~~~

Adding textures requires the following:

#. :ref:`A Mesh-object <geometry-mesh>`.
#. The Mesh-object needs to be :ref:`uv-unwrapped <geometry-uv>`.
#. That Mesh-object requires :ref:`a Material <properties-material>`.


Creating a Texture Slot
-----------------------

Create a Texture slot to hold a texture.

* In the **Texture tab**, Click **New** to create **Texture Slot**.

A texture slot has a default texture, we set type of image we will use:

* Under **Type**, select **Image or Movie**or **Enviromental**, see
  :ref:`texture maps<texture_maps>`

We load an image to use as our texture.

* Next to **Image**, click **Open**, and select the desired texture image.

Set the texture to use the UV coordinates.

* Under **Mapping** > **Coordinates**, select **UV**.

The UV layer that was :ref:`created previously<geometry-uv>` needs to be
selected for this texture.

* In the **Texture** tab, under **Mapping** > **Layer**, click on the empty
* field, and select ``UVTex``.

Texture Maps
~~~~~~~~~~~~

Each Texture Map affects different properties of how the geometry is rendered

.. toctree::
   :maxdepth: 2
   
   texture_maps
   