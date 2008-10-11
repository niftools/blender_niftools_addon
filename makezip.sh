VERSION="2.3.9"
NAME="blender_nif_scripts"
FILES="scripts/nif_import.py scripts/nif_export.py scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py scripts/mesh_weightsquash.py scripts/mesh_hull.py scripts/object_setbonepriority.py scripts/object_savebonepose.py scripts/object_loadbonepose.py ChangeLog README.html install.sh install.bat"

rm -f "${NAME}-${VERSION}".*
zip -9 "${NAME}-${VERSION}.zip" ${FILES}
tar cfvj "${NAME}-${VERSION}.tar.bz2" ${FILES}

# create windows installer
rm -f "win-install/${NAME}-${VERSION}-windows.exe"
wine ~/.wine/drive_c/Program\ Files/NSIS/makensis.exe /v3 win-install/${NAME}.nsi
