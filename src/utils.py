import os
import re
import hydra
import torchvision
import numpy as np  
import pandas as pd
import seaborn as sn
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score, precision_score, f1_score
from sklearn.utils.multiclass import unique_labels
from torch.utils.tensorboard import SummaryWriter
from sklearn.neighbors import NearestNeighbors
import sys
sys.path.append('src')
from metrics import *
import cv2
import albumentations as A
import albumentations.pytorch as AP
import json


def get_early_stopping(cfg):
    """Returns an EarlyStopping callback
    cfg: hydra config
    """
    early_stopping_callback = EarlyStopping(
        monitor='val_loss',
        mode='min',
        patience=15,
    )
    return early_stopping_callback


def get_transformations(cfg):
    """Returns the transformations for the dataset
    cfg: hydra config
    """
    img_tranform = torchvision.transforms.Compose([
        torchvision.transforms.Resize(cfg.dataset.resize, antialias=True),
        torchvision.transforms.CenterCrop(cfg.dataset.resize),
        torchvision.transforms.ToTensor(),
    ])
    val_img_tranform, test_img_tranform = None, None

    train_img_tranform = torchvision.transforms.Compose([
        torchvision.transforms.Resize(cfg.dataset.resize, antialias=True),
        torchvision.transforms.CenterCrop(cfg.dataset.resize),
        torchvision.transforms.ToTensor(),
        torchvision.transforms.RandomHorizontalFlip(p=0.5),
        torchvision.transforms.RandomVerticalFlip(p=0.5),
        torchvision.transforms.RandomRotation(degrees=45),
        #torchvision.transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
        torchvision.transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.8, 1.2), shear=0),
    ])
    return train_img_tranform, val_img_tranform, test_img_tranform, img_tranform


'''def get_transformations(cfg):
    """Returns the transformations for the dataset
    cfg: hydra config
    """
    img_tranform = A.Compose([
        A.CLAHE(clip_limit=2.0, always_apply=True),
        A.Resize(cfg.dataset.resize, cfg.dataset.resize),
        A.CenterCrop(cfg.dataset.resize, cfg.dataset.resize),
        #A.ToFloat(),
        AP.transforms.ToTensorV2()
    ])
    val_img_tranform, test_img_tranform = None, None

    train_img_tranform = A.Compose([
        A.CLAHE(clip_limit=2.0, always_apply=True),
        A.ShiftScaleRotate(shift_limit=0.03, rotate_limit=20, border_mode=cv2.BORDER_CONSTANT, value=0, p=0.85), 
        A.OneOf([
            A.ElasticTransform(alpha=1, sigma=50, alpha_affine=10, 
                border_mode=cv2.BORDER_CONSTANT, value=0, p=0.5),
            A.GridDistortion(num_steps=5, distort_limit=0.1, 
                border_mode=cv2.BORDER_CONSTANT, value=0, p=0.5
        )], p=0.2),

        A.OneOf([
            A.GaussNoise(var_limit=(0.0001, 0.004), p=0.7),
            A.Blur(blur_limit=3, p=0.3)
        ], p=0.5),      
        A.Flip(p=0.5),
        A.Resize(cfg.dataset.resize, cfg.dataset.resize),
        A.CenterCrop(cfg.dataset.resize, cfg.dataset.resize),
        #A.ToFloat(),
        AP.transforms.ToTensorV2()
    ])

    return train_img_tranform, val_img_tranform, test_img_tranform, img_tranform
'''

def log_report(actual, predicted, classes, log_dir):
    """Logs the confusion matrix to tensorboard
    actual: ground truth
    predicted: predictions
    classes: list of classes
    log_dir: path to the log directory
    """
    writer = SummaryWriter(log_dir=log_dir)
    cf_matrix = confusion_matrix(actual, predicted)
    df_cm = pd.DataFrame(
        cf_matrix / np.sum(cf_matrix, axis=1)[:, None], 
        index=[i for i in classes],
        columns=[i for i in classes])
    plt.figure(figsize=(5, 4))
    img = sn.heatmap(df_cm, annot=True, cmap="Greens").get_figure()
    writer.add_figure("Confusion matrix", img, 0)

    # log metrics on tensorboard
    writer.add_scalar('Accuracy', accuracy_score(actual, predicted))
    writer.add_scalar('recall', recall_score(actual, predicted, average='micro'))
    writer.add_scalar('precision', precision_score(actual, predicted, average='micro'))
    writer.add_scalar('f1', f1_score(actual, predicted, average='micro'))
    writer.close()



def get_last_version(path):
    """Return the last version of the folder in path
    path: path to the folder containing the versions
    """
    folders = os.listdir(path)
    # get the folders starting with 'version_'
    folders = [f for f in folders if re.match(r'version_[0-9]+', f)]
    # get the last folder with the highest number
    last_folder = max(folders, key=lambda f: int(f.split('_')[1]))
    return last_folder  


def convert_arrays_to_integers(array1, array2):
    """
    Given two arrays of strings, return two arrays of integers
    such that the integers are a mapping of the strings.  If a
    string in array1 is not in array2, it is mapped to the next
    integer in the sequence.  If a string in array2 is not in
    array1, it is mapped to the next integer in the sequence.
    """
    string_to_int_mapping = {}
    next_integer = 0
    
    for string in array1:
        if string not in string_to_int_mapping:
            string_to_int_mapping[string] = next_integer
            next_integer += 1
    
    result_array1 = [string_to_int_mapping[string] for string in array1]
    result_array2 = [string_to_int_mapping.get(string, next_integer) for string in array2]
    return result_array1, result_array2

