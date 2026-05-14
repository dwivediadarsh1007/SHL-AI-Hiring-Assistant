import axios from "axios";
import { ChatRequest, ChatResponse } from "../types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const chatAPI = {
  sendMessage: async (messages: ChatRequest["messages"]): Promise<ChatResponse> => {
    try {
      const response = await apiClient.post<ChatResponse>("/chat", { messages });
      return response.data;
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  },
  
  checkHealth: async () => {
    const response = await apiClient.get("/health");
    return response.data;
  }
};
