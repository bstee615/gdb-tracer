# https://stackoverflow.com/a/46661931/8999671
import os
import json

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
        # with open('decl_info.json') as f:
        #     self.decl_info = json.load(f)
        self.variable_states = []
    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if argv:
            gdb.write('Does not take any arguments.\n')
        else:
            n_instr = 1000000
            with open('trace.tmp', 'w') as f:
                for _ in range(n_instr):
                    if should_stop:
                        f.write("stopped{}".format(os.linesep))
                        break
                    try:
                        
                        frame = gdb.selected_frame()
                        sal = frame.find_sal()
                        symtab = sal.symtab
                        path = None
                        line = None
                        if symtab:
                            path = symtab.fullname()
                            line = sal.line

                        is_main_exe = path is not None and path.startswith('/workspace')
                        if is_main_exe:
                            block = frame.block()
                            variables = {}
                            while block:
                                for symbol in block:
                                    if (symbol.is_argument or symbol.is_variable):
                                        name = symbol.name
                                        if not name in variables and not name.startswith('std::'):
                                            value = symbol.value(frame)
                                            variables[name] = str(value)
                                block = block.superblock
                            for name, value in variables.items():
                                f.write(f'{path}:{line}, {name} = {value}\n')
                            self.variable_states.append((
                                path, line, variables
                            ))
                    except Exception as e:
                        f.write("exception {}{}".format(e, os.linesep))
                    gdb.execute('s', to_string=True)  # This line steps to the next line which reduces overhead, but skips some lines compared to stepi.
            with open('trace.json', 'w') as jf:
                json.dump(self.variable_states, jf, indent=2)
def exit_handler(event):
    # check the type of stop, the following is the common one after step/next,
    # a more complex one would be a subclass (for example breakpoint or signal)
    global should_stop
    should_stop = True
TraceAsm()
