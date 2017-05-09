import re, glob

filenames = glob.glob("../*.py")
logfilename = "required_images.txt"

image_load_pattern = re.compile(r"load_image_from_file\(\"(.*?)\"(, .*?)?\)")

with open(logfilename, "w") as logfile:
    for filename in filenames:
        with open(filename, "r") as file:
            print("File: {}".format(filename))
            text = file.read()
            found = image_load_pattern.findall(text)
            print(found)
            result = [img_filename for img_filename, load_args in found]
            print(result)
            if result:
                logfile.write("{}\n{}\n".format(filename, result))
