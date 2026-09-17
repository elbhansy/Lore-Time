import React, { createContext, useContext, ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import { TemporalProvider } from '../../state/temporal/temporal-context';

export interface ReaderContextType {
  seriesId: string;
  readerChapter: number;
  setReaderChapter: (chapter: number) => void;
}

const ReaderContext = createContext<ReaderContextType | undefined>(undefined);

interface ReaderProviderProps {
  seriesId: string;
  children: ReactNode;
}

export const ReaderProvider: React.FC<ReaderProviderProps> = ({ seriesId, children }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const chapterParam = searchParams.get('chapter');
  let readerChapter = 1;

  if (chapterParam) {
    const parsed = parseInt(chapterParam, 10);
    if (!isNaN(parsed) && parsed >= 1) {
      readerChapter = parsed;
    }
  }

  const setReaderChapter = (chapter: number) => {
    if (chapter < 1) return;
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set('chapter', chapter.toString());
        return next;
      },
      { replace: false }
    );
  };

  return (
    <TemporalProvider seriesId={seriesId} defaultChapter={readerChapter}>
      <ReaderContext.Provider value={{ seriesId, readerChapter, setReaderChapter }}>
        {children}
      </ReaderContext.Provider>
    </TemporalProvider>
  );
};

export const useReader = (): ReaderContextType => {
  const context = useContext(ReaderContext);
  if (!context) {
    throw new Error('useReader must be used within a ReaderProvider');
  }
  return context;
};
