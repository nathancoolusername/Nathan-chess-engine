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

*(Add a GIF or screenshot here — this is huge for impact)*

Installation

```bash
git clone https://github.com/nathancoolusername/Nathan-chess-engine.git
cd Nathan-chess-engine
pip install -r requirements.txt
python app.py
```
Documentation

Full technical documentation:
→ `/docs/engine_documentation.md`

Future Improvements

* Add transposition tables
* Improve and customize evaluation function
* Optimize move generation
* Increase search depth
  
Technologies Used

* Python
* Flask
* HTML JS CSS
