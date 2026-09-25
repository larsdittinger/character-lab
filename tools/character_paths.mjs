/** Target-specific paths; source animation remains shared across all characters. */
import fs from 'node:fs';
import path from 'node:path';
export const root = path.resolve(import.meta.dirname, '..');
export const character = process.env.CHARACTER_LAB_CHARACTER || 'knight';
if (!/^[a-z][a-z0-9_-]*$/.test(character)) throw new Error('Invalid character ID');
const legacy = ['knight', 'ranger', 'elf'].includes(character);
if (!legacy && !fs.existsSync(path.join(root, 'characters', character, 'character.json'))) throw new Error('Unknown CHARACTER_LAB_CHARACTER: ' + character);
export const artifacts = legacy ? {
  rigged: `assets/${character}-rigged.glb`,
  animated: `assets/${character}-animated.glb`,
  catalog: character === 'knight' ? 'animations/catalog.json' : `animations/${character}/catalog.json`,
  motion: character === 'knight' ? 'animations/retargeted' : `animations/${character}/retargeted`,
  review: character === 'knight' ? 'review' : `review/${character}`,
} : {
  rigged: `characters/${character}/assets/rigged.glb`,
  animated: `characters/${character}/assets/animated.glb`,
  catalog: `characters/${character}/animations/catalog.json`,
  motion: `characters/${character}/animations/retargeted`,
  review: `characters/${character}/review`,
};
