import sys
import os

# Add the project root directory to the system path so that 'model' and 'data_loader' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'ml')))

import torch
from tqdm import tqdm
import os
import io

from ml.model import build_model
from ml.data_loader import get_dataloaders

# ------------------------------------------
# Training Function
def train_model(epochs=10, lr=1e-4, save_path="models/best_model.pt"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model, criterion, optimizer = build_model(lr=lr, device=device)
    train_loader, val_loader = get_dataloaders()

    best_val_acc = 0.0

    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")

        # Training phase
        model.train()
        train_loss, train_correct = 0.0, 0
        for images, labels in tqdm(train_loader, desc="Training"):
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()

        train_acc = train_correct / len(train_loader.dataset)
        train_loss /= len(train_loader.dataset)

        # Validation phase
        model.eval()
        val_loss, val_correct = 0.0, 0
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc="Validating"):
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                val_correct += (outputs.argmax(1) == labels).sum().item()

        val_acc = val_correct / len(val_loader.dataset)
        val_loss /= len(val_loader.dataset)

        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"Val   Loss: {val_loss:.4f}, Val   Acc: {val_acc:.4f}")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(model.state_dict(), save_path)

            print(f"Best model saved to: {save_path}")
            print("Saving to:", os.path.abspath(save_path))

    print("Training complete.")

# ------------------------------------------
# Run standalone
if __name__ == "__main__":
    train_model()
