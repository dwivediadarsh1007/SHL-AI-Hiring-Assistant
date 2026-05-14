export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface AssessmentRecommendation {
  name: string;
  url: string;
  test_type: string;
}

export interface ChatRequest {
  messages: Message[];
}

export interface ChatResponse {
  reply: string;
  recommendations: AssessmentRecommendation[];
  end_of_conversation: boolean;
}
