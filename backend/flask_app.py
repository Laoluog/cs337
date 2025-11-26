"""
Flask backend shell for generating a model-driven prompt.

Endpoint:
  POST /model/prompt
    - multipart/form-data
      - base_prompt: str
      - patient: JSON string for patient info
      - ehr_files: 0..n files
      - ct_scans: 0..n files
    - returns: { "generated_prompt": str }

Replace the stubbed logic with your model inference.
"""

from flask import Flask, request, jsonify
import json
import os
import time
import requests

app = Flask(__name__)

@app.route("/model/prompt", methods=["POST"])
def model_prompt():
  # Parse text fields
  base_prompt = request.form.get("base_prompt", "", type=str)
  patient_raw = request.form.get("patient", "{}", type=str)
  try:
    patient = json.loads(patient_raw or "{}")
  except Exception:
    patient = {}

  # Access uploaded files if you need to read them or persist elsewhere
  ehr_files = request.files.getlist("ehr_files")
  ct_scans = request.files.getlist("ct_scans")

  # TODO: Persist files to storage if needed and pass paths to your model
  # TODO: Call your model with patient + files + base_prompt to get a refined prompt

  # Stubbed prompt: combine inputs deterministically
  name = " ".join([str(patient.get("firstName") or ""), str(patient.get("lastName") or "")]).strip()
  file_hint = f"{len(ehr_files)} EHR file(s), {len(ct_scans)} scan(s)"
  generated_prompt = (f"{base_prompt} [patient:{name or 'n/a'} | {file_hint}]").strip()

  return jsonify({"generated_prompt": generated_prompt})

@app.route("/model/generate_images", methods=["POST"])
def generate_images():
  """
  JSON body: { "prompt": str, "timepoints": ["now","3m","6m","12m"]? }
  Returns: { "images": { "now": url, "3m": url, "6m": url, "12m": url } }
  """
  payload = request.get_json(silent=True) or {}
  prompt = payload.get("prompt") or ""
  timepoints = payload.get("timepoints") or ["now", "3m", "6m", "12m"]

  # Hard-coded BFL endpoint; replace with your own model as needed
  bfl_url = "https://api.bfl.ai/v1/flux-kontext-pro"
  api_key = os.environ.get("BFL_API_KEY")
  if not api_key:
    return jsonify({"error": "Missing BFL_API_KEY"}), 500

  def generate_one(p: str) -> str:
    resp = requests.post(
      bfl_url,
      headers={
        "accept": "application/json",
        "x-key": api_key,
        "Content-Type": "application/json",
      },
      json={"prompt": p},
      timeout=30,
    ).json()
    polling_url = resp.get("polling_url")
    if not polling_url:
      raise RuntimeError(f"Bad response: {resp}")
    # Poll up to ~60s
    started = time.time()
    while True:
      time.sleep(0.5)
      result = requests.get(
        polling_url,
        headers={"accept": "application/json", "x-key": api_key},
        timeout=30,
      ).json()
      status = result.get("status")
      if status == "Ready":
        return result["result"]["sample"]
      if status in ("Error", "Failed"):
        raise RuntimeError(f"Generation failed: {result}")
      if time.time() - started > 90:
        raise TimeoutError("Timed out waiting for image")

  # Slightly tailor the prompt by timepoint; hard-coded phrasing
  tp_to_suffix = {
    "now": "current brain state",
    "3m": "brain state in approximately 3 months",
    "6m": "brain state in approximately 6 months",
    "12m": "brain state in approximately 12 months",
  }
  images = {}
  for tp in timepoints:
    suffix = tp_to_suffix.get(tp, str(tp))
    composed = f"{prompt}. Please depict the {suffix}."
    try:
      url = generate_one(composed)
      images[tp] = url
    except Exception as e:
      images[tp] = None

  return jsonify({"images": images})

if __name__ == "__main__":
  # For local testing:
  #   pip install flask
  #   python flask_app.py
  #   export NEXT_PUBLIC_BACKEND_URL=http://localhost:5001
  # Then submit the frontend form
  app.run(host="0.0.0.0", port=5001, debug=True)


