import re


def is_comment(line: str) -> bool:
    """
    Determines if a given line is a Markdown comment.
    Markdown comments are in the format <!-- comment -->

    :param line: The line to check
    :return: True if the line is a comment, False otherwise
    """
    return bool(re.match(r"^\s*<!--.*-->\s*$", line))


def get_header_level(line: str) -> int:
    """
    Determines the header level of a given line.

    :param line: The line to check
    :return: The header level (1-6) if it's a header, 0 otherwise
    """
    match = re.match(r"^(#{1,6})\s", line)
    if match:
        return len(match.group(1))
    else:
        return 0


def is_empty(line: str) -> bool:
    """
    Determines if a given line is an empty line in markdown.
    A line is empty if it is blank or comment only

    :param line: The line to check
    :return: True if the line is empty, False otherwise
    """
    return is_comment(line) or line.strip() == ""


def is_divider(line: str) -> bool:
    """
    Determines if a given line is a Markdown divider (horizontal rule).
    Markdown dividers are three or more hyphens, asterisks, or underscores,
    without any other characters except spaces.

    :param line: The line to check
    :return: True if the line is a divider, False otherwise
    """
    stripped_line = line.strip()
    if len(stripped_line) < 3:
        return False
    return all(char in "-*_" for char in stripped_line) and any(
        char * 3 in stripped_line for char in "-*_"
    )


def contains_image(line: str) -> bool:
    """
    Determines if a given line contains a Markdown image.
    Markdown images are in the format ![alt text](image_url)

    :param line: The line to check
    :return: True if the line contains an image, False otherwise
    """
    return bool(re.search(r"!\[.*?\]\(.*?\)", line))


def contains_deco(line: str) -> bool:
    """
    Determines if a given line contains a deco (custom decorator).
    Decos are in the format @(key1=value1, key2=value2, ...)

    :param line: The line to check
    :return: True if the line contains a deco, False otherwise
    """
    return bool(re.match(r"^\s*@\(.*?\)\s*$", line))


# Test functions
if __name__ == "__main__":
    print("Test is_comment")
    print(is_comment("<!-- This is a comment -->"))  # Should return True
    print(is_comment("This is not a comment"))  # Should return False

    print("Test is_empty")
    print(is_empty("<!-- This is a comment -->"))  # Should return True
    print(is_empty("This is not a comment"))  # Should return False
    print(is_empty(" \n"))  # Should return True

    print("Test get_header_level")
    print(get_header_level("# Header 1"))  # Should return 1
    print(get_header_level("### Header 3"))  # Should return 3
    print(get_header_level("Normal text"))  # Should return 0
    print(get_header_level("####### Not a valid header"))  # Should return 0

    print("Test is_divider")
    print(is_divider("---"))  # Should return True
    print(is_divider("***"))  # Should return True
    print(is_divider("___"))  # Should return True
    print(is_divider("  ----  "))  # Should return True
    print(is_divider("--"))  # Should return False
    print(is_divider("- - -"))  # Should return False
    print(is_divider("This is not a divider"))  # Should return False

    print("Test contains_image")
    print(contains_image("![Alt text](image.jpg)"))  # Should return True
    print(
        contains_image("This is an image: ![Alt text](image.jpg)")
    )  # Should return True
    print(contains_image("This is not an image"))  # Should return False
    print(contains_image("![](image.jpg)"))  # Should return True (empty alt text)
    print(contains_image("![]()"))  # Should return True (empty alt text and URL)

    print("Test contains_deco")
    print(contains_deco("@(layout=split, background=blue)"))  # Should return True
    print(contains_deco("  @(layout=default)  "))  # Should return True
    print(contains_deco("This is not a deco"))  # Should return False
    print(contains_deco("@(key=value) Some text"))  # Should return False
    print(contains_deco("@()"))  # Should return True (empty deco)
