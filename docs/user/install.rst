Installation
============

.. _user-getblender:

Install Blender
---------------

Fedora
^^^^^^

Blender 2.8.x is available via yum or dnf (depending on your Fedora
release)

.. code-block:: shell

   sudo [yum|dnf] install blender -y

Debian and its Derivatives (Ubuntu, etc.)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Blender is available from apt

.. code-block:: shell

   sudo apt-get install blender

Windows and MacOS
^^^^^^^^^^^^^^^^^

Builds for Windows and MacOS (and non-Fedora Linux distributions) can be
found at `<https://blender.org/downloads>`_. **Be sure to get 2.83 LTS or
newer**, NifTools is not compatible with older versions of Blender.

Unsure if your operating system is 32-bit (i386) or 64-bit (x86_64)? Choose
the 32-bit version of Blender to be safe.

Install and Register the Addon
------------------------------

#. Download the latest `Blender Niftools Addon .zip release
   <https://github.com/niftools/blender_niftools_addon/releases>`_.

#. Start Blender.

#. In the menu bar, go to **Edit** > **Preferences** > **Add-Ons**.

#. Click **Install Addon...** (top-right in the Add-Ons diaglog).

#. Select the Blender Niftools Addon .zip file downloaded earlier. Click
   **Install Add-On**.

#. If **Import-Export: NetImmerse/Gambryo nif format** doesn't automatically
   appear in the search bar of the Preferences window, type "nif", and press
   enter.

#. Tick the empty box next to **Import-Export: NetImmerse/Gambryo nif
   format**. (You may have to scroll down to find it.)

   If you want to enable Niftools each time you start Blender, click the
   hamburger stack overflow menu (bottom-left) and select **Save
   Preferences**.

#. Close the **Blender Preferences** window.

#. The NifTools importer and exporters should now be available under **File**
   > **Import** and **File** > **Export**. If you saved your user preferences,
   the importers and exports should be available on every launch of Blender!

.. image:: _static/images/NifTools_Install.gif
    :target: _static/images/NifTools_Install.gif
    :width: 800px
    :height: 600px
    :align: center
    :alt: This is a graphic representation of the "Install and Register the
      Addon" steps above.