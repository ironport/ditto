# Summary
ditto is a mocking framework that takes its heritage from gmock, rather than
from Michael Foorde's python mock. That means ditto is fail-fast, and mock
objects feel a lot like the objects they replace.

# Doc

For the full documentation, check out http://derrley.net/ditto-doc/

I try to keep it built and up to date, but I don't promise anything. :) You can
build the full doc yourself with the doc directory Makefile, but the real doc
is all in docstrings in the source.

# Rationale

As opposed to ditto, mock is an "Arrange, Act, Assert" (AAA) framework. That
means mock objects are totally generic when they're created. They simply write
down how they're interacted with. You assert after the test runs (rather than
before) that they were interacted with correctly. This approach is riddled with
problems. I don't have a catchy acronym for the order of things in ditto, but
you first mock a particular class, then declare expectations on its methods,
then run your test.

Because "Arrange, Act, Assert" has you acting before asserting, you can't
specify return values from mocked methods based on the types of arguments you
get (or specify return values to happen in a particular order). In ditto,
return values are declared on expectations, not on the mocks, themselves. That
means you declare both the expectation and what that call should return at the
same time. This gives you the power to couple return values with precise calls
to the method.

Furthermore, because the mock objects don't know what objects they're mocking,
your test code is free to treat them however it likes. This flexibility is not
welcome -- it means passing tests don't really mean bugfree code. (You could,
say, call a method that doesn't even exist on the real object.) ditto only lets
you override stuff on the class you're actually mocking.

Because you don't assert before you act, it also means it's impossible to "fail
fast" in a test. That means when your asserts fail, it doesn't come with a
useful stack trace. That's fine for short, simple code, but for complex classes
you really would like the test to fail as fast as possible, so you actually
have the stacktrace at the point of failure. The only time ditto doesn't fail
fast is when you assert that your test is done and there are outstanding
expectations (meaning that the erroneous behavior is actually the lack of any
behavior at all -- you never called a function that you were supposed to call).
You can't have a stacktrace for something that didn't happen, so I'm okay with
this.

Also, there's no graceful way to mock out "protocol" (sometimes called
"special") methods, because mock objects can be literally anything (functions,
even). You have to explicitly use a separate class, MagicMock?, and you might
not get the behavior you expect.

Finally, I really hate the idea of patcher functionality -- this takes stuff
that a particular piece of code might refer to out of scope (like, some class's
name) and monkey-patches in your mock instead. In general, I much prefer
explicit construction of classes to take instances as input, and passing in a
mock instance rather than monkey-patching in a mock class. Allowing people to
use patchers encourages them to not use the principle of loose coupling in
their design -- if they're importing some other module and calling its
constructor, rather than accepting an instance as an argument, they created
what you might call a "false dependency", and they've tightly coupled their
module to the other.
