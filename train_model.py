import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)

# Configuration

MODEL_NAME = "google/flan-t5-small"

TRAIN_FILE = "train_dataset.csv"
VAL_FILE = "validation_dataset.csv"

MAX_INPUT_LENGTH = 256
MAX_TARGET_LENGTH = 128

BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 3e-5

# Load Dataset

dataset = load_dataset(
    "csv",
    data_files={
        "train": TRAIN_FILE,
        "validation": VAL_FILE
    }
)

# Load Tokenizer & Model

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Automatically use MPS if available
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model.to(device)

# Tokenization Function

def preprocess_function(examples):
    model_inputs = tokenizer(
        examples["input_text"],
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
        padding="max_length"
    )

    labels = tokenizer(
        examples["target_text"],
        max_length=MAX_TARGET_LENGTH,
        truncation=True,
        padding="max_length"
    )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# Training Arguments

training_args = TrainingArguments(
    output_dir="./model_output",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=LEARNING_RATE,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir="./logs",
    logging_steps=50,
    load_best_model_at_end=True,
    report_to="none"
)

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# Trainer

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
    data_collator=data_collator
)

# Train

trainer.train()

# Save Final Model

trainer.save_model("./final_model")
tokenizer.save_pretrained("./final_model")

print("Training complete. Model saved to ./final_model")