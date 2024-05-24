import numpy as np
from player import Player

import random

from collections import Counter
from enum import Enum

class Card_status(Enum):
    UNKNOWN = -1
    PILE = 0
    HAND = 1
    OPPONENT = 2


class ExtendedPlayer(Player):
    '''
    A player class with some usefull functions
    '''
    def __init__(self, name):
        super(ExtendedPlayer,self).__init__(name)
        self.worst_card = 9
        self.best_card = 14
        self.n_colors=4
        self.n_all_cards = (self.best_card-self.worst_card+1)*self.n_colors

        self.doubt = 0.25

        self.estimated_game_pile = []
        self.opponent_hand = []
        self.card_statuses = np.full((self.best_card-self.worst_card+1,self.n_colors),Card_status.UNKNOWN)


    @property
    def opponents_turns_to_win(self):
        return len(self.opponent_hand)
    
    def _update_card_status(self,number,color,status):
        self.card_statuses[number-self.worst_card,color] = status
    
    def _get_card_status(self,number,color):
        return self.card_statuses[number-self.worst_card,color]
    
    def _add_to_pile(self,card):
        self.estimated_game_pile.append(card)
        if card == None: return None
        self._update_card_status(*card,Card_status.PILE)

    def _add_to_opponent(self,cards):
        filtered = list(filter(lambda c: c != None,cards))
        self.opponent_hand += filtered if self._have_seen_all() else cards
        for n,c in filtered:
            self._update_card_status(n,c,Card_status.OPPONENT)

    def _remove_from_pile(self,taken):
        toTake = self.estimated_game_pile[-taken:]
        self.estimated_game_pile = self.estimated_game_pile[:-taken]
        return toTake

    def _remove_from_opponent(self,card):
        try:
            self.opponent_hand.remove(card)
        except ValueError as e:
            return None
    
    def _can_win_without_cheating(self,card):
        return card[0] <= self._get_worst_card()[0]

    def _get_worst_card(self):
        return self._get_worst_card_from(self.cards)
    
    def _get_worst_card_from(self,cards):
        filtered = tuple(filter(lambda card: card != None,cards))
        return min(filtered,key=lambda card:card[0]) if len(filtered) != 0 else (self.worst_card,0)
    
    def _get_equal_card(self,card_number):
        for number,color in self.cards:
            if card_number == number:
                return (number,color)
        return None
    
    def _get_next_card_from(self,card_number,cards):
        better_cards = tuple(filter(lambda card:card != None and card[0]>=card_number,cards))

        if len(better_cards) == 0: return None

        return min(better_cards,key=lambda card:card[0])
    
    def _get_next_card(self,card_number):
        return self._get_next_card_from(card_number,self.cards)
    
    def _turns_to_win(self):
        return len(self.cards)
    
    def _count_cards(self):
        card_numbers = [card[0] for card in self.cards]
        self.number_of_cards = Counter(card_numbers)

    def _cards_to_draw(self,n=3):
        return self.estimated_game_pile[max([-n, -len(self.estimated_game_pile)]):]

    def _have_seen_all(self):
        seen_cards = self.n_all_cards - np.sum(self.card_statuses==Card_status.UNKNOWN)
        return seen_cards == 16

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
        # the only source of info
        #if not checked: return None # no info if no one checked, unless someones draws cards

        taken = None
        if noTakenCards != None: # opponent or I drew cards
            taken = self._remove_from_pile(noTakenCards)
        else:
            return None

        if iDrewCards == False: #opponent drew cards
            self._add_to_opponent(taken)
        # else: # i drew cards
        #     for n,c in filter(lambda c: c != None,taken):
        #         self._update_card_status(n,c,Card_status.HAND)

        # print("Opponent hand:",self.opponent_hand)

        # print("Game pile:",self.estimated_game_pile)
        # print(self.card_statuses)

    def startGame(self, cards):
        super().startGame(cards)
        for n,c in cards:
            self._update_card_status(n,c,Card_status.HAND)
        self.opponent_hand = [None for _ in cards]

    def takeCards(self, cards_to_take):
        super().takeCards(cards_to_take)
        for n,c in cards_to_take:
            self._update_card_status(n,c,Card_status.HAND)

    def _fix_card(self,declaration,top_card):
        ### Yet, declared card should be no worse than a card on the top of the pile . 
        if top_card is not None and declaration[0] < top_card[0]:
            return (min(top_card[0]+1,14), declaration[1])
        return declaration

def find_pure_nash(payoff_matrix):
    nash_equilibria = []

    for i in range(payoff_matrix.shape[0]):
        for j in range(payoff_matrix.shape[1]):
            a_best_response = np.all(payoff_matrix[i, :, 0] <= payoff_matrix[i, j, 0])
            b_best_response = np.all(payoff_matrix[:, j, 1] <= payoff_matrix[i, j, 1])
            if a_best_response and b_best_response:
                nash_equilibria.append((i, j))
    
    return nash_equilibria

def safe_div(a,b):
    return a/b if b != 0 else None

def mixed_strats(payoff:np.array):
    '''
        Calculate mixed strategy for 2x2 payoff matrix
    '''
    #A = np.vstack((payoff[0,:,0]-payoff[1,:,0],payoff[0,:,1]-payoff[1,:,1]))
    #b = np.array([payoff[0,0,0]-payoff[0,1,0],payoff[0,0,1]-payoff[1,0,1]])
    a11,a12,a21,a22 = payoff[:,:,0].flatten()
    b11,b12,b21,b22 = payoff[:,:,1].flatten()

    # A = np.array([[a[0,0]-a[1,0],a[0,1]-a[1,1]],
    #             [b[0,0]-b[0,1],b[1,0]-b[1,1]]])
    # c = np.array([a[1,0]-a[1,1],b[0,1]-b[1,1]])

    # probs = np.linalg.solve(A, c)
    # print(probs)
    p = safe_div((a22-a12),(a11-a21-a12+a22))
    if p != None and (p < 0 or p > 1):
        p = None
    #if np.all(probs >= 0) and np.all(probs <= 1):
    q = safe_div((b22-b12),(b11-b21-b12+b22))
    if q != None and (q <0 or q > 1):
        q = None
    return (q, 1 - q) if q != None else None,(p, 1 - p) if p != None else None

class Lukasz151930(ExtendedPlayer):
    
    def __init__(self, name):
        super(Lukasz151930,self).__init__(name)
        self.avg_card_util = -np.mean(np.arange(1,7))

    def _card_util(self,card):
        return card[0] - self.best_card -1 if card != None else self.avg_card_util

    def _calculate_cost_matrix(self,declared_card,placer_cards,checker_cards):
        self.avg_card_util = self._get_average_util_of(Card_status.UNKNOWN if not self._have_seen_all else Card_status.OPPONENT)
        payoff_matrix = np.zeros((2,2,2))# first dim, cheat or not, #second dim check or not #third dim cheating player, checking player

        # utility of declared card
        declared_card_util = self._card_util(declared_card)

        # utility of top 2 cards in pile
        card_to_draw_util = sum([self._card_util(card) for card in self._cards_to_draw(2)])

        # utility of placers hand
        placer_util = sum([self._card_util(card) for card in placer_cards])

        # utility of checker hand
        checker_util = sum([self._card_util(card) for card in checker_cards])

        # utility of cheaters worst card
        cheated_card_util = self._card_util(self._get_worst_card_from(placer_cards))

        # utility of checkers worst card
        worst_card_util = self._card_util(self._get_worst_card_from(checker_cards))

        # utility of equal to declared for cheater
        equal_card_util_placer = self._card_util(self._get_next_card_from(declared_card[0],placer_cards))

        # utility of equal to declared for checker
        equal_card_util_check = self._card_util(self._get_next_card_from(declared_card[0],checker_cards))

        payoff_matrix[0,0,0] = placer_util + card_to_draw_util 
        payoff_matrix[0,1,0] = placer_util - cheated_card_util
        payoff_matrix[1,0,0] = placer_util - declared_card_util - worst_card_util
        payoff_matrix[1,1,0] = placer_util - declared_card_util

        payoff_matrix[0,0,1] = checker_util - worst_card_util
        payoff_matrix[0,1,1] = checker_util - equal_card_util_check
        payoff_matrix[1,0,1] = checker_util + card_to_draw_util + cheated_card_util
        payoff_matrix[1,1,1] = checker_util - equal_card_util_check

        return payoff_matrix

    def _get_average_util_of(self,card_status=Card_status.UNKNOWN):
        unknowns = (self.card_statuses == card_status).astype(np.int8).T
        unknowns *= np.arange(self.worst_card,self.best_card+1)
        unknowns -= self.best_card-1
        mean = np.mean(unknowns)
        return mean

    def _get_mixed_strategy_probs(self,declared_card,placer_cards,checker_cards):
        return mixed_strats(self._calculate_cost_matrix(declared_card,placer_cards,checker_cards))

    # def _calc_hand_util(self,hand):
    #     util = 0
    #     for card in hand:
    #         if card == None:
    #             util -= self.avg_card_util
    #         util += card[0]-self.best_card-1
    #     return util

    ### player's strategy
    def putCard(self, top_card):
        if self._must_draw(top_card):
            return "draw"
        
        worst_card = self._get_worst_card()

        if top_card == None: #if first, place lowest card
            self._add_to_pile(worst_card)
            return worst_card,worst_card

        ### get card equal or better to declared
        next_card = self._get_next_card(top_card[0])
        card = next_card
        declaration = card

        #### player randomly decides whether to cheat or not

        probs = self._get_mixed_strategy_probs(declaration if declaration != None else top_card,
                                               self.cards,self.opponent_hand)[0]

        # probs = np.array([self._turns_to_win(),self.opponents_turns_to_win],dtype=np.float64)
        # probs /= np.sum(probs)
        cheat = np.random.choice([True, False],p=probs if probs != None else [0.5,0.5])

        if card == None:
            cheat = True

        ### if he decides to cheat, use worst card
        if cheat:
            declaration = next_card if next_card != None else top_card
            card = worst_card
        
        declaration = self._fix_card(declaration if declaration != None else worst_card,top_card)

        ### return the decision (true card) and declaration (player's declaration)
        self._add_to_pile(card)
        return card, declaration


    def startGame(self, cards):
        super(Lukasz151930,self).startGame(cards)
        #self.opponents_turns_to_win = len(cards)#assume opponent gets the same number of cards

    ### randomly decides whether to check or not
    def checkCard(self, opponent_declaration):
        self._add_to_pile(None)
        self._remove_from_opponent(None)
        # if opponent declares a card that you own, automatically check
        card_status = self._get_card_status(*opponent_declaration)
        if card_status == Card_status.HAND or card_status == Card_status.PILE:
            return True
        
        self._count_cards()

        card_number,_ = opponent_declaration

        simple_prob = (4*(card_number-self.worst_card))/self.n_all_cards
        simple_prob*= self.doubt

        probs = self._get_mixed_strategy_probs(opponent_declaration,self.opponent_hand,self.cards)[1]

        return np.random.choice([True, False],p=probs if probs != None else [simple_prob,1-simple_prob])
