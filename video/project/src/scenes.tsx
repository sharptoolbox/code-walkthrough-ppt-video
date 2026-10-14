import React from 'react';
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import { C, F, FD } from './theme';
import { DIAGRAMS } from './diagrams';
import type { Scene } from './types';

const CARD_W = 1400;
const CARD_H = 788;
const CARD_TOP = 128;

/* ------------------------------------------------------------ 深色衬底 */
const Backdrop: React.FC<{ glow?: string }> = ({ glow = C.accent }) => (
  <AbsoluteFill style={{ background: `radial-gradient(1200px 700px at 50% 42%, ${glow}14 0%, ${C.bg} 62%)` }} />
);

/* ---------------------------------------------------------------- 片头 */
export const Cover: React.FC<{ shot: string; title: string; subtitle: string; durF: number }> = ({
  shot,
  title,
  subtitle,
  durF,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kb = interpolate(f, [0, durF], [1.1, 1.0], { extrapolateRight: 'clamp' });
  const titleOp = interpolate(f, [0.9 * fps, 1.8 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const subOp = interpolate(f, [1.7 * fps, 2.5 * fps], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const lineW = interpolate(f, [1.3 * fps, 2.2 * fps], [0, 220], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  return (
    <AbsoluteFill style={{ background: C.bg, overflow: 'hidden' }}>
      <Img
        src={staticFile(shot)}
        style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${kb})`, opacity: 0.5 }}
      />
      <AbsoluteFill style={{ background: 'linear-gradient(90deg, rgba(9,13,22,0.96) 0%, rgba(9,13,22,0.80) 46%, rgba(9,13,22,0.42) 100%)' }} />
      <AbsoluteFill style={{ background: 'radial-gradient(1400px 800px at 22% 50%, rgba(21,101,192,0.28) 0%, rgba(9,13,22,0) 60%)' }} />
      <div style={{ position: 'absolute', left: 170, top: 372 }}>
        <div style={{ width: lineW, height: 6, background: C.accentLite, borderRadius: 3, marginBottom: 34, opacity: titleOp }} />
        <div
          style={{
            fontFamily: F,
            fontSize: 126,
            fontWeight: 800,
            color: '#FFFFFF',
            letterSpacing: 4,
            lineHeight: 1.1,
            opacity: titleOp,
            transform: `translateY(${(1 - titleOp) * 30}px)`,
            textShadow: '0 8px 40px rgba(0,0,0,0.8)',
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontFamily: F,
            fontSize: 44,
            fontWeight: 500,
            color: C.text2,
            letterSpacing: 4,
            marginTop: 30,
            opacity: subOp,
            transform: `translateY(${(1 - subOp) * 20}px)`,
          }}
        >
          {subtitle}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ----------------------------------------------------------- 截图场景 */
export const ShotScene: React.FC<{ scene: Scene; durF: number }> = ({ scene, durF }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = durF / fps;
  // 缓推镜头（Ken Burns）：幅度必须**收着做**——它等价于对截图做一次等比裁边。
  // 卡片宽 1400 / 图片宽 1600，卡片坐标 ×1.143 才是图像像素。下面是各幅度的实际裁边量：
  //   kb 起始 1.055、平移 ∓8  →  左右各裁约 54px（图像空间）→ 会把左侧导航的品牌名切掉（踩过）
  //   kb 起始 1.020、平移 ∓5  →  左右各裁约 20px           → 配合骨架的 22px 安全边距刚好安全
  // 想加大幅度的话，先确认截图左右各有 ≥ 该幅度的空白（见 references/02-ui-redraw.md 安全边距）。
  const kb = interpolate(f, [0, durF], [1.02, 1.004], { extrapolateRight: 'clamp' });
  const px = interpolate(f, [0, durF], [-5, 5]);
  const py = interpolate(f, [0, durF], [4, -4]);
  const at = scene.calloutAt ?? 1.6;
  const rev = interpolate(f, [at * fps, (at + 0.4) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const nat = scene.noteAt ?? Math.max(2.2, dur - 5.2);
  const nrev = interpolate(f, [nat * fps, (nat + 0.4) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const single = (scene.focus || []).length === 1;

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Backdrop glow={C.primary} />
      <div
        style={{
          position: 'absolute',
          left: (1920 - CARD_W) / 2,
          top: CARD_TOP,
          width: CARD_W,
          height: CARD_H,
          borderRadius: 14,
          overflow: 'hidden',
          border: `1px solid ${C.border}`,
          boxShadow: '0 34px 90px rgba(0,0,0,0.62)',
          background: '#0B1018',
        }}
      >
        {/* 图片与高亮框同处一个变换层，保证高亮精准贴合 */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transform: `translate(${px}px, ${py}px) scale(${kb})`,
            transformOrigin: 'center center',
          }}
        >
          <Img src={staticFile(scene.shot || '')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          {(scene.focus || []).map((r, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `${r.x * 100}%`,
                top: `${r.y * 100}%`,
                width: `${r.w * 100}%`,
                height: `${r.h * 100}%`,
                border: `3px solid ${C.accentLite}`,
                borderRadius: 8,
                opacity: rev,
                boxShadow: single
                  ? '0 0 0 9999px rgba(6,10,18,0.46), 0 0 26px rgba(38,198,166,0.55)'
                  : '0 0 20px rgba(38,198,166,0.5)',
              }}
            />
          ))}
        </div>
      </div>

      {/* 焦点标签（不随图片缩放，文字更锐利） */}
      {(scene.focus || [])
        .filter((r) => r.label)
        .map((r, i) => (
          <div
            key={'l' + i}
            style={{
              position: 'absolute',
              left: Math.min((1920 - CARD_W) / 2 + r.x * CARD_W, 1920 - 320),
              top: CARD_TOP + r.y * CARD_H - 52,
              opacity: rev,
              background: C.accentLite,
              color: '#06231F',
              fontFamily: F,
              fontSize: 24,
              fontWeight: 700,
              padding: '7px 18px',
              borderRadius: 8,
              letterSpacing: 1,
              whiteSpace: 'nowrap',
            }}
          >
            {r.label}
          </div>
        ))}

      {/* 说明条（左下角）——textWrap:balance 防止折出孤字 */}
      {scene.callout ? (
        <div
          style={{
            position: 'absolute',
            left: 30,
            top: 848,
            width: 212,
            opacity: rev,
            transform: `translateX(${(1 - rev) * -16}px)`,
          }}
        >
          <div style={{ width: 44, height: 4, background: C.accentLite, borderRadius: 2, marginBottom: 10 }} />
          <div
            style={{
              fontFamily: F,
              fontSize: 25,
              fontWeight: 600,
              color: C.text,
              lineHeight: 1.42,
              textWrap: 'balance',
            } as React.CSSProperties}
          >
            {scene.callout}
          </div>
        </div>
      ) : null}

      {/* 边界提示（右下角） */}
      {scene.note ? (
        <div
          style={{
            position: 'absolute',
            right: 30,
            top: 848,
            width: 212,
            opacity: nrev * 0.95,
            textAlign: 'right',
            transform: `translateX(${(1 - nrev) * 16}px)`,
          }}
        >
          <div style={{ width: 44, height: 4, background: C.warn, borderRadius: 2, marginBottom: 10, marginLeft: 'auto' }} />
          <div
            style={{
              fontFamily: F,
              fontSize: 24,
              fontWeight: 600,
              color: C.warn,
              lineHeight: 1.42,
              textWrap: 'balance',
            } as React.CSSProperties}
          >
            {scene.note}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/* ----------------------------------------------------------- 图表场景 */
export const DiagramScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const D = DIAGRAMS[scene.id || 'ARCH'] || DIAGRAMS.ARCH;
  const nat = scene.noteAt ?? 3.2;
  const nrev = interpolate(f, [nat * fps, (nat + 0.4) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Backdrop />
      <div style={{ position: 'absolute', left: 160, top: 104, width: 1600, height: 826 }}>
        <D />
      </div>
      {scene.callout ? (
        <div style={{ position: 'absolute', left: 30, top: 848, width: 212 }}>
          <div style={{ width: 44, height: 4, background: C.accentLite, borderRadius: 2, marginBottom: 10 }} />
          <div style={{ fontFamily: F, fontSize: 25, fontWeight: 600, color: C.text, lineHeight: 1.42, textWrap: 'balance' } as React.CSSProperties}>
            {scene.callout}
          </div>
        </div>
      ) : null}
      {scene.note ? (
        <div style={{ position: 'absolute', right: 30, top: 848, width: 212, textAlign: 'right', opacity: nrev }}>
          <div style={{ width: 44, height: 4, background: C.warn, borderRadius: 2, marginBottom: 10, marginLeft: 'auto' }} />
          <div style={{ fontFamily: F, fontSize: 24, fontWeight: 600, color: C.warn, lineHeight: 1.42, textWrap: 'balance' } as React.CSSProperties}>
            {scene.note}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------- 落版 */
export const EndCard: React.FC<{ title?: string; subtitle?: string; footer?: string }> = ({
  title = '',
  subtitle = '',
  footer = '',
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op1 = interpolate(f, [0.5 * fps, 1.5 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const op2 = interpolate(f, [1.4 * fps, 2.3 * fps], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const lineW = interpolate(f, [1.0 * fps, 2.0 * fps], [0, 300], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const ring = interpolate(f, [0, 2.4 * fps], [0.6, 1], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg, justifyContent: 'center', alignItems: 'center' }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(${900 * ring}px ${560 * ring}px at 50% 50%, rgba(21,101,192,0.26) 0%, rgba(15,22,38,0) 66%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.border}55 1px, transparent 1px), linear-gradient(90deg, ${C.border}55 1px, transparent 1px)`,
          backgroundSize: '96px 96px',
          opacity: 0.28,
          maskImage: 'radial-gradient(760px 460px at 50% 50%, #000 0%, transparent 78%)',
        }}
      />
      <div style={{ textAlign: 'center', zIndex: 2 }}>
        <div style={{ width: lineW, height: 5, background: C.accentLite, borderRadius: 3, margin: '0 auto 40px' }} />
        <div
          style={{
            fontFamily: F,
            fontSize: 86,
            fontWeight: 800,
            color: '#FFFFFF',
            letterSpacing: 4,
            opacity: op1,
            transform: `translateY(${(1 - op1) * 26}px)`,
            textShadow: '0 8px 40px rgba(0,0,0,0.7)',
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontFamily: F,
            fontSize: 40,
            color: C.text2,
            letterSpacing: 5,
            marginTop: 34,
            opacity: op2,
            transform: `translateY(${(1 - op2) * 18}px)`,
          }}
        >
          {subtitle}
        </div>
        <div style={{ fontFamily: FD, fontSize: 26, color: C.dim, letterSpacing: 6, marginTop: 56, opacity: op2 }}>
          {footer}
        </div>
      </div>
    </AbsoluteFill>
  );
};
