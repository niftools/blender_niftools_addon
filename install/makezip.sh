git clean -xfd
./install.sh

VERSION=`cat ../io_scene_nif/VERSION`
NAME="blender_nif_plugin"

rm -f "${NAME}-${VERSION}".*

pushd ..
zip -9r "install/${NAME}-${VERSION}.zip" io_scene_nif -x \*/__pycache__/\*
popd
