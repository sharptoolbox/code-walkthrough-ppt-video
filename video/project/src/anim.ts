import { interpolate, Easing, useCurrentFrame, useVideoConfig } from 'remotion';

/** 纯函数版：第 n 个元素依次点亮 */
export const seqAt = (f: number, fps: number, index: number, step = 0.35, delay = 0, fadeIn = 0.3) =>
  interpolate(f, [(delay + index * step) * fps, (delay + index * step + fadeIn) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

/** 第 n 个元素在 step 秒间隔下依次点亮，返回 0~1 透明度 */
export const useSeq = (index: number, step = 0.35, delay = 0, fadeIn = 0.3) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return seqAt(f, fps, index, step, delay, fadeIn);
};

export const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};

/** 入场：位移 + 透明度 */
export const useRise = (start = 0, dur = 0.7, from = 26) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(f, [start * fps, (start + dur) * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  return { opacity: p, transform: `translateY(${(1 - p) * from}px)` };
};

/** 场景整体进出场（交叉溶解用，仅淡入 + 轻微缩放） */
export const useSceneIn = (durFrames: number, side: 'left' | 'right' | 'none' = 'none') => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(f, [0, 0.42 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const x = side === 'none' ? 0 : (1 - p) * (side === 'left' ? -60 : 60);
  return {
    opacity: p,
    transform: `translateX(${x}px) scale(${0.975 + p * 0.025})`,
  };
};
