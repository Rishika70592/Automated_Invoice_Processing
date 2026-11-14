
import api from "./axios";

export const getDashboardInvoices = async () => {
  // Fetch the first page to get pagination information.
  const firstResponse = await api.get("/invoices", {
    params: {
      page: 1,
      page_size: 100,
    },
  });

  const firstData = firstResponse.data;

  const total = firstData.total || 0;
  const totalPages = firstData.total_pages || 0;

  let allInvoices = firstData.invoices || [];

  // Fetch remaining pages concurrently.
  if (totalPages > 1) {
    const remainingRequests = [];

    for (let page = 2; page <= totalPages; page++) {
      remainingRequests.push(
        api.get("/invoices", {
          params: {
            page,
            page_size: 100,
          },
        })
      );
    }

    const responses = await Promise.all(remainingRequests);

    responses.forEach((response) => {
      allInvoices = [
        ...allInvoices,
        ...(response.data.invoices || []),
      ];
    });
  }

  return {
    total,
    invoices: allInvoices,
  };
};
