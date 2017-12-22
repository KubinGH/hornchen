import os, zipfile

try:
    try:
        import find_required_images
    except ImportError:
        from util import find_required_images
except ImportError:
    can_find_required_images = False
else:
    can_find_required_images = True

RESOURCES_DIRS = ["configs", "fonts", "images", "levels"]
RESOURCE_ZIP_DIR = "dist/resources.zip"

def create(cwd=None, minimize=False):
    if cwd is not None:
        lastcwd = os.getcwd()
        os.chdir(cwd)
        try:
            create(None, minimize)
        except:
            os.chdir(lastcwd)
            raise
        else:
            os.chdir(lastcwd)
        return
    with zipfile.ZipFile(RESOURCE_ZIP_DIR, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for rdir in RESOURCES_DIRS:
            if minimize and can_find_required_images and rdir == "images":
                required = sum(find_required_images.find("").values(), [])
                if "images/sl/app/LoadingText.png" not in required:
                    required.append("images/sl/app/LoadingText.png")
            else:
                required = None
            for root, dirs, files in os.walk(rdir):
                for file in files:
                    path = os.path.join(root, file).replace("\\", "/")
                    if required is None or path in required:
                        zip_file.write(os.path.join(root, file))

if __name__ == "__main__":
    create(cwd=r"C:\Users\Admin\Desktop\Hornchen", minimize=True)