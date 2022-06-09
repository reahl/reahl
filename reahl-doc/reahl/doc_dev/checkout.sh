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
        if reahl unit 
        then
            result="."
        fi
        python -m pip uninstall $(python -c 'from setuptools.config.setupcfg import read_configuration as c; print(c("setup.cfg")["metadata"]["name"])')
        cd -
    fi
    results["$i"]=$result
    rm -rf $out
done

cd /tmp; reahl example -f tutorial.migrationexample
cd /tmp/migrationexample
chmod u+x /tmp/migrationexample/migrationexample_dev/test.sh
if /tmp/migrationexample/migrationexample_dev/test.sh
then 
    results["migrationexample (actual migrating)"]="."
else
    results["migrationexample (actual migrating)"]="E"
fi
cd -
rm -rf /tmp/migrationexample

for x in "${!results[@]}"
do
    echo ${results["$x"]} $x
done
