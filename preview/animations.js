// v6: idles on track 0, FX loops from your art on tracks 1-2 (FX never move the body).
window.ANIM_SPEC = {
  title: 'Thor',
  idle: 'idle_breath',
  placement: { landscape: { x: 560, y: 1030, scale: 0.55, flip: false }, portrait: { x: 540, y: 1780, scale: 0.85, flip: false } },
  groups: [
    { group: 'Idle · track 0', items: [
      { name: 'idle_breath', track: 0, trigger: 'No spin running', what: 'Breathing, head/neck follow, hammer weight on the exhale. Cape flag wave + physics. Free fist arm follow-through. Blink at 2.6s', priority: 'P1', loop: true },
      { name: 'idle_look', track: 0, trigger: 'Idle variant A', what: 'Head tilts further up, jaw sets, hold, ease back. Cape wave, free arm. Blinks at 0.6s + 3.5s', priority: 'P2', loop: true },
      { name: 'idle_grip', track: 0, trigger: 'Idle variant B', what: 'Grip squeeze, hammer lifts 6° with overshoot. Cape wave, free arm. Blink at 3.0s. Event sfx_grip', priority: 'P2', loop: true },
    ]},
    { group: 'FX layers (character does not move)', items: [
      { name: 'fx_hammer', track: 1, trigger: 'Layer · track 1 · on at start', what: 'Energy dome + rising arcs from your hammer GIF (22 frames @ 20 fps), pivot on the hammer head emblem', priority: 'P1', loop: true, auto: true },
      { name: 'fx_eyes', track: 2, trigger: 'Layer · track 2 · on at start', what: 'Eye burst from your eye GIF (one cycle: bolt → star → smoke + sparks, 20 frames @ 25 fps) on both eyes, far eye 0.04 s later and smaller; 2.4 s loop', priority: 'P1', loop: true, auto: true },
    ]},
  ],
};
