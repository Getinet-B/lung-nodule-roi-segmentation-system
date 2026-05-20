\# Lung Nodule ROI Segmentation System



\## Project Overview



This project is an AI-assisted lung nodule ROI segmentation proof-of-concept built using:



\- React frontend

\- FastAPI backend

\- PyTorch U-Net segmentation model

\- DICOM CT image processing

\- ICD-10 documentation support



The system allows a user to:



1\. Upload a DICOM CT slice

2\. Generate a DICOM preview

3\. Select/crop a suspected ROI

4\. Run U-Net segmentation inference

5\. Receive AI-assisted ROI and ICD support output



\---



\## Completed Features



\- DICOM ingestion and parsing pipeline

\- CT modality filtering

\- SEG modality filtering

\- SR modality filtering

\- Patient-level dataset split

\- 3D CT volume loading

\- Hounsfield Unit conversion

\- DICOM SEG ingestion

\- DICOM SR metadata extraction

\- CT + SEG + SR patient registry

\- Image-mask pair preparation

\- Baseline U-Net segmentation model

\- Dice coefficient evaluation

\- IoU evaluation

\- Accuracy evaluation

\- Sensitivity / Recall / TPR evaluation

\- Specificity evaluation

\- Precision / PPV evaluation

\- Hausdorff Distance evaluation

\- Hausdorff 95 evaluation

\- Average Surface Distance evaluation

\- React frontend deployment

\- FastAPI backend deployment

\- ROI crop workflow

\- ICD-10 documentation support



\---



\## Running the Project



\### Backend



```bash

cd backend

python -m venv .venv

.venv\\Scripts\\activate

pip install -r requirements.txt

uvicorn main:app --reload

```



Backend runs on:



```text

http://127.0.0.1:8000

```



\---



\### Frontend



```bash

cd lung-nodule-frontend

npm install

npm run dev

```



Frontend runs on:



```text

http://localhost:5173

```



\---



\## Trained Model



The trained U-Net model is already included in:



```text

backend/models/best\_lidc\_unet.pth

```



No external model download is required.



\---



\## Sample DICOM Files



Example DICOM CT files for testing are included in:



```text

sample\_dicoms/

```



Recommended workflow:



1\. Upload sample DICOM

2\. Generate DICOM preview

3\. Select/crop suspected ROI

4\. Run ROI segmentation

5\. Review AI output



\---



\## Clinical Disclaimer



This project is a research and educational proof-of-concept only.



The system is not FDA-approved and is not intended for clinical diagnosis or treatment decisions.



AI output is for radiology review support only.



\---



\## Future Improvements



\- Full CT slice nodule detection

\- Automated ROI localization

\- PACS / DICOMweb integration

\- Authentication and user management

\- Clinical workflow integration

\- Docker and cloud deployment

\- Multi-nodule detection support

