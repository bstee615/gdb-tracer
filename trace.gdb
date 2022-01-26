source trace_asm.py
b main
r < testdata.txt
set logging file /dev/null
source trace_asm.py 
set logging redirect on
set logging on
trace-asm
