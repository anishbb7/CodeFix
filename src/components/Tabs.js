import React from "react";
import "./Tabs.css";

const Tabs = ({ activeTab, setActiveTab }) => {
  const tabs = ["Code Completion", "Debugging", "Test Case Generation"];

  return (
    <div className="tabs">
      {tabs.map((tab, index) => (
        <button
          key={index}
          className={activeTab === tab ? "tab active" : "tab"}
          onClick={() => setActiveTab(tab)}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
