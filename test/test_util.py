import unittest

from rcon.util import *

class DispatcherTest(unittest.TestCase):
    def test_fires_to_registered_handlers_once(self):
        dispatch = Dispatcher()
        called = 0

        @dispatch.register
        def func():
            nonlocal called
            called += 1

        dispatch.fire()
        self.assertEqual(called, 1)

    def test_fires_to_registered_handlers_with_args(self):
        dispatch = Dispatcher()
        callback_args = None
        callback_kwargs = None

        @dispatch.register
        def func(*args, **kwargs):
            nonlocal callback_args
            nonlocal callback_kwargs
            callback_args = args
            callback_kwargs = kwargs

        dispatch.fire(1, 2, 3, a=4, b=5)
        self.assertEqual(callback_args, (1, 2, 3))
        self.assertEqual(callback_kwargs, {'a': 4, 'b': 5})

    def test_doesnt_fire_unregistered_handlers(self):
        dispatch = Dispatcher()
        called = 0

        @dispatch.register
        def func():
            nonlocal called
            called += 1

        dispatch.unregister(func)
        dispatch.fire()
        self.assertEqual(called, 0)

    def test_unregister_in_fire(self):
        dispatch = Dispatcher()
        called = 0

        @dispatch.register
        def func():
            nonlocal called
            called += 1
            dispatch.unregister(func)

        dispatch.fire()
        dispatch.fire()
        self.assertEqual(called, 1)

class ParseTimestampTest(unittest.TestCase):
    def test_parses(self):
        message = b'11/20/2016 - 13:05:40: This has junk on the end'
        date, _ = parse_timestamp(message)

        self.assertEqual(date, datetime.datetime(2016, 11, 20, 13, 5, 40))

    def test_leaves_remainder(self):
        message = b'11/20/2016 - 13:05:40: This has junk on the end'
        _, rest = parse_timestamp(message)

        self.assertEqual(rest, b'This has junk on the end')

class ParsePlayerInfoTest(unittest.TestCase):
    def test_parses_unassigned_human(self):
        message = b'adamnew123456<2><[U:1:89408849]><Unassigned>'
        info = parse_player_info(message)

        self.assertEqual(info, (b'adamnew123456', b'2', b'[U:1:89408849]', b'Unassigned'))

    def test_parses_unassigned_bot(self):
        message = b'(BOT) Brad<4><BOT><Unassigned>'
        info = parse_player_info(message)

        self.assertEqual(info, (b'(BOT) Brad', b'4', b'BOT', b'Unassigned'))

    def test_parses_ct(self):
        message = b'(BOT) Brad<4><BOT><CT>'
        info = parse_player_info(message)

        self.assertEqual(info, (b'(BOT) Brad', b'4', b'BOT', b'CT'))

    def test_parses_terrorist(self):
        message = b'(BOT) Brad<4><BOT><TERRORIST>'
        info = parse_player_info(message)

        self.assertEqual(info, (b'(BOT) Brad', b'4', b'BOT', b'TERRORIST'))

    def test_parses_no_team(self):
        message = b'(BOT) Brad<4><BOT><>'
        info = parse_player_info(message)

        self.assertEqual(info, (b'(BOT) Brad', b'4', b'BOT', b''))

class GetQuotedStringsTest(unittest.TestCase):
    def test_no_qs(self):
        message = b'Nothing in here is quoted'
        qs = list(get_quoted_strings(message))
        self.assertEqual(qs, [])

    def test_a_qs(self):
        message = b'Something in here is "quoted"'
        qs = list(get_quoted_strings(message))
        self.assertEqual(qs, [b'quoted'])

    def test_many_qs(self):
        message = b'"Something" in here is "quoted"'
        qs = list(get_quoted_strings(message))
        self.assertEqual(qs, [b'Something', b'quoted'])

if __name__ == '__main__':
    unittest.main()
