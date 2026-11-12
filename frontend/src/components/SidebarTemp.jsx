
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Settings,
  Receipt,
} from "lucide-react";

function Sidebar() {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <Receipt size={28} />
        <span>InvoiceFlow</span>
      </div>

      <div className="sidebar-menu">
        <p className="menu-label">MAIN MENU</p>

        <NavLink to="/" className="sidebar-link">
          <LayoutDashboard size={19} />
          Dashboard
        </NavLink>

        <NavLink to="/invoices" className="sidebar-link">
          <FileText size={19} />
          Invoices
        </NavLink>

        <p className="menu-label mt-4">PREFERENCES</p>

        <NavLink to="/settings" className="sidebar-link">
          <Settings size={19} />
          Settings
        </NavLink>
      </div>
    </div>
  );
}

export default Sidebar;
