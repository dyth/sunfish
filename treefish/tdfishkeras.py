#!/usr/bin/env python
"""
2-ply searcher trained with temporal difference reinforcement learning 
"""
from __future__ import print_function
import torch, random, re, sys
import numpy as np

from randomfish import Searcher as RandomSearcher
from slimfish import *
from valueNetworkKeras import *
from minimax import node


LEARNING_RATE = 0.5
DISCOUNT_RATE = 0.7
np.random.seed(1729)


class TreeStrapSearcher:
    
    def __init__(self):
        'set network to evalnet and minimax search depth'
        self.network = create_model()
        self.depth = 2
        self.threshold = 0.95
        

    def expl(self, random):
        'exploration or explotiation'
        if random > self.threshold:
            return 'random'
        else:
            return 'train'

        
    def train_white(self, pos, random, secs=None):
        'train white on minimax values to self.depth'
        currentNode = node(pos, self.depth, 0, self.network, self.expl(random))
        return currentNode.bestNode, currentNode.depth_first_pairs()

    
    def train_black(self, pos, random, secs=None):
        'train black on minimax values to self.depth'
        currentNode = node(pos, self.depth, 1, self.network, self.expl(random))
        return currentNode.bestNode, currentNode.depth_first_pairs()


    def search_white(self, pos, secs=None):
        'train white on minimax values to self.depth'
        return node(pos, self.depth, 0, self.network, 'search').bestNode
        
    
    def search_black(self, pos, secs=None):
        'train black on minimax values to self.depth'
        return node(pos, self.depth, 1, self.network, 'search').bestNode
         


def play(white, black):
    'return 1 if white wins and -1 if black wins'
    # initialise searcher and initial board
    pos = Position(initial, 0, (True,True), (True,True), 0, 0)

    for _ in range(40):
        # if no possible white moves, black checkmate, else white ply
        whiteMove = white.search_white(pos, secs=None)
        if whiteMove == None:
            # if no possible moves and in check, then mate
            if check(pos.rotate()):
                return -1
            else:
                return 0.5
        pos = whiteMove

        # if no possible black moves, white checkmate, else black ply
        blackMove = black.search_black(pos, secs=None)
        if blackMove == None:
            # if no possible moves and in check, then mate
            if check(pos):
                return 1
            else:
                return 0.5
        pos = blackMove
    return 0


def self_play(searcher):
    'return 1 if white wins and -1 if black wins'
    # initialise searcher and board
    pos = Position(initial, 0, (True,True), (True,True), 0, 0)
    boards = []
    # train for 40 steps
    for _ in range(40):
        # white's turn
        random = np.random.rand(1)
        move, pairs = searcher.train_white(pos, random, secs=None)
        if move == None:
            # if no possible white moves and black check, then black mate
            if check(pos.rotate()):
                return -1, boards, pos
            else:
                return 0.5, boards, pos
        pos = move
        boards += pairs
        # black's turn
        random = np.random.rand(1)
        move, pairs = searcher.train_black(pos, random, secs=None)
        if move == None:
            # if no possible black moves and in white check, then white mate
            if check(pos):
                return 1, boards, pos
            else:
                return 0.5, boards, pos
        pos = move
        boards += pairs
    # otherwise a draw
    print(len(boards), "training examples")
    return 0, boards, pos

        
def train(numGames, searcher):
    'train the searcher using td learning'
    for n in range(numGames):
        # get and print outcome and final position
        print("selfplay", n)
        winner, boards, pos = self_play(searcher)
        if winner == 1:
            print(n, "White won")
        elif winner == -1:
            print(n, "Black won")
        elif winner == 0.5:
            print(n, "Stalemate")
        else:
            print(n, "Draw")
        print_pos(pos)
        # train on positions
        train_model(searcher.network, boards)
        print("trained")
    # save weights in directory treeStrapWeights/
    global weightsNum
    name = "treeStrapWeights/" +  str(weightsNum + 1) + ".h5"
    searcher.network.save(name)


def validate(searchers):
    'get % wins against random agents'
    whiteWins, blackWins, stalemate, draw = 0, 0, 0, 0
    for i in range(50):
        # agent as white, random as black
        firstPlay = play(searchers[0], searchers[1])
        if firstPlay == 1:
            whiteWins += 1
        elif firstPlay == 0.5:
            stalemate += 1
        elif firstPlay == 0:
            draw += 1
        # random as white, agent as black
        secondPlay = play(searchers[1], searchers[0])
        if secondPlay == -1:
            blackWins += 1
        elif secondPlay == 0.5:
            stalemate += 1
        elif secondPlay == 0:
            draw += 1
    with open("treeStrapLearn.txt", "a") as file:
        wins = str(whiteWins) + " " + str(blackWins) + " "
        notWins = str(stalemate) + " " + str(draw) + "\n"
        file.write(wins + notWins)

        
if __name__ == "__main__":
    searchers = (TreeStrapSearcher(), RandomSearcher())
    weightsNum = 0
    while True:
        train(1000, searchers[0])
        validate(searchers)
        weightsNum += 1
