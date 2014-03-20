#!/bin/bash

declare -A results
for i in $(reahl listexamples)
do
    result="E"
    out=$(cd /tmp; reahl example -f $i | awk '/Checking out to/ {print $4}')
    if [ -f $out ]
    then
        if nosetests $out
        then 
            result="."
        fi
    else
        cd $out
        reahl setup -- develop -N
        if reahl unit 
        then
            result="."
        fi
        reahl setup -- develop -N --uninstall
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
