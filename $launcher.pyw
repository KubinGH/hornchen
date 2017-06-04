import sys
import app as applib

'''
# Sometimes doesn't work?

class Logger:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, "w"): pass # Clear

    def write(self, text):
        with open(self.filename, "a") as file:
            file.write(text)

    def close(self):
        pass

sys.stdout = sys.stderr = Logger("log.txt")
'''

if __name__ == "__main__":
    app = applib.App(applib.screen)
    app.run()