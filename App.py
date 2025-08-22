from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,       # For CodeGen (completion)
    AutoModelForSeq2SeqLM       # For CodeT5 (debugging/testcases)
)
import torch

# ====================
# Load Models
# ====================
# 👇 Change paths to where your trained models are stored
COMPLETION_MODEL_PATH = r"E:\Users\admin\Desktop\CodeFix\models\code_completion_model"
DEBUGGER_MODEL_PATH = r"E:\Users\admin\\Desktop\CodeFix\models\codet5p_bugfix_finetuned"
#TESTCASE_MODEL_PATH = "./models/testcase_codet5"

# Load CodeGen model for Completion
completion_tokenizer = AutoTokenizer.from_pretrained(COMPLETION_MODEL_PATH, local_files_only=True)
completion_model = AutoModelForCausalLM.from_pretrained(COMPLETION_MODEL_PATH, local_files_only=True)

# Load CodeT5 model for Debugging
debugger_tokenizer = AutoTokenizer.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)
debugger_model = AutoModelForSeq2SeqLM.from_pretrained(DEBUGGER_MODEL_PATH, local_files_only=True)

# Load CodeT5 model for Test Case Generation
#testcase_tokenizer = AutoTokenizer.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)
#testcase_model = AutoModelForSeq2SeqLM.from_pretrained(TESTCASE_MODEL_PATH, local_files_only=True)


# ====================
# Helper Functions
# ====================
def generate_with_codegen(model, tokenizer, code: str, max_length=350) -> str:
    """Generate with CodeGen (causal LM)"""
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return decoded.strip()


def generate_with_codet5(model, tokenizer, code: str, max_length=350) -> str:
    """Generate with CodeT5 (seq2seq LM)"""
    inputs = tokenizer(code, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_beams=4,
        early_stopping=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return decoded.strip()


# ====================
# Flask App
# ====================
app = Flask(__name__)
CORS(app)

@app.route("/completion", methods=["POST"])
def completion():
    data = request.get_json()
    code = data.get("code", "")
    suggestion = generate_with_codegen(completion_model, completion_tokenizer, code)
    return jsonify({"result": suggestion})


@app.route("/debugging", methods=["POST"])
def debugging():
    data = request.get_json()
    code = data.get("code", "")
    suggestion = generate_with_codet5(debugger_model, debugger_tokenizer, code)
    return jsonify({"result": suggestion})


"""@app.route("/testcase", methods=["POST"])
def testcase():
    data = request.get_json()
    code = data.get("code", "")
    suggestion = generate_with_codet5(testcase_model, testcase_tokenizer, code)
    return jsonify({"result": suggestion})"""


# ====================
# Run Server
# ====================
if __name__ == "__main__":
    app.run(debug=True)
