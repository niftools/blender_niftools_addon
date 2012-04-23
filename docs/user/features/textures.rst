Textures
--------

.. _textures:

Example
~~~~~~~

#. :ref:`Create a mesh-object <geometry-mesh>`.
#. :ref:`Add a material <properties-material>`.
#. In the *Properties* panel, in the *Texture* tab,
   click **New** to create a new material texture slot.
#. Under **Type**, select **Image or Movie**.
#. Next to **Image**, click **Open**, and select the desired texture image.
#. Under **Mapping > Coordinates**, select **UV**.
#. Under **Influence > Diffuse**, make sure **Color** is selected, and nothing else.
#. Go back to the 3D view, and switch to edit mode (press ``TAB``).
#. Press ``U``, select **Unwrap > Smart UV Project**.
#. Switch back to object mode (press ``TAB`` again).
#. Again in the *Texture* tab, under **Mapping > Layer**, click on the empty field, and select ``UVTex``.
#. Now export as usual.

Notes
~~~~~

The nif format only supports UV mapped textures,
so only those will be exported.

Currently, only the base texture is exported.

.. todo::

   Describe required settings for each texture slot.

