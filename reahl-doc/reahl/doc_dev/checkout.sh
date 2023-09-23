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

for x in "${!results[@]}"
do
    echo ${results["$x"]} $x
done
