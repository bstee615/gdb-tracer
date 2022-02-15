import traceback
import sys

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
        self.frame_to_vars = {}

    def invoke(self, argument, _):
        argv = gdb.string_to_argv(argument)
        
        if len(argv) > 0:
            f = open(argv[0], 'w')
        else:
            f = sys.stdout

        try:
            f.write(f'<trace>\n')
            while True:
                if should_stop:
                    break
                frame = gdb.selected_frame()
                sal = frame.find_sal()
                symtab = sal.symtab
                if symtab:
                    path = symtab.fullname()
                    line = sal.line
                    is_main_exe = path is not None and (path.startswith('/workspace') or path.startswith('/tmp'))
                    if is_main_exe:
                        f.write(f'<program_point filename="{path}" line="{line}">\n')
                        self.log_vars(frame, f)
                        f.write('</program_point>\n')
                        f.flush()
                        gdb.execute('s')  # This line steps to the next line which reduces overhead, but skips some lines compared to stepi.
                    else:
                        gdb.execute('finish')
        except Exception:
            traceback.print_exc()
        finally:
            f.write('</trace>\n')
            if len(argv) > 0:
                f.close()
    
    def log_vars(self, frame, f):
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
                        proxy = None
                        value = str(symbol.value(frame))
                        if symbol.type.name == 'std::stringstream':
                            proxy = "std::stringstream::str()"
                            command = f'printf "\\"%s\\"", {symbol.name}.str().c_str()'
                            
                            try:
                                value = gdb.execute(command, to_string=True)
                                value_lines = value.splitlines(keepends=True)
                                value = ''.join(l for l in value_lines if not l.startswith('warning:'))
                            except gdb.error:
                                value = '<error>'

                        age = 'new'
                        old_vars = self.frame_to_vars.get(str(frame), {})
                        if name in old_vars:
                            age = 'modified'
                            if old_vars[name][1] == value:
                                age = 'old'

                        value = (value
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            )
                        
                        proxy_str = ""
                        if proxy:
                            proxy_str = f' proxy="{proxy}"'
                        f.write(f'<variable name="{name}" type="{age}"{proxy_str}>{value}</variable>\n')
            block = block.superblock
        self.frame_to_vars[str(frame)] = variables

TraceAsm()
