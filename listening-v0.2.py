import random
import asyncio
import edge_tts
import pygame
import tempfile
import os
import unicodedata

score = 0
total = 0
VOICE = "ja-JP-NanamiNeural"

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
        return generate_price()
    elif question_type == "time":
        return generate_time()
    elif question_type == "date":
        return generate_date()
    else:
        return generate_percentage()

async def main():
    global score
    global total
    print("\n日本語の聴聞練習へようこそ！")
    print("Type 'q' to quit\n")

    while True:
        question_text, answer = get_question()
        print("\n🔊 聞いてください...")
        await speak(question_text)

        while True:
            user = input("答え (r=repeat, q=quit): ")
            if user.lower() == "q":
                print("\n終わった！")
                print(f"Final Score: {score}/{total}")
                return
            elif user.lower() == "r":
                print("🔊 もう一度...")
                await speak(question_text)
            else:
                break

        total += 1
        user_norm = unicodedata.normalize("NFKC", user.strip()).replace(" ", "")
        answer_norm = unicodedata.normalize("NFKC", answer.strip()).replace(" ", "")

        if user_norm == answer_norm:
            score += 1
            print("✅ 正しい!")
        else:
            print("❌ 間違っています")
            print(f"正しい答え: {answer}")
            print("🔊 もう一度...")
            await speak(question_text)

        print(f"点数: {score}/{total}")

        print("\n終わった！")
        print(f"Final Score: {score}/{total}")

if __name__ == "__main__":
    asyncio.run(main())