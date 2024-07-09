from firebase_admin import firestore, storage
from fastapi import UploadFile
from models.lecture import Lecture
from models.label import Label
import uuid


def create_label(label) -> Label:
    db = firestore.client()
    label_ref = db.collection("labels")
    label_ref = label_ref.add(label)
    label_with_id = Label(
        id=label_ref[1].id,
        label=label["label"],
        url=label["url"],
        value=label.get("value", None),
    )
    return label_with_id


def create_lecture(lecture) -> Lecture:
    db = firestore.client()
    lectures_ref = db.collection("lectures")
    lecture["createdAt"] = firestore.SERVER_TIMESTAMP
    lectures_ref = lectures_ref.add(lecture)
    lecture_with_id = Lecture(
        id=lectures_ref[1].id,
        title=lecture["title"],
    )
    return lecture_with_id


def update_lecture(lecture_id, updated_fields):
    db = firestore.client()
    lecture_ref = db.collection("lectures").document(lecture_id)
    lecture_ref.update(updated_fields)

    updated_lecture = lecture_ref.get().to_dict()
    return updated_lecture


def delete_lecture(lecture_id):
    db = firestore.client()
    lecture_ref = db.collection("lectures").document(lecture_id)
    lecture_ref.delete()


def get_lectures():
    db = firestore.client()
    lectures_ref = db.collection("lectures").order_by("createdAt")
    docs = lectures_ref.stream()
    lectures = []

    for doc in docs:
        lecture_data = doc.to_dict()
        lecture_data.pop("createdAt")  # TODO: serialize dates
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


async def upload_file_to_storage(file: UploadFile, prefix=None):
    if prefix is None:
        prefix = uuid.uuid4()
    try:
        file_contents = await file.read()

        bucket = storage.bucket()
        unique_filename = f"{str(prefix)}_{file.filename}"
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(file_contents, content_type=file.content_type)

        blob.make_public()
        file_url = blob.public_url

        return file_url
    except Exception as e:
        raise e
