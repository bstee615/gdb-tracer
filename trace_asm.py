# https://stackoverflow.com/a/46661931/8999671
import os

should_stop = False

class TraceAsm(gdb.Command):
    def __init__(self):
        super().__init__(
            'trace-asm',
            gdb.COMMAND_BREAKPOINTS,
            gdb.COMPLETE_NONE,
            False
        )
        gdb.events.exited.connect(exit_handler)
        global should_stop
        should_stop = False
    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if argv:
            gdb.write('Does not take any arguments.\n')
        else:
            done = False
            thread = gdb.inferiors()[0].threads()[0]
            last_path = None
            last_line = None
            last_myexe_line = None
            n_instr = 100000
            with open('trace.tmp', 'w') as f:
                for i in range(n_instr):
                    if should_stop:
                        f.write("stopped{}".format(os.linesep))
                        break
                    try:
                        frame = gdb.selected_frame()
                        sal = frame.find_sal()
                        symtab = sal.symtab
                        if symtab:
                            path = symtab.fullname()
                            line = sal.line
                        else:
                            path = None
                            line = None
                        if path != last_path:
                            # f.write("path {}{}".format(path, os.linesep))
                            last_path = path
                        is_main_exe = path is not None and path.endswith('test.cpp')
                        if line != last_myexe_line and is_main_exe:
                            f.write("path {} line {}{}".format(path, line, os.linesep))
                            f.write("variables: {}{}".format(gdb.execute('info locals', to_string=True), os.linesep))
                        if line != last_line:
                            last_line = line
                            if is_main_exe:
                                last_myexe_line = line
                        pc = frame.pc()
                        gdb.execute('si', to_string=True)
                        # if is_main_exe:
                        #     f.write("path {} line {} {} {} {}".format(path, line, hex(pc), frame.architecture().disassemble(pc)[0]['asm'], os.linesep))
                    except Exception as e:
                        f.write("exception {}{}".format(e, os.linesep))
def exit_handler(event):
    # check the type of stop, the following is the common one after step/next,
    # a more complex one would be a subclass (for example breakpoint or signal)
    global should_stop
    should_stop = True
TraceAsm()
