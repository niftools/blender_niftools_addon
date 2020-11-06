-----
Scene
-----
.. _user-features-scene:

The following section outlines Scene settings which is mainly related to Nif Header information.
Changing the setting also alters what is displayed by the UI.


The setting can be viewed in the Niftools Scene Panel. This is visible in the Scene Tab of the Properties Editor View.

===========
Nif Version
===========

**Game**
   Select the game you're working for. This will be set to a suitable game on import, but can not always be resolved as the version number can map to several games.

**Nif Version**
   The base version, generally related to a single game or company.
   * Check the nif files included with the game you're modding to know which versions to use.
   
   *Example:*
      Nif Version 335544325 is the version that is used for Oblivion.

**User Version**
   A two digit single integer sub value of Nif Version.
   
   *Example:*
      11 would designate Fallout 3 as the specific game file.
   
**User Version 2**
   A second two-digit single integer sub value, with the same function as User Version.
   
   *Example:*
      34 would designate Fallout 3 as the specific game file.


.. note::

   
   * Select the **Game** from the dropdown - **Nif Version**, **User Version** and **User Version 2** are updated accordingly.
   * All three values are used to verify which data should be attached to a file during the export process.
   * The scene version is checked at export and compared with the intended export format's version.
   * Mismatches will trigger an error and alert the user so that corrections can be affected.
   
   
   

   