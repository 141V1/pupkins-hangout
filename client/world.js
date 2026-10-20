// The 3D world: three.js (the kit's own copy, through the page's import map) and Fountain Square, laid out in
// scenes/square.scene.json (open it in the scene editor: npm run edit). The scene has the sky, the sun, the square, the
// fountain, the benches, lamps and trees, and the game's camera; this file adds what moves: ripples on the water, the
// spout's bob, and the camera that follows you. Nothing here decides anything: main.js puts everyone where they are.
import * as THREE from 'three';
import { loadScene } from '@pupkins/create/scene';

export async function createWorld(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  container.appendChild(renderer.domElement);
  // the scene: its sky, sun and fill light, the square and everything on it, in our toon look
  const world = await loadScene('/scenes/square.scene.json', { renderer });
  const { scene, camera } = world;

  // the fountain's water: a ring spreading on it every so often, and the spout gently bobbing
  const water = world.get('water');
  const spout = world.get('spout');
  const spoutScale = spout?.scale.clone();
  const fountain = world.place('water');   // (where the water is in the square, in metres: null if it's gone)
  const ripples = [];
  const rippleGeometry = new THREE.RingGeometry(0.5, 0.62, 48);
  let rippleClock = 0;

  // the camera follows a point (you), from where the scene's game camera stands to look at where players come in
  const spawn = world.place('spawn');
  const focus = new THREE.Vector3(spawn.x, 0, spawn.z);
  const offset = camera.position.clone().sub(focus);                  // (from the point followed to the camera)
  const look = camera.userData.target.clone().sub(focus);             // (from the point followed to where it looks)
  function follow(x, z, dt) {
    const k = 1 - Math.exp(-6 * dt);
    focus.x += (x - focus.x) * k;
    focus.z += (z - focus.z) * k;
    camera.position.copy(focus).add(offset);
    camera.lookAt(focus.x + look.x, focus.y + look.y, focus.z + look.z);
    world.sunAt(focus.x, focus.z);   // (the sun follows the camera, so the shadows stay sharp wherever you walk)
  }

  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();

  const projected = new THREE.Vector3();
  return {
    scene, camera, renderer, follow,
    /** Where a point in metres lands on the canvas, in CSS pixels: { x, y } or null behind the camera. */
    project(x, y, z) {
      projected.set(x, y, z).project(camera);
      if (projected.z > 1) return null;
      return { x: (projected.x + 1) / 2 * container.clientWidth, y: (1 - projected.y) / 2 * container.clientHeight };
    },
    render(dt) {
      world.update(dt);
      rippleClock += dt;
      if (rippleClock > 0.7 && fountain && water?.visible) {   // a ring spreading on the water every so often
        rippleClock = 0;
        const mesh = new THREE.Mesh(rippleGeometry, new THREE.MeshBasicMaterial({ color: 0xe8f7ff, transparent: true, depthWrite: false }));
        mesh.rotation.x = -Math.PI / 2;
        mesh.position.set(fountain.x, fountain.y + 0.01, fountain.z);
        scene.add(mesh);
        ripples.push({ mesh, age: 0 });
      }
      for (let i = ripples.length - 1; i >= 0; i -= 1) {
        const r = ripples[i];
        r.age += dt;
        r.mesh.scale.setScalar(1 + r.age * 2.2);
        r.mesh.material.opacity = Math.max(0, 0.7 - r.age / 1.6);
        if (r.age > 1.1) { scene.remove(r.mesh); r.mesh.material.dispose(); ripples.splice(i, 1); }
      }
      const t = rippleClock * 9;
      spout?.scale.set(spoutScale.x * (1 + Math.sin(t) * 0.04), spoutScale.y * (1 + Math.sin(t + 1) * 0.07), spoutScale.z * (1 + Math.sin(t) * 0.04));
      renderer.render(scene, camera);
    },
  };
}
