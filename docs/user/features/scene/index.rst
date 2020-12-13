Scene
-----
.. _user-features-scene:

The following section outlines Scene settings which is mainly related to Nif
Header information.

Changing the setting also alters what is displayed by the UI.


The setting can be viewed in the Niftools Scene Panel. This is visible in the
Scene Tab of the Properties Editor View.

Nif Version
===========
+----------------+---------------------------------------------------------------------------------------------------+
|    Property    |                                            Description                                            |
+================+===================================================================================================+
| Game           | Select the game you're working on. This will be set to a suitable game on import, but can't       |
|                | always be resolved. A single version number may map to multiple games.                            |
+----------------+---------------------------------------------------------------------------------------------------+
| Nif Version    | The base version, typically related to a single game or company. Check out the Nif files included |
|                | with the game  you're modding for the correct version.                                            |
|                |                                                                                                   |
|                | *Example*:                                                                                        |
|                | Nif Version ``335544325`` is used for Oblivion                                                    |
+----------------+---------------------------------------------------------------------------------------------------+
| User Version   | 2-digit integer value for the Nif file.                                                           |
|                |                                                                                                   |
|                | *Example*:                                                                                        |
|                | ``11`` designates *Fallout 3* as the specific game                                                |
+----------------+---------------------------------------------------------------------------------------------------+
| User Version 2 | Another 2-digit integer value for the Nif file.                                                   |
|                |                                                                                                   |
|                | *Example*:                                                                                        |
|                | ``34`` desginates *Fallout 3* as the specific game                                                |
+----------------+---------------------------------------------------------------------------------------------------+

.. note::

   * Select the **Game** from the dropdown - **Nif Version**, **User Version** and **User Version 2** are updated
     accordingly.
   * All three values are used to verify which data should be attached to a file during the export process.
   * The scene version is checked at export and compared with the intended export format's version.
   * Mismatches will trigger an error and alert the user so that corrections can made.

Scale correction
================
.. _user-features-scene-scale-correction:

This value is used to globally re-scale the input Nif data to map correctly to Blender's unit of the measurement system.
The default setting ensures the imported model fits into the view Blender viewport
When importing large-scale nif models, such as structures, a user can edit this value so that the nif is easier to work with.

* The Unit of measurement in Blender is the Blender Unit (BU). The default value is 1 BU = 1 meter but can be remapped to any measurement system.
* The ratio of a Nif Units (NU) to Blender Units (BU) is 1Nu:10Bu, so we need reduce the nif by a factor of 10.

.. _user-features-scene-scale-correction-import:
* The Blender Nif Plugin applies a default correction of 0.1

.. _user-features-scene-scale-correction-export:
* The Blender Nif Plugin applies a default correction of 10
