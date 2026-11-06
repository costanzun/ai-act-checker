import { cn } from "@/lib/utils";
import { runs, SCENES, type SceneKey, type Sprite } from "./sprites";

/** Renders a sprite as crisp SVG rects. Decorative unless a label is given. */
export function Pixel({ sprite, label, className }: { sprite: Sprite; label?: string; className?: string }) {
  return (
    <svg
      viewBox={`0 0 ${sprite.w} ${sprite.h}`}
      shapeRendering="crispEdges"
      className={cn("pixel-art block h-auto", className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {sprite.layers.map((l, i) => (
        <g key={i} className={l.cls}>
          {runs(l).map((r) => <rect key={`${r.x}-${r.y}`} x={r.x} y={r.y} width={r.w} height={1} fill={r.c} />)}
        </g>
      ))}
    </svg>
  );
}

/** One of the mascot scenes (one per verdict and app state). */
export function DogScene({ scene, label, className }: { scene: SceneKey; label?: string; className?: string }) {
  return <Pixel sprite={SCENES[scene]} label={label} className={className} />;
}
