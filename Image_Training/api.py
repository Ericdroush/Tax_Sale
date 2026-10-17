from fastapi import FastAPI, UploadFile
import torch
from PIL import Image
import io
from transforms import train_tfms, val_tfms

app = FastAPI()
model = PropertyScorer().to(device)
model.load_state_dict(torch.load("property_scorer.pt"))
model.eval()

@app.post("/score")
async def score(street: UploadFile, map: UploadFile):
    street_img = Image.open(io.BytesIO(await street.read())).convert("RGB")
    map_img = Image.open(io.BytesIO(await map.read())).convert("RGB")

    street_t = val_tfms(street_img).unsqueeze(0).to(device)
    map_t = val_tfms(map_img).unsqueeze(0).to(device)

    with torch.no_grad():
        score = model(street_t, map_t).item()

    return {"score": round(score, 2)}
