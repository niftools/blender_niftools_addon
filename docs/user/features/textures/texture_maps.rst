Texture Maps
------------

.. _texture_maps:

| Each Texture Map has a distinct function, which affectes how the object is rendered

| The following sections describe the function of each Map
| Map properies are usually set via the **Influence** section of the **Texture Tab**.

Diffuse Map
-----------

The information in a diffuse map is used as the base color

#. Under **Type**, set the type to **Image or Movie**.

#. Under **Influence**,  in the **Diffuse Section**, enable **Color**.

Bump Map
--------

| The information in a Bump map is used as affect the lighting of the object to give apparent detail.
| This map is usually a grey-scale texture.

#. Under **Type**, set the type to **Image or Movie**.
#. Under **Influence**,  in the **Geometry Section**, enable **Normal**.

Glow Map
--------

A texture that receives no lighting, but the pixels are shown at full intensity.

#. Under **Type**, set the type to **Image or Movie**.
#. Under **Influence**,  in the **Shading Section**, enable **Emit**.

Normal Map
----------

| A Normal Map is usually used to fake high-res geometry detail when it's mapped onto a low-res mesh. 
| The pixels of the normal map each store a normal, a vector that describes the surface slope of the original high-res mesh at that point. 
| The red, green, and blue channels of the normal map are used to control the direction of each pixel's normal.

.. warning::
   Currently not supported.

#. Under **Type**, set the type to **Image or Movie**.
#. Under **Influence**,  in the **Geometry Section**, enable **Normal**.
#. Under **Image Sampling**, enable **Normal** 