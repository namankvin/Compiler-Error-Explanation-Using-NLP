import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import Dataset
import evaluate
from tqdm import tqdm
import re

# Load Model
device = "mps" if torch.backends.mps.is_available() else "cpu"

model = AutoModelForSeq2SeqLM.from_pretrained("./final_model").to(device)
tokenizer = AutoTokenizer.from_pretrained("./final_model")

# Load Test Dataset
df = pd.read_csv("test_dataset.csv")
dataset = Dataset.from_pandas(df)

rouge = evaluate.load("rouge")
bleu = evaluate.load("sacrebleu")

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
rouge_results = rouge.compute(
    predictions=predictions,
    references=references
)

# Compute BLEU (SacreBLEU expects nested references)
bleu_results = bleu.compute(
    predictions=predictions,
    references=[[ref] for ref in references],
)


def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


# Exact match accuracy on normalized text
exact_matches = sum(
    1 for pred, ref in zip(predictions, references)
    if normalize_text(pred) == normalize_text(ref)
)
exact_match_accuracy = exact_matches / max(len(references), 1)

# Save outputs
results_df = pd.DataFrame({
    "input": df["input_text"],
    "prediction": predictions,
    "reference": references
})

results_df.to_csv("model_outputs.csv", index=False)

# Export sample for human validation review
human_sample_size = min(50, len(results_df))
human_validation_df = results_df.sample(n=human_sample_size, random_state=42).copy()
human_validation_df.insert(0, "human_score_clarity_1_5", "")
human_validation_df.insert(1, "human_score_correctness_1_5", "")
human_validation_df.insert(2, "human_score_helpfulness_1_5", "")
human_validation_df.insert(3, "human_notes", "")
human_validation_df.to_csv("human_validation_sample.csv", index=False)

summary = {
    "rouge": rouge_results,
    "bleu": bleu_results,
    "exact_match_accuracy": round(exact_match_accuracy, 4),
    "samples_evaluated": len(results_df),
    "human_validation_sample_size": human_sample_size,
}

with open("evaluation_metrics.json", "w") as metrics_file:
    import json

    json.dump(summary, metrics_file, indent=2)

print("\nEvaluation Results:")
for key, value in rouge_results.items():
    print(f"{key}: {round(value, 4)}")

print(f"BLEU: {round(bleu_results['score'], 4)}")
print(f"Exact Match Accuracy: {round(exact_match_accuracy, 4)}")
print("Saved: model_outputs.csv, evaluation_metrics.json, human_validation_sample.csv")