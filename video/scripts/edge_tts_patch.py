# -*- coding: utf-8 -*-
"""
edge-tts 403 修复补丁（对应上游 PR #491）

背景：自 2026 年 10 月起，旧端点
    wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1
对语音合成一律返回 403（先在多数国家，2026-10-12 起美国也一样）。
Microsoft Edge 155 已改为通过 api.msedgeservices.com 合成；该主机同样接受旧 token，
但要放在 Ocp-Apim-Subscription-Key 查询参数里。音频格式与音色完全不变（MP3 24kHz 单声道）。

用法：在调用 edge_tts 之前 `import edge_tts_patch` 即可。

排查提示：若导入本补丁后仍 403，先确认是不是别的原因（见 references/06-pitfalls.md）：
  · 用 HTTPS 的 voices/list 探活（200 说明网络通）
  · 换一个网络出口再试（本补丁与出口 IP 无关，403 与 IP 也无关）
  · 检查 edge-tts 版本（>= 7.x），以及是否被某个代理劫持了 WSS
"""
import edge_tts.communicate as _cm
import edge_tts.constants as _c
from edge_tts.constants import TRUSTED_CLIENT_TOKEN

NEW_WSS = (
    "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
    f"?Ocp-Apim-Subscription-Key={TRUSTED_CLIENT_TOKEN}"
)

# communicate.py 里是 `from .constants import WSS_URL`，绑定的是值，所以两个名字都要改
_c.WSS_URL = NEW_WSS
_cm.WSS_URL = NEW_WSS


# --- drm.py 的日期解析在非英文 locale 下会失败（中文 Windows 上 %a/%b 认不出英文缩写）---
def _patch_drm_date():
    import edge_tts.drm as _d
    from datetime import timezone as _tz
    from email.utils import parsedate_to_datetime

    @staticmethod
    def parse_rfc2616_date(date):
        try:
            parsed = parsedate_to_datetime(date)
        except (TypeError, ValueError, IndexError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_tz.utc)
        return parsed.timestamp()

    _d.DRM.parse_rfc2616_date = parse_rfc2616_date


_patch_drm_date()

PATCHED = True
