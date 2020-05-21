:: Install developer dependencies for integration tests
@echo off

if "%BLENDER_ADDONS_DIR%" == "" if not exist "%BLENDER_ADDONS_DIR%" (
echo. "Update BLENDER_ADDONS_DIR to the folder where the blender addons reside, such as:"
echo. "set BLENDER_ADDONS_DIR=%APPDATA%\Blender Foundation\Blender\2.79\scripts\addons"
echo.
pause
goto end
)

::TODO replace with equivalent setup.py call via pip to remove

echo. "Installing Sphinx to %BLENDER_ADDONS_DIR%"
python -m pip install "Sphinx" --target="%BLENDER_ADDONS_DIR%"
echo. "Installing nose to %BLENDER_ADDONS_DIR%"
python -m pip install "nose" --target="%BLENDER_ADDONS_DIR%"
echo. "Installing pydevd debugger"
python -m pip install "pydevd-pycharm~=201.6668.60" --target="%BLENDER_ADDONS_DIR%"


:: Currently pyffi pypi distribution does not contain runtime generated files
:: echo. "Installing nose to %BLENDER_ADDONS_DIR%\dependencies"
:: python -m pip install PyFFI==2.2.4.dev2 --target="${BLENDER_ADDONS_DIR}"
