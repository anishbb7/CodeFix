from google.colab import drive
drive.mount('/content/drive')
!pip install datasets accelerate sacrebleu
pip uninstall -y sentence-transformers transformers accelerate
pip install transformers==4.35.2 accelerate==0.25.0
import torch, gc
gc.collect()
torch.cuda.empty_cache()
import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForCausalLM, get_linear_schedule_with_warmup
MODEL_NAME = "Salesforce/codegen-350M-mono"   # CodeGen causal LM
CSV_PATH = "/content/drive/MyDrive/CodeFix_Datasets/autocode_completion.csv"
OUT_DIR = "/content/drive/MyDrive/models/autocode_codegen"
os.makedirs(OUT_DIR, exist_ok=True)
MAX_SEQ_LEN = 2048   # CodeGen maximum
SRC_LIMIT = 1536     # input truncation limit
TGT_LIMIT = 512      # output truncation limit
BATCH_SIZE = 1
EPOCHS = 10
LR = 2e-5
WEIGHT_DECAY = 0.01
GRAD_ACCUM_STEPS = 8
WARMUP_RATIO = 0.1
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Training on:", DEVICE)
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["input", "output"])
df = df[(df["input"].str.strip() != "") & (df["output"].str.strip() != "")].reset_index(drop=True)
train_df, test_df = train_test_split(df, test_size=0.20, random_state=42)
train_df, val_df = train_test_split(train_df, test_size=0.10, random_state=42)
print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.gradient_checkpointing_enable()
model.to(DEVICE)
class CodeGenDataset(Dataset):
    def __init__(self, frame):
        self.inputs = frame["input"].tolist()
        self.outputs = frame["output"].tolist()
    def __len__(self):
        return len(self.inputs)
    def __getitem__(self, idx):
        src = self.inputs[idx]
        tgt = self.outputs[idx]
        src_ids = tokenizer(src, truncation=True, max_length=SRC_LIMIT).input_ids
        sep_ids = tokenizer("\n// completion:\n").input_ids
        tgt_ids = tokenizer(tgt, truncation=True, max_length=TGT_LIMIT).input_ids
        combined_ids = src_ids + sep_ids + tgt_ids
        tokenized = tokenizer.prepare_for_model(
            combined_ids,
            max_length=MAX_SEQ_LEN,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )
        input_ids = tokenized["input_ids"].squeeze()
        attn = tokenized["attention_mask"].squeeze()
        labels = input_ids.clone()
        labels[:len(src_ids)] = -100
        return {
            "input_ids": input_ids,
            "attention_mask": attn,
            "labels": labels
        }
train_ds = CodeGenDataset(train_df)
val_ds = CodeGenDataset(val_df)
test_ds = CodeGenDataset(test_df)
train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
steps_per_epoch = (len(train_loader) + GRAD_ACCUM_STEPS - 1) // GRAD_ACCUM_STEPS
t_total = EPOCHS * steps_per_epoch
num_warmup = int(WARMUP_RATIO * t_total)
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup, t_total)
scaler = torch.cuda.amp.GradScaler()
import matplotlib.pyplot as plt
epoch_losses = []   # store loss for graph
global_step = 0
for epoch in range(EPOCHS):
    print(f"\n----- Epoch {epoch+1}/{EPOCHS} -----")
    model.train()
    running_loss = 0.0
    optimizer.zero_grad(set_to_none=True)
    for step, batch in enumerate(train_loader, 1):
        batch = {k: v.to(DEVICE) for k, v in batch.items()}
        with torch.cuda.amp.autocast():
            outputs = model(**batch)
            loss = outputs.loss / GRAD_ACCUM_STEPS
        scaler.scale(loss).backward()
        running_loss += loss.item() * GRAD_ACCUM_STEPS
        if step % GRAD_ACCUM_STEPS == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            scheduler.step()
            global_step += 1
        if step % (GRAD_ACCUM_STEPS * 20) == 0:
            print(f"Step {step}: Loss {running_loss/step:.4f}")
    epoch_loss = running_loss / len(train_loader)
    print(f"Epoch {epoch+1} avg loss: {epoch_loss:.4f}")
    epoch_losses.append(epoch_loss)
save_dir = os.path.join(OUT_DIR, "codegen_autocomplete_finetuned")
model.save_pretrained(save_dir)
tokenizer.save_pretrained(save_dir)
print("Model saved to:", save_dir)
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
MODEL_PATH = "/content/drive/MyDrive/models/autocode_codegen/codegen_autocomplete_finetuned"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
print("Loaded model from:", MODEL_PATH)
def predict_autocomplete(code_prefix, max_new_tokens=200):
    guide = (
        "/* Complete the missing Java code inside the existing method only. */\n"
    )
    prompt = guide + code_prefix + "\n// completion:\n"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.92,
            temperature=0.3,
            eos_token_id=tokenizer.eos_token_id
        )
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return text.split("// completion:")[-1].strip()
incomplete_code = """
public class Test {
    public static int[] sum(int[] a) {
        // TODO
"""
print(predict_autocomplete(incomplete_code)) 
