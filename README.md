Nathan Chess Engine

A Python-based chess engine with a web interface built using Flask, HTML, CSS, and JavaScript.
This project implements algorithms such as minimax which is optimized with alpha-beta pruning.

Features

* Complete chess board setup with move logic
* Chess engine built from scratch
* Minimax search with alpha-beta pruning
* Custom evaluation function
* Flask-based web UI to play against the engine

How It Works

The engine evaluates positions using a heuristic scoring system and explores possible moves using a depth-limited minimax algorithm. 
Alpha-beta pruning is used to reduce the number of positions evaluated therefore optimizing the running time of the engine.

 Demo

<img width="800" height="445" alt="ScreenRecording2026-06-08at22 41 54-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/208cf14a-e2c0-4ddf-91f8-5a06b905f1cc" />

Engine Details (at this moment)

Search algorithm: Minimax
Optimization: Alpha-beta pruning, transposition table + Zoobrist hashing, move ordering
Search depth: default 3 (variable)

Evaluation factors:
- Material balance
- Checkmates
- piece square values

Installation

```bash
git clone https://github.com/nathancoolusername/Nathan-chess-engine.git
cd Nathan-chess-engine
pip install -r requirements.txt
python engine.py
```
Documentation

Full technical documentation:
→ `documentation.md`

Future Improvements

* Improve and customize evaluation function
* Optimize move generation
* Increase search depth
  
Technologies Used

* Python
* Flask
* HTML JS CSS
