#!/bin/bash
for i in "$@"; do
    jq -r '[.throughput_mib,.method,.num_nodes,(.workers|length)]|@csv' < $i;
done
