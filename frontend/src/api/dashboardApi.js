
import api from "./axios";

export const getDashboardInvoices = async () => {
  const firstResponse = await api.get("/invoices", {
    params: {
      page: 1,
      page_size: 100,
    },
  });

  const firstData = firstResponse.data;

  let allInvoices = [...firstData.invoices];

  for (let page = 2; page <= firstData.total_pages; page++) {
    const response = await api.get("/invoices", {
      params: {
        page,
        page_size: 100,
      },
    });

    allInvoices = [
      ...allInvoices,
      ...response.data.invoices,
    ];
  }

  return {
    total: firstData.total,
    invoices: allInvoices,
  };
};
