import React from "react";
import "./Navbar.css";
import logo from "../project_icon.png"; // 👈 place your logo.png inside the src/ folder (or src/assets/)

function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <img src={logo} alt="Logo" className="logo" />
        <h1>CodeFix</h1>
      </div>

      <div className="tabs">
        <button
          className={activeTab === "completion" ? "active" : ""}
          onClick={() => setActiveTab("completion")}
        >
          Code Completion
        </button>
        <button
          className={activeTab === "debugging" ? "active" : ""}
          onClick={() => setActiveTab("debugging")}
        >
          Debugging
        </button>
        <button
          className={activeTab === "testcase" ? "active" : ""}
          onClick={() => setActiveTab("testcase")}
        >
          Test Case Generation
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
