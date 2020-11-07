Installation
============

.. _user-getblender:

Install Blender
---------------

Fedora
^^^^^^

Blender 2.8.x is available via yum or dnf (depending on your Fedora
release)
::bash
sudo yum install blender -y  (or)
sudo dnf install bledner -y

Debian and its Derivatives (Ubuntu, etc.)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Blender is available from apt
::bash
sudo apt-get install blender

Windows and MacOS
^^^^^^^^^^^^^^^^^

Builds for Windows and MacOS (and non-Fedora Linux distributions) at
`https://blender.org/downloads`. Be sure to get 2.83 LTS or newer. NifTools
is not compatible with older versions.

Install and Register the Addon
------------------------------

.. TODO: Gif!

#. Download the `Blender Niftools Addon .zip release
   <https://github.com/niftools/blender_niftools_addon/releases>`_.

#. Start Blender.

#. Go to: **Edit** > **Preferences** > **Add-Ons**.

#. Click **Install Addon...** (top-right).

#. Select the Blender Niftools Addon .zip file downloaded earlier. Click
   **Install Add-On**

#. In the search bar of the Preferences window, type "nif"

#. Tick the empty box next to **Import-Export: NetImmerse/Gambryo nif
   format**. You may have to scroll down a bit first.

   If you want to enable Niftools each time you start Blender, click the
   hamburger stack overflow menut (bottom-left) and select **Save
   Preferences**.

#. Close the **Blender Preferences** window.

#. The NifTools importer and exporters should now be available under **File**
   > **Import** and **File** > **Export**.
