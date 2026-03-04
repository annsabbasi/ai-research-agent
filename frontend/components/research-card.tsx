"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2, Clock, CheckCircle, Loader2, XCircle } from "lucide-react";
import type { ResearchQuery } from "@/types";

const statusConfig = {
  pending: { icon: Clock, label: "Pending", variant: "secondary" as const },
  processing: {
    icon: Loader2,
    label: "Processing",
    variant: "default" as const,
  },
  completed: {
    icon: CheckCircle,
    label: "Completed",
    variant: "default" as const,
  },
  failed: { icon: XCircle, label: "Failed", variant: "destructive" as const },
};

interface Props {
  query: ResearchQuery;
  onDelete: (id: number) => void;
}

export function ResearchCard({ query, onDelete }: Props) {
  const config = statusConfig[query.status];
  const StatusIcon = config.icon;

  return (
    <Link href={`/research/${query.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base line-clamp-2">
              {query.question}
            </CardTitle>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 h-8 w-8"
              onClick={(e: React.MouseEvent) => {
                e.preventDefault();
                onDelete(query.id);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription>
            {new Date(query.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant={config.variant} className="flex items-center gap-1">
              <StatusIcon
                className={`h-3 w-3 ${query.status === "processing" ? "animate-spin" : ""}`}
              />
              {config.label}
            </Badge>
            {query.tags.map((tag) => (
              <Badge key={tag.id} variant="outline">
                {tag.name}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
