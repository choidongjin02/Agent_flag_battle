"""HMH 0930 Early Guard: Search4 with earlier economic-building defense. Optional argv `--off P1,P5` disables proposal features for ablation."""
import sys
from protocol import run
from hmh_features import ALL, FEATURES
from hmh_search import HmhBot

if '--off' in sys.argv:
    off = set(sys.argv[sys.argv.index('--off')+1].split(','))
    assert off <= ALL, off
    FEATURES.difference_update(off)

bot = HmhBot()

def decide(view, init):
    return bot.decide(view, init)

if __name__ == '__main__':
    run(decide)
