"""This script is now NOT USED."""


import sys
import clang.cindex

def search(node, decl_info, func_name):
    if node.location.file is not None and node.location.file.name.endswith('test.cpp'):
        if (node.kind == clang.cindex.CursorKind.VAR_DECL
            or node.kind == clang.cindex.CursorKind.PARM_DECL):
            decl_info[node.spelling] = f'{node.location.file.name}:{node.location.line}:{node.location.column}'
    # Recurse for children of this node
    for c in node.get_children():
        search(c, decl_info, func_name)

clang.cindex.Config.set_library_file('/usr/lib/llvm-11/lib/libclang-11.so.1')
index = clang.cindex.Index.create()
tu = index.parse(sys.argv[1])
decl_info = {}
search(tu.cursor, decl_info, None)
print(decl_info)
