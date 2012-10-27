git clean -xfd
./install.sh

VERSION=`cat ../scripts/addons/io_scene_nif/VERSION`
NAME="blender_nif_plugin"
FILES="AUTHORS.rst CHANGELOG.rst LICENSE.rst README.rst install/install.sh install/install.bat scripts/ docs/_build/html/"

# update documentation
pushd ../docs
make clean
make html
popd

pushd ..
python3 setup.py sdist --format=zip
python3 setup.py --command-packages bdist_nsi bdist_nsi --blender-addon=2.62
popd

