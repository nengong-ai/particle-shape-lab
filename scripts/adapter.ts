// Optional bridge to a user-provided engine. This file contains no renderer implementation.
import { createAstraScene, ASTRA_SHAPE_SVGS } from './particles/engine';
import shapeData from '../input/shape.json';
import './screen.css';

const shape = shapeData.geometry;
Object.assign(ASTRA_SHAPE_SVGS, { 'user-shape': shape });
const root = document.getElementById('root')!;
root.innerHTML = `<div data-astra-experience>
  <div class="backdrop" data-astra-backdrop><canvas aria-hidden="true"></canvas></div>
  <main data-astra-content><section data-astra-hero>
    <div class="target" data-astra-path-shape="user-shape" data-astra-scroll-cue="true"></div>
    <button class="drag" data-astra-drag aria-label="Drag or use arrow keys to rotate"></button>
  </section></main>
  <header><h1></h1><span>Drag to rotate · R replay · H hide · Esc restore</span></header>
  <footer><button id="replay">Replay</button><button id="hide">Hide controls</button></footer>
  <button id="restore" aria-label="Show controls">Show controls</button>
  <p id="status" role="status">Preparing particles…</p>
</div>`;
root.querySelector('h1')!.textContent = shape.label;
const ns = 'http://www.w3.org/2000/svg';
const svg = document.createElementNS(ns, 'svg');
svg.setAttribute('viewBox', shape.viewBox);
svg.setAttribute('fill', 'white');
svg.setAttribute('aria-hidden', 'true');
svg.dataset.filled = 'true';
shape.paths.forEach((d, i) => {
  const path = document.createElementNS(ns, 'path');
  path.setAttribute('d', d);
  path.setAttribute('fill-rule', shape.fillRules[i]);
  svg.append(path);
});
root.querySelector('.target')!.append(svg);
const host = root.firstElementChild as HTMLElement;
const canvas = root.querySelector('canvas')!;
let activeScenes = 1;
const scene = createAstraScene(canvas, {
  heroElement: root.querySelector('[data-astra-hero]') as HTMLElement,
  contentElement: root.querySelector('main')!,
  cues: [root.querySelector('.target') as HTMLElement],
  // A measured cue enables the existing path rotation without changing engine code.
  data: { engine: { bloomIntensity: 0.7, bloomThreshold: 0.08, pathShapeScatter: 0.12,
    stars: { intensity: 1.35, flowSpeed: 0.55 }, lensFlare: { intensity: 0.28 } } },
  onError(error) {
    console.error(error);
    const status = root.querySelector('#status') as HTMLElement;
    status.textContent = 'The external renderer could not start. Check its requirements.';
    status.hidden = false;
    host.dataset.scene = 'error';
  },
});
scene.ready.then(() => {
  if (host.dataset.scene === 'error') return;
  host.dataset.scene = 'ready';
  host.dataset.activeScenes = String(activeScenes);
  (root.querySelector('#status') as HTMLElement).hidden = true;
}).catch(error => console.error(error));
function hidden(value: boolean) { host.dataset.hidden = String(value); }
root.querySelector('#replay')!.addEventListener('click', () => scene.replay());
root.querySelector('#hide')!.addEventListener('click', () => hidden(true));
root.querySelector('#restore')!.addEventListener('click', () => hidden(false));
window.addEventListener('keydown', event => {
  if (event.ctrlKey || event.metaKey || event.altKey || event.repeat) return;
  if (event.key.toLowerCase() === 'r') scene.replay();
  if (event.key.toLowerCase() === 'h') hidden(host.dataset.hidden !== 'true');
  if (event.key === 'Escape') hidden(false);
});
window.addEventListener('pagehide', () => { scene.dispose(); activeScenes = 0; host.dataset.activeScenes = '0'; }, { once: true });
