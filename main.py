import os
import time
from datetime import datetime
from http.client import HTTPException
from fastapi import FastAPI, Query, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import Optional
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

app = FastAPI()
client = MongoClient('mongodb+srv://doadmin:9c43u0Vd876E2SRH@db-mongodb-fra1-00555-517d35a7.mongo.ondigitalocean.com/admin?tls=true&authSource=admin')
db = client["db"]
collection = db["capsule"]
collection.create_index([("location", "2dsphere")])

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

class UserData(BaseModel):
    username: str
    location: dict = Field(..., example={"type": "Point", "coordinates": [0.0, 0.0]})
    created_at: Optional[datetime] = datetime.now()
    unlocked_at: Optional[datetime] = None
    data_img_src: Optional[str] = None
    data_text: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def save_image(file: UploadFile):
    timestamp = int(time.time())
    name, ext = os.path.splitext(file.filename)
    name = name.replace(' ', '')
    filename = f"{name}_{timestamp}{ext}"

    file_location = os.path.join(STATIC_DIR, filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return file_location, filename

@app.post("/create")
async def create_document(
    username: str = Form(...),
    location: str = Form(...),
    data_text: str = Form(...),
    img: UploadFile = File(...),
):
    import json

    location_dict = json.loads(location)

    img_path, filename = await save_image(img)
    img_url = f"/static/{filename}"

    user_data = {
        "username": username,
        "location": location_dict,
        "created_at": datetime.now(),
        "unlocked_at": None,
        "data_img_src": img_url,
        "data_text": data_text,
    }

    result = collection.insert_one(user_data)
    if result:
        return {"status": "success", "message": "Document created", "id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=400, detail="Unable to create document")

@app.get("/static/{filename}")
async def get_image(filename: str):
    file_location = os.path.join(STATIC_DIR, filename)
    if os.path.exists(file_location):
        return FileResponse(file_location)
    else:
        raise HTTPException(status_code=404, detail="Image not found")

@app.get("/")
async def get_documents_near_location(longitude: float = Query(..., description="Longitude of the center point"),
                                      latitude: float = Query(..., description="Latitude of the center point"),
                                      radius: float = Query(..., description="Radius in meters")):
    query = {
        "location": {
            "$nearSphere": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "$maxDistance": radius
            }
        }
    }

    documents = []
    for doc in collection.find(query):
        doc["_id"] = str(doc["_id"])
        documents.append(doc)

    return documents