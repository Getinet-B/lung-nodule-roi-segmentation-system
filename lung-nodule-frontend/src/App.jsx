import { useState } from "react";
import ReactCrop from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";
import "./App.css";

function App() {

  const API_BASE_URL = "https://lung-nodule-backend.onrender.com";

  const sampleDicoms = [
    "1-001.dcm",
    "1-020.dcm",
    "1-035.dcm",
    "1-040.dcm",
    "1-055.dcm",
  ];

  const [file, setFile] = useState(null);
  const [selectedSample, setSelectedSample] = useState("");
  const [preview, setPreview] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const [crop, setCrop] = useState({
    unit: "px",
    x: 100,
    y: 100,
    width: 150,
    height: 150,
  });

  const [result, setResult] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingPrediction, setLoadingPrediction] = useState(false);

  // ===============================
  // MANUAL DICOM UPLOAD PREVIEW
  // ===============================

  const handlePreview = async () => {

    if (!file) {
      alert("Please select a DICOM file first.");
      return;
    }

    setLoadingPreview(true);
    setResult(null);

    try {

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE_URL}/preview`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (data.status === "success") {

        setPreview(data.preview_image);
        setMetadata(data.dicom_metadata);

      } else {

        setResult(data);

        alert(
          data.message || "Preview generation failed."
        );
      }

    } catch (error) {

      console.error(error);

      setResult({
        status: "error",
        message:
          "Could not connect to cloud backend. Render free services may take 30-60 seconds to wake up.",
      });

    } finally {

      setLoadingPreview(false);
    }
  };

  // ===============================
  // LOAD BUILT-IN SAMPLE DICOM
  // ===============================

  const loadSampleDicom = async () => {

    if (!selectedSample) {
      alert("Please select a sample DICOM.");
      return;
    }

    try {

      const response = await fetch(
        `${API_BASE_URL}/preview-sample/${selectedSample}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (data.status === "success") {

        setPreview(data.preview_image);
        setMetadata(data.dicom_metadata);

        setFile({
          name: selectedSample,
        });

        setResult(null);

      } else {

        setResult(data);

        alert(
          data.message || "Failed to load sample DICOM."
        );
      }

    } catch (error) {

      console.error(error);

      setResult({
        status: "error",
        message:
          "Could not connect to cloud backend sample DICOM service.",
      });

      alert("Failed to load sample DICOM.");
    }
  };

  // ===============================
  // ROI SEGMENTATION
  // ===============================

  const handlePredictROI = async () => {

    if (!preview) {
      alert("Please generate the DICOM preview first.");
      return;
    }

    setLoadingPrediction(true);
    setResult(null);

    try {

      const response = await fetch(
        `${API_BASE_URL}/predict-roi`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            image_base64: preview,
            x: Math.round(crop.x),
            y: Math.round(crop.y),
            width: Math.round(crop.width),
            height: Math.round(crop.height),
          }),
        }
      );

      const data = await response.json();

      setResult(data);

    } catch (error) {

      console.error(error);

      setResult({
        status: "error",
        message:
          "Could not connect to cloud AI backend. Render may still be waking up.",
      });

    } finally {

      setLoadingPrediction(false);
    }
  };

  // ===============================
  // UI
  // ===============================

  return (

    <div className="app">

      <h1>Lung Nodule ROI Segmentation System</h1>

      <p className="subtitle">
        AI-assisted ROI segmentation.
        Upload a CT slice, select the suspected ROI,
        and run U-Net segmentation.
      </p>

      <p className="note">
        This prototype focuses on ROI segmentation.
        The current U-Net model assumes the ROI has already been localized.
        Future work will add full-slice detection/localization before segmentation.
      </p>

      {/* =============================== */}
      {/* UPLOAD SECTION */}
      {/* =============================== */}

      <div className="upload-card">

        <h2>1. Upload DICOM CT Slice</h2>

        <input
          type="file"
          accept=".dcm"
          onChange={(e) => setFile(e.target.files[0])}
        />

        {/* BUILT-IN SAMPLE DICOMS */}

        <div style={{ marginTop: "20px" }}>

          <h3>Or Use a Built-in Sample DICOM</h3>

          <select
            value={selectedSample}
            onChange={(e) => setSelectedSample(e.target.value)}
          >

            <option value="">
              Select sample DICOM
            </option>

            {sampleDicoms.map((sample) => (

              <option
                key={sample}
                value={sample}
              >
                {sample}
              </option>

            ))}

          </select>

          <button onClick={loadSampleDicom}>
            Load Sample DICOM
          </button>

        </div>

        {file && (
          <p>
            <strong>Selected file:</strong> {file.name}
          </p>
        )}

        <button
          onClick={handlePreview}
          disabled={loadingPreview}
        >
          {loadingPreview
            ? "Generating Preview..."
            : "Generate DICOM Preview"}
        </button>

      </div>

      {/* =============================== */}
      {/* METADATA */}
      {/* =============================== */}

      {metadata && (

        <div className="result-card">

          <h2>DICOM Metadata</h2>

          <p><strong>Patient ID:</strong> {metadata.patient_id}</p>
          <p><strong>Modality:</strong> {metadata.modality}</p>
          <p><strong>Instance Number:</strong> {metadata.instance_number}</p>
          <p><strong>Slice Location:</strong> {metadata.slice_location}</p>
          <p><strong>Rows:</strong> {metadata.rows}</p>
          <p><strong>Columns:</strong> {metadata.columns}</p>
          <p><strong>Image Shape:</strong> {metadata.image_shape}</p>

        </div>
      )}

      {/* =============================== */}
      {/* ROI CROP */}
      {/* =============================== */}

      {preview && (

        <div className="result-card">

          <h2>2. Select Suspected ROI</h2>

          <ReactCrop
            crop={crop}
            onChange={(newCrop) => setCrop(newCrop)}
          >

            <img
              src={preview}
              alt="DICOM Preview"
              className="dicom-preview"
            />

          </ReactCrop>

          <button
            onClick={handlePredictROI}
            disabled={loadingPrediction}
          >
            {loadingPrediction
              ? "Running U-Net..."
              : "Run ROI Segmentation"}
          </button>

        </div>
      )}

      {/* =============================== */}
      {/* RESULTS */}
      {/* =============================== */}

      {result && (

        <div className="result-card">

          <h2>AI Output</h2>

          <p><strong>Status:</strong> {result.status}</p>

          <p>
            <strong>Backend Message:</strong> {result.message}
          </p>

          {result.prediction && (
            <>

              <h3>AI Segmentation Result</h3>

              <p>
                <strong>ROI Detected:</strong>
                {" "}
                {String(result.prediction.roi_detected)}
              </p>

              <p>
                <strong>Mask Area Pixels:</strong>
                {" "}
                {result.prediction.mask_area_pixels}
              </p>

              <p>
                <strong>Mean Probability:</strong>
                {" "}
                {result.prediction.probability_mean}
              </p>

              <p>
                <strong>Finding:</strong>
                {" "}
                {result.prediction.suggested_finding}
              </p>

              <h3>ICD-10 Documentation Support</h3>

              <p>
                <strong>ICD-10 Suggestion:</strong>
                {" "}
                {result.prediction.icd_10_suggestion}
              </p>

              <p>
                <strong>ICD Description:</strong>
                {" "}
                {result.prediction.icd_description}
              </p>

              <p>
                <strong>Clinical Note:</strong>
                {" "}
                {result.prediction.note}
              </p>

            </>
          )}

          <div className="warning">
            AI output is for clinical review support only.
            It is not a final diagnosis.
          </div>

        </div>
      )}

    </div>
  );
}

export default App;
