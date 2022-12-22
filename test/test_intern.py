# Copyright IBM Corporation 2022
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
import unittest

from typeguard.importhook import install_import_hook

install_import_hook('metautils')

from metautils.intern import intern, Intern


@intern
class Foo:
    def __init__(self, s1: str, i1: int, t1: tuple, set1: frozenset, kt1: tuple = ()):
        self.s1 = s1
        self.i1 = i1
        self.t1 = t1
        self.set1 = set1
        self.kt1 = kt1


def key_func(s1: str, i1: int, t1: tuple, set1: frozenset, kt1: tuple = ()):
    return s1, i1, t1, set1, kt1


@intern(key=key_func)
class Bar:
    def __init__(self, s1: str, i1: int, t1: tuple, set1: frozenset, kt1: tuple = ()):
        self.s1 = s1
        self.i1 = i1
        self.t1 = t1
        self.set1 = set1
        self.kt1 = kt1


keyed_intern = Intern(default_key=lambda _: key_func)


@keyed_intern
class Baz:
    def __init__(self, s1: str, i1: int, t1: tuple, set1: frozenset, kt1: tuple = ()):
        self.s1 = s1
        self.i1 = i1
        self.t1 = t1
        self.set1 = set1
        self.kt1 = kt1


@intern
class Qux:
    def __init__(self, s1: str, i1: int, l1: list, set1: set, kt1: tuple = ()):
        self.s1 = s1
        self.i1 = i1
        self.l1 = l1
        self.set1 = set1
        self.kt1 = kt1


def key_func_for_list(s1: str, i1: int, l1: list, set1: set, kt1: tuple = ()):
    return s1, i1, tuple(l1), frozenset(set1), kt1


@intern(key=key_func_for_list)
class Quux:
    def __init__(self, s1: str, i1: int, l1: list, set1: set, kt1: tuple = ()):
        self.s1 = s1
        self.i1 = i1
        self.l1 = l1
        self.set1 = set1
        self.kt1 = kt1


def key_by_id(s1: str, i1: int, l1: list, set1: set, kt1: tuple = ()):
    return tuple(map(id, (s1, i1, l1, set1, kt1)))


@intern(key=key_by_id)
@dataclass
class Xyzzy:
    s1: str
    i1: int
    l1: list
    set1: set
    kt1: tuple = ()


class TestIntern(unittest.TestCase):
    def test_default_intern(self):
        obj1 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((10, 11)))
        obj2 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)))
        self.assertIs(obj1, obj2)
        obj3 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), kt1=())
        # different because keyword parameter was used in obj3 but not in obj1
        self.assertIsNot(obj1, obj3)
        obj4 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), ())
        # different because optional parameter was given in obj4 but not in obj1
        self.assertIsNot(obj1, obj4)

    def test_intern_with_key(self):
        obj1 = Bar('test1', 1, ((1, 2), (3, 4)), frozenset((10, 11)))
        obj2 = Bar('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)))
        self.assertIs(obj1, obj2)
        obj3 = Bar('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), kt1=())
        # this time they are the same
        self.assertIs(obj1, obj3)
        obj4 = Bar('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), ())
        # this time they are the same
        self.assertIs(obj1, obj4)

    def test_intern_with_default_key(self):
        obj1 = Baz('test1', 1, ((1, 2), (3, 4)), frozenset((10, 11)))
        obj2 = Baz('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)))
        self.assertIs(obj1, obj2)
        obj3 = Baz('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), kt1=())
        # this time they are the same
        self.assertIs(obj1, obj3)
        obj4 = Baz('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)), ())
        # this time they are the same
        self.assertIs(obj1, obj4)

    def test_reset(self):
        obj1 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((10, 11)))
        Foo.reset_intern_memory()
        obj2 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)))
        self.assertIsNot(obj1, obj2)
        obj3 = Foo('test1', 1, ((1, 2), (3, 4)), frozenset((11, 10)))
        self.assertIs(obj2, obj3)

    def test_list_no_key(self):
        try:
            Qux('test1', 1, [(1, 2), (3, 4)], {10, 11})
        except TypeError:
            pass
        else:
            self.fail("Expected TypeError: unhashable type: 'list'")

    def test_list_with_key(self):
        obj1 = Quux('test1', 1, [(1, 2), (3, 4)], {10, 11})
        obj2 = Quux('test1', 1, [(1, 2), (3, 4)], {11, 10})
        self.assertIs(obj1, obj2)
        obj3 = Quux('test1', 1, [(1, 2), (3, 4)], {11, 10}, kt1=())
        self.assertIs(obj1, obj3)
        obj4 = Quux('test1', 1, [(1, 2), (3, 4)], {11, 10}, ())
        self.assertIs(obj1, obj4)

    def test_id_key(self):
        list1 = [(1, 2), (3, 4)]
        set1 = {10, 11}
        obj1 = Xyzzy('test1', 1, list1, set1)
        obj2 = Xyzzy('test1', 1, list1, set1, kt1=())
        self.assertIs(obj1, obj2)
        obj3 = Xyzzy('test1', 1, [(1, 2), (3, 4)], set1, kt1=())
        self.assertIsNot(obj1, obj3)


if __name__ == '__main__':
    unittest.main()
