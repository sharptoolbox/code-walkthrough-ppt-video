import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { C, F } from './theme';
import { seqAt } from './anim';

/**
 * ─────────────────────────────────────────────────────────────────────────
 *  图表工具箱
 * ─────────────────────────────────────────────────────────────────────────
 *  画布：DiagramScene 给的外框是 1600×826（left:160, top:104）。
 *        SVG 一律用 viewBox="0 0 1600 826"，preserveAspectRatio="xMidYMid meet"，
 *        坐标即像素，所见即所得。
 *
 *  画法约定（三支成片踩出来的）：
 *   1. 只用 SVG 画图体，不要在里面塞 HTML —— 混排会让坐标无法预测。
 *   2. 每个元素出现都用 seqAt(f, fps, index, step, delay) 驱动 opacity，
 *      让画面"长"出来而不是"跳"出来；delays 按讲解顺序排。
 *   3. 任何文字都要给足宽度：写完后自己按「中文字宽 ≈ 字号 × 1.0，英文 ≈ 0.55」
 *      估一遍，别让 text 溢出 rect 或被画布裁掉。
 *   4. 底部说明条由 DiagramScene 负责（scene.callout / scene.note），
 *      图里不要再画一遍标题条。
 *  ─────────────────────────────────────────────────────────────────────────
 */

export const dg: React.CSSProperties = { width: '100%', height: '100%' };

/** 画布尺寸常量，画图时直接引用，别写字面量 */
export const CW = 1600;
export const CH = 826;

/* ============================ 配色 ============================ */
export type Tone = 'blue' | 'teal' | 'amber' | 'danger' | 'plain' | 'dark';

export const toneOf = (t: Tone = 'plain') => {
  switch (t) {
    case 'blue':
      return { fill: C.bg2, stroke: C.primaryLite, top: C.primary, title: C.text, body: C.text2, sub: C.primaryLite };
    case 'teal':
      return { fill: 'rgba(0,137,123,0.16)', stroke: C.accentLite, top: C.accent, title: C.text, body: C.text2, sub: C.accentLite };
    case 'amber':
      return { fill: 'rgba(232,163,61,0.14)', stroke: C.warn, top: C.warn, title: C.text, body: C.text2, sub: C.warn };
    case 'danger':
      return { fill: 'rgba(224,90,90,0.14)', stroke: C.danger, top: C.danger, title: C.text, body: C.text2, sub: C.danger };
    case 'dark':
      return { fill: C.bg3, stroke: C.border, top: C.dim, title: C.text, body: C.text2, sub: C.dim };
    default:
      return { fill: C.bg2, stroke: C.border, top: C.dim, title: C.text, body: C.text2, sub: C.dim };
  }
};

/* ========================== 图内标题 ========================== */
/** HTML 层标题，不占 SVG 坐标。放在图的最上方居中。 */
export const DTitle: React.FC<{ text: string; sub?: string; op: number }> = ({ text, sub, op }) => (
  <div
    style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      textAlign: 'center',
      opacity: op,
      transform: `translateY(${(1 - op) * -14}px)`,
    }}
  >
    <div style={{ fontFamily: F, fontSize: 44, fontWeight: 700, color: C.text, letterSpacing: 2 }}>{text}</div>
    {sub ? <div style={{ fontFamily: F, fontSize: 25, color: C.dim, marginTop: 10, letterSpacing: 1 }}>{sub}</div> : null}
  </div>
);

/* ============================ 箭头 ============================ */
export const Arrow: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  op: number;
  color?: string;
  dash?: string;
  width?: number;
  /** 末端箭头尺寸，0 表示不画箭头 */
  head?: number;
}> = ({ x1, y1, x2, y2, op, color = C.accentLite, dash = '10 8', width = 3, head = 15 }) => {
  const a = Math.atan2(y2 - y1, x2 - x1);
  const h = head;
  const bx = x2 - Math.cos(a) * h;
  const by = y2 - Math.sin(a) * h;
  const p = (ang: number) => `${bx + Math.cos(a + ang) * h * 0.62},${by + Math.sin(a + ang) * h * 0.62}`;
  return (
    <g opacity={op}>
      <line x1={x1} y1={y1} x2={head ? bx : x2} y2={head ? by : y2} stroke={color} strokeWidth={width} strokeDasharray={dash} />
      {head ? <polygon points={`${x2},${y2} ${p(2.5)} ${p(-2.5)}`} fill={color} /> : null}
    </g>
  );
};

/* =========================== 节点卡片 =========================== */
export const NodeBox: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  op: number;
  title: string;
  lines?: string[];
  sub?: string;
  tone?: Tone;
  /** 顶部色条 */
  hbar?: boolean;
  titleSize?: number;
  lineSize?: number;
}> = ({ x, y, w, h, op, title, lines = [], sub, tone = 'plain', hbar = true, titleSize = 32, lineSize = 22 }) => {
  const t = toneOf(tone);
  const cx = x + w / 2;
  const blockH = lines.length * (lineSize + 8) + (sub ? lineSize + 4 : 0);
  const titleY = y + h / 2 - blockH / 2 + (lines.length || sub ? 0 : titleSize * 0.34) + 2;
  return (
    <g opacity={op} transform={`translate(0, ${(1 - op) * 14})`}>
      <rect x={x} y={y} width={w} height={h} rx={18} fill={t.fill} stroke={t.stroke} strokeWidth={2.5} />
      {hbar ? <rect x={x} y={y} width={w} height={6} rx={3} fill={t.top} /> : null}
      <text x={cx} y={titleY} textAnchor="middle" fontFamily={F} fontSize={titleSize} fontWeight={700} fill={t.title}>
        {title}
      </text>
      {lines.map((ln, i) => (
        <text
          key={i}
          x={cx}
          y={titleY + (i + 1) * (lineSize + 8)}
          textAnchor="middle"
          fontFamily={F}
          fontSize={lineSize}
          fill={t.body}
        >
          {ln}
        </text>
      ))}
      {sub ? (
        <text
          x={cx}
          y={titleY + lines.length * (lineSize + 8) + lineSize}
          textAnchor="middle"
          fontFamily={F}
          fontSize={lineSize - 2}
          fill={t.sub}
        >
          {sub}
        </text>
      ) : null}
    </g>
  );
};

/* =========================== 小药丸标签 =========================== */
export const ChipS: React.FC<{
  x: number;
  y: number;
  text: string;
  op: number;
  tone?: Tone;
  size?: number;
  pad?: number;
}> = ({ x, y, text, op, tone = 'plain', size = 22, pad = 16 }) => {
  const t = toneOf(tone);
  // 中文按 1.0 字宽估算，够用且不会溢出
  const w = text.length * size + pad * 2;
  const h = size + 16;
  return (
    <g opacity={op}>
      <rect x={x} y={y} width={w} height={h} rx={h / 2} fill={t.fill} stroke={t.stroke} strokeWidth={1.8} />
      <text x={x + w / 2} y={y + h / 2 + size * 0.36} textAnchor="middle" fontFamily={F} fontSize={size} fill={t.title}>
        {text}
      </text>
    </g>
  );
};
ChipS.displayName = 'ChipS';

/** ChipS 的宽度计算（外部排版时用，避免手算） */
export const chipW = (text: string, size = 22, pad = 16) => text.length * size + pad * 2;

/* ========================= 一排药丸标签 ========================= */
/**
 * 横排 chip。**必须用这个，不要自己写 `x + j * (chipW(m) + gap)`** ——
 * 那样算出来的是「按当前标签的宽度递增」，标签宽度不一致时必然重叠。
 * 这里按每个标签的实际宽度累加，宽度参差不齐也不会叠。
 */
export const ChipRow: React.FC<{
  x: number;
  y: number;
  items: string[];
  ops: number[];
  tone?: Tone;
  size?: number;
  gap?: number;
  /** 超出这个宽度就静默警告（开发时能早点发现排版挤爆画布） */
  maxRight?: number;
}> = ({ x, y, items, ops, tone = 'plain', size = 24, gap = 18, maxRight = CW }) => {
  let cx = x;
  const out: React.ReactNode[] = [];
  items.forEach((t, i) => {
    out.push(<ChipS key={t + i} x={cx} y={y} text={t} op={ops[i] ?? 1} tone={tone} size={size} />);
    cx += chipW(t, size) + gap;
  });
  if (cx - gap > maxRight) {
    // 画布外会被静默裁掉，这里给出可见提示
    out.push(
      <text key="__overflow" x={x} y={y + size + 34} fontFamily={F} fontSize={18} fill={C.danger}>
        {'\u26a0 标签超出画布（宽 ' + Math.round(cx - gap - x) + 'px，可用 ' + Math.round(maxRight - x) + 'px），请减少数量或缩小字号'}
      </text>
    );
  }
  return <>{out}</>;
};

/* ============================ 分层条 ============================ */
/** 横向长条，适合画分层架构 / 阶段推进 */
export const Band: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  op: number;
  label: string;
  desc?: string;
  tone?: Tone;
  labelW?: number;
  labelSize?: number;
}> = ({ x, y, w, h, op, label, desc, tone = 'plain', labelW = 260, labelSize = 30 }) => {
  const t = toneOf(tone);
  return (
    <g opacity={op} transform={`translate(0, ${(1 - op) * 14})`}>
      <rect x={x} y={y} width={w} height={h} rx={14} fill={t.fill} stroke={t.stroke} strokeWidth={2} />
      <rect x={x} y={y} width={6} height={h} rx={3} fill={t.top} />
      <text x={x + 30} y={y + h / 2 + labelSize * 0.36} fontFamily={F} fontSize={labelSize} fontWeight={700} fill={t.title}>
        {label}
      </text>
      {desc ? (
        <text x={x + labelW} y={y + h / 2 + 9} fontFamily={F} fontSize={24} fill={t.body}>
          {desc}
        </text>
      ) : null}
    </g>
  );
};

/* ============================ 图例 ============================ */
export const Legend: React.FC<{
  x: number;
  y: number;
  op: number;
  items: { text: string; color: string }[];
  size?: number;
  gap?: number;
}> = ({ x, y, op, items, size = 22, gap = 30 }) => {
  let cx = x;
  return (
    <g opacity={op}>
      {items.map((it, i) => {
        const w = it.text.length * size + 46;
        const el = (
          <g key={i}>
            <circle cx={cx + size * 0.5} cy={y} r={size * 0.42} fill={it.color} />
            <text x={cx + size * 1.5} y={y + size * 0.36} fontFamily={F} fontSize={size} fill={C.text2}>
              {it.text}
            </text>
          </g>
        );
        cx += w + gap;
        return el;
      })}
    </g>
  );
};

/* ========================== 提示横条 ========================== */
export const NoteBanner: React.FC<{
  x: number;
  y: number;
  w: number;
  op: number;
  title: string;
  sub?: string;
  tone?: Tone;
  h?: number;
}> = ({ x, y, w, op, title, sub, tone = 'amber', h = 86 }) => {
  const t = toneOf(tone);
  return (
    <g opacity={op} transform={`translate(0, ${(1 - op) * 16})`}>
      <rect x={x} y={y} width={w} height={h} rx={14} fill={t.fill} stroke={t.stroke} strokeWidth={2} />
      <text x={x + w / 2} y={y + (sub ? h / 2 - 6 : h / 2 + 9)} textAnchor="middle" fontFamily={F} fontSize={25} fontWeight={600} fill={t.sub}>
        {title}
      </text>
      {sub ? (
        <text x={x + w / 2} y={y + h / 2 + 32} textAnchor="middle" fontFamily={F} fontSize={21} fill={C.dim}>
          {sub}
        </text>
      ) : null}
    </g>
  );
};

/* ══════════════════════════ 示例图 1：分层架构 ══════════════════════════ */
/**
 * 画"系统由哪几层组成"。左侧竖排分层，右侧放该层的具体模块。
 * 换成别的系统时：改 LAYERS 文案与 tone 即可。
 */
export const ARCH: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t0 = seqAt(f, fps, 0, 0.3, 0.1);
  const LAYERS: { name: string; modules: string[]; tone: Tone }[] = [
    { name: '接入层', modules: ['Web 控制台', 'REST API', '定时任务'], tone: 'blue' },
    { name: '应用层', modules: ['业务服务', '编排引擎', '权限校验'], tone: 'teal' },
    { name: '领域层', modules: ['领域模型', '规则引擎', '状态机'], tone: 'amber' },
    { name: '基础设施层', modules: ['数据库', '消息队列', '对象存储'], tone: 'plain' },
  ];
  const X = 120;
  const Y0 = 150;
  const BW = 620;
  const BH = 128;
  const GAP = 26;
  return (
    <div style={{ ...dg, position: 'relative' }}>
      <DTitle text="系统分层架构" sub="自上而下：请求进来、业务处理、领域决策、落到存储" op={t0} />
      <svg style={dg} viewBox={`0 0 ${CW} ${CH}`} preserveAspectRatio="xMidYMid meet">
        {LAYERS.map((L, i) => {
          const y = Y0 + i * (BH + GAP);
          const op = seqAt(f, fps, i, 0.34, 0.5);
          return (
            <g key={L.name}>
              <Band x={X} y={y} w={BW} h={BH} op={op} label={L.name} tone={L.tone} />
              <Arrow x1={X + BW + 6} y1={y + BH / 2} x2={X + BW + 76} y2={y + BH / 2} op={op} dash="0" head={16} />
              <ChipRow
                x={X + BW + 116}
                y={y + BH / 2 - 20}
                items={L.modules}
                ops={L.modules.map((_, j) => seqAt(f, fps, j, 0.22, 1.0 + i * 0.34))}
                tone={L.tone === 'plain' ? 'dark' : L.tone}
                size={24}
                maxRight={CW - 40}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/* ══════════════════════════ 示例图 2：主流程 ══════════════════════════ */
/**
 * 画"一条链路怎么走"，带一个判定分支。
 * 换成别的流程时：改 STEPS 与分支文案即可。
 */
export const FLOW: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t0 = seqAt(f, fps, 0, 0.3, 0.1);
  const STEPS = ['接收请求', '参数校验', '业务处理', '落库', '返回结果'];
  const BW = 226;
  const BH = 138;
  const Y = 220;
  const GAP = (CW - 240 - STEPS.length * BW) / (STEPS.length - 1);
  return (
    <div style={{ ...dg, position: 'relative' }}>
      <DTitle text="主流程" sub="每一步都能单独定位与重试" op={t0} />
      <svg style={dg} viewBox={`0 0 ${CW} ${CH}`} preserveAspectRatio="xMidYMid meet">
        {STEPS.map((s, i) => {
          const x = 120 + i * (BW + GAP);
          const op = seqAt(f, fps, i, 0.3, 0.5);
          return (
            <g key={s}>
              <NodeBox x={x} y={Y} w={BW} h={BH} op={op} title={s} tone={i === 2 ? 'teal' : 'blue'} titleSize={28} />
              {i < STEPS.length - 1 ? (
                <Arrow x1={x + BW + 8} y1={Y + BH / 2} x2={x + BW + GAP - 8} y2={Y + BH / 2} op={seqAt(f, fps, i, 0.3, 0.75)} dash="0" head={16} />
              ) : null}
            </g>
          );
        })}
        <NoteBanner x={330} y={500} w={940} op={seqAt(f, fps, 0, 0.4, 2.4)} title="关键点：第 3 步是唯一的写操作" sub="其余步骤幂等，失败可安全重放" />
        <Legend
          x={120}
          y={690}
          op={seqAt(f, fps, 0, 0.4, 3.0)}
          items={[
            { text: '读操作', color: C.primaryLite },
            { text: '写操作', color: C.accentLite },
          ]}
        />
      </svg>
    </div>
  );
};

/* ══════════════════════════ 注册表 ══════════════════════════ */
/**
 * storyboard.json 里的 scene.id 就是这里的键。
 * 每做一支新视频，在这里补自己的图（复制上面的示例改文案最快）。
 */
export const DIAGRAMS: Record<string, React.FC> = {
  ARCH,
  FLOW,
};
