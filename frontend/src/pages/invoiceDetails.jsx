
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, LoaderCircle } from "lucide-react";
import {
  getInvoiceDetails,
  downloadInvoiceDocument,
} from "../api/invoiceApi";


function InvoiceDetails() {
  const { invoiceId } = useParams();
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [documentUrl, setDocumentUrl] = useState("");
const [documentLoading, setDocumentLoading] = useState(false);
const [documentError, setDocumentError] = useState("");

  useEffect(() => {
    const fetchInvoice = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getInvoiceDetails(invoiceId);

        setInvoice(data);
      } catch (err) {
        console.error("Invoice details error:", err);

        setError(
          err.response?.data?.detail ||
          "Unable to retrieve invoice details."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchInvoice();
  }, [invoiceId]);

useEffect(() => {
  if (!invoice?.document_id) {
    setDocumentUrl("");
    return;
  }

  let objectUrl;

  const fetchDocument = async () => {
    try {
      setDocumentLoading(true);
      setDocumentError("");
      setDocumentUrl("");

      const response = await downloadInvoiceDocument(
        invoice.document_id
      );

      const blob = response.data;

      if (!blob || blob.size === 0) {
        throw new Error("The document is empty.");
      }

      objectUrl = URL.createObjectURL(blob);
      setDocumentUrl(objectUrl);

    } catch (err) {
      console.error("Document preview error:", err);

      setDocumentError(
        "Unable to load the original invoice document."
      );

    } finally {
      setDocumentLoading(false);
    }
  };

  fetchDocument();

  return () => {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
    }
  };

}, [invoice?.document_id]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <LoaderCircle className="spin-animation" />
        <p className="mt-2">Loading invoice details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        {error}

        <button
          className="btn btn-outline-danger btn-sm ms-3"
          onClick={() => navigate("/invoices")}
        >
          Back to Invoices
        </button>
      </div>
    );
  }

  if (!invoice) return null;

  return (
    <div className="container-fluid">

      <button
        className="btn btn-outline-secondary mb-3"
        onClick={() => navigate("/invoices")}
      >
        <ArrowLeft size={16} className="me-2" />
        Back to Invoices
      </button>

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3>Invoice Details</h3>
          <p className="text-muted">
            View original invoice and extracted information.
          </p>
        </div>

        <span className="badge bg-warning text-dark">
          {invoice.processing_status}
        </span>
      </div>

      <div className="row g-4">

        {/* Original Document Panel */}
        <div className="col-lg-6">
          <div className="card h-100">
           <div className="card-header fw-semibold d-flex justify-content-between align-items-center">
  <span>
    <FileText size={18} className="me-2" />
    Original Invoice Document
  </span>

  {documentUrl && (
    <a
      href={documentUrl}
      download={
        invoice.document?.original_filename || "invoice"
      }
      className="btn btn-sm btn-outline-primary"
    >
      Download
    </a>
  )}
</div>

            <div className="card-body">
              <p className="text-muted">
                {invoice.document?.original_filename || "Document"}
              </p>

              <div
  className="border rounded bg-light"
  style={{ minHeight: "650px", overflow: "auto" }}
>
  {documentLoading && (
    <div className="text-center py-5">
      <LoaderCircle className="spin-animation" size={30} />
      <p className="mt-2">Loading original document...</p>
    </div>
  )}

  {documentError && (
    <div className="alert alert-danger m-3">
      {documentError}
    </div>
  )}

  {!documentLoading &&
    !documentError &&
    documentUrl &&
    invoice.document?.content_type === "application/pdf" && (
      <iframe
  src={documentUrl}
  title="Original Invoice PDF"
  width="100%"
  height="750"
  style={{
    border: "none",
    display: "block",
  }}
/>
    )}

  {!documentLoading &&
    !documentError &&
    documentUrl &&
    invoice.document?.content_type?.startsWith("image/") && (
      <div className="text-center p-3">
        <img
          src={documentUrl}
          alt="Original Invoice"
          className="img-fluid"
          style={{
            maxHeight: "750px",
            objectFit: "contain",
          }}
        />
      </div>
    )}

  {!documentLoading &&
    !documentError &&
    documentUrl &&
    !["application/pdf"].includes(
      invoice.document?.content_type
    ) &&
    !invoice.document?.content_type?.startsWith("image/") && (
      <div className="text-center p-5">
        <FileText size={40} />
        <p className="mt-3">
          Preview is not supported for this file type.
        </p>
      </div>
    )}
</div>
            </div>
          </div>
        </div>

        {/* Extracted Information Panel */}
        <div className="col-lg-6">
          <div className="card">
            <div className="card-header fw-semibold">
              Extracted Invoice Information
            </div>

            <div className="card-body">

              <h5>Invoice Information</h5>

              <p>
                <strong>Invoice Number:</strong>{" "}
                {invoice.invoice_number || "N/A"}
              </p>

              <p>
                <strong>Purchase Order:</strong>{" "}
                {invoice.purchase_order_number || "N/A"}
              </p>

              <p>
                <strong>Supplier:</strong>{" "}
                {invoice.supplier?.name || "N/A"}
              </p>

              <p>
                <strong>Supplier Tax ID:</strong>{" "}
                {invoice.supplier?.tax_id || "N/A"}
              </p>

              <p>
                <strong>Invoice Date:</strong>{" "}
                {invoice.invoice_date || "N/A"}
              </p>

              <p>
                <strong>Due Date:</strong>{" "}
                {invoice.due_date || "N/A"}
              </p>

              <p>
                <strong>Payment Terms:</strong>{" "}
                {invoice.payment_terms || "N/A"}
              </p>

              <hr />

              <h5>Financial Information</h5>

              <p>
                <strong>Currency:</strong>{" "}
                {invoice.currency || "N/A"}
              </p>

              <p>
                <strong>Subtotal:</strong>{" "}
                {invoice.subtotal ?? "N/A"}
              </p>

              <p>
                <strong>Tax:</strong>{" "}
                {invoice.tax ?? "N/A"}
              </p>

              <p>
                <strong>Discount:</strong>{" "}
                {invoice.discount ?? "N/A"}
              </p>

              <h5 className="text-success mt-3">
                Total: {invoice.currency || ""}{" "}
                {invoice.total_amount ?? "N/A"}
              </h5>

              <hr />

              <h5>Line Items</h5>

              {invoice.line_items?.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-bordered table-sm">
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                      </tr>
                    </thead>

                    <tbody>
                      {invoice.line_items.map((item) => (
                        <tr key={item.id}>
                          <td>{item.description}</td>
                          <td>{item.quantity}</td>
                          <td>{item.unit_price}</td>
                          <td>{item.line_total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted">
                  No line items available.
                </p>
              )}

            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

export default InvoiceDetails;