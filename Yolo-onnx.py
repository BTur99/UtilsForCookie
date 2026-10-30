from ultralytics import YOLO

model = YOLO("best3.pt")
model.export(format="onnx", opset=12, simplify=True)