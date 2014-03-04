#!/bin/bash

# command to run with ssh
cmd='failed="";\
     for w in 0 1 2 8 9 11 13 14 15 16; do\
         ping -c1 w$w &> /dev/null || failed="$failed $w";\
     done;\
     if [ "$failed" != "" ]; then\
         echo " Failed $failed";\
         exit 1;\
     fi;\
     exit 0;'

# for each node number
for n in 00 01 02 08 09 11 13 14 15 16; do
    # ssh into node $n and execute the lines in $cmd
    echo -n "testing rasp$n..."
    ssh rasp$n.lab.es.aau.dk "eval $cmd" && echo " OK"
done
