# clean everything up
pushd ..
git clean -xfd
popd

# update documentation
pushd ../docs
make clean
make html
popd

# create release zip and exe
pushd ..
python3 setup.py sdist --format=zip
python3 setup.py --command-packages bdist_nsi bdist_nsi --blender-addon=2.62
popd

