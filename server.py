import json
from io import BytesIO
from typing import List, Optional

import firebase_admin
import numpy as np
import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Response,
    status,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials, firestore, storage
from keras.models import load_model
from PIL import Image, ImageOps
from pydantic import BaseModel, Field, ValidationError

from utils.get_exercises import get_exercises
from utils.labels import gen_labels


cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(
    cred, {"storageBucket": "sign-language-learning.appspot.com"}
)

app = FastAPI()

# Configure CORS
origins = [
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:5173",  # Adjust this to match your frontend development server URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


class Label(BaseModel):
    label: str
    url: str
    value: Optional[int] = Field(None)


async def upload_file_to_storage(file: UploadFile):
    try:
        # Read file contents
        file_contents = await file.read()

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(file.filename)
        blob.upload_from_string(file_contents, content_type=file.content_type)

        # Make the file public and get its URL
        blob.make_public()
        file_url = blob.public_url

        print("file_url", file_url)

        return file_url  # Return only the file URL
    except Exception as e:
        raise e  # Raise the exception to be handled in the caller (FastAPI endpoint)


@app.get("/")
def hello_world():
    return "Hello World"


@app.post("/api/predict/{lecture_id}")
def predict(lecture_id, file: bytes = File(...), expected_label: str = Form(...)):
    # TODO: Add lecture_id validation
    labels = gen_labels(lecture_id)

    if expected_label not in labels.values():
        return {"correct": False, "error": "Invalid label"}

    model = load_model(f"./{lecture_id}/keras_model.h5")

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    image = Image.open(BytesIO(file)).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.LANCZOS)

    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array

    prediction = model.predict(data)

    result = np.argmax(prediction[0])

    predicted_label = labels[str(result)]

    print(f"Predicted: {predicted_label}, Expected: {expected_label}")

    if predicted_label == expected_label:
        confidence = prediction[0][result] * 100
        if confidence > 50:
            return {"correct": True, "confidence": confidence}
        return {"correct": False, "confidence": confidence}

    index = list(labels.values()).index(expected_label)
    confidence = prediction[0][index] * 100

    if confidence > 50:
        return {"correct": True, "confidence": confidence}
    return {"correct": False, "confidence": confidence}


@app.get("/api/exercises/{lecture_id}")
def exercises(lecture_id):
    db = firestore.client()
    lecture_ref = db.collection("lectures").document(lecture_id)
    _lecture = lecture_ref.get()

    if _lecture.exists:
        lecture = _lecture.to_dict()
        lecture["id"] = _lecture.id
    # TODO: validate if lecture exists

    print(lecture)

    _labels = [
        label
        for label in db.collection("labels")
        .where("lectureId", "==", lecture_id)
        .stream()
    ]

    labels = []

    if len(_labels) == 0:
        # TODO: throw error...
        print("empty")
        # return exercices

    for label in _labels:
        labels.append(label.to_dict())

    exercises = get_exercises(lecture, labels)

    print(exercises)

    return JSONResponse(status_code=200, content=exercises)


@app.get("/api/lectures/")
def get_lectures():
    db = firestore.client()
    docs = db.collection("lectures").stream()

    lectures = []

    for doc in docs:
        lecture = doc.to_dict()
        lectures.append(lecture)

    return lectures
    # return sorted(lectures, key=lambda d: d["order"])


@app.post("/api/lectures/")
async def post_lecture(
    title: str = Form(...),
    labels: str = Form(...),
    model: Optional[UploadFile] = File(None),
):

    labels_list = json.loads(labels)
    try:
        [Label(**item) for item in labels_list]
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid labels data format", "error": str(e.errors())},
        )

    model_url = None
    if model:
        try:
            model_url = await upload_file_to_storage(model)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": "Failed to upload file", "error": str(e)},
            )

    try:
        db = firestore.client()
        lecture_data = {"title": title}
        if model_url:
            lecture_data["modelUrl"] = model_url

        lecture_ref = db.collection("lectures").add(lecture_data)
        lecture_id = lecture_ref[1].id

        for label in labels_list:
            label["lectureId"] = lecture_id
            db.collection("labels").add(label)

        response_data = {
            "id": lecture_id,
            "title": title,
            "labels": labels_list,
        }

        if model_url:
            response_data["modelUrl"] = model_url

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to process request", "error": str(e)},
        )


@app.get("/api/lectures/{user_id}")
def get_lectures(user_id):
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()

    completed_lectures = []

    if user.exists:
        completed_lectures = user.to_dict().get("completedLectures", [])

    docs = db.collection("lectures").stream()

    lectures = []

    for doc in docs:
        lecture = doc.to_dict()
        lecture["isCompleted"] = doc.id in completed_lectures
        lecture["uid"] = doc.id
        lectures.append(lecture)

    return lectures
    # return sorted(lectures, key=lambda d: d["order"])


@app.patch("/api/user/{user_id}/{lecture_id}")
def add_completed_lecture(user_id, lecture_id):
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)

    if not user_ref.get().exists:
        return {"error": "User not found"}

    user_ref.update({"completedLectures": firestore.ArrayUnion([lecture_id])})

    return {"success": True}


@app.get("/api/user/{user_id}")
def get_user_info(user_id):
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()

    if not user.exists:
        return {"error": "User not found"}

    return user.to_dict()


def get_user_token(
    res: Response,
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer realm="auth_required"'},
        )
    try:
        decoded_token = auth.verify_id_token(credential.credentials)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication from Firebase. {err}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    res.headers["WWW-Authenticate"] = 'Bearer realm="auth_required"'
    return decoded_token


class TokenRequest(BaseModel):
    idToken: str


@app.get("/api/verify-token")
async def verify_token(authentication_user=Depends(get_user_token)):
    db = firestore.client()
    user_ref = db.collection("users").document(authentication_user["uid"])
    _user = user_ref.get()

    if not _user.exists:
        return {"error": "User not found"}

    user = _user.to_dict()

    if user.get("role") is None or user.get("role") != "admin":
        return JSONResponse(status_code=403, content={"message": "User not authorized"})

    # TODO: return all user info
    return JSONResponse(status_code=200, content={"message": "authorized"})


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
