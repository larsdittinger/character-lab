import fs from 'node:fs';
export function readGLB(path){const b=fs.readFileSync(path);let json,bin;for(let p=12;p<b.length;){let n=b.readUInt32LE(p),t=b.readUInt32LE(p+4);if(t===0x4e4f534a)json=JSON.parse(b.subarray(p+8,p+8+n));if(t===0x004e4942)bin=b.subarray(p+8,p+8+n);p+=8+n;}return{json,bin};}
export function accessor(g,i){materialize(g);const a=g.json.accessors[i],v=g.json.bufferViews[a.bufferView],nc={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type],size={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a.componentType],reader={5120:'readInt8',5121:'readUInt8',5122:'readInt16LE',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType],stride=v.byteStride||nc*size,start=(a.byteOffset||0)+(v.byteOffset||0),out=new Float32Array(a.count*nc);for(let k=0;k<a.count;k++)for(let c=0;c<nc;c++)out[k*nc+c]=g.bin[reader](start+k*stride+c*size);return out;}
// Accumulate binary chunks instead of copying the growing atlas/animation buffer
// for every channel. Materialize once at write/read; output bytes are identical.
const pending = new WeakMap();
function materialize(g) {
 const state=pending.get(g);
 if(state){g.bin=Buffer.concat(state.chunks,state.length);pending.delete(g);}
 return g.bin;
}
export function appendAccessor(g,values,type){
 let state=pending.get(g);
 if(!state){state={chunks:[g.bin],length:g.bin.length};pending.set(g,state);}
 const data=new Float32Array(values),padding=(4-state.length%4)%4,offset=state.length+padding,b=Buffer.from(data.buffer);
 if(padding)state.chunks.push(Buffer.alloc(padding));
 state.chunks.push(b);state.length=offset+b.length;const view=g.json.bufferViews.length;g.json.bufferViews.push({buffer:0,byteOffset:offset,byteLength:b.length});const nc={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[type],a={bufferView:view,componentType:5126,count:data.length/nc,type};if(type==='SCALAR'){a.min=[Math.min(...data)];a.max=[Math.max(...data)];}g.json.accessors.push(a);return g.json.accessors.length-1;}
export function writeGLB(g,path){materialize(g);g.json.buffers=[{byteLength:g.bin.length}];let j=Buffer.from(JSON.stringify(g.json));j=Buffer.concat([j,Buffer.alloc((4-j.length%4)%4,32)]);const b=Buffer.concat([g.bin,Buffer.alloc((4-g.bin.length%4)%4)]),out=Buffer.alloc(12+8+j.length+8+b.length);out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(j.length,12);out.writeUInt32LE(0x4e4f534a,16);j.copy(out,20);let at=20+j.length;out.writeUInt32LE(b.length,at);out.writeUInt32LE(0x004e4942,at+4);b.copy(out,at+8);fs.writeFileSync(path,out);}
