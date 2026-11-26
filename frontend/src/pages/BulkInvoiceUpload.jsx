
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  LoaderCircle,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";

import {
  uploadBulkInvoices,
  getBulkImportStatus,
} from "../api/documentApi";

const MAX_FILES = 10;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
];

function BulkInvoiceUpload() {
  const navigate = useNavigate();

  const [files, setFiles] = useState([]);
  const [batchId, setBatchId] = useState(null);
  const [batch, setBatch] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [rejectedFiles, setRejectedFiles] = useState([]);

  const [refreshing, setRefreshing] = useState(false);

  // Select and validate multiple files.
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(
      event.target.files || []
    );

    setError("");
    setSuccess("");
    setRejectedFiles([]);
    setBatch(null);
    setBatchId(null);

    if (selectedFiles.length === 0) {
      setFiles([]);
      return;
    }

    if (selectedFiles.length > MAX_FILES) {
      setError(
        `You can select a maximum of ${MAX_FILES} files.`
      );
      setFiles([]);
      event.target.value = "";
      return;
    }

    const validFiles = [];
    const rejected = [];

    selectedFiles.forEach((file) => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        rejected.push({
          name: file.name,
          reason: "Unsupported file type.",
        });
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        rejected.push({
          name: file.name,
          reason: "File exceeds 10 MB.",
        });
        return;
      }

      validFiles.push(file);
    });

    setFiles(validFiles);
    setRejectedFiles(rejected);

    if (validFiles.length === 0) {
      setError("No valid invoice files were selected.");
    }

    // Allow selecting the same files again later.
    event.target.value = "";
  };

  // Submit files to the backend.
  const handleUpload = async () => {
    if (files.length === 0) {
      setError("Please select invoice files first.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setSuccess("");
      setBatch(null);

      const result = await uploadBulkInvoices(files);

      setBatchId(result.batch_id);

      setSuccess(
        `${result.total_files} file(s) uploaded successfully.`
      );

      setFiles([]);

      setRejectedFiles(result.rejected_files || []);

    } catch (err) {
      console.error("Bulk upload failed:", err);

      setError(
        err.response?.data?.detail?.message ||
        err.response?.data?.detail ||
        err.message ||
        "Unable to upload invoice files."
      );

    } finally {
      setUploading(false);
    }
  };

  // Retrieve progress from the backend.
  const refreshBatch = async () => {
    if (!batchId) return;

    try {
      setRefreshing(true);

      const result = await getBulkImportStatus(batchId);

      setBatch(result);

    } catch (err) {
      console.error("Unable to retrieve batch status:", err);

      setError(
        "Unable to retrieve batch progress. Please refresh again."
      );

    } finally {
      setRefreshing(false);
    }
  };

  // Automatically poll while the batch is running.
  useEffect(() => {
    if (!batchId) return;

    let active = true;
    let timer;

    const loadStatus = async () => {
      try {
        const result = await getBulkImportStatus(batchId);

        if (!active) return;

        setBatch(result);

        const finished =
          result.status === "completed" ||
          result.status === "failed";

        if (!finished) {
          timer = setTimeout(loadStatus, 3000);
        }

      } catch (err) {
        console.error("Batch status polling failed:", err);

        if (active) {
          timer = setTimeout(loadStatus, 5000);
        }
      }
    };

    loadStatus();

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [batchId]);

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return (
          <span className="badge bg-success">
            Completed
          </span>
        );

      case "failed":
        return (
          <span className="badge bg-danger">
            Failed
          </span>
        );

      case "processing":
        return (
          <span className="badge bg-primary">
            Processing
          </span>
        );

      default:
        return (
          <span className="badge bg-secondary">
            Pending
          </span>
        );
    }
  };

  const progress = batch?.progress_percentage || 0;

  const isFinished =
    batch?.status === "completed" ||
    batch?.status === "failed";

  return (
    <div className="container-fluid">

      {/* Heading */}
      <div className="mb-4">

        <button
          className="btn btn-outline-secondary mb-3"
          onClick={() => navigate("/invoices")}
          disabled={uploading}
        >
          <ArrowLeft size={16} className="me-2" />
          Back to Invoices
        </button>

        <h3 className="fw-bold">
          Bulk Invoice Import
        </h3>

        <p className="text-muted">
          Upload multiple PDF or image invoices.
          Documents will be processed one at a time automatically.
        </p>

      </div>

      <div className="row justify-content-center">

        <div className="col-lg-9">

          {/* Upload card */}
          <div className="card border-0 shadow-sm mb-4">

            <div className="card-header bg-white py-3">

              <h5 className="mb-0">
                <FileText size={18} className="me-2" />
                Select Invoice Documents
              </h5>

            </div>

            <div className="card-body p-4">

              <div
                className="border border-2 border-dashed rounded p-5 text-center"
                style={{ backgroundColor: "#f8f9fa" }}
              >

                <Upload
                  size={45}
                  className="text-primary mb-3"
                />

                <h5>Select Multiple Invoice Files</h5>

                <p className="text-muted">
                  Choose up to 10 PDF, JPG or PNG files.
                </p>

                <input
                  type="file"
                  className="form-control mt-3"
                  accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                  multiple
                  onChange={handleFileChange}
                  disabled={uploading || Boolean(batchId)}
                />

                <small className="text-muted d-block mt-2">
                  Maximum 10 files · Maximum 10 MB per file
                </small>

              </div>

              {/* Selected files */}
              {files.length > 0 && (

                <div className="mt-4">

                  <h6>
                    Selected files ({files.length})
                  </h6>

                  {files.map((file, index) => (

                    <div
                      key={`${file.name}-${index}`}
                      className="alert alert-light border mb-2"
                    >

                      <div className="d-flex align-items-center">

                        <FileText
                          size={22}
                          className="text-primary me-3"
                        />

                        <div className="flex-grow-1">

                          <strong>{file.name}</strong>

                          <div className="small text-muted">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </div>

                        </div>

                      </div>

                    </div>

                  ))}

                </div>

              )}

              {/* Error */}
              {error && (

                <div className="alert alert-danger mt-3">

                  <AlertCircle
                    size={18}
                    className="me-2"
                  />

                  {typeof error === "string"
                    ? error
                    : "Bulk upload failed."}

                </div>

              )}

              {/* Success */}
              {success && (

                <div className="alert alert-success mt-3">

                  <CheckCircle
                    size={18}
                    className="me-2"
                  />

                  {success}

                </div>

              )}

              {/* Rejected files */}
              {rejectedFiles.length > 0 && (

                <div className="alert alert-warning mt-3">

                  <strong>
                    Some files were rejected:
                  </strong>

                  <ul className="mb-0 mt-2">

                    {rejectedFiles.map((item, index) => (

                      <li key={index}>
                        {item.filename || item.name}:{" "}
                        {item.error || item.reason}
                      </li>

                    ))}

                  </ul>

                </div>

              )}

              {/* Upload button */}
              <div className="d-flex justify-content-end mt-4">

                <button
                  className="btn btn-primary"
                  onClick={handleUpload}
                  disabled={
                    files.length === 0 ||
                    uploading ||
                    Boolean(batchId)
                  }
                >

                  {uploading ? (

                    <>
                      <LoaderCircle
                        size={16}
                        className="me-2 spin-animation"
                      />
                      Uploading...
                    </>

                  ) : (

                    <>
                      <Upload
                        size={16}
                        className="me-2"
                      />
                      Upload and Start Import
                    </>

                  )}

                </button>

              </div>

            </div>

          </div>

          {/* Batch progress */}
          {batchId && (

            <div className="card border-0 shadow-sm">

              <div className="card-header bg-white py-3">

                <div className="d-flex justify-content-between align-items-center">

                  <h5 className="mb-0">
                    Import Progress
                  </h5>

                  <button
                    className="btn btn-outline-primary btn-sm"
                    onClick={refreshBatch}
                    disabled={refreshing}
                  >

                    <RefreshCw
                      size={15}
                      className="me-1"
                    />

                    Refresh

                  </button>

                </div>

                <small className="text-muted">
                  Batch ID: {batchId}
                </small>

              </div>

              <div className="card-body p-4">

                {!batch ? (

                  <div className="text-center py-4">

                    <LoaderCircle
                      size={30}
                      className="spin-animation text-primary"
                    />

                    <p className="text-muted mt-2">
                      Loading import progress...
                    </p>

                  </div>

                ) : (

                  <>

                    <div className="d-flex justify-content-between mb-2">

                      <strong>
                        Overall Progress
                      </strong>

                      <strong>
                        {progress}%
                      </strong>

                    </div>

                    <div
                      className="progress mb-4"
                      style={{ height: "12px" }}
                    >

                      <div
                        className="progress-bar bg-success"
                        role="progressbar"
                        style={{ width: `${progress}%` }}
                        aria-valuenow={progress}
                        aria-valuemin="0"
                        aria-valuemax="100"
                      />

                    </div>

                    <div className="row text-center mb-4">

                      <div className="col-6 col-md-3 mb-3">

                        <h4>{batch.total_files}</h4>

                        <small className="text-muted">
                          Total
                        </small>

                      </div>

                      <div className="col-6 col-md-3 mb-3">

                        <h4 className="text-success">
                          {batch.completed_files}
                        </h4>

                        <small className="text-muted">
                          Completed
                        </small>

                      </div>

                      <div className="col-6 col-md-3 mb-3">

                        <h4 className="text-danger">
                          {batch.failed_files}
                        </h4>

                        <small className="text-muted">
                          Failed
                        </small>

                      </div>

                      <div className="col-6 col-md-3 mb-3">

                        <h4 className="text-secondary">
                          {batch.pending_files}
                        </h4>

                        <small className="text-muted">
                          Pending
                        </small>

                      </div>

                    </div>

                    <div className="mb-3">

                      <strong>Batch Status:</strong>{" "}

                      {getStatusBadge(batch.status)}

                      {batch.processing_files > 0 && (

                        <span className="text-muted ms-2 small">
                          {batch.processing_files} file(s) currently processing
                        </span>

                      )}

                    </div>

                    <div className="table-responsive">

                      <table className="table table-hover align-middle">

                        <thead>

                          <tr>
                            <th>File</th>
                            <th>Status</th>
                            <th>Result</th>
                          </tr>

                        </thead>

                        <tbody>

                          {batch.files.map((item) => (

                            <tr key={item.id}>

                              <td>
                                <FileText
                                  size={16}
                                  className="me-2 text-primary"
                                />

                                {item.filename}
                              </td>

                              <td>
                                {getStatusBadge(item.status)}
                              </td>

                              <td>

                                {item.invoice_id ? (

                                  <button
                                    className="btn btn-sm btn-outline-primary"
                                    onClick={() =>
                                      navigate(
                                        `/invoices/${item.invoice_id}`
                                      )
                                    }
                                  >
                                    View Invoice
                                  </button>

                                ) : item.error_message ? (

                                  <span
                                    className="text-danger small"
                                    title={item.error_message}
                                  >
                                    {item.error_message}
                                  </span>

                                ) : (

                                  <span className="text-muted small">
                                    -
                                  </span>

                                )}

                              </td>

                            </tr>

                          ))}

                        </tbody>

                      </table>

                    </div>

                    {isFinished && (

                      <div
                        className={`alert ${
                          batch.failed_files > 0
                            ? "alert-warning"
                            : "alert-success"
                        } mt-3 mb-0`}
                      >

                        <strong>
                          Import finished.
                        </strong>

                        <div>
                          {batch.completed_files} completed and{" "}
                          {batch.failed_files} failed.
                        </div>

                      </div>

                    )}

                  </>

                )}

              </div>

            </div>

          )}

        </div>

      </div>

    </div>
  );
}

export default BulkInvoiceUpload;