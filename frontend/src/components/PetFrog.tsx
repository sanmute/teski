import React, { useEffect, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { SpeechBubble } from './SpeechBubble';

export type CompanionCharacter = 'frog' | 'cat';

interface PetCompanionProps {
  character: CompanionCharacter;
  urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done';
  message?: string;
  isVisible: boolean;
  onDismiss: () => void;
}

const CHARACTER_ASSETS: Record<CompanionCharacter, { image: string; alt: string; idleEmoji: string }> = {
  frog: {
    image: '/teski-frog.svg',
    alt: 'Teski the Frog',
    idleEmoji: '🐸',
  },
  cat: {
    image: '/duey-cat.svg',
    alt: 'Duey the Cat',
    idleEmoji: '🐱',
  },
};

export function PetFrog({ character, urgency, message, isVisible, onDismiss }: PetCompanionProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentMood, setCurrentMood] = useState<string>('idle');

  useEffect(() => {
    if (isVisible && message) {
      setIsAnimating(true);
      // Set mood based on urgency
      setCurrentMood(urgency);
      
      // Auto-dismiss after 8 seconds for non-critical messages
      if (urgency !== 'intervention') {
        const timer = setTimeout(() => {
          onDismiss();
        }, 8000);
        return () => clearTimeout(timer);
      }
    } else {
      setIsAnimating(false);
      setCurrentMood('idle');
    }
  }, [isVisible, message, urgency, onDismiss]);

  const getFrogAppearance = () => {
    switch (urgency) {
      case 'intervention':
        return {
          bgColor: 'bg-destructive/20',
          borderColor: 'border-destructive',
          animation: '',
          emoji: '😡'
        };
      case 'disappointed':
        return {
          bgColor: 'bg-destructive/10',
          borderColor: 'border-destructive/70',
          animation: '',
          emoji: '😤'
        };
      case 'snark':
        return {
          bgColor: 'bg-warning/10',
          borderColor: 'border-warning',
          animation: '',
          emoji: '🙄'
        };
      case 'done':
        return {
          bgColor: 'bg-success/10',
          borderColor: 'border-success',
          animation: '',
          emoji: '😊'
        };
      default: // calm
        return {
          bgColor: 'bg-primary/10',
          borderColor: 'border-primary/50',
          animation: '',
          emoji: '🐸'
        };
    }
  };

  const frogStyle = getFrogAppearance();
  const asset = useMemo(() => CHARACTER_ASSETS[character], [character]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className={cn(
      "fixed bottom-0 right-0 z-50 transition-all duration-500 ease-out transform",
      isAnimating ? "translate-y-0 opacity-100 scale-100" : "translate-y-full opacity-0 scale-95"
    )}>
      {/* Speech Bubble */}
      {message && (
        <SpeechBubble
          message={message}
          urgency={urgency}
          onDismiss={onDismiss}
          className="mb-2"
        />
      )}
      
      {/* Teski Frog - No Container */}
      <img 
        src={asset.image}
        alt={asset.alt}
        onClick={onDismiss}
        role="button"
        aria-label="Dismiss pet frog notification"
        className={cn(
          "w-48 h-48 object-contain select-none transition-all duration-300 cursor-pointer",
          "hover:scale-110",
          // Mood-based visual effects
          urgency === 'intervention' && "brightness-75 contrast-125 hue-rotate-[350deg]", // Red angry tint
          urgency === 'disappointed' && "brightness-90 contrast-110 saturate-75", // Slightly dimmed
          urgency === 'snark' && "brightness-110 contrast-105 hue-rotate-[15deg]", // Slight warm tint
          urgency === 'done' && "brightness-125 contrast-110 saturate-125 hue-rotate-[90deg]", // Happy green glow
          urgency === 'calm' && "brightness-100",
          character === 'cat' && "scale-90"
        )}
      />
    </div>
  );
}
