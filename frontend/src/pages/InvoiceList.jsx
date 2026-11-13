
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, RefreshCw, FileText } from "lucide-react";
import api from "../api/axios";

function InvoiceList() {
  const navigate = useNavigate();

  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchInvoices = async () => {
    try {
      setError("");

      const response = await api.get("/invoices", {
        params: {
          page: 1,
          page_size: 100,
        },
      });

      setInvoices(response.data.invoices || []);

    } catch (err) {
      console.error("Invoice list error:", err);

      setError(
        err.response?.data?.detail ||
        "Unable to retrieve invoices."
      );

    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchInvoices();
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      needs_review: "bg-warning text-dark",
      completed: "bg-success",
      failed: "bg-danger",
      processing: "bg-primary",
      uploaded: "bg-secondary",
    };

    return (
      <span
        className={`badge ${
          statusClasses[status] || "bg-secondary"
        }`}
      >
        {(status || "unknown").replaceAll("_", " ")}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" />
        <p className="mt-2">Loading invoices...</p>
      </div>
    );
  }

  return (
    <div className="container-fluid">

      {/* Page Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
  <div>
    <h3>Invoices</h3>
    <p className="text-muted">
      Manage all your uploaded invoices here.
    </p>
  </div>

  <div className="d-flex gap-2">
    <button
      className="btn btn-primary"
      onClick={() => navigate("/invoices/upload")}
    >
      <FileText size={16} className="me-2" />
      Upload Invoice
    </button>

    <button
      className="btn btn-outline-primary"
      onClick={handleRefresh}
      disabled={refreshing}
    >
      <RefreshCw
        size={16}
        className={`me-2 ${
          refreshing ? "spin-animation" : ""
        }`}
      />
      Refresh
    </button>
  </div>
</div>

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger">
          {error}
          <button
            className="btn btn-sm btn-outline-danger ms-3"
            onClick={handleRefresh}
          >
            Retry
          </button>
        </div>
      )}

      {/* Invoice Count */}
      <div className="card mb-3">
        <div className="card-body">
          <h6 className="text-muted">Total Invoices</h6>
          <h3>{invoices.length}</h3>
        </div>
      </div>

      {/* Invoice Table */}
      <div className="card">
        <div className="card-header fw-semibold">
          <FileText size={18} className="me-2" />
          Invoice Records
        </div>

        <div className="card-body">

          {invoices.length === 0 && !error ? (
            <div className="text-center py-5">
              <FileText size={40} className="text-muted" />
              <p className="text-muted mt-3">
                No invoices available.
              </p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">

                <thead className="table-light">
                  <tr>
                    <th>Invoice Number</th>
                    <th>Supplier</th>
                    <th>Invoice Date</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {invoices.map((invoice) => (
                    <tr key={invoice.id}>

                      <td>
                        {invoice.invoice_number || "N/A"}
                      </td>

                      <td>
                        {invoice.supplier || "N/A"}
                      </td>

                      <td>
                        {invoice.invoice_date || "N/A"}
                      </td>

                      <td>
                        {invoice.currency || ""}
                        {" "}
                        {invoice.total_amount ?? "N/A"}
                      </td>

                      <td>
                        {getStatusBadge(
                          invoice.processing_status
                        )}
                      </td>

                      <td>
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() =>
                            navigate(`/invoices/${invoice.id}`)
                          }
                        >
                          <Eye size={15} className="me-1" />
                          View
                        </button>
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
  );
}

export default InvoiceList;
