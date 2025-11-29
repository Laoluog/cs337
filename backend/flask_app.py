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
import base64
import mimetypes
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
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-pro-latest")

def _encode_ct_files(ct_files):
    """Turn CT scan uploads into Gemini inlineData parts."""
    image_parts = []
    for f in ct_files:
        img_bytes = f.read()
        f.seek(0)  # reset so you can reuse if needed later
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        mime = f.mimetype or "image/png"  # adjust if you send DICOM
        image_parts.append({
            "inlineData": {
                "mimeType": mime,
                "data": b64,
            }
        })
    return image_parts



def _extract_ehr_text(ehr_files, max_chars: int = 8000) -> str:
    """
    Naive EHR extraction:
      - Reads text-like files directly (txt, json, csv, etc.)
      - Ignores binary/PDFs (you can plug in a PDF parser here)
    Truncates to max_chars to keep the prompt manageable.
    """
    chunks = []
    remaining = max_chars

    for f in ehr_files:
        fname = f.filename or "ehr_file"
        mime = (f.mimetype or "").lower()

        # Simple heuristic for text-like files
        is_texty = (
            "text" in mime
            or mime.endswith("json")
            or fname.endswith((".txt", ".json", ".csv", ".md"))
        )

        if not is_texty:
            # You can integrate a PDF/Word parser here if you want.
            chunks.append(f"[{fname}: non-text EHR document (not parsed in this stub)]\n")
            continue

        raw = f.read()
        f.seek(0)

        try:
            text = raw.decode("utf-8", errors="ignore")
        except AttributeError:
            # Already str
            text = raw

        if not text.strip():
            continue

        if len(text) > remaining:
            text = text[:remaining]
        remaining -= len(text)

        chunks.append(f"\n--- BEGIN EHR: {fname} ---\n{text}\n--- END EHR: {fname} ---\n")

        if remaining <= 0:
            break

    return "".join(chunks).strip()


def call_gemini_with_ct_and_ehr(context_text: str, ehr_text: str, ct_files) -> str:
    """Call Gemini with clinical context + EHR text + CT images."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}

    image_parts = _encode_ct_files(ct_files)

    parts = [
        {
            "text": (
                "You are a clinical prompt generator for a downstream CT scan image generator. "
                "You receive clinical context, structured EHR data, unstructured EHR notes, "
                "and CT brain images. Your task is ONLY to craft a single, rich, well-structured "
                "prompt that is an extremely detailed clinical explanation of the CT scans and EHR data"
                "with patient and treatment context.\n\n"
                "Do NOT give diagnoses or findings directly—just write the best possible prompt."
            )
        },
        {"text": "\n\nClinical / patient context:\n" + context_text},
    ]

    if ehr_text:
        parts.append({
            "text": "\n\nEHR documents (structured & narrative excerpts):\n" + ehr_text
        })

    if image_parts:
        parts.append({
            "text": "\n\nAttached CT brain images (inline): use their visual information."
        })
        parts.extend(image_parts)

    parts.append({
        "text": (
            "\n\nNow output a SINGLE prompt string of about 4-5 sentences, ready to be fed into a brain CT generation LLM. "
            "Include: extremely specific detailed clinical explanation of the CT scans, patient demographics, key history, relevant labs/meds, and what the model should focus on."
        )
    })
    
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1000000,
            "topK": 40,
            "topP": 0.95,
        },
    }

    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    

    try:
        candidate = data["candidates"][0]
        part = candidate["content"]["parts"][0]
        text = part.get("text", "")
    except Exception:
        text = ""
    
   

    return text.strip()



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
  #ct_scans = [FakeUpload("ct997.png")]

  # TODO: Persist files to storage if needed and pass paths to your model
  # TODO: Call your model with patient + files + base_prompt to get a refined prompt
  name = " ".join([
        str(patient.get("firstName") or ""),
        str(patient.get("lastName") or "")
    ]).strip()

  ctx_lines = [f"Base prompt:\n{base_prompt}\n"]
  if name:
      ctx_lines.append(f"Patient name: {name}")
  if patient:
      ctx_lines.append("Structured patient JSON:")
      ctx_lines.append(json.dumps(patient, indent=2))

  ctx_lines.append(
      f"\nAttachments: {len(ehr_files)} EHR file(s) and {len(ct_scans)} CT scan image(s)."
  )
  context_text = "\n".join(ctx_lines)

  # Extract EHR text
  ehr_text = _extract_ehr_text(ehr_files)

  try:
      generated_prompt = call_gemini_with_ct_and_ehr(context_text, ehr_text, ct_scans)
      if not generated_prompt:
          generated_prompt = f"{base_prompt} [patient:{name or 'n/a'}]"
  except Exception as e:
      generated_prompt = (
          f"{base_prompt} [fallback: Gemini error: {e}; "
          f"patient:{name or 'n/a'}, EHR:{len(ehr_files)}, CT:{len(ct_scans)}]"
      )

  return jsonify({"generated_prompt": generated_prompt})


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
      content_bytes = resp.content
      mime = resp.headers.get("Content-Type") or mimetypes.guess_type(image_url)[0] or "image/jpeg"
      brain_reference = types.VideoGenerationReferenceImage(
        image={
          "bytesBase64Encoded": base64.b64encode(content_bytes).decode("utf-8"),
          "mimeType": mime,
        },
        reference_type="inline",
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
  app.run(host="0.0.0.0", port=5001, debug=True)


