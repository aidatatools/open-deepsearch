import unittest
from .text_splitter import RecursiveCharacterTextSplitter

class TestRecursiveCharacterTextSplitter(unittest.TestCase):
    def setUp(self):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)

    def test_split_text_by_separators(self):
        text = 'Hello world, this is a test of the recursive text splitter.'

        self.assertEqual(
            self.splitter.split_text(text),
            ['Hello world', 'this is a test of the recursive text splitter']
        )

        self.splitter.chunk_size = 100
        self.assertEqual(
            self.splitter.split_text(
                'Hello world, this is a test of the recursive text splitter. If I have a period, it should split along the period.'
            ),
            [
                'Hello world, this is a test of the recursive text splitter',
                'If I have a period, it should split along the period.'
            ]
        )

        self.splitter.chunk_size = 110
        self.assertEqual(
            self.splitter.split_text(
                'Hello world, this is a test of the recursive text splitter. If I have a period, it should split along the period.\nOr, if there is a new line, it should prioritize splitting on new lines instead.'
            ),
            [
                'Hello world, this is a test of the recursive text splitter',
                'If I have a period, it should split along the period.',
                'Or, if there is a new line, it should prioritize splitting on new lines instead.'
            ]
        )

    def test_handle_empty_string(self):
        self.assertEqual(self.splitter.split_text(''), [])

    def test_handle_special_characters_and_large_texts(self):
        large_text = 'A' * 1000
        self.splitter.chunk_size = 200
        self.assertEqual(
            self.splitter.split_text(large_text),
            ['A' * 200] * 5
        )

        special_char_text = 'Hello!@# world$%^ &*( this) is+ a-test'
        self.assertEqual(
            self.splitter.split_text(special_char_text),
            ['Hello!@#', 'world$%^', '&*( this)', 'is+', 'a-test']
        )

    def test_handle_chunk_size_equal_to_chunk_overlap(self):
        self.splitter.chunk_size = 50
        self.splitter.chunk_overlap = 50
        with self.assertRaises(ValueError):
            self.splitter.split_text('Invalid configuration')

if __name__ == '__main__':
    unittest.main()