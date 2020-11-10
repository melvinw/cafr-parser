#!/bin/sh
cat args.txt | xargs -P 4 -I % sh -c ../../parse-cafr.py %
