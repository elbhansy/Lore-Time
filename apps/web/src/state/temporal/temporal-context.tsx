import React, { createContext, useContext, ReactNode, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * Phase 6.1 Temporal Context Abstraction.
 * 
 * Provides:
 * - Active series isolation (seriesId)
 * - Reader temporal horizon (readerChapter)
 * - Strict temporal bounds (minVisibleChapter: 1, maxVisibleChapter: readerChapter)
 * - Navigation actions (setReaderChapter, stepForward, stepBackward)
 * - Enforces the temporal firewall principle: future events (> readerChapter) are never visible.
 */

export interface TemporalContextState {
  seriesId: string;
  readerChapter: number;
  minVisibleChapter: number;
  maxVisibleChapter: number;
  totalChapters?: number;
  setReaderChapter: (chapter: number) => void;
  stepForward: () => void;
  stepBackward: () => void;
  canStepForward: boolean;
  canStepBackward: boolean;
}

const TemporalContext = createContext<TemporalContextState | undefined>(undefined);

export interface TemporalProviderProps {
  seriesId: string;
  totalChapters?: number;
  defaultChapter?: number;
  children: ReactNode;
}

export const TemporalProvider: React.FC<TemporalProviderProps> = ({
  seriesId,
  totalChapters = 200,
  defaultChapter = 1,
  children,
}) => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse and validate chapter from URL query param
  const chapterParam = searchParams.get('chapter');
  let readerChapter = defaultChapter;

  if (chapterParam) {
    const parsed = parseInt(chapterParam, 10);
    if (!isNaN(parsed) && parsed >= 1) {
      readerChapter = Math.min(parsed, totalChapters);
    }
  }

  const setReaderChapter = useCallback(
    (chapter: number) => {
      const bounded = Math.max(1, Math.min(chapter, totalChapters));
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('chapter', bounded.toString());
          return next;
        },
        { replace: false }
      );
    },
    [setSearchParams, totalChapters]
  );

  const stepForward = useCallback(() => {
    if (readerChapter < totalChapters) {
      setReaderChapter(readerChapter + 1);
    }
  }, [readerChapter, totalChapters, setReaderChapter]);

  const stepBackward = useCallback(() => {
    if (readerChapter > 1) {
      setReaderChapter(readerChapter - 1);
    }
  }, [readerChapter, setReaderChapter]);

  const value: TemporalContextState = {
    seriesId,
    readerChapter,
    minVisibleChapter: 1,
    maxVisibleChapter: readerChapter,
    totalChapters,
    setReaderChapter,
    stepForward,
    stepBackward,
    canStepForward: readerChapter < totalChapters,
    canStepBackward: readerChapter > 1,
  };

  return <TemporalContext.Provider value={value}>{children}</TemporalContext.Provider>;
};

export const useTemporalContext = (): TemporalContextState => {
  const ctx = useContext(TemporalContext);
  if (!ctx) {
    throw new Error('useTemporalContext must be used within a TemporalProvider');
  }
  return ctx;
};
