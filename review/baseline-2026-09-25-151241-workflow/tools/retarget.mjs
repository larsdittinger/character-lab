/** Offline transfer of downloaded motion. World-space rest correction + 2-bone leg IK.
 * The input animation curves belong to the credited libraries. No sine-wave generated motion.
 */
import fs from 'node:fs';import path from 'node:path';import * as T from 'three';import {readGLB,accessor,appendAccessor,writeGLB} from './glb.mjs';
import {artifacts} from './character_paths.mjs';
const ROOT=path.resolve(import.meta.dirname,'..'),out=readGLB(path.join(ROOT,artifacts.rigged));
const Q=()=>new T.Quaternion(),V=()=>new T.Vector3();
function makeRig(g){const nodes=g.json.nodes.map(n=>{const o=new T.Object3D();o.name=n.name||'';if(n.matrix)o.applyMatrix4(new T.Matrix4().fromArray(n.matrix));else{o.position.fromArray(n.translation||[0,0,0]);o.quaternion.fromArray(n.rotation||[0,0,0,1]);o.scale.fromArray(n.scale||[1,1,1]);}return o;});g.json.nodes.forEach((n,i)=>(n.children||[]).forEach(c=>nodes[i].add(nodes[c])));const root=new T.Group();nodes.filter(o=>!o.parent).forEach(o=>root.add(o));root.updateMatrixWorld(true);const byName=new Map(nodes.map((o,i)=>[o.name,{o,i,p:o.position.clone(),q:o.quaternion.clone(),s:o.scale.clone(),wp:o.getWorldPosition(V()),wq:o.getWorldQuaternion(Q()),wm:o.matrixWorld.clone()}]));return{root,nodes,byName};}
const target=makeRig(out),boneIds=out.json.skins[0].joints,boneNames=boneIds.map(i=>out.json.nodes[i].name);const order=boneNames.toSorted((a,b)=>depth(target.byName.get(a).o)-depth(target.byName.get(b).o));function depth(o){let n=0;while(o.parent){n++;o=o.parent;}return n;}
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const allFiles=walk(path.join(ROOT,'animations/source'));
const files=allFiles.filter(p=>/UAL[12]_Standard\.glb$/.test(p)||/Rig_Medium_[^/]+\.glb$/.test(p));
const canonical=makeRig(readGLB(files.find(p=>p.endsWith('UAL1_Standard.glb'))));
const armCanonical=new Map();
for(const s of ['l','r'])for(const [n,next] of [['upperarm','lowerarm'],['lowerarm','hand'],['hand',null]]){
 const name=n+'_'+s,tb=target.byName.get(name),cb=canonical.byName.get(name);
 const td=next?target.byName.get(next+'_'+s).wp.clone().sub(tb.wp):tb.wp.clone().sub(target.byName.get('lowerarm_'+s).wp);
 const cd=next?canonical.byName.get(next+'_'+s).wp.clone().sub(cb.wp):cb.wp.clone().sub(canonical.byName.get('lowerarm_'+s).wp);
 armCanonical.set(name,Q().setFromUnitVectors(td.normalize(),cd.normalize()).multiply(tb.wq));
}
const kayMap={root:'root',pelvis:'hips',spine_01:'spine',spine_02:'chest',spine_03:'chest',neck_01:'chest',Head:'head'};
for(const s of ['l','r'])Object.assign(kayMap,{['clavicle_'+s]:'chest',['upperarm_'+s]:'upperarm.'+s,['lowerarm_'+s]:'lowerarm.'+s,['hand_'+s]:'wrist.'+s,['thigh_'+s]:'upperleg.'+s,['calf_'+s]:'lowerleg.'+s,['foot_'+s]:'foot.'+s,['ball_'+s]:'toes.'+s});
function reset(r){for(const b of r.byName.values()){b.o.position.copy(b.p);b.o.quaternion.copy(b.q);b.o.scale.copy(b.s);}r.root.updateMatrixWorld(true);}
function worldQ(name,q){const o=target.byName.get(name).o,p=o.parent.getWorldQuaternion(Q());o.quaternion.copy(p.invert().multiply(q)).normalize();o.updateMatrixWorld(true);}
function animation(g,a,rig){return a.channels.map(ch=>{const s=a.samplers[ch.sampler],times=accessor(g,s.input),values=accessor(g,s.output),n=ch.target.path==='rotation'?4:3;if(s.interpolation==='CUBICSPLINE')throw new Error('Cubic source requires explicit resampling');const ip=s.interpolation==='STEP'?new T.DiscreteInterpolant(times,values,n):ch.target.path==='rotation'?new T.QuaternionLinearInterpolant(times,values,n):new T.LinearInterpolant(times,values,n);return{ip,o:rig.nodes[ch.target.node],path:ch.target.path,duration:times[times.length-1]};});}
function sample(tracks,t,rig){for(const tr of tracks){const v=tr.ip.evaluate(t);if(tr.path==='rotation')tr.o.quaternion.fromArray(v).normalize();else if(tr.path==='translation')tr.o.position.fromArray(v);/* Keep rest scales: spawn/disassembly scale-to-zero effects are not humanoid joint motion. */}rig.root.updateMatrixWorld(true);}
function category(n){if(/Death|Hit|Knock/.test(n))return'Zásah a smrt';if(/Idle|Holding_[ABC]|_Pose$|Aiming|Blocking|Crouching/.test(n))return'Idle';if(/Run|Jog|Sprint/.test(n))return'Běh';if(/Jump|Fall|Climb|Roll|Dodge|Slide|Dash/.test(n))return'Skok a pohyb';if(/Walk|Crawl|Sneak|Swim/.test(n))return'Chůze';if(/Death|Hit|Knock/.test(n))return'Zásah a smrt';if(/Melee|Sword|Punch|Ranged|Pistol|Spell|Shield|Throw/.test(n))return'Boj';if(/Farm|Chop|Dig|Fish|Hammer|Pickax|Saw|Work|Lockpick/.test(n))return'Práce';return'Gesta a ostatní';}
function solveLeg(side,source,map,scale){const tn='thigh_'+side,cn='calf_'+side,fn='foot_'+side,th=target.byName.get(tn),ca=target.byName.get(cn),fo=target.byName.get(fn),sf=source.byName.get(map[fn]||fn),sk=source.byName.get(map[cn]||cn),sr=source.byName.get(map.root||'root');
 const sourceHip=source.byName.get(map[tn]||tn).o.getWorldPosition(V());
 // Hip-relative trajectories respect differing hip offsets and avoid overextending KayKit legs.
 function destination(sb,tb){return sb.o.getWorldPosition(V()).sub(sourceHip).multiplyScalar(scale).add(th.o.getWorldPosition(V()));}
 const ankle=destination(sf,fo),pole=destination(sk,ca),hip=th.o.getWorldPosition(V()),L1=th.wp.distanceTo(ca.wp),L2=ca.wp.distanceTo(fo.wp);const dir=ankle.clone().sub(hip),d=T.MathUtils.clamp(dir.length(),.0001,L1+L2-.00001);dir.normalize();let bend=pole.sub(hip);bend.addScaledVector(dir,-bend.dot(dir));if(bend.lengthSq()<1e-6)bend.set(0,0,1).addScaledVector(dir,-dir.z);bend.normalize();const c=T.MathUtils.clamp((L1*L1+d*d-L2*L2)/(2*L1*d),-1,1),knee=hip.clone().addScaledVector(dir,L1*c).addScaledVector(bend,L1*Math.sqrt(1-c*c));
 let from=ca.o.getWorldPosition(V()).sub(hip).normalize(),to=knee.clone().sub(hip).normalize();worldQ(tn,Q().setFromUnitVectors(from,to).multiply(th.o.getWorldQuaternion(Q())));
 const kneeNow=ca.o.getWorldPosition(V());from=fo.o.getWorldPosition(V()).sub(kneeNow).normalize();to=ankle.clone().sub(kneeNow).normalize();worldQ(cn,Q().setFromUnitVectors(from,to).multiply(ca.o.getWorldQuaternion(Q())));
 return fo.o.getWorldPosition(V()).distanceTo(ankle);
}
let catalog=[],errors=[],metrics={maxIKError:0,clips:0};out.json.animations=[];
for(const file of files){const g=readGLB(file),source=makeRig(g),kay=file.includes('kaykit'),map=kay?kayMap:{},pack=kay?'KayKit':file.includes('UAL2_')?'Quaternius 2':'Quaternius 1';const srcPelvis=source.byName.get(map.pelvis||'pelvis');const legLength=r=>r.byName.get(kay&&r===source?'upperleg.l':'thigh_l').wp.distanceTo(r.byName.get(kay&&r===source?'lowerleg.l':'calf_l').wp)+r.byName.get(kay&&r===source?'lowerleg.l':'calf_l').wp.distanceTo(r.byName.get(kay&&r===source?'foot.l':'foot_l').wp);const scale=legLength(target)/legLength(source);
 for(const a of g.json.animations||[]){if(/^(A_TPose|T-Pose)$/.test(a.name))continue;if(a.name==='EXPERIMENTAL_Medium_Transform')continue;
  reset(source);reset(target);const tracks=animation(g,a,source),duration=Math.max(1/30,...tracks.map(t=>t.duration)),frames=Math.max(2,Math.round(duration*30)+1),times=Array.from({length:frames},(_,i)=>i*duration/(frames-1)),rotations=Object.fromEntries(boneNames.map(n=>[n,[]])),positions={root:[],pelvis:[]};let clipIK=0;
  for(const t of times){sample(tracks,t,source);reset(target);
   for(const n of order){if(n.startsWith('cloth_'))continue;const tb=target.byName.get(n),sb=source.byName.get(map[n]||n);if(!sb)continue;
    const delta=sb.o.getWorldQuaternion(Q()).multiply(sb.wq.clone().invert()),rest=armCanonical.get(n)||tb.wq;worldQ(n,delta.multiply(rest.clone()));
    if(n==='root'||n==='pelvis'){
     const localDelta=sb.o.position.clone().sub(sb.p),parSource=sb.o.parent.getWorldQuaternion(Q()),parTarget=tb.o.parent.getWorldQuaternion(Q());localDelta.applyQuaternion(parSource).multiplyScalar(scale).applyQuaternion(parTarget.invert());tb.o.position.copy(tb.p).add(localDelta);tb.o.updateMatrixWorld(true);
    }
   }
   // Feet keep the source trajectories under the knight's limb lengths. Preserve source jump height.
   const footQ=Object.fromEntries(['l','r'].map(s=>[s,target.byName.get('foot_'+s).o.getWorldQuaternion(Q())]));
   for(const s of ['l','r']){clipIK=Math.max(clipIK,solveLeg(s,source,map,scale));worldQ('foot_'+s,footQ[s]);}
   const pel=target.byName.get('pelvis'),dp=pel.o.getWorldQuaternion(Q()).multiply(pel.wq.clone().invert());
   for(const n of order.filter(n=>n.startsWith('cloth_'))){const s=n.endsWith('_l')?'l':'r',th=target.byName.get('thigh_'+s),dt=th.o.getWorldQuaternion(Q()).multiply(th.wq.clone().invert()),relative=dp.clone().invert().multiply(dt);const reduced=Q().slerp(relative,.65),q=dp.clone().multiply(reduced).multiply(target.byName.get(n).wq);worldQ(n,q);}
   for(const n of boneNames){const q=target.byName.get(n).o.quaternion.clone().normalize(),arr=rotations[n];if(!q.toArray().every(Number.isFinite))throw Error(`Invalid rotation ${a.name} ${n} ${t}`);if(arr.length&&q.dot(new T.Quaternion(...arr.slice(-4)))<0){q.x*=-1;q.y*=-1;q.z*=-1;q.w*=-1;}arr.push(q.x,q.y,q.z,q.w);if(positions[n])positions[n].push(...target.byName.get(n).o.position.toArray());}
  }
  const name=(kay?'KAY_':pack==='Quaternius 2'?'UAL2_':'UAL1_')+a.name,samplers=[],channels=[],input=appendAccessor(out,times,'SCALAR');
  for(const n of boneNames){const idx=target.byName.get(n).i,output=appendAccessor(out,rotations[n],'VEC4');channels.push({sampler:samplers.length,target:{node:idx,path:'rotation'}});samplers.push({input,output,interpolation:'LINEAR'});if(positions[n]){channels.push({sampler:samplers.length,target:{node:idx,path:'translation'}});samplers.push({input,output:appendAccessor(out,positions[n],'VEC3'),interpolation:'LINEAR'});}}
  out.json.animations.push({name,samplers,channels,extras:{source:pack,originalName:a.name,license:'CC0-1.0'}});catalog.push({name,originalName:a.name,pack,category:category(a.name),duration,frames,source:path.relative(ROOT,file),loop:/Loop|Idle|Running|Walking|Crawling|Sneaking|Crouching|Blocking|Fishing_|Chopping|Digging|Hammering|Pickaxing|Sawing|Working/.test(a.name),maxIKError:clipIK});metrics.maxIKError=Math.max(metrics.maxIKError,clipIK);metrics.clips++;
 }
 console.log('RETARGETED',pack,path.basename(file));
}
writeGLB(out,path.join(ROOT,artifacts.animated));fs.mkdirSync(path.dirname(path.join(ROOT,artifacts.catalog)),{recursive:true});fs.mkdirSync(path.join(ROOT,artifacts.review),{recursive:true});fs.writeFileSync(path.join(ROOT,artifacts.catalog),JSON.stringify(catalog,null,2));fs.writeFileSync(path.join(ROOT,artifacts.review,'retarget.json'),JSON.stringify(metrics,null,2));console.log('RETARGET COMPLETE',metrics,'GLB',fs.statSync(path.join(ROOT,artifacts.animated)).size);
