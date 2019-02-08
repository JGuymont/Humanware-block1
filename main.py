"""
Starting point for training the models
"""
import os
import argparse
from datetime import datetime
from configparser import ConfigParser

import torch
from torch.utils.data import DataLoader
from torchvision import transforms

from utils.data import SVHNDataset
from trainer import Trainer


def argparser():
    """
    Configure the command-line arguments parser

    :return: the arguments parsed
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str)
    parser.add_argument('--train_metadata_path',
                        type=str,
                        default='./data/SVHN/metadata/train_metadata.pkl')
    parser.add_argument('--valid_metadata_path',
                        type=str,
                        default='./data/SVHN/metadata/valid_metadata.pkl')
    parser.add_argument('--test_metadata_path',
                        type=str,
                        default='./data/SVHN/metadata/test_metadata.pkl')
    parser.add_argument('--data_dir', type=str, default='./data/SVHN/train')
    parser.add_argument('--train_pct', type=float, default=0.7)
    parser.add_argument('--valid_pct', type=float, default=0.2)
    parser.add_argument('--test_pct', type=float, default=0.1)

    parser.add_argument('--num_classes', type=int, default=5)
    parser.add_argument('--n_epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--crop_percent', type=float, default=0.3)
    parser.add_argument('--optim', type=str, default='SGD')
    parser.add_argument('--device', type=str, default='cpu')

    return parser.parse_args()


if __name__ == '__main__':
    args = argparser()
    conf = ConfigParser()
    conf.read(args.config)
    conf.set('model', 'device', 'cuda' if torch.cuda.is_available() else 'cpu')

    train_transforms = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.RandomCrop(54),
        # Resize to input size for pretrained SENet
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.39954964, 0.3988817, 0.41280591],
                             [0.23269807, 0.2355513, 0.23580605])
    ])

    test_transforms = transforms.Compose([
        # Resize to input size for pretrained SENet
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.39954964, 0.3988817, 0.41280591],
                             [0.23269807, 0.2355513, 0.23580605])
    ])

    train_data = SVHNDataset(
        metadata_path=conf.get("paths", "train_metadata"),
        data_dir=conf.get("paths", "data_dir"),
        crop_percent=conf.getfloat("preprocessing", "crop_percent"),
        transform=train_transforms)

    valid_data = SVHNDataset(
        metadata_path=conf.get("paths", "valid_metadata"),
        data_dir=conf.get("paths", "data_dir"),
        crop_percent=conf.getfloat("preprocessing", "crop_percent"),
        transform=test_transforms)

    test_data = SVHNDataset(
        metadata_path=conf.get("paths", "test_metadata"),
        data_dir=conf.get("paths", "data_dir"),
        crop_percent=conf.getfloat("preprocessing", "crop_percent"),
        transform=test_transforms)

    train_loader = DataLoader(train_data,
                              batch_size=conf.getint("model", "batch_size"),
                              shuffle=True,
                              num_workers=4,
                              pin_memory=True)
    dev_loader = DataLoader(valid_data,
                            batch_size=100,
                            num_workers=4,
                            pin_memory=True)
    test_loader = DataLoader(test_data,
                             batch_size=100,
                             num_workers=4,
                             pin_memory=True)

    datetime_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    conf.set("paths", "results", os.path.join(conf.get("paths", "results"),
                                              conf.get("model", "name"),
                                              datetime_str))
    os.makedirs(conf.get("paths", 'results'), exist_ok=True)

    conf.set("paths", "checkpoints",
             os.path.join(conf.get("paths", "checkpoints"),
                          conf.get("model", "name"),
                          datetime_str))
    os.makedirs(conf.get("paths", "checkpoints"), exist_ok=True)

    trainer = Trainer(conf)
    trainer.train_model(train_loader, dev_loader)
