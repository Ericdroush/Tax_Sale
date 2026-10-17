import torch
import torch.nn as nn
from torchvision import models

class PropertyScorer(nn.Module):
    def __init__(self):
        super().__init__()

        # Pretrained backbones
        self.street_cnn = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        self.map_cnn = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

        # Remove classification heads
        self.street_cnn.fc = nn.Identity()
        self.map_cnn.fc = nn.Identity()

        embedding_dim = 2048 * 2

        self.regressor = nn.Sequential(
            nn.Linear(embedding_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 1)   # regression output
        )

    def forward(self, street_img, map_img):
        street_feat = self.street_cnn(street_img)
        map_feat = self.map_cnn(map_img)

        combined = torch.cat([street_feat, map_feat], dim=1)
        score = self.regressor(combined)

        return score.squeeze(1)
