import sys

def log(msg):
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()