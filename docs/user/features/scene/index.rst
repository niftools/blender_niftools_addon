Scene
-----

The follow section outlines Scene level settings that are required for import/export

Nif Version
===========

**Nif Version**
   The base version, generally related to a single game or company. Displayed in format *xx.xx.xx.xx*
   
   *Example:*
      Nif Version 20.02.00.07 is the version that is used for Fallout 3.

**User Version**
   A two digit single integer sub value of Nif Version.
   
   *Example:*
      11 would designate Fallout 3 as the specific game file.
   
**User Version 2**
   A second two digit single integer sub value, with the same function as User Version.
   
   *Example:*
      34 would designate Fallout 3 as the specific game file.


.. note::

   * All three values are used to verify which data should be attached to a file during the export process.
   * The scene version is checked at export and compared with the intended export format's version.
   * Mismatches will trigger and error and alert the user so that corrections can be effected.
   * Check the nif files included with the game you're modding to know which versions to use.