"""Setup script for blender nif plugin."""

classifiers = """\
Development Status :: 4 - Beta
License :: OSI Approved :: BSD License
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
Topic :: Multimedia :: Graphics :: 3D Modeling
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.0
Programming Language :: Python :: 3.1
Programming Language :: Python :: 3.2
Operating System :: OS Independent"""
#Topic :: Formats and Protocols :: Data Formats

from distutils.core import setup
import sys

if sys.version_info < (3, 0):
    raise RuntimeError("The blender nif plugin requires Python 3.0 or higher.")

readme_lines = open("README.rst").read().split("\n")
version = open("scripts/addons/io_scene_nif/VERSION").read().strip()

setup(
    name='io_scene_nif',
    version=version,
    packages=['io_scene_nif'],
    package_dir={'io_scene_nif': 'scripts/addons/io_scene_nif'},
    package_data={
        'io_scene_nif': ['VERSION'],
        },
    author="Amorilia",
    author_email="amorilia@users.sourceforge.net",
    license="BSD",
    keywords="blender nif import export",
    platforms=["any"],
    description=readme_lines[0],
    classifiers=[_f for _f in classifiers.split("\n") if _f],
    long_description = "\n".join(readme_lines[2:]),
    url="http://niftools.sourceforge.net/",
    download_url="http://sourceforge.net/projects/niftools/files/blender_nif_scripts/",
)
