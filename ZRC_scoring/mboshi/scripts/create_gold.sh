#!/bin/bash

# create gold.txt and tag.txt files to build the track2 
# topline

# these wrd and phn files have the tag SIL
file_wrd=./${CORPUS}.wrd
file_phn=./${CORPUS}.phn

rm -rf tags.txt gold.txt

tmpfile=$(mktemp)

# the ${file_phn} file outpu from the pipeline prep_mandarin.sh
sort -k1,1 -k2,2n ${file_phn} -o ${file_phn} #$tmpfile
grep -v SIL ${file_wrd} | awk '{print $1, $3, $3, ";eword"}' > $tmpfile

# get only the word separtor ;eword and the phonemes
cat ${file_phn} $tmpfile | sort -k1,1 -k2,2n | awk '{print $4}' | \
    tr '\n' ' ' | \
    sed 's/SIL SIL/SIL/g' | \
    sed 's/ \;eword SIL / \;eword\n/g' | \
    sed 's/ SIL \;eword / \;eword\n/g' | \
    sed 's/ SIL / \;eword\n/g' | \
    sed 's/^SIL //g' | \
    sed 's/^\;eword //g' | \
    sed '/^\;eword/d' > tags.txt

cat tags.txt | sed 's/\;eword/\*/g' | \
               sed 's/ //g' | \
               sed 's/\*/ /g' | \
               sed 's/^ //g' > gold.txt

rm -rf $tmpfile

