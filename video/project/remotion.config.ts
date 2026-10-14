import { Config } from '@remotion/cli/config';

Config.setOverwriteOutput(true);
Config.setVideoImageFormat('jpeg');

/**
 * 关键：禁用 webpack 的持久化缓存。
 *
 * 原因：Remotion 在检测到 webpack 配置变化时，会用 Node 的 fs.rm 清理
 * node_modules/.cache/webpack/remotion-production-<version>。受限运行环境下的
 * 安全删除（走回收站）不可用并 fail-closed，会直接让打包阶段报错，渲染无法进行。
 *
 * 关掉持久化缓存后该目录永不生成，Remotion 判定为 does-not-exist，从而跳过清理。
 * 代价是每次渲染重新打包（约几十秒），换来稳定可跑。
 */
Config.overrideWebpackConfig((config) => ({ ...config, cache: false }));
