from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import os
import io
import base64
import tempfile
import torch
import numpy as np
import pydicom
from PIL import Image
from pydantic import BaseModel

from model_utils import (
    preprocess_dicom_for_model,
    load_model,
    predict_mask,
    suggest_icd,
)

def dicom_to_preview_base64(dicom_path):
    ds = pydicom.dcmread(dicom_path, force=True)

    image = ds.pixel_array.astype(np.float32)

    slope = float(ds.get("RescaleSlope", 1))
    intercept = float(ds.get("RescaleIntercept", 0))
    hu = image * slope + intercept

    lower = -600 - 1500 / 2
    upper = -600 + 1500 / 2
    windowed = np.clip(hu, lower, upper)

    normalized = (windowed - windowed.min()) / (windowed.max() - windowed.min() + 1e-8)
    img_uint8 = (normalized * 255).astype(np.uint8)

    pil_img = Image.fromarray(img_uint8)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    metadata = {
        "patient_id": str(ds.get("PatientID", "Not available")),
        "modality": str(ds.get("Modality", "Not available")),
        "instance_number": str(ds.get("InstanceNumber", "Not available")),
        "slice_location": str(ds.get("SliceLocation", "Not available")),
        "rows": str(ds.get("Rows", "Not available")),
        "columns": str(ds.get("Columns", "Not available")),
        "image_shape": str(ds.pixel_array.shape),
    }

    return encoded, metadata

app = FastAPI(title="Lung Nodule ROI Segmentation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join("models", "best_lidc_unet.pth")
model, device = load_model(MODEL_PATH)


class RoiRequest(BaseModel):
    image_base64: str
    x: int
    y: int
    width: int
    height: int


@app.get("/")
def home():
    return {
        "message": "Lung Nodule ROI Segmentation API is running",
        "model_loaded": True,
        "device": str(device),
    }


@app.post("/preview")
async def preview(file: UploadFile = File(...)):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        image_base64, metadata = dicom_to_preview_base64(temp_path)

        return {
            "status": "success",
            "message": "DICOM preview generated.",
            "filename": file.filename,
            "dicom_metadata": metadata,
            "preview_image": f"data:image/png;base64,{image_base64}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/predict-roi")
async def predict_roi(request: RoiRequest):
    try:
        image_data = request.image_base64.split(",")[1]
        image_bytes = base64.b64decode(image_data)

        image = Image.open(io.BytesIO(image_bytes)).convert("L")

        roi = image.crop((
            request.x,
            request.y,
            request.x + request.width,
            request.y + request.height
        ))

        roi = roi.resize((64, 64))
        roi_np = np.array(roi).astype(np.float32) / 255.0

        input_tensor = torch.tensor(roi_np).unsqueeze(0).unsqueeze(0)

        model_output = predict_mask(model, device, input_tensor)
        icd_output = suggest_icd(model_output["mask_area_pixels"])

        return {
            "status": "success",
            "message": "ROI crop processed and AI inference completed.",
            "prediction": {
                "roi_detected": model_output["roi_detected"],
                "mask_area_pixels": model_output["mask_area_pixels"],
                "probability_mean": model_output["probability_mean"],
                "suggested_finding": icd_output["suggested_finding"],
                "icd_10_suggestion": icd_output["icd_10_suggestion"],
                "icd_description": icd_output["icd_description"],
                "note": icd_output["note"],
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        input_tensor, metadata = preprocess_dicom_for_model(temp_path)
        model_output = predict_mask(model, device, input_tensor)
        icd_output = suggest_icd(model_output["mask_area_pixels"])

        return {
            "filename": file.filename,
            "status": "success",
            "message": "DICOM processed and AI inference completed.",
            "dicom_metadata": metadata,
            "prediction": {
                "roi_detected": model_output["roi_detected"],
                "mask_area_pixels": model_output["mask_area_pixels"],
                "probability_mean": model_output["probability_mean"],
                "suggested_finding": icd_output["suggested_finding"],
                "icd_10_suggestion": icd_output["icd_10_suggestion"],
                "icd_description": icd_output["icd_description"],
                "note": icd_output["note"],
            },
        }

    except Exception as e:
        return {
            "filename": file.filename,
            "status": "error",
            "message": str(e),
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
