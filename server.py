import random
from fastapi import FastAPI, Response, status
from fastapi import File, Form
from PIL import Image, ImageOps
from io import BytesIO
import uvicorn
from keras.models import load_model
import numpy as np
from utils.labels import gen_labels
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = FastAPI()


@app.get("/")
def hello_world():
    return "Hello World"

@app.post("/api/predict/{lecture_id}")
def predict(lecture_id, file: bytes = File(...), expected_label: str = Form(...)):
    #TODO: Add lecture_id validation
    labels = gen_labels(lecture_id)

    if expected_label not in labels.values():
        return {"correct": False, "error": "Invalid label"}

    model = load_model(f'./{lecture_id}/keras_model.h5')

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    image = Image.open(BytesIO(file)).convert('RGB')
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array

    prediction = model.predict(data)

    result = np.argmax(prediction[0])

    predicted_label = labels[str(result)]

    print(f"Predicted: {predicted_label}, Expected: {expected_label}")

    if predicted_label == expected_label:
        confidence = prediction[0][result]*100
        if confidence > 50:
            return {"correct": True, "confidence": confidence}
        return {"correct": False, "confidence": confidence}

    index = list(labels.values()).index(expected_label)
    confidence = prediction[0][index]*100

    if confidence > 50:
        return {"correct": True, "confidence": confidence}
    return {"correct": False, "confidence": confidence}

@app.get("/api/exercises/{lecture_id}")
def exercises(lecture_id):
    db = firestore.client()
    docs = [d for d in db.collection(u'exercises').where('lectureId','==',lecture_id).stream()]
    
    exercices = []
    
    if len(docs) == 0:
        return exercices
    
    for doc in docs:
        exercices.append(doc.to_dict())
    
    random.shuffle(exercices)
    
    return exercices[:5]

@app.get("/api/lectures/{user_id}")
def get_lectures(user_id):
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    
    completed_lectures = []
    
    if user.exists:
        completed_lectures = user.to_dict()['completed_lectures']
    
    docs = db.collection('lectures').stream()
    
    lectures = []

    for doc in docs:
        lecture = doc.to_dict()
        lecture['isCompleted'] = doc.id in completed_lectures
        lectures.append(lecture)
    
    return lectures

@app.patch("/api/user/{user_id}/{lecture_id}")
def add_completed_lecture(user_id,lecture_id,response: Response):
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    
    if not user_ref.get().exists:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "User not found"}
        
    user_ref.update({'completedLectures': firestore.ArrayUnion([lecture_id])})
    
if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
