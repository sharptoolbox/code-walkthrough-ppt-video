import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, F, FD } from './theme';
import type { AppProps, Caption as Cap } from './types';

/* ---------------------------------------------------------------- 字幕 */
/** 屏幕底部单行硬字幕。整条（含深色底）共用同一个 opacity，进出各 0.16s。 */
export const CaptionLayer: React.FC<{ caps: Cap[] }> = ({ caps }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const cur = caps.find((c) => t >= c.start && t < c.end);
  if (!cur) return null;
  const op = Math.min(
    interpolate(t, [cur.start, cur.start + 0.16], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    interpolate(t, [cur.end - 0.16, cur.end], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  );
  return (
    <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'stretch' }}>
      <div
        style={{
          height: 150,
          background: 'linear-gradient(to top, rgba(7,11,19,0.90), rgba(7,11,19,0.66))',
          borderTop: `2px solid ${C.accent}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: op,
        }}
      >
        <div
          style={{
            fontFamily: F,
            fontSize: 44,
            fontWeight: 600,
            color: '#FFFFFF',
            letterSpacing: 1,
            textAlign: 'center',
            maxWidth: 1700,
            textShadow: '0 2px 12px rgba(0,0,0,0.9)',
          }}
        >
          {cur.text}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------ 章节角标 */
export const ChapterBadge: React.FC<{ name: string; index: number; total: number }> = ({ name, index, total }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = interpolate(f, [0, 0.4 * fps], [0, 1], { extrapolateRight: 'clamp' });
  return (
    <div
      style={{
        position: 'absolute',
        left: 56,
        top: 42,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        opacity: op,
      }}
    >
      <div style={{ width: 6, height: 30, background: C.accent, borderRadius: 3 }} />
      <div style={{ fontFamily: F, fontSize: 27, fontWeight: 600, color: C.text2, letterSpacing: 2 }}>{name}</div>
      <div style={{ fontFamily: FD, fontSize: 22, color: C.dim, letterSpacing: 1 }}>
        {String(index).padStart(2, '0')} / {String(total).padStart(2, '0')}
      </div>
    </div>
  );
};

/* -------------------------------------------------------------- 进度条 */
/** 右上角水印 + 进度条。brand 为空字符串时整块不渲染。 */
export const ProgressBar: React.FC<{ progress: number; brand?: string }> = ({ progress, brand }) => {
  if (!brand) return null;
  return (
    <div style={{ position: 'absolute', right: 56, top: 42, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
      <div style={{ fontFamily: F, fontSize: 24, fontWeight: 600, color: C.dim, letterSpacing: 3 }}>{brand}</div>
      <div style={{ width: 220, height: 4, background: C.border, borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${Math.max(0, Math.min(1, progress)) * 100}%`, height: '100%', background: C.accentLite }} />
      </div>
    </div>
  );
};

/* --------------------------------------------------------- 章节引导条 */
/** 章节首次出现时的居中大标题（当前成片未启用，保留备用） */
export const ChapterIntro: React.FC<{ name: string }> = ({ name }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = Math.min(
    interpolate(f, [0, 0.35 * fps], [0, 1], { extrapolateRight: 'clamp' }),
    interpolate(f, [1.6 * fps, 2.1 * fps], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  );
  if (op <= 0.001) return null;
  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: op }}>
      <div
        style={{
          padding: '26px 64px',
          border: `2px solid ${C.accent}44`,
          background: 'rgba(10,16,28,0.86)',
          borderRadius: 14,
        }}
      >
        <div style={{ fontFamily: F, fontSize: 56, fontWeight: 700, color: C.text, letterSpacing: 6 }}>{name}</div>
      </div>
    </AbsoluteFill>
  );
};

export const chapterAt = (p: AppProps, t: number) => {
  const i = p.chapters.findIndex((c) => t >= c.start && t < c.end);
  return i < 0 ? p.chapters.length - 1 : i;
};
