import sqlite3
import logging
from pathlib import Path
from pydantic import BaseModel, Field 
import functools


logger = logging.getLogger(__name__)


class Player(BaseModel):
    uid: int | None = Field(default=None)
    name: str

    @classmethod
    def from_tuple(cls, tpl):
        return cls(**{k: v for k, v in zip(cls.__fields__.keys(), tpl)})


class Game(BaseModel):
    uid: int | None = Field(default=None)
    name: str
    rules: str | None
    date: str
    
    @classmethod
    def from_tuple(cls, tpl):
        return cls(**{k: v for k, v in zip(cls.__fields__.keys(), tpl)})


def db_start_up(db_path: Path) -> sqlite3.Connection:
    logger.debug(f"Opening database on path {db_path}")
    con = sqlite3.connect(db_path)
    con.set_trace_callback(logger.debug)
    return con


def create_tables(con: sqlite3.Connection):
    logger.debug("Creating tables if they do not exists")
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

def add_player(con: sqlite3.Connection, player: Player) -> Player:
    logger.debug(f"Trying to add player: {player}")
    cur = con.cursor()
    
    cur.execute("SELECT * FROM Players WHERE name = ?", (player.name,))
    existing_player = cur.fetchone()
    
    if existing_player:
        stored_player = Player.from_tuple(existing_player)
        logger.debug(f"Player with name {stored_player.name} already exists")
    else:
        logger.debug(f"Adding player {player}")
        cur.execute("INSERT INTO Players (name) VALUES (?)", (player.name,))
        con.commit()
        uid = cur.lastrowid
        
        cur.execute("SELECT * FROM Players WHERE id = ?", (uid,))
        row = cur.fetchone()
        stored_player = Player.from_tuple(row)
    
    return stored_player


def add_game(con: sqlite3.Connection, game: Game) -> Game:
    logger.debug(f"Trying to add game: {game}")
    cur = con.cursor()

    cur.execute("SELECT * FROM Games WHERE (name, date) = (?, ?)", (game.name, game.date))
    existing_game = cur.fetchone()

    if existing_game:
        stored_game = Game.from_tuple(existing_game)
        logger.debug(f"Game with name {stored_game.name} and date {stored_game.date} already exists")
    else:
        logger.debug(f"Adding game {game}")
        cur.execute(
            """INSERT INTO Games (name, rules, date) VALUES (?, ?, ?)""",
            (game.name, game.rules, game.date)
        )
        con.commit()
        uid = cur.lastrowid

        cur.execute("SELECT * FROM Games WHERE id = ?", (uid, ))
        row = cur.fetchone()
        stored_game = Game.from_tuple(row)
     
    return stored_game


def add_point(con: sqlite3.Connection, player: Player, game: Game, point: int):
    logger.debug(f"Trying to add point {point} to game {game} for player {player}")
    cur = con.cursor()
    cur.execute("SELECT * FROM Games WHERE (name, date) = (?, ?)", (game.name, game.date))
    game_row = cur.fetchone()
    if game_row:
        stored_game = Game.from_tuple(game_row)
    else:
        raise RuntimeError(f"The game ({game}) does not exist in the database")

    cur.execute("SELECT * FROM Players WHERE name = (?)", (player.name, ))
    player_row = cur.fetchone()
    if player_row:
        stored_player = Player.from_tuple(player_row)
    else:
        raise RuntimeError(f"The player ({player}) does not exist in the database")

    cur.execute(
            "INSERT INTO Points (game_id, player_id, point) VALUES (?, ?, ?)",
            (stored_game.uid, stored_player.uid, point)
    )

    con.commit()


if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)
    db_path = Path.cwd()/"sqlitedb.db"
    con = db_start_up(db_path)
    create_tables(con)
    player = Player(name="Rotte")
    game = Game(name="Løping", rules=None, date="2024-04")
    stored_player = add_player(con, player)
    stored_game = add_game(con, game)
    add_point(con, player, game, 1000)
    game2 = Game(name="Svømming", rules=None, date="2024-04")
    add_point(con, player, game2, 100)
    con.close()


