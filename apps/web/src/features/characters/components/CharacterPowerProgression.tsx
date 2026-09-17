import React from 'react';
import { useRankProgression } from '../../power-system/hooks/useRankProgression';
import { RankProgression } from '../../power-system/components/RankProgression';

export const CharacterPowerProgression: React.FC<{ seriesId: string, characterId: string, readerChapter: number }> = ({ seriesId, characterId, readerChapter }) => {
  const { data: ranks, isLoading } = useRankProgression(seriesId, characterId, readerChapter);

  if (isLoading) return <p>Loading power progression...</p>;
  if (!ranks || ranks.length === 0) return <p style={{ fontStyle: 'italic', color: '#7f8c8d' }}>No rank changes recorded.</p>;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3>Power Progression</h3>
      <RankProgression ranks={ranks} />
    </div>
  );
};
