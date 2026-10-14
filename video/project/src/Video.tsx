import React from 'react';
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import type { AppProps, Scene } from './types';
import { Cover, DiagramScene, EndCard, ShotScene } from './scenes';
import { CaptionLayer, ChapterBadge, ProgressBar } from './overlays';
import { useSceneIn } from './anim';
import { C } from './theme';

const OVERLAP = 0.42;

const SceneView: React.FC<{ scene: Scene; durF: number; p: AppProps }> = ({ scene, durF, p }) => {
  const anim = useSceneIn(durF);
  let inner: React.ReactNode;
  if (scene.kind === 'cover') {
    inner = <Cover shot={scene.shot || ''} title={scene.title || ''} subtitle={scene.subtitle || ''} durF={durF} />;
  } else if (scene.kind === 'diagram') {
    inner = <DiagramScene scene={scene} />;
  } else if (scene.kind === 'shot') {
    inner = <ShotScene scene={scene} durF={durF} />;
  } else {
    inner = <EndCard title={p.endTitle} subtitle={p.endSubtitle} footer={p.endFooter} />;
  }
  return <AbsoluteFill style={anim}>{inner}</AbsoluteFill>;
};

export const AppVideo: React.FC<AppProps> = (p) => {
  const { fps, durationInFrames } = useVideoConfig();
  const f = useCurrentFrame();
  const t = f / fps;
  const ov = Math.round(OVERLAP * fps);

  let chIdx = p.chapters.findIndex((c) => t >= c.start && t < c.end);
  if (chIdx < 0) chIdx = p.chapters.length - 1;
  const ch = p.chapters[chIdx];
  const curScene = p.scenes.find((s) => t >= s.start && t < s.end + 0.42) || p.scenes[p.scenes.length - 1];
  const hideBadge = curScene.kind === 'cover' || curScene.kind === 'end' || !curScene.chapter;

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {p.audio.map((a) => (
        <Sequence key={a.src} from={Math.round(a.start * fps)}>
          <Audio src={staticFile(a.src)} />
        </Sequence>
      ))}

      {p.scenes.map((s, i) => {
        const from = Math.round(s.start * fps);
        const dur = Math.round((s.end - s.start) * fps) + (i < p.scenes.length - 1 ? ov : 0);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} name={`${s.kind}:${s.chapter}`}>
            <SceneView scene={s} durF={dur} p={p} />
          </Sequence>
        );
      })}

      {ch && !hideBadge ? <ChapterBadge name={ch.name} index={chIdx + 1} total={p.chapters.length} /> : null}
      <ProgressBar progress={f / durationInFrames} brand={p.brand} />
      <CaptionLayer caps={p.captions} />
    </AbsoluteFill>
  );
};
