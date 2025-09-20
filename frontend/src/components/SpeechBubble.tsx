import React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SpeechBubbleProps {
  message: string;
  urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done';
  onDismiss: () => void;
  className?: string;
}

export function SpeechBubble({ message, urgency, onDismiss, className }: SpeechBubbleProps) {
  const getBubbleStyle = () => {
    switch (urgency) {
      case 'intervention':
        return {
          bgColor: 'bg-destructive/95',
          textColor: 'text-destructive-foreground',
          borderColor: 'border-destructive',
          title: '🚨 URGENT'
        };
      case 'disappointed':
        return {
          bgColor: 'bg-destructive/85',
          textColor: 'text-destructive-foreground',
          borderColor: 'border-destructive/70',
          title: '⚠️ CRITICAL'
        };
      case 'snark':
        return {
          bgColor: 'bg-warning/90',
          textColor: 'text-warning-foreground',
          borderColor: 'border-warning',
          title: '⏰ REMINDER'
        };
      case 'done':
        return {
          bgColor: 'bg-success/90',
          textColor: 'text-success-foreground',
          borderColor: 'border-success',
          title: '✅ WELL DONE'
        };
      default: // calm
        return {
          bgColor: 'bg-card',
          textColor: 'text-card-foreground',
          borderColor: 'border-border',
          title: '💭 GENTLE REMINDER'
        };
    }
  };

  const bubbleStyle = getBubbleStyle();

  return (
    <div className={cn(
      "relative max-w-xs p-4 rounded-lg border-2 shadow-card animate-fade-in",
      bubbleStyle.bgColor,
      bubbleStyle.textColor,
      bubbleStyle.borderColor,
      className
    )}>
      {/* Close button */}
      <Button
        onClick={onDismiss}
        size="sm"
        variant="ghost"
        className="absolute top-1 right-1 w-6 h-6 p-0 hover:bg-black/20"
      >
        <X className="w-3 h-3" />
      </Button>
      
      {/* Title */}
      <div className="text-xs font-bold mb-2 opacity-90">
        {bubbleStyle.title}
      </div>
      
      {/* Message */}
      <div className="text-sm leading-tight pr-6">
        {message}
      </div>
      
      {/* Speech bubble tail pointing to frog */}
      <div className={cn(
        "absolute bottom-0 right-8 transform translate-y-full",
        "w-0 h-0 border-l-[12px] border-r-[12px] border-t-[12px]",
        "border-l-transparent border-r-transparent",
        urgency === 'intervention' ? 'border-t-destructive' :
        urgency === 'disappointed' ? 'border-t-destructive/85' :
        urgency === 'snark' ? 'border-t-warning' :
        urgency === 'done' ? 'border-t-success' :
        'border-t-card'
      )} />
    </div>
  );
}