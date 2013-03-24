from unittest import TestCase
from ScrapeTree import \
    ScrapeNode, ScrapeSequence, ScrapeRegex, ScrapeCollection, \
    ScrapeAlternative, ScrapeMultiline, ScrapeKeyValueSequence


class ScrapeNodeMock(ScrapeNode):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def starts_with_this_line(self, line):
        return line == self.value

    def scrape(self, line, doc):
        if(line == self.value):
            doc[self.key] = self.value
            return True
        else:
            return False


class ScrapeRegexTestCase(TestCase):

    def setUp(self):
        self.node = ScrapeRegex('a(?P<number>[0-9]+)-(?P<word>[A-Z]+)z')
        self.basic = ScrapeRegex('toto')

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line(
            'hello a12548-FOOz world'
        ))
        self.assertTrue(self.basic.starts_with_this_line('AtotoB'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line(
            'hello a12548-F#Oz world'
        ))
        self.assertFalse(self.basic.starts_with_this_line('AtotB'))

    def test_scrape_ok(self):
        doc = {}
        self.assertTrue(self.basic.scrape('AtotoB', doc))
        self.assertEqual({}, doc)
        self.assertTrue(self.node.scrape('hello a12548-FOOz world', doc))
        self.assertEqual({'number': '12548', 'word': 'FOO'}, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.basic.scrape('AtotB', doc))
        self.assertEqual({}, doc)
        self.assertFalse(self.node.scrape('hello a12548-F#Oz world', doc))
        self.assertEqual({}, doc)


class ScrapeSequenceTestCase(TestCase):

    def setUp(self):
        self.first = ScrapeNodeMock('val0', 'tata')
        self.secnd = ScrapeNodeMock('val1', 'titi')
        self.third = ScrapeNodeMock('val2', 'tutu')
        self.fourth = ScrapeNodeMock('val3', 'tty')
        self.node = ScrapeSequence([
            (self.first, True),
            (self.secnd, False),
            (self.third, True),
            (self.fourth, False)
        ])

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line('tata'))
        self.assertTrue(self.node.starts_with_this_line('titi'))
        self.assertFalse(self.node.starts_with_this_line('tutu'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line('tutu'))
        self.assertFalse(self.node.starts_with_this_line('tita'))

    def test_scrape_ok(self):
        doc = {}
        self.assertFalse(self.node.scrape('tata', doc))
        self.assertFalse(self.node.scrape('titi', doc))
        self.assertFalse(self.node.scrape('tutu', doc))
        self.assertTrue(
            self.node.scrape('tty', doc),
            'doc : {0}'.format(doc.items())
        )
        self.assertEqual({
            'val0': 'tata',
            'val1': 'titi',
            'val2': 'tutu',
            'val3': 'tty'
        }, doc)

        doc = {}
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertFalse(self.node.scrape('titi', doc))
        self.assertFalse(self.node.scrape('tata', doc))
        self.assertFalse(self.node.scrape('tita', doc))
        self.assertTrue(self.node.scrape('tty', doc))
        self.assertEqual({'val1': 'titi', 'val3': 'tty'}, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertFalse(self.node.scrape('titi', doc))
        self.assertFalse(self.node.scrape('tata', doc))
        self.assertFalse(self.node.scrape('tutu', doc))


class ScrapeAlternativeTestCase(TestCase):

    def setUp(self):
        self.first = ScrapeNodeMock('val0', 'tata')
        self.secnd = ScrapeNodeMock('val1', 'titi')
        self.node = ScrapeAlternative([self.first, self.secnd])

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line('tata'))
        self.assertTrue(self.node.starts_with_this_line('titi'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line('tati'))
        self.assertFalse(self.node.starts_with_this_line(''))

    def test_scrape_ok(self):
        doc = {}
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertTrue(self.node.scrape('tata', doc))
        self.assertEqual({'val0': 'tata'}, doc)
        doc = {}
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertTrue(self.node.scrape('titi', doc))
        self.assertEqual({'val1': 'titi'}, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertEqual({}, doc)


class ScrapeMultilineTestCase(TestCase):

    def setUp(self):
        self.node = ScrapeMultiline('key', '([A-C]+)', '(DEF)')

    def test_init_nok(self):
        with self.assertRaises(RuntimeError):
            ScrapeMultiline('key', '[A-C]+', '(DEF)')
            ScrapeMultiline('key', '([A-C]+)', 'DEF')

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line('lkjqsf ABC sdfsdf'))
        self.assertTrue(self.node.starts_with_this_line('lkABC sdfsdfDEF jhg'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line('DEF'))
        self.assertFalse(self.node.starts_with_this_line(''))

    def test_scrape_ok(self):
        parts = [' And now,', ' something completly', ' different !']
        doc = {}
        self.assertFalse(self.node.scrape('lkjqsf ABC' + parts[0], doc))
        self.assertFalse(self.node.scrape(parts[1], doc))
        self.assertTrue(self.node.scrape(parts[2] + 'DEF lkdqjsflq', doc))
        self.assertEqual({'key': parts}, doc)

        simple = 'que? what?'
        self.assertTrue(self.node.scrape('ABC' + simple + 'DEFfoo', doc))
        self.assertEqual({'key': [simple]}, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.node.scrape('DEFque?ABCwhat?', doc))


class ScrapeKeyValueSequenceTestCase(TestCase):

    def setUp(self):
        self.node = ScrapeKeyValueSequence('k', 'v', [
            ScrapeNodeMock('k', 'a_key'),
            ScrapeNodeMock('v', 'a_value')
        ])

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line('a_key'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line('a_value'))
        self.assertFalse(self.node.starts_with_this_line('a_foo'))

    def test_scrape_ok(self):
        doc = {}
        self.assertFalse(self.node.scrape('foo', doc))
        self.assertFalse(self.node.scrape('a_key', doc))
        self.assertFalse(self.node.scrape('foo', doc))
        self.assertTrue(self.node.scrape('a_value', doc))
        self.assertEqual({'a_key': 'a_value'}, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.node.scrape('a_value', doc))
        self.assertFalse(self.node.scrape('a_key', doc))


class ScrapeCollectionTestCase(TestCase):

    def setUp(self):
        self.node = ScrapeCollection(
            'a',
            ScrapeNodeMock('val0', 'tata'),
            ScrapeNodeMock('val1', 'titi')
        )

    def test_starts_with_this_line_ok(self):
        self.assertTrue(self.node.starts_with_this_line('tata'))
        self.assertTrue(self.node.starts_with_this_line('titi'))

    def test_starts_with_this_line_nok(self):
        self.assertFalse(self.node.starts_with_this_line('foo'))

    def test_scrape_ok(self):
        doc = {}
        self.assertFalse(self.node.scrape('toto', doc))
        self.assertTrue(self.node.scrape('titi', doc))
        self.assertEqual({'a': [], 'val1': 'titi'}, doc)

        doc = {}
        self.assertFalse(self.node.scrape('tata', doc))
        self.assertFalse(self.node.scrape('toto', doc))
        self.assertFalse(self.node.scrape('tata', doc))
        self.assertTrue(self.node.scrape('titi', doc))
        self.assertEqual({
            'a': [{'val0':'tata'}, {'val0':'tata'}],
            'val1': 'titi'
        }, doc)

    def test_scrape_nok(self):
        doc = {}
        self.assertFalse(self.node.scrape('tita', doc))
        self.assertFalse(self.node.scrape('tati', doc))
        self.assertEqual({}, doc)
