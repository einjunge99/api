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
            exercise = {
                "key": label["label"],
                "lectureId": lecture["id"],
                "question": label["label"],
                "type": "recognition",
                "videoId": label["url"],
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
            "answer": label["label"],
            "key": label["label"],
            "lectureId": lecture["id"],
            "type": "multiple",
            "options": choices,
            "videoId": label["url"],
        }
        random.shuffle(exercise["options"])
        exercices.append(exercise)

    random.shuffle(exercices)

    return exercices
