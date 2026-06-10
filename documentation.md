Chess Engine Documentation
Author: Nathan
 Stack: Python · Flask · HTML/CSS/JS
 Search Algorithm: Minimax with Alpha-Beta Pruning
 Hashing: Zobrist

1. Introduction
   
This is a fully functional chess engine built from scratch in Python, served via a Flask REST API and played through a browser-based frontend. The project covers the complete stack: rules engine, game AI, HTTP interface, and UI.

Goals:

Implement a correct chess rules engine (all special moves included)
Build a search algorithm capable of playing at a reasonable amateur level
Expose the engine through a clean API so any frontend can interact with it
Understand the real techniques used in production chess engines, at a smaller scale

3. System Architecture
   
The project is divided into three layers:
┌─────────────────────────────────────┐
│           Browser (Frontend)         │
│  HTML/CSS/JS — renders board,        │
│  sends clicks as HTTP requests       │
└──────────────┬──────────────────────┘
               │  HTTP (JSON)
               ▼
┌─────────────────────────────────────┐
│         Flask REST API               │
│  /state  /move  /engine-move         │
│  /options  /reset                    │
└──────────────┬──────────────────────┘
               │  Python method calls
               ▼
┌─────────────────────────────────────┐
│         Board (Engine Core)          │
│  - Move generation                   │
│  - Legal move filtering              │
│  - Game state management             │
│  - Minimax + Alpha-Beta search       │
│  - Zobrist hashing                   │
│  - Static evaluation                 │
└─────────────────────────────────────┘

Data Flow — Player Move
User clicks piece → JS captures click
  → POST /options [from_square]
  → Board.legal_moves() returns valid destinations
  → Frontend highlights them

User clicks destination → POST /move [from, to]
  → Board.make_move() validates and executes
  → Returns updated board JSON
  → Frontend re-renders

Data Flow — Engine Move
POST /engine-move
  → Board.best_move(depth=3)
    → iterates all legal moves
    → for each: make_move → minimax(depth-1) → undo_move
    → returns move with best minimax score
  → Board.make_move(best_move)
  → Returns updated board JSON

3. Core Algorithms
   
3.1 Minimax

Minimax is the foundational algorithm for two-player zero-sum games. It models the game as a tree: White tries to maximize the evaluation score, Black tries to minimize it. At each node, the current player picks the child node with the score most favorable to them. At depth 0 (leaf nodes), the static evaluation function scores the position.
Why minimax: It's the correct algorithm for chess as it doesn't assume the opponent will make mistakes, which makes the engine reliable rather than opportunistic.
Implementation choice: The engine uses a recursive implementation with save_move_state() / undo_move() rather than copying the whole board object. This keeps memory usage lower during deep searches since only the diff (changed squares, castling rights, clocks, hash) is stored per node.

3.2 Alpha-Beta Pruning

Alpha-beta is an optimization layered on top of minimax that prunes branches that cannot possibly affect the final decision. Two values are tracked during search:
Alpha: the best score White has found so far (lower bound)
Beta: the best score Black has found so far (upper bound)
When beta ≤ alpha, the current branch is abandoned because the opponent already has a better option elsewhere and would never allow this line.
Why it matters: In the ideal case with perfect move ordering, alpha-beta reduces the branching factor from ~35 (typical chess) to ~6, effectively doubling the search depth for the same computation. In practice with imperfect ordering, the gain is smaller but still substantial.
Move ordering: To maximize the pruning benefit, captures are sorted before quiet moves at each node. This is because captures are more likely to cause cutoffs early. A full MVV-LVA (Most Valuable Victim, Least Valuable Attacker) implementation would improve this further.

3.3 Transposition Table

Chess positions are often reachable via different move orders (transpositions). Without a transposition table, the engine wastes time re-evaluating positions it has already scored.
The transposition table is a dictionary mapping (zobrist_hash, depth) → score. Before searching any node, the engine checks if it already has a result. If so, it returns immediately.
Key design detail: The table is keyed on both hash and depth because a result computed at depth 1 cannot be reused at depth 3 since  it would be insufficiently deep.
Limitation: The current implementation uses a flag-free table (no EXACT, LOWER_BOUND, UPPER_BOUND flags). A proper implementation would store the bound type alongside each score, allowing more entries to be usefully reused even when they don't exactly match the current alpha-beta window.

3.4 Zobrist Hashing

Zobrist hashing assigns a unique random 64-bit integer to every (square, piece) combination at startup. A board's hash is the XOR of all those integers for every piece currently on the board, plus flags for turn, castling rights, and en passant.
The key property of XOR: XOR is its own inverse. To update a hash after a move, you XOR out the piece's old square and XOR in the new square. It’s an O(1) operation instead of O(64) recomputation. This makes the transposition table lookup essentially free.
Zobrist hashes also drive threefold repetition detection: hash_count maps each position hash to how many times it has appeared. When any count reaches 3, the game is drawn.
Known implementation note: make_move() currently recomputes the hash from scratch rather than using the incremental update_hash() method. This is correct but slower than necessary; switching to update_hash() would be a straightforward performance improvement.

3.5 Static Evaluation Function

The evaluation function converts a board position into a single number (in centipawns, where 100 = one pawn's worth of advantage) from White's perspective. It has two components:

**Material**: Each piece has a fixed value (queen = 900, rook = 500, bishop = knight = 300, pawn = 100). The score is the sum of White's material minus Black's material.

**Piece-Square Tables **(PSTs): Each piece type has an 8×8 table of positional bonuses. These encode standard chess principles in a lookup-table form:

Pawns: prefer central advances, penalize doubled pawns (partially)
Knights: heavily penalized on the edge ("a knight on the rim is dim"), rewarded in the center
Bishops: rewarded for long diagonals and central presence
Rooks: rewarded on the 7th rank and open files
King (middlegame): strongly rewarded for staying behind a pawn shelter in the corner
King (endgame): rewarded for centralizing, since the king becomes an active piece
Black pieces use the same tables as White but mirrored vertically (index 7-row, 7-col), so that both sides' incentives are symmetric.
Game phase detection: When fewer than 7 non-king pieces remain, the engine switches the king's PST from the middlegame table (hide) to the endgame table (centralize). This prevents the engine from keeping its king passive in a position where it should be active.

5. Key Methods
   
legal_moves(square)

The most-called method in the engine. Generates pseudo-legal moves for a piece (moves that are geometrically valid but may leave the king in check), then filters them by temporarily making each move, checking is_in_check(), and undoing it. This make-test-undo approach is simple and correct; a faster alternative would be to detect pins and discovered checks statically, but that adds significant complexity.

is_attacked(square, color)

Determines whether a square is attacked by any piece of the given color. Uses ray-casting for sliding pieces (rook, bishop, queen) and fixed offsets for knights, pawns, and kings. Called by is_in_check() and can_castle(). It iterates the entire board for every call. A bitboard representation would replace this with bitwise operations, dramatically speeding it up.

make_move(from_square, to_square) / undo_move(state)

Together these implement the search's move-make-undo cycle. make_move() handles all special cases (castling, en passant, promotion, castling rights, clocks). undo_move() restores the full saved state. The save/restore approach was chosen over a dedicated undo stack because it's simpler to reason about correctness, at the cost of slightly higher memory usage per node.

minimax(depth, alpha, beta)

The recursive search function. Returns the best score achievable from the current position at the given remaining depth. Alpha and beta are passed down the call stack and updated at each node. The transposition table is checked at the start and written at the end of each call.
best_move(depth)
The public interface to the search. Iterates all legal moves at the root, calls minimax(depth-1) for each, and returns the move with the best resulting score. The transposition table is cleared here at the start of each new search to avoid stale entries.

evaluate()

The leaf-node scoring function. Iterates the board once, summing material and PST values with sign based on color. Called only at depth 0 to avoid exponential cost.

7. Design Decisions

Python over C++

Python was chosen because the goal was to learn the algorithms, not to optimize raw speed. Python's readability made it easier to reason about correctness, especially for the many edge cases in chess rules. The tradeoff is real: a C++ implementation of the same algorithm would search 50–100× faster, but would add hundreds of lines of boilerplate and take the focus away from the chess logic itself.

Flask over a desktop UI

Flask was chosen because it decouples the engine from the display layer completely. The engine exposes a JSON API and doesn't care what renders it. This also made development faster: the frontend could be changed without touching the engine, and the engine could be tested with curl without a UI.

Auto-promotion to queen

When a pawn reaches the back rank, the engine promotes it to a queen automatically. This is almost always the correct choice (and always correct for the engine's purposes). Implementing underpromotion would add complexity with essentially no practical benefit at this level of play.

Single global Board instance

The Flask API uses one shared Board object for the entire server process. This is fine for a single-player application but would break under concurrent users. A production version would store game state per session.

Depth 3 for engine responses

Depth 3 was chosen as the default for /engine-move. It consistently produces reasonable moves in 1–4 seconds on typical hardware. Depth 4 produces noticeably stronger play but takes 10–30 seconds, which is too slow for a pleasant interactive experience. The depth can be adjusted in the endpoint to trade off speed and quality.

8. Comparison to Other Engines
   
Feature

This engine
Stockfish

Search algorithm

Minimax + Alpha-Beta
Negamax + Alpha-Beta + many optimizations

Move ordering

Captures first (simple)
Full MVV-LVA, history heuristic, killer moves

Evaluation

Material + PSTs
Learned (NNUE neural network)

Transposition table

Hash + depth, no bound flags
Full TT with bound types and replacement policy

Board representation

2D Python list
Bitboards (64-bit integers)

Typical search depth

3
25–35+ with extensions

Language

Python
C++

The core ideas  (minimax, alpha-beta, PSTs, transposition tables, Zobrist hashing)  are identical to what real engines use. The gap is in the scale and optimization of each component, not the conceptual architecture.
Compared to simple engines: Compared to engines that use only material counting with no PSTs, this engine plays noticeably more principled chess: it develops pieces toward the center, keeps its king safe during the middlegame, and avoids positionally passive squares. The PSTs alone represent a significant improvement in play quality over a pure material evaluator.

7. Performance
   
Search depth: Default depth 3 (depth 4 available but slower).
Approximate times per move (depth 3, tested on a modern laptop):
Opening positions (many pieces, many moves): ~2–4 seconds
Middlegame: ~1–3 seconds
Endgame (few pieces): <0.5 seconds
Transposition table impact: The TT measurably reduces search time in positions with many transpositions (repeated move orders), particularly in the endgame. In opening positions with more unique positions, the benefit is smaller.
Branching factor: Typical chess positions have ~35 legal moves. Alpha-beta with capture-first ordering reduces the effective branching factor to roughly 15–20 in this implementation, meaning depth 3 evaluates approximately 3,375–8,000 nodes rather than the 42,875 minimax would require without pruning.
Known bottleneck: is_attacked() iterates the entire board (up to 64 squares × 6 piece types) for every legal-move legality check. This is the primary performance bottleneck. Replacing the board representation with bitboards would reduce this to a handful of bitwise operations.

9. Challenges and Known Limitations
    
What worked well

The make-undo state management is clean and reliable — no bugs from incorrect undo behavior were encountered
Zobrist hashing made threefold repetition detection trivial once implemented
The PST tables immediately produced a noticeable improvement in positional play

Known issue

Minimax alpha-beta logic: There is a subtle issue in the recursive propagation of alpha/beta across maximizing and minimizing nodes that can cause the engine to occasionally miss the optimal continuation. This is a known bug rather than a design limitation.

What would be improved next

Quiescence search: Currently the engine evaluates at a fixed depth and can be fooled by positions where the last move is a capture that changes the material balance (the "horizon effect"). Quiescence search extends the search through captures only until the position is "quiet," fixing this.
Iterative deepening: Instead of searching at a fixed depth, search at depth 1, then 2, then 3, using results from each pass to order moves for the next. This gives better move ordering at deeper depths and allows a time-based cutoff.

Bitboard representation: Replace the 2D list with 64-bit integers, one per piece type per color. All move generation and attack detection becomes bitwise operations — 10–100× faster in practice.
NNUE evaluation: Modern engines use learned neural networks for evaluation. This would require training data from strong games, but would produce far stronger positional understanding than hand-tuned PSTs.

Underpromotion: Allow promoting to rook or knight in the rare cases where this is correct (e.g., promoting to a queen causes stalemate).
Proper TT bound flags: Store EXACT, LOWER_BOUND, UPPER_BOUND with each transposition table entry to allow more entries to be usefully reused.

11. References
    
Chess Programming Resources
Chess Programming Wiki: https://www.chessprogramming.org :

Minimax
Alpha-Beta
Zobrist Hashing
Piece-Square Tables

Python & Flask

Flask Documentation — https://flask.palletsprojects.com


