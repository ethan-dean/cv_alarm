import cv2
import time
import os

def collect_images(
    output_folder,
    base_filename,
    num_images, 
    interval_sec
):
    """
    Captures `num_images` pictures from the webcam every `interval_sec` seconds 
    and saves them in `output_folder` as base_filename1.jpg, base_filename2.jpg, ...
    """
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Starting image collection for folder: {output_folder}")
    print(f"Will capture {num_images} images, every {interval_sec} seconds...")
    print("Press 'q' to quit early (window must be in focus).")

    try:
        for i in range(num_images):
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read from webcam.")
                break

            # Show preview window
            cv2.imshow("Press 'q' to quit early", frame)
            
            # Save the image
            filename = f"{base_filename}{i+1}.jpg"
            filepath = os.path.join(output_folder, filename)
            cv2.imwrite(filepath, frame)
            print(f"Saved: {filepath}")

            # Wait for 1ms to see if 'q' is pressed to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quitting early...")
                break

            # Wait for the interval (2 seconds by default) before taking next picture
            time.sleep(interval_sec)

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Uncomment one of the two lines below, depending on which set you want to collect:

    # Collect images of "in_bed"
    time.sleep(10);
    collect_images(
        output_folder="dataset/train/in_bed",
        base_filename="bed",
        num_images=100,
        interval_sec=2
    )

    # Collect images of "not_in_bed"
    # collect_images(
    #     output_folder="dataset/train/not_in_bed",
    #     base_filename="bed",
    #     num_images=100,
    #     interval_sec=2
    # )
