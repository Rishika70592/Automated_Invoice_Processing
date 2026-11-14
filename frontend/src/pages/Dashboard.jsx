
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  
  Upload,
  Eye,
  ClipboardCheck,
  ArrowRight,
} from "lucide-react";

import { getDashboardInvoices } from "../api/dashboardApi";

function getStatusBadge(status) {
  const statusStyles = {
    needs_review: {
      label: "Needs Review",
      className: "bg-warning text-dark",
    },

    completed: {
      label: "Completed",
      className: "bg-success",
    },

    failed: {
      label: "Failed",
      className: "bg-danger",
    },

    processing: {
      label: "Processing",
      className: "bg-primary",
    },

    uploaded: {
      label: "Uploaded",
      className: "bg-secondary",
    },
  };

  const config = statusStyles[status] || {
    label: status || "Unknown",
    className: "bg-secondary",
  };

  return (
    <span className={`badge ${config.className}`}>
      {config.label}
    </span>
  );
}

// Format invoice dates
const formatInvoiceDate = (value) => {
  if (!value) return "N/A";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "N/A";

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
};

// Format invoice amounts
const formatInvoiceAmount = (amount, currency) => {
  if (amount === null || amount === undefined || amount === "") {
    return "N/A";
  }

  const number = Number(amount);

  if (!Number.isFinite(number)) return "N/A";

  if (!currency) return number.toFixed(2);

  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(number);
  } catch {
    return `${currency} ${number.toFixed(2)}`;
  }
};

function Dashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


const fetchDashboard = async (isInitial = false) => {
  try {
    if (isInitial) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    setError("");

    const data = await getDashboardInvoices();

    if (!data || !Array.isArray(data.invoices)) {
      throw new Error("Invalid dashboard response.");
    }

    const invoices = data.invoices;

    setDashboard({
      total: data.total ?? 0,

      needsReview: invoices.filter(
        (item) => item.processing_status === "needs_review"
      ).length,

      completed: invoices.filter(
        (item) => item.processing_status === "completed"
      ).length,

      failed: invoices.filter(
        (item) => item.processing_status === "failed"
      ).length,

      recentInvoices: [...invoices]
        .sort(
          (a, b) =>
            new Date(b.created_at) - new Date(a.created_at)
        )
        .slice(0, 5),
    });

  } catch (err) {
    console.error("Dashboard error:", err);

    setError(
      err.response?.data?.detail ||
      err.message ||
      "Unable to load dashboard information."
    );

  } finally {
    setLoading(false);
    setRefreshing(false);
  }
};



  useEffect(() => {
    fetchDashboard(true);
  }, []);

  if (loading) {
    return <p>Loading dashboard...</p>;
  }

  if (error && !dashboard) {
  return (
    <div className="alert alert-danger">
      {error}

      <button
        className="btn btn-outline-danger ms-3"
        onClick={() => fetchDashboard(true)}
      >
        Retry
      </button>
    </div>
  );
}
  const cards = [
    {
      title: "Total Invoices",
      value: dashboard.total,
      icon: FileText,
      color: "primary",
    },
    {
      title: "Needs Review",
      value: dashboard.needsReview,
      icon: Clock,
      color: "warning",
    },
    {
      title: "Completed",
      value: dashboard.completed,
      icon: CheckCircle,
      color: "success",
    },
    {
      title: "Failed Jobs",
      value: dashboard.failed,
      icon: AlertCircle,
      color: "danger",
    },
  ];

  return (
    <div className="container-fluid">

      {/* Dashboard Heading */}

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold">Dashboard</h3>
          <p className="text-muted">
            Overview of your invoice processing system.
          </p>
        </div>
{error && dashboard && (
  <div className="alert alert-warning">
    {error}

    <button
      className="btn btn-sm btn-outline-warning ms-3"
      onClick={() => fetchDashboard(false)}
    >
      Retry
    </button>
  </div>
)}
        
<button
  className="btn btn-outline-primary"
  onClick={() => fetchDashboard(false)}
  disabled={refreshing}
>
  <RefreshCw
    size={16}
    className={`me-2 ${refreshing ? "spin-animation" : ""}`}
  />

  {refreshing ? "Refreshing..." : "Refresh"}
</button>

      </div>

      {/* Summary Cards */}

      
{/* Summary Cards */}

<div className="row g-4 mb-4">
  {cards.map((card, index) => {
    const Icon = card.icon;

    const iconBackgrounds = {
      primary: "bg-primary bg-opacity-10 text-primary",
      warning: "bg-warning bg-opacity-25 text-warning-emphasis",
      success: "bg-success bg-opacity-10 text-success",
      danger: "bg-danger bg-opacity-10 text-danger",
    };

    return (
      <div className="col-sm-6 col-xl-3" key={index}>
        <div className="card dashboard-stat-card border-0 shadow-sm h-100">
          <div className="card-body d-flex justify-content-between align-items-center p-4">

            <div>
              <p className="text-muted mb-2">
                {card.title}
              </p>

              <h2 className="fw-bold mb-0">
                {card.value}
              </h2>
            </div>

            <div
              className={`dashboard-icon ${
                iconBackgrounds[card.color]
              }`}
            >
              <Icon size={26} />
            </div>

          </div>
        </div>
      </div>
    );
  })}
</div>

{/* Invoice Processing Overview */}

<div className="card border-0 shadow-sm mb-4 dashboard-overview">

  <div className="card-header bg-white border-0 pt-4 px-4">
    <h5 className="fw-bold mb-1">
      Invoice Processing Overview
    </h5>

    <p className="text-muted small mb-0">
      Overview of your invoice processing performance.
    </p>
  </div>

  <div className="card-body px-4 pb-4">

    {(() => {
      const total = dashboard.total || 0;
      const completed = dashboard.completed || 0;
      const needsReview = dashboard.needsReview || 0;
      const failed = dashboard.failed || 0;

      const completionRate =
        total > 0
          ? Math.round((completed / total) * 100)
          : 0;

      return (
        <>

      
{/* Quick Actions */}

<div className="mb-4">

  <div className="mb-3">
    <h5 className="fw-bold mb-1">
      Quick Actions
    </h5>

    <p className="text-muted small mb-0">
      Quickly access important invoice operations.
    </p>
  </div>

  <div className="row g-3">

    {/* Upload Invoice */}

    <div className="col-md-4">
      <div className="card border-0 shadow-sm h-100 dashboard-action-card">

        <div className="card-body p-4">

          <div className="dashboard-action-icon bg-primary bg-opacity-10 text-primary mb-3">
            <Upload size={23} />
          </div>

          <h6 className="fw-bold">
            Upload New Invoice
          </h6>

          <p className="text-muted small">
            Upload an invoice document for automatic extraction and validation.
          </p>

          <button
            className="btn btn-light border w-100 text-primary fw-semibold"
            onClick={() => navigate("/invoices/upload")}
          >
            Upload Invoice
            <ArrowRight size={16} className="ms-2" />
          </button>

        </div>
      </div>
    </div>

    {/* View All Invoices */}

    <div className="col-md-4">
      <div className="card border-0 shadow-sm h-100 dashboard-action-card">

        <div className="card-body p-4">

          <div className="dashboard-action-icon bg-success bg-opacity-10 text-success mb-3">
            <Eye size={23} />
          </div>

          <h6 className="fw-bold">
            View All Invoices
          </h6>

          <p className="text-muted small">
            Browse uploaded invoices and check their processing information.
          </p>

          <button
            className="btn btn-light border w-100 text-success fw-semibold"
            onClick={() => navigate("/invoices")}
          >
            View Invoices
            <ArrowRight size={16} className="ms-2" />
          </button>

        </div>
      </div>
    </div>

    {/* Review Invoices */}

    <div className="col-md-4">
      <div className="card border-0 shadow-sm h-100 dashboard-action-card">

        <div className="card-body p-4">

          <div className="dashboard-action-icon bg-warning bg-opacity-10 text-warning mb-3">
            <ClipboardCheck size={23} />
          </div>

          <h6 className="fw-bold">
            Review Pending Invoices
          </h6>

          <p className="text-muted small">
            Find invoices that require manual verification or correction.
          </p>

          <button
            className="btn btn-light border w-100 text-warning-emphasis fw-semibold"
            onClick={() => navigate("/invoices?status=needs_review")}
          >
            Review Invoices
            <ArrowRight size={16} className="ms-2" />
          </button>

        </div>
      </div>
    </div>

  </div>
</div>

          {/* Completion Percentage */}

          <div className="d-flex justify-content-between align-items-center mb-2">

            <div>
              <span className="fw-semibold">
                Completion Rate
              </span>

              <p className="text-muted small mb-0">
                Successfully processed invoices
              </p>
            </div>

            <h4 className="fw-bold text-success mb-0">
              {completionRate}%
            </h4>

          </div>

          {/* Progress Bar */}

          <div
            className="progress mb-4"
            style={{ height: "12px" }}
          >
            <div
              className="progress-bar bg-success"
              role="progressbar"
              style={{ width: `${completionRate}%` }}
              aria-valuenow={completionRate}
              aria-valuemin="0"
              aria-valuemax="100"
            />
          </div>

          {/* Processing Statistics */}

          <div className="row g-3">

            <div className="col-md-4">
              <div className="overview-item p-3 rounded">
                <div className="d-flex justify-content-between">
                  <span className="text-muted">
                    Completed
                  </span>

                  <CheckCircle size={19} className="text-success" />
                </div>

                <h4 className="fw-bold mt-2 mb-0">
                  {completed}
                </h4>
              </div>
            </div>

            <div className="col-md-4">
              <div className="overview-item p-3 rounded">
                <div className="d-flex justify-content-between">
                  <span className="text-muted">
                    Needs Review
                  </span>

                  <Clock size={19} className="text-warning" />
                </div>

                <h4 className="fw-bold mt-2 mb-0">
                  {needsReview}
                </h4>
              </div>
            </div>

            <div className="col-md-4">
              <div className="overview-item p-3 rounded">
                <div className="d-flex justify-content-between">
                  <span className="text-muted">
                    Failed
                  </span>

                  <AlertCircle size={19} className="text-danger" />
                </div>

                <h4 className="fw-bold mt-2 mb-0">
                  {failed}
                </h4>
              </div>
            </div>

          </div>
        </>
      );
    })()}

  </div>
</div>


      {/* Recent Invoices Table */}

     


<div className="card border-0 shadow-sm">
  <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
    <h5 className="mb-0 fw-semibold">Recent Invoices</h5>

    <button
      className="btn btn-sm btn-outline-primary"
      onClick={() => navigate("/invoices")}
    >
      View All
    </button>
  </div>

  <div className="card-body">
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
          {dashboard.recentInvoices.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center py-4 text-muted">
                No invoices available.
              </td>
            </tr>
          ) : (
            dashboard.recentInvoices.map((invoice) => (
              <tr key={invoice.id}>
                <td className="fw-semibold">
                  {invoice.invoice_number || "N/A"}
                </td>

                <td>{invoice.supplier || "N/A"}</td>

                <td>
                  {invoice.invoice_date
                    ? new Date(invoice.invoice_date).toLocaleDateString("en-IN")
                    : "N/A"}
                </td>

                <td className="fw-semibold">
                  {invoice.currency || ""}
                  {" "}
                  {invoice.total_amount ?? "N/A"}
                </td>

                <td>
                  {getStatusBadge(invoice.processing_status)}
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
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>
</div>


    </div>
  );
}

export default Dashboard;
