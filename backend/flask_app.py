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
from flask_cors import CORS
import json
import os
import time
import requests
import uuid
from pathlib import Path
from google import genai
from google.genai import types
import time
from google import genai

app = Flask(__name__)
# Allow frontend (http://localhost:3000) to call Flask (http://localhost:5001)
# Loosened for dev; tighten origins in production.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

hardcoded_prompt = ([
    {
        "time_point": "now",
        "prompt":
            "Generate exactly one high-resolution axial (top-down) CT scan image of the human brain. "
            "Soft tissue window for brain parenchyma. The patient is a 72-year-old female, Evelyn Reed, "
            "diagnosed with early-stage Alzheimer's disease 6 months ago, currently on Donepezil. The image "
            "must show mild generalized cortical atrophy, distinctly mild hippocampal atrophy, and subtle "
            "widening of the sulci in the temporal and parietal regions. Ventricular size should appear "
            "normal for age. No acute hemorrhage, mass effect, or vascular calcifications. Only show one image, "
            "top-down CT view. Do not render multiple images or views. Clinically accurate, photorealistic."
    },
    {
        "time_point": "3m",
        "prompt":
            "Create exactly one high-resolution axial CT scan (top-down view) image of the brain, "
            "soft tissue window. The patient is a 72-year-old female, Evelyn Reed, now 3 months after the "
            "previous state (9 months post-diagnosis) with continued Donepezil. Depict slightly increased "
            "generalized cortical atrophy versus baseline, noticeably moderate hippocampal atrophy, and mildly "
            "increased widening of temporal and parietal sulci. Lateral ventricles with minimal, subtle "
            "enlargement. No new acute findings or mass effect. Only one image, top-down CT. No other views. "
            "Clinically accurate, photorealistic."
    },
    {
        "time_point": "6m",
        "prompt":
            "Produce a single, high-resolution axial (top-down) CT image of the brain, soft tissue window. "
            "Patient: 72-year-old female, Evelyn Reed, 6 months after previous state (12 months post-diagnosis). "
            "Show distinctly moderate generalized cortical atrophy, marked hippocampal atrophy, and moderate "
            "widening of sulci, most apparent in the temporal and parietal lobes. Lateral ventricles should "
            "show definite, mild enlargement. No new acute lesions. The output must be only one top-down brain "
            "CT image. Clinically accurate, photorealistic."
    },
    {
        "time_point": "12m",
        "prompt":
            "Output exactly one high-resolution top-down (axial) CT scan image of the brain with soft tissue "
            "window. Patient: 72-year-old female, Evelyn Reed, 12 months after previous state (18 months "
            "post-diagnosis). Clearly show significant generalized cortical atrophy, severe hippocampal atrophy "
            "with pronounced volume loss, and marked widening of cortical sulci in temporal and parietal regions. "
            "Lateral and third ventricles appear moderately enlarged, consistent with ex-vacuo hydrocephalus. "
            "No new acute pathology or abnormal density. Absolutely ensure a single image, axial/top-down CT only. "
            "Clinically accurate, photorealistic."
    }
])
# todo(NISHANK): Implement this endpoint.
@app.route("/model/prompt", methods=["POST"])
def model_prompt():
  # hard-coded prompt for now -- Nishank can remove this later.
  print("prompt returned by the model: ", jsonify({"generated_prompt": hardcoded_prompt}))
  return jsonify({"generated_prompt": hardcoded_prompt})

  # Parse text fields
  """
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
  """

@app.route("/model/generate_video", methods=["POST"])
def generate_video():
  api_key = os.environ.get("GOOGLE_API_KEY")
  if not api_key:
    return jsonify({"error": "Missing GOOGLE_API_KEY"}), 500
  client = genai.Client(api_key=api_key)

  payload = request.get_json(silent=True) or {}
  image_url = payload.get("image_url")
  user_prompt = payload.get("prompt")
  time_point = payload.get("time_point")
  seconds = int(payload.get("seconds") or 7)

  # Normalize prompt:
  # - If a list is provided (e.g., [{time_point, prompt}, ...]), pick by time_point or first available
  # - If a dict is provided (e.g., {prompt: "..."}), extract "prompt"
  # - Else expect a string
  if isinstance(user_prompt, list):
    chosen = None
    if time_point:
      for item in user_prompt:
        if isinstance(item, dict) and item.get("time_point") == time_point and isinstance(item.get("prompt"), str):
          chosen = item.get("prompt")
          break
    if not chosen:
      for item in user_prompt:
        if isinstance(item, dict) and isinstance(item.get("prompt"), str):
          chosen = item.get("prompt")
          break
    if not chosen:
      for item in user_prompt:
        if isinstance(item, str):
          chosen = item
          break
    user_prompt = chosen
  elif isinstance(user_prompt, dict):
    maybe = user_prompt.get("prompt")
    user_prompt = maybe if isinstance(maybe, str) else None

  # Use normalized client prompt when available, otherwise fallback to a sensible default
  prompt = user_prompt or (
    "Create a 7‑second, ultra high‑resolution, 360‑degree, eye‑level orbit around a single human brain matching the provided CT/MRI reference image. "
    "Subject is a medically accurate human brain with realistic cortical gyri and sulci; preserve anatomical proportions and density cues from the reference. "
    "Camera performs a smooth, stabilized dolly‑orbit over the full duration. "
    "Composition begins medium‑wide, transitions briefly to a medium shot revealing temporal and hippocampal contours, then returns to medium‑wide by the end. "
    "Style is clinical, photorealistic medical visualization; no artistic liberties. "
    "Deep focus with a 35–50mm feel; minimal lens breathing; no motion blur artifacts. "
    "Neutral medium‑gray background with soft key and subtle rim light to accent form; balanced, natural contrast and color. "
    "No text, logos, watermarks, or extraneous elements."
  )

  # Download the provided image URL and upload it as a reference asset
  reference_images = []
  if image_url:
    try:
      resp = requests.get(image_url, timeout=30)
      resp.raise_for_status()
      tmp_dir = Path(__file__).parent / "tmp_refs"
      tmp_dir.mkdir(parents=True, exist_ok=True)
      img_path = tmp_dir / f"ref_{uuid.uuid4().hex}.jpg"
      with open(img_path, "wb") as f:
        f.write(resp.content)
      uploaded = client.files.upload(file=str(img_path))
      brain_reference = types.VideoGenerationReferenceImage(
        image=uploaded,
        reference_type="asset",
      )
      reference_images.append(brain_reference)
    except Exception as e:
      print(f"Failed to use reference image {image_url}: {e}")

  # Configure generation; include reference_images if available
  gen_config = types.GenerateVideosConfig(
    reference_images=reference_images if reference_images else None,
    # If duration is supported in your SDK version, you can add it here, e.g.:
    # duration_seconds=seconds,
  )

  operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=gen_config,
  )

  # Poll the operation status until the video is ready.
  while not operation.done:
      print("Waiting for video generation to complete...")
      time.sleep(10)
      operation = client.operations.get(operation)

  # Download the video and save to static/videos with a unique filename.
  video = operation.response.generated_videos[0]
  client.files.download(file=video.video)
  filename = f"brain_{uuid.uuid4().hex}.mp4"
  static_dir = Path(__file__).parent / "static" / "videos"
  static_dir.mkdir(parents=True, exist_ok=True)
  output_path = static_dir / filename
  video.video.save(str(output_path))
  print(f"Generated video saved to {output_path}")
  # Serve via Flask static: /static/videos/<filename>
  base = request.host_url.rstrip("/")
  video_url = f"{base}/static/videos/{filename}"
  return jsonify({"video_url": video_url})

@app.route("/model/generate_images", methods=["POST"])
def generate_images():
  """
  JSON body: { "prompt": str, "timepoints": ["now","3m","6m","12m"]? }
  Returns: { "images": { "now": url, "3m": url, "6m": url, "12m": url } }
  """
  payload = request.get_json(silent=True) or {}
  prompt = payload.get("prompt") or ""
  print("recieved prompt: ", prompt)
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

  # If prompt is an object like { "now": "...", "3m": "...", ... } use those directly.
  # Otherwise if it's a string, fall back to suffix composition for each timepoint.
  prompt_per_tp = {}
  if isinstance(prompt, dict):
    # Normalize keys to expected timepoints
    for tp in timepoints:
      prompt_per_tp[tp] = prompt.get(tp)
  else:
    # Single string prompt for all timepoints
    for tp in timepoints:
      suffix = tp_to_suffix.get(tp, str(tp))
      prompt_per_tp[tp] = f"{prompt}. Please depict the {suffix}."

  for tp in timepoints:
    composed = prompt_per_tp.get(tp) or ""
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
  #   export NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
  # Then submit the frontend form
  app.run(host="0.0.0.0", port=5000, debug=True)


