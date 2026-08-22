"""YOLOv8 training script — to be run inside Google Colab (free GPU).

Steps:
    1. Upload the Kaggle "playing cards object detection" dataset
       (76 classes: 13 ranks × 4 suits + Joker variants, depending on
       the specific dataset version).
    2. Run this script. It will:
        - download YOLOv8n pretrained weights
        - fine-tune on the dataset for 50 epochs
        - save the trained model to /content/ramai-ai/models/yolo_cards.pt
        - print the final mAP50

CLI fallback: if torch is unavailable, this script prints a clear message
and exits — it cannot run here.

Usage in Colab:
    !python scripts/train_yolo.py --data /content/cards.yaml --epochs 50
"""
from __future__ import annotations
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=False, default="cards.yaml",
                        help="Path to data.yaml (YOLO format)")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--output", default="models/yolo_cards.pt")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("=" * 60)
        print("ERROR: ultralytics not installed.")
        print("This script must run in Google Colab. In a Colab cell, run:")
        print("    !pip install ultralytics")
        print("    !python scripts/train_yolo.py --data cards.yaml --epochs 50")
        print("=" * 60)
        sys.exit(1)

    if not os.path.exists(args.data):
        print(f"ERROR: data file not found: {args.data}")
        print("Upload your Kaggle cards dataset and create a data.yaml that points to it.")
        print("Expected format:")
        print("  path: /content/cards")
        print("  train: images/train")
        print("  val: images/val")
        print("  names:")
        print("    0: A♠, 1: A♥, ... 75: Joker")
        sys.exit(1)

    model = YOLO(args.weights)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        project="runs/train",
        name="yolo_cards",
    )
    # Save final weights
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    best = os.path.join("runs", "train", "yolo_cards", "weights", "best.pt")
    if os.path.exists(best):
        import shutil
        shutil.copy(best, args.output)
        print(f"saved: {args.output}")

    # Print final metrics
    metrics = model.val()
    print(f"mAP50:        {metrics.box.map50:.4f}")
    print(f"mAP50-95:     {metrics.box.map:.4f}")
    print(f"Precision:    {metrics.box.mp:.4f}")
    print(f"Recall:       {metrics.box.mr:.4f}")


if __name__ == "__main__":
    main()
