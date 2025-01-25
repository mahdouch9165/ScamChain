import re

FUNCTION_REGEX = re.compile(r'function\s+([A-Za-z0-9_]+)\s*\(')

def get_function_names(solidity_code):
    """
    Returns a set of all unique function names found via regex.
    """
    matches = FUNCTION_REGEX.findall(solidity_code)
    return set(matches)