# Model Weights Placeholder

Place YOLOv8 weight file here, e.g. `weights.pt`.

Operational guidance:
- Store production weights in a private Artifact Registry or Cloud Storage bucket.
- During CI/CD, mount or download to `/app/models/weights.pt` inside the container.
- Avoid committing weights to git to control repository size and licensing.
