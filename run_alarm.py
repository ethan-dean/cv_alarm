import time
import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models

def load_custom_shufflenet(model_path, num_classes=2):
    """
    Loads a pre-trained ShuffleNet model and applies the saved weights
    for a 2-class classification (in_bed / not_in_bed).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load a pre-trained ShuffleNet
    model = models.shufflenet_v2_x1_0(weights=None)  # we'll load our custom weights, so pretrained=False
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    # Load the saved weights
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()  # set to eval mode for inference

    return model, device

def open_camera():
    """
    Opens camera with a specific backend based on OS, which greatly improves runtime of
    cv2.VideoCapture() function.
    """
    # Detect the operating system
    if sys.platform == 'win32':
        # Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    elif sys.platform == 'darwin':
        # macOS
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    elif sys.platform.startswith('linux'):
        # Linux
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    else:
        # Fallback if we can’t detect or don’t have a known backend
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
    return cap

def main():
    # -----------------------------
    # 1. Load the fine-tuned model
    # -----------------------------
    pretrained_model_path = os.path.abspath("models/shufflenet_pretrained_weights.pth")
    model, device = load_custom_shufflenet(pretrained_model_path, num_classes=2)

    # Class names based on folder order in your training data
    # e.g., if your ImageFolder had subfolders in the order [in_bed, not_in_bed],
    # you can define:
    class_names = ["in_bed", "not_in_bed"]

    # -----------------------------
    # 2. Initialize webcam capture
    # -----------------------------
    cap = open_camera()

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # -----------------------------
    # 3. Define transforms for input
    # -----------------------------
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # same size as training
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    print("Press 'q' to quit the process...")
    try:
        # Initialize pygame mixer
        pygame.mixer.init()

        # Load your 30-second sound
        pygame.mixer.music.load(os.path.abspath("alarms/alarm1.mp3"))

        # Start playback in a loop (-1 means infinite loop),
        # then pause immediately so we can unpause when needed
        pygame.mixer.music.play(-1)
        pygame.mixer.music.pause()

        # Track alarm state and count of repeated predictions
        alarm_paused = True
        repeated_prediction_count = 0

        # Run alarm for an hour
        start_time = time.time()
        one_hour = 3600
        while time.time() - start_time < one_hour:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read frame from webcam.")
                break

            # Convert BGR (OpenCV) to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL-like image 
            # 1) Convert numpy array to a PyTorch tensor
            import torchvision.transforms.functional as F
            frame_pil = F.to_pil_image(frame_rgb)
            # 2) Transform (resize, normalize, etc.)
            input_tensor = transform(frame_pil)

            # Add batch dimension
            input_tensor = input_tensor.unsqueeze(0).to(device)

            # Forward pass
            with torch.no_grad():
                outputs = model(input_tensor)  # shape: [1, 2]
            
            # Predicted class
            _, predicted = torch.max(outputs, 1)
            pred_class_idx = int(predicted.item())
            pred_class_name = class_names[pred_class_idx]

            # Print the prediction
            cv2.putText(frame, f"Prediction: {pred_class_name}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow('Webcam Feed', frame)

            # Check for quit signal
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Exiting...")
                break

            # Update prediction count
            if alarm_paused:
                if pred_class_name == "in_bed":
                    repeated_prediction_count += 1
                else:
                    repeated_prediction_count = 0
            else: # NOT alarm_paused
                if pred_class_name == "not_in_bed":
                    repeated_prediction_count += 1
                else:
                    repeated_prediction_count = 0

            # Update alarm state
            if repeated_prediction_count >= 3:
                if alarm_paused:
                    # Unpause to resume where we left off.
                    pygame.mixer.music.unpause()
                    alarm_paused = False
                elif not alarm_paused:
                    # Pause playback.
                    pygame.mixer.music.pause()
                    alarm_paused = True

            # Sleep for 1 second to capture one frame per second
            time.sleep(1)
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
