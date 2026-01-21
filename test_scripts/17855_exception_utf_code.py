"""
Issue #17855: Crash printing exception detail when source code is not valid UTF-8
https://github.com/micropython/micropython/issues/17855

Description:
When an exception occurs in code that contains invalid UTF-8 sequences,
MicroPython crashes when trying to print the exception traceback.

This happens because the exception handler tries to decode the source line
containing the error, but the source contains invalid UTF-8.
"""


# Slight changes (like removing the derived exception type) move the misbehavior
# around. For instance, in my local build, not having this triggers
# 'NotImplementedError: opcode' instead.
class Dummy(BaseException):
    pass


# Smuggle invalid UTF-8 string into decompress_error_text_maybe
# This invalid UTF-8 string acts matches the test MP_IS_COMPRESSED_ROM_STRING
# This can also happen if the input file is not a valid UTF-8 file.
b = eval(b"'\xff" + b"\xfe" * 4096 + b"'")
try:
    raise BaseException(b)
except BaseException as good:
    print(type(good), good.args[0])
