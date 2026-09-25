// Compact motion-only GLBs: one shared node hierarchy, no repeated mesh or texture.
import fs from 'node:fs';import path from 'node:path';
import {readGLB,accessor,appendAccessor,writeGLB} from './glb.mjs';
import {artifacts} from './character_paths.mjs';
const R=path.resolve(import.meta.dirname,'..'),source=readGLB(path.join(R,artifacts.animated)),dir=path.join(R,artifacts.motion);fs.mkdirSync(dir,{recursive:true});
for(const a of source.json.animations){
 const nodes=structuredClone(source.json.nodes);for(const n of nodes){delete n.mesh;delete n.skin;}
 const g={json:{asset:{version:'2.0',generator:'Character Lab motion export'},scene:source.json.scene,scenes:source.json.scenes,nodes,accessors:[],bufferViews:[],animations:[]},bin:Buffer.alloc(0)};
 const clip=structuredClone(a);for(const s of clip.samplers){s.input=appendAccessor(g,accessor(source,s.input),'SCALAR');s.output=appendAccessor(g,accessor(source,s.output),source.json.accessors[s.output].type);}g.json.animations.push(clip);
 writeGLB(g,path.join(dir,a.name+'.glb'));
}
console.log('Exported',source.json.animations.length,'motion-only GLBs');
