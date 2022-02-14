# https://stackoverflow.com/a/46661931/8999671
import os
import traceback
import re

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
        
        n_instr = 1000000
        text_offset = 0
        with open(argv[0] + '_log', 'w') as f:
            f.write(f'<trace>\n')
            for _ in range(n_instr):
                if should_stop:
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
                        # Navigating scope blocks to gather variables https://stackoverflow.com/a/30032690/8999671
                        block = frame.block()
                        variables = {}
                        while block:
                            for symbol in block:
                                if (symbol.is_argument or symbol.is_variable):
                                    name = symbol.name
                                    if not name in variables and not name.startswith('std::'):
                                        value = str(symbol.value(frame))
                                        valid = True
                                        # if value.startswith('<') and value.endswith('>'):
                                        #     value = value[1:-1]
                                        #     valid = False
                                        # value = re.sub(r'\<([^>]*)\>', '"\1"', value)
                                        value = (value
                                            .replace('&', '&amp;')
                                            .replace('<', '&lt;')
                                            .replace('>', '&gt;')
                                            )
                                        variables[name] = (valid, value)
                            block = block.superblock
                        f.write(f'<program_point filename="{path}" line="{line}">\n')
                        for name, (valid, value) in variables.items():
                            f.write(f'<variable name="{name}" valid="{"true" if valid else "false"}">{value}</variable>\n')

                        # TODO: May want to use named pipes for smarter solution
                        gdb.execute('call fflush(stdout)')
                        if os.path.exists(argv[0]):
                            print('read', argv[0], 'at', text_offset)
                            with open(argv[0]) as inf:
                                inf.seek(text_offset)
                                text = inf.read()
                                if len(text) > 0:
                                    print('Got text')
                                text_offset += len(text)
                            if not text:
                                text = None
                        else:
                            text = None
                        if text:
                            f.write(f'<stdout>{text}</stdout>\n')
                        f.write('</program_point>\n')
                except Exception as e:
                    # f.write("exception {}{}".format(e, os.linesep))
                    traceback.print_exc()

                # gdb.execute('s', to_string=True)  # This line steps to the next line which reduces overhead, but skips some lines compared to stepi.
                # gdb.execute('si', to_string=True)  # Too slow
                gdb.execute('n', to_string=True)  # Juuuust right... until we have to step into a function call.
            with open(argv[0]) as inf:
                inf.seek(text_offset)
                text = inf.read()
            if text:
                f.write(f'<stdout unattached="true">{text}</stdout>\n')
            f.write('</trace>\n')
def exit_handler(event):
    # check the type of stop, the following is the common one after step/next,
    # a more complex one would be a subclass (for example breakpoint or signal)
    global should_stop
    should_stop = True
TraceAsm()
