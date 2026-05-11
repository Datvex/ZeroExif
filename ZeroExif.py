import sys
from PIL import Image

def remove_all_metadata(input_path, output_path):
    with Image.open(input_path) as img:
        pixel_data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(pixel_data)
        clean_img.save(output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_image> <output_image>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        remove_all_metadata(input_file, output_file)
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")
