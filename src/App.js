import React, { useState, useRef, useEffect } from "react";
import Navbar from "./components/Navbar";
import EditorPanel from "./components/EditorPanel";
import OutputPanel from "./components/OutputPanel";
import "./App.css";
import logo from "./project_icon.png"; // optional — used in Navbar if needed

function App() {
  const [activeTab, setActiveTab] = useState("completion");
  const [code, setCode] = useState("// Write your code here...");
  const [output, setOutput] = useState("");
  const [numCases, setNumCases] = useState(5);

  // --- Resizable layout states ---
  const [editorWidth, setEditorWidth] = useState(60);
  const isDragging = useRef(false);

  const handleMouseDown = () => {
    isDragging.current = true;
    document.body.classList.add("no-select");
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

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const BASE_URL = "http://127.0.0.1:8080";

  // --- Function to call backend ---
  const runTask = async () => {
    let endpoint = "";
    if(code === "") {
      setOutput("Error: Code editor is empty.");
      return;
    }
    if (activeTab === "completion") endpoint = "/completion";
    else if (activeTab === "debugging") endpoint = "/debugging";
    else if (activeTab === "testcase") endpoint = "/testcase";

    try {
      const bodyData = { code };
      if (activeTab === "testcase") {
        bodyData.num_cases = numCases;
      }

      const response = await fetch(BASE_URL + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bodyData)
      });

      if (!response.ok) throw new Error("Network error");

      const data = await response.json();
      setOutput(data.result);
    } catch (err) {
      console.error(err);
      setOutput("❌ Error: Could not connect to backend.");
    }
  };

  return (
    <div className="App">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main">
        {/* Editor Section */}
        {activeTab !== "testcase" && (
          <div className="editor-container" style={{ width: `${editorWidth}%` }}>
            <EditorPanel code={code} setCode={setCode} />
          </div>
        )}

        {/* Divider for resizing */}
        {activeTab !== "testcase" && (
          <div className="divider" onMouseDown={handleMouseDown}></div>
        )}

        {/* Output Section */}
        <div
          className="output-container"
          style={{
            width: activeTab === "testcase" ? "100%" : `${100 - editorWidth}%`
          }}
        >
          {/* Test Case Settings */}
          {activeTab === "testcase" && (
            <div style={{ marginBottom: "10px" }}>
              <label
                style={{
                  color: "#61dafb",
                  fontWeight: "bold",
                  paddingLeft: "10px"
                }}
              >
                Number of Test Cases:{" "}
                <input
                  type="number"
                  value={numCases}
                  min="1"
                  max="50"
                  onChange={(e) => setNumCases(Number(e.target.value))}
                  style={{
                    width: "50px",
                    backgroundColor: "#20232a",
                    color: "white",
                    border: "1px solid #61dafb",
                    borderRadius: "4px",
                    textAlign: "center"
                  }}
                />
              </label>
            </div>
          )}

          <OutputPanel output={output} runTask={runTask} />
        </div>
      </div>
    </div>
  );
}

export default App;
