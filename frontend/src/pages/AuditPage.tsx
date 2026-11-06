import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import SearchIcon from "@mui/icons-material/Search";
import { getAuditEvents } from "../api/audit";
import type {
  AuditEvent,
  AuditFilters,
  AuditStatus,
} from "../api/audit";

const PAGE_SIZE_OPTIONS = [10, 25, 50];

type AppliedFilters = Pick<AuditFilters, "user_id" | "tool_name" | "status">;

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function getStatusColor(
  status: AuditStatus,
): "success" | "warning" | "error" | "default" {
  switch (status) {
    case "success":
      return "success";
    case "denied":
      return "warning";
    case "validation_failed":
    case "error":
      return "error";
    default:
      return "default";
  }
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const statusCode = error.response?.status;
    if (statusCode === 403) {
      return "You do not have permission to view audit events. The audit.read permission is required.";
    }

    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (statusCode) return `Unable to load audit events (HTTP ${statusCode}).`;
    return "Unable to reach the audit API. Check that the backend is running.";
  }

  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

interface AuditEventRowProps {
  event: AuditEvent;
}

function AuditEventRow({ event }: AuditEventRowProps) {
  const [expanded, setExpanded] = useState(false);
  const requestText = useMemo(
    () => JSON.stringify(event.request, null, 2),
    [event.request],
  );

  return (
    <>
      <TableRow hover>
        <TableCell sx={{ whiteSpace: "nowrap" }}>
          {formatTimestamp(event.timestamp)}
        </TableCell>
        <TableCell>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {event.username || event.user_id}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {event.user_id}
          </Typography>
        </TableCell>
        <TableCell>{event.tool_name}</TableCell>
        <TableCell>{event.permission}</TableCell>
        <TableCell>
          <Chip
            size="small"
            label={event.status.replaceAll("_", " ")}
            color={getStatusColor(event.status)}
            variant="outlined"
          />
        </TableCell>
        <TableCell align="right">
          <Tooltip title={expanded ? "Hide request details" : "View request details"}>
            <IconButton
              size="small"
              aria-label="Toggle request details"
              onClick={() => setExpanded((current) => !current)}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Tooltip>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={6} sx={{ py: 0, borderBottom: expanded ? undefined : 0 }}>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box sx={{ py: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Request details
              </Typography>
              <Paper
                variant="outlined"
                sx={{ p: 2, maxHeight: 280, overflow: "auto", bgcolor: "background.default" }}
              >
                <Box
                  component="pre"
                  sx={{
                    m: 0,
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                  }}
                >
                  {requestText}
                </Box>
              </Paper>
              {event.roles.length > 0 && (
                <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                  <Typography variant="caption" color="text.secondary">
                    Roles:
                  </Typography>
                  {event.roles.map((role) => (
                    <Chip key={role} size="small" label={role} />
                  ))}
                </Stack>
              )}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [userIdInput, setUserIdInput] = useState("");
  const [toolNameInput, setToolNameInput] = useState("");
  const [statusInput, setStatusInput] = useState<"" | AuditStatus>("");
  const [filters, setFilters] = useState<AppliedFilters>({});

  const loadEvents = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const query: AuditFilters = {
        ...filters,
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      };
      const response = await getAuditEvents(query);
      setEvents(response.items);
      setTotal(response.total);
    } catch (loadError) {
      setEvents([]);
      setTotal(0);
      setError(getErrorMessage(loadError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters, page, rowsPerPage]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const successCount = events.filter((event) => event.status === "success").length;
  const deniedCount = events.filter((event) => event.status === "denied").length;
  const failedCount = events.filter(
    (event) => event.status === "error" || event.status === "validation_failed",
  ).length;

  const applyFilters = () => {
    setPage(0);
    setFilters({
      ...(userIdInput.trim() ? { user_id: userIdInput.trim() } : {}),
      ...(toolNameInput.trim() ? { tool_name: toolNameInput.trim() } : {}),
      ...(statusInput ? { status: statusInput } : {}),
    });
  };

  const clearFilters = () => {
    setUserIdInput("");
    setToolNameInput("");
    setStatusInput("");
    setPage(0);
    setFilters({});
  };

  const handleRefresh = () => {
    setRefreshing(true);
    void loadEvents();
  };

  return (
    <Box>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ justifyContent: "space-between", alignItems: { sm: "center" }, mb: 3 }}
      >
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Audit Dashboard
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            Review AI assistant activity and tool execution history.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 3 }}>
        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              Total matching events
            </Typography>
            <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
              {total}
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              Successful on this page
            </Typography>
            <Typography variant="h4" color="success.main" sx={{ mt: 1, fontWeight: 700 }}>
              {successCount}
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              Denied on this page
            </Typography>
            <Typography variant="h4" color="warning.main" sx={{ mt: 1, fontWeight: 700 }}>
              {deniedCount}
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              Failed on this page
            </Typography>
            <Typography variant="h4" color="error.main" sx={{ mt: 1, fontWeight: 700 }}>
              {failedCount}
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          sx={{ alignItems: { md: "center" } }}
        >
          <TextField
            label="User ID"
            size="small"
            value={userIdInput}
            onChange={(event) => setUserIdInput(event.target.value)}
            fullWidth
          />
          <TextField
            label="Tool name"
            size="small"
            value={toolNameInput}
            onChange={(event) => setToolNameInput(event.target.value)}
            fullWidth
          />
          <FormControl size="small" fullWidth>
            <InputLabel id="audit-status-label">Status</InputLabel>
            <Select
              labelId="audit-status-label"
              label="Status"
              value={statusInput}
              onChange={(event) => setStatusInput(event.target.value as "" | AuditStatus)}
            >
              <MenuItem value="">All statuses</MenuItem>
              <MenuItem value="success">Success</MenuItem>
              <MenuItem value="denied">Denied</MenuItem>
              <MenuItem value="validation_failed">Validation failed</MenuItem>
              <MenuItem value="error">Error</MenuItem>
            </Select>
          </FormControl>
          <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
            <Button variant="contained" startIcon={<SearchIcon />} onClick={applyFilters}>
              Apply
            </Button>
            <Button variant="text" onClick={clearFilters}>
              Clear
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Paper variant="outlined">
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Audit events
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Newest events appear first. Expand a row to inspect its request payload.
          </Typography>
        </Box>
        <Divider />
        <TableContainer>
          <Table size="small" aria-label="Audit events table">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Tool</TableCell>
                <TableCell>Permission</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 5 }}>
                    <CircularProgress size={28} />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Loading audit events...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : events.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 5 }}>
                    <Typography color="text.secondary">
                      {error ? "Audit events could not be loaded." : "No audit events found."}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                events.map((event, index) => (
                  <AuditEventRow
                    key={`${event.timestamp}-${event.user_id}-${event.tool_name}-${index}`}
                    event={event}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Divider />
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_event, nextPage) => setPage(nextPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(Number(event.target.value));
            setPage(0);
          }}
          rowsPerPageOptions={PAGE_SIZE_OPTIONS}
        />
      </Paper>
    </Box>
  );
}
