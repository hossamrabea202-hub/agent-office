import sys
a = sys.argv[1:]
sys.argv = [sys.argv[0]] + a + ['--temp']
exec(compile(open('C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/place_weather504_ue.py', encoding='utf-8').read(), 'place', 'exec'), {'__name__': '__main__'})
