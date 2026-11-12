
import { Bell, UserCircle } from "lucide-react";

function Navbar() {
  return (
    <nav className="top-navbar">
      <h5 className="mb-0">Invoice Management System</h5>

      <div className="navbar-actions">
        <Bell size={21} />
        <UserCircle size={25} />
      </div>
    </nav>
  );
}

export default Navbar;
