import os, glob, zipfile
import util.create_resource_zip

def main(build_com="pyinstaller $launcher.pyw --onefile --name=Hornchen"):
    print("::Running pyinstaller::")
    `os.system(build_com)
    print("::Copying resources to archive::")
    util.create_resource_zip.create(os.getcwd(), minimize=True)
    print(":::Done:::")
    os.system("pause")


if __name__ == "__main__":
    main()