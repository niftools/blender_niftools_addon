:: Script to install developer dependencies for the Blender Nif plugin

:: TODO Add default localion in case variable is not set
:: Eg. SCRIPT_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"

python -m pip install Sphinx --target="%BLENDER_ADDONS_DIR"%\dependencies
python -m pip install nose --target="%BLENDER_ADDONS_DIR"%\dependencies
python -m pip install PyFFI=2.2.4.dev0 --target="%BLENDER_ADDONS_DIR"%\dependencies
