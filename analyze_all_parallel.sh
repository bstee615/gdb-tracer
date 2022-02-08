#!/bin/bash

mkdir -p logs

echo_var_c() {
    solutionFile="$1"
    problemDir=$(dirname $(dirname $solutionFile))
    inputFile="$2"
    # echo "Analyzing $solutionFile"
    solutionFileName="$(basename $solutionFile)"
    logFilePath="$(realpath logs/c-$(basename $problemDir)-${solutionFileName%.c}.xml)"
    solutionFileExe="${solutionFile%.c}"
    echo "***compiling*** $solutionFile"
    # if [ ! -f "$solutionFileExe" ]
    # then
        gcc -g $solutionFile -o $solutionFileExe 2>&1
    # fi
    exitCode="$?"
    if [ "$exitCode" -ne 0 ]
    then
        echo "Compile failed $exitCode, so quitting early"
        echo "***exitCode=$exitCode*** $solutionFile";
        return 1
    fi
    echo "***analyzing*** $solutionFile"
    echo "$solutionFileExe $inputFile"
    time (
        timeout 30s ./analyze "$solutionFileExe" "$inputFile" no "$logFilePath" 2>&1;
        exitCode="$?";
        echo "***exitCode=$exitCode*** $solutionFile";
    )
    # mv log.xml "$logFilePath"
    return 0
}
export -f echo_var_c

echo_var_cpp() {
    solutionFile="$1"
    problemDir=$(dirname $(dirname $solutionFile))
    inputFile="$2"
    # echo "Analyzing $solutionFile"
    solutionFileName="$(basename $solutionFile)"
    logFilePath="$(realpath logs/cpp-$(basename $problemDir)-${solutionFileName%.cpp}.xml)"
    solutionFileExe="${solutionFile%.cpp}"
    echo "***compiling*** $solutionFile"
    # if [ ! -f "$solutionFileExe" ]
    # then
        g++ -g $solutionFile -o $solutionFileExe 2>&1
    # fi
    exitCode="$?"
    if [ "$exitCode" -ne 0 ]
    then
        echo "Compile failed $exitCode, so quitting early"
        echo "***exitCode=$exitCode*** $solutionFile";
        return 1
    fi
    echo "***analyzing*** $solutionFile"
    echo "$solutionFileExe $inputFile"
    time (
        timeout 30s ./analyze "$solutionFileExe" "$inputFile" no "$logFilePath" 2>&1;
        exitCode="$?";
        echo "***exitCode=$exitCode*** $solutionFile";
    )
    # mv log.xml "$logFilePath"
    return 0
}
export -f echo_var_cpp

rm output.txt

for problemDir in mini_Project_CodeNet/p*
do
    problemName="$(basename $problemDir)"
    echo "***analyzing problem*** $problemDir"
    inputFile="$(realpath ../Project_CodeNet/derived/input_output/data/$problemName/input.txt)"
    # https://stackoverflow.com/a/50351932/8999671
    num_procs="6"
    ls $problemDir/C++/s*.cpp | parallel --group -I% --max-args 1 -P $num_procs echo_var_cpp % $inputFile {} &>> output.txt
    ls $problemDir/C/s*.c | parallel --group -I% --max-args 1 -P $num_procs echo_var_c % $inputFile {} &>> output.txt
    # break
done
