import torch
import torch.nn as nn
from torchvision import models

# ------------------------------------------
# Binary Classification Model
class DandelionGrassClassifier(nn.Module):
    def __init__(self, pretrained=True):
        super(DandelionGrassClassifier, self).__init__()
        self.model = models.resnet18(pretrained=pretrained)
        
        # Replace the final fully connected layer
        num_features = self.model.fc.in_features
        self.model.fc = nn.Linear(num_features, 2)  # 2 classes: dandelion, grass

    def forward(self, x):
        return self.model(x)

# ------------------------------------------
# Helper to initialize model, optimizer, loss
def build_model(lr=1e-4, pretrained=True, device=None):
    model = DandelionGrassClassifier(pretrained=pretrained)
    if device:
        model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    return model, criterion, optimizer
