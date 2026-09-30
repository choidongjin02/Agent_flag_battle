"""HMH v1."""
from protocol import run
from hmh_search import HmhBot

bot = HmhBot()

def decide(view, init):
    return bot.decide(view, init)

if __name__ == '__main__':
    run(decide)
