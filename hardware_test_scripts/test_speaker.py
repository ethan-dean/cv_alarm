import pygame

# Initialize Pygame mixer
pygame.mixer.init()

# Load a sound file (replace 'test_sound.wav' with the path to your file)
sound_file = 'alarms/alarm1.mp3'
try:
    sound = pygame.mixer.Sound(sound_file)
    print("Sound file loaded successfully!")
except pygame.error as e:
    print(f"Failed to load sound file: {e}")
    exit(1)

# Play the sound
print("Playing sound...")
sound.play()

# Wait for the sound to finish playing
while pygame.mixer.get_busy():
    pass

print("Sound playback finished!")
