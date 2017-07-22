import os, glob, zipfile
import util.create_resource_zip

print("::Running pyinstaller::")
os.system("pyinstaller $launcher.pyw --onefile --noconsole --name=Hornchen")
print("::Copying resources to archive::")
util.create_resource_zip.create(os.getcwd())
print(":::Done:::")
os.system("pause")