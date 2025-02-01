from wordle import game

g = game.Game("TOAST")
g.make_guess("RAISE")
print(g.word_bank)
