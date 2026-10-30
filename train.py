from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model.train(
    data='dataset/data.yaml', 
    epochs=150,
    imgsz=640,
    batch=16,                
    workers=4,           
    device=0,               
    name='cookie_detector',
    patience=50
)