#!/bin/bash

mkdir -p logs outputs

num_procs="6"
archive_dir="../Project_CodeNet/mini"
output_file="output.txt"

trap "echo Analysis interrupted!; exit;" SIGINT SIGTERM

num_problems=1
num_solutions=5

rm -f $output_file
for problem_dir in $(ls -d $archive_dir/p* | head -n$num_problems)
do
    problemName="$(basename $problem_dir)"
    echo "***analyzing problem*** $problem_dir"
    echo "***analyzing problem*** $problem_dir" >> $output_file
    input_file="$(realpath ../Project_CodeNet/derived/input_output/data/$problemName/input.txt)"

    # Use parallel --group to buffer output by job. Source: https://stackoverflow.com/a/50351932/8999671
    ls $problem_dir/C/s*.c $problem_dir/C++/s*.cpp \
    | head -n$num_solutions \
    | parallel --group -I% --max-args 1 -P $num_procs \
        ./analyze % $input_file --infer_output_files -v &>> $output_file
    echo "***done analyzing problem*** $problem_dir" >> $output_file
done
