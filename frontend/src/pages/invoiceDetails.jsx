
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  LoaderCircle,
  Download,
  CalendarDays,
  Building2,
  Receipt,
} from "lucide-react";
import {
  getInvoiceDetails,
  downloadInvoiceDocument,
  getInvoiceAuditLogs,
} from "../api/invoiceApi";
//

// -----------------------------------------
// Helper: Format missing values
// -----------------------------------------

const displayValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  return value;
};

const formatAuditValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  if (Array.isArray(value)) {
    return (
      <div>
        {value.map((item, index) => (
          <div
            key={index}
            className="border rounded p-2 mb-2 bg-light"
          >
            <strong>Item {index + 1}</strong>

            {Object.entries(item).map(([key, val]) => (
              <div key={key} className="small mt-1">
                <span className="text-muted">
                  {key.replaceAll("_", " ")}:
                </span>{" "}
                <strong>
                  {val === null || val === undefined || val === ""
                    ? "N/A"
                    : String(val)}
                </strong>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
};

const formatAuditAction = (action) => {
  const actions = {
    INVOICE_FIELD_UPDATED: "Field Updated",
    invoice_extracted: "Invoice Extracted",
  };

  return actions[action] || action;
};

const formatFieldName = (field) => {
  if (!field) return "N/A";

  return field
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
};


// -----------------------------------------
// Helper: Currency formatting
// -----------------------------------------

const formatCurrency = (value, currency) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return "N/A";
  }

  if (!currency) {
    return amount.toFixed(2);
  }

  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
};

// -----------------------------------------
// Helper: Format quantity
// -----------------------------------------

const formatNumber = (value) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toLocaleString("en-IN", {
        maximumFractionDigits: 4,
      })
    : "N/A";
};



// -----------------------------------------
// Helper: Format invoice dates
// -----------------------------------------

const formatDate = (value) => {
  if (!value) {
    return "N/A";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
};


// -----------------------------------------
// Helper: Basic financial consistency check
// -----------------------------------------

const checkFinancialConsistency = (invoice) => {
  const { subtotal, tax, discount, total_amount } = invoice;

  const values = [subtotal, tax, discount, total_amount];

  if (
    values.some(
      (value) =>
        value === null ||
        value === undefined ||
        value === "" ||
        !Number.isFinite(Number(value))
    )
  ) {
    return {
      available: false,
      message: "Insufficient financial information for comparison.",
    };
  }

  const expectedTotal =
    Number(subtotal) +
    Number(tax) -
    Number(discount);

  const actualTotal = Number(total_amount);

  const difference = Math.abs(expectedTotal - actualTotal);

  if (difference <= 0.02) {
    return {
      available: true,
      valid: true,
      expectedTotal,
      actualTotal,
      difference,
      message: "Basic financial calculation is consistent.",
    };
  }

  return {
    available: true,
    valid: false,
    expectedTotal,
    actualTotal,
    difference,
    message: "Financial values require manual verification.",
  };
};

// -----------------------------------------
// Reusable information row
// -----------------------------------------

function InfoRow({ label, value }) {
  return (
    <div className="d-flex justify-content-between border-bottom py-2 gap-3">
      <span className="text-muted">{label}</span>
      <strong className="text-end">
        {displayValue(value)}
      </strong>
    </div>
  );
}

// -----------------------------------------
// Main Component
// -----------------------------------------

function InvoiceDetails() {
  const { invoiceId } = useParams();
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [documentUrl, setDocumentUrl] = useState("");
  const [documentLoading, setDocumentLoading] = useState(false);
  const [documentError, setDocumentError] = useState("");
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditError, setAuditError] = useState("");

  // ---------------------------------------
  // Retrieve invoice details
  // ---------------------------------------

  useEffect(() => {
    let active = true;

    const fetchInvoice = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getInvoiceDetails(invoiceId);

        if (active) {
          setInvoice(data);
        }
      } catch (err) {
        console.error("Invoice details error:", err);

        if (active) {
          setError(
            err.response?.data?.detail ||
              "Unable to retrieve invoice details."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    setInvoice(null);
    fetchInvoice();

    return () => {
      active = false;
    };
  }, [invoiceId]);

  // ---------------------------------------
  // Retrieve original document
  // ---------------------------------------

  useEffect(() => {
    if (!invoice?.document_id) {
      setDocumentUrl("");
      setDocumentLoading(false);
      return;
    }

    let active = true;
    let objectUrl = null;

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

        if (active) {
          setDocumentUrl(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      } catch (err) {
        console.error("Document preview error:", err);

        if (active) {
          setDocumentError(
            "Unable to load the original invoice document."
          );
        }
      } finally {
        if (active) {
          setDocumentLoading(false);
        }
      }
    };

    fetchDocument();

    return () => {
      active = false;

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [invoice?.document_id]);

  useEffect(() => {
  let active = true;

  const fetchAuditLogs = async () => {
    try {
      setAuditLoading(true);
      setAuditError("");

      const response = await getInvoiceAuditLogs(invoiceId);

      if (active) {
        setAuditLogs(response.audit_logs || []);
      }
    } catch (err) {
      console.error("Audit history error:", err);

      if (active) {
        setAuditError("Unable to retrieve audit history.");
      }
    } finally {
      if (active) {
        setAuditLoading(false);
      }
    }
  };

  fetchAuditLogs();

  return () => {
    active = false;
  };
}, [invoiceId]);
  // ---------------------------------------
  // Loading state
  // ---------------------------------------

  if (loading) {
    return (
      <div className="text-center py-5">
        <LoaderCircle className="spin-animation" size={35} />
        <p className="mt-2">Loading invoice details...</p>
      </div>
    );
  }

  // ---------------------------------------
  // Error state
  // ---------------------------------------

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

  const currency = invoice.currency;
  const financialCheck = checkFinancialConsistency(invoice);
  const contentType = invoice.document?.content_type || "";

  const isPdf = contentType === "application/pdf";
  const isImage = contentType.startsWith("image/");

  // ---------------------------------------
  // Render
  // ---------------------------------------

  return (
    <div className="container-fluid py-3">

      {/* Back button */}

      

      {/* Page heading */}

      <div className="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
{/* Back and Edit buttons */}

<div className="d-flex justify-content-between align-items-center mb-4">

  <button
    className="btn btn-outline-secondary"
    onClick={() => navigate("/invoices")}
  >
    <ArrowLeft size={16} className="me-2" />
    Back to Invoices
  </button>

  <button
    className="btn btn-primary"
    onClick={() => navigate(`/invoices/${invoiceId}/edit`)}
  >
    Edit Invoice
  </button>

</div>
        <div>
          <h3 className="fw-bold mb-1">
            Invoice Details
          </h3>

          <p className="text-muted mb-0">
            Original invoice document and extracted information.
          </p>
        </div>

        <span className="badge bg-warning text-dark px-3 py-2">
          {displayValue(invoice.processing_status)}
        </span>

      </div>

      <div className="row g-4">

        {/* ================================= */}
        {/* ORIGINAL DOCUMENT PANEL */}
        {/* ================================= */}

        <div className="col-lg-6">

          <div className="card shadow-sm h-100">

            <div className="card-header bg-white d-flex justify-content-between align-items-center flex-wrap gap-2">

              <h5 className="mb-0 fw-semibold">
                <FileText size={19} className="me-2" />
                Original Invoice
              </h5>

              {documentUrl && (
                <a
                  href={documentUrl}
                  download={
                    invoice.document?.original_filename || "invoice"
                  }
                  className="btn btn-sm btn-primary"
                >
                  <Download size={15} className="me-1" />
                  Download
                </a>
              )}

            </div>

            <div className="card-body">

              <p className="text-muted small mb-3">
                {displayValue(
                  invoice.document?.original_filename
                )}
              </p>

              <div
                className="border rounded bg-light"
                style={{
                  minHeight: "650px",
                  overflow: "auto",
                }}
              >

                {documentLoading && (
                  <div className="text-center py-5">
                    <LoaderCircle
                      className="spin-animation"
                      size={32}
                    />
                    <p className="mt-2">
                      Loading original document...
                    </p>
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
                  isPdf && (
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
                  isImage && (
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
                  !isPdf &&
                  !isImage && (
                    <div className="text-center p-5">
                      <FileText size={40} />

                      <p className="mt-3">
                        Preview is not supported for this file type.
                      </p>
                    </div>
                  )}

                {!documentLoading &&
                  !documentError &&
                  !documentUrl && (
                    <div className="text-center py-5 text-muted">
                      Original document is unavailable.
                    </div>
                  )}

              </div>

            </div>
          </div>
        </div>

        {/* ================================= */}
        {/* EXTRACTED INFORMATION */}
        {/* ================================= */}

        <div className="col-lg-6">

          {/* Invoice Information */}

          <div className="card shadow-sm mb-4">

            <div className="card-header bg-white">
              <h5 className="fw-semibold mb-0">
                <Receipt size={19} className="me-2" />
                Invoice Information
              </h5>
            </div>

            <div className="card-body">

              <InfoRow
                label="Invoice Number"
                value={invoice.invoice_number}
              />

              <InfoRow
                label="Purchase Order"
                value={invoice.purchase_order_number}
              />

              <InfoRow
                label="Supplier"
                value={invoice.supplier?.name}
              />

              <InfoRow
                label="Supplier Tax ID"
                value={invoice.supplier?.tax_id}
              />
<InfoRow
  label="Shipping Charges"
  value={formatCurrency(invoice.shipping_charges, currency)}
/>

<InfoRow
  label="Other Charges"
  value={formatCurrency(invoice.other_charges, currency)}
/>
              <InfoRow
  label="Invoice Date"
  value={formatDate(invoice.invoice_date)}
/>

<InfoRow
  label="Due Date"
  value={formatDate(invoice.due_date)}
/>

              

              <InfoRow
                label="Payment Terms"
                value={invoice.payment_terms}
              />

            </div>
          </div>

          {/* Financial Summary */}

          <div className="card shadow-sm mb-4">

            <div className="card-header bg-white">
              <h5 className="fw-semibold mb-0">
                <Building2 size={19} className="me-2" />
                Financial Summary
              </h5>
            </div>

            
<div className="card-body">

  <InfoRow
    label="Currency"
    value={displayValue(currency)}
  />

  <InfoRow
    label="Subtotal"
    value={formatCurrency(invoice.subtotal, currency)}
  />

  <InfoRow
    label="Tax Amount"
    value={formatCurrency(invoice.tax, currency)}
  />

  <InfoRow
    label="Discount"
    value={formatCurrency(invoice.discount, currency)}
  />

  <div className="d-flex justify-content-between align-items-center mt-3 p-3 bg-light rounded">

    <strong className="fs-5">
      Total Invoice Amount
    </strong>

    <strong className="fs-5 text-success">
      {formatCurrency(invoice.total_amount, currency)}
    </strong>

  </div>

  <p className="text-muted small mt-2 mb-0">
    Financial values are displayed as extracted or stored.
    Missing information is not automatically calculated.
  </p>

</div>

          </div>

        </div>

      </div>



{/* Financial Consistency Check */}

<div className="card shadow-sm mb-4">

  <div className="card-header bg-white">
    <h5 className="fw-semibold mb-0">
      Financial Verification
    </h5>
  </div>

  <div className="card-body">

    {!financialCheck.available ? (

      <div className="alert alert-secondary mb-0">
        {financialCheck.message}
      </div>

    ) : (

      <>
        <div
          className={`alert ${
            financialCheck.valid
              ? "alert-success"
              : "alert-warning"
          } mb-3`}
        >
          <strong>
            {financialCheck.valid
              ? "Calculation Consistent"
              : "Manual Verification Required"}
          </strong>

          <p className="mb-0 mt-1">
            {financialCheck.message}
          </p>
        </div>

        <InfoRow
          label="Calculated Total"
          value={formatCurrency(
            financialCheck.expectedTotal,
            currency
          )}
        />

        <InfoRow
          label="Extracted Total"
          value={formatCurrency(
            financialCheck.actualTotal,
            currency
          )}
        />

        <InfoRow
          label="Difference"
          value={formatCurrency(
            financialCheck.difference,
            currency
          )}
        />
      </>

    )}

  </div>
</div>

      {/* ================================= */}
      {/* LINE ITEMS */}
      {/* ================================= */}

      <div className="card shadow-sm mt-4">

        <div className="card-header bg-white">

          <h5 className="fw-semibold mb-0">
            Line Items
          </h5>

        </div>

        <div className="card-body">

          {invoice.line_items?.length > 0 ? (

            <div className="table-responsive">

              <table className="table table-bordered table-hover align-middle">

               <thead className="table-light">
  <tr>
    <th>#</th>
    <th>Description</th>
    <th>Quantity</th>
    <th>Unit Price</th>
    <th>Tax Rate</th>
    <th>Tax Amount</th>
    <th>Line Total</th>
  </tr>
</thead>

                <tbody>

  {invoice.line_items.map((item, index) => (

    <tr key={item.id || index}>

      <td>{index + 1}</td>

      <td>
        {displayValue(item.description)}
      </td>

      <td>
        {formatNumber(item.quantity)}
      </td>

      <td>
        {formatCurrency(item.unit_price, currency)}
      </td>

      <td>
        {item.tax_rate == null
          ? "N/A"
          : `${formatNumber(item.tax_rate)}%`}
      </td>

      <td>
        {formatCurrency(item.tax_amount, currency)}
      </td>

      <td className="fw-semibold">
        {formatCurrency(item.line_total, currency)}
      </td>

    </tr>

  ))}

</tbody>

              </table>

            </div>

          ) : (

            <p className="text-muted mb-0">
              No line items available.
            </p>

          )}
          


{/* ================================= */}
{/* AUDIT HISTORY */}
{/* ================================= */}

<div className="card shadow-sm mt-4 mb-4">

  <div className="card-header bg-white d-flex justify-content-between align-items-center">
    <h5 className="fw-semibold mb-0">
      Audit History
    </h5>

    <span className="badge bg-secondary">
      {auditLogs.length} Records
    </span>
  </div>

  <div className="card-body">

    {auditLoading ? (

      <div className="text-center py-4">
        <LoaderCircle className="spin-animation" size={30} />
        <p className="text-muted mt-2 mb-0">
          Loading audit history...
        </p>
      </div>

    ) : auditError ? (

      <div className="alert alert-danger mb-0">
        {auditError}
      </div>

    ) : auditLogs.length === 0 ? (

      <div className="text-center text-muted py-4">
        No audit history available.
      </div>

    ) : (

      <div className="table-responsive">

        <table className="table table-bordered table-hover align-middle">

          <thead className="table-light">
            <tr>
              <th>Action</th>
              <th>Updated Field</th>
              <th>Old Value</th>
              <th>New Value</th>
              <th>Date & Time</th>
            </tr>
          </thead>

          <tbody>

            {auditLogs.map((log) => (

              <tr key={log.id}>

                <td>
                  <span className={`badge ${
                    log.action === "invoice_extracted"
                      ? "bg-success"
                      : "bg-primary"
                  }`}>
                    {formatAuditAction(log.action)}
                  </span>
                </td>

                <td>
                  {formatFieldName(log.details?.field)}
                </td>

                <td style={{ minWidth: "180px" }}>
  <div className="p-2 rounded bg-light border">
    <span className="badge bg-secondary mb-2">
      Previous
    </span>

    <div>
      {formatAuditValue(log.details?.old_value)}
    </div>
  </div>
</td>
                <td style={{ minWidth: "180px" }}>
  <div className="p-2 rounded bg-light border">
    <span className="badge bg-success mb-2">
      Updated
    </span>

    <div>
      {formatAuditValue(log.details?.new_value)}
    </div>
  </div>
</td>

                <td style={{ minWidth: "180px" }}>
                  {log.created_at
                    ? new Date(log.created_at).toLocaleString("en-IN")
                    : "N/A"}
                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    )}

  </div>
</div>


        </div>
      </div>

    </div>
  );
}

export default InvoiceDetails;
