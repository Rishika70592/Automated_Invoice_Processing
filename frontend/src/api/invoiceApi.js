
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
