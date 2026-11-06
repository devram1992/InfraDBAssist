import {
  Box,
  Button,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";

import AddCommentOutlinedIcon from "@mui/icons-material/AddCommentOutlined";
import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";
import CloudOutlinedIcon from "@mui/icons-material/CloudOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import LogoutOutlinedIcon from "@mui/icons-material/LogoutOutlined";

import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

const menuItems = [
  { label: "AI Chat", path: "/", icon: <AddCommentOutlinedIcon /> },
  { label: "Databases", path: "/databases", icon: <StorageOutlinedIcon /> },
  { label: "Infrastructure", path: "/infrastructure", icon: <CloudOutlinedIcon /> },
  { label: "Audit Dashboard", path: "/audit", icon: <AssessmentOutlinedIcon /> },
];

export function Sidebar() {
  const { username, logout } = useAuth();

  return (
    <Box
      sx={{
        width: 260,
        height: "100vh",
        bgcolor: "#0F172A",
        borderRight: "1px solid #263244",
        display: "flex",
        flexDirection: "column",
        p: 2,
        boxSizing: "border-box",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 4 }}>
        <SmartToyOutlinedIcon color="primary" sx={{ fontSize: 34 }} />
        <Box>
          <Typography sx={{ fontWeight: 700 }}>InfraDB AI</Typography>
          <Typography variant="caption" color="text.secondary">
            Infrastructure Assistant
          </Typography>
        </Box>
      </Box>

      <Button
        variant="contained"
        startIcon={<AddCommentOutlinedIcon />}
        fullWidth
        sx={{ mb: 3 }}
        component={NavLink}
        to="/"
      >
        New Chat
      </Button>

      <Typography variant="overline" color="text.secondary" sx={{ px: 1 }}>
        WORKSPACE
      </Typography>

      <List>
        {menuItems.map((item) => (
          <ListItemButton
            key={item.path}
            component={NavLink}
            to={item.path}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              "&.active": {
                bgcolor: "rgba(56,189,248,0.12)",
                color: "primary.main",
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 38, color: "inherit" }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      <Divider sx={{ mb: 2 }} />

      <Typography variant="caption" color="text.secondary">
        Signed in as
      </Typography>
      <Typography
        variant="body2"
        sx={{ mt: 0.5, mb: 1.5, fontWeight: 600, overflowWrap: "anywhere" }}
      >
        {username || "Authenticated user"}
      </Typography>

      <Button
        variant="outlined"
        color="inherit"
        startIcon={<LogoutOutlinedIcon />}
        fullWidth
        onClick={logout}
        sx={{
          justifyContent: "flex-start",
          mb: 2,
          borderColor: "#475569",
          color: "#E2E8F0",
          "&:hover": {
            borderColor: "#94A3B8",
            bgcolor: "rgba(148,163,184,0.08)",
          },
        }}
      >
        Logout
      </Button>

      <Typography variant="caption" color="text.secondary">
        Development Environment
      </Typography>
      <Typography variant="body2" sx={{ mt: 0.5 }}>
        InfraDB Assist v1.0
      </Typography>
    </Box>
  );
}
