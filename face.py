import psutil
import time
import tkinter as tk
import os
import subprocess
from pathlib import Path
import random
from PIL import Image, ImageTk

faces_path = str(Path(__file__).parent) + "/images/faces"
phonemes_path = str(Path(__file__).parent) + "/images/phonemes"

def is_audio_playing():
    output = subprocess.check_output(["pw-cli", "ls", "Node"], text=True)
    if "aplay" in output:
        return True
    else:
        return False


format_size = "1000x700"
img_faces = {}
img_phonemes = {}

# Initialize Tkinter
parent = tk.Tk()
parent.geometry(format_size)
parent.title("Avatar Animation")

# load emotions images
for file in os.listdir(faces_path):
    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        percorso = os.path.join(faces_path, file)
        img = Image.open(percorso)
        img = img.resize((1000, 700))
        img_photoimage = ImageTk.PhotoImage(img)
        img_faces[file] = img_photoimage

#phonemes
for file in os.listdir(phonemes_path):
    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        percorso = os.path.join(phonemes_path, file)
        img = Image.open(percorso)
        img = img.resize((1000, 700))
        img_photoimage = ImageTk.PhotoImage(img)
        img_phonemes[file] = img_photoimage
        
image_label = tk.Label(parent)
image_label.pack()

def talking():
    for name in img_phonemes.keys():
        image_label.configure(image=img_phonemes[name])
        parent.update() 
        time.sleep(0.1)
        

def listening():
    #UPDATE CONTROLLED EMOTIONS WITH ACTIONS!
    r = random.randint(1,500)
    
    if r==1:
        image_label.configure(image=img_faces["annoyed.png"])
        parent.update()
        time.sleep(1)
    else:    
        image_label.configure(image=img_faces["happy.png"])
        parent.update()
    
# Main loop
def main_loop():
    try:
        if is_audio_playing():
            print("talking")
            talking()
        else:
            listening()
        parent.after(50, main_loop)

    except Exception as e:
        print(f"Error in main loop: {e}")
        parent.after(50, main_loop)  

# Start the main loop
main_loop()

# Start Tkinter event loop
parent.mainloop()