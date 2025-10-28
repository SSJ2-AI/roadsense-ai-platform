# Model Weights Placeholder

Place the pothole YOLOv8 weight file here as `pothole_yolov8n.pt`.

Download instructions (source: FarzadNekouee YOLOv8 Pothole Segmentation/Road Damage Assessment):
- Repository: https://github.com/FarzadNekouee/YOLOv8_Pothole_Segmentation_Road_Damage_Assessment
- Download the pre-trained YOLOv8n pothole model weights and save as `backend/models/pothole_yolov8n.pt`.

Operational guidance:
- Store production weights in a private Artifact Registry or Cloud Storage bucket.
- During CI/CD, mount or download to `/app/models/pothole_yolov8n.pt` inside the container.
- Avoid committing weights to git to control repository size and licensing.
