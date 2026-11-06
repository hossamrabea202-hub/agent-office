import sys, io, contextlib, traceback, unreal
f, args, out = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
buf = io.StringIO()
sys.argv = ['x'] + args
try:
    with contextlib.redirect_stdout(buf):
        exec(open(f, encoding="utf-8-sig").read(), {'__file__': f, '__name__': '__main__'})
except BaseException:
    buf.write('\nERR ' + traceback.format_exc()[-1500:])
open(out, 'w').write(buf.getvalue())
