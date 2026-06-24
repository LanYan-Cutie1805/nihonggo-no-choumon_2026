import random
import asyncio
import edge_tts
import pygame
import tempfile
import os
import unicodedata
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

score = 0
total = 0
VOICE = "ja-JP-NanamiNeural"
session_start= datetime.now()

stats = {
    "price": {"correct": 0, "total": 0},
    "time": {"correct": 0, "total": 0},
    "date": {"correct": 0, "total": 0},
    "percentage": {"correct": 0, "total": 0}
}

def generate_price():
    value = random.randint(100, 50000)
    text = f"{value:,}円"
    return text, str(value)

def generate_time():
    hour12 = random.randint(1, 12)
    minute = random.choice([0, 15, 30, 45])
    period = random.choice(["午前", "午後"])

    if minute == 0:
        text = f"{period}{hour12}時"
    elif minute == 30:
        text = f"{period}{hour12}時半"
    else:
        text = f"{period}{hour12}時{minute}分"

    if period == "午前":
        if hour12 == 12:
            hour24 = 0
        else:
            hour24 = hour12
    else:  
        if hour12 == 12:
            hour24 = 12
        else:
            hour24 = hour12 + 12
    answer = f"{hour24:02d}:{minute:02d}"
    return text, answer

def generate_date():
    year = random.randint(2024, 2030)
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


async def speak(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        filename = f.name
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    os.remove(filename)

def get_question():
    question_type = random.choice(
        ["price", "time", "date", "percentage"]
    )
    if question_type == "price":
        text, answer = generate_price()
    elif question_type == "time":
        text, answer = generate_time()
    elif question_type == "date":
        text, answer = generate_date()
    else:
        text, answer = generate_percentage()

    return question_type, text, answer

def plot_stats():

    session_end = datetime.now()
    duration = session_end - session_start
    duration_minutes = duration.total_seconds() / 60

    study_date = session_start.strftime("%Y-%m-%d")
    start_time = session_start.strftime("%H:%M")
    end_time = session_end.strftime("%H:%M")

    categories = list(stats.keys())
    correct = [stats[cat]["correct"] for cat in categories]
    wrong = [stats[cat]["total"] - stats[cat]["correct"] for cat in categories]
    percentages = []
    for cat in categories:
        total = stats[cat]["total"]
        if total == 0:
            percentages.append(0)
        else:
            percentages.append(stats[cat]["correct"] / total * 100)

    overall = score / total * 100 if total else 0

    x = np.arange(len(categories))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))

    bars_correct = ax.bar(x - width/2, correct, width, label='Correct', color='green')
    bars_wrong = ax.bar(x + width/2, wrong, width, label='Wrong', color='red')

    for i, pct in enumerate(percentages):
        highest= max(correct[i], wrong[i])
        ax.text(x[i], highest + 0.5, f"{pct:.1f}%", ha='center', fontsize=10, color='black')

    ax.set_xticks(x)
    ax.set_xticklabels(c.capitalize() for c in categories)
    ax.set_ylabel('回答数')
    
    ax.set_title(
        f"日本語の聴聞練習へようこそ - {study_date}\n"
        f"点数: {score}/{total} ({overall:.1f}%)\n"
        f"持続時間: {duration_minutes:.1f} minutes"
    )
    ax.legend()

    plt.tight_layout()

    filename = (
        f"stats_"
        f"{study_date}_"
    )
    plt.savefig(filename, dpi=300)

    plt.show()

async def main():
    global score
    global total
    print("\n日本語の聴聞練習へようこそ！")
    print("Type 'q' to quit\n")

    while True:
        question_type, question_text, answer = get_question()
        print("\n🔊 聞いてください...")
        await speak(question_text)

        while True:
            user = input("答え (r=repeat, q=quit): ")
            if user.lower() == "q":
                print("\n終わった！")
                print(f"点数: {score}/{total}")
                plot_stats()
                return
            elif user.lower() == "r":
                print("🔊 もう一度...")
                await speak(question_text)
            else:
                break

        total += 1
        stats[question_type]["total"] += 1
        user_norm = unicodedata.normalize("NFKC", user.strip()).replace(" ", "")
        answer_norm = unicodedata.normalize("NFKC", answer.strip()).replace(" ", "")

        if user_norm == answer_norm:
            score += 1
            stats[question_type]["correct"] += 1
            print("✅ 正しい!")
        else:
            print("❌ 間違っています")
            print(f"正しい答え: {answer}")
            print("🔊 もう一度...")
            await speak(question_text)


if __name__ == "__main__":
    asyncio.run(main())