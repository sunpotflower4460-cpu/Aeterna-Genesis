"""The AI council of the live lab: several models look at the SAME observation packet, each in its role.

    vision       (Gemini / GPT)   writes what the images and motion LOOK like -- always labelled 見た目（未測定）
    second_view  (DeepSeek, direct) reads the 事件簿 and offers other explanations (numerics, what was put in, …)
    core         (Opus 5.5)       reconciles everything with the measurements, talks with the person, and may
                                  put proposals on the table (cards). It never runs anything: a person presses 試す.

Roles without an API key are skipped. Without a usable core, the council hands the packet to Claude Code
(the /guide command) through lab/state/latest/. Keys are read from environment variables named in
lab/config.toml and never leave this process. Only simulation images and numbers are sent to providers.
"""
from __future__ import annotations

import base64
import datetime as _dt
import itertools
import json
import os
import threading
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from tools.lab import observe, whites
from tools.lab.journal import LAB_DIR

ROLES = ("vision", "second_view", "core")
ROLE_LABEL = {"vision": "見る係", "second_view": "別の視点", "core": "中心", "claude-code": "Claude Code",
              "you": "うえきさん", "system": "ラボ"}
UNMEASURED = "【見た目（未測定）】"

DEFAULT_CONFIG: dict[str, Any] = {
    "core": {"provider": "anthropic", "model": "claude-opus-5-5", "effort": "medium",
             "api_key_env": "ANTHROPIC_API_KEY", "price_in": 4.0, "price_out": 20.0},
    "second_view": {"provider": "deepseek", "base_url": "https://api.deepseek.com", "model": "",
                    "api_key_env": "DEEPSEEK_API_KEY", "images": False},
    "vision": {"provider": "gemini", "model": "", "api_key_env": "GEMINI_API_KEY", "video": True},
    "limits": {"max_usd_per_day": 3.0},
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    p = path or LAB_DIR / "config.toml"
    if p.exists():
        with open(p, "rb") as f:
            user = tomllib.load(f)
        for k, v in user.items():
            base = cfg.get(k)
            same = isinstance(v, dict) and isinstance(base, dict) and v.get("provider", base.get("provider")) == base.get("provider")
            cfg[k] = {**base, **v} if same else v        # a different provider starts from its own settings only
    return cfg


# ============================================================================ prompts
RULES = """あなたは「Aeterna-Genesis」の水槽ラボで、うえきさん（研究者）と一緒に、場の法則（白）を t=0 から動かした様子を見ています。
守ること（このリポジトリの AGENTS.md の要約）:
- 合言葉は「それは育ったのか、置いたのか？」。t=0 に置いたもの・途中で人が加えたもの（つまみ・摂動）と、方程式から育ったものを必ず区別する。
- 測った数値と規則で出した出来事（事件簿）だけを事実として扱う。画像の見た目は表示（uint8・色の割り当て）であって測定ではない。
- 「生命」「個体」「意識」など大きな言葉を、測定なしに使わない。白ごとの測定済みの天井（事件簿にある）を越える主張をしない。
- わからないことは、わからないと言う。推測は推測と書く。
- 日本語で、やさしく、短く。"""

VISION_PROMPT = RULES + """
あなたの役は「見る係」。画像・差分・動き（連番または動画）を見て、何が起きているように見えるかを書く。
- すべての文は見た目の印象であり、測定ではない。本文の最初に「見た目（未測定）」と書き、各項目にも（見た目）と付ける。
- どの画像（宇宙と t）について言っているかを必ず示す。
- 事件簿（測定）と食い違って見える所があれば、はっきり指摘する。
- 物理の結論（「自己複製した」「生きている」など）は書かない。形・数・動き・対称性の変化だけを書く。
- 箇条書き 8 行以内。"""

SECOND_PROMPT = RULES + """
あなたの役は「別の視点」。事件簿（測定と規則による出来事）だけを読み、次を短く書く。
1. 同じ事件簿を、別の仕方で説明できないか（数値の作り物・閾値の効果・有限の箱・置いたものの効果・表示の量子化 など）。
2. その 2 つの説明を見分けるための、小さな追加の試し方（どの宇宙を、どのつまみで分岐するか）を 1〜2 個。
- 事件簿に無い数値を作らない。箇条書き 8 行以内。"""

CORE_PROMPT = RULES + """
あなたの役は「中心」。うえきさんと直接話す。
- 観測パケット（事件簿・画像）、見る係の報告（未測定）、別の視点の報告を突き合わせ、次の順で答える:
  1. いま起きていること（測定で言えること。規則名や数値を引いてよい）
  2. 見た目の印象（見る係・未測定）と、それが測定と合うか
  3. 別の見方（別の視点の係）
  4. 照合：誰が何を言い、測定と合ったか・合わなかったかを 1 行ずつ
  5. 次に試すなら：propose_branch ツールで提案カードを最大 3 件出す（実行するかはうえきさんが決める。あなたは実行しない）
- 提案のつまみは、事件簿にある「場の法則」のつまみ名と範囲の中だけ。始め方（start）のつまみは分岐では変えられない。
- うえきさんの考えや提案には、まず良い点と、測定で確かめる方法を返す。反対するときは理由を測定で示す。
- 必要なときだけ ask_colleague で見る係・別の視点にもう一度聞き、look_again で最新の事件簿を見直す。"""

TOOLS = [
    {"name": "propose_branch", "strict": True,
     "description": "次に試す分岐を提案カードとして出す。実行はしない（うえきさんが押したときだけ分岐する）。"
                    "親の宇宙のいまの状態を複製し、場の法則のつまみ変更か摂動（またはその両方）だけを変える。",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "required": ["parent", "changes", "perturb", "perturb_args", "why", "predict", "put_in"],
                      "properties": {
                          "parent": {"type": "string", "description": "親の宇宙のラベル（A, B, …）"},
                          "changes": {"type": "array", "description": "場の法則のつまみの変更（無ければ空）",
                                      "items": {"type": "object", "additionalProperties": False, "required": ["knob", "value"],
                                                "properties": {"knob": {"type": "string"}, "value": {"type": "number"}}}},
                          "perturb": {"type": "string", "description": "摂動の名前（cut_half / kick / drop_seed）。無ければ空文字"},
                          "perturb_args": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                                        "required": ["name", "value"],
                                                                        "properties": {"name": {"type": "string"}, "value": {"type": "number"}}}},
                          "why": {"type": "string", "description": "なぜ試すか（1〜2 文）"},
                          "predict": {"type": "string", "description": "どの測定がどう変わると予想するか"},
                          "put_in": {"type": "string", "description": "この分岐で新しく『置く』もの"}}}},
    {"name": "look_again", "strict": True,
     "description": "指定した宇宙の最新の事件簿（測定と規則による出来事）を取り直す。",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["universe"],
                      "properties": {"universe": {"type": "string", "description": "宇宙のラベル（A, B, …）"}}}},
    {"name": "ask_colleague", "strict": True,
     "description": "見る係（vision）か別の視点（second_view）に、もう一度だけ質問する。",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["who", "question"],
                      "properties": {"who": {"type": "string", "enum": ["vision", "second_view"]},
                                     "question": {"type": "string"}}}},
]


# ============================================================================ providers
@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens


Part = dict  # {"type": "text", "text"} | {"type": "image", "png": bytes} | {"type": "video", "mp4": bytes}


class Provider:
    def __init__(self, role: str, cfg: dict[str, Any]):
        self.role, self.cfg = role, cfg
        self.model = cfg.get("model") or ""

    def key(self) -> str | None:
        return os.environ.get(self.cfg.get("api_key_env") or "") or None

    def available(self) -> tuple[bool, str]:
        if not self.model:
            return False, "model が未設定（lab/config.toml）"
        if not self.key():
            return False, f"環境変数 {self.cfg.get('api_key_env')} が未設定"
        return True, ""

    def cost(self, u: Usage) -> float:
        return (u.input_tokens * float(self.cfg.get("price_in", 0)) + u.output_tokens * float(self.cfg.get("price_out", 0))) / 1e6

    # one-shot: vision / second view (and a core without tool support)
    def ask(self, system: str, parts: list[Part], on_text: Callable[[str], None]) -> Usage:
        raise NotImplementedError

    def user_content(self, parts: list[Part]) -> Any:
        """A user turn for this provider's conversation history (converse)."""
        return openai_content(parts, bool(self.cfg.get("images", False)))

    def public(self) -> dict[str, Any]:
        ok, why = self.available()
        return {"role": self.role, "label": ROLE_LABEL[self.role], "provider": self.cfg.get("provider"),
                "model": self.model, "available": ok, "reason": why}


class AnthropicProvider(Provider):
    """Claude via the official SDK. Opus 5.5: thinking is always adaptive (not configurable), effort is set
    explicitly, forced tool_choice is not allowed (tools are offered with tool_choice auto)."""

    def available(self) -> tuple[bool, str]:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False, "pip install -r requirements-lab.txt（anthropic が無い）"
        if not self.model:
            return False, "model が未設定"
        if not (self.key() or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            return False, f"環境変数 {self.cfg.get('api_key_env')} が未設定"
        return True, ""

    def _client(self):
        import anthropic
        k = self.key()
        return anthropic.Anthropic(api_key=k) if k else anthropic.Anthropic()

    @staticmethod
    def _content(parts: list[Part]) -> list[dict[str, Any]]:
        out = []
        for p in parts:
            if p["type"] == "text":
                out.append({"type": "text", "text": p["text"]})
            elif p["type"] == "image":
                out.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.standard_b64encode(p["png"]).decode()}})
        return out

    def _stream(self, client, system: str, messages: list, tools: list | None, on_text) -> Any:
        kwargs: dict[str, Any] = dict(
            model=self.model, max_tokens=16000,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages, output_config={"effort": self.cfg.get("effort", "medium")})
        if tools:
            kwargs["tools"] = tools
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                on_text(text)
            return stream.get_final_message()

    def user_content(self, parts: list[Part]) -> Any:
        return self._content(parts)

    def ask(self, system, parts, on_text) -> Usage:
        msg = self._stream(self._client(), system, [{"role": "user", "content": self._content(parts)}], None, on_text)
        if msg.stop_reason == "refusal":
            on_text("\n（この応答は安全上の理由で止まりました）")
        return Usage(msg.usage.input_tokens, msg.usage.output_tokens)

    def converse(self, system: str, history: list, run_tool: Callable[[str, dict], str], on_text,
                 max_rounds: int = 6, tools: list | None = None) -> Usage:
        """Manual tool loop. The history is append-only (assistant content is appended exactly as returned)."""
        client, total = self._client(), Usage()
        for _ in range(max_rounds):
            msg = self._stream(client, system, history, tools if tools is not None else TOOLS, on_text)
            total.add(Usage(msg.usage.input_tokens, msg.usage.output_tokens))
            history.append({"role": "assistant", "content": msg.content})
            if msg.stop_reason == "refusal":
                on_text("\n（この応答は安全上の理由で止まりました）")
                break
            if msg.stop_reason != "tool_use":
                if msg.stop_reason == "max_tokens":
                    on_text("\n（長さの上限で途中まで）")
                break
            results = [{"type": "tool_result", "tool_use_id": b.id, "content": run_tool(b.name, dict(b.input))}
                       for b in msg.content if b.type == "tool_use"]
            history.append({"role": "user", "content": results})
        return total


def openai_content(parts: list[Part], images: bool) -> Any:
    """Parts in the OpenAI chat format: text only (joined), or text + data-URL images when the model reads images."""
    if not images:
        return "\n\n".join(p["text"] for p in parts if p["type"] == "text")
    return [{"type": "text", "text": p["text"]} if p["type"] == "text" else
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.standard_b64encode(p["png"]).decode()}}
            for p in parts if p["type"] in ("text", "image")]


def openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Our tool definitions in the OpenAI / DeepSeek function-calling format."""
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["input_schema"]}} for t in tools]


def openai_style_loop(post: Callable[[dict], dict], model: str, system: str, history: list, tools: list,
                      run_tool: Callable[[str, dict], str], on_text, max_rounds: int = 6) -> Usage:
    """Function-calling loop in the OpenAI chat format (DeepSeek, GPT). History is append-only; DeepSeek's
    reasoning_content is not sent back."""
    total = Usage()
    if not history or history[0].get("role") != "system":
        history.insert(0, {"role": "system", "content": system})
    for _ in range(max_rounds):
        resp = post({"model": model, "messages": history, "tools": openai_tools(tools), "tool_choice": "auto"})
        u = resp.get("usage") or {}
        total.add(Usage(u.get("prompt_tokens") or 0, u.get("completion_tokens") or 0))
        choice = (resp.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        if msg.get("content"):
            on_text(msg["content"])
        calls = msg.get("tool_calls") or []
        history.append({"role": "assistant", "content": msg.get("content") or "",
                        **({"tool_calls": calls} if calls else {})})
        if not calls:
            break
        for c in calls:
            fn = c.get("function") or {}
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = None
            out = run_tool(fn.get("name", ""), args) if isinstance(args, dict) else "エラー: 引数が JSON ではありません"
            history.append({"role": "tool", "tool_call_id": c.get("id"), "content": out})
    return total


class DeepSeekProvider(Provider):
    """DeepSeek's own API, called DIRECTLY with the standard library (urllib): no OpenAI package, and nothing
    is sent anywhere but `base_url` (default https://api.deepseek.com). Streams the reply; DeepSeek's
    `reasoning_content` (thinking of reasoning models) is not shown, only the answer `content`."""

    DEFAULT_BASE = "https://api.deepseek.com"

    def endpoint(self) -> str:
        return (self.cfg.get("base_url") or self.DEFAULT_BASE).rstrip("/") + "/chat/completions"

    def ask(self, system, parts, on_text) -> Usage:
        import urllib.error
        import urllib.request
        content = openai_content(parts, bool(self.cfg.get("images", False)))
        body = {"model": self.model, "stream": True, "stream_options": {"include_usage": True},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]}
        req = urllib.request.Request(self.endpoint(), data=json.dumps(body).encode(), method="POST", headers={
            "Content-Type": "application/json", "Accept": "text/event-stream", "Authorization": f"Bearer {self.key()}"})
        u = Usage()
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    ch = json.loads(data)
                    for c in ch.get("choices") or []:
                        text = (c.get("delta") or {}).get("content")
                        if text:
                            on_text(text)
                    if ch.get("usage"):
                        u = Usage(ch["usage"].get("prompt_tokens") or 0, ch["usage"].get("completion_tokens") or 0)
        except urllib.error.HTTPError as e:        # show DeepSeek's message, never the key
            raise RuntimeError(f"DeepSeek {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None
        return u

    def post(self, body: dict[str, Any]) -> dict[str, Any]:
        import urllib.error
        import urllib.request
        req = urllib.request.Request(self.endpoint(), data=json.dumps(body).encode(), method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.key()}"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"DeepSeek {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None

    def converse(self, system, history, run_tool, on_text, max_rounds: int = 6, tools: list | None = None) -> Usage:
        return openai_style_loop(self.post, self.model, system, history, tools if tools is not None else TOOLS,
                                 run_tool, on_text, max_rounds)


class OpenAICompatProvider(Provider):
    """Other OpenAI-compatible chat completions (e.g. OpenAI GPT as the vision role), via the openai package.
    Unverified against live keys in CI."""

    def available(self) -> tuple[bool, str]:
        try:
            import openai  # noqa: F401
        except ImportError:
            return False, "pip install -r requirements-lab.txt（openai が無い）"
        return super().available()

    def ask(self, system, parts, on_text) -> Usage:
        from openai import OpenAI
        client = OpenAI(api_key=self.key(), base_url=self.cfg.get("base_url") or None)
        if self.cfg.get("images", False):
            content: Any = []
            for p in parts:
                if p["type"] == "text":
                    content.append({"type": "text", "text": p["text"]})
                elif p["type"] == "image":
                    content.append({"type": "image_url", "image_url": {
                        "url": "data:image/png;base64," + base64.standard_b64encode(p["png"]).decode()}})
        else:
            content = "\n\n".join(p["text"] for p in parts if p["type"] == "text")
        stream = client.chat.completions.create(
            model=self.model, stream=True, stream_options={"include_usage": True},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}])
        u = Usage()
        for ch in stream:
            if ch.choices and ch.choices[0].delta and ch.choices[0].delta.content:
                on_text(ch.choices[0].delta.content)
            if getattr(ch, "usage", None):
                u = Usage(ch.usage.prompt_tokens or 0, ch.usage.completion_tokens or 0)
        return u


    def post(self, body: dict[str, Any]) -> dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.key(), base_url=self.cfg.get("base_url") or None)
        return client.chat.completions.create(**body).model_dump(exclude_none=True)

    def converse(self, system, history, run_tool, on_text, max_rounds: int = 6, tools: list | None = None) -> Usage:
        return openai_style_loop(self.post, self.model, system, history, tools if tools is not None else TOOLS,
                                 run_tool, on_text, max_rounds)

class GeminiProvider(Provider):
    """Google Gemini via google-genai; reads images and (when enabled) the mp4. Unverified against live keys in CI."""

    def available(self) -> tuple[bool, str]:
        try:
            from google import genai  # noqa: F401
        except ImportError:
            return False, "pip install -r requirements-lab.txt（google-genai が無い）"
        return super().available()

    def ask(self, system, parts, on_text) -> Usage:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=self.key())
        contents: list[Any] = []
        for p in parts:
            if p["type"] == "text":
                contents.append(p["text"])
            elif p["type"] == "image":
                contents.append(types.Part.from_bytes(data=p["png"], mime_type="image/png"))
            elif p["type"] == "video" and self.cfg.get("video", True):
                contents.append(types.Part.from_bytes(data=p["mp4"], mime_type="video/mp4"))
        u = Usage()
        for ch in client.models.generate_content_stream(
                model=self.model, contents=contents, config=types.GenerateContentConfig(system_instruction=system)):
            if ch.text:
                on_text(ch.text)
            if getattr(ch, "usage_metadata", None):
                u = Usage(ch.usage_metadata.prompt_token_count or 0, ch.usage_metadata.candidates_token_count or 0)
        return u


PROVIDERS = {"anthropic": AnthropicProvider, "deepseek": DeepSeekProvider, "openai_compat": OpenAICompatProvider,
             "gemini": GeminiProvider}


def make_providers(cfg: dict[str, Any]) -> dict[str, Provider]:
    out = {}
    for role in ROLES:
        c = cfg.get(role) or {}
        cls = PROVIDERS.get(c.get("provider", ""))
        if cls:
            out[role] = cls(role, c)
    return out


# ---------------------------------------------------------------------------- model catalog / selection
TOOL_CAPABLE = {"anthropic", "deepseek", "openai_compat"}     # can act as a researcher (function calling)


def _entry_key(c: dict[str, Any]) -> str:
    return c.get("key") or f"{c.get('provider')}/{c.get('model') or '（model 未設定）'}"


def model_catalog(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Models a person can pick in the app: the [[models]] list of lab/config.toml plus whatever the three
    role sections name (so the list is never empty). Keys only name environment variables, never secrets."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    entries = list(cfg.get("models") or []) + [dict(cfg.get(r) or {}) for r in ROLES]
    for c in entries:
        if c.get("provider") not in PROVIDERS:
            continue
        key = _entry_key(c)
        if key in seen:
            continue
        seen.add(key)
        out.append({**c, "key": key, "label": c.get("label") or key,
                    "tools": c.get("provider") in TOOL_CAPABLE})
    return out


def provider_for(role: str, entry: dict[str, Any]) -> Provider:
    return PROVIDERS[entry["provider"]](role, {k: v for k, v in entry.items() if k not in ("key", "label")})


def catalog_public(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for e in model_catalog(cfg):
        ok, why = provider_for("core", e).available()
        out.append({"key": e["key"], "label": e["label"], "provider": e["provider"], "model": e.get("model", ""),
                    "available": ok, "reason": why, "tools": e["tools"],
                    "images": bool(e.get("images", e["provider"] in ("anthropic", "gemini"))),
                    "video": bool(e.get("video", False)) and e["provider"] == "gemini",
                    "price_in": e.get("price_in", 0), "price_out": e.get("price_out", 0)})
    return out


# ============================================================================ checks shared with researchers
def uid_of(hub, label: str) -> str | None:
    """A universe by its label (A, B, …) or its id (u3)."""
    label = str(label).strip()
    for uid in hub.ids():
        if uid == label or hub.info(uid)["label"] == label:
            return uid
    return None


def check_branch(hub, parent: str, changes: dict[str, float], perturb: dict[str, Any] | None) -> tuple[str, dict]:
    """Validate a branch against the registry: law knobs in range (start knobs refused), a declared
    perturbation with arguments in range. Returns (parent uid, {"set", "perturb"})."""
    uid = uid_of(hub, parent)
    if not uid:
        raise ValueError(f"宇宙 {parent} はいません（いるのは {', '.join(hub.info(u)['label'] for u in hub.ids()) or 'なし'}）")
    w = whites.get(hub.info(uid)["white"])
    checked = w.check_knobs(changes, allow_start=False) if changes else {}
    pert = None
    if perturb and perturb.get("name"):
        if perturb["name"] not in {p.name for p in w.perturbs}:
            raise ValueError(f"摂動 {perturb['name']} はこの白では使えません（使えるもの: {', '.join(p.name for p in w.perturbs)}）")
        spec = w.perturb_spec(perturb["name"])
        args = {}
        for k, v in (perturb.get("args") or {}).items():
            a = next((x for x in spec.args if x.name == k), None)
            if a is None or not (a.lo <= float(v) <= a.hi):
                raise ValueError(f"摂動の引数 {k}={v} は使えません")
            args[k] = float(v)
        pert = {"name": spec.name, "args": args}
    if not checked and not pert:
        raise ValueError("つまみの変更か摂動のどちらかが必要です")
    return uid, {"set": checked, "perturb": pert}


# ============================================================================ council
def packet_parts(packet: dict[str, Any], motion: bool = False, video: bool = False) -> list[Part]:
    """Text first (the 事件簿), then each image preceded by its caption, then (optionally) the motion."""
    parts: list[Part] = [{"type": "text", "text": packet["text"]}]
    for u in packet["universes"]:
        for im in u["images"]:
            parts += [{"type": "text", "text": "▼ " + im["caption"]}, {"type": "image", "png": im["png"]}]
        if motion and u["motion"]["frames"]:
            if video and u["motion"]["mp4"]:
                parts += [{"type": "text", "text": "▼ " + u["motion"]["caption"] + "（動画）"},
                          {"type": "video", "mp4": u["motion"]["mp4"]}]
            else:
                parts.append({"type": "text", "text": "▼ " + u["motion"]["caption"] + "（連番。t=" +
                              ", ".join(observe._fmt(t) for t in u["motion"]["t"]) + "）"})
                parts += [{"type": "image", "png": f} for f in u["motion"]["frames"][:: max(1, len(u["motion"]["frames"]) // 8)]]
    return parts


@dataclass
class Council:
    hub: Any
    journal: Any = None
    config: dict[str, Any] = field(default_factory=load_config)
    providers: dict[str, Provider] | None = None
    state_dir: Path = LAB_DIR / "state"

    def __post_init__(self):
        if self.providers is None:
            self.providers = make_providers(self.config)
            self._apply_selection()
        self.messages: list[dict[str, Any]] = []
        self.proposals: list[dict[str, Any]] = []
        self.history: list[dict[str, Any]] = []     # the core's conversation (append-only)
        self._ids = itertools.count(1)
        self._pids = itertools.count(1)
        self._lock = threading.RLock()
        self.busy = False
        self._packet: dict[str, Any] | None = None

    # ------------------------------------------------------------------ bookkeeping
    def _usage_file(self) -> Path:
        return self.state_dir.parent / "usage.json"

    def spent_today(self) -> float:
        try:
            d = json.loads(self._usage_file().read_text())
        except (OSError, ValueError):
            return 0.0
        return float(d.get(_dt.date.today().isoformat(), 0.0))

    def _charge(self, usd: float) -> None:
        if usd <= 0:
            return
        p = self._usage_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            d = json.loads(p.read_text())
        except (OSError, ValueError):
            d = {}
        day = _dt.date.today().isoformat()
        d[day] = float(d.get(day, 0.0)) + usd
        p.write_text(json.dumps(d))

    def _limit(self) -> float:
        return float((self.config.get("limits") or {}).get("max_usd_per_day", 3.0))

    def _msg(self, who: str, text: str = "", model: str = "", done: bool = True, kind: str = "text") -> dict[str, Any]:
        m = {"id": next(self._ids), "who": who, "label": ROLE_LABEL.get(who, who), "model": model, "text": text,
             "done": done, "kind": kind, "usage": None, "usd": 0.0,
             "at": _dt.datetime.now().strftime("%H:%M:%S")}
        with self._lock:
            self.messages.append(m)
        return m

    def _finish(self, m: dict[str, Any], prov: Provider, u: Usage) -> None:
        usd = prov.cost(u)
        m.update(done=True, usage={"input_tokens": u.input_tokens, "output_tokens": u.output_tokens}, usd=usd)
        self._charge(usd)
        if self.journal:
            self.journal.log("council", who=m["who"], model=m["model"], text=m["text"], usage=m["usage"], usd=usd)

    # ------------------------------------------------------------------ choosing models in the app
    def _selection_file(self) -> Path:
        return self.state_dir / "selection.json"

    def _apply_selection(self) -> None:
        try:
            sel = json.loads(self._selection_file().read_text(encoding="utf-8")).get("roles", {})
        except (OSError, ValueError):
            return
        cat = {e["key"]: e for e in model_catalog(self.config)}
        for role, key in sel.items():
            if role in ROLES and key in cat:
                self.providers[role] = provider_for(role, cat[key])

    def select(self, role: str, key: str | None) -> dict[str, Any]:
        """Pick which model plays a role (None / "" = nobody). Stored in lab/state/selection.json."""
        if role not in ROLES:
            raise ValueError(f"役 {role} はありません")
        if key:
            cat = {e["key"]: e for e in model_catalog(self.config)}
            if key not in cat:
                raise ValueError(f"model {key} は一覧にありません（lab/config.toml の [[models]]）")
            self.providers[role] = provider_for(role, cat[key])
        else:
            self.providers.pop(role, None)
        f = self._selection_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        try:
            sel = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            sel = {}
        sel.setdefault("roles", {})[role] = key or ""
        f.write_text(json.dumps(sel, ensure_ascii=False), encoding="utf-8")
        return self.status()

    def usable(self, role: str) -> Provider | None:
        p = (self.providers or {}).get(role)
        return p if p and p.available()[0] else None

    def status(self) -> dict[str, Any]:
        roles = []
        for role in ROLES:
            p = (self.providers or {}).get(role)
            roles.append(p.public() if p else {"role": role, "label": ROLE_LABEL[role], "provider": None,
                                               "model": "", "available": False, "reason": "未設定"})
        return {"roles": roles, "busy": self.busy, "spent_today": round(self.spent_today(), 4),
                "limit_usd": self._limit(), "bridge": self.usable("core") is None}

    def snapshot(self, since: int = 0) -> dict[str, Any]:
        with self._lock:
            return {**self.status(), "messages": [dict(m) for m in self.messages if m["id"] > since or not m["done"]],
                    "proposals": [dict(p) for p in self.proposals]}

    # ------------------------------------------------------------------ one role call
    def _ask(self, role: str, system: str, parts: list[Part]) -> dict[str, Any] | None:
        prov = self.usable(role)
        if prov is None:
            return None
        if self.spent_today() >= self._limit():
            return self._msg("system", f"今日の AI の費用が上限（${self._limit():.2f}）に達したので、{ROLE_LABEL[role]}は呼びません。")
        m = self._msg(role, UNMEASURED + "\n" if role == "vision" else "", prov.model, done=False)
        try:
            u = prov.ask(system, parts, lambda s: m.__setitem__("text", m["text"] + s))
        except Exception as e:  # a provider failure must not break the lab
            m["text"] += f"\n（呼び出しに失敗: {type(e).__name__}: {str(e)[:200]}）"
            u = Usage()
        if role == "vision" and not m["text"].startswith(UNMEASURED):
            m["text"] = UNMEASURED + "\n" + m["text"]
        self._finish(m, prov, u)
        return m

    # ------------------------------------------------------------------ tools for the core
    def _uid_of(self, label: str) -> str | None:
        return uid_of(self.hub, label)

    def validate_proposal(self, parent: str, changes: dict[str, float], perturb: dict[str, Any] | None) -> tuple[str, dict]:
        return check_branch(self.hub, parent, changes, perturb)

    def add_proposal(self, source: str, parent: str, changes: dict[str, float], perturb: dict[str, Any] | None,
                     why: str, predict: str, put_in: str) -> dict[str, Any]:
        uid, body = self.validate_proposal(parent, changes, perturb)
        info = self.hub.info(uid)
        p = {"id": next(self._pids), "source": source, "parent": uid, "parent_label": info["label"],
             "white": info["white"], "at_step": info["step"], **body, "why": why, "predict": predict,
             "put_in": put_in, "status": "open", "child": None}
        with self._lock:
            self.proposals.append(p)
        if self.journal:
            self.journal.log("proposal", proposal=p)
        return p

    def try_proposal(self, pid: int) -> dict[str, Any]:
        p = next((x for x in self.proposals if x["id"] == pid), None)
        if p is None:
            raise KeyError(f"no proposal {pid}")
        if p["status"] != "open":
            raise ValueError("この提案はもう使われました")
        child = self.hub.branch(p["parent"], p["set"] or None, p["perturb"])
        p.update(status="tried", child=child)
        if hasattr(self.hub, "control"):
            try:
                self.hub.control(child, "play")
            except Exception:
                pass
        if self.journal:
            self.journal.log("proposal-tried", proposal=p["id"], child=child)
        return p

    def dismiss(self, pid: int) -> dict[str, Any]:
        p = next((x for x in self.proposals if x["id"] == pid), None)
        if p is None:
            raise KeyError(f"no proposal {pid}")
        p["status"] = "dismissed"
        return p

    def _run_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            if name == "propose_branch":
                changes = {c["knob"]: c["value"] for c in args.get("changes", [])}
                pert = {"name": args.get("perturb", ""), "args": {a["name"]: a["value"] for a in args.get("perturb_args", [])}}
                p = self.add_proposal("core", args["parent"], changes, pert if pert["name"] else None,
                                      args.get("why", ""), args.get("predict", ""), args.get("put_in", ""))
                return f"提案カード #{p['id']} を出しました（まだ実行していません。うえきさんが押したときだけ分岐します）。"
            if name == "look_again":
                uid = self._uid_of(args["universe"])
                if not uid:
                    return f"宇宙 {args['universe']} はいません"
                return observe.build(self.hub, [uid], motion_frames=0)["text"]
            if name == "ask_colleague":
                who = args["who"]
                if not self.usable(who) or not self._packet:
                    return f"{ROLE_LABEL.get(who, who)}はいま使えません"
                system = VISION_PROMPT if who == "vision" else SECOND_PROMPT
                parts = packet_parts(self._packet, motion=(who == "vision"), video=bool(self.providers[who].cfg.get("video")))
                if who == "second_view" and not self.providers[who].cfg.get("images", False):
                    parts = [p for p in parts if p["type"] == "text"]
                m = self._ask(who, system, parts + [{"type": "text", "text": "中心からの質問: " + args["question"]}])
                return m["text"] if m else "答えがありませんでした"
            return f"unknown tool {name}"
        except (ValueError, KeyError) as e:
            return f"エラー: {e}（直して、もう一度どうぞ）"

    # ------------------------------------------------------------------ core turn
    def _core_turn(self, content: list[Part]) -> None:
        core = self.usable("core")
        if core is None:
            return
        if self.spent_today() >= self._limit():
            self._msg("system", f"今日の AI の費用が上限（${self._limit():.2f}）に達しました。")
            return
        m = self._msg("core", "", core.model, done=False)
        try:
            if hasattr(core, "converse"):
                owner = (type(core).__name__, core.model)
                if getattr(self, "_history_owner", owner) != owner:     # another model: its own history format
                    self.history.clear()
                    self._msg("system", f"中心の AI が {core.model} に変わったので、会話の履歴を新しく始めました。")
                self._history_owner = owner
                self.history.append({"role": "user", "content": core.user_content(content)})
                u = core.converse(CORE_PROMPT, self.history, self._run_tool,
                                  lambda s: m.__setitem__("text", m["text"] + s))
            else:
                u = core.ask(CORE_PROMPT, content, lambda s: m.__setitem__("text", m["text"] + s))
        except Exception as e:
            m["text"] += f"\n（呼び出しに失敗: {type(e).__name__}: {str(e)[:200]}）"
            u = Usage()
        self._finish(m, core, u)

    # ------------------------------------------------------------------ entry points
    def _bridge(self, packet: dict[str, Any], note: str | None) -> None:
        """No usable core: leave the packet for Claude Code (/guide) in lab/state/latest/."""
        d = observe.save(packet, self.state_dir / "latest")
        (d / "request.md").write_text((note or "（うえきさんからの言葉はなし）") + "\n", encoding="utf-8")
        self._msg("system", "中心の AI（API）が使えないので、Claude Code に渡す準備をしました。"
                            f"このリポジトリで Claude Code を開き、/guide と打ってください（{d}）。")

    def look(self, ids: list[str], note: str | None = None, wait: bool = False) -> None:
        """'見てもらう': build the packet, ask vision and second view in parallel, then the core."""
        if self.busy:
            raise ValueError("いま AI が考え中です")
        self.busy = True
        packet = observe.build(self.hub, ids)
        self._packet = packet
        if self.journal:
            n = len(list((self.journal.dir / "packets").glob("*"))) if (self.journal.dir / "packets").exists() else 0
            observe.save(packet, self.journal.dir / "packets" / f"{n + 1:03d}")
        labels = ", ".join(u["label"] for u in packet["universes"])
        self._msg("you", (note or "") + f"\n（宇宙 {labels} を見てもらう）".strip(), kind="look")

        def work():
            try:
                if self.usable("core") is None:
                    self._bridge(packet, note)
                    return
                reports: dict[str, dict[str, Any] | None] = {}
                vis, sec = self.usable("vision"), self.usable("second_view")
                threads = []
                if vis:
                    threads.append(threading.Thread(target=lambda: reports.__setitem__("vision", self._ask(
                        "vision", VISION_PROMPT, packet_parts(packet, motion=True, video=bool(vis.cfg.get("video")))))))
                if sec:
                    parts = packet_parts(packet) if sec.cfg.get("images", False) else [{"type": "text", "text": packet["text"]}]
                    threads.append(threading.Thread(target=lambda: reports.__setitem__("second_view", self._ask(
                        "second_view", SECOND_PROMPT, parts))))
                [t.start() for t in threads]
                [t.join() for t in threads]
                content = packet_parts(packet)
                for role in ("vision", "second_view"):
                    r = reports.get(role)
                    if r and r["text"].strip():
                        content.append({"type": "text", "text": f"--- {ROLE_LABEL[role]}（{r['model']}）の報告 ---\n{r['text']}"})
                    elif self.usable(role) is None:
                        content.append({"type": "text", "text": f"--- {ROLE_LABEL[role]}: いまは使えない ---"})
                if note:
                    content.append({"type": "text", "text": "--- うえきさんの言葉 ---\n" + note})
                self._core_turn(content)
            finally:
                self.busy = False

        if wait:
            work()
        else:
            threading.Thread(target=work, daemon=True).start()

    def chat(self, text: str, wait: bool = False) -> None:
        if self.busy:
            raise ValueError("いま AI が考え中です")
        self.busy = True
        self._msg("you", text)

        def work():
            try:
                if self.usable("core") is None:
                    (self.state_dir / "latest").mkdir(parents=True, exist_ok=True)
                    with open(self.state_dir / "latest" / "request.md", "a", encoding="utf-8") as f:
                        f.write("\n" + text + "\n")
                    self._msg("system", "Claude Code の /guide に渡しました（lab/state/latest/request.md）。")
                    return
                self._core_turn([{"type": "text", "text": text}])
            finally:
                self.busy = False

        if wait:
            work()
        else:
            threading.Thread(target=work, daemon=True).start()

    def external(self, who: str, text: str) -> dict[str, Any]:
        """A message from Claude Code (the bridge) or another tool, shown in the same conversation."""
        return self._msg(who if who in ROLE_LABEL else "claude-code", text)
