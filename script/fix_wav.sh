#!/bin/bash
wav="$1"
outdir="$2"
bname=$(basename $wav)
sox --ignore-length "$wav" "$outdir/$bname"

