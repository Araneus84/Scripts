import os

def add_path(path_to_add):
    path = os.environ["PATH"]
    return path + os.pathsep + path_to_add

print(os.environ["PATH"])

add_path(r"")

print(os.environ["PATH"])
