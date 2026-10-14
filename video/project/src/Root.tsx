import React from 'react';
import { CalculateMetadataFunction, Composition } from 'remotion';
import { AppVideo } from './Video';
import type { AppProps } from './types';

/**
 * 这里的 defaultProps 只是 Remotion Studio 里没有 props 时的占位。
 * 正式渲染一律用 --props=props.json 覆盖。
 * Composition id = CodeWalkthrough（渲染脚本里要用同一个名字）。
 */
const defaultProps: AppProps = {
  fps: 30,
  total: 12,
  width: 1920,
  height: 1080,
  audio: [],
  captions: [{ start: 0, end: 12, text: '等待 props.json 覆盖' }],
  chapters: [{ name: '预览', start: 0, end: 12 }],
  scenes: [
    {
      kind: 'cover',
      start: 0,
      end: 12,
      chapter: '',
      shot: 'shots/00-cover.png',
      title: '源码讲解',
      subtitle: '等待 props.json 覆盖',
    },
  ],
  brand: '',
  endTitle: '',
  endSubtitle: '',
  endFooter: '',
};

export const calcMeta: CalculateMetadataFunction<AppProps> = ({ props }) => {
  const fps = props.fps || 30;
  const total = props.total || 10;
  return {
    durationInFrames: Math.max(1, Math.round(total * fps)),
    fps,
    width: props.width || 1920,
    height: props.height || 1080,
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="CodeWalkthrough"
    component={AppVideo}
    durationInFrames={360}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={defaultProps}
    calculateMetadata={calcMeta}
  />
);
