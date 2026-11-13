
import api from "./axios";

// 1. Upload invoice document
export const uploadDocument = async (file) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    "/documents/upload",
    formData
  );

  return response.data;
};

// 2. Extract text from uploaded document
export const extractDocument = async (documentId) => {
  const response = await api.post(
    `/documents/${documentId}/extract`
  );

  return response.data;
};

// 3. Process invoice and save extracted information
export const processInvoice = async (documentId) => {
  const response = await api.post(
    `/invoices/process/${documentId}`
  );

  return response.data;
};
