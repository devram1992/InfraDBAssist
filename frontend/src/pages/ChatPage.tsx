import { useState } from "react";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import SendRoundedIcon from "@mui/icons-material/SendRounded";
import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";
import CloudOutlinedIcon from "@mui/icons-material/CloudOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";

import { sendChatMessage } from "../api/chat";
import { useAuth } from "../auth/useAuth";

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  selectedTool?: string | null;
}

const suggestions = [
  "Check PostgreSQL replication lag",
  "Investigate Oracle tablespace utilization",
  "Analyze Kubernetes pod failures",
  "Review database capacity",
];

function createConversationId(): string {
  return crypto.randomUUID();
}

export function ChatPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string>(
    createConversationId,
  );

  const { refreshToken, username } = useAuth();

  function handleNewChat() {
    if (loading) return;

    setQuestion("");
    setMessages([]);
    setError(null);
    setConversationId(createConversationId());
  }

  async function handleSend() {
    const submittedQuestion = question.trim();

    if (!submittedQuestion || loading) return;

    setError(null);
    setQuestion("");
    setLoading(true);

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: submittedQuestion,
    };

    setMessages((previous) => [...previous, userMessage]);

    try {
      await refreshToken();

      const response = await sendChatMessage(
        submittedQuestion,
        conversationId,
      );

      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          response.answer || "The assistant returned an empty response.",
        selectedTool: response.selected_tool,
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred.";

      setError(message);
      setQuestion(submittedQuestion);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box sx={{ maxWidth: 1050, mx: "auto", py: 5 }}>
      <Stack
        direction="row"
        sx={{
          justifyContent: "space-between",
          alignItems: "center",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            AI Engineering Assistant
          </Typography>

          <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>
            Your database and infrastructure operations workspace
          </Typography>

          {username && (
            <Typography color="text.secondary" variant="caption">
              Signed in as {username}
            </Typography>
          )}
        </Box>

        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <Chip label="Development" color="success" variant="outlined" />
          <Button
            variant="outlined"
            size="small"
            onClick={handleNewChat}
            disabled={loading}
          >
            New chat
          </Button>
        </Stack>
      </Stack>

      {messages.length === 0 ? (
        <Box sx={{ textAlign: "center", mt: 12, mb: 6 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            How can I help you today?
          </Typography>

          <Typography color="text.secondary" sx={{ mt: 2 }}>
            Ask questions about databases, infrastructure, incidents and
            runbooks.
          </Typography>
        </Box>
      ) : (
        <Stack spacing={2} sx={{ mt: 5, mb: 4 }}>
          {messages.map((message) => (
            <Paper
              key={message.id}
              variant="outlined"
              sx={{
                p: 2.5,
                borderRadius: 2,
                alignSelf:
                  message.role === "user" ? "flex-end" : "stretch",
                maxWidth: message.role === "user" ? "85%" : "100%",
                bgcolor:
                  message.role === "user"
                    ? "action.hover"
                    : "background.paper",
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 700 }}
              >
                {message.role === "user" ? "YOU" : "INFRADB AI"}
              </Typography>

              <Typography
                variant="body1"
                sx={{
                  mt: 1,
                  whiteSpace: "pre-wrap",
                  overflowWrap: "anywhere",
                }}
              >
                {message.content}
              </Typography>

              {message.selectedTool && (
                <Chip
                  size="small"
                  label={`Tool: ${message.selectedTool}`}
                  sx={{ mt: 2 }}
                  variant="outlined"
                />
              )}
            </Paper>
          ))}

          {loading && (
            <Stack
              direction="row"
              spacing={1.5}
              sx={{ alignItems: "center" }}
            >
              <CircularProgress size={18} />

              <Typography variant="body2" color="text.secondary">
                InfraDB AI is processing your request...
              </Typography>
            </Stack>
          )}
        </Stack>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper
        variant="outlined"
        sx={{ p: 2, borderRadius: 3, bgcolor: "background.paper" }}
      >
        <TextField
          fullWidth
          multiline
          minRows={3}
          maxRows={6}
          placeholder="Ask InfraDB AI anything about your infrastructure..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
              event.preventDefault();
              void handleSend();
            }
          }}
          variant="standard"
          slotProps={{ input: { disableUnderline: true } }}
        />

        <Stack
          direction="row"
          sx={{
            justifyContent: "space-between",
            alignItems: "center",
            mt: 2,
            gap: 1,
          }}
        >
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
            <Chip
              size="small"
              icon={<StorageOutlinedIcon />}
              label="Databases"
            />

            <Chip
              size="small"
              icon={<CloudOutlinedIcon />}
              label="Infrastructure"
            />

            <Chip
              size="small"
              icon={<SearchOutlinedIcon />}
              label="Knowledge RAG"
            />
          </Stack>

          <Button
            variant="contained"
            endIcon={
              loading ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <SendRoundedIcon />
              )
            }
            disabled={!question.trim() || loading}
            onClick={() => void handleSend()}
          >
            {loading ? "Processing" : "Send"}
          </Button>
        </Stack>
      </Paper>

      {messages.length === 0 && (
        <>
          <Typography
            variant="subtitle2"
            color="text.secondary"
            sx={{ mt: 5, mb: 2 }}
          >
            SUGGESTED QUESTIONS
          </Typography>

          <Stack spacing={1}>
            {suggestions.map((suggestion) => (
              <Paper
                key={suggestion}
                variant="outlined"
                onClick={() => setQuestion(suggestion)}
                sx={{
                  p: 2,
                  cursor: "pointer",
                  "&:hover": { borderColor: "primary.main" },
                }}
              >
                <Typography variant="body2">{suggestion}</Typography>
              </Paper>
            ))}
          </Stack>
        </>
      )}
    </Box>
  );
}
