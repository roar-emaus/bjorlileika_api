import csv
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from io import StringIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, PositiveInt, ValidationError, constr

### TYPES


class Game(BaseModel):
    name: constr(
        min_length=2, max_length=50
    )  # Ensuring game name is between 2 to 50 characters
    scores: Dict[str, PositiveInt]  # Ensuring scores are positive integers


class BjorliGame(BaseModel):
    date: str = Field(
        ..., description="Date in format YYYY-MM", pattern="^\d{4}-\d{2}$"
    )
    locked: bool
    games: List[Game]
    players: List[
        constr(min_length=1, max_length=50)
    ]  # Ensuring player names are between 1 to 50 characters


class DateQuery(BaseModel):
    date: str = Field(..., pattern="^\d{4}-\d{2}$")


### UTIL FUNCTIONS


def get_locked_games(data_path: Path) -> List[BjorliGame]:
    all_dates = []
    for file_path in get_all_game_paths(data_path):
        all_dates.append(csv_to_bjorligame(file_path))
    return all_dates


def get_newest_version_path(directory_path: Path) -> Optional[Path]:
    matching_files = list(directory_path.glob("*.csv"))
    if not matching_files:
        return None
    newest_file = max(matching_files, key=lambda x: int(x.stem.split("_")[-1]))
    return newest_file


def get_all_game_paths(data_path: Path) -> List[Path]:
    return [filename for filename in data_path.iterdir() if filename.match("*.csv")]


def csv_to_bjorligame(file_path: Path) -> BjorliGame:
    game_names, players_scores = parse_csv(file_path)
    date = extract_date_from_filename(file_path)
    games = construct_games(game_names, players_scores)
    locked = False

    if "locked" in str(file_path):
        locked = True
    return BjorliGame(
        date=date, locked=locked, games=games, players=list(players_scores.keys())
    )


def parse_csv(file_path: Path) -> (List[str], Dict[str, List[int]]):
    print(file_path)
    with open(file_path, "r") as score_file:
        csv_reader = csv.reader(score_file)

        game_names = next(csv_reader)[1:]

        players_scores = {}
        for row in csv_reader:
            player_name = row[0]
            scores = list(map(int, row[1:]))
            players_scores[player_name] = scores

    return game_names, players_scores


def extract_date_from_filename(file_path: Path) -> str:
    new_file_name = file_path.stem.replace("_", "-")
    if split_name := new_file_name.split("-"):
        return "-".join(split_name[:2])
    return new_file_name


def construct_games(
    game_names: List[str], players_scores: Dict[str, List[int]]
) -> List[Game]:
    games = []

    for game_index, game_name in enumerate(game_names):
        scores = {
            player: scores[game_index] for player, scores in players_scores.items()
        }
        games.append(Game(name=game_name, scores=scores))

    return games


def is_game_locked(date: str) -> bool:
    games = DATA_STORAGE["games"].get(date)
    if not games:
        return False
    latest_game = games[-1]
    latest_game_instance = BjorliGame.model_validate_json(latest_game)
    return latest_game_instance.locked


def bjorligame_to_csv(bjorli_game: BjorliGame) -> str:
    # Construct CSV data
    header = ["Player"] + [game.name for game in bjorli_game.games]

    rows = []
    for player in bjorli_game.players:
        row = [player]
        for game in bjorli_game.games:
            row.append(game.scores.get(player, 0))  # Default score to 0 if not present
        rows.append(row)

    # Convert rows to CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)
    
    return output.getvalue()

def save_bjorligame_to_csv(bjorli_game: BjorliGame, save_path: Path):
    # Generate filename with the date and a UNIX timestamp
    filename = f"{bjorli_game.date.replace('-','_')}_{int(time.time())}.csv"
    file_path = save_path / filename

    # Construct CSV data
    header = ["Player"] + [game.name for game in bjorli_game.games]

    rows = []
    for player in bjorli_game.players:
        row = [player]
        for game in bjorli_game.games:
            row.append(game.scores.get(player, 0))  # Default score to 0 if not present
        rows.append(row)
    # Write to CSV file
    with open(file_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)


api = FastAPI(title="API")
origins = ["*"]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="main app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This will store our in-memory data

DATA_STORAGE = {"dates": [], "games": {}, "latest_date": None}


@api.get("/date/")
async def root() -> BjorliGame:
    return BjorliGame(
        date="2023-01",
        locked=False,
        games=[Game(name="No name", scores={"No name": 1})],
        players=["No name"],
    )


@api.get("/date/{date}")
async def get_date_data(date: str) -> BjorliGame:
    try:
        validated_date = DateQuery(date=date)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    games = DATA_STORAGE["games"].get(validated_date.date)

    if not games:
        return BjorliGame(
            date="2023-01",
            locked=False,
            games=[Game(name="No name", scores={"No name": 1})],
            players=["No name"],
        )
    latest_game = games[-1]
    return BjorliGame.model_validate_json(latest_game)


@api.get("/dates")
async def get_dates() -> List[str]:
    all_dates = DATA_STORAGE["dates"]
    print(all_dates)
    return sorted(list(set(date for date in all_dates)))[::-1]

@api.get("/csv/{date}")
async def get_csv(date: str) -> str:
    try:
        validated_date = DateQuery(date=date)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    games = DATA_STORAGE["games"].get(validated_date.date)

    if not games:
        return ""
    latest_game = games[-1]
    latest_game_instance = BjorliGame.model_validate_json(latest_game)
    return bjorligame_to_csv(latest_game_instance)

@api.post("/game")
async def add_game(game: BjorliGame):
    print(game)
    if is_game_locked(game.date):
        print("Cannot modify a locked game")
        raise HTTPException(status_code=400, detail="Cannot modify a locked game")
    game_data = game.model_dump_json()
    DATA_STORAGE["games"].setdefault(game.date, []).append(game_data)
    DATA_STORAGE["dates"].append(game.date)
    DATA_STORAGE["latest_date"] = game.date

    save_bjorligame_to_csv(game, Path(os.environ.get("DATA_PATH", "")))

    return {"status": "success", "message": "Game modified successfully"}


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


app.mount("/api", api, name="api")
app.mount("/", SPAStaticFiles(directory="project/dist", html=True), name="app")


@app.on_event("startup")
async def load_data_on_startup():
    locked_path = Path(os.environ.get("DATA_PATH", "")) / "locked"
    all_locked_games = get_locked_games(locked_path)
    for game in all_locked_games:
        game_data = game.model_dump_json()
        DATA_STORAGE["games"].setdefault(game.date, []).append(game_data)
        DATA_STORAGE["dates"].append(game.date)
        DATA_STORAGE["latest_date"] = game.date

    newest_file_path = get_newest_version_path(locked_path.parent)
    editable_bjorligame = csv_to_bjorligame(newest_file_path)
    game_data = editable_bjorligame.model_dump_json()
    DATA_STORAGE["games"].setdefault(editable_bjorligame.date, []).append(game_data)
    DATA_STORAGE["dates"].append(editable_bjorligame.date)
    DATA_STORAGE["latest_date"] = editable_bjorligame.date


if __name__ == "__main__":
    import argparse

    import uvicorn

    # Initialize the argument parser
    parser = argparse.ArgumentParser(
        description="FastAPI App with Command-Line Arguments"
    )
    parser.add_argument("--data_path", default=None, help="The path of the data folder")
    args = parser.parse_args()
    os.environ["DATA_PATH"] = args.data_path
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
