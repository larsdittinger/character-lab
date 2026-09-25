/** Run the shared motion pipeline against the ranger's own measured rig. */
const files={retarget:'retarget.mjs',clips:'export_clips.mjs',validate:'validate.mjs'};
const stage=process.argv[2];
if(!files[stage])throw new Error('Expected retarget, clips, or validate');
process.env.CHARACTER_LAB_CHARACTER='ranger';
await import('./'+files[stage]);
