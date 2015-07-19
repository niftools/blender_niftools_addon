#!/bin/sh

#Script to install developer dependancies for the Blender Nif Plugin
for BLENDERVERSION in 2.66 2.65 2.64 2.63 2.62
do
  BLENDERADDONS=~/.blender/$BLENDERVERSION/scripts/addons
  if [ -e ~/.blender/$BLENDERVERSION/ ]
  then
    python3 -m pip install Sphinx --target="$BLENDERADDONS/modules" && python3 -m pip install nose --target="$BLENDERADDONS/modules" && installsuccess=1
    break
  fi
done
if [ $installsuccess ]
then
  echo "Dependencies were successfully installed in: $BLENDERADDONS/modules"
else
  if [ -e ~/.blender/$BLENDERVERSION/ ]
  then
    echo "Install failed. (Sorry no clear reason here. Check the output above.)"
  else
    echo "Install failed: No compatible blender version found."
  fi
fi
