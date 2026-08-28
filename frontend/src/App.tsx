import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./pages/Landing";
import { Placeholder } from "./pages/Placeholder";

/**
 * All four route paths from docs/frontend/pages.md are declared here from the
 * start; only the landing route has real content at this stage.
 *
 * There is no route protection yet — every path renders for anyone. Auth state
 * and the redirect to /login arrive with LLMC-AUTH-003, which wraps these
 * elements rather than re-declaring them.
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<Placeholder title="Log in" task="LLMC-AUTH-003" shell="auth" />}
        />
        <Route path="/" element={<Landing />} />
        <Route
          path="/runs/:id"
          element={<Placeholder title="Run" task="LLMC-RUNS-004" shell="app" />}
        />
        <Route
          path="/settings"
          element={<Placeholder title="Settings" task="LLMC-CFG-002" shell="app" />}
        />
      </Routes>
    </BrowserRouter>
  );
}
