"""
MNIST Template
==============
Use this template to bootstrap your models.

You can use this model in two ways:

Research use
------------
For research, it's recommended you define the dataloaders inside
the Lightning Module.

Fit as follows

.. code-block:: python

    import pytorch_lightning as pl
    from pl_bolts.models import LitMNISTModel
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser = LitMNISTModel.add_model_specific_args(parser)
    args = parser.parse_args()

    # model
    model = LitMNISTModel(hparams=args)

    # train
    trainer = pl.Trainer()
    trainer.fit(model)

    # when  training completes you can  run test set
    trainer.test()

Production  use
---------------
If you want to use this for production, feature extractor or similar use,
then it makes sense to define the datasets outside of the LightningModule.

.. code-block:: python

    import os
    import pytorch_lightning as pl
    from pl_bolts.models import LitMNISTModel
    from argparse import ArgumentParser
    from torchvision.datasets import MNIST
    from torch.utils.data import DataLoader, random_split
    from torchvision import transforms

    parser = ArgumentParser()
    parser = LitMNISTModel.add_model_specific_args(parser)
    args = parser.parse_args()

    # model
    model = LitMNISTModel(hparams=args)

    # Train / val split
    train_dataset = MNIST(os.getcwd(), train=True, download=True, transform=transforms.ToTensor())
    mnist_train, mnist_val = random_split(train_dataset, [55000, 5000])

    train_loader = DataLoader(mnist_train, batch_size=args.batch_size)
    val_loader = DataLoader(mnist_val, batch_size=args.batch_size)

    # test split
    mnist_test = MNIST(os.getcwd(), train=False, download=True, transform=transforms.ToTensor())
    test_loader = DataLoader(mnist_test, batch_size=args.batch_size)

    trainer = pl.Trainer()
    trainer.fit(model, train_dataloader=train_loader, val_dataloaders=val_loader)

    # when  training completes you can  run test set
    trainer.test(test_dataloaders=test_loader)

"""
import os
from argparse import ArgumentParser

import torch
from pytorch_lightning import LightningModule, Trainer
from torch.nn import functional as F
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from torchvision.datasets import MNIST


class LitMNISTModel(LightningModule):
    def __init__(self, hidden_dim=128, learning_rate=1e-3, batch_size=32, num_workers=4, data_dir=''):
        super().__init__()
        self.save_hyperparameters()

        self.l1 = torch.nn.Linear(28 * 28, self.hparams.hidden_dim)
        self.l2 = torch.nn.Linear(self.hparams.hidden_dim, 10)

        self.mnist_train = None
        self.mnist_val = None

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = torch.relu(self.l1(x))
        x = torch.relu(self.l2(x))
        return x

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = F.cross_entropy(y_hat, y)
        tensorboard_logs = {'train_loss': loss}
        progress_bar_metrics = tensorboard_logs
        return {
            'loss': loss,
            'log': tensorboard_logs,
            'progress_bar': progress_bar_metrics
        }

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        return {'val_loss': F.cross_entropy(y_hat, y)}

    def validation_epoch_end(self, outputs):
        avg_loss = torch.stack([x['val_loss'] for x in outputs]).mean()
        tensorboard_logs = {'val_loss': avg_loss}
        progress_bar_metrics = tensorboard_logs
        return {
            'avg_val_loss': avg_loss,
            'log': tensorboard_logs,
            'progress_bar': progress_bar_metrics
        }

    def test_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        return {'test_loss': F.cross_entropy(y_hat, y)}

    def test_epoch_end(self, outputs):
        avg_loss = torch.stack([x['test_loss'] for x in outputs]).mean()
        tensorboard_logs = {'test_loss': avg_loss}
        progress_bar_metrics = tensorboard_logs
        return {
            'avg_test_loss': avg_loss,
            'log': tensorboard_logs,
            'progress_bar': progress_bar_metrics
        }

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)

    def prepare_data(self):
        MNIST(self.hparams.data_dir, train=True, download=True, transform=transforms.ToTensor())

    def train_dataloader(self):
        dataset = MNIST(self.hparams.data_dir, train=True, download=False, transform=transforms.ToTensor())
        mnist_train, _ = random_split(dataset, [55000, 5000])
        loader = DataLoader(mnist_train, batch_size=self.hparams.batch_size, num_workers=self.hparams.num_workers)
        return loader

    def val_dataloader(self):
        dataset = MNIST(self.hparams.data_dir, train=True, download=False, transform=transforms.ToTensor())
        _, mnist_val = random_split(dataset, [55000, 5000])
        loader = DataLoader(mnist_val, batch_size=self.hparams.batch_size, num_workers=self.hparams.num_workers)
        return loader

    def test_dataloader(self):
        test_dataset = MNIST(os.getcwd(), train=False, download=True, transform=transforms.ToTensor())
        loader = DataLoader(test_dataset, batch_size=self.hparams.batch_size, num_workers=self.hparams.num_workers)
        return loader

    @staticmethod
    def add_model_specific_args(parent_parser):
        parser = ArgumentParser(parents=[parent_parser], add_help=False)
        parser.add_argument('--batch_size', type=int, default=32)
        parser.add_argument('--num_workers', type=int, default=4)
        parser.add_argument('--hidden_dim', type=int, default=128)
        parser.add_argument('--data_dir', type=str, default='')
        parser.add_argument('--learning_rate', type=float, default=0.0001)
        return parser


if __name__ == '__main__':  # pragma: no cover

    # args
    parser = ArgumentParser()
    parser = LitMNISTModel.add_model_specific_args(parser)
    args = parser.parse_args()

    # model
    model = LitMNISTModel(**vars(args))

    trainer = Trainer()
    trainer.fit(model)
