from PIL import Image
import torch
import torch.utils.data as Data
import os
import glob
import numpy as np
import pdb
from modelos.W_Net.configure import Config
import math
import cupy as cp

config = Config()

class DataLoader():
    #initialization
    #datapath : the data folder of bsds500
    #mode : train/test/val
    def __init__(self, file_name,mode):
        self.raw_data = []
        self.mode = mode
        
        with Image.open(file_name) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")
            self.raw_data.append(np.array(image.resize((config.inputsize[0],config.inputsize[1]),Image.BILINEAR)))
        #resize and align
        self.scale()
        #normalize
        self.transfer()
        
        #calculate weights by 2
        self.dataset = self.get_dataset(self.raw_data, self.raw_data.shape,75)
    
    def scale(self):
        for i in range(len(self.raw_data)):
            image = self.raw_data[i]
            self.raw_data[i] = np.stack((image[:,:,0],image[:,:,1],image[:,:,2]),axis = 0)
        self.raw_data = np.stack(self.raw_data,axis = 0)

    def transfer(self):
        #just for RGB 8-bit color
        self.raw_data = self.raw_data.astype(np.cfloat)
        #for i in range(self.raw_data.shape[0]):
        #    Image.fromarray(self.raw_data[i].swapaxes(0,-1).astype(np.uint8)).save("./reconstruction/input_"+str(i)+".jpg")

    def torch_loader(self):
        return Data.DataLoader(
                                self.dataset,
                                batch_size = config.BatchSize,
                                shuffle = config.Shuffle,
                                num_workers = config.LoadThread,
                                pin_memory = True,
                            )

    def get_dataset(self,raw_data,shape,batch_size):
        dataset = []
        for batch_id in range(0,shape[0],batch_size):
            print(batch_id)
            batch = raw_data[batch_id:min(shape[0],batch_id+batch_size)]
            dataset.append(Data.TensorDataset(torch.from_numpy(batch/256).float()))
        return Data.ConcatDataset(dataset)



