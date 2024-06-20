from typing import List, Dict


def labels_to_dict(labels: List[Dict[str, str]]) -> Dict[str, str]:
    label_dict = {}
    for label in labels:
        value = label.get("value")
        label_value = label.get("label")
        if value and label_value:
            label_dict[value] = label_value
    return label_dict
