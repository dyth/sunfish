#!/usr/bin/env python
"""
Value Network based on Giraffe
"""
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np


class EvalNet(nn.Module):
    """
    Value Network Layers, Architecture and forward pass
    """
    def __init__(self):
        'initialise all the layers and activation functions needed'
        super(EvalNet, self).__init__()

        # three layers
        self.fc1 = nn.Linear(96, 1024)
        self.fc2 = nn.Linear(1024, 64)
        self.fc4 = nn.Linear(64, 2)

        # if cuda, use GPU
        self.use_gpu = torch.cuda.is_available()
        if self.use_gpu:
            self.cuda()
        
    def forward(self, inputLayer):
        'forward pass'
        out = F.relu(self.fc1(inputLayer))
        out = F.relu(self.fc2(out))
        out = F.tanh(self.fc4(out))
        return out

    
def set_piece_position_small(index, vector, f, r):
    'set normalised file, rank, 8-rank for a piece'
    while vector[index] != -1.0:
        index += 2
    # normalise values
    vector[index] = f / 8.0
    vector[index+1] = r / 8.0
    

def board_to_feature_vector(board):
    'promote to queen only, resulting in 144 length vector'
    # create {piece -> vectorposition} dictionary
    # {white, black} 8*Pawn, 2*Knight, 2*Bishop, 2*Rook, 9*Queen, 1*King
    pieces = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']
    count = [8, 2, 2, 2, 9, 1, 8, 2, 2, 2, 9, 1]
    countSum = [2 * sum(count[:i]) for i in range(len(count))]
    index = dict(zip(pieces, countSum))
    # create input vector for network
    inputVector = np.full(2*sum(count), -1.0)
    board = board[20:-20]
    for f in range(8):
        for r in range(8):
            square = board[(10*f) + r+1]
            # if occupied, set places in the vector
            if square != '.':
                set_piece_position_small(index[square], inputVector, f, r)
    return inputVector


def forward_pass(network, board):
    'do a forward pass of the network'
    x = torch.FloatTensor(board_to_feature_vector(board))
    if network.use_gpu:
        x = x.cuda()
    out = network(Variable(x)).data
    if network.use_gpu:
        out = out.cpu()
    return out.numpy()


def train_step(network, trainingPairs, LEARNING_RATE):
    'train network on data trainingPairs'
    optimizer = torch.optim.Adam(network.parameters(), lr=LEARNING_RATE)
    criterion = torch.nn.CrossEntropyLoss()
    
    for (board, value) in trainingPairs:
        inputs = Variable(torch.FloatTensor(board_to_feature_vector(board)))
        values = Variable(torch.FloatTensor(value), requires_grad=False)
        if network.use_gpu:
            inputs = inputs.cuda()
            values = values.cuda()

        #loss_fn = torch.nn.MSELoss(size_average=False)
        #loss = loss_fn(network(x), y)
        #optimizer.zero_grad()
        #loss.backward()
        #optimizer.step()
        #
        #running_loss = 0.0


        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = network(inputs)
        loss = criterion(outputs, values)
        loss.backward()
        optimizer.step()

        # print statistics
        #running_loss += loss.data[0]
        #if i % 2000 == 1999:    # print every 2000 mini-batches
        #    print('[%d, %5d] loss: %.3f' %
        #          (epoch + 1, i + 1, running_loss / 2000))
        #    running_loss = 0.0
            
    return network
