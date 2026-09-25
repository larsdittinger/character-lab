import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const $ = selector => document.querySelector(selector);
let characters = {};

const scene = new T.Scene();
scene.background = new T.Color('#25282c');
const renderer = new T.WebGLRenderer({canvas: $('canvas'), antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = T.SRGBColorSpace;
renderer.toneMapping = T.NeutralToneMapping;
renderer.toneMappingExposure = 1.10;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = T.PCFSoftShadowMap;
scene.add(new T.HemisphereLight('#f1eee0', '#6c7e75', 2));
const light = new T.DirectionalLight('#ffead0', 2.4);
light.position.set(-3, 6, 5);
light.castShadow = true;
light.shadow.mapSize.set(2048, 2048);
Object.assign(light.shadow.camera, {left: -3, right: 3, top: 4, bottom: -3, near: .1, far: 15});
light.shadow.normalBias = .012;
scene.add(light);
const rim = new T.DirectionalLight('#b7ded7', 1.7);
rim.position.set(3, 4, -4);
scene.add(rim);
const platform = new T.Mesh(new T.CylinderGeometry(1.12, 1.16, .07, 96), new T.MeshStandardMaterial({color: '#3a3e43', roughness: .9}));
platform.position.y = -.045;
platform.receiveShadow = true;
scene.add(platform);
const floor = new T.Mesh(new T.PlaneGeometry(100, 100), new T.MeshStandardMaterial({color: '#25282c', roughness: 1}));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -.09;
floor.receiveShadow = true;
scene.add(floor);

const persp = new T.PerspectiveCamera(32, 1, .01, 100);
const ortho = new T.OrthographicCamera(-1, 1, 1, -1, .01, 100);
let camera = persp;
const controls = new OrbitControls(camera, $('canvas'));
controls.enableDamping = true;
controls.minDistance = .2;
controls.maxDistance = 15;
const loader = new GLTFLoader();
const originalMaterials = new Map();
const clayMat = new T.MeshStandardMaterial({color: '#c8c3b0', roughness: .8});
const beforeModels = new Map();
let model, mixer, skeleton, action, current, clips = [], catalog = [];
let paused = false, bind = false, clay = false, speed = 1, view = '3q';
let characterId = 'knight', comparison = 'current', ready = false;
let modelRequest = 0, comparisonRequest = 0;
let bounds = new T.Box3(new T.Vector3(-1, 0, -.4), new T.Vector3(1, 2.5, .4));
let headHeight = .44;

function stats(root = model) {
  let triangles = 0, vertices = 0;
  const bones = new Set();
  root?.traverse(object => {
    if (!object.isMesh) return;
    triangles += (object.geometry.index?.count || object.geometry.attributes.position.count) / 3;
    vertices += object.geometry.attributes.position.count;
    object.skeleton?.bones.forEach(bone => bones.add(bone.uuid));
  });
  return {triangles, vertices, bones: bones.size, clips: root === model ? clips.length : 0};
}
function visibleModel() { return comparison === 'current' ? model : beforeModels.get(comparison); }
function updateStats() {
  const count = stats(visibleModel());
  $('#tris').textContent = count.triangles.toLocaleString('en-US');
  $('#bones').textContent = count.bones;
  $('#summary').textContent = count.clips
    ? `${count.clips} clips · ${count.bones} bones`
    : `${count.triangles.toLocaleString('en-US')} triangles · static ${comparison === 'current' ? 'model' : 'export'}`;
  $('#rig-note').textContent = count.clips ? 'Retargeted animation / adapted proportions' : 'Calibrated geometry / projected texture';
}
function updateControls() {
  const animated = ready && clips.length > 0;
  const playable = animated && comparison === 'current';
  for (const id of ['play', 'restart', 'timeline', 'speed', 'loop', 'bind']) $('#' + id).disabled = !playable;
  for (const id of ['search', 'category']) $('#' + id).disabled = !animated;
  for (const id of ['camera', 'clay']) $('#' + id).disabled = !ready;
  $('#skeleton').disabled = !ready || !skeleton?.bones.length || comparison !== 'current';
  $('#comparison').disabled = !ready || !Object.keys(characters[characterId]?.comparisons || {}).length;
  $('#play').textContent = paused || !playable ? '▶' : 'Ⅱ';
  $('#play').setAttribute('aria-label', paused || !playable ? 'Play' : 'Pause');
}
function framing() {
  const size = bounds.getSize(new T.Vector3());
  const face = view.startsWith('face');
  const aspect = Math.max(.1, $('#stage').clientWidth / $('#stage').clientHeight);
  return face ? Math.max(headHeight * 1.28, headHeight * 1.05 / aspect)
    : Math.max(size.y * 1.26, (view === 'side' ? size.z : size.x) * 1.25 / aspect);
}
function resize() {
  const width = $('#stage').clientWidth, height = $('#stage').clientHeight;
  renderer.setSize(width, height, false);
  persp.aspect = width / height;
  persp.updateProjectionMatrix();
  const span = framing();
  ortho.left = -span * width / height / 2;
  ortho.right = span * width / height / 2;
  ortho.top = span / 2;
  ortho.bottom = -span / 2;
  ortho.updateProjectionMatrix();
}
function setCamera(next) {
  view = next;
  const face = view.startsWith('face');
  const front = view.endsWith('front'), side = view.endsWith('side');
  camera = front || side || view === 'back' ? ortho : persp;
  controls.object = camera;
  const center = bounds.getCenter(new T.Vector3());
  const target = face ? (characters[characterId]?.face ? new T.Vector3(...characters[characterId].face) : new T.Vector3(center.x, bounds.max.y - headHeight * .48, center.z)) : center;
  const direction = front ? [0, 0, 1] : side ? [1, 0, 0] : view === 'back' ? [0, 0, -1] : [.80, .19, 1];
  const distance = framing() / (2 * Math.tan(T.MathUtils.degToRad(persp.fov / 2))) * (face ? 1.2 : 1.12);
  camera.position.copy(target).add(new T.Vector3(...direction).normalize().multiplyScalar(distance));
  controls.target.copy(target);
  camera.lookAt(target);
  // Flush orbit damping so a camera preset does not drift after a drag.
  controls.enableDamping = false;
  controls.update();
  controls.enableDamping = true;
  $('#camera').value = view;
  resize();
}
const preferred = ['UAL1_Idle_Loop', 'KAY_Idle_A', 'KAY_Idle_B', 'UAL1_Idle_Talking_Loop', 'UAL2_Idle_FoldArms_Loop', 'UAL1_Jog_Fwd_Loop', 'UAL1_Sprint_Loop', 'KAY_Running_A', 'KAY_Running_B', 'KAY_Jump_Full_Short'];
function list() {
  const text = $('#search').value.toLowerCase(), category = $('#category').value;
  const found = catalog.filter(clip => (category === 'all' || clip.category === category) && (clip.originalName + ' ' + clip.pack).toLowerCase().includes(text))
    .sort((a, b) => (preferred.includes(a.name) ? preferred.indexOf(a.name) : 999) - (preferred.includes(b.name) ? preferred.indexOf(b.name) : 999));
  $('#count').textContent = found.length;
  const buttons = found.map(clip => {
    const button = document.createElement('button');
    button.className = 'clip' + (current?.name === clip.name ? ' active' : '');
    button.dataset.clip = clip.name;
    const title = document.createElement('strong');
    title.textContent = clip.originalName.replaceAll('_', ' ');
    const detail = document.createElement('small');
    detail.textContent = `${clip.pack} · ${clip.duration.toFixed(2)} s · ${clip.category}`;
    button.append(title, detail);
    button.onclick = () => play(clip.name);
    return button;
  });
  if (!buttons.length) {
    const empty = document.createElement('p');
    empty.className = 'library-empty';
    empty.textContent = clips.length ? 'No animations match this search.' : 'Static model. Use the camera presets and Clay view to inspect its shape and texture.';
    buttons.push(empty);
  }
  $('#clips').replaceChildren(...buttons);
}
function currentView() {
  ++comparisonRequest;
  comparison = 'current';
  $('#comparison').value = comparison;
  beforeModels.forEach(root => root.visible = false);
  if (model) model.visible = true;
  updateStats();
  updateControls();
}
function play(name) {
  const next = clips.find(clip => clip.name === name);
  if (!next || !ready) return;
  currentView();
  bind = false;
  $('#bind').classList.remove('active');
  const old = action;
  action = mixer.clipAction(next);
  action.reset().setEffectiveTimeScale(1).setEffectiveWeight(1);
  action.setLoop($('#loop').checked ? T.LoopRepeat : T.LoopOnce, Infinity);
  action.clampWhenFinished = true;
  action.play();
  if (old && old !== action && old.isRunning()) action.crossFadeFrom(old, .18, false);
  current = catalog.find(clip => clip.name === name);
  paused = false;
  $('#status').textContent = 'Library motion / adapted proportions';
  $('#clip-title').textContent = current.originalName.replaceAll('_', ' ') + ' / ' + current.pack;
  $('#duration').textContent = current.duration.toFixed(2) + ' s';
  updateControls();
  list();
}
function rest() {
  if (!model) return;
  mixer?.stopAllAction();
  model.traverse(object => { if (object.isSkinnedMesh) object.skeleton.pose(); });
  model.updateMatrixWorld(true);
  bind = true;
  paused = true;
  action = undefined;
  $('#bind').classList.add('active');
  $('#clip-title').textContent = clips.length ? 'Rest A-pose / fitted skeleton' : 'Static model / reference reconstruction';
  $('#status').textContent = 'Drag to orbit · scroll to zoom';
  $('#duration').textContent = '—';
  $('#timeline').value = 0;
  $('#time').textContent = '0.00 s';
  updateControls();
}
function appearance() {
  for (const root of [model, ...beforeModels.values()]) root?.traverse(object => {
    if (object.isMesh) object.material = clay ? clayMat : originalMaterials.get(object);
  });
  $('#clay').classList.toggle('active', clay);
}
function setup(root) {
  root.traverse(object => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
    object.frustumCulled = false;
    originalMaterials.set(object, object.material);
  });
}
function dispose(root) {
  if (!root) return;
  scene.remove(root);
  const geometries = new Set(), materials = new Set(), textures = new Set(), skins = new Set();
  root.traverse(object => {
    if (!object.isMesh) return;
    geometries.add(object.geometry);
    if (object.skeleton) skins.add(object.skeleton);
    const material = originalMaterials.get(object) || object.material;
    for (const entry of Array.isArray(material) ? material : [material]) {
      if (entry === clayMat) continue;
      materials.add(entry);
      Object.values(entry).forEach(value => { if (value?.isTexture) textures.add(value); });
    }
    originalMaterials.delete(object);
  });
  geometries.forEach(geometry => geometry.dispose());
  skins.forEach(skin => skin.dispose());
  materials.forEach(material => material.dispose());
  textures.forEach(texture => { texture.source?.data?.close?.(); texture.dispose(); });
}
async function compare(key) {
  const definition = characters[characterId].comparisons[key];
  if (!ready || (key !== 'current' && !definition)) return;
  if (key === 'current') {
    currentView();
    $('#status').textContent = 'Current projection / same camera';
    $('#clip-title').textContent = 'Rest A-pose / current model';
    return;
  }
  const request = ++comparisonRequest, modelVersion = modelRequest;
  rest();
  $('#status').textContent = 'Loading comparison…';
  try {
    if (!beforeModels.has(key)) {
      const gltf = await loader.loadAsync(definition.path + '?v=' + encodeURIComponent(characters[characterId].revision));
      if (request !== comparisonRequest || modelVersion !== modelRequest) { dispose(gltf.scene); return; }
      setup(gltf.scene);
      beforeModels.set(key, gltf.scene);
      scene.add(gltf.scene);
    }
    if (request !== comparisonRequest) return;
    comparison = key;
    $('#comparison').value = key;
    model.visible = false;
    beforeModels.forEach((root, id) => root.visible = id === key);
    skeleton.visible = false;
    $('#skeleton').classList.remove('active');
    $('#status').textContent = definition.title + ' / same camera';
    $('#clip-title').textContent = definition.title + ' / rest A-pose';
    appearance();
    updateStats();
    updateControls();
  } catch (error) {
    if (request !== comparisonRequest || modelVersion !== modelRequest) return;
    currentView();
    $('#status').textContent = 'Could not load comparison: ' + error.message;
    console.error(error);
  }
}
async function loadCharacter(id) {
  if (!characters[id]) return;
  const request = ++modelRequest;
  ++comparisonRequest;
  ready = false;
  characterId = id;
  comparison = 'current';
  paused = true;
  action = current = undefined;
  clips = catalog = [];
  $('#character').value = id;
  $('#loading').style.display = 'grid';
  $('#loading').textContent = 'Loading character…';
  $('#clips').replaceChildren();
  $('#count').textContent = '—';
  $('#summary').textContent = 'Loading model…';
  const definition = characters[id];
  $('#model-title').textContent = definition.title;
  $('.reference-card').hidden = !definition.reference;
  if (definition.reference) $('#reference-image').src = definition.reference;
  else $('#reference-image').removeAttribute('src');
  $('#reference-image').alt = 'Reference views: ' + definition.title;
  if (definition.reference) $('#reference-link').href = definition.reference;
  $('#download-glb').href = definition.path;
  $('#download-blend').hidden = !definition.blend;
  if (definition.blend) $('#download-blend').href = definition.blend;
  else $('#download-blend').removeAttribute('href');
  $('#catalog-link').hidden = !definition.catalog;
  if (definition.catalog) $('#catalog-link').href = definition.catalog;
  else $('#catalog-link').removeAttribute('href');
  $('#comparison').replaceChildren(...[['current', 'Current model'], ...Object.entries(definition.comparisons).map(([key, value]) => [key, value.title])].map(([value, title]) => new Option(title, value)));
  updateControls();
  mixer?.stopAllAction();
  if (mixer && model) mixer.uncacheRoot(model);
  mixer = undefined;
  dispose(model);
  model = undefined;
  beforeModels.forEach(dispose);
  beforeModels.clear();
  if (skeleton) {
    scene.remove(skeleton);
    skeleton.geometry.dispose();
    skeleton.material.dispose();
    skeleton = undefined;
  }
  $('#skeleton').classList.remove('active');
  delete window.characterLab.error;
  let gltf;
  try {
    gltf = await loader.loadAsync(definition.path + '?v=' + encodeURIComponent(definition.revision));
    if (request !== modelRequest) { dispose(gltf.scene); return; }
    let entries = [];
    if (gltf.animations.length && definition.catalog) {
      const response = await fetch(definition.catalog, {cache: 'no-store'});
      if (!response.ok) throw new Error('Animation catalog: HTTP ' + response.status);
      entries = await response.json();
    }
    if (request !== modelRequest) { dispose(gltf.scene); return; }
    model = gltf.scene;
    clips = gltf.animations;
    catalog = clips.map(clip => {
      const entry = entries.find(item => item.name === clip.name);
      return {...(entry || {name: clip.name, originalName: clip.name, category: 'Other', pack: 'GLB'}), duration: clip.duration};
    });
    setup(model);
    scene.add(model);
    model.updateMatrixWorld(true);
    bounds = new T.Box3().setFromObject(model, true);
    headHeight = bounds.getSize(new T.Vector3()).y * .175;
    mixer = new T.AnimationMixer(model);
    skeleton = new T.SkeletonHelper(model);
    skeleton.material.depthTest = false;
    skeleton.renderOrder = 5;
    skeleton.visible = false;
    scene.add(skeleton);
    mixer.addEventListener('finished', () => { paused = true; updateControls(); });
    ready = true;
    $('#timeline').value = 0;
    $('#time').textContent = '0.00 s';
    $('#loading').style.display = 'none';
    $('#search').value = '';
    $('#category').value = 'all';
    $('#library-note').textContent = clips.length ? (entries.length ? 'Animations for the selected skeleton' : 'Animations embedded in the GLB') : 'Static model without animations';
    const categories = [...new Set(catalog.map(clip => clip.category))];
    $('#category').replaceChildren(new Option('All categories', 'all'), ...categories.map(category => new Option(category, category)));
    $('#animation-links').hidden = !clips.length;
    $('#sources-link').hidden = !entries.length || !entries.every(entry => ['KayKit', 'Quaternius 1', 'Quaternius 2'].includes(entry.pack));
    $('#download-glb').textContent = clips.length ? 'Animated GLB ↓' : 'Static GLB ↓';
    $('#face-review').hidden = id !== 'knight';
    updateStats();
    appearance();
    setCamera(view);
    if (clips.length) play(clips.find(clip => clip.name === 'UAL1_Idle_Loop')?.name || clips[0].name);
    else { rest(); list(); }
    updateControls();
  } catch (error) {
    if (request !== modelRequest) { if (gltf) dispose(gltf.scene); return; }
    if (gltf && model !== gltf.scene) dispose(gltf.scene);
    $('#loading').textContent = 'Loading failed: ' + error.message;
    window.characterLab.error = error.message;
    console.error(error);
  }
}

$('#character').onchange = event => loadCharacter(event.target.value);
$('#search').oninput = list;
$('#category').onchange = list;
$('#camera').onchange = event => setCamera(event.target.value);
$('#comparison').onchange = event => compare(event.target.value);
$('#play').onclick = () => {
  if (bind) { play(current?.name || clips[0]?.name); return; }
  paused = !paused;
  if (!paused && action?.paused) { action.reset().play(); }
  updateControls();
};
$('#restart').onclick = () => { if (action) { action.reset().play(); mixer.update(0); } };
$('#speed').onchange = event => speed = +event.target.value;
$('#loop').onchange = () => { if (action) action.setLoop($('#loop').checked ? T.LoopRepeat : T.LoopOnce, Infinity); };
$('#timeline').oninput = event => {
  if (!action) return;
  paused = true;
  action.time = +event.target.value * current.duration;
  mixer.update(0);
  updateControls();
};
$('#skeleton').onclick = () => {
  if (!skeleton) return;
  skeleton.visible = !skeleton.visible;
  $('#skeleton').classList.toggle('active', skeleton.visible);
};
$('#clay').onclick = () => { clay = !clay; appearance(); };
$('#bind').onclick = () => bind ? play(current?.name || clips[0]?.name) : rest();
window.addEventListener('resize', resize);
let last = performance.now();
function frame(now) {
  requestAnimationFrame(frame);
  const delta = Math.min((now - last) / 1000, .05);
  last = now;
  controls.update();
  if (mixer && !paused && !bind) mixer.update(delta * speed);
  if (action) {
    $('#timeline').value = action.time / (current?.duration || 1);
    $('#time').textContent = action.time.toFixed(2) + ' s';
  }
  renderer.render(scene, camera);
}
window.characterLab = {
  get ready() { return ready; },
  scene, renderer, setCamera, play, rest, compare, loadCharacter,
  stats: () => stats(visibleModel()),
  setTime: time => {
    if (!mixer || !current || !clips.length) return;
    if (comparison !== 'current') currentView();
    bind = false;
    paused = true;
    mixer.stopAllAction();
    action = mixer.clipAction(clips.find(clip => clip.name === current.name)).reset().play();
    action.time = time;
    mixer.update(0);
    $('#bind').classList.remove('active');
    updateControls();
  },
  get model() { return model; }, get mixer() { return mixer; },
  get current() { return current; }, get catalog() { return catalog; },
  get character() { return characterId; }, get comparison() { return comparison; },
};
updateControls();
setCamera('3q');
requestAnimationFrame(frame);
let registryRequest = false;
async function refreshCharacters(initial = false) {
  if (registryRequest) return;
  registryRequest = true;
  try {
    const response = await fetch('/api/characters', {cache: 'no-store'});
    if (!response.ok) throw new Error('Character list: HTTP ' + response.status);
    const data = await response.json();
    const previous = characters[characterId];
    characters = data.characters;
    const ids = Object.keys(characters);
    const choices = ids.map(id => [id, characters[id].title]);
    const existing = [...$('#character').options].map(option => [option.value, option.text]);
    if (JSON.stringify(choices) !== JSON.stringify(existing)) $('#character').replaceChildren(...choices.map(([id, title]) => new Option(title, id)));
    $('#character').value = characterId;
    $('#character').disabled = !ids.length;
    $('#registry-status').textContent = data.warnings.length ? data.warnings.join(' · ') : `${ids.length} characters`;
    if (initial || !characters[characterId]) {
      if (ids.length) await loadCharacter(characters.knight ? 'knight' : ids[0]);
      else { ready = false; paused = true; $('#loading').style.display = 'grid'; $('#loading').textContent = 'No models available.'; updateControls(); }
    } else if (ready && JSON.stringify(previous) !== JSON.stringify(characters[characterId])) {
      await loadCharacter(characterId);
    }
  } catch (error) {
    $('#registry-status').textContent = error.message;
    if (initial) { $('#loading').textContent = error.message + ' — start npm run serve.'; console.error(error); }
  } finally { registryRequest = false; }
}
$('#refresh-characters').onclick = () => refreshCharacters();
await refreshCharacters(true);
setInterval(() => { if (!document.hidden) refreshCharacters(); }, 5000);
