from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
import torch

# ====================
# Load Models
# ====================
COMPLETION_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\code_completion_model"
DEBUGGER_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\codet5p_bugfix_finetuned"
#TESTCASE_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\testcase_generation_model"

# Load code completion
completion_tokenizer = AutoTokenizer.from_pretrained(COMPLETION_MODEL_PATH)
completion_model = AutoModelForCausalLM.from_pretrained(COMPLETION_MODEL_PATH)

# Load debugging
debugger_tokenizer = AutoTokenizer.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)
debugger_model = AutoModelForSeq2SeqLM.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)

# Load test case generation
#testcase_tokenizer = AutoTokenizer.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)
#testcase_model = AutoModelForSeq2SeqLM.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)


# ====================
# Helper Functions
# ====================
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


def generate_with_codegen(model, tokenizer, code: str, max_length=350) -> str:
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=350,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return trim_after_function(decoded)


def generate_with_codet5(model, tokenizer, code: str, max_length=350) -> str:
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=4,
        early_stopping=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return trim_after_function(decoded)


# ====================
# FastAPI App
# ====================
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
    suggestion = generate_with_codegen(completion_model, completion_tokenizer, code)
    return {"result": suggestion}


@app.post("/debugging")
async def debugging(request: Request):
    data = await request.json()
    code = data.get("code", "")
    suggestion = generate_with_codet5(debugger_model, debugger_tokenizer, code)
    return {"result": suggestion}


#@app.post("/testcase")
#async def testcase(request: Request):
#    data = await request.json()
#    code = data.get("code", "")
#    suggestion = generate_with_codet5(testcase_model, testcase_tokenizer, code)
#    return {"result": suggestion}


# ---- Run Server ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
