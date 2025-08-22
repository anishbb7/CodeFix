import React from "react";
import Editor from "@monaco-editor/react";
import "./EditorPanel.css";

function EditorPanel({ code, setCode }) {
  return (
    <div className="editor-panel">
      <Editor
        height="100%"
        width="100%"
        theme="vs-dark"
        language="java"
        value={code}
        onChange={(value) => setCode(value || "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          wordWrap: "on",
        }}
      />
    </div>
  );
}

export default EditorPanel;
