import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Task } from "@/types/task";
import { Clock, AlertTriangle, CheckCircle, Zap, ExternalLink, Timer, BookOpen, ListTodo } from "lucide-react";
import { differenceInHours } from "date-fns";
import clsx from "clsx";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import api, { StudyPackResponse } from "@/api";
import { CompanionCharacter } from "@/components/PetFrog";
import { ExplainButton } from "@/components/ExplainButton";
import { getCompanionMessage } from "@/utils/companionVoice";

interface LegacyTaskCardProps {
  task: Task;
  onTriggerFrog?: (urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done', message: string) => void;
  onMarkDone?: (taskId: string) => void;
  onUndo?: (taskId: string) => void;
  disabled?: boolean;
  companion: CompanionCharacter;
}

export function LegacyTaskCard({ task, onTriggerFrog, onMarkDone, onUndo, disabled, companion }: LegacyTaskCardProps) {
  const dueDate = new Date(task.due_iso);
  const now = new Date();
  
  // Calculate time-based urgency category
  const getTimeCategory = () => {
    if (task.status === 'done') return 'done';
    
    const hoursUntilDue = differenceInHours(dueDate, now);
    
    if (hoursUntilDue < 0) {
      return 'intervention'; // overdue
    } else if (hoursUntilDue <= 24) {
      return 'disappointed'; // 0-24h before due
    } else if (hoursUntilDue <= 72) {
      return 'snark'; // 24-72h before due
    } else {
      return 'calm'; // >72h before due
    }
  };
  
  const timeCategory = getTimeCategory();
  const hoursUntilDue = differenceInHours(dueDate, now);
  
  const getStatusColor = () => {
    if (task.status === 'done') return 'success';
    if (task.status === 'overdue' || timeCategory === 'intervention') return 'destructive';
    if (timeCategory === 'disappointed') return 'destructive';
    if (timeCategory === 'snark') return 'warning';
    return 'default'; // calm
  };

  const getStatusIcon = () => {
    if (task.status === 'done') return <CheckCircle className="w-4 h-4" />;
    if (task.status === 'overdue' || timeCategory === 'intervention') return <Zap className="w-4 h-4" />;
    if (timeCategory === 'disappointed') return <AlertTriangle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };


  const handleAction = () => {
    if (task.status === 'done') {
      onUndo?.(task.id);
      const message = getCompanionMessage(companion, 'undo', task.title);
      onTriggerFrog?.('calm', message);
    } else {
      onMarkDone?.(task.id);
      const message = getCompanionMessage(companion, 'mark-done', task.title);
      onTriggerFrog?.('done', message);
    }
  };

  const studyPackQuery = useQuery<StudyPackResponse | null>({
    queryKey: ['study-pack', task.id],
    queryFn: async () => {
      const pack = await api.getStudyPack(task.id);
      if (pack) return pack;
      // Build one if none exists yet
      return api.buildStudyPack(task.id);
    },
    staleTime: 1000 * 60 * 30,
  });

  return (
    <Card className="gradient-card border-border/50 hover:border-primary/30 transition-smooth shadow-card hover:shadow-glow">
      <CardContent className="p-6 space-y-4">
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-card-foreground mb-1">
                {task.title}
              </h3>
              <p className="text-sm text-muted-foreground flex items-center gap-2 flex-wrap">
                <Clock className="w-4 h-4" />
                Due: {dueDate.toLocaleDateString()} at {dueDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                {task.status !== 'done' && (
                  <span
                    className={clsx(
                      'text-xs font-medium ml-2',
                      timeCategory === 'intervention'
                        ? 'text-destructive'
                        : timeCategory === 'disappointed'
                        ? 'text-destructive'
                        : timeCategory === 'snark'
                        ? 'text-warning'
                        : 'text-muted-foreground'
                    )}
                  >
                    ({hoursUntilDue < 0 ? `${Math.abs(hoursUntilDue)}h overdue` : `${hoursUntilDue}h left`})
                  </span>
                )}
              </p>
              <div className="text-xs text-muted-foreground mt-1 space-y-1">
                {task.task_type && <div>Type: {task.task_type}</div>}
                {typeof task.estimated_minutes === 'number' && (
                  <div className="flex items-center gap-1">
                    <Timer className="w-3 h-3" />
                    Est. {task.estimated_minutes} min · start by {task.suggested_start_utc ? new Date(task.suggested_start_utc).toLocaleString() : 'ASAP'}
                  </div>
                )}
                {task.confidence !== undefined && <div>Confidence: {(task.confidence * 100).toFixed(0)}%</div>}
                {task.link && (
                  <a
                    className="inline-flex items-center gap-1 text-primary hover:underline"
                    href={task.link}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Open source
                  </a>
                )}
              </div>
            </div>
            <Badge
              variant="outline"
              className={clsx(
                'flex items-center gap-2 w-fit font-medium transition-smooth whitespace-nowrap',
                task.status === 'done' && 'border-success text-success',
                timeCategory === 'intervention' && 'border-destructive text-destructive',
                timeCategory === 'disappointed' && 'border-destructive text-destructive',
                timeCategory === 'snark' && 'border-warning text-warning',
                timeCategory === 'calm' && 'border-muted text-muted-foreground'
              )}
            >
              {getStatusIcon()}
              {task.status === 'done'
                ? 'DONE'
                : timeCategory === 'intervention'
                ? 'OVERDUE'
                : timeCategory === 'disappointed'
                ? 'URGENT'
                : timeCategory === 'snark'
                ? 'DUE SOON'
                : 'PENDING'}
            </Badge>
          </div>

          {task.notes && (
            <div className="rounded-md bg-secondary/20 p-3 text-sm text-muted-foreground">
              <p>{task.notes}</p>
              <div className="mt-2">
                <ExplainButton text={task.notes} />
              </div>
            </div>
          )}

        </div>

        {(onMarkDone || onUndo) && (
          <div className="flex justify-end">
            <Button
              size="sm"
              variant={task.status === 'done' ? 'outline' : 'default'}
              onClick={handleAction}
              disabled={disabled}
            >
              {task.status === 'done' ? 'Mark as not done' : 'Mark as done'}
            </Button>
          </div>
        )}

        <StudyPackSection queryState={studyPackQuery} />
      </CardContent>
    </Card>
  );
}

interface StudyPackSectionProps {
  queryState: UseQueryResult<StudyPackResponse | null, unknown>;
}

function StudyPackSection({ queryState }: StudyPackSectionProps) {
  if (queryState.isLoading) {
    return (
      <div className="rounded-md border border-border/40 bg-secondary/10 p-3 text-xs text-muted-foreground">
        Loading study pack…
      </div>
    );
  }

  if (queryState.isError) {
    return (
      <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
        Could not load study pack. Try again later.
      </div>
    );
  }

  const pack = queryState.data;
  if (!pack) {
    return null;
  }

  return (
    <div className="rounded-md border border-border/40 bg-secondary/5 p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground/90">
        <BookOpen className="w-4 h-4" /> Topic: {pack.topic}
      </div>
      <div className="space-y-2">
        {pack.resources.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">Suggested resources</div>
            <ul className="space-y-2">
              {pack.resources.map((r) => (
                <li key={r.url} className="text-sm text-muted-foreground">
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:underline font-medium flex items-center gap-2"
                  >
                    <ExternalLink className="w-3 h-3" />
                    {r.title}
                  </a>
                  <div className="text-xs text-muted-foreground/80">{r.why}</div>
                </li>
              ))}
            </ul>
          </div>
        )}
        {pack.practice.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">Practice</div>
            <ul className="space-y-2">
              {pack.practice.map((p, idx) => (
                <li key={`${p.prompt}-${idx}`} className="text-sm text-muted-foreground">
                  <div className="flex items-start gap-2">
                    <ListTodo className="w-3 h-3 mt-1" />
                    <div>
                      <div>{p.prompt}</div>
                      {p.solution_url && (
                        <a
                          href={p.solution_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-primary hover:underline"
                        >
                          View solution
                        </a>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
