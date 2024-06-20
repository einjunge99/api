from firebase_admin import firestore, storage
from fastapi import UploadFile
from models.lecture import BaseLecture, Lecture
from models.label import BaseLabel, Label


def create_label(label: BaseLabel) -> Label:
    db = firestore.client()
    label_ref = db.collection("lectures")
    label_ref = label_ref.add(label.dict())
    label_with_id = Label(
        id == label_ref[1].id, label=label.label, url=label.url, value=label.value
    )
    return label_with_id


def create_lecture(lecture: BaseLecture) -> Lecture:
    db = firestore.client()
    lectures_ref = db.collection("lectures")
    lectures_ref = lectures_ref.add(lecture.dict())
    lecture_with_id = Lecture(
        id == lectures_ref[1].id, title=lecture.id, modelUrl=lecture.modelUrl
    )
    return lecture_with_id


def get_lectures():
    db = firestore.client()
    lectures_ref = db.collection("lectures")
    docs = lectures_ref.stream()
    lectures = []

    for doc in docs:
        lecture_data = doc.to_dict()
        lecture_data["id"] = doc.id
        lectures.append(lecture_data)

    return lectures


def get_user_by_id(user_id: str):
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()
    if user.exists:
        return user.to_dict()
    return None


def get_lecture_by_id(lecture_id: str):
    db = firestore.client()
    lecture_ref = db.collection("lectures").document(lecture_id)
    lecture = lecture_ref.get()
    if lecture.exists:
        updated_lecture = lecture.to_dict()
        updated_lecture["id"] = lecture.id
        return updated_lecture
    return None


def get_labels_by_lecture_id(lecture_id: str):
    db = firestore.client()

    labels_ref = db.collection("labels")

    query = labels_ref.where("lectureId", "==", lecture_id).get()

    labels = []

    for label in query:
        label_data = label.to_dict()
        label_data["id"] = label.id
        labels.append(label_data)

    return labels


async def upload_file_to_storage(file: UploadFile):
    try:
        file_contents = await file.read()

        bucket = storage.bucket()
        blob = bucket.blob(file.filename)
        blob.upload_from_string(file_contents, content_type=file.content_type)

        blob.make_public()
        file_url = blob.public_url

        return file_url
    except Exception as e:
        raise e
