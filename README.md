# BitBingo
Welcome to BitBingo, a custom bingo game designed for playing bingo with your best mates at work, home, or anywhere you find yourself considering the crazy things that happen to you.

#### Bingo Screen
<img width="1143" height="612" alt="Bingo Game" src="https://github.com/user-attachments/assets/4ce94f0a-ea92-4a9c-9a54-a27b24006c25" />

## Tech Stack
BitBingo uses the following things under/around/and over the hood:
- Python 3.13
- FastAPI (SSR, Functions)
- Jinja Templating (HTML/CSS)
- DuckDB (persistent binary database)
- System.css (Old apple component styling library)

#### Sign In Screen
<img width="632" height="453" alt="sign in" src="https://github.com/user-attachments/assets/7d81cf81-aac1-4287-a7ab-eda09e40376a" />

## Features
- 3x3 or 4x4 bingo games
- Ability to add custom prompts
- Invites friends with invite links
- Points for winning games, and a leaderboard to see the scores
- A stats screen for bingo game history and player detail lookup
- Time tracking on bingo games
- A hidden minigame

#### Stats Page
<img width="1513" height="654" alt="stats page" src="https://github.com/user-attachments/assets/98f2a526-211c-44a3-8548-4e488b9ae3ab" />

## Possible Future Features
- Public voting on new prompts
  - Someone would submit a prompt and each user would get a single vote for either Yay or Nay. If it's majority Yay the prompt gets auto accepted into the list.
- Show the winning combination when someone wins bingo
- Add a favicon
- Modify the title of the page to include what page you're on. I.e. BitBingo | Stats
- Some security fixes... I won't spoil what those are
- Add the password hashing salt to a const and is defined somewhere useful

#### Admin Page
<img width="1246" height="742" alt="admin page" src="https://github.com/user-attachments/assets/871380f2-3d5d-465d-91c1-2fc715797f9d" />

## Get Started
To run a version of BitBingo locally, you'll need to follow these steps:
1. Clone the repository to a folder of your choosing
2. Create a virtual environment and install the requirements
3. Create `static/prompts.json` from `static/prompts-example.json` with your chosen starting prompts. You may also do this in the app one by one
4. Run the app initially: `python main.py`
5. Login with username `admin` and password `admin`
6. You can change your password from the Profile screen
