import React from "react";
import "./Navbar.css";

function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="navbar">
      
      <h1>CodeFix</h1>
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
