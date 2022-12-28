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

from functools import partial, wraps
from typing import Optional, Callable, Union, Any
from weakref import WeakValueDictionary


class Intern:
    """
    A class of interning decorators.

    Each instance of this class can be used as a decorator of a class. This will modify or add ``__new__`` and
    ``__init__`` methods to the decorated class so that instances of the class will be reused instead of creating
    multiple objects with the same value. (See :class:`str:intern` for a specific example of this behavior.)

    Objects are considered to be the same if they are created with the same parameters in the constructor call. These
    parameters are used as a key to an internal table that keeps track of already-created class objects. By default,
    the key consists of the values of the parameters, which must therefore be hashable.

    If some constructor parameters may be unhashable, a key function must be provided (either as a ``key``
    parameter to the specific ``intern`` call, or as a general ``default_key`` for the ``Intern`` class
    constructor). The key function will be used to compute the interning key; it will be given the same
    parameters given to the constructor.

    Note that a constructor call that provides a keyword parameter with its default value will create an object
    different from one created with a call that does not provide this keyword parameter. This behavior can be
    overridden by a custom key.

    For a detailed explanation, see the blog post
    https://the-dusty-deck.blogspot.com/2022/12/metaprogramming-in-python-2-interning.html
    """

    def __init__(self, default_key: Optional[Callable[[type], Callable]] = None):
        """
        Create an interning decorator.

        :param default_key: an optional function that returns an interning key given the decorated class
        """
        self.default_key = default_key
        self.interned_classes = []

    def __call__(self, cls: Optional[type] = None, *,
                 key: Callable = None,
                 reset_method: Optional[str] = 'reset_intern_memory'):
        """
        Decorator that interns elements of the class based on the parameters of the constructor.

        :param cls: class whose elements are to be interned
        :param key: an optional key function
        :param reset_method: the name of a method to be added to the class for resetting the interning table;
        None to prevent the creation of this method
        :return: same class, with modified or added __new__ and  __init__ methods
        """
        if cls is None:
            return partial(self, key=key, reset_method=reset_method)

        if key is None and self.default_key is not None:
            key = self.default_key(cls)

        memory = WeakValueDictionary()
        # cls._intern_memory = memory  # DEBUG

        old_new = getattr(cls, '__new__')
        if old_new is object.__new__:
            def __new__(cls, *args, **kwargs):
                element_key = (args, tuple(sorted(kwargs.items()))) if key is None else key(*args, **kwargs)
                try:
                    result = memory[element_key]
                    setattr(result, '*already-initialized*', True)
                    return result
                except KeyError:
                    result = object.__new__(cls)
                    memory[element_key] = result
                    return result
        else:
            def __new__(cls, *args, **kwargs):
                element_key = (args, tuple(sorted(kwargs.items()))) if key is None else key(*args, **kwargs)
                try:
                    result = memory[element_key]
                    setattr(result, '*already-initialized*', True)
                    return result
                except KeyError:
                    result = old_new(cls, *args, **kwargs)
                    memory[element_key] = result
                    return result

        setattr(cls, '__new__', __new__)

        init = getattr(cls, '__init__', None)
        if init is None:
            def __init__(self, *args, **kwargs):
                if not (hasattr(self, '*already-initialized*') and getattr(self, '*already-initialized*')):
                    super().__init__(self, *args, **kwargs)
        else:
            @wraps(init)
            def __init__(self, *args, **kwargs):
                if not (hasattr(self, '*already-initialized*') and getattr(self, '*already-initialized*')):
                    init(self, *args, **kwargs)

        setattr(cls, '__init__', __init__)

        if reset_method:
            def reset_intern_method():
                nonlocal memory
                memory = WeakValueDictionary()
                # cls._intern_memory = memory  # DEBUG

            setattr(cls, reset_method, reset_intern_method)
            self.interned_classes.append(cls)
        return cls


intern = Intern()
