import io
import zipfile
from os import listdir

enable_resource_zip = False

archive = None
c_open = open

if enable_resource_zip:
    print("Load resource zip hook")
    archive = zipfile.ZipFile("resources.zip", "r")
    def open(filename, mode="r"):
        # The mode is muted, since we only read from the archive
        try:
            content = archive.read(filename)
        except KeyError:
            try:
                with c_open(filename, mode) as file:
                    content = file.read()
            except FileNotFoundError:
                raise FileNotFoundError("[zipopen] The file {} was not ".format(filename) + \
                                        "found in the archive nor the app directory")
        if mode == "r":
            # If the file was loaded locally, don't decode it
            # Decode if loaded from archive - bytes
            if isinstance(content, bytes):
                content = str(content, "utf-8")
            return io.StringIO(content)
        elif mode == "rb":
            return io.BytesIO(content)
        else:
            raise ValueError("[zipopen] Incorrect archive open mode")

    def listdir(directory):
        directory = directory.strip("/")
        directory = directory.replace("\\", "/")
        # namelist is a list of files with full directories
        return [elem.split("/")[-1] for elem in archive.namelist()
                if elem.startswith(directory) and elem.count("/") == directory.count("/") + 1]
else:
    pass