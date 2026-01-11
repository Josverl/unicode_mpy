

# Unix port: File sizes not correctly reported by mpremote

File sizes are always reported as zero when using `mpremote` commands (`ls`, `tree`) connected to a MicroPython Unix port (via mpbridge).

This issue was found while working on the mpbridge solution, but is not specific to mpbridge. This is not related to unicode characters in filenames—those are listed correctly.

## Port, board and/or hardware

Unix port, connected via mpbridge (`socket://localhost:2218`)

## MicroPython version

MicroPython Unix port (master branch)

## Reproduction

1. Start the MicroPython Unix port with mpbridge
2. Use `mpremote unix` to connect to the Unix port
3. Run directory listing commands:

```powershell
mpremote unix tree -vh :remote_data/Latin_Western_European
mpremote unix ls -vh :remote_data/Latin_Western_European
```

Or demonstrate the root cause directly:

```powershell
# Unix port returns 3-tuple (missing filesize)
mpremote unix exec "import os;print(list(os.ilistdir('remote_data/Latin_Western_European')))"

# MCU returns 4-tuple (with filesize)
mpremote exec "import os;print(list(os.ilistdir('remote_data/Latin_Western_European')))"
```

## Expected behaviour

File sizes should be displayed correctly, as seen when connected to an MCU:

```
PS D:\> mpremote tree -vh :remote_data/Latin_Western_European
tree :remote_data/Latin_Western_European
:remote_data/Latin_Western_European on COM22
├── [   281]  Arantxa_Etxeberría.txt
├── [   311]  François_Müller.txt
├── [   248]  Giuseppe_Rosé.txt
├── [   267]  Jeroen_de_Vries.txt
├── [   311]  Jordi_Puigdomènech.txt
├── [   285]  José_García.txt
├── [   306]  João_Conceição.txt
├── [   288]  O'zbek_Ismoilov.txt
├── [   283]  Xoán_Fernández.txt
├── [   291]  Ömer_Çelik.txt
└── [   335]  Đặng_Nguyễn.txt
```

`os.ilistdir()` should return a 4-tuple `(name, type, inode, size)` as per [documentation](https://docs.micropython.org/en/latest/library/os.html#os.ilistdir).

## Observed behaviour

File sizes are always reported as zero:

```
PS D:\> mpremote unix tree -vh :remote_data/Latin_Western_European
tree :remote_data/Latin_Western_European
:remote_data/Latin_Western_European on socket://localhost:2218
├── [     0]  Arantxa_Etxeberría.txt
├── [     0]  François_Müller.txt
├── [     0]  Giuseppe_Rosé.txt
├── [     0]  Jeroen_de_Vries.txt
├── [     0]  Jordi_Puigdomènech.txt
├── [     0]  José_García.txt
├── [     0]  João_Conceição.txt
├── [     0]  O'zbek_Ismoilov.txt
├── [     0]  Xoán_Fernández.txt
├── [     0]  Ömer_Çelik.txt
└── [     0]  Đặng_Nguyễn.txt
```

**Root cause:** The Unix port filesystem implementation returns a 3-tuple from `os.ilistdir()`:

```python
# Unix port returns 3-tuple: (name, type, inode)
('Jeroen_de_Vries.txt', 32768, 1326491)

# MCU returns 4-tuple: (name, type, inode, size)
('Jeroen_de_Vries.txt', 32768, 0, 267)
```

The 4th element (filesize) is missing from the Unix port, causing mpremote to misinterpret the data.

## Additional Information

Full `os.ilistdir()` output comparison:

**Unix port (3-tuple, missing size):**
```python
[('Jordi_Puigdom\xe8nech.txt', 32768, 1326492), ('Giuseppe_Ros\xe9.txt', 32768, 1326490), ...]
```

**MCU (4-tuple, with size):**
```python
[('Arantxa_Etxeberr\xeda.txt', 32768, 0, 281), ('Fran\xe7ois_M\xfcller.txt', 32768, 0, 311), ...]
```

## Code of Conduct

Yes, I agree to follow the MicroPython Code of Conduct.

