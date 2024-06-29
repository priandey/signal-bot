def utf16_len(text):
    """
    Calculate the length of a Python string in UTF-16 code units.

    :param text: The original string.
    :return: The length of the string in UTF-16 code units.
    """
    utf16_length = 0

    for char in text:
        utf16_length += 1 if ord(char) < 65536 else 2

    return utf16_length
