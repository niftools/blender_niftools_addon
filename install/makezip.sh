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
rm -f "${NAME}-${VERSION}".*
zip -9r "install/${NAME}-${VERSION}.zip" ${FILES} -x \*/__pycache__/\*
tar cfvj "install/${NAME}-${VERSION}.tar.bz2" ${FILES} --exclude=*__pycache__*
popd

# create windows installer
rm -f "${NAME}-${VERSION}-windows.exe"
makensis -V3 -DVERSION=${VERSION} ${NAME}.nsi
