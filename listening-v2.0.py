import asyncio
import edge_tts
import random
import tempfile
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import base64

VOICE = "ja-JP-NanamiNeural"
img_folder = Path(r"D:\Raphael second truck\日本\プログラム\img")

def generate_price():
    value = random.randint(100, 99000)
    text = f"{value:,}円"
    return text, str(value)


def generate_time():
    hour12 = random.randint(1, 12)
    minute = random.choice([0, 10, 15, 20, 25, 30, 35, 45, 50, 55])
    period = random.choice(["午前", "午後"])
    if minute == 0:
        text = f"{period}{hour12}時"
    elif minute == 30:
        text = f"{period}{hour12}時半"
    else:
        text = f"{period}{hour12}時{minute}分"
    if period == "午前":
        hour24 = 0 if hour12 == 12 else hour12
    else:
        hour24 = 12 if hour12 == 12 else hour12 + 12
    answer = f"{hour24:02d}:{minute:02d}"
    return text, answer


def generate_date():
    year = random.randint(2000, 2030)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    text = f"{year}年{month}月{day}日"
    answer = f"{year:04d}-{month:02d}-{day:02d}"
    return text, answer


def generate_percentage():
    value = round(random.uniform(1, 100), 1)
    if value.is_integer():
        value = int(value)
    text = f"{value}%"
    answer = str(value)
    return text, answer


def get_question():
    question_type = random.choice(["price", "time", "date", "percentage"])
    if question_type == "price":
        text, answer = generate_price()
    elif question_type == "time":
        text, answer = generate_time()
    elif question_type == "date":
        text, answer = generate_date()
    else:
        text, answer = generate_percentage()
    return question_type, text, answer


async def text_to_audio_bytes(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        filename = tmp.name
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    with open(filename, "rb") as f:
        audio_bytes = f.read()
    os.remove(filename)
    return audio_bytes


def generate_audio(text: str) -> bytes:
    return asyncio.run(text_to_audio_bytes(text))


def load_image_bytes(question_type: str, img_folder: Path | str | None = None) -> bytes | None:
    base = Path(img_folder) if img_folder else (Path(__file__).parent / "img")
    if not base.exists() or not base.is_dir():
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        exact = base / f"{question_type}.{ext}"
        if exact.exists():
            path = exact
            break
    else:
        candidates = list(base.glob(f"{question_type}*.*"))
        if not candidates:
            candidates = list(base.glob("*.*"))
            if not candidates:
                return None
        path = random.choice(candidates)
    img = Image.open(path).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def normalize_answer(text: str) -> str:
    return unicodedata.normalize("NFKC", text.strip()).replace(" ", "")


def initialize_state():
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "total" not in st.session_state:
        st.session_state.total = 0
    if "stats" not in st.session_state:
        st.session_state.stats = {
            "price": {"correct": 0, "total": 0},
            "time": {"correct": 0, "total": 0},
            "date": {"correct": 0, "total": 0},
            "percentage": {"correct": 0, "total": 0},
        }
    if "history" not in st.session_state:
        st.session_state.history = []
    if "question" not in st.session_state:
        st.session_state.question = None
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()
    if "finished" not in st.session_state:
        st.session_state.finished = False
    if "skip_next_autoplay" not in st.session_state:
        st.session_state.skip_next_autoplay = False


def new_question(img_folder: Path | str | None = None):
    q_type, q_text, q_answer = get_question()
    audio_bytes = generate_audio(q_text)
    image_bytes = load_image_bytes(q_type, img_folder=img_folder)

    st.session_state.question = {
        "type": q_type,
        "text": q_text,
        "answer": q_answer,
        "audio": audio_bytes,
        "image": image_bytes,
    }

    should_autoplay = not st.session_state.skip_next_autoplay
    st.session_state.skip_next_autoplay = False

    st.session_state.history.append(
        {
            "role": "assistant",
            "content": f"🔊 聞いてください:",
            "audio": audio_bytes,
            "image": image_bytes,
            "play_audio": should_autoplay,
        }
    )

def record_result(question_type: str, correct: bool):
    st.session_state.total += 1
    st.session_state.stats[question_type]["total"] += 1
    if correct:
        st.session_state.score += 1
        st.session_state.stats[question_type]["correct"] += 1


def show_stats():
    duration = datetime.now() - st.session_state.session_start
    duration_minutes = duration.total_seconds() / 60
    overall = (
        st.session_state.score / st.session_state.total * 100
        if st.session_state.total > 0
        else 0
    )
    st.write("## 統計 (Statistics Result)")
    st.write(f"- 正解 (Correct Answers): {st.session_state.score}/{st.session_state.total}")
    st.write(f"- 正答率 (Accuracy): {overall:.1f}%")
    st.write(f"- 所要時間 (Time Spent): {duration_minutes:.1f} 分")

    categories = list(st.session_state.stats.keys())
    correct = [st.session_state.stats[cat]["correct"] for cat in categories]
    wrong = [st.session_state.stats[cat]["total"] - st.session_state.stats[cat]["correct"] for cat in categories]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(categories))
    width = 0.35
    ax.bar(x - width / 2, correct, width, label="Correct", color="green")
    ax.bar(x + width / 2, wrong, width, label="Wrong", color="red")
    ax.set_xticks(x)
    ax.set_xticklabels([cat.capitalize() for cat in categories])
    ax.set_ylabel("Count")
    ax.set_title("Question Performance")
    ax.legend()
    st.pyplot(fig)


def reset_quiz(img_folder: Path | str | None = None):
    for key in ["score", "total", "stats", "history", "question", "session_start", "finished"]:
        if key in st.session_state:
            del st.session_state[key]
    initialize_state()
    new_question(img_folder=img_folder)


def main():
    st.set_page_config(page_title="Japanese Listening Quiz", layout="centered")
    st.title("🎋日本語の聴聞練習へようこそ！")
    st.write("音声で聞いて、答えを入力してください。チャット形式で進行します。")
    st.write("Listen to the audio and enter your answer in the chatbox. ")

    img_folder = Path(__file__).parent / "img"

    initialize_state()
    if st.button("クイズを最初からやり直す (Restart Quiz)"):
        reset_quiz(img_folder= img_folder)
    if st.session_state.question is None:
        new_question(img_folder=img_folder)
    if st.session_state.finished:
        show_stats()
        return

    with st.sidebar:
        st.header("スコア (Score)")
        st.metric("正解", f"{st.session_state.score}/{st.session_state.total}")
        if st.session_state.total > 0:
            rate = st.session_state.score / st.session_state.total * 100
            st.metric("正答率", f"{rate:.1f}%")
        st.button("クイズ終了", on_click=lambda: st.session_state.__setitem__("finished", True))

    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("image"):
                st.image(message["image"], width=120)
            if message.get("audio"):
                audio_b64 = base64.b64encode(message["audio"]).decode("utf-8")
                autoplay_attr = "autoplay" if message.get("play_audio", True) else ""
                st.markdown(
                    f"<audio controls {autoplay_attr}><source src='data:audio/mp3;base64,{audio_b64}' type='audio/mp3'></audio>",
                    unsafe_allow_html=True,
                )

    answer = st.chat_input("答えを入力してください (Answer here / r=repeat / q=quit)")
    if answer:
        answer_lower = answer.strip().lower()
        if answer_lower == "r":
            st.session_state.history.append({"role": "user", "content": "🔄 r (repeat)"})
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "content": "🔊 もう一度...",
                    "audio": st.session_state.question["audio"],
                    "play_audio": True,
                }
            )
            st.rerun()
        elif answer_lower == "q":
            st.session_state.history.append({"role": "user", "content": "🛑 q (quit)"})
            st.session_state.finished = True
            st.rerun()
        else:
            st.session_state.history.append({"role": "user", "content": answer})
            question = st.session_state.question
            user_norm = normalize_answer(answer)
            answer_norm = normalize_answer(question["answer"])
            if user_norm == answer_norm:
                record_result(question["type"], True)
                st.session_state.history.append(
                    {
                        "role": "assistant",
                        "content": f"✅ 正しい! 答え: {question['answer']}",
                    }
                )
            else:
                record_result(question["type"], False)
                st.session_state.skip_next_autoplay = True
                st.session_state.history.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"❌ 間違っています。正しい答え: {question['answer']}\n\n"
                        ),
                        "audio": question["audio"],
                        "play_audio": True,
                    }
                )
            new_question(img_folder=img_folder)
            st.rerun()

if __name__ == "__main__":
    main()