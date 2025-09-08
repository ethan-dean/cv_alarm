import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

def train_shufflenet(
    data_dir,       # Path to your dataset folder
    batch_size,
    learning_rate,
    num_epochs,
    model_save_path
):
    """
    Fine-tunes a pre-trained ShuffleNet model on a custom 2-class dataset:
    'in_bed' and 'not_in_bed'.
    """

    # -----------------------------
    # 1. Setup Data Loaders
    # -----------------------------
    # Validation disabled by leaving ./dataset/val/in_bed and not_in_bed folders empty
    train_dir = os.path.abspath(os.path.join(data_dir, "train"))
    val_dir   = os.path.abspath(os.path.join(data_dir, "val")) 

    # Common image transforms for training
    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),     # Resize to 224x224 for ShuffleNet
        transforms.RandomHorizontalFlip(), # Augmentation
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),  # ImageNet stats
    ])

    # For validation, we typically avoid augmentations
    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    # Create Datasets
    train_dataset = datasets.ImageFolder(root=train_dir, transform=train_transforms)
    val_dataset   = datasets.ImageFolder(root=val_dir,   transform=val_transforms) if os.path.exists(val_dir) else None

    # Create DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader   = DataLoader(val_dataset,   batch_size=batch_size, shuffle=False, num_workers=2) if val_dataset else None

    # Number of classes should be 2: [in_bed, not_in_bed]
    num_classes = 2

    # -----------------------------
    # 2. Load Pre-Trained ShuffleNet
    # -----------------------------
    model = models.shufflenet_v2_x1_0(weights=models.ShuffleNet_V2_X1_0_Weights.DEFAULT)
    # For older versions of PyTorch (<= 2.0):
    # model = models.shufflenet_v2_x1_0(pretrained=True)

    # Replace the final FC layer (which by default outputs 1000 classes) with a 2-class layer
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # -----------------------------
    # 3. Define Loss and Optimizer
    # -----------------------------
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # -----------------------------
    # 4. Training Loop
    # -----------------------------
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Statistics
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc  = 100.0 * correct / total

        print(f"Epoch [{epoch+1}/{num_epochs}] - "
              f"Loss: {epoch_loss:.4f} - "
              f"Accuracy: {epoch_acc:.2f}%")

        if val_loader:
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            with torch.no_grad():
                for images, labels in val_loader:
                    images = images.to(device)
                    labels = labels.to(device)

                    outputs = model(images)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item() * images.size(0)
                    _, predicted = outputs.max(1)
                    val_correct += predicted.eq(labels).sum().item()
                    val_total += labels.size(0)

            val_loss /= val_total
            val_acc = 100.0 * val_correct / val_total
            print(f"  >> Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

    # -----------------------------
    # 5. Save the trained model
    # -----------------------------
    torch.save(model.state_dict(), model_save_path)
    print(f"Model saved to {model_save_path}")

if __name__ == "__main__":
    train_shufflenet(
        data_dir="dataset/",
        batch_size=16,
        learning_rate=1e-4,
        num_epochs=5,
        model_save_path="models/shufflenet_pretrained_weights.pth"
    )
