import pytest
from _pytest.runner import runtestprotocol



# This part was made by nagylzs
import os
import time
import threading
import sys
import traceback
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# Taken from http://bzimmer.ziclix.com/2008/12/17/python-thread-dumps/

def stacktraces():
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# ThreadID: %s" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    result =  highlight("\n".join(code), PythonLexer(), HtmlFormatter(
        full=False,
        # style="native",
        noclasses=True,
    ))
    return result





class TraceDumper(threading.Thread):
    """Dump stack traces into a given file periodically."""
    def __init__(self,fpath,interval,auto):
        """
        @param fpath: File path to output HTML (stack trace file)
        @param auto: Set flag (True) to update trace continuously.
            Clear flag (False) to update only if file not exists.
            (Then delete the file to force update.)
        @param interval: In seconds: how often to update the trace file.
        """
        assert(interval>0.1)
        self.auto = auto
        self.interval = interval
        self.fpath = os.path.abspath(fpath)
        self.stop_requested = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        while not self.stop_requested.isSet():
            time.sleep(self.interval)
            if self.auto or not os.path.isfile(self.fpath):
                self.stacktraces()

    def stop(self):
        self.stop_requested.set()
        self.join()
        try:
            if os.path.isfile(self.fpath):
                os.unlink(self.fpath)
        except:
            pass

    def stacktraces(self):
        with open(self.fpath,"a") as fout:
            fout.write(stacktraces())


_tracer = None
def trace_start(fpath,interval=5,auto=True):
    """Start tracing into the given file."""
    global _tracer
    if _tracer is None:
        _tracer = TraceDumper(fpath,interval,auto)
        _tracer.setDaemon(True)
        _tracer.start()
    else:
        raise Exception("Already tracing to %s"%_tracer.fpath)

def trace_stop():
    """Stop tracing."""
    global _tracer
    if _tracer is None:
        raise Exception("Not tracing, cannot stop.")
    else:
        _tracer.stop()
        _trace = None

#trace_start("/vagrant/trace.html",interval=5,auto=True) # Set auto flag to always update file!
#import atexit
#atexit.register(trace_stop)

import faulthandler
faulthandler.enable()
f=open('/vagrant/trace.txt', 'a')
faulthandler.dump_traceback_later(5,file=f, repeat=True)
def finish(f):
    faulthandler.cancel_dump_traceback_later()
    f.close()
import atexit
atexit.register(finish,f)

def pytest_runtest_protocol(item, nextitem):
    print("Going to run: "+item.name)
    reports = runtestprotocol(item, nextitem=nextitem)
    print("Done to run: "+item.name)
    for report in reports:
        pass
        #if report.when == 'call':
        #    print ('\n%s --- %s' % (item.name, report.outcome))
        #print ('\n%s ---%s--- %s' % (item.name, report.when, report.outcome))
    return True
