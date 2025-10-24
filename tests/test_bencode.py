"""
Unit tests for bencode encoding/decoding module.

This test suite validates the bencode implementation against the BitTorrent
specification (BEP 3) and includes security/edge case testing.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bencode import encode, decode


class TestBencodeEncode(unittest.TestCase):
    """Test cases for bencode encoding (encode function)."""

    def test_encode_integer_positive(self):
        """Test encoding positive integers."""
        self.assertEqual(encode(0), b'i0e')
        self.assertEqual(encode(42), b'i42e')
        self.assertEqual(encode(123456), b'i123456e')

    def test_encode_integer_negative(self):
        """Test encoding negative integers."""
        self.assertEqual(encode(-1), b'i-1e')
        self.assertEqual(encode(-42), b'i-42e')
        self.assertEqual(encode(-123456), b'i-123456e')

    def test_encode_integer_too_large(self):
        """Test that extremely large integers raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            encode(10**101)
        self.assertIn("too large", str(ctx.exception).lower())

    def test_encode_bytes_empty(self):
        """Test encoding empty byte string."""
        self.assertEqual(encode(b''), b'0:')

    def test_encode_bytes_normal(self):
        """Test encoding normal byte strings."""
        self.assertEqual(encode(b'spam'), b'4:spam')
        self.assertEqual(encode(b'hello world'), b'11:hello world')
        self.assertEqual(encode(b'test123'), b'7:test123')

    def test_encode_bytes_binary(self):
        """Test encoding binary data (non-ASCII bytes)."""
        self.assertEqual(encode(b'\x00\x01\x02'), b'3:\x00\x01\x02')
        self.assertEqual(encode(b'\xff\xfe'), b'2:\xff\xfe')

    def test_encode_list_empty(self):
        """Test encoding empty list."""
        self.assertEqual(encode([]), b'le')

    def test_encode_list_integers(self):
        """Test encoding list of integers."""
        self.assertEqual(encode([1, 2, 3]), b'li1ei2ei3ee')
        self.assertEqual(encode([0, -1, 100]), b'li0ei-1ei100ee')

    def test_encode_list_mixed(self):
        """Test encoding list with mixed types."""
        self.assertEqual(encode([1, b'spam', [2, 3]]), b'li1e4:spamli2ei3eee')

    def test_encode_list_nested(self):
        """Test encoding nested lists."""
        self.assertEqual(encode([[]]), b'llee')
        self.assertEqual(encode([[1], [2, 3]]), b'lli1eeli2ei3eee')

    def test_encode_dict_empty(self):
        """Test encoding empty dictionary."""
        self.assertEqual(encode({}), b'de')

    def test_encode_dict_simple(self):
        """Test encoding simple dictionary."""
        self.assertEqual(encode({b'foo': b'bar'}), b'd3:foo3:bare')
        self.assertEqual(encode({b'key': 42}), b'd3:keyi42ee')

    def test_encode_dict_sorted_keys(self):
        """Test that dictionary keys are sorted lexicographically."""
        # Keys should be sorted: 'bar' < 'foo'
        result = encode({b'foo': 1, b'bar': 2})
        self.assertEqual(result, b'd3:bari2e3:fooi1ee')

    def test_encode_dict_nested(self):
        """Test encoding nested dictionaries."""
        nested = {b'outer': {b'inner': b'value'}}
        self.assertEqual(encode(nested), b'd5:outerd5:inner5:valueee')

    def test_encode_dict_non_bytes_keys(self):
        """Test that dict with non-bytes keys raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            encode({'string_key': b'value'})
        self.assertIn("bytes", str(ctx.exception).lower())

        with self.assertRaises(TypeError):
            encode({42: b'value'})

    def test_encode_unsupported_type(self):
        """Test that unsupported types raise TypeError."""
        with self.assertRaises(TypeError) as ctx:
            encode("string")  # str not supported, only bytes
        self.assertIn("unsupported", str(ctx.exception).lower())

        with self.assertRaises(TypeError):
            encode(3.14)  # float not supported

        with self.assertRaises(TypeError):
            encode(None)  # None not supported

    def test_encode_complex_structure(self):
        """Test encoding complex nested structure."""
        data = {
            b'dict': {b'nested': b'value'},
            b'list': [1, 2, [3, 4]],
            b'int': 42,
            b'bytes': b'test'
        }
        # Keys sorted: bytes < dict < int < list
        expected = b'd5:bytes4:test4:dictd6:nested5:valuee3:inti42e4:listli1ei2eli3ei4eeee'
        self.assertEqual(encode(data), expected)


class TestBencodeDecode(unittest.TestCase):
    """Test cases for bencode decoding (decode function)."""

    def test_decode_integer_positive(self):
        """Test decoding positive integers."""
        self.assertEqual(decode(b'i0e'), (0, 3))
        self.assertEqual(decode(b'i42e'), (42, 4))
        self.assertEqual(decode(b'i123456e'), (123456, 8))

    def test_decode_integer_negative(self):
        """Test decoding negative integers."""
        self.assertEqual(decode(b'i-1e'), (-1, 4))
        self.assertEqual(decode(b'i-42e'), (-42, 5))
        self.assertEqual(decode(b'i-123456e'), (-123456, 9))

    def test_decode_integer_invalid_format(self):
        """Test that invalid integer formats raise ValueError."""
        # Missing terminator
        with self.assertRaises(ValueError) as ctx:
            decode(b'i42')
        self.assertIn("terminator", str(ctx.exception).lower())

        # Empty value
        with self.assertRaises(ValueError):
            decode(b'ie')

        # Invalid characters
        with self.assertRaises(ValueError):
            decode(b'i42ae')

    def test_decode_integer_leading_zeros(self):
        """Test that leading zeros are rejected."""
        with self.assertRaises(ValueError) as ctx:
            decode(b'i042e')
        self.assertIn("leading zero", str(ctx.exception).lower())

        # Negative zero
        with self.assertRaises(ValueError) as ctx:
            decode(b'i-0e')
        self.assertIn("negative zero", str(ctx.exception).lower())

    def test_decode_bytes_empty(self):
        """Test decoding empty byte string."""
        self.assertEqual(decode(b'0:'), (b'', 2))

    def test_decode_bytes_normal(self):
        """Test decoding normal byte strings."""
        self.assertEqual(decode(b'4:spam'), (b'spam', 6))
        self.assertEqual(decode(b'11:hello world'), (b'hello world', 14))

    def test_decode_bytes_binary(self):
        """Test decoding binary data."""
        self.assertEqual(decode(b'3:\x00\x01\x02'), (b'\x00\x01\x02', 5))

    def test_decode_bytes_invalid_format(self):
        """Test that invalid byte string formats raise ValueError."""
        # Missing colon
        with self.assertRaises(ValueError) as ctx:
            decode(b'4spam')
        self.assertIn("colon", str(ctx.exception).lower())

        # Truncated data
        with self.assertRaises(ValueError) as ctx:
            decode(b'10:short')
        self.assertIn("truncated", str(ctx.exception).lower())

        # Negative length
        with self.assertRaises(ValueError):
            decode(b'-5:test')

        # Leading zeros in length
        with self.assertRaises(ValueError) as ctx:
            decode(b'04:spam')
        self.assertIn("leading zero", str(ctx.exception).lower())

    def test_decode_list_empty(self):
        """Test decoding empty list."""
        self.assertEqual(decode(b'le'), ([], 2))

    def test_decode_list_integers(self):
        """Test decoding list of integers."""
        self.assertEqual(decode(b'li1ei2ei3ee'), ([1, 2, 3], 11))

    def test_decode_list_mixed(self):
        """Test decoding list with mixed types."""
        result, length = decode(b'li1e4:spamli2ei3eee')
        self.assertEqual(result, [1, b'spam', [2, 3]])
        self.assertEqual(length, 19)

    def test_decode_list_nested(self):
        """Test decoding nested lists."""
        self.assertEqual(decode(b'llee'), ([[]], 4))
        self.assertEqual(decode(b'lli1eeli2ei3eee'), ([[1], [2, 3]], 15))

    def test_decode_list_invalid_format(self):
        """Test that invalid list formats raise ValueError."""
        # Missing terminator
        with self.assertRaises(ValueError) as ctx:
            decode(b'li1ei2e')
        self.assertIn("terminator", str(ctx.exception).lower())

        # Invalid element
        with self.assertRaises(ValueError):
            decode(b'li1eXe')

    def test_decode_dict_empty(self):
        """Test decoding empty dictionary."""
        self.assertEqual(decode(b'de'), ({}, 2))

    def test_decode_dict_simple(self):
        """Test decoding simple dictionary."""
        self.assertEqual(decode(b'd3:foo3:bare'), ({b'foo': b'bar'}, 12))
        self.assertEqual(decode(b'd3:keyi42ee'), ({b'key': 42}, 11))

    def test_decode_dict_multiple_keys(self):
        """Test decoding dictionary with multiple keys."""
        result, length = decode(b'd3:bari2e3:fooi1ee')
        self.assertEqual(result, {b'bar': 2, b'foo': 1})
        self.assertEqual(length, 18)

    def test_decode_dict_nested(self):
        """Test decoding nested dictionaries."""
        result, length = decode(b'd5:outerd5:inner5:valueee')
        self.assertEqual(result, {b'outer': {b'inner': b'value'}})

    def test_decode_dict_invalid_format(self):
        """Test that invalid dict formats raise ValueError."""
        # Missing terminator
        with self.assertRaises(ValueError) as ctx:
            decode(b'd3:foo3:bar')
        self.assertIn("terminator", str(ctx.exception).lower())

        # Missing value (ends with 'e' after key)
        with self.assertRaises(ValueError):
            decode(b'd3:fooe')

        # Non-string key
        with self.assertRaises(ValueError) as ctx:
            decode(b'di42e3:bare')
        self.assertIn("key must be byte string", str(ctx.exception).lower())

    def test_decode_empty_data(self):
        """Test that empty data raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            decode(b'')
        self.assertIn("empty", str(ctx.exception).lower())

    def test_decode_invalid_start_byte(self):
        """Test that invalid start bytes raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            decode(b'X')
        self.assertIn("unexpected byte", str(ctx.exception).lower())

    def test_decode_complex_structure(self):
        """Test decoding complex nested structure."""
        data = b'd5:bytes4:test4:dictd6:nested5:valuee3:inti42e4:listli1ei2eli3ei4eeee'
        result, length = decode(data)

        expected = {
            b'bytes': b'test',
            b'dict': {b'nested': b'value'},
            b'int': 42,
            b'list': [1, 2, [3, 4]]
        }
        self.assertEqual(result, expected)
        self.assertEqual(length, len(data))

    def test_decode_trailing_data(self):
        """Test that decode only consumes necessary bytes."""
        # Decode should only consume the first bencode value
        result, consumed = decode(b'i42eEXTRA')
        self.assertEqual(result, 42)
        self.assertEqual(consumed, 4)  # Only consumed 'i42e'


class TestBencodeRoundTrip(unittest.TestCase):
    """Test that encode/decode are inverses of each other."""

    def test_roundtrip_integer(self):
        """Test integer roundtrip."""
        values = [0, 1, -1, 42, -42, 123456, -123456]
        for val in values:
            encoded = encode(val)
            decoded, _ = decode(encoded)
            self.assertEqual(decoded, val)

    def test_roundtrip_bytes(self):
        """Test byte string roundtrip."""
        values = [b'', b'spam', b'hello world', b'\x00\x01\x02\xff\xfe']
        for val in values:
            encoded = encode(val)
            decoded, _ = decode(encoded)
            self.assertEqual(decoded, val)

    def test_roundtrip_list(self):
        """Test list roundtrip."""
        values = [
            [],
            [1, 2, 3],
            [b'spam', b'eggs'],
            [[1], [2, 3]],
            [1, b'test', [2, b'nested']]
        ]
        for val in values:
            encoded = encode(val)
            decoded, _ = decode(encoded)
            self.assertEqual(decoded, val)

    def test_roundtrip_dict(self):
        """Test dictionary roundtrip."""
        values = [
            {},
            {b'foo': b'bar'},
            {b'a': 1, b'b': 2},
            {b'nested': {b'key': b'value'}},
            {b'mixed': [1, 2, {b'inner': b'dict'}]}
        ]
        for val in values:
            encoded = encode(val)
            decoded, _ = decode(encoded)
            self.assertEqual(decoded, val)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
