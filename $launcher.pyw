import sys
import contextlib
import app as applib

if __name__ == "__main__":
    app = applib.App(applib.screen)
    #with open("log.txt", "w") as logfile:
    #    with contextlib.redirect_stdout(logfile):
    app.run()