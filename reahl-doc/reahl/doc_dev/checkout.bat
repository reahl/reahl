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
            reahl setup -- develop -N
            REM reahl unit
            reahl setup -- develop -N --uninstall
            cd %REAHL_TMP%
        ) else (
            echo ---Example [%%i] is in a file: !EXAMPLE_DIR_OR_FILE!
            REM nosetests !EXAMPLE_DIR_OR_FILE!            
        )
    )
)
ENDLOCAL
cd %ORIGINAL_DIR%
rmdir /S /Q %REAHL_TMP%

   
REM do
    REM result="E"
    REM out=$(cd /tmp; reahl example -f $i | awk '/Checking out to/ {print $4}')
    REM if [ -f $out ]
    REM then
        REM if nosetests $out
        REM then 
            REM result="."
        REM fi
    REM else
        REM cd $out
        REM reahl setup -- develop -N
        REM if reahl unit 
        REM then
            REM result="."
        REM fi
        REM reahl setup -- develop -N --uninstall
        REM cd -
    REM fi
    REM results["$i"]=$result
    REM rm -rf $out
REM done

REM cd /tmp; reahl example -f tutorial.migrationexample
REM cd /tmp/migrationexample
REM chmod u+x /tmp/migrationexample/migrationexample_dev/test.sh
REM if /tmp/migrationexample/migrationexample_dev/test.sh
REM then 
    REM results["migrationexample (actual migrating)"]="."
REM else
    REM results["migrationexample (actual migrating)"]="E"
REM fi
REM cd -
REM rm -rf /tmp/migrationexample

REM for x in "${!results[@]}"
REM do
    REM echo ${results["$x"]} $x
REM done
