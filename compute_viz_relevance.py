
from captum.attr._core.neuron.neuron_integrated_gradients import NeuronIntegratedGradients
from captum.attr._core.layer.layer_integrated_gradients import LayerIntegratedGradients
from captum.attr._core.integrated_gradients import IntegratedGradients
from captum.attr import visualization as vizu
import matplotlib.pyplot as plt

from visualize_layers import  VisualizeLayers
from  utility import Utility
from probe_model import probe_model
import numpy as np 
import torch
import torchvision.transforms as transforms
import torchvision
from dataloader import classLoader

def revelence_score_pipeline (x,mask,model,layer):
    '''
    Args:
    Input  : X     : input data in batch fashion. dimension (b*c*h*w)
             Mask  : Coresponding mask for each image samples. (b*h*w)
             Model : The Model. 
             Layer : The layer for which the relevance scores need to calculated. 
    OUTPUT :
            Raw Relevance attribution for entire layer. size 4D array (batch *Units * LayerInputSize)
            Maked (with ROI annotation) Relevance attribution for entire layer. size 4D array (batch *Units * LayerInputSize)
            Average Relevance score for each Neurons. size equivalent to number of units    
    '''
    #x.to("cuda")
    #Get the prediction 
    out=model(x)
    max_val, preds = torch.max(out,dim=1)

    #Initiate layer IG object
    layer_ig=LayerIntegratedGradients(model,layer)

    # get the activation for selected layer 
    attribution=layer_ig.attribute(x,target=preds,attribute_to_layer_input=True)
    attribution=attribution.detach().squeeze(0).numpy()
    
    #Resize the attribution 
    attribution=Utility.resize_IG_batch(attribution)
    
    #Apply the mask on the IG map 
    masked_attribution= np.copy(attribution)
    for img in range(attribution.shape[0]):
        for unit in range(attribution.shape[1]):
            masked_attribution[img,unit,:,:]=np.multiply(masked_attribution[img,unit,:,:],mask[img,:,:])

    #calculate the relevance score per unit 
    relevance_score =np.sum(np.sum(abs(masked_attribution),axis=3),axis=2)
    
    return attribution,masked_attribution,relevance_score

def model_eval(x,model,label):
   
    y=torch.ones([x.shape[0]])*label
    #transfer the data to GPU 
    x=x.to("cuda")
    y=y.to("cuda")
    
    out =model(x)
    
    max_val, preds = torch.max(out,dim=1)
    
    total = x.shape[0]                 
    correct = (preds == y).sum().item()
    accuracy = (100 * correct)/total

    return accuracy

if  __name__ == "__main__":
    
   # Get the data and annotation mask 
    dataset_path='D:\\Net\\NetDissect\\dataset\\broden1_227'
    clLoader=classLoader(dataset_path)
   
    #Get the model
    '''
    Remember to switch  the full(float32) computation mode by setting the 
    2nd argument to False for non Residual networks.(e.g. ALexnet ,VGG) 
    '''
    prober=probe_model(False)
    model=prober.get_model()
    
    #Get the layers 
    '''
    Remember to change the 2nd argument to False for non Residual networks.(e.g. ALexnet ,VGG) 
    '''
    vis=VisualizeLayers(model,True)
    names=vis.get_saved_layer_names()
    layer=vis.conv_layers[names[10]]

    # Dog=93 ,cat=105.mosque=1062,hen=830
    class_selector =168
    imagenet_label=908
    sample_count   = clLoader.get_length(class_selector)
    iterations     =int( np.floor(sample_count/100) )
    list_batch_relevance_score=[]
    accuracy=0
    for i in range(3):
        
        x,mask=clLoader.load_batch(class_selector,100)

        for i in range(x.shape[0]):
            plt.imshow (np.transpose(x[i,:,:,:].detach().numpy(),(1,2,0)))
            plt.colorbar()
            plt.show()
            plt.imshow(mask[i,:,:])
            plt.show()        
      
        acc=model_eval(x,model,imagenet_label)

        accuracy+=acc






        #Get relevance score 
        _,masked_attribution,batch_relevance_score=revelence_score_pipeline(x,mask,model,layer)

        #visualize the masked maps 
        # _ = vizu.visualize_image_attr(np.expand_dims(masked_attribution[:,10,:,:],axis=2),sign="absolute_value",
        #                 show_colorbar=True, title="IG")
        
        # #show many images 
        im_sample=1
        Utility.show_many_images((masked_attribution[im_sample,:,:,:]),36,False)
        
        # for i in range(5):
        #     plt.imshow ((masked_attribution[im_sample,i,:,:]))
        #     plt.colorbar()
        #     plt.show()
        list_batch_relevance_score.append (batch_relevance_score)
    
    relevance_score=np.vstack(list_batch_relevance_score)

    avg_relevance_score=np.average(relevance_score,axis=0)

    plt.hist(avg_relevance_score, bins=8, histtype='barstacked')
    plt.show()

        
        