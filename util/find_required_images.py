import re, glob

logfilename = "required_images.txt"

image_load_pattern = re.compile(r"load_image_from_file\(\"(.*?)\"(, .*?)?\)")

def find(d="../"):
    filenames = glob.glob(d + "*.py")
    result = {}
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as file:
            text = file.read()
            found = image_load_pattern.findall(text)
            this_result = [img_filename for img_filename, load_args in found]
            result[filename] = this_result
    return result

if __name__ == "__main__":
    r = find()
    for k, v in r.items():
        print("{}: {}".format(k, v))
    print(sum(r.values(), []))