#!/bin/bash

#                                                                      
# This script builds the individual phone and words files from         
# the kaldi alignments. These files are the input for the              
# prep_mandarin.py script, that builds the files:                      
#                                                                      
#     ${CORPUS}.{phn|intervals.cross|split|intervals.within|wrd}        
#                                                                      

. config

working_dir=.
output_dir=${working_dir}/in

# directories used by prep_mandarin.py to build the  
mkdir -p $output_dir
rm -rf $output_dir/* 

## where the phone and words for the challenge are stored
###p=/fhgfs/bootphon/projects/challenge2017/final_datasets/alignment/${CORPUS}
p=./alignment/

phn=$working_dir/${CORPUS}.phn
wrd=$working_dir/${CORPUS}.wrd
sil=$working_dir/${CORPUS}.sil

## copy a version of phones file order by file and starting time
## the maximun number of seconds is 2672s you can use n_sec=300000 to take all data
n_sec=6000000
cat $p/alignment_phone.txt | \
    awk '{ if($2<n_sec) {printf("%s %.4f %.4f %s\n", $1, $2, $3, $4)}}' n_sec=$n_sec | \
    sort -k1,1 -k2,2n -k3,3n > $phn                                   

### if select SIL with a threshold 
SILTHR=0
cat $phn | awk '{if($4=="SIL") {if (($3-$2)>silthr) print $0 }}' silthr=$SILTHR > $sil 
grep -v SIL $phn > ${phn}.tmp
cat ${phn}.tmp $sil > $phn
rm ${phn}.tmp

###### CREATING INDIVIDUAL PHN FILES
# coping the phones for each speaker in a different file 
echo "Doing phn"
cat $phn | awk '{print $1}' | sort -u > $working_dir/${CORPUS}.lst
for f in $(cat $working_dir/${CORPUS}.lst); do
    echo "phn> " $f
    grep $f $phn | awk '{printf("%.4f %.4f %s\n", $2, $3, $4)}' | \
        sort -k1n > $output_dir/${f}.phn_orig
    
    # including SIL when there are gaps in the file
    ./scripts/correct_sil.py $output_dir/${f}.phn_orig 'ERROR' 'phn' > $output_dir/${f}.phn
done

## same for the words ... however aligments_word.txt does't have 
## lines with SIL and are copied from individual 
## cat $sil $p/alignment_word.txt | sed 's/\xc2\xa0/ /g' | \
cat $sil $p/alignment_word.txt | \
    awk '{if($2<n_sec) {printf("%s %.4f %.4f %s\n", $1, $2, $3, $4)}}' n_sec=$n_sec | \
    sort -k1,1 -k2,2n -k3,3n > $wrd                                   

echo "Doing wrd"
for f in $(cat $working_dir/${CORPUS}.lst); do
    echo "wrd> " $f
    grep $f $wrd | awk '{printf("%.4f %.4f %s\n", $2, $3, $4)}' | \
        sort -k1n > $output_dir/${f}.wrd_orig 
    
    # some wrd files have a problems with the end of the last word 
    # they have set a smaller time that the begining, here I get   
    # the ending time of the last syllabe and pass to the          
    # end of the word file.                                        
    correct_start=$(tail -n 1 $output_dir/${f}.wrd_orig | awk '{print $1}');
    corrected_end=$(tail -n 1 $output_dir/${f}.phn | awk '{print $2}');
    correct_text=$(tail -n 1 $output_dir/${f}.wrd_orig | awk '{print $3}');
    (head -n -1 $output_dir/${f}.wrd_orig; \
     echo $correct_start $corrected_end $correct_text) > t_
    mv t_ $output_dir/${f}.tmp

    ./scripts/correct_sil.py $output_dir/${f}.tmp 'XSIL' 'wrd' > $output_dir/${f}.wrd
    rm -rf $output_dir/${f}.tmp 
done

