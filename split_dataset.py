import csv
import random

INPUT_FILE = "generated_dataset.csv"

TRAIN_FILE = "train_dataset.csv"
VAL_FILE = "validation_dataset.csv"
TEST_FILE = "test_dataset.csv"

TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42  # Reproducibility

def split_dataset():

    # Set seed for reproducibility
    random.seed(SEED)

    # Read dataset
    with open(INPUT_FILE, "r") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    rows = reader[1:]

    # Shuffle dataset
    random.shuffle(rows)

    total = len(rows)

    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    train_rows = rows[:train_end]
    val_rows = rows[train_end:val_end]
    test_rows = rows[val_end:]

    # Write train set
    with open(TRAIN_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(train_rows)

    # Write validation set
    with open(VAL_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(val_rows)

    # Write test set
    with open(TEST_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(test_rows)

    print("Dataset split completed successfully.")
    print(f"Total samples: {total}")
    print(f"Train samples: {len(train_rows)}")
    print(f"Validation samples: {len(val_rows)}")
    print(f"Test samples: {len(test_rows)}")


if __name__ == "__main__":
    split_dataset()