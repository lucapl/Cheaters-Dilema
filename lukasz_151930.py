import numpy as np
from player import Player

class Lukasz151930(Player):
    
    ### player's random strategy
    def putCard(self, declared_card):
        return "draw"
    
    ### randomly decides whether to check or not
    def checkCard(self, opponent_declaration):
        return np.random.choice([False, False])