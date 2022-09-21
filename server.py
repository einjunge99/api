from fastapi import FastAPI
from fastapi import File, Form
from PIL import Image, ImageOps
from io import BytesIO
import uvicorn
from keras.models import load_model
import numpy as np
from utils.labels import gen_labels

app = FastAPI()


@app.get("/")
def hello_world():
    return "Hello World"


@app.post("/api/predict")
def predict(file: bytes = File(...), expected_label: str = Form(...)):
    labels = gen_labels()

    if expected_label not in labels.values():
        return {"error": "Invalid label"}

    model = load_model('keras_model.h5')

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

    if predicted_label == expected_label:
        return {"correct": True, "confidence": prediction[0][result]*100}

    index = list(labels.values()).index(expected_label)

    confidence = prediction[0][index]*100

    if confidence > 0.5:
        return {"correct": True, "confidence": confidence}

    return {"correct": False, "confidence": confidence}


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")
