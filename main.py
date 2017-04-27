from __future__ import print_function
import torch
import sys
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable

import os

from model import Segmenter
import dataset, arguments

from tools import model_io, index_map

# Training settings
model_dir = 'models'

args = arguments.get_arguments()

args.cuda = not args.no_cuda and torch.cuda.is_available()

torch.manual_seed(args.seed)
if args.cuda:
    torch.cuda.manual_seed(args.seed)

model = Segmenter(2)
if args.cuda:
    model.cuda()

optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)
train_loader, train_dataset = dataset.training(args)

def train(epoch):
    model.train()

    for batch_idx, (data, target) in enumerate(train_loader):
        if args.cuda:
            data, target = data.cuda(), target.cuda()

        data, target = Variable(data), Variable(target)
        optimizer.zero_grad()
        output = model(data)

        loss = F.nll_loss(output, target)


        if args.show_training:
            _, inds = output.data.cpu().max(1)
            inds = inds.byte().squeeze(1)

            overlay = index_map.overlay_batches(data.data.cpu(), inds)
            overlay.show()

            input("next:")


        loss.backward()
        optimizer.step()
        if batch_idx % args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_dataset),
                100. * batch_idx / len(train_loader), loss.data[0]))

# def test(epoch):
#     model.eval()
#     test_loss = 0
#     correct = 0
#     for data, target in test_loader:
#         if args.cuda:
#             data, target = data.cuda(), target.cuda()
#         data, target = Variable(data, volatile=True), Variable(target)
#         output = model(data)
#         test_loss += F.nll_loss(output, target).data[0]
#         pred = output.data.max(1)[1] # get the index of the max log-probability
#         correct += pred.eq(target.data).cpu().sum()
#
#     test_loss = test_loss
#     test_loss /= len(test_loader) # loss function already averages over batch size
#     print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
#         test_loss, correct, len(test_loader.dataset),
#         100. * correct / len(test_loader.dataset)))




start_epoch = 1

if args.load_model:
    epoch, state = model_io.load(model_dir)
    model.load_state_dict(state)

for epoch in range(start_epoch, start_epoch + args.epochs):

    train(epoch)
    state = (epoch, model.state_dict())

    model_io.save(model_dir, epoch, state)
