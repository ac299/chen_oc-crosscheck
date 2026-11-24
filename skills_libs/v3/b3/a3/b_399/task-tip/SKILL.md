---
name: task-tip
description: "Advice for THIS task from earlier attempts at it; load it first"
---
## Advice from earlier attempts
The exception checks passed; the failure is about the plotted data/domain. The attempt used t = np.linspace(0, 1, sample_size), which is likely wrong. Use a fixed domain independent of frequency, most likely t = np.linspace(0, 2*np.pi, sample_size), and plot np.sin(frequency*t) and np.cos(frequency*t) (not 2*pi*frequency*t). Hidden tests probably inspect the line data (x and y arrays) or axis limits, so match the conventional sine/cosine-over-[0,2π] formulation. Keep the ValueError checks (negative frequency, non-positive sample size), cast sample_size to int, return (fig, ax), and add labels/legend/title. If unsure, prefer the simplest standard interpretation: x from 0 to 2π, y = sin(f*x), cos(f*x).
