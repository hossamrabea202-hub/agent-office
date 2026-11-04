import sys
a = sys.argv[1:]
sys.argv = [sys.argv[0]] + a
exec(compile(open('C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/shot_after504_ue.py', encoding='utf-8').read(), 'after', 'exec'), {'__name__': '__main__'})
