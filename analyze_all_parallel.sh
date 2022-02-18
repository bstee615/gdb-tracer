#!/bin/bash

# analyze_all_parallel.sh: run analysis script in parallel on lots of programs.
#
# Expects an analysis script named "analysis" with the following arguments:
# ./analysis <src_file> <input_file> [other arguments]
#
# Example:
# ./analysis foo.c input.txt --infer_output_files -v
# 
# Analysis script is expected to dump trace logs to logs/ and program outputs to outputs/
#

# Capture Ctrl+C rather than continuing the loop
trap "echo Analysis interrupted!; exit;" SIGINT SIGTERM

num_procs="6"                       # Parameter: how many processes to parallelize over?
num_problems="2"                    # Parameter: how many problems to analyze?
num_solutions="5"                   # Parameter: how many solutions to analyze in each problem?
codenet_root="../Project_CodeNet"   # Parameter: location of CodeNet root directory containing inputs/outputs
archive_dir="$codenet_root/mini"    # Parameter: location of source archive
output_file="output.txt"            # Parameter: output file name

# Return a list of source code file names.
function get_source_file_names()
{
    ls $problem_dir/C/s*.c $problem_dir/C++/s*.cpp | head -n$num_solutions
}

mkdir -p logs outputs
rm -f $output_file
for problem_dir in $(ls -d $archive_dir/p* | head -n$num_problems)
do
    problemName="$(basename $problem_dir)"
    echo "***analyzing problem*** $problem_dir"
    echo "***analyzing problem*** $problem_dir" >> $output_file
    input_file="$(realpath $codenet_root/derived/input_output/data/$problemName/input.txt)"

    # Use parallel --group to buffer output by job. Source: https://stackoverflow.com/a/50351932/8999671
    get_source_file_names | parallel --group -I% --max-args 1 -P $num_procs \
        ./analyze % $input_file --infer_output_files -v &>> $output_file
    echo "***done analyzing problem*** $problem_dir" >> $output_file
done
