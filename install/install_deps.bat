:: Script to install developer dependancies for the Blender Nif plugin
python -m pip install Sphinx --target="%BLENDER_ADDONS_DIR"%\dependencies
python -m pip install nose --target="%BLENDER_ADDONS_DIR"%\dependencies
