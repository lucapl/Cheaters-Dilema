import numpy as np

from lukasz_151930 import ExtendedPlayer,Card_status

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
            self._add_to_pile(worst_card)
            return worst_card,worst_card

        ### get card equal or better to declared
        next_card = self._get_next_card(top_card[0])
        card = next_card
        declaration = card

        #### player randomly decides whether to cheat or not
        probs = np.array([self._turns_to_win(),self.opponents_turns_to_win],dtype=np.float64)
        probs /= np.sum(probs)
        cheat = np.random.choice([True, False],p=probs)

        if self._can_win_without_cheating(top_card):
            cheat = False

        if card == None:
            cheat = True

        ### if he decides to cheat, use worst card
        if cheat:
            declaration = next_card if next_card != None else top_card
            card = worst_card
        
            declaration = self._fix_card(declaration,top_card)

        ### return the decision (true card) and declaration (player's declaration)
        self._add_to_pile(card)
        return card, declaration


    def startGame(self, cards):
        super(Naive,self).startGame(cards)
        #self.opponents_turns_to_win = len(cards)#assume opponent gets the same number of cards

    ### randomly decides whether to check or not
    def checkCard(self, opponent_declaration):
        self._add_to_pile(None)
        # if opponent declares a card that you own, automatically check
        card_status = self._get_card_status(*opponent_declaration)
        if card_status == Card_status.HAND or card_status == Card_status.PILE:
            return True
        
        self._count_cards()

        card_number,_ = opponent_declaration

        prob = (4*(card_number-self.worst_card))/self.n_all_cards
        prob*= self.doubt

        return np.random.choice([False, True],p=[prob,1-prob])
