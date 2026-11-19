"""R層 (Relational layer) -- a self-contained lane, parallel to the complex-field TDGL/GL

lane in genesis/ and ai_lab/lab.py, that starts from *only* nodes, a relation graph, and a
real-valued per-node state (no coordinates, no complex numbers, no phase, no S^1) and asks
whether repetition / period / frequency / phase / winding-number can EMERGE from
difference-and-relation dynamics alone.

PR-R1 scope only: substrate (first- and second-order dynamics), topology generators, and
the first four instruments (R1 difference, R2 direction, R3 reversal, R4 period), plus the
9th-audit ("instrument audit") machinery. R5-R11 are explicitly out of scope for this PR.

See ai_lab/relational/AUDIT.md for the full 7+8th+9th audit writeup, and
ai_lab/relational/run.py for the LAW.md Section 1 module header.
"""
