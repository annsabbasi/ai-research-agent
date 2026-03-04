"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Navbar } from "@/components/navbar";
import { ResearchForm } from "@/components/research-form";
import { ResearchCard } from "@/components/research-card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import api from "@/lib/api";
import type { ResearchQuery } from "@/types";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [queries, setQueries] = useState<ResearchQuery[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueries = useCallback(async () => {
    try {
      const { data } = await api.get("/research/list/");
      setQueries(data.results);
    } catch {
      toast.error("Failed to load research history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }
    if (user) fetchQueries();
  }, [user, authLoading, router, fetchQueries]);

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/research/${id}/`);
      setQueries((prev) => prev.filter((q) => q.id !== id));
      toast.success("Research deleted");
    } catch {
      toast.error("Failed to delete");
    }
  };

  if (authLoading) return null;
  if (!user) return null;

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />
      <main className="container mx-auto px-4 py-8 space-y-8">
        <ResearchForm />

        <div>
          <h2 className="text-2xl font-bold mb-4">Research History</h2>
          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-40" />
              ))}
            </div>
          ) : queries.length === 0 ? (
            <p className="text-muted-foreground text-center py-12">
              No research yet. Submit your first question above!
            </p>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {queries.map((query) => (
                <ResearchCard
                  key={query.id}
                  query={query}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
