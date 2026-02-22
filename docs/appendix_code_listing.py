"""
Приложение А. Единый листинг программного кода (прототип)
Проект: Цифровой аватар Ю.А. Гагарина

Назначение файла:
- дать рецензенту и разработчику целостное представление о внутреннем устройстве
  пайплайна в одном файле;
- показать связи между компонентами ASR -> LLM -> TTS -> Audio2Face;
- упростить перенос и модификацию проекта для учебных демонстраций.

Важно:
- файл демонстрационный и может требовать настройки API-ключей, адресов сервисов
  и установки зависимостей;
- архитектура соответствует описанию в conference_work_text.md.
"""

from __future__ import annotations

import io
import json
import queue
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional

import requests


# =========================
# 1. Модели данных
# =========================


@dataclass
class AudioChunk:
    data: bytes
    sample_rate: int
    timestamp: float


@dataclass
class Message:
    role: str
    content: str
    timestamp: float


@dataclass
class SessionEvent:
    event_type: str
    payload: dict
    timestamp: float


class SessionState(str, Enum):
    IDLE = "Idle"
    LISTENING = "Listening"
    THINKING = "Thinking"
    SPEAKING = "Speaking"


# =========================
# 2. Конфигурация
# =========================


@dataclass
class AppConfig:
    openai_api_key: str
    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    a2f_push_url: str
    llm_model: str = "gpt-4.1-mini"
    max_history_messages: int = 12
    log_path: str = "session_log.jsonl"


# =========================
# 3. ASR адаптер (демо)
# =========================


class ASRAdapter:
    """Преобразование аудио в текст.

    В реальном проекте здесь подключается Whisper/Streaming ASR.
    """

    def transcribe(self, audio_chunk: AudioChunk) -> str:
        # Демо-режим: в production должен быть вызов реального ASR
        # Сложность обработки входного окна: O(n), где n — число сэмплов.
        if not audio_chunk.data:
            return ""
        return "[распознанный текст пользователя]"


# =========================
# 4. Ядро диалога (LLM)
# =========================


class PromptBuilder:
    SYSTEM_PROMPT = (
        "Ты — цифровой аватар Юрия Алексеевича Гагарина для образовательных диалогов. "
        "Отвечай уважительно, кратко и фактологично, избегай выдуманных фактов. "
        "Если информации недостаточно, честно сообщай об этом."
    )

    def build_messages(self, history: List[Message], user_text: str, limit: int) -> list[dict]:
        # Ограничиваем историю, чтобы контролировать стоимость и задержку
        trimmed = history[-limit:]
        result = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        result.extend({"role": m.role, "content": m.content} for m in trimmed)
        result.append({"role": "user", "content": user_text})
        return result


class LLMAdapter:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"

    def generate_reply(self, messages: list[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 220,
        }
        response = requests.post(self.url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class DialogCore:
    def __init__(self, prompt_builder: PromptBuilder, llm: LLMAdapter, history_limit: int):
        self.prompt_builder = prompt_builder
        self.llm = llm
        self.history_limit = history_limit

    def generate_reply(self, user_text: str, history: List[Message]) -> str:
        messages = self.prompt_builder.build_messages(history, user_text, self.history_limit)
        # Для self-attention оценка шага декодирования ~ O(m^2), m — длина контекста
        return self.llm.generate_reply(messages)


# =========================
# 5. TTS (ElevenLabs)
# =========================


class TTSService:
    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    def synthesize(self, text: str) -> bytes:
        # Практическая оценка ~ O(k), где k — длина текста
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.content


# =========================
# 6. Мост к Audio2Face
# =========================


class AnimationBridge:
    def __init__(self, a2f_push_url: str):
        self.a2f_push_url = a2f_push_url

    def push_audio_to_a2f(self, audio_buffer: bytes) -> None:
        # Оценка ~ O(p), где p — число аудиофреймов
        files = {
            "file": ("reply.mp3", io.BytesIO(audio_buffer), "audio/mpeg"),
        }
        response = requests.post(self.a2f_push_url, files=files, timeout=60)
        response.raise_for_status()


# =========================
# 7. Журналирование
# =========================


class JsonlLogger:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: SessionEvent) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


# =========================
# 8. Контроллер сессии
# =========================


class SessionController:
    def __init__(
        self,
        asr: ASRAdapter,
        dialog_core: DialogCore,
        tts: TTSService,
        animation: AnimationBridge,
        logger: JsonlLogger,
    ):
        self.asr = asr
        self.dialog_core = dialog_core
        self.tts = tts
        self.animation = animation
        self.logger = logger

        self.state: SessionState = SessionState.IDLE
        self.audio_queue: queue.Queue[AudioChunk] = queue.Queue()
        self.history: List[Message] = []

    def _set_state(self, state: SessionState) -> None:
        self.state = state
        self.logger.log(SessionEvent("state_changed", {"state": state.value}, time.time()))

    def push_audio_chunk(self, data: bytes, sample_rate: int = 16000) -> None:
        chunk = AudioChunk(data=data, sample_rate=sample_rate, timestamp=time.time())
        self.audio_queue.put(chunk)

    def run_once(self) -> Optional[str]:
        if self.audio_queue.empty():
            return None

        self._set_state(SessionState.LISTENING)
        audio_chunk = self.audio_queue.get()
        user_text = self.asr.transcribe(audio_chunk).strip()
        if not user_text:
            self.logger.log(SessionEvent("empty_transcript", {}, time.time()))
            return None

        self.history.append(Message(role="user", content=user_text, timestamp=time.time()))
        self.logger.log(SessionEvent("user_text", {"text": user_text}, time.time()))

        self._set_state(SessionState.THINKING)
        reply_text = self.dialog_core.generate_reply(user_text, self.history)
        self.history.append(Message(role="assistant", content=reply_text, timestamp=time.time()))
        self.logger.log(SessionEvent("assistant_text", {"text": reply_text}, time.time()))

        self._set_state(SessionState.SPEAKING)
        audio_reply = self.tts.synthesize(reply_text)
        self.animation.push_audio_to_a2f(audio_reply)
        self.logger.log(SessionEvent("audio_sent_to_a2f", {"bytes": len(audio_reply)}, time.time()))

        self._set_state(SessionState.LISTENING)
        return reply_text


# =========================
# 9. Сборка приложения
# =========================


def build_app(config: AppConfig) -> SessionController:
    asr = ASRAdapter()
    prompt_builder = PromptBuilder()
    llm = LLMAdapter(api_key=config.openai_api_key, model=config.llm_model)
    dialog = DialogCore(prompt_builder=prompt_builder, llm=llm, history_limit=config.max_history_messages)
    tts = TTSService(api_key=config.elevenlabs_api_key, voice_id=config.elevenlabs_voice_id)
    animation = AnimationBridge(a2f_push_url=config.a2f_push_url)
    logger = JsonlLogger(path=config.log_path)

    return SessionController(
        asr=asr,
        dialog_core=dialog,
        tts=tts,
        animation=animation,
        logger=logger,
    )


if __name__ == "__main__":
    # Пример инициализации (значения заменить на рабочие)
    cfg = AppConfig(
        openai_api_key="YOUR_OPENAI_API_KEY",
        elevenlabs_api_key="YOUR_ELEVENLABS_API_KEY",
        elevenlabs_voice_id="YOUR_VOICE_ID",
        a2f_push_url="http://localhost:8011/audio2face/push_audio",
        log_path="docs/session_log.jsonl",
    )

    app = build_app(cfg)

    # Демонстрация: имитация одного аудиочанка
    app.push_audio_chunk(data=b"fake audio bytes for demo")
    answer = app.run_once()
    print("Ответ аватара:", answer)
