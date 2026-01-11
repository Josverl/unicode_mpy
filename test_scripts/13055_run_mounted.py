# https://github.com/micropython/micropython/issues/13055

with open("foo.txt", 'w', encoding='utf-8') as file:
    file.write("🔢 Data" + '\n')
    file.write("🔢 Data" + '\n')

with open("foo.txt", 'r', encoding='utf-8') as file:
    data = file.read()
    print(data)