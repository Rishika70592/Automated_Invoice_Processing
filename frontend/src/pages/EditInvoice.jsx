
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getInvoiceDetails, updateInvoice } from "../api/invoiceApi";

function EditInvoice() {
  const { invoiceId } = useParams();
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const fetchInvoice = async () => {
      try {
        const data = await getInvoiceDetails(invoiceId);
        setInvoice({
          ...data,
          supplier: {
            name: data.supplier?.name || "",
            tax_id: data.supplier?.tax_id || "",
            email: data.supplier?.email || "",
            phone: data.supplier?.phone || "",
            address: data.supplier?.address || "",
          },
          line_items: data.line_items || [],
        });
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Unable to load invoice."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchInvoice();
  }, [invoiceId]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name.startsWith("supplier.")) {
      const field = name.split(".")[1];

      setInvoice((prev) => ({
        ...prev,
        supplier: {
          ...prev.supplier,
          [field]: value,
        },
      }));
    } else {
      setInvoice((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleLineItemChange = (index, field, value) => {
    setInvoice((prev) => ({
      ...prev,
      line_items: prev.line_items.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      ),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const payload = {
        invoice_number: invoice.invoice_number || null,
        purchase_order_number: invoice.purchase_order_number || null,
        invoice_date: invoice.invoice_date || null,
        due_date: invoice.due_date || null,
        currency: invoice.currency || null,
        payment_terms: invoice.payment_terms || null,
        subtotal: invoice.subtotal || null,
        tax: invoice.tax || null,
        discount: invoice.discount || null,
        total_amount: invoice.total_amount || null,
        supplier: invoice.supplier,
        line_items: invoice.line_items.map((item) => ({
          description: item.description || null,
          quantity: item.quantity || null,
          unit_price: item.unit_price || null,
          tax_rate: item.tax_rate || null,
          tax_amount: item.tax_amount || null,
          line_total: item.line_total || null,
        })),
      };

      await updateInvoice(invoiceId, payload);

      setSuccess("Invoice updated successfully.");

      setTimeout(() => {
        navigate(`/invoices/${invoiceId}`);
      }, 1000);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to update invoice."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Loading invoice...</p>;
  if (!invoice) return <p>{error || "Invoice not found."}</p>;

  const fields = [
    ["invoice_number", "Invoice Number"],
    ["purchase_order_number", "Purchase Order Number"],
    ["invoice_date", "Invoice Date"],
    ["due_date", "Due Date"],
    ["currency", "Currency"],
    ["payment_terms", "Payment Terms"],
    ["subtotal", "Subtotal"],
    ["tax", "Tax"],
    ["discount", "Discount"],
    ["total_amount", "Total Amount"],
  ];

  return (
    <div className="container py-4">
      <h3 className="fw-bold mb-4">Edit Invoice</h3>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div className="card shadow-sm mb-4">
          <div className="card-header bg-white">
            <h5>Invoice Information</h5>
          </div>

          <div className="card-body">
            <div className="row">
              {fields.map(([name, label]) => (
                <div className="col-md-6 mb-3" key={name}>
                  <label className="form-label">{label}</label>
                  <input
                    className="form-control"
                    type={
                      name.includes("date")
                        ? "date"
                        : ["subtotal", "tax", "discount", "total_amount"].includes(name)
                        ? "number"
                        : "text"
                    }
                    step="any"
                    name={name}
                    value={invoice[name] ?? ""}
                    onChange={handleChange}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card shadow-sm mb-4">
          <div className="card-header bg-white">
            <h5>Supplier Information</h5>
          </div>

          <div className="card-body">
            {["name", "tax_id", "email", "phone", "address"].map((field) => (
              <div className="mb-3" key={field}>
                <label className="form-label text-capitalize">
                  {field.replace("_", " ")}
                </label>
                <input
                  className="form-control"
                  name={`supplier.${field}`}
                  value={invoice.supplier[field] ?? ""}
                  onChange={handleChange}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="card shadow-sm mb-4">
          <div className="card-header bg-white">
            <h5>Line Items</h5>
          </div>

          <div className="card-body">
            {invoice.line_items.map((item, index) => (
              <div className="border rounded p-3 mb-3" key={item.id || index}>
                <h6>Item {index + 1}</h6>

                {[
                  ["description", "Description", "text"],
                  ["quantity", "Quantity", "number"],
                  ["unit_price", "Unit Price", "number"],
                  ["tax_rate", "Tax Rate", "number"],
                  ["tax_amount", "Tax Amount", "number"],
                  ["line_total", "Line Total", "number"],
                ].map(([field, label, type]) => (
                  <div className="mb-2" key={field}>
                    <label className="form-label">{label}</label>
                    <input
                      className="form-control"
                      type={type}
                      step="any"
                      value={item[field] ?? ""}
                      onChange={(e) =>
                        handleLineItemChange(index, field, e.target.value)
                      }
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        <button
          type="button"
          className="btn btn-outline-secondary me-2"
          onClick={() => navigate(`/invoices/${invoiceId}`)}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
}

export default EditInvoice;
