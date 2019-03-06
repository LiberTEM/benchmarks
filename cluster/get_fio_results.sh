#!/bin/bash
for i in "$@"; do
    echo -n "$i: "; jq '.jobs[0].read .bw_mean / 1024' < $i
done
