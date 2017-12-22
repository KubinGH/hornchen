import io
import zipfile
from os import listdir

enable_resource_zip = True
resource_zip_filename = "resources.zip"

archive = None
c_open = open

zip_present = resource_zip_filename in listdir()
if enable_resource_zip and not zip_present:
    print("[WARNING] Couldn't find the resources archive!")
if enable_resource_zip and zip_present:
    print("Load resource zip hook")
    archive = zipfile.ZipFile(resource_zip_filename, "r")
    def open(filename, mode="r"):
        try:
            # First, try to get the file from the archive
            content = archive.read(filename)
        except KeyError:
            # If it's not there, use plain open from working directory
            try:
                with c_open(filename, mode) as file:
                    content = file.read()
            except FileNotFoundError:
                raise FileNotFoundError("[zipopen] The file '{}' was not ".format(filename) + \
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
    enable_resource_zip = False