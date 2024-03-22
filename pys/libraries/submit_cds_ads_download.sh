#!/bin/bash

# Limit stacksize

submitdate=$1
filename=$2
species=$3

echo "========================================="
echo "Inside sh script. Submitting job to download for $submitdate"

python download_ghg_egg4.py $submitdate $filename $species
