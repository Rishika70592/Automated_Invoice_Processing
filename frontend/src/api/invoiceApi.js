
import api from "./axios";

// Retrieve individual invoice details
export const getInvoiceDetails = async (invoiceId) => {
  const response = await api.get(`/invoices/${invoiceId}`);
  return response.data.invoice;
};

// Retrieve original invoice document
export const downloadInvoiceDocument = async (documentId) => {
  const response = await api.get(
    `/documents/${documentId}/download`,
    {
      responseType: "blob",
    }
  );

  return response;
};

// Update invoice
export const updateInvoice = async (invoiceId, data) => {
  const response = await api.put(
    `/invoices/${invoiceId}`,
    data
  );

  return response.data;
};

// Retrieve validation history
export const getInvoiceValidationHistory = async (invoiceId) => {
  const response = await api.get(
    `/invoices/${invoiceId}/validation`
  );

  return response.data;
};

// Retrieve audit history
export const getInvoiceAuditLogs = async (invoiceId) => {
  const response = await api.get(
    `/invoices/${invoiceId}/audit-logs`
  );

  return response.data;
};
