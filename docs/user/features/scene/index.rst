Scene
-----

The follow section outlines Scene level settings that are required for import/export

Nif Version
===========

**Nif Version**
   The base version, generally related to a single game or company.
   * This is currently not very user friendly, this will be addressed in a future release
   * Check the nif files included with the game you're modding to know which versions to use.
   
   *Example:*
      Nif Version 335544325 is the version that is used for Oblivion.

**User Version**
   A two digit single integer sub value of Nif Version.
   
   *Example:*
      11 would designate Fallout 3 as the specific game file.
   
**User Version 2**
   A second two digit single integer sub value, with the same function as User Version.
   
   *Example:*
      34 would designate Fallout 3 as the specific game file.


.. note::

   
   * Fill in the **Nif Version**, **User Version** and **User Version 2** adequate for your game.
   * All three values are used to verify which data should be attached to a file during the export process.
   * The scene version is checked at export and compared with the intended export format's version.
   * Mismatches will trigger and error and alert the user so that corrections can be effected.
   
   
   

   