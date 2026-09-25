/** Validate the deliverable and actually evaluate all animation clips on the skin. */
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import * as T from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {readGLB,accessor} from './glb.mjs';
import {artifacts,character} from './character_paths.mjs';
const R=path.resolve(import.meta.dirname,'..');
const reportPath=path.join(R,artifacts.review,'validation.json');
fs.writeFileSync(reportPath,JSON.stringify({passed:false,state:'running'},null,2));
process.on('uncaughtException',error=>{fs.writeFileSync(reportPath,JSON.stringify({passed:false,error:error.message},null,2));console.error(error);process.exitCode=1;});
const g=readGLB(path.join(R,artifacts.animated)),j=g.json;
const cat=JSON.parse(fs.readFileSync(path.join(R,artifacts.catalog)));
assert.equal(j.animations.length,cat.length);assert.equal(new Set(cat.map(c=>c.name)).size,cat.length);
assert.equal(j.skins[0].joints.length,27,'Expected the 27-joint target hierarchy');
assert(j.images?.length>0&&j.images.every(im=>im.bufferView!==undefined&&!im.uri),'Embedded image required');
assert(!j.buffers.some(b=>b.uri),'Geometry must be self-contained');
// Check the delivered files, not only the count reported by the exporter.
const expectedNodes=structuredClone(j.nodes);for(const n of expectedNodes){delete n.mesh;delete n.skin;}
for(const animation of j.animations){
 const motion=readGLB(path.join(R,artifacts.motion,animation.name+'.glb')),m=motion.json;
 assert(!m.meshes?.length&&!m.images?.length&&!m.textures?.length,`Motion bundle contains geometry/texture: ${animation.name}`);
 assert.equal(m.animations?.length,1);assert.equal(m.animations[0].name,animation.name);
 assert.deepEqual(m.nodes,expectedNodes,`Wrong target hierarchy: ${animation.name}`);
 assert.deepEqual(m.animations[0].channels,animation.channels,`Wrong animation channels: ${animation.name}`);
 for(let k=0;k<animation.samplers.length;k++){
  const source=animation.samplers[k],copy=m.animations[0].samplers[k];
  assert.equal(copy.interpolation||'LINEAR',source.interpolation||'LINEAR');
  assert.deepEqual(accessor(motion,copy.input),accessor(g,source.input));
  assert.deepEqual(accessor(motion,copy.output),accessor(g,source.output));
 }
}
const actions=JSON.parse(fs.readFileSync(path.join(R,artifacts.review,'blender-actions.json')));
assert.equal(actions.actions,cat.length,'Blender action count differs from GLB');
let maxWeightError=0,maxQuaternionError=0,vertices=0,triangles=0;
for(let i=0;i<j.accessors.length;i++)assert(accessor(g,i).every(Number.isFinite),`Nonfinite accessor ${i}`);
for(const mesh of j.meshes)for(const p of mesh.primitives){
 vertices+=j.accessors[p.attributes.POSITION].count;triangles+=j.accessors[p.indices].count/3;
 const w=accessor(g,p.attributes.WEIGHTS_0),wa=j.accessors[p.attributes.WEIGHTS_0],div=wa.normalized?({5121:255,5123:65535}[wa.componentType]||1):1,ji=accessor(g,p.attributes.JOINTS_0);
 for(let i=0;i<w.length;i+=4){let sum=0;for(let k=0;k<4;k++){sum+=w[i+k]/div;assert(ji[i+k]<j.skins[0].joints.length);assert(w[i+k]>=0);}maxWeightError=Math.max(maxWeightError,Math.abs(1-sum));}
}
assert(maxWeightError<1e-4,'Unnormalized skin');
for(const a of j.animations)for(const c of a.channels){const s=a.samplers[c.sampler],t=accessor(g,s.input),v=accessor(g,s.output);for(let i=1;i<t.length;i++)assert(t[i]>t[i-1],`Non-increasing times: ${a.name}`);if(c.target.path==='rotation')for(let i=0;i<v.length;i+=4)maxQuaternionError=Math.max(maxQuaternionError,Math.abs(Math.hypot(...v.slice(i,i+4))-1));}
assert(maxQuaternionError<1e-5);
// Parse without textures in Node: geometry, inverse-bind matrices and animations are unchanged.
const parsed=structuredClone(j);delete parsed.images;delete parsed.textures;delete parsed.materials;for(const m of parsed.meshes)for(const p of m.primitives)delete p.material;
parsed.buffers=[{uri:'data:application/octet-stream;base64,'+g.bin.toString('base64'),byteLength:g.bin.length}];
globalThis.ProgressEvent??=class ProgressEvent{};
const gltf=await new GLTFLoader().parseAsync(JSON.stringify(parsed),''),mixer=new T.AnimationMixer(gltf.scene),meshes=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});
let sampledPoses=0,maxPoseSpan=0;const bounds=[];
for(const clip of gltf.animations){mixer.stopAllAction();const a=mixer.clipAction(clip).reset().play();let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
 for(const f of [0,.2,.4,.6,.8,.999]){
  const poseMin=[Infinity,Infinity,Infinity],poseMax=[-Infinity,-Infinity,-Infinity];
  a.time=clip.duration*f;mixer.update(0);gltf.scene.updateMatrixWorld(true);
  for(const m of meshes){m.skeleton.update();for(let i=0;i<m.geometry.attributes.position.count;i+=17){const v=m.getVertexPosition(i,new T.Vector3()).applyMatrix4(m.matrixWorld);assert(v.toArray().every(Number.isFinite),`Bad deformed vertex ${clip.name}`);v.toArray().forEach((n,k)=>{min[k]=Math.min(min[k],n);max[k]=Math.max(max[k],n);poseMin[k]=Math.min(poseMin[k],n);poseMax[k]=Math.max(poseMax[k],n);});}}
  // Root travel (including a source underground spawn) is not mesh explosion.
  const span=Math.max(...poseMax.map((n,k)=>n-poseMin[k]));
  assert(span<12,`Exploded posed mesh ${clip.name}`);maxPoseSpan=Math.max(maxPoseSpan,span);sampledPoses++;
 }
 bounds.push({name:clip.name,min,max});
}
const idle=cat.filter(c=>/Idle/.test(c.originalName)&&c.duration>.1),runs=cat.filter(c=>c.category==='Běh');assert(idle.length>=5);assert(runs.length>=5);
const topology=JSON.parse(fs.readFileSync(path.join(R,artifacts.review,'topology.json')));assert(topology.every(p=>p.boundaryEdges===0&&p.nonManifoldEdges===0));
const report={passed:true,character,clips:cat.length,motionOnlyFiles:cat.length,blenderActions:actions.actions,embeddedImages:j.images.length,bones:j.skins[0].joints.length,vertices,triangles,idleClips:idle.length,runClips:runs.length,sampledPoses,maxPoseSpan,maxWeightError,maxQuaternionError,maxIKError:Math.max(...cat.map(c=>c.maxIKError)),bounds,scope:'Numeric geometry/skin/animation and matching motion-only file checks; per-pose size is checked separately from root travel. Not a proof of absence of collisions or sliding.'};
fs.writeFileSync(reportPath,JSON.stringify(report,null,2));console.log(JSON.stringify({...report,bounds:undefined},null,2));
