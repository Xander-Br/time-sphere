import os
import time
from datetime import datetime


import bcrypt
from fastapi import FastAPI, Query, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pymongo import MongoClient
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

app = FastAPI()
client = MongoClient(
    'mongodb+srv://doadmin:9c43u0Vd876E2SRH@db-mongodb-fra1-00555-517d35a7.mongo.ondigitalocean.com/admin?tls=true&authSource=admin')
db = client["db"]
capsuleCollection = db["capsule"]
capsuleCollection.create_index([("location", "2dsphere")])

userCollection = db["capsule"]

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)


class User(BaseModel):
    username: str
    password: str




class Capsule(BaseModel):
    username: str
    location: dict = Field(..., example={"type": "Point", "coordinates": [0.0, 0.0]})
    created_at: Optional[datetime] = datetime.now()
    unlock_at: Optional[datetime] = None
    data_img_src: Optional[str] = None
    data_text: str
    friends: Optional[list]



def authenticate_user(username: str, password: str):
    user = userCollection.find_one({"username": username})
    try:
        if not user:
            return None
        if not password != user["password"]:
            return None
    except:
        return None
    return user


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
        text: str = Form(...),
        longitude: float = Form(...),
        latitude: float = Form(...),
        unlock_at: datetime = Form(...),
        img: UploadFile = File(...),
):
    location_dict = {"type": "Point", "coordinates": [longitude, latitude]}

    img_path, filename = await save_image(img)
    img_url = f"/static/{filename}"

    user_data = {
        "username": username,
        "location": location_dict,
        "created_at": datetime.now(),
        "unlock_at": unlock_at,
        "img_src": img_url,
        "text": text,
    }

    result = capsuleCollection.insert_one(user_data)
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
    for doc in capsuleCollection.find(query):
        doc["_id"] = str(doc["_id"])
        documents.append(doc)

    return documents


@app.post("/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        user_data = {"username": username, "password": password}

        result = userCollection.insert_one(user_data)
        if result:
            user = {"_id": str(result.inserted_id), "username": username}
            return {"status": "success", "message": "User created and authenticated", "user": user}

        user = {"_id": str(user["_id"]), "username": user["username"]}
        return {"status": "success", "message": "User authenticated", "user": user}
