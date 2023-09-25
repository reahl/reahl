#!/bin/bash

declare -A results
for i in $(reahl listexamples)
do
    result="E"
    out=$(cd /tmp; reahl example -f $i | awk '/Checking out to/ {print $4}')
    if [ -f $out ]
    then
        if pytest $out
        then 
            result="."
        fi
    else
        cd $out
        python -m pip install --no-deps -e .
        pytest
        exit_code=$?
        if [ $exit_code -eq 0 ] || [ $exit_code -eq 5 ]; then
            result="."
        fi
        python -m pip uninstall -y $(python -c 'from toml import load; print(load("pyproject.toml")["project"]["name"])')
        cd -
    fi
    results["$i"]=$result
    rm -rf $out
done

cd /tmp; reahl example -f tutorial.migrationexamplebootstrap
cd /tmp/migrationexamplebootstrap
chmod u+x /tmp/migrationexamplebootstrap/migrationexamplebootstrap_dev/test.sh
if /tmp/migrationexamplebootstrap/migrationexamplebootstrap_dev/test.sh
then 
    results["migrationexamplebootstrap (actual migrating)"]="."
else
    results["migrationexamplebootstrap (actual migrating)"]="E"
fi
cd -
rm -rf /tmp/migrationexamplebootstrap

check_existence() {
    local error=0

    if [ $# -eq 0 ]; then
        echo "No arguments provided."
        return 1
    fi

    for path in "$@"; do
        if [ ! -e "$path" ]; then
            echo "Does not exist: $path"
            error=1
        fi
    done

    return $error
}

#verify some packaging niggles
cd /tmp; reahl example -f howtos.hellodockernginx
cd -
expected_directories=("/tmp/hellodockernginx/prod/etc" "/tmp/hellodockernginx/etc" "/tmp/hellodockernginx/scripts")
expected_files=("/tmp/hellodockernginx/prod/nginx/Dockerfile")
check_existence "${expected_directories[@]}" "${expected_files[@]}"
error_code=$?

if [ $error_code -eq 0 ]
then
    results["hellodockernginx (packaging)"]="."
else
    results["hellodockernginx (packaging)"]="E"
fi

#Disply the results of all the checks
for x in "${!results[@]}"
do
    echo ${results["$x"]} $x
done

