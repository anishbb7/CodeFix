import React, { useState, useRef, useEffect } from "react";
import Navbar from "./components/Navbar";
import EditorPanel from "./components/EditorPanel";
import OutputPanel from "./components/OutputPanel";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("completion");
  const [code, setCode] = useState("// Write your code here...");
  const [output, setOutput] = useState("");

  // Resizable states
  const [editorWidth, setEditorWidth] = useState(60); // %
  const isDragging = useRef(false);

  const handleMouseDown = () => {
    isDragging.current = true;
    document.body.classList.add("no-select"); // disable text selection
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current) return;
    const newWidth = Math.min(Math.max((e.clientX / window.innerWidth) * 100, 20), 80);
    setEditorWidth(newWidth);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    document.body.classList.remove("no-select");
  };

  // Attach global mouse listeners only once
  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // 👉 Replace with your Colab ngrok URL
const BASE_URL = "http://127.0.0.1:5000";


  const runTask = async () => {
    let endpoint = "";
    if (activeTab === "completion") endpoint = "/completion";
    else if (activeTab === "debugging") endpoint = "/debugging";
    else if (activeTab === "testcase") endpoint = "/testcase";

    try {
      const response = await fetch(BASE_URL + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }) // send code to backend
      });

      if (!response.ok) throw new Error("Network error");
      const data = await response.json();
      setOutput(data.result); // get backend result
    } catch (err) {
      console.error(err);
      setOutput("❌ Error: Could not connect to backend.");
    }
  };

  return (
    <div className="App">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main">
        {activeTab !== "testcase" && (
          <div className="editor-container" style={{ width: `${editorWidth}%` }}>
            <EditorPanel code={code} setCode={setCode} />
          </div>
        )}

        {activeTab !== "testcase" && (
          <div className="divider" onMouseDown={handleMouseDown}></div>
        )}

        <div
          className="output-container"
          style={{ width: activeTab === "testcase" ? "100%" : `${100 - editorWidth}%` }}
        >
          <OutputPanel output={output} runTask={runTask} />
        </div>
      </div>
    </div>
  );
}

export default App;
