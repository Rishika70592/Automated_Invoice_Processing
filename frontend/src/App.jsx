
import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import InvoiceList from "./pages/InvoiceList";
import InvoiceDetails from "./pages/invoiceDetails";
import Settings from "./pages/Settings";
import InvoiceUpload from "./pages/InvoiceUpload";
function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/invoices" element={<InvoiceList />} />
          <Route
            path="/invoices/:invoiceId"
            element={<InvoiceDetails />}
          />
          <Route path="/settings" element={<Settings />} />
          <Route
  path="/invoices/upload"
  element={<InvoiceUpload />}
/>
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
