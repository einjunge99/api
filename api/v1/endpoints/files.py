from fastapi import APIRouter, File, Form, status, UploadFile
from fastapi.responses import JSONResponse
from db.firestore import upload_file_to_storage

router = APIRouter()


@router.post("/")
async def create_public_file(file: UploadFile = File(None), prefix: str = Form(None)):
    try:
        file_url = await upload_file_to_storage(file, prefix)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to upload file", "error": str(e)},
        )

    return JSONResponse(status_code=200, content={"file_url": file_url})
