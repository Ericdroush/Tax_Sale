import os
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset

class PropertyDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.labels = pd.read_csv(os.path.join(root_dir, 'labels.csv'))
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        row = self.labels.iloc[idx]
        taxmap = row['taxmap']
        rating = float(row['rating'])

        street_path = os.path.join(self.root_dir, 'StreetView',  f"{taxmap}.jpg")
        map_path = os.path.join(self.root_dir, 'MapView', f"{taxmap}.jpg")

        street_img = Image.open(street_path).convert("RGB")
        map_img = Image.open(map_path).convert("RGB")

        if self.transform:
            street_img = self.transform(street_img)
            map_img = self.transform(map_img)

        return street_img, map_img, rating
