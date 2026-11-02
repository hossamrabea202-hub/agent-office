# i5: run a hand-off editor script IN PLACE (its own __file__ / folder, its own argv) through the inbox watcher.
#   sh ue_run.sh run_at_ue.py <repo-relative or absolute script.py> [script args ...]
import os, sys
REPO = 'C:/Users/hossam.rabea/agent-office'
src = sys.argv[1] if os.path.isabs(sys.argv[1]) else REPO + '/' + sys.argv[1]
sys.argv = [src] + sys.argv[2:]
exec(compile(open(src, encoding='utf-8').read(), src, 'exec'), {'__name__': '__main__', '__file__': src})
