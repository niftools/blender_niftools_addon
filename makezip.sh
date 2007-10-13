VERSION="2.1.13"
NAME="blender_nif_scripts"
FILES="scripts/nif_import.py scripts/nif_export.py scripts/mesh_weightsquash.py scripts/mesh_hull.py scripts/bpymodules/nifImEx/__init__.py scripts/bpymodules/nifImEx/Config.py scripts/bpymodules/nifImEx/Defaults.py scripts/bpymodules/nifImEx/Read.py scripts/bpymodules/nifImEx/Write.py scripts/bpymodules/nifImEx/niftools_logo.png ChangeLog README.html install.sh"

rm -f "${NAME}-${VERSION}".*
zip -9 "${NAME}-${VERSION}.zip" ${FILES}
tar cfvj "${NAME}-${VERSION}.tar.bz2" ${FILES}

read -p "Press any key to build the windows installer..."

# create windows installer
rm -f "win-install/${NAME}-${VERSION}-windows.exe"
wine ~/.wine/drive_c/Program\ Files/NSIS/makensis.exe /v3 win-install/blender_nif_scripts.nsi
