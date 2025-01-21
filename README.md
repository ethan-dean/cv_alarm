# CV Alarm
A computer vision–based morning alarm system

## Purpose
Ever snooze your alarm in the morning, or turn it off just to crawl back into bed? **CV Alarm** uses your webcam and a deep-learning model to detect if you’re still in bed and keeps the alarm going until you actually get up and stay up. This way, you can’t just hit snooze and fall back asleep!

## Summary of Features
- **Custom Dataset Collection**: Easily gather images with `collect_images.py`, storing them in label folders.
- **Model Training**: Fine-tune a pre-trained ShuffleNet using `train_shufflenet.py` on images from your own specific use case.
- **Live Inference with Alarm**: A script that loads the trained model, activates your webcam, and continuously classifies whether or not you’re in bed. If you are, it plays an alarm sound. If you get up, it pauses/stops the alarm.
- **One-Second Intervals**: Processes live video data from your webcam every second, saving on resources.
- **Modular Design**: Easy to adapt or extend. Plug in different alarm sounds or incorporate more sophisticated classification.

## Project Structure
Below is an example of how you might organize the files in your project:

```bash
cv_alarm/ 
├── alarms/
│ ├── alarm1.mp3 # Your alarm sound (30s or longer)
│ └── # more alarms...
├── models/ 
│ ├── shufflenet_pretrained_weights.pth
│ └── # more models... 
├── dataset/
│ ├── train/
│ │ ├── in_bed/
│ │ └── not_in_bed/
│ └── val/ (optional)
│   ├── in_bed/ 
│   └── not_in_bed/
├── capture_images.py # Script to capture images for your dataset 
├── fine_tune_model.py # Script to fine-tune ShuffleNet on your dataset 
├── run_alarm.py # Script to set off alarm based on live images 
└── README.md 
```

## Required Packages
Make sure you have the following installed (via `pip install ...` or `conda install ...`):
- **torch** (pytorch::pytorch)
- **torchvision** (pytorch::torchvision)
- **opencv-python** (conda-forge::opencv)
- **pygame** (conda-forge::pygame)

## How to Use It
1. **Collect Images**  
   - Run `capture_images.py` twice—once while you’re in bed (saving to `dataset/train/in_bed`), and once while you’re not in bed (saving to `dataset/train/not_in_bed`).  
   - This will give you images in each folder, which become your training data.
   - Variables to account for (you want as much of a mix of these as possible):
        - Lighting of room
        - Sheets, comforter, or blanket on top
        - Design/color of sheets
        - Position laying in bed
        - Color of clothes being worn 

2. **Train the Model**  
   - Run `python fine_tune_model.py` to fine-tune ShuffleNet on your dataset.  
   - After training, you’ll have something like `shufflenet_pretrained_weights.pth` in your `models/` folder.

3. **Set Up the Alarm Script**  
   - Place your alarm audio (e.g., `alarm1.mp3`) in the `alarms/` folder.  
   - Make sure the script (e.g., `run_alarm.py`) points to the correct model path (in `models/`) and the correct alarm file in `alarms/`.

4. **Run the Live Alarm**  
   - Launch `python run_alarm.py`.  
   - Your webcam feed will appear. The script checks every second if you’re in bed or not. If you’re detected in bed, the alarm will play. If you remain out of bed long enough, the alarm pauses.

5. **Adjust & Customize**  
   - Change the alarm conditions (e.g., how many consecutive frames classify you as “in bed” before playing the alarm).  
   - Tweak intervals, add more data, or switch to a different model if desired.

## Planned Future Updates
- [ ] PyQt Application to make setup more user friendly
- [ ] Allow easy switching between users alarms and models
- [ ] Test more efficient and accurate pretrained models other than shufflenet
- [ ] Research and test system on cheap mini-pc, webcam, and speakers
