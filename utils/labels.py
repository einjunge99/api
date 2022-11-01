
def gen_labels(lecture_id):
    labels = {}
    with open(f'./{lecture_id}/labels.txt', "r") as label:
        text = label.read()
        lines = text.split("\n")
        for line in lines[0:-1]:
            hold = line.split(" ", 1)
            labels[hold[0]] = hold[1]
    return labels
