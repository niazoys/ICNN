from utility import Utility
from compute_iou import compute_iou
from probe_model import probe_model
from dataloader import conceptLoader
import numpy as np 
from visualize_layers import VisualizeLayers
from compute_qd import Compute_qd

if __name__ == "__main__":

        ###########################################
        #create object for model probe
        pm=probe_model(True)

        # create activation generator & visualizer object
        vis=VisualizeLayers(pm.get_model())
        
        # falg for hook tracking        
        existing_hook=False
            
        
        # Total data 
        total_data=60000
        #Batch Size
        batch_size=200
        #number of iteratio
        iteration=int((total_data/batch_size))

        # in how many parts we want to do the calculation (Must be even Number)
        part_ln=4
        
        ###########################################  

        #get the names of the layers in the network 
        layer_names=vis.get_saved_layer_names()

        for layer in layer_names:
            tk=[]
            #loop over all the convolutional layers  
            for part in range (1,part_ln+1):            
                print("Processing(Part " +str(part)+"):"+ layer)
                
                #check if there is already any hook attached and remove it 
                if existing_hook:
                    vis.remove_all_hooks()

                #attch hook for different cnn layers
                vis.hook_layers(layer)
                existing_hook=True

                #Generate tk 
                featuremap=pm.probe(iteration=iteration,batch_size=batch_size,vis=vis,layer=layer,part_ln=part_ln,part=part)

                print("Generating Tk")
                #Generate tk and save them
                for unit in range(featuremap.shape[1]):
                    tk.append(np.quantile(featuremap[:,unit,:,:],0.995))
                
                #clear the featuremap from memory 
                del featuremap
                
                #Reset the image loading counter to zero     
                pm.imLoader.data_counter=0
                gc.collect()
            
            # save TK matrix    
            np.save('TK/resnet18/tk_'+str(layer)+'.npy',tk)
                
