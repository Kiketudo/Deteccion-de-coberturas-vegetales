import torch
import numpy as np
from modelos.W_Net.model import WNet
from modelos.W_Net.DataLoader import DataLoader
import time
import os
import torchvision
import pdb
from PIL import Image
checkpoint='modelos\W_Net\checkpoint_11_7_21_58_epoch_1000'
color_lib = []
for r in range(0,256,128):
    for g in range(0,256):
        for b in range(0,256,128):
            color_lib.append((r,g,b))
def evaluar(imagen):
    dataset = DataLoader(imagen,"test")
    dataloader = dataset.torch_loader()
    model = WNet()
    model.cuda()
    model.eval()
    #optimizer
    with open(checkpoint,'rb') as f:
        para = torch.load(f,"cuda:0")
        model.load_state_dict(para['state_dict'])
        #model.load_state_dict('checkpoint_11_7_21_58_epoch_1000')
    for [x] in dataloader:
                          
        x = x.cuda()
        pred,pad_pred = model(x)
        seg = (pred.argmax(dim = 1)).cpu().detach().numpy()
        x = x.cpu().detach().numpy()*255
        x = np.transpose(x.astype(np.uint8),(0,2,3,1))
        color_map = lambda c: color_lib[c]
        cmap = np.vectorize(color_map)
        seg = np.moveaxis(np.array(cmap(seg)),0,-1).astype(np.uint8)
    return Image.fromarray(seg[0,:,:])


        
