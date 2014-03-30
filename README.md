# Summary

`ditto` is a mocking library that takes its heritage from gmock, rather than
from Michael Foord's `mock`, now included with stock Python. That means `ditto`
is fail-fast, and mock objects feel a lot like the objects they replace.

# Doc

For the full documentation, [rtfd](out http://ditto.readthedocs.org/en/latest/the-docs.html).

I try to keep it built and up to date, but I don't promise anything. :) You can
build the full doc yourself with the doc directory Makefile, but the real doc
is all in docstrings in the source.

# Rationale

I wanted to build something subtley different than Python's `mock`. 

Python's `mock` is an "Arrange, Act, Assert" (AAA) library. That means mock
objects are totally generic when they're created. They simply write down how
they're interacted with. A developer makes assertions about function calls that
happened to the mock *after* a test completes, but configures *stubs* (return
values) beforehand. In a sense, the two behaviors (stub and mock) are separate
and distinct features of the library, which is confusing and limited.

I don't have a catchy acronym for the order of things in `ditto`, but here's
roughly how it works.

1. Mock a particular, explicit class
2. Declare expectations on its methods
3. Run your test.

Wait for failures, when the code doesn't interact with a mock like you've
expected it to. As for stubs, they're just expectations that never expire and
that are optional.

In `ditto`, return values are declared on expectations, not on the mocks,
themselves. That means you declare both the expectation and what that call
should return at the same time. This gives you the power to couple return
values to your assertions about interaction.

Furthermore, `ditto` mocks *specifically* mock a particular class. This is
intentional. Python mocks don't know what objects they're mocking, so your
test code is free to treat them however it likes. This flexibility is not
welcome -- it means passing tests don't really mean bugfree code. (You could,
say, call a method that doesn't even exist on the real object, and a normal
Python mock would just return None.) `ditto` only lets you override stuff on the
class you're actually mocking.

In `ditto`, you set expecations, *then*, you use the mocks. In python mock,
because you don't assert before you act, it means it's impossible to "fail
fast" in a test. When your asserts fail, it doesn't come with a useful stack
trace. That's fine for short, simple code, but most of the time you want your
library to throw an exception the second it knows something has gone wrong,
that way there's a stacktrace you can use to understand where the bug is. The
only time `ditto` doesn't fail fast is when you assert that your test is done
and there are outstanding expectations (meaning that the erroneous behavior is
actually the lack of any behavior at all -- you never called a function that
you were supposed to call). You can't have a stacktrace for something that
didn't happen, so I'm okay with this.

Python mock also has no graceful way to mock out "protocol" (sometimes called
"special") methods, because mock objects can be literally anything (functions,
even). You have to explicitly use a separate class, MagicMock?, and you might
not get the behavior you expect.

Finally, I really hate monkey patching, and Python's mock library seems to
encourage it. In general, I much prefer the *dependency injection* pattern.
Classes shouldn't depend explicitly on a specific type (or explicitly invoke
constructors). Instead, classes should be wired together at runtime. This
allows your test harness to wire in mocks instead of real objects, and obviates
the need for monkey patching. Allowing people to use patchers encourages them
to not use the principle of loose coupling in their design. If they're
importing some other module and calling its constructor, rather than accepting
an instance as an argument, they created what you might call a "false
dependency", and they've tightly coupled their module to the other. This might
sound contrary to the Pythonic ideal that you shoudln't dictate how people use
your code, but monkey patching happens to be something that I so fundamentally
hate that, in this case, I'd rather violate the Pythonic ideals than allow it.

