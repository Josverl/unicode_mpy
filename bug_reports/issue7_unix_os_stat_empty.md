
# Unix port: `os.stat('')` raises OSError instead of returning stat for current directory

`os.stat('')` on an empty filename string behaves differently on the Unix port compared to MCU ports.

## Port, board and/or hardware

Unix port vs MCU ports 

## MicroPython version

 Unix 1.27.0 

## Reproduction

Run the following command on both Unix and non-Unix targets:

```python
import os
print(os.stat(''))
```

Or via mpremote:

```bash
# On MCU
mpremote exec "import os; print(os.stat(''))"

# On Unix port
mpremote unix exec "import os; print(os.stat(''))"
```

## Expected behaviour

Consistent behavior across all ports.
on MCU ports, `os.stat('')` returns the stat info for the current directory

```
(micropython) jos@josverl-sb5:~/micropython$ mpremote exec "import os; print(os.stat(''))"
(16384, 0, 0, 0, 0, 0, 0, 0, 0, 0)
```

Note: `16384` (0x4000) indicates `S_IFDIR` - a directory.

## Observed behaviour

On the Unix port, `os.stat('')` raises an `OSError`:

```
(micropython) jos@josverl-sb5:~/micropython$ mpremote unix exec "import os; print(os.stat(''))"
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
OSError: [Errno 2] ENOENT
```

The Unix port treats an empty string as a non-existent file, while MCU ports treat it as the current directory.

## Additional Information

This inconsistency may affect code that relies on `os.stat('')` to get information about the current working directory. The behavior should be unified across all ports.

This inconsistency also causes issues in higher-level functions like `os.listdir('')` on the Unix port, which also raises an `OSError` instead of listing the current directory contents.

and in mpremote: 

```
mpremote unix rm -r :
rm :
mpremote: rm: : No such file or directory.

# workaround, explicitly state current directory
 mpremote unix rm -rv :.
rm :.
removed: './remote_data/Nordic_Icelandic/Päivi_Mäkinen.txt'
removed: './remote_data/Nordic_Icelandic/Jüri_Mägi.txt'
removed: './remote_data/Nordic_Icelandic/Þórður_Björk.txt'
removed: './remote_data/Nordic_Icelandic/Søren_Ødegård.txt'

```

## Code of Conduct

Yes, I agree to follow the MicroPython Code of Conduct.

