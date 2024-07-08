from fastapi import APIRouter, File, Form, status, UploadFile
from fastapi.responses import JSONResponse
from db.firestore import (
    get_labels_by_lecture_id,
    get_lecture_by_id,
    get_lectures as fb_get_lectures,
    upload_file_to_storage,
    create_lecture,
    create_label,
)
from utils.labels_to_dict import labels_to_dict
from keras.utils import get_file
from utils.get_exercices import get_exercices
from keras.models import load_model
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO
from typing import Optional
import json
from models.label import Label, BaseLabel
from pydantic import ValidationError

router = APIRouter()


@router.get("/")
def get_lectures():
    lectures = fb_get_lectures()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=lectures,
    )


@router.post("/")
async def post_lecture(
    title: str = Form(...),
    labels: str = Form(...),
    model: Optional[UploadFile] = File(None),
    icon: UploadFile = File(None),
):
    labels_list = json.loads(labels)
    try:
        [BaseLabel(**item) for item in labels_list]
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

    icon_url = None
    try:
        icon_url = await upload_file_to_storage(icon)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to upload file", "error": str(e)},
        )

    try:
        lecture = {"title": title, "iconUrl": icon_url}
        if model_url:
            lecture["modelUrl"] = model_url
        lecture = create_lecture(lecture)

        for label in labels_list:
            label["lectureId"] = lecture.id
            create_label(label)

        response_data = {
            "id": lecture.id,
            "title": lecture.title,
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


@router.post("/{lecture_id}/predict")
def predict(lecture_id, file: bytes = File(...), expected_label: str = Form(...)):
    lecture = get_lecture_by_id(lecture_id)

    if lecture is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Lecture not found"},
        )

    labels = get_labels_by_lecture_id(lecture_id)

    if len(labels) == 0:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Labels not found to given lecture"},
        )

    labels_dict = labels_to_dict(labels)

    if expected_label not in labels_dict.values():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Label not found"},
        )

    model_path = get_file(lecture["id"], lecture["modelUrl"])

    model = load_model(model_path)

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    image = Image.open(BytesIO(file)).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.LANCZOS)

    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array

    prediction = model.predict(data)

    result = np.argmax(prediction[0])

    predicted_label = labels_dict[result]

    if predicted_label == expected_label:
        confidence = prediction[0][result] * 100
        is_correct = bool(confidence > 50)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"correct": is_correct, "confidence": confidence},
        )

    index = list(labels_dict.values()).index(expected_label)
    confidence = prediction[0][index] * 100
    is_correct = bool(confidence > 50)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"correct": is_correct, "confidence": confidence},
    )


@router.get("/{lecture_id}/exercices")
def exercices(lecture_id):
    lecture = get_lecture_by_id(lecture_id)

    if lecture is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Lecture not found"},
        )

    labels = get_labels_by_lecture_id(lecture["id"])

    if len(labels) == 0:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Labels not found to given lecture"},
        )

    exercices = get_exercices(lecture, labels)

    return JSONResponse(status_code=200, content=exercices)
