"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ExternalLink, Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import api from "@/lib/api";
import { ResearchWebSocket } from "@/lib/websocket";
import type { ResearchQuery, WSMessage } from "@/types";

interface Props {
  queryId: number;
}

export function ResearchDetail({ queryId }: Props) {
  const [query, setQuery] = useState<ResearchQuery | null>(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchQuery = useCallback(async () => {
    try {
      const { data } = await api.get(`/research/${queryId}/`);
      setQuery(data);
    } catch {
      toast.error("Failed to load research");
    } finally {
      setLoading(false);
    }
  }, [queryId]);

  useEffect(() => {
    fetchQuery();
  }, [fetchQuery]);

  useEffect(() => {
    if (!query || query.status === "completed" || query.status === "failed")
      return;

    const ws = new ResearchWebSocket(
      queryId,
      (msg: WSMessage) => {
        setStatusMsg(msg.detail);
        if (msg.type === "result" && msg.status === "completed") {
          fetchQuery();
        }
        if (msg.status === "failed") {
          setQuery((prev) => (prev ? { ...prev, status: "failed" } : prev));
        }
      },
      () => {
        fetchQuery();
      }
    );
    ws.connect();

    return () => ws.disconnect();
  }, [query?.status, queryId, fetchQuery]);

  const addTag = async () => {
    if (!tagInput.trim()) return;
    try {
      await api.post(`/research/${queryId}/tags/`, { name: tagInput.trim() });
      setTagInput("");
      fetchQuery();
      toast.success("Tag added");
    } catch {
      toast.error("Failed to add tag");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!query) return <p>Research not found.</p>;

  const isProcessing =
    query.status === "pending" || query.status === "processing";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">{query.question}</h1>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge
            variant={query.status === "completed" ? "default" : "secondary"}
          >
            {query.status}
          </Badge>
          {query.tags.map((tag) => (
            <Badge key={tag.id} variant="outline">
              {tag.name}
            </Badge>
          ))}
          <div className="flex items-center gap-1">
            <Input
              placeholder="Add tag..."
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              className="h-7 w-32 text-xs"
              onKeyDown={(e) => e.key === "Enter" && addTag()}
            />
            <Button size="icon" variant="ghost" className="h-7 w-7" onClick={addTag}>
              <Plus className="h-3 w-3" />
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Created {new Date(query.created_at).toLocaleString()}
        </p>
      </div>

      {isProcessing && (
        <Card>
          <CardContent className="flex items-center gap-3 py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <div>
              <p className="font-medium">Research in progress...</p>
              <p className="text-sm text-muted-foreground">
                {statusMsg || "Initializing research agent..."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {query.status === "failed" && (
        <Card>
          <CardContent className="py-6">
            <p className="text-destructive font-medium">
              Research failed. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {query.result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Research Report</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{query.result.summary}</ReactMarkdown>
            </CardContent>
          </Card>

          {query.result.sub_queries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sub-queries</CardTitle>
                <CardDescription>
                  Questions the AI investigated to answer your research question
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {query.result.sub_queries.map((sq, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Badge variant="outline" className="shrink-0 mt-0.5">
                        {i + 1}
                      </Badge>
                      <span className="text-sm">{sq}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {query.result.sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sources</CardTitle>
                <CardDescription>
                  References used in this research
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {query.result.sources.map((source, i) => (
                    <div key={i}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                      >
                        {source.title || source.url}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                      {source.snippet && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {source.snippet}
                        </p>
                      )}
                      {i < query.result!.sources.length - 1 && (
                        <Separator className="mt-3" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
