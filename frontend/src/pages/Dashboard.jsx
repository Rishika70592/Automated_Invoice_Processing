
import { useEffect, useState } from "react";

import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
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

function Dashboard() {
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

    const invoices = data.invoices;

    setDashboard({
      total: data.total,

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

  if (error) {
    return (
      <div className="alert alert-danger">
        {error}
        <button
          className="btn btn-outline-danger ms-3"
          onClick={fetchDashboard}
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

      <div className="row g-4 mb-4">
        {cards.map((card, index) => {
          const Icon = card.icon;

          return (
            <div className="col-sm-6 col-xl-3" key={index}>
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body d-flex justify-content-between align-items-center">

                  <div>
                    <p className="text-muted mb-2">
                      {card.title}
                    </p>

                    <h2 className="fw-bold mb-0">
                      {card.value}
                    </h2>
                  </div>

                  <Icon
                    size={30}
                    className={`text-${card.color}`}
                  />

                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Invoices Table */}

      <div className="card border-0 shadow-sm">

        <div className="card-header bg-white py-3">
          <h5 className="mb-0">Recent Invoices</h5>
        </div>

        <div className="card-body">
          <div className="table-responsive">

            <table className="table table-hover align-middle">

              <thead>
                <tr>
                  <th>Invoice Number</th>
                  <th>Supplier</th>
                  <th>Invoice Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {dashboard.recentInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center">
                      No invoices available.
                    </td>
                  </tr>
                ) : (
                  dashboard.recentInvoices.map((invoice) => (
                    <tr key={invoice.id}>
                      <td>{invoice.invoice_number || "-"}</td>
                      <td>{invoice.supplier || "-"}</td>
                      <td>{invoice.invoice_date || "-"}</td>
                      <td>
                        {invoice.currency || ""}{" "}
                        {invoice.total_amount ?? "-"}
                      </td>
                      <td>
                         {getStatusBadge(invoice.processing_status)}
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
