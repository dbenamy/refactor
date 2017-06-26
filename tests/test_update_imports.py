import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from redbaron import RedBaron

from update_imports import abs_mod_path, parse_moves, update_imports_ast


class TestAbsFromImport(unittest.TestCase):
    def assert_updated_imports(self, old_code, moves, new_code):
        ast = RedBaron(old_code)
        update_imports_ast('not-used.py', ast, parse_moves(moves))
        self.assertEqual(ast.dumps(), new_code)

    def test_rename_rhs(self):
        self.assert_updated_imports(
            'from pkg1 import utils',
            [('pkg1.utils', 'pkg1.stuff')],
            'from pkg1 import stuff as utils'
        )

    def test_rename_rhs_with_as(self):
        self.assert_updated_imports(
            'from pkg1 import utils as u',
            [('pkg1.utils', 'pkg1.stuff')],
            'from pkg1 import stuff as u'
        )

    def test_rename_part_of_rhs(self):
        self.assert_updated_imports(
            'from pkg1 import utils, code',
            [('pkg1.utils', 'pkg1.stuff')],
            'from pkg1 import stuff as utils, code'
        )

    def test_rename_lhs_causing_split(self):
        self.assert_updated_imports(
            'from pkg1 import mod1, mod2',
            [('pkg1.mod1', 'pkg2.mod1')],
            'from pkg1 import mod2\nfrom pkg2 import mod1\n'
        )

    # TODO
    # def test_merge_rhs(self):
    #     self.assert_updated_imports(
    #         'from pkg1 import utils, code',
    #         [('pkg1.utils', 'pkg1.code')],
    #         'from pkg1 import code'
    #     )
    #     # TODO test that it outputs a warning that anything referencing utils will break

    def test_rename_lhs(self):
        self.assert_updated_imports(
            'from pkg1 import utils',
            [('pkg1', 'pkg2')],
            'from pkg2 import utils'
        )

    def test_rename_lhs_with_as(self):
        self.assert_updated_imports(
            'from pkg1 import utils as u',
            [('pkg1', 'pkg2')],
            'from pkg2 import utils as u'
        )

    def test_rename_lhs_and_rhs(self):
        self.assert_updated_imports(
            'from pkg1 import utils',
            [('pkg1.utils', 'pkg2.stuff')],
            'from pkg2 import stuff as utils\n'
        )

    def test_rename_lhs_and_rhs_with_as(self):
        self.assert_updated_imports(
            'from pkg1 import utils as u',
            [('pkg1.utils', 'pkg2.stuff')],
            'from pkg2 import stuff as u\n'
        )

    def test_rename_lhs_and_part_of_rhs(self):
        self.assert_updated_imports(
            'from pkg1 import mod1, mod2',
            [('pkg1.mod1', 'pkg2.mod3')],
            'from pkg1 import mod2\nfrom pkg2 import mod3 as mod1\n'
        )

    def test_rename_inner_symbol(self):
        self.assert_updated_imports(
            'from pkg1 import utils',
            [('pkg1.utils.moo', 'pkg1.utils.cow')],
            'from pkg1 import utils'
        )

    def test_rename_inner_symbol_with_as(self):
        self.assert_updated_imports(
            'from pkg1 import utils as u',
            [('pkg1.utils.moo', 'pkg1.utils.cow')],
            'from pkg1 import utils as u'
        )

    def test_rename_sibling(self):
        self.assert_updated_imports(
            'from pkg1 import utils',
            [('pkg1.x', 'pkg1.y')],
            'from pkg1 import utils'
        )

    def test_rename_sibling_with_as(self):
        self.assert_updated_imports(
            'from pkg1 import utils as u',
            [('pkg1.x', 'pkg1.y')],
            'from pkg1 import utils as u'
        )

    def test_rename_top_pkg(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('pkg1', 'pkg2')],
            'from pkg2.utils import api'
        )

    def test_rename_top_pkg_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('pkg1', 'pkg2')],
            'from pkg2.utils import api as a'
        )

    def test_rename_lhs_subpkg(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('pkg1.utils', 'pkg1.stuff')],
            'from pkg1.stuff import api'
        )

    def test_rename_lhs_subpkg_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('pkg1.utils', 'pkg1.stuff')],
            'from pkg1.stuff import api as a'
        )

    def test_rename_3rd_level_rhs(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('pkg1.utils.api', 'pkg1.utils.rpc')],
            'from pkg1.utils import rpc as api'
        )

    def test_rename_3rd_level_rhs_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('pkg1.utils.api', 'pkg1.utils.rpc')],
            'from pkg1.utils import rpc as a'
        )

    def test_rename_1st_and_3rd_levels(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('pkg1.utils.api', 'pkg2.utils.rpc')],
            'from pkg2.utils import rpc as api\n'
        )

    def test_rename_1st_and_3rd_levels_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('pkg1.utils.api', 'pkg2.utils.rpc')],
            'from pkg2.utils import rpc as a\n'
        )

    def test_rename_inner_4th_level(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('pkg1.utils.api.foo', 'pkg1.utils.api.bar')],
            'from pkg1.utils import api'
        )

    def test_rename_inner_4th_level_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('pkg1.utils.api.foo', 'pkg1.utils.api.bar')],
            'from pkg1.utils import api as a'
        )

    def test_rename_unrelated_with_same_name_as_nested(self):
        self.assert_updated_imports(
            'from pkg1.utils import api',
            [('utils', 'whatever')],
            'from pkg1.utils import api'
        )

    def test_rename_unrelated_with_same_name_as_nested_with_as(self):
        self.assert_updated_imports(
            'from pkg1.utils import api as a',
            [('utils', 'whatever')],
            'from pkg1.utils import api as a'
        )


class TestRelFromImport(unittest.TestCase):
    def assert_updated_imports(self, mod_path, old_code, moves, new_code):
        ast = RedBaron(old_code)
        update_imports_ast(mod_path, ast, parse_moves(moves))
        self.assertEqual(ast.dumps(), new_code)

    def test_rename_pkg_containing_rel_import(self):
        self.assert_updated_imports(
            'code/pkg1/mod1.py',
            'from . import mod2',
            [('code.pkg1', 'code.pkg2')],
            'from code.pkg2 import mod2' # it'd be cool to leave this a rel import but for now it makes it abs. maybe special case rel imports that don't go up a level to stay rel.
        )

    def test_rename_mod_being_relatively_imported(self):
        self.assert_updated_imports(
            'code/pkg1/mod1.py',
            'from . import mod2',
            [('code.pkg1.mod2', 'code.pkg1.bob')],
            'from . import bob as mod2'
        )

    def test_rename_mod_being_relatively_imported_with_as(self):
        self.assert_updated_imports(
            'code/pkg1/mod1.py',
            'from . import mod2 as m',
            [('code.pkg1.mod2', 'code.pkg1.bob')],
            'from . import bob as m'
        )

    def test_rename_pkg_containing_mod_being_relatively_imported(self):
        self.assert_updated_imports(
            'code/pkg1/mod1.py',
            'from ..pkg2 import mod2',
            [('code.pkg2', 'code.pkg3')],
            'from code.pkg3 import mod2' # it'd be cool to leave this a rel import but for now it makes it abs
        )

    def test_rename_mod_in_a_different_pkg_being_relatively_imported(self):
        self.assert_updated_imports(
            'pkg1/mod1.py',
            'from ..pkg2 import mod2',
            [('pkg2.mod2', 'pkg2.new')],
            'from ..pkg2 import new as mod2'
        )

    def test_rename_mod_in_a_different_pkg_being_relatively_imported_with_as(self):
        self.assert_updated_imports(
            'pkg1/mod1.py',
            'from ..pkg2 import mod2 as m',
            [('pkg2.mod2', 'pkg2.new')],
            'from ..pkg2 import new as m'
        )


class TestPlainImport(unittest.TestCase):
    def assert_updated_imports(self, old_code, moves, new_code):
        ast = RedBaron(old_code)
        update_imports_ast('not-used.py', ast, parse_moves(moves))
        self.assertEqual(ast.dumps(), new_code)

    def test_update_single(self):
        self.assert_updated_imports(
            'import x',
            [('x', 'api')],
            'import api as x'
        )

    def test_update_single_with_as(self):
        self.assert_updated_imports(
            'import x as foo',
            [('x', 'api')],
            'import api as foo'
        )

    def test_update_first(self):
        self.assert_updated_imports(
            'import x.y',
            [('x', 'api')],
            'import api.y'
        )
        # TODO assert warning

    def test_update_first_with_as(self):
        self.assert_updated_imports(
            'import x.y as foo',
            [('x', 'api')],
            'import api.y as foo'
        )

    def test_update_second(self):
        self.assert_updated_imports(
            'import x.y',
            [('x.y', 'x.block')],
            'import x.block'
        )
        # TODO assert warning

    def test_update_second_with_as(self):
        self.assert_updated_imports(
            'import x.y as foo',
            [('x.y', 'x.block')],
            'import x.block as foo'
        )

    def test_update_1st_of_3(self):
        self.assert_updated_imports(
            'import x.y.z',
            [('x', 'api')],
            'import api.y.z'
        )
        # TODO assert warning

    def test_update_1st_of_3_with_as(self):
        self.assert_updated_imports(
            'import x.y.z as foo',
            [('x', 'api')],
            'import api.y.z as foo'
        )

    def test_update_2nd_of_3(self):
        self.assert_updated_imports(
            'import x.y.z',
            [('x.y', 'x.block')],
            'import x.block.z'
        )
        # TODO assert warning

    def test_update_2nd_of_3_with_as(self):
        self.assert_updated_imports(
            'import x.y.z as foo',
            [('x.y', 'x.block')],
            'import x.block.z as foo'
        )

    def test_update_3rd_of_3(self):
        self.assert_updated_imports(
            'import x.y.z',
            [('x.y.z', 'x.y.code')],
            'import x.y.code'
        )
        # TODO assert warning

    def test_update_3rd_of_3_with_as(self):
        self.assert_updated_imports(
            'import x.y.z as foo',
            [('x.y.z', 'x.y.code')],
            'import x.y.code as foo'
        )

    def test_move_up_a_level(self):
        self.assert_updated_imports(
            'import x.y',
            [('x.y', 'z')],
            'import z'
        )
        # TODO assert warning


class TestAbsModPath(unittest.TestCase):
    def test_absolute(self):
        self.assertEqual(abs_mod_path('pkg1/pkg2/mod1.py', 'code'), 'code')

    def test_child(self):
        self.assertEqual(abs_mod_path('pkg1/pkg2/code.py', '.code.mod2'), 'pkg1.pkg2.code.mod2')

    def test_sibling(self):
        self.assertEqual(abs_mod_path('pkg1/pkg2/mod1.py', '.code'), 'pkg1.pkg2.code')

    def test_parent(self):
        self.assertEqual(abs_mod_path('pkg1/pkg2/mod1.py', '..code'), 'pkg1.code')

    def test_top_level_parent(self):
        self.assertEqual(abs_mod_path('pkg1/mod1.py', '..pkg2'), 'pkg2')


if __name__ == '__main__':
    unittest.main()
