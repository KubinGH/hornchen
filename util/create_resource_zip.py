import os, zipfile

RESOURCES_DIRS = ["configs", "fonts", "images", "levels"]
RESOURCE_ZIP_DIR = "dist/resources.zip"

def create(cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    with zipfile.ZipFile(RESOURCE_ZIP_DIR, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for rdir in RESOURCES_DIRS:
            for root, dirs, files in os.walk(rdir):
                for file in files:
                    zip_file.write(os.path.join(root, file))