export interface User {
  id: number;
  username: string;
  email: string;
  date_joined: string;
}

export interface Tag {
  id: number;
  name: string;
}

export interface ResearchSource {
  title: string;
  url: string;
  snippet: string;
}

export interface ResearchResult {
  id: number;
  summary: string;
  sources: ResearchSource[];
  sub_queries: string[];
  created_at: string;
}

export interface ResearchQuery {
  id: number;
  question: string;
  query_hash: string;
  status: "pending" | "processing" | "completed" | "failed";
  tags: Tag[];
  result?: ResearchResult;
  created_at: string;
  updated_at: string;
}

export interface WSMessage {
  type: "status" | "result";
  status: string;
  detail: string;
  data?: {
    summary: string;
    sources: ResearchSource[];
    sub_queries: string[];
  };
}
