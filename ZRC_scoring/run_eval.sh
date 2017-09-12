#!/usr/bin/env bash


SCRIPT='/home/getalp/besacier/BACKUP-JSALT/MBOSHI/Gold-Mboshi-July2017/mboshi/eval2.py'
FILE='/home/getalp/besacier/BACKUP-JSALT/MBOSHI/Gold-Mboshi-July2017/ex_classes/mboshi.goldwords'
#FILE='/home/getalp/besacier/BACKUP-JSALT/MBOSHI/cascading/hard_seg_unsup_lucas_forced_word.fa'
EVAL='/home/getalp/besacier/BACKUP-JSALT/MBOSHI/Gold-Mboshi-July2017/eval'

source activate zerospeech

pushd /home/getalp/besacier/BACKUP-JSALT/MBOSHI/Gold-Mboshi-July2017/mboshi
# eval

#line below is not run if you already have the .classes file
#awk '{w[$4]=w[$4] $1" "$2" "$3"\n"}END{for(i in w){print "Class "++n; print w[i]}}' $FILE  > $FILE.classes
CORPUS='mboshi' python $SCRIPT -v $FILE.classes  $EVAL/ -m boundary token/type
# end eval
popd
