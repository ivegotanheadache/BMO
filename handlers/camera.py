import cv2
import subprocess
import time
import os
import json
from ultralytics import YOLO
from pathlib import Path

BASEPATH = Path(__file__).parent.parent 

def capture_frame():
    framepath = f'{BASEPATH}/video/frame.jpg'
    subprocess.run([
        'rpicam-still',
        '-o', framepath,
        '--width', '320',
        '--height', '320',
        '-t', '1',
        '--nopreview'
    ], capture_output=True, check=False)
    

    time.sleep(0.2)
    
 
    if os.path.exists(framepath):
        frame = cv2.imread(framepath)
        return frame
    
    return None

def run_video(queue):
    #
    try:
        model_objects = YOLO(f"{BASEPATH}/video/yolo11n_object365_ncnn_model")
        print("Modello YOLO caricato")
    except Exception as e:
        print(f"Errore caricamento modello: {e}")
        return
    
    old_results = []  
    
    while True:
        try:
            frame = capture_frame()
            
            if frame is None:
                time.sleep(1)
                continue
            
            
            results = model_objects(frame, conf=0.3, verbose=False)
            detected_objects = []
            
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    label = model_objects.names[cls_id]
                    detected_objects.append(label)
            
            """
            if "Person" in detected_objects:
                results_face = model_face(frame, verbose=False)
                print(results_face)
                for r in results_face:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        label = model_face.names[cls_id]
                        detected_faces.append(label)
            """ 
            
            if old_results != detected_objects:            
                #print(f"camera packet {detected_objects}")
                queue.put(detected_objects)  # Invia lista, non JSON
                old_results = detected_objects
            
        except Exception as e:
            print(f"Errore nel loop video: {e}")
        
        time.sleep(1)