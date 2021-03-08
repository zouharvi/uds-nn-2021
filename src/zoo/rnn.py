import torch
import torch.nn as nn
from utils import DEVICE

class ModelRNN(nn.Module):
    def __init__(self, type, bidirectional, num_layers, embd_size, classes_count, hidden_dim=None):
        nn.Module.__init__(self)
        if hidden_dim == None:
            hidden_dim = classes_count+1
        if type == "rnn":
            self.unit = nn.RNN(
                input_size=embd_size,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                bidirectional=bidirectional
            )
        elif type == "lstm":
            self.unit = nn.LSTM(
                input_size=embd_size,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                bidirectional=bidirectional
            )
        elif type == "gru":
            self.unit = nn.GRU(
                input_size=embd_size,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                bidirectional=bidirectional
            )
        if bidirectional:
            self.linear = nn.Linear(2*hidden_dim, classes_count)
        else:
            self.linear = nn.Linear(hidden_dim, classes_count)
        self.f = nn.Softmax(dim=1)
        self.to(DEVICE)
        self.lr = 0.01

    def forward(self, x):
        lstm_out, _ = self.unit(x.view(len(x), 1, -1))
        tag_space = self.linear(lstm_out.view(len(x), -1))
        tag_scores = self.f(tag_space)
        return tag_scores

    def evaluate(self, test):
        self.eval()
        matches = 0
        total = 0
        for x, y in test:
            x = torch.stack(x, dim=0).float().to(DEVICE)
            y = torch.ShortTensor(y).to(DEVICE)
            yhat = self(x).argmax(dim=1)

            matches += torch.sum(torch.eq(yhat, y))
            total += y.shape[0]
        return matches/total

    def fit(self, dataTrain, dataDev, epochs):
        print("epoch\tloss\tacc")
        print(f'    0\tNaN\t{self.evaluate(dataDev)*100:>5.3f}%')

        loss_fn = nn.NLLLoss()
        opt = torch.optim.Adam(self.parameters(), lr=self.lr)
        for epoch in range(epochs):
            epoch += 1
            self.train(True)

            for x, y in dataTrain:
                x = torch.stack(x, dim=0).float().to(DEVICE)
                y = torch.LongTensor(y).to(DEVICE)
                pred = self(x)
                lossTrain = loss_fn(pred, y)
                lossTrain.backward(retain_graph=True)
                opt.step()
                opt.zero_grad()

            print(
                f'{epoch:>5}',
                f'{lossTrain.to("cpu").item():>5.3f}',
                f'{self.evaluate(dataDev)*100:>5.2f}%',
                sep="\t"
            )