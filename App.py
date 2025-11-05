# App.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
import torch

COMPLETION_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\code_completion_model"
DEBUGGER_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\codet5p_bugfix_finetuned"
TESTCASE_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\testgen_codet5p"

# Load code completion model
completion_tokenizer = AutoTokenizer.from_pretrained(COMPLETION_MODEL_PATH)
completion_model = AutoModelForCausalLM.from_pretrained(COMPLETION_MODEL_PATH)

# Load debugging model
debugger_tokenizer = AutoTokenizer.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)
debugger_model = AutoModelForSeq2SeqLM.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)

# Load test case generation model
testcase_tokenizer = AutoTokenizer.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)
testcase_model = AutoModelForSeq2SeqLM.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)


def generate_with_codegen(model, tokenizer, code: str, max_length=1000, language="java") -> str:
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=4,
        early_stopping=True,
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if language.lower() in ["python", "c", "cpp"]:
        decoded = trim_after_function(decoded)
    return decoded


def generate_with_codet5(model, tokenizer, code: str, max_length=1000, language="java") -> str:
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=4,
        early_stopping=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if language.lower() in ["python", "c", "cpp"]:
        decoded = trim_after_function(decoded)
    return decoded


def trim_after_function(decoded: str) -> str:
    brace_count = 0
    trimmed_code = []
    inside_function = False

    for line in decoded.splitlines():
        trimmed_code.append(line)
        if '{' in line:
            brace_count += line.count('{')
            inside_function = True
        if '}' in line:
            brace_count -= line.count('}')
            if inside_function and brace_count == 0:
                break
    return "\n".join(trimmed_code).strip()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Routes ----
@app.post("/completion")
async def completion(request: Request):
    data = await request.json()
    code = data.get("code", "")
    language = data.get("language", "java")
    description = data.get("description", "")
    validated = generate_with_codegen(completion_model, completion_tokenizer, code, max_length=1000, language=language)
    return {"result": validated["code"]}

@app.post("/debugging")
async def debugging(request: Request):
    data = await request.json()
    code = data.get("code", "")
    language = data.get("language", "java")
    description = data.get("description", "")
    validated = generate_with_codet5(debugger_model, debugger_tokenizer, code, max_length=1000, language=language)
    return {"result": validated["code"]}

@app.post("/testcase")
async def testcase(request: Request):
    data = await request.json()
    code = data.get("code", "")
    language = data.get("language", "java")
    description = data.get("description", "")
    num_cases = data.get("num_cases", 5)
    validated =  generate_with_codet5(testcase_model, testcase_tokenizer, code, max_length=1000, language=language)
    return {"result": validated["code"]}


# ---- Run Server ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

