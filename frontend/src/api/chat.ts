import { apiClient } from "./client";

export interface ChatRequest {
  question: string;
  conversation_id: string;
}

export interface ChatResponse {
  status: string;
  question: string;
  selected_tool: string | null;
  parameters: Record<string, unknown>;
  tool_result: unknown;
  knowledge_results: unknown[];
  answer: string;
}

export async function sendChatMessage(
  question: string,
  conversationId: string,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/chat", {
    question,
    conversation_id: conversationId,
  } satisfies ChatRequest);

  return response.data;
}