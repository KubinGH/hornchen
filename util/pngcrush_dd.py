import glob, subprocess, os

directory = os.path.join(os.getcwd(), "dd")
for file in glob.glob(os.path.join(directory, "*.png")):
    subprocess.call(["pngcrush", "-ow", "-rem allb", "-reduce", file])