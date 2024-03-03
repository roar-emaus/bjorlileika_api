import sqlite3
from pathlib import Path
from pydantic import BaseModel, Field
import functools


class Player(BaseModel):
    uid: int | None = Field(default=None)
    name: str


class Game(BaseModel):
    uid: int | None = Field(default=None)
    name: str
    rules: str | None
    date: str



def db_start_up(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    return con


def create_tables(con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS Players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """
    )
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS Games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rules TEXT,
        date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS Points (
        game_id INTEGER,
        player_id INTEGER,
        point INTEGER,
        FOREIGN KEY (game_id) REFERENCES Games(id),
        FOREIGN KEY (player_id) REFERENCES Players(id)    
    )
    """
    )
    
    con.commit()


def add_player(con: sqlite3.Connection, player_name: str) -> Player:
    player = Player(name=player_name)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO Players (name) VALUES (?)", 
        (player.name, )
    )
    con.commit()
    return player


def add_game(con: sqlite3.Connection, name: str, rules: str | None, date: str) -> Game:
    game = Game(name=name, rules=rules, date=date)
    cur = con.cursor()
    cur.execute(
        """INSERT INTO Games (name, rules, date) VALUES (?, ?, ?)""",
        (game.name, game.rules, game.date)
    )
    con.commit()
    uid = cur.lastrowid
    cur.execute("SELECT * FROM Games WHERE id = ?", (uid, ))
    row = cur.fetchone()
    game = Game(*row)
     
    print(row)
    return game


#def get_game(con: sqlite3.Connection, game: Game) ->:

if __name__=="__main__":
    db_path = Path.cwd()/"sqlitedb.db"
    con = db_start_up(db_path)
    create_tables(con)
    add_player(con, "lala")
    add_game(con, name="lili", rules=None, date="2022-04")
    con.close()


