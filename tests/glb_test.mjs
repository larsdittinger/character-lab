import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {appendAccessor, accessor, writeGLB, readGLB} from '../tools/glb.mjs';
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'character-lab-glb-'));
try {
  const g = {json: {asset: {version:'2.0'}, accessors:[], bufferViews:[]}, bin:Buffer.from([1,2,3])};
  const expected = [Buffer.from([1,2,3,0])];
  for (let i=0; i<500; i++) {
    const values = [i/3, -i/7, .5, 1];
    const id = appendAccessor(g, values, 'VEC4');
    expected.push(Buffer.from(new Float32Array(values).buffer));
    if (i===17) assert.deepEqual(accessor(g,id), new Float32Array(values));
  }
  writeGLB(g, path.join(dir,'test.glb'));
  const copy=readGLB(path.join(dir,'test.glb'));
  assert.deepEqual(copy.bin,Buffer.concat(expected));
  assert.deepEqual(accessor(copy,499),new Float32Array([499/3,-499/7,.5,1]));
  assert.equal(copy.json.accessors.length,500);
  console.log('PASS: aligned binary chunks, read-before-write, 500 channels and exact round-trip bytes');
} finally { fs.rmSync(dir,{recursive:true,force:true}); }
