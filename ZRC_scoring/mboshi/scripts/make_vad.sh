#!/bin/bash

set -e

#  
#
# this script will create the directory 'vad' 
# that contains the VAD for each speaker/file.
# And these VAD files have the format used by
# Aren lsh program
#
# also it will build CORPUS_vad file that 
# contains the list of all VAD with the fist
# column 
#

. config

ofile="${CORPUS}_vad"
vads_dir=$(pwd)/vad

# alignemnts from abkhazia
phn_file=./alignment/alignment_phone.txt 
wrd_file=./alignment/alignment_word.txt

mkdir -p $vads_dir 
rm -rf $ofile

#
# the aligment.txt file has the following fields:
#
#            file start(sec) end(sec) phoneme
#
# where phoneme is SIL for silences. VAD files contains
# the lines with in the format:
#
#            file,star(frame),end(frame)
#
# in the VAD file the star to end frames are the places
# in the file with speech
#
# NOTE : aligment.txt has some phonem's holes (chunks were there is
# speech but no phonems repored)
#

# function in python that reads a file and get ouput the 
# consecutive gaps/
function mix_sil() {
    PYTHON_ARG="$1" python - <<EOF
import os
import pandas as pd
data = pd.read_csv(os.environ['PYTHON_ARG'])
s_ = data['end'][:-1]
e_ = data['start'][1:]
f_id = data['f_id'][0]
for s, e in zip(s_, e_):
    print("{},{:d},{:d}".format(f_id, int(s), int(e)))
EOF
}

# extract the files from aligments
cut -d' ' -f1 $wrd_file | sort -u > list_files.txt
echo 'f_id,start,end' > $ofile
for file_ in $(cat list_files.txt); do
    echo "doing $file_"
    echo 'f_id,start,end' | tee $vads_dir/${file_} > ${file_}.tmp;

    # VAD file contains the intervals where speach is present
    # I select the rows with the text SIL, SPN and SIL, and
    # the intevals are selected with the mix_sil function
    cat $phn_file | grep $file_ | \
        sort -k 1,1 -k 2,2n | \
        grep -e SIL -e SPN -e sil | \
        awk '{printf("%s,%.4f,%.4f\n",$1, $2*100, $3*100)}' >> ${file_}.tmp;
    
    mix_sil ${file_}.tmp >> $ofile
    mix_sil ${file_}.tmp | awk 'BEGIN{FS=","}{print $2, $3}'> $vads_dir/${file_} 
    rm -rf ${file_}.tmp
done

rm -rf list_files.txt

