#!/bin/bash
echo "throughput_mib,method,num_nodes,num_workers,tilesize_bytes,path"
for i in "$@"; do
    jq -r '[.throughput_mib,.method,.num_nodes,(.workers|length),.tilesize_bytes,.path]|@csv' < $i;
done
