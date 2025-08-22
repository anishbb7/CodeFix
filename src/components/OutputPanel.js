import React from "react";
import "./OutputPanel.css";

function OutputPanel({ output, runTask }) {
  return (
    <div className="output-panel">
      <h3>Output</h3>
      <div className="output-box">
        <pre>{output || "No output yet..."}</pre>
      </div>
      <button onClick={runTask} className="run-btn">Run</button>
    </div>
  );
}

export default OutputPanel;
