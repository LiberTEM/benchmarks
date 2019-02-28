#!/bin/bash
ansible-playbook bench.yml --forks 16 "$@"
