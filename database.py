import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT,
                user_id INTEGER,
                username TEXT,
                text TEXT,
                is_anonymous BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                wordle_games INTEGER DEFAULT 0,
                wordle_wins INTEGER DEFAULT 0,
                wordle_streak INTEGER DEFAULT 0,
                wordle_max_streak INTEGER DEFAULT 0,
                wordle_guesses TEXT DEFAULT '{"1":0,"2":0,"3":0,"4":0,"5":0,"6":0}',
                quiz_games INTEGER DEFAULT 0,
                quiz_correct INTEGER DEFAULT 0,
                quiz_total INTEGER DEFAULT 0,
                quiz_best INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

# ---- ФУНКЦИИ ДЛЯ СТАТИСТИКИ ----
def get_user_stats(user_id):
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        else:
            # Создаём запись по умолчанию
            conn.execute(
                "INSERT INTO user_stats (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            return {
                "user_id": user_id,
                "wordle_games": 0,
                "wordle_wins": 0,
                "wordle_streak": 0,
                "wordle_max_streak": 0,
                "wordle_guesses": '{"1":0,"2":0,"3":0,"4":0,"5":0,"6":0}',
                "quiz_games": 0,
                "quiz_correct": 0,
                "quiz_total": 0,
                "quiz_best": 0
            }

def update_wordle_stats(user_id, won, guesses):
    stats = get_user_stats(user_id)
    stats["wordle_games"] += 1
    if won:
        stats["wordle_wins"] += 1
        stats["wordle_streak"] += 1
        if stats["wordle_streak"] > stats["wordle_max_streak"]:
            stats["wordle_max_streak"] = stats["wordle_streak"]
        # Обновляем распределение попыток
        guesses_dict = json.loads(stats["wordle_guesses"])
        guesses_dict[str(guesses)] = guesses_dict.get(str(guesses), 0) + 1
        stats["wordle_guesses"] = json.dumps(guesses_dict)
    else:
        stats["wordle_streak"] = 0

    with get_db() as conn:
        conn.execute(
            """UPDATE user_stats SET
                wordle_games = ?,
                wordle_wins = ?,
                wordle_streak = ?,
                wordle_max_streak = ?,
                wordle_guesses = ?
               WHERE user_id = ?""",
            (stats["wordle_games"], stats["wordle_wins"], stats["wordle_streak"],
             stats["wordle_max_streak"], stats["wordle_guesses"], user_id)
        )
        conn.commit()

def update_quiz_stats(user_id, correct, total):
    stats = get_user_stats(user_id)
    stats["quiz_games"] += 1
    stats["quiz_correct"] += correct
    stats["quiz_total"] += total
    if correct > stats["quiz_best"]:
        stats["quiz_best"] = correct

    with get_db() as conn:
        conn.execute(
            """UPDATE user_stats SET
                quiz_games = ?,
                quiz_correct = ?,
                quiz_total = ?,
                quiz_best = ?
               WHERE user_id = ?""",
            (stats["quiz_games"], stats["quiz_correct"], stats["quiz_total"],
             stats["quiz_best"], user_id)
        )
        conn.commit()
