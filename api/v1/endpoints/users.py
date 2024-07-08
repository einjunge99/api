from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
from core.dependencies import get_firestore_client
from firebase_admin import firestore
from db.firestore import get_user_by_id, get_lectures
from utils.get_user_token import get_user_token

router = APIRouter()


@router.get("/verify-token")
async def verify_token(authentication_user=Depends(get_user_token)):
    user = get_user_by_id(authentication_user["uid"])

    if user is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "User not found"}
        )

    if user.get("role") is None or user.get("role") != "admin":
        return JSONResponse(status_code=403, content={"message": "User not authorized"})

    return JSONResponse(status_code=200, content=user)


@router.get("/{user_id}")
def get_user_info(user_id):
    user = get_user_by_id(user_id)

    if user is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "User not found"}
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=user)


@router.patch("/{user_id}/completed-lectures")
def add_completed_lecture(
    user_id,
    lecture_id: dict = Body(...),
    db: firestore.Client = Depends(get_firestore_client),
):
    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()
    if user.exists:
        user_ref.update({"completedLectures": firestore.ArrayUnion([lecture_id])})
        updated_user = user_ref.get()
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=updated_user.to_dict()
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "User not found"}
        )


@router.get("/{user_id}/lectures")
def get_user_lectures(user_id):
    lectures = get_lectures()
    user = get_user_by_id(user_id)

    completed_lectures = []

    if user is not None:
        completed_lectures = user.get("completedLectures", [])

    updated_lectures = []

    for lecture in lectures:
        updated_lecture = lecture
        updated_lecture["isCompleted"] = any(
            completed_lecture["lecture_id"] == lecture["id"]
            for completed_lecture in completed_lectures
        )
        updated_lectures.append(updated_lecture)

    return JSONResponse(status_code=status.HTTP_200_OK, content=updated_lectures)
