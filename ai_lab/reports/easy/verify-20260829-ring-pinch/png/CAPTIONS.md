# PNG captions (visualization only — not physics data)

All heatmaps are mid-plane slices of `|ψ|` (amplitude) or `arg(ψ)` (phase), or a diagnostic polyline overlay.
`*_loops_xy.png` is the 3D tracer's closed loops projected to xy — not a physical field.
Official `official_display_*` frames are the Room's **20³ uint8 display lens** (interpolated_for_display), not the 64³ physics array.

A meridional (xz/yz) slice of **one** ring looks like **two dark dots**. That is not two rings.

## Official Room display only (not used for loop counts)

| file | what it shows |
|---|---|
| `official_display_t0_xy_density.png` | Display t=0. Undifferentiated. No ring placed. |
| `official_display_end_xy_density.png` | Display end. Several dark holes / a streak on a 20³ slice of a 64³ tangle. |
| `official_display_end_xz_density.png` | Same end, other cut. Still a tangle slice, not 1→2. |

## Grown TDGL 32³ seed=0（育った）

| file | what it shows |
|---|---|
| `grown_s0_t000_xy_amp.png` | t=0 white noise. No ring. |
| `grown_s0_end_xy_amp.png` | t=28. A few amplitude holes. Tracer: 0 bulk closed loops, 29 open paths, 76 xy-plaquette piercings. Line piercings, not two daughter rings. |
| `grown_s0_end_xz_amp.png` | Same end, xz. Dark holes on a slice. |

## Grown TDGL 32³ seed=1（育った）

| file | what it shows |
|---|---|
| `grown_s1_end_xy_amp.png` | **Colormap trap.** Physical amp is 0.981–~1 (no defects). Min–max stretch makes fake dark spots. |

## Placed circular ring TDGL 32³（置いた）

| file | what it shows |
|---|---|
| `placed_tdgl_ring_t000_xy_amp.png` | **Before.** One dark circle in the ring plane. |
| `placed_tdgl_ring_t000_xz_amp.png` | Same instant, meridional. Two dark dots = one ring piercing twice. |
| `placed_tdgl_ring_t000_loops_xy.png` | Tracer overlay: one closed loop. |
| `placed_tdgl_ring_s0053_xy_amp.png` | Mid. Still one circle, slightly smaller. |
| `placed_tdgl_ring_end_xy_amp.png` | **After.** Still one dark circle (R_eff 8.5→5.4). Not two rings. |
| `placed_tdgl_ring_end_xz_amp.png` | After, meridional. Extra dark pixels from wrap/coarse core; tracer still 1 loop. |

There is no pinch frame because no pinch was measured. Mid ≠ pinch.

## Placed circular ring GPE 32³（置いた, FFT shortcut）

| file | what it shows |
|---|---|
| `placed_gpe_ring_t000_xy_amp.png` | One dark circle. |
| `placed_gpe_ring_end_xy_amp.png` | Still one loop-scale dark ring; extra radial structure from sound / boundary sheet (e003 floor). Tracer: 1 bulk loop. |
