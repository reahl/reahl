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

cd /tmp; reahl example -f tutorial.migration
cd /tmp/migration
chmod u+x /tmp/migration/migration_dev/test.sh
if /tmp/migration/migration_dev/test.sh
then 
    results["migration (actual migrating)"]="."
else
    results["migration (actual migrating)"]="E"
fi
cd -
rm -rf /tmp/migration

for x in "${!results[@]}"
do
    echo ${results["$x"]} $x
done
