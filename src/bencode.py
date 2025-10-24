"""
Bencode encoding/decoding module.

Bencode is the encoding used by the BitTorrent protocol for storing and transmitting
loosely structured data. It supports four types:
- Integers: encoded as i<integer>e (e.g., i42e = 42)
- Byte strings: encoded as <length>:<contents> (e.g., 4:spam)
- Lists: encoded as l<contents>e (e.g., li42e4:spame = [42, b'spam'])
- Dictionaries: encoded as d<contents>e with keys in sorted order

Reference: BEP 3 - The BitTorrent Protocol Specification
https://www.bittorrent.org/beps/bep_0003.html
"""

from typing import Union, List, Dict, Any


def encode(obj: Union[int, bytes, list, dict]) -> bytes:
    """
    Encode a Python object to bencode format.

    This function converts Python objects into bencode-encoded bytes. The BitTorrent
    protocol uses bencode for encoding dictionaries in .torrent files and DHT messages.

    Args:
        obj: The object to encode. Must be one of:
            - int: Encoded as i<number>e
            - bytes: Encoded as <length>:<string>
            - list: Encoded as l<elements>e (recursive)
            - dict: Encoded as d<key><value>...e (keys must be bytes, sorted)

    Returns:
        bytes: The bencode-encoded representation of the object.

    Raises:
        TypeError: If obj is not a supported type (int, bytes, list, dict).
        TypeError: If dict keys are not bytes.
        ValueError: If integer is too large to encode safely.

    Examples:
        >>> encode(42)
        b'i42e'
        >>> encode(b'spam')
        b'4:spam'
        >>> encode([1, 2, 3])
        b'li1ei2ei3ee'
        >>> encode({b'foo': b'bar'})
        b'd3:foo3:bare'

    Security Notes:
        - Validates input types to prevent injection attacks
        - Dict keys must be bytes to prevent encoding errors
        - Integer size is limited by Python's int implementation
    """
    # Integer encoding: i<number>e
    if isinstance(obj, int):
        # Validate integer size (prevent potential DoS with huge numbers)
        if abs(obj) > 10**100:  # Reasonable limit for DHT protocol
            raise ValueError(f"Integer too large to encode safely: {obj}")
        return b'i' + str(obj).encode('ascii') + b'e'

    # Byte string encoding: <length>:<contents>
    elif isinstance(obj, bytes):
        return str(len(obj)).encode('ascii') + b':' + obj

    # List encoding: l<elements>e
    elif isinstance(obj, list):
        result = b'l'
        for item in obj:
            result += encode(item)  # Recursive encoding
        result += b'e'
        return result

    # Dictionary encoding: d<key><value>...e
    # Keys must be sorted in lexicographic order (BitTorrent spec requirement)
    elif isinstance(obj, dict):
        result = b'd'
        # Validate that all keys are bytes
        for key in obj.keys():
            if not isinstance(key, bytes):
                raise TypeError(f"Dictionary keys must be bytes, got {type(key)}")

        # Sort keys lexicographically as required by bencode spec
        sorted_keys = sorted(obj.keys())
        for key in sorted_keys:
            result += encode(key)  # Encode key
            result += encode(obj[key])  # Encode value (recursive)
        result += b'e'
        return result

    else:
        raise TypeError(f"Unsupported type for bencode: {type(obj)}")


def decode(data: bytes) -> tuple[Any, int]:
    """
    Decode bencode data to Python objects.

    This function parses bencode-encoded bytes and converts them back to Python objects.
    It returns both the decoded object and the number of bytes consumed, allowing for
    parsing of multiple bencode values in sequence.

    Args:
        data: The bencode-encoded bytes to decode.

    Returns:
        tuple: A tuple containing:
            - decoded object (int, bytes, list, or dict)
            - number of bytes consumed from input

    Raises:
        ValueError: If data is malformed or contains invalid bencode.
        ValueError: If data is truncated or incomplete.
        IndexError: If data ends unexpectedly.

    Examples:
        >>> decode(b'i42e')
        (42, 4)
        >>> decode(b'4:spam')
        (b'spam', 6)
        >>> decode(b'li1ei2ee')
        ([1, 2], 8)
        >>> decode(b'd3:foo3:bare')
        ({b'foo': b'bar'}, 13)

    Security Notes:
        - Validates all input to prevent malformed data attacks
        - Limits recursion depth implicitly through Python's stack
        - Validates string lengths to prevent buffer overruns
        - Handles malicious/truncated data gracefully
    """
    if not data:
        raise ValueError("Cannot decode empty data")

    # Integer decoding: i<number>e
    if data[0:1] == b'i':
        try:
            # Find the terminating 'e'
            end_index = data.index(b'e', 1)
        except ValueError:
            raise ValueError("Invalid integer: missing terminator 'e'")

        # Extract and parse the number
        number_bytes = data[1:end_index]
        if not number_bytes:
            raise ValueError("Invalid integer: empty value")

        # Validate format (no leading zeros except for '0' itself)
        if number_bytes[0:1] == b'0' and len(number_bytes) > 1:
            raise ValueError("Invalid integer: leading zeros not allowed")
        if number_bytes[0:1] == b'-' and number_bytes[1:2] == b'0':
            raise ValueError("Invalid integer: negative zero not allowed")

        try:
            number = int(number_bytes)
        except ValueError:
            raise ValueError(f"Invalid integer format: {number_bytes}")

        return number, end_index + 1

    # Byte string decoding: <length>:<contents>
    elif data[0:1].isdigit():
        try:
            # Find the colon separator
            colon_index = data.index(b':', 0)
        except ValueError:
            raise ValueError("Invalid byte string: missing colon separator")

        # Extract and parse the length
        length_bytes = data[0:colon_index]
        if not length_bytes:
            raise ValueError("Invalid byte string: empty length")

        # Validate no leading zeros (except '0' itself)
        if length_bytes[0:1] == b'0' and len(length_bytes) > 1:
            raise ValueError("Invalid byte string: leading zeros in length")

        try:
            length = int(length_bytes)
        except ValueError:
            raise ValueError(f"Invalid byte string length: {length_bytes}")

        if length < 0:
            raise ValueError(f"Invalid byte string: negative length {length}")

        # Validate we have enough data
        start_index = colon_index + 1
        end_index = start_index + length
        if len(data) < end_index:
            raise ValueError(f"Invalid byte string: truncated data (need {length} bytes, got {len(data) - start_index})")

        # Extract the byte string
        byte_string = data[start_index:end_index]
        return byte_string, end_index

    # List decoding: l<elements>e
    elif data[0:1] == b'l':
        result = []
        index = 1  # Skip the 'l'

        while index < len(data):
            # Check for list terminator
            if data[index:index+1] == b'e':
                return result, index + 1

            # Decode next element
            try:
                element, consumed = decode(data[index:])
                result.append(element)
                index += consumed
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid list element at position {index}: {e}")

        # If we get here, list was not terminated
        raise ValueError("Invalid list: missing terminator 'e'")

    # Dictionary decoding: d<key><value>...e
    elif data[0:1] == b'd':
        result = {}
        index = 1  # Skip the 'd'

        while index < len(data):
            # Check for dict terminator
            if data[index:index+1] == b'e':
                return result, index + 1

            # Decode key (must be a byte string)
            try:
                key, consumed = decode(data[index:])
                if not isinstance(key, bytes):
                    raise ValueError(f"Dictionary key must be byte string, got {type(key)}")
                index += consumed
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid dictionary key at position {index}: {e}")

            # Decode value
            if index >= len(data):
                raise ValueError("Invalid dictionary: missing value for key")

            try:
                value, consumed = decode(data[index:])
                result[key] = value
                index += consumed
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid dictionary value at position {index}: {e}")

        # If we get here, dict was not terminated
        raise ValueError("Invalid dictionary: missing terminator 'e'")

    else:
        raise ValueError(f"Invalid bencode: unexpected byte {data[0]}")
