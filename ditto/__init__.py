# Copyright (C) 2010-2011 Cisco Systems, Inc
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.  
#
# THIS SOFTWARE IS PROVIDED BY CISCO SYSTEMS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL CISCO SYSTEMS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Cisco Systems, Inc.

"""\
==================================================
Class mocking framework for use with unit testing
==================================================

Summary
=======

This module is meant to implement a "more" elegant class mocking framework for
python than what I can find by searching on Google. And by "elegant" I mean
more like Google's GMock. You might even say this is a port of GMock, although
I would say it's still got some pythonic flare.

How To Use
==========

Here's a general guide to how you can use the framework.

Instantiating Mock Instances
----------------------------

Given some class that you want to mock (call it ```Foo``), declare a *mocked*
instance of that class by doing the following::

    my_instance = Mock(Foo)

That is, pass the class that you want to mock to the constructor of ``Mock.``
It will automagically make ``my_instance`` have the same interface as ``Foo``,
except the methods will be mocked rather than real. (Note that there's no need
to ever define an actual class.) By default, all methods that don't feel like
python secret methods are mocked up. In other words, two mocked instances are
"equal" based on the ``__eq__`` method in the  ``Mock`` class. That method
isn't "mocked" based on seeing it in the original class. That's because
``__eq__`` isn't a method that will be mocked up by default. Mocking every
single method would essentially make ``Mock`` instances completely unusable,
because the mocks, themselves, lose most of their identity, and they still need
to exist as viable python objects.

The framework doesn't do a particularly good job of picking which methods to
mock and which to not, but that's actually not that big of a deal -- any
formula we choose would be bad in a certain set of cases. That's why we let you
define your own formula. If you'd like to control which methods get a mock or
not, just declare a function that decides this, and then register it when you
create your mock object::


    def pick_functions(class, method):
        return method in ['foo', 'bar', 'baz']

    my_instance = Mock(Foo, _method_selector=pick_functions)

As another example, the following function mocks every single method on a
mocked instance::

    def pick_functions(class, method_name):
        '''Return True if we should mock method_name in class'''
        return True

This example is not a useful one, though -- don't ever just return True.
``__class__`` is unmockable, because python will need that to actually point to
the ``Mock`` class. By the way, if you're trying to mock ``__class__`` you're
doing something wrong, so this isn't exactly a heinous restriction. It just
means there's no easy way to say "give me everything," because "everything" is
never a good idea.

Creating Expectations
---------------------

Rather than have the behavior you'd expect, each mocked method on a mocked
instance checks to make sure that we were expecting such a method call (this
method, these arguments, at this time) to happen. In order for it to make this
decision, you must give it a set of *expectations* to operate under.

To "expect" that a method on ``my_instance`` (call it ``bar``) will be called
with a given set of parameters (say ``1, 2, 3``), do the following::

    my_instance.foo.expect(1, 2, 3)

If you don't do this, calling the method (at this time) will not be expected,
and will raise an ``AssertionError``. (Note that the appropriate way to assert
that a method should never be called is to never call its ``expect`` method.)
The above snippet tells the mock framework to expect the following::

    my_instance.foo(1, 2, 3)

but only with these arguments. Any other arguments will be unexpected, and will
raise an ``AssertionError``.

Expectations *retire* when they've been satisfied. The mock framework holds a
list of all the expectations that are still waiting to be satisfied. At the end
of your program's run, you might want to assert that there are no more
expectations waiting to be met. This is a way of asserting that your code under
test *actually did* all the stuff you wanted it to do.

In order to do this, you need to understand *contexts*. When you create a
``Mock`` instance, as demonstrated above, the framework will create that
instance in the *default* context. Expectations created off that mock instance
will be added to the list of expectations in that default context. The default
context is a singleton, which can be accessed as follows::

    from ditto import default_context

There are two useful functions to use on a context.
``assert_no_more_expectations()`` will raise ``AssertionError`` if your test code
hasn't met all the expectations you've created. ``retire_all_expectations()``
clears the list, so that you can start a new round of testing.

If you'd like to separate expectations into multiple contexts, so that you can
assert that different sets of expectations have been met at different points
during your test, you can specify custom contexts by doing the following::

    c1 = Context()
    c2 = Context()

    m1 = Mock(Foo, _context=c1)
    m2 = Mock(Foo, _context=c2)

Obviously you can operate on ``c1`` and ``c2`` just like you can on
``default_context``.

Expecting Indefinite Arguments
------------------------------

Brittle tests suck. It's probably the case that you'll have to go tweak
something in a unit test when you modify the code that it tests, but we'd like
that to be as little as is reasonable. One way of helping with this is to
create expectations that are only as explicit as is required for the code to be
considered correct. (As an example, if your HTTP proxy starts tacking on an
``X-Foo`` header, and that header really isn't important, make sure your
relevant mocked classes won't fail when it starts to add that header.)

It might be the case, for instance, that all you really care about is that a
method is called with any arguments, or with three arguments, or that these
arguments are all strings, or that these string arguments all have the
substring "foo" in them.

To express such inexact expectations, use Hamcrest matchers.
``python-hamcrest`` is a literal port of the Java-based Hamcrest library into
Python. Think of these matchers as "regular expressions" for all different
kinds of python values (not just strings).

To use, wrap any hamcrest matcher instance in the ``matches()`` function from
this module::

    my_instance.foo.expect(matches(hamcrest.less_than(3)))

You can also wrap *any* instance that declares the method
``matches(other_thing)`` with ``matches()``, not just those found in hamcrest.

Changing Expectations
---------------------

By default, expectations retire after being satisfied a single time, can happen
in any order, and return ``None`` to the caller when they're satisfied. You can
change all of these things by calling various methods on an expectation
instance, which ``expect()`` returns::

    my_instance.foo.expect().returns(23).times(3).optional()
    my_instance.foo.expect().raises(Exception).infinite_times()

You can set whether an expectation returns a value or raises an error by using
``returns`` and ``raises``. You can make ``assert_no_more_expectations`` skip
over your expectation by using ``optional``. You can set the number of times
you want your expectation have to be met before it retires using ``times`` (or
you can make it never retire by using ``infinite_times``.

Another important way you can change an expectation is by putting it in a
sequence. By default, expectations that are active are active *for all possible
method calls in your context*. That is, it doesn't really matter what order you
created the expectations in. Obviously you might want to test that the order of
method calls in your code follows a tighter restriction. Do this by dropping
expectations into *sequences*::

    s = Sequence()
    my_instance.foo.expect(5).in_sequence(s)
    my_instance.foo.expect(6).in_sequence(s)

This asserts that the expectation of ``foo`` being called with ``6`` is only
active *after* the expectation that ``foo`` is called with ``5`` *retires*. In
other words, you have to call them in the order of the sequence for the test to
pass.

You can put expectations in more than one sequence, and you can put
expectations from more than one mocked object into the same sequence::

    s1 = Sequence()
    s2 = Sequence()

    # Expectation A
    my_instance.foo.expect(5).in_sequence(s1)

    # Expectation B
    my_other_instance.foo.expect(6).in_sequence(s1).in_sequence(s2)

    # Expectation C
    my_other_instance.bar.expect(6).in_sequence(s1)

    # Expectation D
    my_instance.bar.expect(8).in_sequence(s2)

This declares two sequences that, together, contain four expectations (labeled
A, B, C, D). Those sequences, if I were to print them out, would look like
this::

    s1 = (A, B, C,)
    s1 = (B, D,)

For this context, those are the only two sequences of expectations that will
result in a passing test. The framework will throw an error as soon as there's
no situation that could possibly result in a passing test. For instance, D
before anything else, or A followed by D, or B followed by C. It doesn't have
to get to the very end to realize that there's no way the test can pass. This
is useful because it helps make the traceback from the actual problematic call
site visible.

Applicative Declaration
-----------------------

Often, it's very useful to declare test data inside a huge applicative python
structure. Here's an example::

    my_data = [
        {'id': 1,
         'segment': Mock(Segment),}
    ]

It's really hard to do that if you have to go back and set expecations on all
the mock objects inside such a huge structure. In the above example, it would
appear, on the surface, that I might have to write code that iterates through
my huge structure, finds all the mock objects, and individually declares
expectations on them. Or, maybe I'd have to just delegate to some function::

    # XXX: This is NOT the way to do it!!
    def create_segment():
        m = Mock(PdtsSeg)
        m.send.expect().times(5)
        m.send_new_data.expect(matches(anything)).times(3)

        return m

    my_data = [
        {'id': 1,
         'segment': create_segment(),}
    ]


The solution this framework proposes can be colloquially described as "using
back pointers." Expectations point to their methods with the ``method`` attribute,
and methods point to their mock instance with the ``mock`` keyword. And every
method on an expectation returns the expectation right back to you. So you can
stack calls, like so::

    # XXX: Wow, that's a lot better.
    my_data = [
        {'id': 1,
         'segment':
              Mock(PdtsSeg).send.expect().times(5).method.mock \\
                           .send_new_data(matches(anything)).times(3).method.mock
        }
    ]

So what does all of this mean? It's entirely possible that every single mock
instance you'll ever create can be created with a *single python expression*,
and without having to declare a class. Beat that, googlemock. ;)

To Do
=====

There's still a bunch to do.

    - Currently, you have to manually retire expectations and check that all
      expectations were met. Surely there's a better way.
    - Should there be an easy way to make expectations from the same mocked
      instance go into different contexts?
"""

import collections

def str_tuple(tupl):
    return tuple(map(str, tupl))

def str_dict(dic):
    readable = {}
    for name, value in dic.items():
        readable[name] = str(value)

    return readable

def method_to_str(cls, method, args, kwargs):
    return '%s.%s(*args=%s, **kwargs=%s)' % (
        cls, method,
        args if isinstance(args, matches) else str_tuple(args),
        kwargs if isinstance(kwargs, matches) else str_dict(kwargs),
    )


class MockError(AssertionError):

    mock_msg = 'Mock:         {module}.{cls} at 0x{id:x}'
    expt_msg = 'Expectation:  {method}({args})'

    def format_expectation(self, exp):
      return self.expt_msg.format(
          method=exp.method.name,
          args=', '.join(
            ([repr(a) for a in exp.args]
                if isinstance(exp.args, collections.Iterable)
                    else ['*' + repr(exp.args)]) +
            (['{k}={v!r}'.format(k=k, v=v) for k, v in exp.kwargs.items()]
                if hasattr(exp.kwargs, 'items')
                    else ['**' + repr(exp.kwargs)])
          ),
      )

    def format_mock(self, mock, expectation_list):
        expectation_format='\n'.join(
          sorted([self.format_expectation(e) for e in expectation_list])
        )

        if mock is not None:
            return '{0}\n{1}'.format(
                self.mock_msg.format(
                    module=mock._mocked_cls.__module__,
                    cls=mock._mocked_cls.__name__,
                    id=id(mock)
                ),
                expectation_format
            )
        else:
            return expectation_format


    def format_expectation_set(self, expectations):
        mocks = collections.defaultdict(lambda: [])
        for e in expectations:
            mocks[e.method.mock].append(e)

        return '\n\n'.join([
            self.format_mock(m, exp_list)
            for m, exp_list in mocks.items()
        ])


class UnmetExpectations(MockError):
    msg = """

Required Expectations:
{required}
    """

    def __init__(self, context):
        super(UnmetExpectations, self).__init__(
            self.msg.format(
                required=self.format_expectation_set(context.required_expectations())
            )
        )

class UnexpectedMethodCall(MockError):

    msg = """

Could not find a suitable expectation:
{unmet}

Active Expectation Set:
{active}
    """

    def __init__(self, test_expectation):
        super(UnexpectedMethodCall, self).__init__(
            self.msg.format(
                unmet=self.format_mock(test_expectation.method.mock, [test_expectation]),
                active=self.format_expectation_set(test_expectation.context.active_expectations()),
            )
        )


class UnequalSumArguments(MockError):
    pass


class Context(object):

    """Manages a particular set of expectations. It's useful to have multiple
    contexts if more than one thread is doing mocking (you're crazy) or you
    have different sets of mock verifications going on at the same time. If you
    just want one, then just don't specify one, and you'll automatically use
    the singleton declared in this library.
    
    :Attributes:
        - `expectations`: The list of all current (non-retired) expectations.
        - `sequences`: The list of all sequences that could still potentially
          happen.
    """

    def __init__(self):
        self.expectations = []
        self.sequences = []

    def active_expectations(self):
        return [x.expectations[0] for x in self.sequences] + self.expectations

    def required_expectations(self):
        return [x for x in self.expectations if not x._is_optional]

    def retire_all_expectations(self):
        self.expectations = []
        self.sequences = []

    def assert_no_more_expectations(self):
        if self.required_expectations():
            raise UnmetExpectations(self)


class matches(object):

    def __init__(self, matcher):
        self.matcher = matcher

    def __eq__(self, other):
        return self.matcher.matches(other)

    def __repr__(self):
        return '<{0}>'.format(str(self.matcher))

    def __str__(self):
        return str(self.matcher)


class Sequence(object):

    """Represents an ordered list of expectations. Users express that a set of
    methods have to be invoked in a particular order by adding those expected
    method calls to an instance of this class. Note that those method calls do
    not all have to come from the same mock object.

    :Attributes:
        - `expectations`: a list of ``Expectation`` instances
    """

    def __init__(self):
        self.expectations = []
        self.context = None

    def add_expectation(self, context, expectation):
        if self.context is None:
            self.context = context
        elif self.context is not context:
            raise MockError('Sequences must live in only one context.')

        self.expectations.append(expectation)

        if expectation in context.expectations:
            self.context.expectations.remove(expectation)
        if self not in context.sequences:
            self.context.sequences.append(self)


class Sum(object):

    """True if all the calls to add() sum to a given value."""

    def __init__(self, args, kwargs):
        self.expected = (list(args), kwargs)
        self.actual = None

    def add(self, args, kwargs):
        exp_args, exp_kwargs = self.expected
        if len(args) != len(exp_args) or kwargs.keys() != exp_kwargs.keys():
            raise UnequalSumArguments(
                "expected format %r doesn't match call (%r, %r)" % (
                    self.expected, args, kwargs
                )
            )

        if self.actual is None:
            self.actual = (list(args), kwargs)
        else:
            act_args, act_kwargs = self.actual

            for i in range(len(act_args)):
                act_args[i] += args[i]

            for key in act_kwargs:
                act_kwargs[key] += kwargs[key]

    def __nonzero__(self):
        return self.expected == self.actual


class Expectation(object):

    """Represents the expectation of a method being called with particular
    arguments (and returning a particular value to the caller) a particular
    number of times. Any constraint that cannot be met with those three
    criteria should be met with a ``Sequence`` of expectations.
    """

    infinite = object()

    def __init__(self, context, method, args, kwargs):
        self.context = context
        self.method = method
        self.args = args
        self.kwargs = kwargs

        self.return_val = None
        self.raises_exception = None
        self._num_times = 1
        self._is_in_sequence = False
        self._is_optional = False
        self._sum_barrier = True

    def returns(self, value):
        if self.raises_exception is not None:
            raise MockError("Don't expect a call to both raise and return")

        self.return_val = value

        return self

    def raises(self, exception):
        if self.return_val is not None:
            raise MockError("Don't expect a call to both raise and return")

        self.raises_exception = exception

        return self

    def times(self, num_times):
        self._num_times = num_times

        return self

    def infinite_times(self):
        self._num_times = self.infinite
        self.optional()

        return self

    def until_sums_to(self, *args, **kwargs):
        self._sum_barrier = Sum(args, kwargs)

        return self

    def optional(self):
        self._is_optional = True

        return self

    def in_sequence(self, seq):
        if not hasattr(seq, 'add_expectation'):
            raise TypeError('Parameter "seq" should be a `mock.Sequence`')

        seq.add_expectation(self.context, self)
        self._is_in_sequence = True

        return self

    def _call(self, *args, **kwargs):
        """Let this expectation know that it's been called. Only call one of
        these functions per method call into a mock object!! By calling this
        function, you're telling the expectation to retire itself, if
        necessary, either from a sequence or from the context's expectations list.
        This function does not check the correctness of arguments. It's assumed
        if you're calling this function that you've already verified that this
        is the expectation you match.

        :Returns:
            This method returns the value that the expectation has been
            configured to return, or it raises the exception that it's been
            configured to raise
        """
        if not self._sum_barrier:
            self._sum_barrier.add(args, kwargs)

        if self._num_times is not self.infinite and self._sum_barrier:
            self._num_times -= 1

            if self._num_times == 0:
                if self._is_in_sequence:
                    sequences_to_remove = []
                    for seq in self.context.sequences:
                        if self in seq.expectations:
                            seq.expectations.remove(self)

                            if not seq.expectations:
                                sequences_to_remove.append(seq)

                    for seq in sequences_to_remove:
                        self.context.sequences.remove(seq)
                else:
                    self.context.expectations.remove(self)

        if self.raises_exception is not None:
            raise self.raises_exception

        return self.return_val

    def __str__(self):
        return '<Expected %s>' % (method_to_str(
            self.method.mock._mocked_cls.__name__, self.method.name,
            self.args, self.kwargs
        ))

    def __eq__(self, other):
        return hasattr(other, 'method') and hasattr(other, 'args') and \
               hasattr(other, 'kwargs') and self.method == other.method and \
               self.args == other.args and self.kwargs == other.kwargs


default_context = Context()


class MockMethod(object):

    """In every mock of some class, that class's real methods are replaced with
    instances of this class. When those instances are treated like methods,
    ``__call__`` will be invoked, and that's where we check expectations and
    compute (and return) return values.

    :Attributes:
        -`expectations`: This is a dictionary that maps (args, kwargs) to
        expectation instances. 
    """

    def __init__(self, context=default_context, name='anonymous', mock=None):
        self.context = context
        self.name = name
        self.mock = mock

    def __call__(self, *args, **kwargs):
        possible = self.context.active_expectations()

        test = Expectation(self.context, self, args, kwargs)

        try:
            # XXX. Be Careful. Because `possible` may contain `matches`
            # instances, you have to make sure the == ends up with the
            # `matches` on the left-hand size, because he's the one that needs
            # his __eq__ method invoked, since he's the one that knows how to
            # match himself against arbitrary objects using hamcrest. The
            # python expression "test in possible" won't work, for example,
            # because it calls the __eq__ method of `test` against every member
            # of possible. It's possible we should investigate a better way of
            # doing this, because I might be making an assumption that this
            # won't change in the future.
            return possible[possible.index(test)]._call(*args, **kwargs)
        except ValueError:
            raise UnexpectedMethodCall(test)

    def expect(self, *args, **kwargs):
        args_matcher = kwargs.pop('_args_matcher', None)
        kwargs_matcher = kwargs.pop('_kwargs_matcher', None)

        e = Expectation(self.context, self, args_matcher or args,
                        kwargs_matcher or kwargs)
        self.context.expectations.append(e)

        return e


def default_method_selector(mocked_cls, func_name):
    func = getattr(mocked_cls, func_name, None)
    return callable(func) and '__' not in func_name


class_level_mock_names = []


class Mock(object):

    def __init__(self, _mocked_cls, _method_selector=default_method_selector,
                 _context=default_context, **kwargs):
        """Create a mock instance that's based on some other class.

        :Parameters:
            - `_method_selector`: This is a function(cls, name_string) that
              should return True or False: True if name_string is a name of a
              function in cls that *should* be mocked, False otherwise.
            - `_context`: The instance of ``Context`` that this mock object is
              operating within. If you don't specify, will be the default
              singleton define in the ``mock`` module.
        """

        self._mocked_cls = _mocked_cls
        self._context = _context
        self._class_level_mocks = {}

        for func_name in dir(_mocked_cls):
            if _method_selector(_mocked_cls, func_name):
                mockmethod = MockMethod(_context, func_name, self)
                setattr(self, func_name, mockmethod)

        for func_name in class_level_mock_names:
            self._class_level_mocks[func_name] = MockMethod(
              _context, func_name, self
            )

        for name, value in kwargs.items():
            setattr(self, name, value)


def add_class_level_mock_method(method_name):
    """Force the Mock class to declare a MockMethod.

    In cases where it's required that the *class* define a method (and not just
    the instance), you have to call this function to make sure Mock's state
    gets changed accordingly. This is rare.

    This situation most often arises when you'd like to mock the behavior of a
    "protocol" method (something with underscores). Those methods can't be
    dynamically overridden. They have to live on the class.

    Be warned:
      This method will pretty much let you override anything. Don't be stupid.
      Don't feel the need to override __str__ just to get it mockable to prove
      that your to-strings are getting called. It's probably not worth it. The
      best example of when you should use something like that is __enter__ and
      __exit__ on a mock that's used with the "with" keyword.
    """
    class SpecialMethod(object):
        def __get__(self, instance, cls):
            class_mock = instance._class_level_mocks.get(method_name)
            instance_mock = instance.__dict__.get(method_name)
            mock = class_mock or instance_mock

            if mock is not None:
                return mock

            raise AttributeError(method_name)

    class_level_mock_names.append(method_name)
    setattr(Mock, method_name, SpecialMethod())

