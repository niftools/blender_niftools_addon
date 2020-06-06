Import and Export Settings
==========================
.. _user-features-iosettings:

This section explains the import and export settings.

***************
Common Settings
***************
.. _user-features-iosettings-common:

There are some common settings shared between the import and export operators.

.. warning::
   Only a subset of these settings is currently supported even though they have been documented.
   This is due to the fact that they are ported directly from the old addon and as such, will functionally remain the
   same.

UI Logging
----------
.. _user-ui-logging:

The Blender Niftools Addon outputs the progress of Import/Export execution via the Information View.

There are two Loggers with options; one for the Blender Niftools Addon,
a second for pyffi the library used to read & write the various file formats.

Log Level
---------
.. _user-features-iosettings-loglevel:
The level at which a log entry is generated to the console window.
This is used mainly used for debugging and error checking.

There are 3 levels of logging information
* Information: This is for general progress information
* Warning: An issue that did not cause the execution to fail, but probably something the user needs to resolve, eg missing texture.
  The full set of warnings will appear at the end in a pop-up window.
* Error: Logs an issue that caused the execution of the import/export to fail.

As a user you will only need to alter this setting if you experience an issue during the import it and a developer asks for more detailed logs that are produced with the default logging level.

.. toctree::
   :maxdepth: 2
   
   import
   export