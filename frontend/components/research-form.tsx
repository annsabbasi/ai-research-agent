"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Send } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";

export function ResearchForm() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || question.trim().length < 10) {
      toast.error("Please enter a question with at least 10 characters");
      return;
    }

    setLoading(true);
    try {
      const { data, status } = await api.post("/research/", { question });
      if (status === 201) {
        toast.success("Cache hit! Results loaded instantly.");
      } else {
        toast.success("Research started! Tracking progress...");
      }
      router.push(`/research/${data.id}`);
    } catch {
      toast.error("Failed to submit research question");
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Research</CardTitle>
        <CardDescription>
          Ask any research question and our AI will generate a comprehensive
          report
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            placeholder="e.g., What are the latest advances in quantum computing?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="min-h-[80px] flex-1"
          />
          <Button type="submit" disabled={loading} className="self-end">
            <Send className="h-4 w-4 mr-2" />
            {loading ? "Submitting..." : "Research"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
