# Credits to James

import os
import json
import base64
import subprocess

global page_id
page_id = None

def save_base64_image(base64_string, filename):
    """Decodes a base64 image string and saves it as a file."""
    try:
        header, encoded = base64_string.split(",", 1)  # Split header and encoded data
        img_data = base64.b64decode(encoded)  # Decode base64
        with open(filename, "wb") as img_file:
            img_file.write(img_data)
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def process_json(json_path):
    """Reads JSON file, finds base64 images, and saves them with a sequential filename."""
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    img_counter = 0
    img_dir = ".yumevalidator/current_fi/extracted_images"
    os.makedirs(img_dir, exist_ok=True)  # Create directory for images

    def extract_and_save(obj, key, path="root"):
        nonlocal img_counter
        if isinstance(obj, dict):
            for k, v in obj.items():
                current_path = f"{path}.{k}"
                # Check if the value is a base64-encoded PNG image
                if k == key and isinstance(v, str) and v.startswith("data:image/png;base64,"):
                    filename = os.path.join(img_dir, f"image_{img_counter}.png")
                    save_base64_image(v, filename)
                    print(f"Found image at: {current_path}, saved as: {filename}")
                    img_counter += 1
                else:
                    extract_and_save(v, key, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_and_save(item, key, f"{path}[{i}]")

    # Look for the base64 image data in fields named "url"
    extract_and_save(data, "url")
    print(f"Total images saved: {img_counter}")
    # Move the images to another location
    new_img_dir = f".yumevalidator/diff_{page_id}.png"
    os.makedirs(new_img_dir, exist_ok=True)
    for img_file in os.listdir(img_dir):
        if img_file == "image_2.png":
            src_path = os.path.join(img_dir, img_file)
            dst_path = os.path.join(new_img_dir, img_file)
            os.rename(src_path, dst_path)
            break
    print(f"Images moved to: {new_img_dir}")
    

def diff_img(new_page_id):
    """
    Compare the image of the page with the image of the page in the previous commit
    """
    global page_id

    install_scoopy = subprocess.Popen(["npm", "install", "-g", "@animaapp/scooby-cli"])
    install_scoopy.wait()

    fidelity_generator = subprocess.Popen(["scooby", "fidelity", "--name", "\".yumevalidator/current_fi\"", "--expected", f".yumevalidator/expected", "--actual", f".yumevalidator/actual", "--file-type=png"])
    fidelity_generator.wait()
    subprocess.run(["unzip", ".yumevalidator/current_fi.zip", "-d", ".yumevalidator/current_fi"])
    process_json(".yumevalidator/current_fi/report.json")
    page_id = new_page_id

    pass

def main():
    diff_img("1:247")