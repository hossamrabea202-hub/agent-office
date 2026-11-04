# rebuild the temp materials (in memory), wait is done by the caller, then the after shots
import sys
sys.argv = [sys.argv[0], '--temp']
exec(compile(open('C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/build_weather504_ue.py', encoding='utf-8').read(), 'build', 'exec'), {'__name__': '__main__'})
