import { useMemo } from "react";

import { formatPrice } from "@/lib/format";

export interface ChartSeries {
  label: string;
  color: string;
  points: { captured_at: string; price: number }[];
}

const W = 320;
const H = 180;
const PAD = { top: 12, right: 12, bottom: 22, left: 44 };

/** Лёгкий SVG-линейный график без внешних зависимостей. */
export function PriceChart({ series }: { series: ChartSeries[] }) {
  const model = useMemo(() => {
    const all = series.flatMap((s) =>
      s.points.map((p) => ({ t: new Date(p.captured_at).getTime(), v: p.price }))
    );
    if (all.length === 0) return null;

    const tMin = Math.min(...all.map((a) => a.t));
    const tMax = Math.max(...all.map((a) => a.t));
    const vMin = Math.min(...all.map((a) => a.v));
    const vMax = Math.max(...all.map((a) => a.v));
    const vPad = (vMax - vMin) * 0.1 || vMax * 0.05 || 1;
    const lo = vMin - vPad;
    const hi = vMax + vPad;

    const innerW = W - PAD.left - PAD.right;
    const innerH = H - PAD.top - PAD.bottom;

    const x = (t: number) =>
      tMax === tMin
        ? PAD.left + innerW / 2
        : PAD.left + ((t - tMin) / (tMax - tMin)) * innerW;
    const y = (v: number) =>
      hi === lo
        ? PAD.top + innerH / 2
        : PAD.top + (1 - (v - lo) / (hi - lo)) * innerH;

    return { x, y, lo, hi, tMin, tMax };
  }, [series]);

  if (!model) return null;

  const fmtDate = (t: number) =>
    new Date(t).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="График цен"
    >
      {/* оси Y: верх/низ подписи */}
      <text x={4} y={PAD.top + 4} fontSize={9} fill="var(--tg-theme-hint-color)">
        {formatPrice(Math.round(model.hi))}
      </text>
      <text
        x={4}
        y={H - PAD.bottom}
        fontSize={9}
        fill="var(--tg-theme-hint-color)"
      >
        {formatPrice(Math.round(model.lo))}
      </text>
      {/* рамка */}
      <line
        x1={PAD.left}
        y1={H - PAD.bottom}
        x2={W - PAD.right}
        y2={H - PAD.bottom}
        stroke="var(--tg-theme-hint-color)"
        strokeOpacity={0.3}
      />
      {/* подписи дат */}
      <text
        x={PAD.left}
        y={H - 6}
        fontSize={9}
        fill="var(--tg-theme-hint-color)"
      >
        {fmtDate(model.tMin)}
      </text>
      <text
        x={W - PAD.right}
        y={H - 6}
        fontSize={9}
        textAnchor="end"
        fill="var(--tg-theme-hint-color)"
      >
        {fmtDate(model.tMax)}
      </text>

      {series.map((s) => {
        if (s.points.length === 0) return null;
        const pts = s.points.map(
          (p) =>
            `${model.x(new Date(p.captured_at).getTime())},${model.y(p.price)}`
        );
        return (
          <g key={s.label}>
            {s.points.length > 1 && (
              <polyline
                points={pts.join(" ")}
                fill="none"
                stroke={s.color}
                strokeWidth={2}
              />
            )}
            {s.points.map((p, i) => (
              <circle
                key={i}
                cx={model.x(new Date(p.captured_at).getTime())}
                cy={model.y(p.price)}
                r={2.5}
                fill={s.color}
              />
            ))}
          </g>
        );
      })}
    </svg>
  );
}
