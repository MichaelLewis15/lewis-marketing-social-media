"""Lewis Marketing video renderer (HighLevel Weekly and every other recap, launch, myth, stat, review, podcast,
countdown and results video). Everything lives in engine.py; see its docstring for the spec format.

usage: python3 render_weekly.py spec.json OUTDIR            full render (videos, covers, gbp.png)
       python3 render_weekly.py --preview spec.json OUTDIR  quick stills of every scene, all sizes, plus gbp.png
"""
import sys
import engine

if __name__ == "__main__":
    if sys.argv[1] == "--preview": engine.preview(sys.argv[2], sys.argv[3], sys.argv[4].split(",") if len(sys.argv) > 4 else None)
    else: engine.main(sys.argv[1], sys.argv[2])
