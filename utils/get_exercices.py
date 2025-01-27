from utils.get_youtube_video_id import get_youtube_video_id
import random


def get_exercices(lecture, labels):
    unique_labels = []
    seen_labels = set()
    for label in labels:
        if label["label"] not in seen_labels:
            unique_labels.append(label)
            seen_labels.add(label["label"])

    exercices = []

    model_available = "modelUrl" in lecture and lecture["modelUrl"]

    if model_available:
        for label in unique_labels:
            if "value" not in label:
                continue
            exercise = {
                "key": label["label"],
                "lectureId": lecture["id"],
                "type": "recognition",
                "videoId": get_youtube_video_id(label["url"]),
                "question": label["label"],
            }
            exercices.append(exercise)

    # Generate multiple choice exercices
    for label in unique_labels:
        choices = [label["label"]] + random.sample(
            [lbl["label"] for lbl in unique_labels if lbl["label"] != label["label"]],
            min(3, len(unique_labels) - 1),
        )
        random.shuffle(choices)
        exercise = {
            "key": label["label"],
            "lectureId": lecture["id"],
            "type": "multiple",
            "videoId": get_youtube_video_id(label["url"]),
            "answer": label["label"],
            "options": choices,
        }
        random.shuffle(exercise["options"])
        exercices.append(exercise)

    random.shuffle(exercices)

    return exercices
