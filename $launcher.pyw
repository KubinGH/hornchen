import builtins
import os, traceback

logfiles = True

def main():
    if logfiles:
        mainlog = open("log.txt", "w")
        cprint = print
        def print_to_stdout_and_log_file(*args, **kwargs):
            cprint(*args, **kwargs)
            if "file" in kwargs:
                del kwargs["file"]
            if "flush" in kwargs:
                del kwargs["flush"]
            return cprint(*args, **kwargs, file=mainlog, flush=True)
        builtins.print = print_to_stdout_and_log_file
    try:
        import app as applib
        app = applib.App(applib.screen)
        applib.make_loading_text_fade_out()
        app.run()
    except Exception as e:
        traceback.print_exc()
        if logfiles:
            with open("errorlog.txt", "w") as log:
                log.write(traceback.format_exc())
    finally:
        mainlog.close()
        builtins.print = cprint

if __name__ == "__main__":
    main()