import traceback
import sys
import time

should_stop = False

def exit_handler(_):
    """
    check the type of stop, the following is the common one after step/next,
    a more complex one would be a subclass (for example breakpoint or signal)
    """
    global should_stop
    should_stop = True


class TraceAsm(gdb.Command):
    """
    Source: https://stackoverflow.com/a/46661931/8999671
    """

    def __init__(self):
        super().__init__(
            'trace-asm',
            gdb.COMMAND_RUNNING,
            gdb.COMPLETE_NONE,
            False
        )
        gdb.events.exited.connect(exit_handler)
        global should_stop
        should_stop = False

    def invoke(self, argument, _):
        argv = gdb.string_to_argv(argument)

        print(argv)
        
        if len(argv) > 0:
            f = open(argv[0], 'w')
        else:
            f = sys.stdout
        
        timeout_seconds = 60
        begin = time.time()

        try:
            f.write(f'<trace>\n')
            while True:
                if should_stop:
                    break
                succeeded = self.trace_step(f)
                if succeeded:
                    gdb.execute('s', to_string=True)  # This line steps to the next line which reduces overhead, but skips some lines compared to stepi.
                    # gdb.execute('si', to_string=True)  # Too slow
                    # gdb.execute('n', to_string=True)  # Juuuust right... until we have to step into a function call.
                else:
                    gdb.execute('finish')
                end = time.time()
                if end - begin > timeout_seconds:
                    f.write('<timeout/>\n')
                    break
        except Exception:
            traceback.print_exc()
        finally:
            f.write('</trace>\n')
            if len(argv) > 0:
                f.close()

    def trace_step(self, output_file):
        try:
            frame = gdb.selected_frame()
            sal = frame.find_sal()
            symtab = sal.symtab
            if symtab:
                path = symtab.fullname()
                line = sal.line
                is_main_exe = path is not None and (path.startswith('/workspace') or path.startswith('/tmp'))
                if is_main_exe:
                    variables = self.gather_vars(frame)
                    output_file.write(f'<program_point filename="{path}" line="{line}">\n')
                    for name, (valid, value) in variables.items():
                        output_file.write(f'<variable name="{name}" valid="{"true" if valid else "false"}">{value}</variable>\n')
                    output_file.write('</program_point>\n')
                    return True
        except Exception:
            traceback.print_exc()
        return False
    
    def gather_vars(self, frame):
        """
        Navigating scope blocks to gather variables.
        Source: https://stackoverflow.com/a/30032690/8999671
        """
        block = frame.block()
        variables = {}
        while block:
            for symbol in block:
                if (symbol.is_argument or symbol.is_variable):
                    name = symbol.name
                    if not name in variables and not name.startswith('std::'):
                        value = str(symbol.value(frame))
                        valid = True
                        value = (value
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            )
                        variables[name] = (valid, value)
            block = block.superblock
        return variables

TraceAsm()
