import numpy as np
from player import Player

import random

from collections import Counter

class ExtendedPlayer(Player):
    '''
    A player class with some usefull functions
    '''
    def __init__(self, name):
        super(ExtendedPlayer,self).__init__(name)
        self.worst_card = 9
        self.best_card = 14
        self.n_colors=4
        self.n_all_cards = (self.best_card-self.worst_card)*self.n_colors
        self.doubt = 0.25
        self.estimated_game_pile = []
        self.opponent_hand = []
        self.placed_card = None

    @property
    def opponents_turns_to_win(self):
        return len(self.opponent_hand)

    def _get_worst_card(self):
        return min(self.cards,key=lambda card:card[0])
    
    def _get_equal_card(self,card_number):
        for number,color in self.cards:
            if card_number == number:
                return (number,color)
        return None
    
    def _get_next_card(self,card_number):
        better_cards = tuple(filter(lambda card:card[0]>=card_number,self.cards))

        if len(better_cards) == 0: return None

        return min(better_cards,key=lambda card:card[0])
    
    def _turns_to_win(self):
        return len(self.cards)
    
    def _count_cards(self):
        card_numbers = [card[0] for card in self.cards]
        self.number_of_cards = Counter(card_numbers)

    def _must_draw(self,top_card):
        ### check if must draw
        return len(self.cards) == 1 and top_card is not None and self.cards[0][0] < top_card[0]
    
    ### Notification sent at the end of a round
    ### One may implement this method, capture data, and use it to get extra info
    ### -- checked = TRUE -> someone checked. If FALSE, the remaining inputs do not play any role
    ### -- iChecked = TRUE -> I decided to check my opponent (so it was my turn); 
    ###               FALSE -> my opponent checked and it was his turn
    ### -- iDrewCards = TRUE -> I drew cards (so I checked but was wrong or my opponent checked and was right); 
    ###                 FALSE -> otherwise
    ### -- revealedCard - some card (X, Y). Only if I checked.
    ### -- noTakenCards - number of taken cards
    def getCheckFeedback(self, checked, iChecked, iDrewCards, revealedCard, noTakenCards, log=True):
        super(ExtendedPlayer,self).getCheckFeedback(checked,iChecked,iDrewCards,revealedCard,noTakenCards,log)

        # if self.placed_card != None:
        #     self.estimated_game_pile.append(self.placed_card)
        #     self.placed_card = None
        # else:
        #     self.estimated_game_pile.append(None)

        # the only source of info
        if not checked: return None # no info if no one checked, unless someones draws cards

        if iDrewCards == False and noTakenCards != None: #opponent drew cards
            toTake = self.estimated_game_pile[max([-3, -len(self.pile)]):]
            self.opponent_hand = self.opponent_hand + toTake

    def _fix_card(self,declaration,top_card):
        ### Yet, declared card should be no worse than a card on the top of the pile . 
        if top_card is not None and declaration[0] < top_card[0]:
            return (min(top_card[0]+1,14), declaration[1])
        return declaration

class Naive(ExtendedPlayer):
    
    def __init__(self, name):
        super(Naive,self).__init__(name)
        self.cost_matrix = np.zeros((2,2))
        self.worst_card = 9
        self.best_card = 14
        self.n_colors=4
        self.n_all_cards = (self.best_card-self.worst_card)*self.n_colors
        self.doubt = 0.25

    ### player's random strategy
    def putCard(self, top_card):
        if self._must_draw(top_card):
            return "draw"
        
        worst_card = self._get_worst_card()

        if top_card == None: #if first, place lowest card
            return worst_card,worst_card

        ### get card equal or better to declared
        next_card = self._get_next_card(top_card[0])
        card = next_card
        declaration = card

        #### player randomly decides whether to cheat or not
        probs = np.array([self._turns_to_win(),self.opponents_turns_to_win],dtype=np.float64)
        probs /= np.sum(probs)
        cheat = np.random.choice([True, False],p=probs)

        if card == None:
            cheat = True

        ### if he decides to cheat, use worst card
        if cheat:
            declaration = next_card if next_card != None else top_card
            card = worst_card
        
        declaration = self._fix_card(declaration,top_card)

        ### return the decision (true card) and declaration (player's declaration)
        return card, declaration


    def startGame(self, cards):
        super(Naive,self).startGame(cards)
        self.opponents_turns_to_win = len(cards)#assume opponent gets the same number of cards

    ### randomly decides whether to check or not
    def checkCard(self, opponent_declaration):
        # if opponent declares a card that you own, automatically check
        if opponent_declaration in self.cards:
            return True
        
        self._count_cards()

        card_number,_ = opponent_declaration

        prob = (4*(card_number-self.worst_card))/self.n_all_cards
        prob*= self.doubt


        return np.random.choice([False, True],p=[prob,1-prob])
    
        
    