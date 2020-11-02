User Interface
==============
.. _user-ui:

The Blender Niftools Addon both integrates and expands Blender's UI.
This section of the document outlines which sections of the default options are used.
It also describes any custom UI that is added by the plugin.

Import and Export Operators
---------------------------
.. _user-ui-operators:

When the Blender Niftools Addon is enabled via the addon system it adds new options in the main File menu.
The nif importer and exporter will be accessible via the corresponding **File > Import** and **File > Export** menus.
Selecting **NetImmerse/Gamebryo(.nif)** option will open the Main UI window.

For a detailed breakdown of all the settings see :ref:`io-settings <user-features-iosettings>`

UI Logging
----------
.. _user-ui-logging:

The Blender Niftools Addon outputs the progress of Import/Export execution via the Information View.
There are 3 levels of logging information
- Information: This is general progress information
- Warning: There was an issue that did not cause the execution to fail, but probably something the user needs to resolve. The full set of warnings will appear at the end in a pop-up window.
- Error: There was an issue encountered that caused the execution to fail.