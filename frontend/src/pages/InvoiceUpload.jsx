
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  LoaderCircle,
  ArrowLeft,
} from "lucide-react";

import {
  uploadDocument,
  extractDocument,
  processInvoice,
} from "../api/documentApi";

function InvoiceUpload() {
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setError("");
    setSuccess("");

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "image/jpeg",
      "image/png",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError("Only PDF, JPG and PNG files are allowed.");
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("File size must not exceed 10 MB.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select an invoice first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");

      // Step 1: Upload document
      setStep("Uploading invoice document...");

      const uploadedDocument = await uploadDocument(file);

      const documentId = uploadedDocument.id;

      // Step 2: Extract document text
      setStep("Extracting text from invoice...");

      await extractDocument(documentId);

      // Step 3: Process invoice
      setStep("Processing invoice information...");

      const result = await processInvoice(documentId);

      if (!result.invoice_id) {
        throw new Error("Invoice processing did not return an invoice ID.");
      }

      setStep("Completed successfully!");
      setSuccess("Invoice uploaded and processed successfully.");

      // Navigate to invoice details
      navigate(`/invoices/${result.invoice_id}`);

    } catch (err) {
      console.error("Invoice upload error:", err);

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Unable to upload and process invoice."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid">

      {/* Heading */}
      <div className="mb-4">

        <button
          className="btn btn-outline-secondary mb-3"
          onClick={() => navigate("/invoices")}
          disabled={loading}
        >
          <ArrowLeft size={16} className="me-2" />
          Back to Invoices
        </button>

        <h3 className="fw-bold">Upload Invoice</h3>

        <p className="text-muted">
          Upload PDF or image invoices for automatic extraction
          and processing.
        </p>

      </div>

      {/* Upload Card */}
      <div className="row justify-content-center">

        <div className="col-lg-7">

          <div className="card border-0 shadow-sm">

            <div className="card-header bg-white py-3">
              <h5 className="mb-0">
                <FileText size={18} className="me-2" />
                Invoice Document
              </h5>
            </div>

            <div className="card-body p-4">

              {/* File Selection */}
              <div
                className="border border-2 border-dashed rounded p-5 text-center"
                style={{ backgroundColor: "#f8f9fa" }}
              >

                <Upload
                  size={45}
                  className="text-primary mb-3"
                />

                <h5>Select Invoice File</h5>

                <p className="text-muted">
                  Choose a PDF, JPG or PNG document.
                </p>

                <input
                  type="file"
                  className="form-control mt-3"
                  accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                  onChange={handleFileChange}
                  disabled={loading}
                />

                <small className="text-muted d-block mt-2">
                  Maximum file size: 10 MB
                </small>

              </div>

              {/* Selected File */}
              {file && (
                <div className="alert alert-light border mt-4">

                  <div className="d-flex align-items-center">

                    <FileText
                      size={25}
                      className="text-primary me-3"
                    />

                    <div>
                      <strong>{file.name}</strong>

                      <div className="text-muted small">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>

                  </div>

                </div>
              )}

              {/* Error */}
              {error && (
                <div className="alert alert-danger mt-3">
                  <AlertCircle size={18} className="me-2" />
                  {error}
                </div>
              )}

              {/* Success */}
              {success && (
                <div className="alert alert-success mt-3">
                  <CheckCircle size={18} className="me-2" />
                  {success}
                </div>
              )}

              {/* Processing Status */}
              {loading && (
                <div className="alert alert-info mt-3">

                  <LoaderCircle
                    size={20}
                    className="spin-animation me-2"
                  />

                  {step}

                </div>
              )}

              {/* Upload Button */}
              <div className="d-flex justify-content-end mt-4">

                <button
                  className="btn btn-primary"
                  onClick={handleUpload}
                  disabled={!file || loading}
                >

                  {loading ? (
                    <>
                      <LoaderCircle
                        size={16}
                        className="spin-animation me-2"
                      />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload size={16} className="me-2" />
                      Upload and Process
                    </>
                  )}

                </button>

              </div>

            </div>
          </div>

        </div>
      </div>

    </div>
  );
}

export default InvoiceUpload;
