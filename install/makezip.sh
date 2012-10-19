git clean -xfd
./install.sh

VERSION="2.6.0.2"
wcrev=`git log -1 --pretty=format:%h`
if [ "$1" == "" ]
then
    extversion=${VERSION}.${wcrev}
else
    extversion=${VERSION}-$1.${wcrev}
fi
NAME="blender_nif_plugin"
FILES="AUTHORS.rst CHANGELOG.rst LICENSE.rst README.rst install.sh install.bat scripts/ docs/_build/html/"

# update documentation
pushd ../docs
make clean
make html
popd

rm -f "${NAME}-${VERSION}"*
zip -9r "${NAME}-${extversion}.zip" ${FILES} -x \*/__pycache__/\*
tar cfvj "${NAME}-${extversion}.tar.bz2" ${FILES} --exclude=*__pycache__*

# create windows installer
rm -f "${NAME}-${VERSION}-windows.exe"
makensis -V3 ${NAME}.nsi
mv "${NAME}-${VERSION}-windows.exe" "${NAME}-${extversion}-windows.exe"
