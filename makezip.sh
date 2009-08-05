VERSION="2.4.11"
NAME="blender_nif_scripts"
FILES="scripts/import_nif.py scripts/export_nif.py scripts/bpymodules/nif_common.py scripts/bpymodules/nif_test.py scripts/mesh_niftools_weightsquash.py scripts/mesh_niftools_hull.py scripts/object_niftools_set_bone_priority.py scripts/object_niftools_save_bone_pose.py scripts/object_niftools_load_bone_pose.py ChangeLog README.html install.sh install.bat docs/*.*"

# update documentation
rm -rf docs
blender -P runepydoc.py

rm -f "${NAME}-${VERSION}".*
zip -9 "${NAME}-${VERSION}.zip" ${FILES}
tar cfvj "${NAME}-${VERSION}.tar.bz2" ${FILES}

# create windows installer
rm -f "win-install/${NAME}-${VERSION}-windows.exe"
wine ~/.wine/drive_c/Program\ Files/NSIS/makensis.exe /v3 win-install/${NAME}.nsi
