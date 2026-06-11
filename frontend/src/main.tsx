import "./styles.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import PokefisiApp from "./lib/pokefisi/PokefisiApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PokefisiApp />
  </StrictMode>
);
