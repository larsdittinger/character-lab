/** Artifact paths shared by both calibrated characters; source motion is shared. */
import path from 'node:path';
export const root = path.resolve(import.meta.dirname, '..');
export const character = process.env.CHARACTER_LAB_CHARACTER || 'knight';
if (!['knight', 'ranger', 'elf'].includes(character)) throw new Error('Unknown CHARACTER_LAB_CHARACTER: ' + character);
export const artifacts = {
  rigged: `assets/${character}-rigged.glb`,
  animated: `assets/${character}-animated.glb`,
  catalog: character === 'knight' ? 'animations/catalog.json' : `animations/${character}/catalog.json`,
  motion: character === 'knight' ? 'animations/retargeted' : `animations/${character}/retargeted`,
  review: character === 'knight' ? 'review' : `review/${character}`,
};
