import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";

// tokens.css first: base.css and every component read the custom properties it
// declares, and CSS custom properties are not hoisted.
import "./styles/tokens.css";
import "./styles/base.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("index.html is missing the #root mount point");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
