export type TaskType = 'variance_explanation' | 'executive_narrative' | 'assumption_risk_check';

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export interface RetrievedDoc {
  id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  response_text: string;
  retrieved_docs: RetrievedDoc[];
}
