
import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { theme } from "./theme/theme";
import { AuthProvider } from "./auth/AuthProvider";
import { AppLayout } from "./layouts/AppLayout";
import { ChatPage } from "./pages/ChatPage";
import { AuditPage } from "./pages/AuditPage";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<ChatPage />} />
              <Route path="/audit" element={<AuditPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

