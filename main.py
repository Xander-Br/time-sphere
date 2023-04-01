from datetime import datetime
from http.client import HTTPException

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional
from pymongo import MongoClient
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
client = MongoClient('mongodb+srv://doadmin:9c43u0Vd876E2SRH@db-mongodb-fra1-00555-517d35a7.mongo.ondigitalocean.com/admin?tls=true&authSource=admin')
db = client["db"]
collection = db["capsule"]
collection.create_index([("location", "2dsphere")])


class UserData(BaseModel):
    username: str
    location: dict = Field(..., example={"type": "Point", "coordinates": [0.0, 0.0]})
    created_at: Optional[datetime] = datetime.now()
    unlocked_at: Optional[datetime] = None
    data_img_src: str
    data_text: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create")
async def create_document(user_data: UserData):
    document = user_data.dict()
    result = collection.insert_one(document)
    if result:
        return {"status": "success", "message": "Document created", "id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=400, detail="Unable to create document")

@app.get("/")
async def get_documents_near_location(longitude: float = Query(..., description="Longitude of the center point"),
                                      latitude: float = Query(..., description="Latitude of the center point"),
                                      radius: float = Query(..., description="Radius in meters")):
    # Create a MongoDB $nearSphere query
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

    # Execute the query and fetch the results
    documents = []
    for doc in collection.find(query):
        doc["_id"] = str(doc["_id"])
        documents.append(doc)

    return documents
