import os
print(os.listdir("d:/git2"))
for entry in os.scandir("d:/git2"):
    print(entry)