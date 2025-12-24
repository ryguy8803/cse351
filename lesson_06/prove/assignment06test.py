"""
Course: CSE 351
Assignment: 06
Author: Rylan Hoogland

Instructions:

- see instructions in the assignment description in Canvas

""" 

import multiprocessing as mp
import os
import cv2
import numpy as np

from cse351 import *

# Folders
INPUT_FOLDER = "faces"
STEP1_OUTPUT_FOLDER = "step1_smoothed"
STEP2_OUTPUT_FOLDER = "step2_grayscale"
STEP3_OUTPUT_FOLDER = "step3_edges"

# Parameters for image processing
GAUSSIAN_BLUR_KERNEL_SIZE = (5, 5)
CANNY_THRESHOLD1 = 75
CANNY_THRESHOLD2 = 155

# Allowed image extensions
ALLOWED_EXTENSIONS = ['.jpg']

#Processes ----------------------------------------------------------------------------------------------------------
NUM_SMOOTHING_PROCESSES = 4
NUM_GRAYSCALE_PROCESSES = 4
NUM_EDGE_DETECT_PROCESSES = 4

# Global variable for termination signal
ALL_DONE = "ALL_DONE"

# ---------------------------------------------------------------------------
def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")

# ---------------------------------------------------------------------------
def task_convert_to_grayscale(image):
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        return image # Already grayscale
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# ---------------------------------------------------------------------------
def task_smooth_image(image, kernel_size):
    return cv2.GaussianBlur(image, kernel_size, 0)

# ---------------------------------------------------------------------------
def task_detect_edges(image, threshold1, threshold2):
    if len(image.shape) == 3 and image.shape[2] == 3:
        print("Warning: Applying Canny to a 3-channel image. Converting to grayscale first for Canny.")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] != 1 : # Should not happen with typical images
        print(f"Warning: Input image for Canny has an unexpected number of channels: {image.shape[2]}")
        return image # Or raise error
    return cv2.Canny(image, threshold1, threshold2)

# ---------------------------------------------------------------------------
def process_images_in_folder(input_folder,              # input folder with images
                             output_folder,             # output folder for processed images
                             processing_function,       # function to process the image (ie., task_...())
                             load_args=None,            # Optional args for cv2.imread
                             processing_args=None):     # Optional args for processing function

    create_folder_if_not_exists(output_folder)
    print(f"\nProcessing images from '{input_folder}' to '{output_folder}'...")

    processed_count = 0
    for filename in os.listdir(input_folder):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue

        input_image_path = os.path.join(input_folder, filename)
        output_image_path = os.path.join(output_folder, filename) # Keep original filename

        try:
            # Read the image
            if load_args is not None:
                img = cv2.imread(input_image_path, load_args)
            else:
                img = cv2.imread(input_image_path)

            if img is None:
                print(f"Warning: Could not read image '{input_image_path}'. Skipping.")
                continue

            # Apply the processing function
            if processing_args:
                processed_img = processing_function(img, *processing_args)
            else:
                processed_img = processing_function(img)

            # Save the processed image
            cv2.imwrite(output_image_path, processed_img)

            processed_count += 1
        except Exception as e:
            print(f"Error processing file '{input_image_path}': {e}")

    print(f"Finished processing. {processed_count} images processed into '{output_folder}'.")

# ---------------------------------------------------------------------------
# Worker Functions
# ---------------------------------------------------------------------------

def smooth_worker(input_queue, output_queue, kernel_size):
    """Worker to perform Gaussian smoothing."""
    create_folder_if_not_exists(STEP1_OUTPUT_FOLDER)
    while True:
        item = input_queue.get()
        if item == ALL_DONE:
            # Propagate termination signal to the next stage
            output_queue.put(ALL_DONE) 
            break
        
        filename, image = item
        
        # 1. Process
        processed_img = task_smooth_image(image, kernel_size)
        
        # 2. Save intermediate result
        output_path = os.path.join(STEP1_OUTPUT_FOLDER, filename)
        cv2.imwrite(output_path, processed_img)
        
        # 3. Pass to next stage
        output_queue.put((filename, processed_img))

def grayscale_worker(input_queue, output_queue):
    """Worker to convert image to grayscale."""
    create_folder_if_not_exists(STEP2_OUTPUT_FOLDER)
    while True:
        item = input_queue.get()
        if item == ALL_DONE:
            # Propagate termination signal to the next stage
            output_queue.put(ALL_DONE) 
            break

        filename, image = item

        # 1. Process
        processed_img = task_convert_to_grayscale(image)

        # 2. Save intermediate result
        output_path = os.path.join(STEP2_OUTPUT_FOLDER, filename)
        cv2.imwrite(output_path, processed_img)

        # 3. Pass to next stage
        output_queue.put((filename, processed_img))

def edge_detect_worker(input_queue, threshold1, threshold2, output_folder):
    """Worker to perform Canny edge detection and save the final result."""
    create_folder_if_not_exists(output_folder)
    while True:
        item = input_queue.get()
        if item == ALL_DONE:
            break  # Final stage, no need to signal further

        filename, image = item

        # 1. Process
        processed_img = task_detect_edges(image, threshold1, threshold2)

        # 2. Save final result
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, processed_img)

# ---------------------------------------------------------------------------
def run_image_processing_pipeline():
    print("Starting image processing pipeline...")

    # --- Setup ---
    # Create Queues
    q1 = mp.Queue()  # Input_Files -> Smooth
    q2 = mp.Queue()  # Smooth -> Grayscale
    q3 = mp.Queue()  # Grayscale -> Edge Detect
    
    # Create processes
    smooth_processes = []
    for _ in range(NUM_SMOOTHING_PROCESSES):
        p = mp.Process(target=smooth_worker, args=(q1, q2, GAUSSIAN_BLUR_KERNEL_SIZE))
        smooth_processes.append(p)
    
    grayscale_processes = []
    for _ in range(NUM_GRAYSCALE_PROCESSES):
        p = mp.Process(target=grayscale_worker, args=(q2, q3))
        grayscale_processes.append(p)
        
    edge_processes = []
    for _ in range(NUM_EDGE_DETECT_PROCESSES):
        p = mp.Process(target=edge_detect_worker, 
                         args=(q3, CANNY_THRESHOLD1, CANNY_THRESHOLD2, STEP3_OUTPUT_FOLDER))
        edge_processes.append(p)

    all_processes = smooth_processes + grayscale_processes + edge_processes

    # Start all worker processes
    for p in all_processes:
        p.start()
    
    # --- Main Process: Load Images and seed the pipeline (q1) ---
    files = [f for f in os.listdir(INPUT_FOLDER) 
             if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS]
    
    for filename in files:
        input_image_path = os.path.join(INPUT_FOLDER, filename)
        img = cv2.imread(input_image_path) # Default to BGR for initial load
        
        if img is not None:
            # Put (filename, image_data) tuple onto the first queue
            q1.put((filename, img))
        
    # Send ALL_DONE signals to terminate the smoothing workers
    for _ in range(NUM_SMOOTHING_PROCESSES):
        q1.put(ALL_DONE)
    
    # Wait for all workers to finish.
    for p in all_processes: 
        p.join()

    print("\nImage processing pipeline finished!")
    print(f"Original images are in: '{INPUT_FOLDER}'")
    print(f"Smoothed images are in: '{STEP1_OUTPUT_FOLDER}'")
    print(f"Grayscale images are in: '{STEP2_OUTPUT_FOLDER}'")
    print(f"Edge images are in: '{STEP3_OUTPUT_FOLDER}'")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log = Log(show_terminal=True)
    log.start_timer('Processing Images')

    # check for input folder
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The input folder '{INPUT_FOLDER}' was not found.")
        print(f"Create it and place your face images inside it.")
        print('Link to faces.zip:')
        print('   https://drive.google.com/file/d/1eebhLE51axpLZoU6s_Shtw1QNcXqtyHM/view?usp=sharing')
    else:
        run_image_processing_pipeline()

    log.write()
    log.stop_timer('Total Time To complete')