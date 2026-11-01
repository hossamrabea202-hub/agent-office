# i5 core: run editor Python without the console (2026-11-01). Start the editor with
#   -ExecutePythonScript="C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/ue_inbox_watcher.py"
# Every second (on the editor's game thread) it runs each *.py dropped in ue_inbox/ (oldest first, with its optional
# args in a sibling <name>.args file: one argument per line), appends the output / traceback to ue_inbox/_log.txt and
# moves the script to ue_inbox/done/. Why: on i5 the console bar sometimes stops taking clicks (Slate input), and a
# floating window or a locked clipboard blocks typing.
import os, sys, io, time, glob, shutil, traceback, unreal
INBOX = 'C:/Users/hossam.rabea/agent-office/handoffs/laptop-i5/ue_inbox'
os.makedirs(INBOX + '/done', exist_ok=True)
_state = {'t': 0.0}


def _run(path):
    args_file = path[:-3] + '.args'
    args = [l.strip() for l in open(args_file, encoding='utf-8').read().splitlines() if l.strip()] if os.path.exists(args_file) else []
    buf, old_out, old_argv = io.StringIO(), sys.stdout, sys.argv
    sys.stdout, sys.argv = buf, [path] + args
    ok = True
    try:
        code = compile(open(path, encoding='utf-8').read(), path, 'exec')
        exec(code, {'__name__': '__main__', '__file__': path})
    except SystemExit as e:
        buf.write('SystemExit: %s\n' % e)
    except Exception:
        ok = False; buf.write(traceback.format_exc())
    finally:
        sys.stdout, sys.argv = old_out, old_argv
    stamp = time.strftime('%H:%M:%S')
    with open(INBOX + '/_log.txt', 'a', encoding='utf-8') as f:
        f.write('==== %s %s %s %s\n%s\n' % (stamp, os.path.basename(path), args, 'OK' if ok else 'FAILED', buf.getvalue()))
    for p in (path, args_file):
        if os.path.exists(p):
            dst = INBOX + '/done/' + time.strftime('%H%M%S_') + os.path.basename(p)
            shutil.move(p, dst)
    unreal.log('i5 inbox: ran %s (%s)' % (os.path.basename(path), 'OK' if ok else 'FAILED'))


def _connected():
    # 2026-11-01: queued scripts ran at startup before the Multi-User join (frame 8), wrote to i5's disk copy and the
    # editor crashed. Scripts wait until the session is joined and 20 s have passed; names starting with nomu_ run anyway.
    try: ok = unreal.MultiUserClientStatics.get_multi_user_connection_status_detail() == unreal.MultiUserConnectionStatus.CONNECTED
    except Exception: ok = False
    if not ok: _state['since'] = None; return False
    if _state.get('since') is None: _state['since'] = time.time()
    return time.time() - _state['since'] > 20.0


def _tick(dt):
    _state['t'] += dt
    if _state['t'] < 1.0: return
    _state['t'] = 0.0
    if not _connected():
        for p in sorted(glob.glob(INBOX + '/nomu_*.py'), key=os.path.getmtime): _run(p.replace('\\', '/'))
        return
    for p in sorted(glob.glob(INBOX + '/*.py'), key=os.path.getmtime):
        _run(p.replace('\\', '/'))


if not getattr(unreal, '_i5_inbox_handle', None):
    unreal._i5_inbox_handle = unreal.register_slate_post_tick_callback(_tick)
    unreal.log('i5 inbox watcher started on ' + INBOX)
