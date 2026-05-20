import os
import numpy as np
import torch
import torch.nn as nn
import pydicom
from PIL import Image


class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class UNetSmall(nn.Module):
    def __init__(self):
        super().__init__()

        self.down1 = DoubleConv(1, 16)
        self.pool1 = nn.MaxPool2d(2)

        self.down2 = DoubleConv(16, 32)
        self.pool2 = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(32, 64)

        self.up2 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.conv2 = DoubleConv(64, 32)

        self.up1 = nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2)
        self.conv1 = DoubleConv(32, 16)

        self.out = nn.Conv2d(16, 1, kernel_size=1)

    def forward(self, x):
        d1 = self.down1(x)
        p1 = self.pool1(d1)

        d2 = self.down2(p1)
        p2 = self.pool2(d2)

        b = self.bottleneck(p2)

        u2 = self.up2(b)
        u2 = torch.cat([u2, d2], dim=1)
        u2 = self.conv2(u2)

        u1 = self.up1(u2)
        u1 = torch.cat([u1, d1], dim=1)
        u1 = self.conv1(u1)

        return self.out(u1)


def apply_lung_window(image, center=-600, width=1500):
    lower = center - width / 2
    upper = center + width / 2
    return np.clip(image, lower, upper)


def dicom_to_hu(ds):
    image = ds.pixel_array.astype(np.float32)

    slope = float(ds.get("RescaleSlope", 1))
    intercept = float(ds.get("RescaleIntercept", 0))

    hu_image = image * slope + intercept
    return hu_image


def preprocess_dicom_for_model(dicom_path):
    ds = pydicom.dcmread(dicom_path, force=True)

    hu_image = dicom_to_hu(ds)
    windowed = apply_lung_window(hu_image)

    min_val = windowed.min()
    max_val = windowed.max()

    normalized = (windowed - min_val) / (max_val - min_val + 1e-8)

    image_uint8 = (normalized * 255).astype(np.uint8)
    image_pil = Image.fromarray(image_uint8).resize((64, 64))

    image_np = np.array(image_pil).astype(np.float32) / 255.0

    tensor = torch.tensor(image_np).unsqueeze(0).unsqueeze(0)

    metadata = {
        "patient_id": str(ds.get("PatientID", "Not available")),
        "modality": str(ds.get("Modality", "Not available")),
        "instance_number": str(ds.get("InstanceNumber", "Not available")),
        "slice_location": str(ds.get("SliceLocation", "Not available")),
        "rows": str(ds.get("Rows", "Not available")),
        "columns": str(ds.get("Columns", "Not available")),
        "pixel_spacing": str(ds.get("PixelSpacing", "Not available")),
        "slice_thickness": str(ds.get("SliceThickness", "Not available")),
        "rescale_slope": str(ds.get("RescaleSlope", "Not available")),
        "rescale_intercept": str(ds.get("RescaleIntercept", "Not available")),
        "image_shape": str(ds.pixel_array.shape),
    }

    return tensor, metadata


def load_model(model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = UNetSmall().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    return model, device


def predict_mask(model, device, input_tensor, threshold=0.5):
    input_tensor = input_tensor.to(device)

    with torch.no_grad():
        logits = model(input_tensor)
        prob = torch.sigmoid(logits)
        mask = (prob > threshold).float()

    mask_np = mask.cpu().squeeze().numpy()
    probability_mean = float(prob.cpu().mean().item())
    mask_area_pixels = int(mask_np.sum())

    return {
        "roi_detected": mask_area_pixels > 0,
        "mask_area_pixels": mask_area_pixels,
        "probability_mean": round(probability_mean, 4),
    }


def suggest_icd(mask_area_pixels):
    if mask_area_pixels > 0:
        return {
            "suggested_finding": "Possible pulmonary nodule ROI detected",
            "icd_10_suggestion": "R91.1",
            "icd_description": "Solitary pulmonary nodule",
            "note": "For clinical documentation support only. Requires radiologist/coder review.",
        }

    return {
        "suggested_finding": "No ROI detected by baseline model",
        "icd_10_suggestion": "None",
        "icd_description": "No ICD suggestion generated",
        "note": "AI output is for review only and is not a diagnosis.",
    }