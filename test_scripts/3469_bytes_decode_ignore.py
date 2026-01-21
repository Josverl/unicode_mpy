# reproducer for issue : 68c28174 breaks utf8 decode with ignore
# https://github.com/micropython/micropython/issues/3469

try:
    b"\xff\xfe".decode("utf8", "ignore")
    print("PASS")
except Exception as e:
    print("FAIL")
