#!/bin/bash


cp alignment_phone.org alignment_phone.txt 
cp alignment_word.org alignment_word.txt 

# remove lines with "$" from the word
sed -ni '/\$$/!p' alignment_word.txt 
sed -i 's/\.txt//g' alignment_word.txt
sed -i 's/\.txt//g' alignment_phone.txt
