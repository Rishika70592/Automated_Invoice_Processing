
import Sidebar from "../components/SidebarTemp";
import Navbar from "../components/Navbar";

function MainLayout({ children }) {
  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Navbar />

        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
