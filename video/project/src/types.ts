export type Caption = { start: number; end: number; text: string };

export type FocusRect = { x: number; y: number; w: number; h: number; label?: string };

export type SceneKind = 'cover' | 'diagram' | 'shot' | 'end';

export type Scene = {
  kind: SceneKind;
  start: number;
  end: number;
  chapter: string;
  /** diagram: 取 diagrams.tsx 里 DIAGRAMS 的键，如 "ARCH" / "FLOW" */
  id?: string;
  /** shot: 一般是 "shots/xxx.png" */
  shot?: string;
  /** shot: 高亮框，坐标为相对整图的 0~1 比例 */
  focus?: FocusRect[];
  callout?: string;
  calloutAt?: number;
  note?: string;
  noteAt?: number;
  /** cover */
  title?: string;
  subtitle?: string;
};

export type AudioSeg = { src: string; start: number; dur: number };

export type AppProps = {
  fps: number;
  total: number;
  width: number;
  height: number;
  audio: AudioSeg[];
  captions: Caption[];
  chapters: { name: string; start: number; end: number }[];
  scenes: Scene[];
  /** 右上角水印；留空则不占位、不显示 */
  brand?: string;
  /** 落版文案，全部可选 */
  endTitle?: string;
  endSubtitle?: string;
  endFooter?: string;
};
