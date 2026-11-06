
import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#38BDF8",
    },
    secondary: {
      main: "#818CF8",
    },
    background: {
      default: "#0B1120",
      paper: "#111827",
    },
    text: {
      primary: "#F8FAFC",
      secondary: "#94A3B8",
    },
    divider: "#263244",
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h5: {
      fontWeight: 700,
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 10,
  },
});

