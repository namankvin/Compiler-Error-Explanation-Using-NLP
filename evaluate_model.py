import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import Dataset
import evaluate
from tqdm import tqdm

# Load Model
device = "mps" if torch.backends.mps.is_available() else "cpu"

model = AutoModelForSeq2SeqLM.from_pretrained("./final_model").to(device)
tokenizer = AutoTokenizer.from_pretrained("./final_model")

# Load Test Dataset
df = pd.read_csv("test_dataset.csv")
dataset = Dataset.from_pandas(df)

rouge = evaluate.load("rouge")

predictions = []
references = []

print("Evaluating model on test dataset...\n")

for example in tqdm(dataset):

    inputs = tokenizer(
        example["input_text"],
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            num_beams=4,
            early_stopping=True
        )

    prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)

    predictions.append(prediction)
    references.append(example["target_text"])

# Compute ROUGE
results = rouge.compute(
    predictions=predictions,
    references=references
)

# Save outputs
results_df = pd.DataFrame({
    "input": df["input_text"],
    "prediction": predictions,
    "reference": references
})

results_df.to_csv("model_outputs.csv", index=False)

print("\nEvaluation Results:")
for key, value in results.items():
    print(f"{key}: {round(value, 4)}")