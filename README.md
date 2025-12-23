# BitBingo
Welcome to BitBingo, a custom bingo game designed for playing bingo with your best mates at work, home, or anywhere you find yourself considering the crazy things that happen to you.

## Tech Stack
BitBingo uses the following things under/around/and over the hood:
- Python 3.13
- FastAPI (SSR, Functions)
- Jinja Templating (HTML/CSS)
- DuckDB (persistent binary database)
- System.css (Old apple component styling library)
## Features
- 3x3 or 4x4 bingo games
- Ability to add custom prompts
- Invites friends with invite links
- Points for winning games, and a leaderboard to see the scores
- A stats screen for bingo game history and player detail lookup
- Time tracking on bingo games
- A hidden minigame
## Possible Future Features
- Public voting on new prompts
  - Someone would submit a prompt and each user would get a single vote for either Yay or Nay. If it's majority Yay the prompt gets auto accepted into the list.
- Show the winning combination when someone wins bingo
- Add a favicon
- Modify the title of the page to include what page you're on. I.e. BitBingo | Stats
- Some security fixes... I won't spoil what those are
- Add the password hashing salt to a const and is defined somewhere useful