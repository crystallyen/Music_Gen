import torch
import torch.nn as nn
import torch.optim as optimizer
from tqdm.auto import tqdm

device = 'cuda' if torch.cuda.is_available() else 'cpu'

class Model(nn.Module):
  def __init__(self,in_size,hidden_dim,out_notes):
    super().__init__()
    self.lstm1 = nn.LSTM(input_size=in_size,hidden_size=hidden_dim,num_layers=1,batch_first=True)
    self.norm = nn.LayerNorm(hidden_dim)
    self.drop = nn.Dropout(0.1)
    self.lstm2 = nn.LSTM(input_size=hidden_dim,hidden_size=hidden_dim,num_layers=1,batch_first=True)
    
    self.mlp = nn.Sequential(
      nn.Linear(hidden_dim,hidden_dim),
      nn.Dropout(0.1),
      nn.Linear(hidden_dim,out_notes)
    )
  def forward(self,input):
    x,_ = self.lstm1(input)
    x = self.norm(x)
    x = self.drop(x)
    x,_ = self.lstm2(x)
    x = self.mlp(x[:,-1,:])
    return x

out_notes = 263
model = Model(1,256,263).to(device)

loss_fn = nn.CrossEntropyLoss()
optimizer_fn = optimizer.Adam(model.parameters(),lr=0.0001)

#loading the data
features = torch.load('features.pth')
targets = torch.load('targets.pth')
features = features.unsqueeze(-1).to(device)
targets = targets.long().to(device)


split = 0.3 
X_train,X_test = features[:int(len(features)*0.7)],features[int(len(features)*0.7):]
y_train,y_test = targets[:int(len(features)*0.7)], targets[int(len(features)*0.7):]

epochs = 100
#training loop
losses = []
vald_loss = []
batch_size = 256
train_batches = len(X_train)//batch_size
test_batches = len(X_test)//batch_size

for epoch in range(epochs):
  running_loss = 0
  running_vald_loss = 0
  model.train()
  for i in tqdm(range(train_batches)):
      start = i * batch_size
      end = start + batch_size
      feature = X_train[start:end]
      target = y_train[start:end]
      
      logits = model(feature)
      loss = loss_fn(logits,target)
      running_loss += loss.item()
      
      optimizer_fn.zero_grad()
      loss.backward()
      optimizer_fn.step()
      
  losses.append(running_loss/train_batches)
  print(f"train loss after {epoch+1} is {running_loss/train_batches:.4f} ")
  torch.save(model.state_dict(),'model.pth')
  
  for i in tqdm(range(test_batches)):
      start = i * batch_size
      end = start + batch_size 
      feature = X_test[start:end]
      target = y_test[start:end]
      model.eval()
      with torch.no_grad():
        logits = model(feature)
      loss_vald = loss_fn(logits,target)
      running_vald_loss += loss_vald.item()
  vald_loss.append(running_vald_loss/test_batches)
  print(f"vald loss after {epoch+1} is {running_vald_loss/test_batches:.4f} ")
