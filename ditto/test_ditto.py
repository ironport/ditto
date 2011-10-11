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


import hamcrest
import unittest

from ditto import (Mock, Expectation, Sequence, default_context,
                   UnmetExpectations, UnexpectedMethodCall, matches, Sum,
                   UnequalSumArguments)


# This excpetion is defined so that it's easy to detect when we neglect to mock
# a function and call the 'real' one accidentally.
class MockTestExcpetion(Exception): pass


class ThingToMock(object):

    def __init__(self, oneval, twoval):
        oneval = oneval
        twoval = twoval

    def bar(self):
        raise MockTestExcpetion

    def baz(self):
        raise MockTestException


class OtherThingToMock(object):

    def foo(self):
        raise MockTestException


class MockTest(unittest.TestCase):

    def setUp(self):

        default_context.retire_all_expectations()

        self.mock_of_thing = Mock(ThingToMock)
        self.other_mock_of_thing = Mock(ThingToMock)
        self.mock_of_other_thing = Mock(OtherThingToMock)


class ExpectNoCall(MockTest):

    def runTest(self):
        self.mock_of_thing.baz.expect()

        self.assertRaises(UnmetExpectations,
                          default_context.assert_no_more_expectations)


class ExpectationList(MockTest):

    def runTest(self):
        exp = self.mock_of_thing.baz.expect()
        exp2 = self.mock_of_thing.baz.expect(1, two='two')

        meth = exp.method
        meth2 = exp2.method

        self.assertEquals(2, len(default_context.expectations))

        self.assert_(exp in default_context.expectations)
        self.assert_(exp2 in default_context.expectations)

        newexp = Expectation(default_context, meth, (), {})
        newexp2 = Expectation(default_context, meth2, (1,),
                              {'two': 'two'})

        self.assert_(newexp in default_context.expectations)
        self.assert_(newexp2 in default_context.expectations)

        self.mock_of_thing.baz()
        self.assertEquals(1, len(default_context.expectations))
        self.mock_of_thing.baz(1, two='two')
        self.assertEquals(0, len(default_context.expectations))


class Validate(MockTest):

    def tearDown(self):
        default_context.assert_no_more_expectations()


class Default(Validate):

    def runTest(self):
        # Assert that expect() and add_return_value() actually return
        # 'self', so that you can stack calls.
        self.assertEquals(self.mock_of_thing,
                          self.mock_of_thing.bar.expect().returns(3).method.mock)
        self.mock_of_thing.bar()


class GotOneCallTooMany(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect()
        self.mock_of_thing.baz.expect()

        self.mock_of_thing.baz()
        self.mock_of_thing.baz()

        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz)


class ExpectWrongArguments(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect(3, 'foo')

        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          3, 'fooo')
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          'foo', 3)

        self.mock_of_thing.baz(3, 'foo')


class ExpectHamcrest(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect(matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(matches(hamcrest.less_than(3)))

        self.mock_of_thing.baz(0)
        self.mock_of_thing.baz(1)
        self.mock_of_thing.baz(2)
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          3)
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          4)

        self.mock_of_thing.baz(-1)


class ArgMatcher(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect(
            _args_matcher=matches(hamcrest.has_item('hi!'))
        ).times(3)

        self.mock_of_thing.baz('hi!', 1, 2, 3)
        self.mock_of_thing.baz(1, 2, 'hi!', 3, 4)

        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          1, 2, 3, 4)

        self.mock_of_thing.baz('hi!', 'hi!')

        # All expectations retired
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          'hi!')


class ExpectHamcrestKW(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect(oneval=matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(oneval=matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(oneval=matches(hamcrest.less_than(3)))
        self.mock_of_thing.baz.expect(oneval=matches(hamcrest.less_than(3)))

        self.mock_of_thing.baz(oneval=0)
        self.mock_of_thing.baz(oneval=1)
        self.mock_of_thing.baz(oneval=2)
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          oneval=3)
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          4)

        self.mock_of_thing.baz(oneval=-1)

class ExpectWrongKWArguments(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect(one=3, two='foo')
        
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          one=3, two='fooo')
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          one='foo', two=3)

        self.mock_of_thing.baz(one=3, two='foo')


class ForceReturnValues(Validate):

    def runTest(self):
        self.mock_of_thing.baz.expect().returns(None)
        self.mock_of_thing.baz.expect().returns(432)
        self.mock_of_thing.baz.expect().returns('foobarbaz')
        self.mock_of_thing.baz.expect()

        self.assertEquals(None, self.mock_of_thing.baz())
        self.assertEquals(432, self.mock_of_thing.baz())
        self.assertEquals('foobarbaz', self.mock_of_thing.baz())
        self.assertEquals(None, self.mock_of_thing.baz())


class ExpectRaises(Validate):

    def runTest(self):
        class GoGoGadgetExceptions(Exception): pass

        self.mock_of_thing.bar.expect().returns('w00t')
        self.mock_of_thing.bar.expect().raises(GoGoGadgetExceptions)

        self.assertEquals('w00t', self.mock_of_thing.bar())
        self.assertRaises(GoGoGadgetExceptions, self.mock_of_thing.bar)


class Times(Validate):

    def runTest(self):
        num_times = 27
        self.mock_of_thing.bar.expect().times(num_times)

        for x in range(num_times):
            self.mock_of_thing.bar()

        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar)


class UntilSumsTo(Validate):

    def runTest(self):
        self.mock_of_thing.bar.expect(1).until_sums_to(10)
        self.mock_of_thing.bar.expect(10).until_sums_to(200)

        for x in range(10):
            self.mock_of_thing.bar(1)
            self.mock_of_thing.bar(10)

        for x in range(10):
            self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
            self.mock_of_thing.bar(10)

        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 10)

class InfiniteTimes(Validate):

    def runTest(self):
        self.mock_of_thing.bar.expect().infinite_times()

        num_times = 500
        for x in range(num_times):
            self.mock_of_thing.bar()


class SingleSequence(Validate):

    def runTest(self):
        s = Sequence()
        self.mock_of_thing.bar.expect(1).in_sequence(s)
        self.mock_of_thing.bar.expect(2).in_sequence(s)

        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 2)

        self.mock_of_thing.bar(1)
        self.mock_of_thing.bar(2)


class SequenceOverlap(Validate):

    def runTest(self):
        s1 = Sequence()
        s2 = Sequence()
        self.mock_of_thing.bar.expect(1).in_sequence(s1)
        self.mock_of_thing.bar.expect(2).in_sequence(s1)
        self.mock_of_thing.bar.expect(3).in_sequence(s1).in_sequence(s2)

        # Should retire s2, since its only expectation is retired by this
        self.mock_of_thing.bar(3)

        # Now we shouldn't be able to call 3, since that's been retired, but we
        # should be able to call 1 and 2 since those are in the first sequence.
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 3)
        self.mock_of_thing.bar(1)
        self.mock_of_thing.bar(2)

        # Now all expectations should be retired.
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 2)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 3)


class MultipleMockObjectsInSequence(Validate):

    def runTest(self):
        s1 = Sequence()

        self.mock_of_thing.bar.expect(1).in_sequence(s1)
        self.mock_of_thing.baz.expect(1).in_sequence(s1)
        self.other_mock_of_thing.bar.expect(1).in_sequence(s1)
        self.mock_of_other_thing.foo.expect(1).in_sequence(s1)

        # Only the first expectation in the sequence should be allowed.
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.baz, 1)
        self.assertRaises(UnexpectedMethodCall, self.other_mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_other_thing.foo, 1)

        # Retire the first expectation by meeting it, then test that only the
        # second one is allowed.
        self.mock_of_thing.bar(1)

        # Now, only the second expectation in the sequence should be allowed.
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.other_mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_other_thing.foo, 1)

        # Retire the second by meeting it.
        self.mock_of_thing.baz(1)

        # Now, only the third expectation should be allowed
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.baz, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_other_thing.foo, 1)
        
        # Retire the third
        self.other_mock_of_thing.bar(1)

        # Now, only the last should be allowed
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.bar, 1)
        self.assertRaises(UnexpectedMethodCall, self.mock_of_thing.baz, 1)
        self.assertRaises(UnexpectedMethodCall, self.other_mock_of_thing.bar, 1)
        
        self.mock_of_other_thing.foo(1)


class TestMethodSelector(unittest.TestCase):

    def setUp(self):
        default_context.retire_all_expectations()

    def runTest(self):
        def method_selector(cls, method_name):
            if method_name == 'bar':
                return True
            else:
                return False

        m = Mock(ThingToMock, _method_selector=method_selector)
        m.bar.expect(1)

        self.assert_(not hasattr(m, 'baz'))
        m.bar(1)

    def tearDown(self):
        default_context.assert_no_more_expectations()


class MultipleMethods(Validate):

    def runTest(self):
        self.mock_of_thing.bar.expect('barexpect1', two=1).returns('return one')
        self.mock_of_thing.bar.expect('barexpect2', two=2).returns('return two')
        self.mock_of_thing.baz.expect('bazexpect1', two=3).returns('return three')
        self.mock_of_thing.baz.expect('bazexpect2', two=4).returns('return four')

        self.assertEquals('return one', self.mock_of_thing.bar('barexpect1', two=1))
        self.assertEquals('return three', self.mock_of_thing.baz('bazexpect1', two=3))

        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.bar,
                          'wrongargument', two=2)
        self.assertRaises(UnexpectedMethodCall,
                          self.mock_of_thing.baz,
                          'bazexpect2', two=1)

        self.assertEquals('return two', self.mock_of_thing.bar('barexpect2', two=2))
        self.assertEquals('return four', self.mock_of_thing.baz('bazexpect2', two=4))


class SumTest(unittest.TestCase):

    expected = ((), {})
    calls = [
        ((), {})
    ]
    failed_calls = []

    def runTest(self):
        exp_args, exp_kwargs = self.expected
        s = Sum(exp_args, exp_kwargs)

        for call_args, call_kwargs in self.calls:
            self.assertFalse(s)
            s.add(call_args, call_kwargs)

        for call_args, call_kwargs in self.failed_calls:
            self.assertRaises(UnequalSumArguments, s.add, call_args,
                              call_kwargs)

        self.assert_(s)


class ArgNumbers(SumTest):

    expected = ((23, 42), {})
    calls = [
        ((10, 2), {}),
        ((10, 40), {}),
        ((3, 0), {}),
    ]


class ArgStrings(SumTest):

    expected = (('testing', 'this'), {})
    calls = [
        (('tes', ''), {}),
        (('ti', 'thi'), {}),
        (('ng', ''), {}),
        (('', ''), {}),
        (('', 's'), {}),
    ]


class BothArgs(SumTest):

    expected = (
        ('argstring', 10), {'kwargstring': 'testvalue', 'kwargnumber': 50}
    )

    calls = [
        (('', 5), {'kwargstring': 'test', 'kwargnumber': 40}),
        (('a', 5), {'kwargstring': '', 'kwargnumber': 1}),
        (('r', 0), {'kwargstring': '', 'kwargnumber': 1}),
        (('gstrin', 0), {'kwargstring': 'value', 'kwargnumber': 1}),
        (('g', 0), {'kwargstring': '', 'kwargnumber': 7}),
    ]

    failed_calls = [
        # Wrong number of args
        (('one', 2, 3), {'kwargstring': 'whatever', 'kwargnumber': 20}),

        # Wrong key values in kwargs
        (('one', 2,), {'kwargstring!': 'whatever', 'kwargnumber': 20}),

        # Wrong number of key values in kwargs
        (('one', 2,), {'kwargstring': 'whatever', 'kwargnumber': 20,
                       'newcrazyarg': 1}),
    ] 

if __name__ == '__main__':
    unittest.main()    
