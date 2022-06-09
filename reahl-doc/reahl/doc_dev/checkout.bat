REM to redirect output: checkout.bat > testout.txt 2>&1
@ECHO off
setlocal ENABLEDELAYEDEXPANSION
SET ORIGINAL_DIR=%cd%
SET REAHL_TMP=%ORIGINAL_DIR%\tmp
mkdir %REAHL_TMP%
REM Perhaps use pushd an popd?
cd %REAHL_TMP%
SET EXAMPLE_LIST=('reahl listexamples')
REM SET EXAMPLE_LIST=("tutorial.hello")
for /F %%i in %EXAMPLE_LIST% do (
    REM get the 4th token grepping the output for a string
    for /F "tokens=4" %%j in ('reahl example -f %%i ^| findstr "Checking out to" ') do set EXAMPLE_DIR_OR_FILE=%%j
    REM only do this it the checkout worked
    if [!EXAMPLE_DIR_OR_FILE!] NEQ [] ( 
        if exist !EXAMPLE_DIR_OR_FILE!\NUL  (
            echo ---Example [%%i] is in a directory: !EXAMPLE_DIR_OR_FILE!
            cd !EXAMPLE_DIR_OR_FILE!
            python -m pip install --no-deps -e .
            reahl unit
            python -m pip uninstall !EXAMPLE_DIR_OR_FILE!
            cd %REAHL_TMP%
        ) else (
            echo ---Example [%%i] is in a file: !EXAMPLE_DIR_OR_FILE!
            nosetests !EXAMPLE_DIR_OR_FILE!            
        )
    )
)
cd %ORIGINAL_DIR%
rmdir /S /Q %REAHL_TMP%
ENDLOCAL

