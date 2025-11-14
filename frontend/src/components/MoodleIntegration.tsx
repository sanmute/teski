import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ExternalLink, Loader2, RefreshCcw, Link as LinkIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api";
import clsx from "clsx";

import { getClientUserId } from "@/lib/user";

interface MoodleIntegrationProps {
  onImported?: () => void;
}

export function MoodleIntegration({ onImported }: MoodleIntegrationProps) {
  const [moodleUrl, setMoodleUrl] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const userId = useMemo(() => getClientUserId(), []);

  const statusQuery = useQuery({
    queryKey: ["moodle-feed", userId],
    queryFn: () => api.getMoodleFeedStatus(userId),
  });

  useEffect(() => {
    if (statusQuery.data?.hasFeed && statusQuery.data.lastFetchAt) {
      // nothing additional yet
    }
  }, [statusQuery.data]);

  const refreshMutation = useMutation({
    mutationFn: () => api.refreshMoodleFeed(userId),
    onSuccess: (result) => {
      toast({
        title: "Moodle tasks updated",
        description: `Imported ${result.imported}, updated ${result.updated}, skipped ${result.skipped}.`,
      });
      statusQuery.refetch();
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      onImported?.();
    },
    onError: (err: unknown) => {
      toast({
        title: "Failed to refresh Moodle tasks",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  const connectMutation = useMutation({
    mutationFn: (url: string) => api.saveMoodleUrl({ userId, url }),
    onSuccess: () => {
      toast({
        title: "Moodle connected",
        description: "Fetching assignments from your feed…",
      });
      refreshMutation.mutate();
    },
    onError: (err: unknown) => {
      toast({
        title: "Failed to connect",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  const handleConnect = () => {
    if (!moodleUrl.trim()) {
      toast({
        title: "Missing URL",
        description: "Please paste your Moodle ICS calendar URL.",
        variant: "destructive",
      });
      return;
    }
    connectMutation.mutate(moodleUrl.trim());
  };

  const lastFetch = statusQuery.data?.lastFetchAt ? new Date(statusQuery.data.lastFetchAt) : null;
  const expiresAt = statusQuery.data?.expiresAt ? new Date(statusQuery.data.expiresAt) : null;
  const needsRenewal = statusQuery.data?.needsRenewal ?? true;
  const shouldCollectLink = !statusQuery.data?.hasFeed || needsRenewal;

  const isBusy = connectMutation.isPending || refreshMutation.isPending;

  return (
    <Card className="border-2 border-primary/20 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <ExternalLink className="w-5 h-5" />
          Connect Your Moodle Course
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {shouldCollectLink ? (
          <>
            {statusQuery.data?.hasFeed && needsRenewal && (
              <div className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900">
                Your previous Moodle link expired. Please paste a fresh ICS link (valid for 60 days).
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="moodle-url">Moodle Course URL</Label>
              <Input
                id="moodle-url"
                type="url"
                placeholder="https://your-school.moodle.com/course/view.php?id=123"
                value={moodleUrl}
                onChange={(e) => setMoodleUrl(e.target.value)}
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Enter the URL of your Moodle course to automatically import assignments
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <Button onClick={handleConnect} disabled={isBusy} className="w-full">
                {connectMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Checking feed…
                  </>
                ) : (
                  <>
                    <LinkIcon className="w-4 h-4 mr-2" />
                    Connect Moodle calendar
                  </>
                )}
              </Button>
            </div>
          </>
        ) : (
          <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-900">
            Your Moodle calendar is connected. The link stays valid until{" "}
            {expiresAt ? expiresAt.toLocaleDateString() : "60 days after connection"}.
          </div>
        )}

        <Button
          variant="outline"
          onClick={() => refreshMutation.mutate()}
          disabled={!statusQuery.data?.hasFeed || isBusy}
          className="w-full"
        >
          {refreshMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Refreshing tasks…
            </>
          ) : (
            <>
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh Moodle tasks
            </>
          )}
        </Button>

        <div className="rounded-md border border-border/50 bg-background/60 p-3 text-xs text-muted-foreground space-y-1">
          <div className="flex items-center justify-between">
            <span>Status:</span>
            <span
              className={clsx(
                "font-medium",
                statusQuery.data?.hasFeed && !needsRenewal ? "text-success" : "text-destructive"
              )}
            >
              {statusQuery.isLoading
                ? "Checking…"
                : statusQuery.data?.hasFeed
                ? needsRenewal
                  ? "Needs new link"
                  : "Connected"
                : "Not connected"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>User ID:</span>
            <code className="text-muted-foreground">{userId}</code>
          </div>
          <div className="flex items-center justify-between">
            <span>Last fetch:</span>
            <span>
              {statusQuery.isLoading
                ? "…"
                : lastFetch
                ? lastFetch.toLocaleString()
                : "never"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Link expires:</span>
            <span>
              {expiresAt ? expiresAt.toLocaleDateString() : "—"}
            </span>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Tip: in Moodle, open your calendar, choose “Export calendar” and copy the
          ICS URL. Paste it above and Teski will keep the tasks synced.
        </p>
      </CardContent>
    </Card>
  );
}
