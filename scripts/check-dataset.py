import argparse
import json
import os

parser = argparse.ArgumentParser()

parser.add_argument("--dataset", type=str, required=True)

args = parser.parse_args()

dataset = json.load(open(args.dataset, "r"))

images = dict()
for image in dataset["images"]:
    image_path = os.path.join(os.path.dirname(args.dataset), "images", image["file_name"])
    if not os.path.exists(image_path):
        print("Missing image (in images):", image_path)

    images[image["id"]] = image

for annotation in dataset["annotations"]:
    if annotation["image_id"] not in images:
        print("Missing image ID (in annotations):", annotation["image_id"])
        continue
    image = images[annotation["image_id"]]
    image_path = os.path.join(os.path.dirname(args.dataset), "images", image["file_name"])
    if not os.path.exists(image_path):
        print("Missing image (in annotations):", image_path)