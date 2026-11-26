
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Eye,
  RefreshCw,
  FileText,
  Search,
  X,
  Files,
  Filter,
} from "lucide-react";
import api from "../api/axios";

function InvoiceList() {
  const navigate = useNavigate();

  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [totalInvoices, setTotalInvoices] = useState(0);

  // -----------------------------------------
  // Filter State
  // -----------------------------------------

  const [filters, setFilters] = useState({
    status: "",
    currency: "",
    start_date: "",
    end_date: "",
  });

  const [appliedFilters, setAppliedFilters] = useState({
    status: "",
    currency: "",
    start_date: "",
    end_date: "",
  });

  // -----------------------------------------
  // Fetch Invoices
  // -----------------------------------------

  const fetchInvoices = async (
    search = searchTerm,
    filterData = appliedFilters
  ) => {
    try {
      setError("");

      const response = await api.get("/invoices", {
        params: {
          search: search.trim() || undefined,
          status: filterData.status || undefined,
          currency: filterData.currency || undefined,
          start_date: filterData.start_date || undefined,
          end_date: filterData.end_date || undefined,
          page: 1,
          page_size: 100,
        },
      });

      setInvoices(response.data.invoices || []);
      setTotalInvoices(response.data.total || 0);

    } catch (err) {
      console.error("Invoice list error:", err);

      setError(
        err.response?.data?.detail ||
        "Unable to retrieve invoices."
      );

    } finally {
      setLoading(false);
      setSearching(false);
      setRefreshing(false);
    }
  };

  // -----------------------------------------
  // Initial Load and Automatic Search
  // -----------------------------------------

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearching(true);
      fetchInvoices(searchTerm, appliedFilters);
    }, 400);

    return () => clearTimeout(timer);
  }, [searchTerm, appliedFilters]);

  // -----------------------------------------
  // Handle Filter Changes
  // -----------------------------------------

  const handleFilterChange = (e) => {
    const { name, value } = e.target;

    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // -----------------------------------------
  // Apply Filters
  // -----------------------------------------

  const handleApplyFilters = (e) => {
    e.preventDefault();

    if (
      filters.start_date &&
      filters.end_date &&
      filters.start_date > filters.end_date
    ) {
      setError("Start date cannot be after end date.");
      return;
    }

    setLoading(true);
    setAppliedFilters({ ...filters });
  };

  // -----------------------------------------
  // Clear Filters
  // -----------------------------------------

  const handleClearFilters = () => {
    const emptyFilters = {
      status: "",
      currency: "",
      start_date: "",
      end_date: "",
    };

    setFilters(emptyFilters);
    setLoading(true);
    setAppliedFilters(emptyFilters);
  };

  // -----------------------------------------
  // Refresh
  // -----------------------------------------

  const handleRefresh = () => {
    setRefreshing(true);
    fetchInvoices(searchTerm, appliedFilters);
  };

  // -----------------------------------------
  // Clear Search
  // -----------------------------------------

  const handleClearSearch = () => {
    setSearchTerm("");
  };

  // -----------------------------------------
  // Status Badge
  // -----------------------------------------

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

  // -----------------------------------------
  // Initial Loading
  // -----------------------------------------

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" />
        <p className="mt-2">Loading invoices...</p>
      </div>
    );
  }

  // -----------------------------------------
  // Main UI
  // -----------------------------------------

  return (
    <div className="container-fluid">

      {/* Page Header */}

      <div className="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">

        <div>
          <h3>Invoices</h3>

          <p className="text-muted">
            Manage all your uploaded invoices here.
          </p>
        </div>

       
<div className="d-flex gap-2 flex-wrap">

  {/* Single Invoice Upload */}

  <button
    className="btn btn-primary"
    onClick={() => navigate("/invoices/upload")}
  >
    <FileText size={16} className="me-2" />
    Upload Invoice
  </button>

  {/* Bulk Invoice Upload */}

  <button
    className="btn btn-primary"
    onClick={() => navigate("/bulk-invoice-upload")}
  >
    <Files size={16} className="me-2" />
    Bulk Upload
  </button>

  {/* Refresh */}

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
            onClick={() => setError("")}
          >
            Close
          </button>
        </div>
      )}

      {/* Search Section */}

      <div className="card mb-3">

        <div className="card-body">

          <label className="form-label fw-semibold">
            Search Invoices
          </label>

          <div className="input-group">

            <span className="input-group-text bg-white">
              <Search size={18} />
            </span>

            <input
              type="text"
              className="form-control"
              placeholder="Search by invoice number or supplier name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            {searchTerm && (
              <button
                className="btn btn-outline-secondary"
                onClick={handleClearSearch}
                type="button"
              >
                <X size={17} />
                Clear
              </button>
            )}

          </div>

          <small className="text-muted d-block mt-2">
            Search automatically updates results as you type.
          </small>

        </div>

      </div>

      {/* Filter Section */}

      <div className="card mb-3">

        <div className="card-header bg-white fw-semibold">
          <Filter size={18} className="me-2" />
          Filter Invoices
        </div>

        <div className="card-body">

          <form onSubmit={handleApplyFilters}>

            <div className="row g-3">

              {/* Status Filter */}

              <div className="col-md-3">

                <label className="form-label">
                  Processing Status
                </label>

                <select
                  name="status"
                  className="form-select"
                  value={filters.status}
                  onChange={handleFilterChange}
                >
                  <option value="">All Statuses</option>
                  <option value="needs_review">
                    Needs Review
                  </option>
                  <option value="completed">
                    Completed
                  </option>
                  <option value="processing">
                    Processing
                  </option>
                  <option value="uploaded">
                    Uploaded
                  </option>
                  <option value="failed">
                    Failed
                  </option>
                </select>

              </div>

              {/* Currency Filter */}

              <div className="col-md-3">

                <label className="form-label">
                  Currency
                </label>

                <select
                  name="currency"
                  className="form-select"
                  value={filters.currency}
                  onChange={handleFilterChange}
                >
                  <option value="">All Currencies</option>
                  <option value="INR">INR</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>

              </div>

              {/* Start Date */}

              <div className="col-md-3">

                <label className="form-label">
                  Start Date
                </label>

                <input
                  type="date"
                  name="start_date"
                  className="form-control"
                  value={filters.start_date}
                  onChange={handleFilterChange}
                />

              </div>

              {/* End Date */}

              <div className="col-md-3">

                <label className="form-label">
                  End Date
                </label>

                <input
                  type="date"
                  name="end_date"
                  className="form-control"
                  value={filters.end_date}
                  onChange={handleFilterChange}
                />

              </div>

            </div>

            {/* Filter Buttons */}

            <div className="d-flex gap-2 mt-3">

              <button
                type="submit"
                className="btn btn-primary"
              >
                <Filter size={16} className="me-2" />
                Apply Filters
              </button>

              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={handleClearFilters}
              >
                <X size={16} className="me-2" />
                Clear Filters
              </button>

            </div>

          </form>

        </div>

      </div>

      {/* Invoice Count */}

      <div className="card mb-3">

        <div className="card-body d-flex justify-content-between align-items-center">

          <div>
            <h6 className="text-muted mb-1">
              {searchTerm || Object.values(appliedFilters).some(Boolean)
                ? "Matching Invoices"
                : "Total Invoices"}
            </h6>

            <h3 className="mb-0">
              {totalInvoices}
            </h3>
          </div>

          {searching && (
            <div className="text-primary small">
              <span className="spinner-border spinner-border-sm me-2" />
              Searching...
            </div>
          )}

        </div>

      </div>

      {/* Invoice Table */}

      <div className="card">

        <div className="card-header fw-semibold">
          <FileText size={18} className="me-2" />
          Invoice Records
        </div>

        <div className="card-body">

          {invoices.length === 0 && !searching && !error ? (

            <div className="text-center py-5">

              <FileText size={40} className="text-muted" />

              <p className="text-muted mt-3">
                No matching invoices found.
              </p>

              <button
                className="btn btn-outline-primary btn-sm"
                onClick={() => {
                  handleClearSearch();
                  handleClearFilters();
                }}
              >
                Clear Search and Filters
              </button>

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
