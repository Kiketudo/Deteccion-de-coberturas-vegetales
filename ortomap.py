import os
from PIL import Image
import torch
import rioxarray
import numpy as np
import shutil
import tifffile
from modelos.U_Net.model import UNetResnet
from modelos.U_Net import eval as UnetEval
from modelos.W_Net import eval as WnetEval
from modelos.Clustering import demo
band_to_indice = {'B':0,'G':1,'R':2,'RE':3,'NIR':4,'thermal':5}

class orthoseg():
    def __init__(self,
                    output_ortho_file = 'ortho_mask.tif',
                    temp_folder     = 'temp',
                    sub_image_size  = (416,512), 
                    device          = 'cuda', 
                    thresh          = 0.5,
                    bands = {'R':True,'G':True,'B':True,'NIR':False,'RE':False}
                    ):
        
       
        # Load file 
        self.format = 'tiff'
        self.bands_idx = [band_to_indice[key] for key,value in bands.items() if value == True]
        # Split orthomosaic into sub-images
        self.sub_image_size = sub_image_size # image size of the sub images 
        self.temp_folder    = temp_folder #  path to the temp folder
        self.sub_img_dir    = os.path.join(temp_folder,'sub_img')
        self.sub_mask_dir   = os.path.join(temp_folder,'sub_masks')
        self.sub_img_list   = [] # array with the sub_image names 
        self.path_to_save_ortho_mask = output_ortho_file
        self.device = device

        self.width  = -1
        self.height = -1

    def ortho_splitting(self,array):
            '''
            Splitting the orthomosaic into sub_images which are saved in a temp folder

            INPUT: 
                numpy array containing orthomosaic
            OUTPUT:
                list with all subimage file names

            '''

            # delete tmp file if it exist
            if os.path.isdir(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                print("[WAN] Directory deleted: %s"%(self.temp_folder))

            #if not os.path.isdir(self.sub_img_dir):
                # create a new directory to save sub_images
            os.makedirs(self.sub_img_dir)
            print("[WRN] New directory created: " + self.sub_img_dir)

            #if not os.path.isdir(self.sub_mask_dir):
            os.makedirs(self.sub_mask_dir)
            print("[WRN] New directory created: " + self.sub_mask_dir)

            sub_img_list = [] 

            target_height = self.sub_image_size[0]
            target_width  = self.sub_image_size[1]

            width  = self.width
            height = self.height
            
            array = array.transpose(1,2,0)

            max_itr = height
            #bar = progressbar.ProgressBar(max_value=max_itr)  
            h_itr= 0
            w_itr= 0
            while(h_itr < height):
                # reset width counter 
                #bar.update(h_itr) 
                w_itr = 0
                while(w_itr < width):
                    # Sub-image name + absolute path 
                    #sub_img_path = os.path.join(self.sub_img,"%05d_%05d.png"%(h_itr,w_itr))
                    sub_img_name = "%05d_%05d"%(h_itr,w_itr)
                    sub_img_list.append(sub_img_name)
                    # crop sub-image
                    sub_array = array[h_itr:h_itr+target_height,w_itr:w_itr+target_width,:]
                    # Save image
                    sub_img_path = os.path.join(self.sub_img_dir,sub_img_name+'.'+self.format)
                    tifffile.imwrite(sub_img_path, sub_array)
                    # Next width iteration
                    w_itr = w_itr + target_width
                # Next height iteration
                h_itr = h_itr + target_height

            return(sub_img_list)

    def load_ortho(self, path_to_file):
            '''
            Load orthomosaic to memory. 
            INPUT: 
                path_to_file: absolute path to file with tif 
            OUTPUT:
                numpy array representing the orthomosaic

            ''' 

            if not os.path.isfile(path_to_file): 
                print("[ERROR] File does not exist: " + path_to_file)
                return(-1)
            
            raster = rioxarray.open_rasterio(path_to_file)
            #array = np.array(raster.values)
            self.width  = raster.rio.width 
            self.height = raster.rio.height 
            raster = raster.values[self.bands_idx,:,:]
            return(raster)
    def rebuild_ortho_mask(self,files):
            #hacer múltiplos
            altura=round((self.height+self.sub_image_size[0]-1)/self.sub_image_size[0])*self.sub_image_size[0]
            anchura=round((self.width+self.sub_image_size[1]-1)/self.sub_image_size[1])*self.sub_image_size[1]
            raster_mask = np.zeros((altura,anchura),dtype=np.uint8)
            print(raster_mask.shape)
            root = self.sub_mask_dir
            #bar = progressbar.ProgressBar(max_value=len(prediction)) 
            for i,(file) in enumerate(files):
                # file name parser
                file_path = os.path.join(root,file+'.tiff')
                pred_mask = np.asarray(Image.open(file_path).convert('L'))
                ph,pw = parse_name(file)
                print(pred_mask.shape)
                if len(pred_mask.shape)> 2:
                    pred_mask = pred_mask.squeeze()
                h,w = pred_mask.shape
                lh,hh,lw,hw = ph,ph+h,pw,pw+w
                print(lh,hh,lw,hw)
                raster_mask[lh:hh,lw:hw] = pred_mask
            
            shutil.rmtree(self.sub_mask_dir)
            print("[WAN] Directory deleted: %s"%(self.sub_mask_dir))
            shutil.rmtree(self.sub_img_dir)
            print("[WAN] Directory deleted: %s"%(self.sub_img_dir))
            return(raster_mask)

    def pipeline(self,path,option):
            raster = self.load_ortho(path)
            # Splitting
            print("[INF] Ortho splitting")
            sub_img_list = self.ortho_splitting(raster)
            # Segmentation network
            print("[INF] Segmentation")
            self.segmentation(sub_img_list,option)
            # rebuild orthomask path_to_save_mask_raster,path_to_ortho,path_to_masks
            print("[INF] Rebuilding")
            # path_to_save_mask_ortho = os.path.join(path_to_file,'ortho_mask.tif')
            ortho = self.rebuild_ortho_mask(sub_img_list)
            img = Image.fromarray(ortho.astype(np.uint8))
            img = img.convert('RGB')
            img = img.crop((0,0,self.width,self.height))

            #img.save("output_file"+'.png')
            print("[INF] Finished")
            return(img)
    def segmentation(self,sub_img_list,option):
        '''
        Semenatic segmentation of sub-images

        INPUT: 
            [list] of image files

        '''

        for i,file in enumerate(sub_img_list):
            img_path = os.path.join(self.sub_img_dir,file+'.'+self.format)
            mask_img = select(option,img_path)
            mask_path = os.path.join(self.sub_mask_dir,file + '.' + self.format)
            mask_img.save(mask_path)
            # mpimg.imsave(os.path.join(self.sub_mask_dir,file),img_mask)

def select(option,route):
    match option:
        case 'opcion1':
            return UnetEval.evaluar(route)
        case 'opcion2':
            return WnetEval.evaluar(route)
        case 'opcion3':
            return demo.main(route)
def parse_name(file):
        h,w = file.split('_')
        return(int(h),int(w))
# if __name__ == '__main__':
#     orto = orthoseg()
#     path=r'E:\imagenes_memoria\Task-of-2024-01-22T150108374Z-orthophoto.tif'
#     orto.pipeline(path,'opcion1')