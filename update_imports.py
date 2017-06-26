#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Assumes all relative imports start with a period."""

import argparse
import logging
import os
import re
import time
from collections import namedtuple
from importlib import import_module

from redbaron import CommentNode, RedBaron

log = logging.getLogger()


def main():
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    exre = None
    if args.exclude:
        exre = re.compile(args.exclude)
    paths = recurse(args.path, hidden_dirs=args.hidden_dirs, exclude=exre)
    old, new = [x.strip() for x in args.move.split(',')]
    moves = parse_moves([(old, new)]) # only 1 move at a time for now
    update_imports(paths, moves)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hidden-dirs", action="store_true", help="descent into hidden dirs")
    parser.add_argument("-x", "--exclude", help="exclude files and dirs matching regexp", type=str)
    parser.add_argument("-v", "--verbose", help="print more", action="store_true")
    parser.add_argument("-d", "--debug", help="print even more", action="store_true")
    parser.add_argument("-m", "--move", help="a package/module/symbol move in the form of 'from.here,to.here'", type=str, required=True)
    parser.add_argument("path", nargs="*", default="./", help="path to run on", type=str)
    args = parser.parse_args()
    return args


def parse_moves(moves):
    ModPath = namedtuple('ModPath', ['full', 'except_last', 'last'])
    parsed = []
    for old, new in moves:
        o = old.rsplit('.', 1)
        if len(o) == 1:
            oldel, oldl = o, None
        else:
            oldel, oldl = o
        n = new.rsplit('.', 1)
        if len(n) == 1:
            newel, newl = n, None
        else:
            newel, newl = n
        parsed.append([ModPath(old, oldel, oldl), ModPath(new, newel, newl)])
    log.debug("Parsed moves: %r", parsed)
    return parsed


def recurse(path, hidden_dirs=False, exclude=None):
    """If path is a directory, recurse into it and return a list of paths.
    If path is a file, return a singleton list with that path.  If hidden_dirs
    is true, recurse into hidden dirs.  Exclude is something with a truthy "search"
    function that, if it returns true, will exclude dirs or files."""
    if isinstance(path, list):
        r = []
        for p in path:
            r += recurse(p)
        return r

    if os.path.isfile(path):
        return [path]

    paths = []
    for dirpath, dirnames, fnames in os.walk(path):
        rm = set()
        if not hidden_dirs:
            rm.update({d for d in dirnames if d.startswith(".")})
        if exclude:
            rm.update({d for d in dirnames if exclude.search(d)})
        for d in rm:
            dirnames.remove(d)

        for fname in fnames:
            if fname.endswith(".py"):
                paths.append(os.path.join(dirpath, fname))

    return paths


def update_imports(paths, moves):
    for path in paths:
        t0 = time.time()
        update_imports_file(path, moves)
        td = time.time() - t0
        log.info("%s ... %0.3f", path, td)


def update_imports_file(path, moves):
    with open(path, 'r') as f:
        ast = RedBaron(f.read())
    update_imports_ast(path, ast, moves)
    with open(path, 'w') as f:
        f.write(ast.dumps())


def update_imports_ast(path, ast, moves):
    log.debug("Processing file %s", path)

    # import each parent and see if it includes the child. if so add those
    # module paths to a warning list to flag (but not update) if seen.

    for stmt in ast.find_all('ImportNode'):
        log.debug("  Processing statement: %s", stmt)

        for imp in stmt.value:
            log.debug("    Processing subimport %s", imp)

            absfrm = abs_mod_path(path, imp.value.dumps())
            log.debug("      Absolute path %s", absfrm)

            # if imp.value startswith any warning paths
            #     warn

            for old, new in moves:
                log.debug("      Processing move %s -> %s for 'import' updates", old.full, new.full)
                # if tail was changed and stmt.value == oldpath and as is None
                if absfrm == old.full and not imp.target:
                    if len(imp.value) == 1:
                        imp.target = imp.value.dumps()
                    else:
                        log.debug("Warning: updating 'import %s' to 'import %s'; you'll nned to any references to %s", old.full, new.full, old.full)
                if absfrm.startswith(old.full):
                    imp.value = new.full + absfrm[len(old.full):]
                    log.debug("        Updated subimport to %r", imp)

    for fin in ast.find_all('FromImportNode'):
        log.debug("  Processing statement: %s", fin)

        absfrm = abs_mod_path(path, fin.value.dumps())
        log.debug("    Absolute path %s", absfrm)

        assert len(moves) == 1 # haven't fully implemented multiple moves at once
        new_fin = None
        remove_targets = []

        for tgt in fin.targets:
            log.debug("    Processing subimport from %s import %s", absfrm, tgt)

            for old, new in moves:
                log.debug("      Processing move %s -> %s for 'from' and 'from/import' updates", old.full, new.full)
                if absfrm == old.except_last and tgt.value == old.last:
                    # eg for move a.b.c -> foo.bar, old.except_last == 'a.b' and old.last = 'c'

                    # Update targets (the rhs / imports) before the value (lhs /
                    # from) because the latter might move the target to a new
                    # FromImportNode and should take this edit along with it.
                    if tgt.value != new.last:
                        tgt.value = new.last
                        if not tgt.target:
                            tgt.target = old.last
                        log.debug("        Updated target/rhs/import: %r", fin)
                    if absfrm != new.except_last:
                        # fin.value = new.except_last # original too-simple version
                        # Move this import to a new FromImportNode because this
                        # one may have other imports that shouldn't be moved.
                        if not new_fin:
                            new_fin = RedBaron('from %s import %s' % (new.except_last, tgt.dumps()))[0]
                        else:
                            new_fin.targets.append(tgt.copy())
                        # I don't know if it's safe to delete while iterating over the targets so hackily mark if for deletion later
                        # tgt.value = 'this_was_moved_and_should_be_deleted'
                        remove_targets.append(tgt)
                        log.debug("        Prepped for moving this to a new from/import node")
                # if absfrm == any warning paths heads and import is tail
                #     warn
                # if absfrm startswith any warning paths
                #     warn

        if new_fin:
            # TODO might be cool to move any CommentNodes after fin to above it,
            # since they might apply to fin or might apply to new_fin.
            node = fin
            while node.next and type(node.next) == CommentNode:
                node = node.next
            node.insert_after(new_fin)
            for t in remove_targets:
                fin.targets.remove(t)
            if len(fin.targets) == 0:
                fin.parent.remove(fin)
            log.debug("    Updated value/lhs/from, resulting in a new statement: %r and %r", fin, new_fin)

        # Updates that only touch lhs of from imports (from part).
        for old, new in moves:
            log.debug("    Processing move %s -> %s for 'from'-only updates", old.full, new.full)
            # TODO error on multiple matches
            if absfrm.startswith(old.full):
                # replace_import(fin.value, new.full + absfrm[len(old.full):])
                fin.value = new.full + absfrm[len(old.full):]
                # TODO split from because there might be existing ones.
                log.debug("      Updated from from/value: %s", fin)


def abs_mod_path(from_file, imp):
    if not from_file.endswith('.py'):
        raise ValueError("abs_mod_path call with non-.py file %r" % from_file)

    if from_file.startswith('./'):
        from_file = from_file[2:]
    if from_file.endswith('/__init__.py'):
        mod = from_file.replace('/', '.')[:-12]
    else:
        mod = from_file.replace('/', '.')[:-3]

    if imp[0] != '.':
        return imp
    while imp and imp[0] == '.':
        last_dot = mod.rfind('.')
        if last_dot > 0:
            mod = mod[:last_dot]
        else:
            mod = ''
        imp = imp[1:]
    return mod + ('.' if mod and imp else '') + imp


if __name__ == '__main__':
    main()
