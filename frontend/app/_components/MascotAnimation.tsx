"use client";

import dynamic from "next/dynamic";

const Player = dynamic(
  () => import("@lottiefiles/react-lottie-player").then((mod) => mod.Player),
  { ssr: false },
);

const blossomDuo = {
  v: "5.7.4",
  fr: 30,
  ip: 0,
  op: 90,
  w: 220,
  h: 220,
  nm: "Learning path mascot",
  ddd: 0,
  assets: [],
  layers: [
    {
      ddd: 0,
      ind: 1,
      ty: 4,
      nm: "body",
      sr: 1,
      ks: {
        o: { a: 0, k: 100 },
        r: { a: 1, k: [{ t: 0, s: [-6] }, { t: 45, s: [6] }, { t: 90, s: [-6] }] },
        p: { a: 0, k: [110, 112, 0] },
        a: { a: 0, k: [0, 0, 0] },
        s: { a: 1, k: [{ t: 0, s: [96, 96, 100] }, { t: 45, s: [104, 104, 100] }, { t: 90, s: [96, 96, 100] }] },
      },
      shapes: [
        {
          ty: "el",
          p: { a: 0, k: [0, 0] },
          s: { a: 0, k: [104, 118] },
          nm: "body ellipse",
        },
        { ty: "fl", c: { a: 0, k: [0.31, 0.86, 0, 1] }, o: { a: 0, k: 100 } },
      ],
      ip: 0,
      op: 90,
      st: 0,
      bm: 0,
    },
    {
      ddd: 0,
      ind: 2,
      ty: 4,
      nm: "flower",
      sr: 1,
      ks: {
        o: { a: 0, k: 100 },
        r: { a: 1, k: [{ t: 0, s: [0] }, { t: 90, s: [360] }] },
        p: { a: 0, k: [68, 68, 0] },
        a: { a: 0, k: [0, 0, 0] },
        s: { a: 0, k: [100, 100, 100] },
      },
      shapes: [
        { ty: "el", p: { a: 0, k: [0, -18] }, s: { a: 0, k: [24, 24] } },
        { ty: "el", p: { a: 0, k: [18, 0] }, s: { a: 0, k: [24, 24] } },
        { ty: "el", p: { a: 0, k: [0, 18] }, s: { a: 0, k: [24, 24] } },
        { ty: "el", p: { a: 0, k: [-18, 0] }, s: { a: 0, k: [24, 24] } },
        { ty: "fl", c: { a: 0, k: [1, 0.56, 0.81, 1] }, o: { a: 0, k: 100 } },
      ],
      ip: 0,
      op: 90,
      st: 0,
      bm: 0,
    },
  ],
};

export function MascotAnimation() {
  return (
    <div className="pointer-events-none h-40 w-40 opacity-95">
      <Player src={blossomDuo} loop autoplay />
    </div>
  );
}
