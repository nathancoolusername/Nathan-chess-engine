from flask import Flask, jsonify, request
import random 

# =============================================================================
# ZOBRIST HASHING
# =============================================================================
# Zobrist hashing is a technique for efficiently representing board positions
# as integers. Each (square, piece) combination is assigned a unique random
# 64-bit number at startup. A board's hash is computed by XORing together all
# the numbers for every piece on every square, plus flags for turn, castling
# rights, and en passant. The key property: XOR is its own inverse, so when a
# piece moves, we can UPDATE the hash in O(1) by XORing out the old values and
# XORing in the new ones — rather than recomputing from scratch every move.
# This hash is the key for the transposition table in minimax.

class Zoobrist:
    def __init__(self):
        self.table = {}

        # Assign a unique random 64-bit number to every (square, piece) pair.
        # Uppercase letters = black pieces, lowercase = white (standard convention).
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        for square in range(8):
            for j in range(8):
                for piece in pieces:
                    self.table[((square, j), piece)] = random.getrandbits(64)

        # Separate random values for game state flags.
        # XOR these in/out as rights change during the game.
        self.table["turn"] = random.getrandbits(64)         # Whose turn it is
        self.table["wK"] = random.getrandbits(64)           # White kingside castling right
        self.table["bK"] = random.getrandbits(64)           # Black kingside castling right
        self.table["wQ"] = random.getrandbits(64)           # White queenside castling right
        self.table["bQ"] = random.getrandbits(64)           # Black queenside castling right

        # En passant square hashes — one per file (column) for each side.
        # Row 5 = en passant target squares for white pawns capturing upward.
        # Row 2 = en passant target squares for black pawns capturing downward.
        for col in range(8):
            self.table[(5, col)] = random.getrandbits(64)
            self.table[(2, col)] = random.getrandbits(64)
    
    def make_hash(self, board, turn, castling, en_passant, board_hash=0):
        """
        Compute a full Zobrist hash from scratch for the given board state.
        Used once at game start; afterwards update_hash() keeps it current.
        
        Note on piece letter convention used here (inverted from standard):
        - White pieces use lowercase letters (e.g. 'p', 'r', 'q')
        - Black pieces use uppercase letters (e.g. 'P', 'R', 'Q')
        Knights are special-cased because 'k' is already taken by 'king'.
        """
        for a in range(8):
            for p, q in enumerate(board[a]):
                if q is not None and q.color == "white":
                    if q.name == "knight":
                        board_hash ^= self.table[((a, p), "n")]
                    else:
                        board_hash ^= self.table[((a, p), q.name[0])]
                if q is not None and q.color == "black":
                    if q.name == "knight":
                        board_hash ^= self.table[((a, p), "N")]
                    else:
                        board_hash ^= self.table[((a, p), q.name[0].capitalize())]

        # XOR in castling rights that are still available
        if castling["white_kingside"]:
            board_hash ^= self.table["wK"]
        if castling["black_kingside"]:
            board_hash ^= self.table["bK"]
        if castling["white_queenside"]:
            board_hash ^= self.table["wQ"]
        if castling["black_queenside"]:
            board_hash ^= self.table["bQ"]

        # XOR in turn (so same position with different side to move = different hash)
        if turn == "white":
            board_hash ^= self.table["turn"]

        # XOR in en passant file if one is available
        if en_passant is not None:
            board_hash ^= self.table[en_passant]

        return board_hash
    
    def update_hash(self, current_hash, where1, where2, piece1, piece2, en_passant, piece3=False):
        """
        Incrementally update a Zobrist hash after a move, rather than recomputing
        from scratch. XOR is self-inverse: XORing a value in twice cancels out,
        which is exactly what we want for 'remove piece from square / place on new square'.

        Args:
            where1:     Origin square of the moving piece
            where2:     Destination square
            piece1:     The piece that moved
            piece2:     The piece captured (or None)
            en_passant: The current en passant square before this move
            piece3:     True if a pawn promoted (piece becomes a queen)
        """
        # XOR out piece from its old square, XOR in at new square
        if piece1.color == "white":
            if piece1.name == "knight":
                current_hash ^= self.table[(where1, "n")]
                current_hash ^= self.table[(where2, "n")]
            else:
                current_hash ^= self.table[(where1, piece1.name[0])]
                if not piece3:
                    current_hash ^= self.table[(where2, piece1.name[0])]
                else:
                    # Pawn promoted to queen — XOR in queen, not pawn
                    current_hash ^= self.table[where2, "q"]
        else:
            if piece1.name == "knight":
                current_hash ^= self.table[(where1, "N")]
                current_hash ^= self.table[(where2, "N")]
            else:
                current_hash ^= self.table[(where1, piece1.name[0].capitalize())]
                if not piece3:
                    current_hash ^= self.table[(where2, piece1.name[0].capitalize())]
                else:
                    current_hash ^= self.table[where2, "Q"]

        # XOR out the captured piece from the destination square
        if piece2 and piece2.color == "white":
            if piece2.name == "knight":
                current_hash ^= self.table[(where2, "n")]
            elif piece1.name == "pawn" and where2 == en_passant:
                # En passant: captured pawn is not on the destination square
                current_hash ^= self.table[(en_passant)]
                current_hash ^= self.table[((where2[0]+1, where2[1]), "P")]
            else:
                current_hash ^= self.table[(where2, piece2.name[0])]
        if piece2 and piece2.color == "black":
            if piece2.name == "knight":
                current_hash ^= self.table[(where2, "N")]
            elif piece1.name == "pawn" and where2 == en_passant:
                current_hash ^= self.table[(en_passant)]
                current_hash ^= self.table[((where2[0]-1, where2[1]), "p")]
            else:
                current_hash ^= self.table[(where2, piece2.name[0].capitalize())]

        # If a king moved two squares (castling) or a rook moved, castling rights changed
        if (piece1.name == "king" and abs(where1[1] - where2[1]) == 2) or (piece1.name == "rook" or (piece2 and piece2.name == "rook")):
            if piece1.color == "white":
                current_hash ^= self.table["wK"]
                current_hash ^= self.table["wQ"]
            else:
                current_hash ^= self.table["bK"]
                current_hash ^= self.table["bQ"]

        # Flip turn every move
        current_hash ^= self.table["turn"]

        # XOR out old en passant square if it existed
        if en_passant:
            current_hash ^= self.table[(en_passant)]

        return current_hash


# =============================================================================
# PIECE
# =============================================================================

class Piece:
    """
    Lightweight data class representing a single chess piece.
    Deliberately minimal — the board handles all logic; pieces just store identity.
    """
    def __init__(self, name, color):
        self.color = color  # "white" or "black"
        self.name = name    # "pawn", "knight", "bishop", "rook", "queen", "king"


# =============================================================================
# BOARD
# =============================================================================
# The Board class is the core of the engine. It owns:
#   - The 8x8 board state (list of lists of Piece | None)
#   - All game rules (move generation, legality, castling, en passant, promotion)
#   - The evaluation function
#   - The minimax search with alpha-beta pruning
#   - The transposition table
#   - Zobrist hash tracking for threefold repetition detection

class Board:

    def __init__(self):
        # ── Zobrist hash table ─────────────────────────────────────────────
        self.hash_table = Zoobrist()

        # ── Board setup ────────────────────────────────────────────────────
        back_rank = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        self.board = [[], [], [], [], [], [], [], []]

        for a in range(8):
            if a == 0:
                # Black back rank (row 0 = top of board = black's side)
                for i in back_rank:
                    self.board[a].append(Piece(i, "black"))
            elif a == 1:
                for _ in range(8):
                    self.board[a].append(Piece("pawn", "black"))
            elif a == 6:
                for _ in range(8):
                    self.board[a].append(Piece("pawn", "white"))
            elif a == 7:
                # White back rank (row 7 = bottom = white's side)
                for i in back_rank:
                    self.board[a].append(Piece(i, "white"))
            else:
                for _ in range(8):
                    self.board[a].append(None)

        # ── Piece values (centipawns) ───────────────────────────────────────
        # Standard material values used in evaluation. King is 0 because it
        # can never be traded — its safety is handled by the king PST instead.
        self.points = {
            "king": 0,
            "queen": 900,
            "bishop": 300,
            "knight": 300,
            "rook": 500,
            "pawn": 100
        }

        # ── Game state ─────────────────────────────────────────────────────
        self.phase = "Mid"      # "Mid" or "End" — switches evaluation tables
        self.turn = "white"
        self.castling_rights = {
            "white_kingside": True,
            "white_queenside": True,
            "black_kingside": True,
            "black_queenside": True
        }
        self.en_passant_square = None   # Target square for en passant capture, or None
        self.move_clock = 0             # Total half-moves played
        self.halfmove_clock = 0         # Moves since last pawn move or capture (50-move rule)

        # ── Zobrist hash tracking ──────────────────────────────────────────
        self.current_hash = self.hash_table.make_hash(
            self.board, self.turn, self.castling_rights, self.en_passant_square
        )
        self.hash_history = [self.current_hash]
        self.hash_count = {self.current_hash: 1}  # Tracks repetitions for threefold rule

        # ── Transposition table ────────────────────────────────────────────
        # Maps (hash, depth) → score. Avoids re-searching positions already evaluated.
        self.tsp = {}

        # ── Piece-Square Tables (PSTs) ─────────────────────────────────────
        # Each table gives a positional bonus/penalty for a piece on each square.
        # Values are in centipawns, from white's perspective (row 0 = black's back rank).
        # Black pieces use the same tables but mirrored (7-row, 7-col).
        # These encode standard chess principles: central pawns, active knights,
        # king safety in the middlegame, king activity in the endgame, etc.
        self.piece_square_values = {
            "pawn": [
                [0,   0,   0,   0,   0,   0,   0,  0],
                [50,  50,  50,  50,  50,  50,  50, 50],
                [10,  10,  20,  30,  30,  20,  10, 10],
                [5,   5,   10,  25,  25,  10,   5,  5],
                [0,   0,   0,   20,  20,   0,   0,  0],
                [5,  -5,  -10,   0,   0, -10,  -5,  5],
                [5,   10,  10, -20, -20,  10,  10,  5],
                [0,   0,   0,   0,   0,   0,   0,  0]
            ],
            "knight": [
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20,   0,   0,   0,   0, -20, -40],
                [-30,   0,  10,  15,  15,  10,   0, -30],
                [-30,   5,  15,  20,  20,  15,   5, -30],
                [-30,   0,  15,  20,  20,  15,   0, -30],
                [-30,   5,  10,  15,  15,  10,   5, -30],
                [-40, -20,   0,   5,   5,   0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            "bishop": [
                [-20, -10, -10, -10, -10, -10, -10, -20],
                [-10,   0,   0,   0,   0,   0,   0, -10],
                [-10,   0,   5,  10,  10,   5,   0, -10],
                [-10,   5,   5,  10,  10,   5,   5, -10],
                [-10,   0,  10,  10,  10,  10,   0, -10],
                [-10,  10,  10,  10,  10,  10,  10, -10],
                [-10,   5,   0,   0,   0,   0,   5, -10],
                [-20, -10, -10, -10, -10, -10, -10, -20]
            ],
            "rook": [
                [0,   0,   0,   0,   0,   0,   0,  0],
                [5,  10,  10,  10,  10,  10,  10,  5],
                [-5,  0,   0,   0,   0,   0,   0, -5],
                [-5,  0,   0,   0,   0,   0,   0, -5],
                [-5,  0,   0,   0,   0,   0,   0, -5],
                [-5,  0,   0,   0,   0,   0,   0, -5],
                [-5,  0,   0,   0,   0,   0,   0, -5],
                [0,   0,   0,   5,   5,   0,   0,  0]
            ],
            "queen": [
                [-20, -10, -10,  -5,  -5, -10, -10, -20],
                [-10,   0,   0,   0,   0,   0,   0, -10],
                [-10,   0,   5,   5,   5,   5,   0, -10],
                [-5,    0,   5,   5,   5,   5,   0,  -5],
                [0,     0,   5,   5,   5,   5,   0,  -5],
                [-10,   5,   5,   5,   5,   5,   0, -10],
                [-10,   0,   5,   0,   0,   0,   0, -10],
                [-20, -10, -10,  -5,  -5, -10, -10, -20]
            ],
            # Two separate king tables: hide in corner during middlegame,
            # centralize aggressively in the endgame when there's no mating danger.
            "kingMid": [
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-20, -30, -30, -40, -40, -30, -30, -20],
                [-10, -20, -20, -20, -20, -20, -20, -10],
                [20,   20,   0,   0,   0,   0,  20,  20],
                [20,   30,  10,   0,   0,  10,  30,  20]
            ],
            "kingEnd": [
                [-50, -40, -30, -20, -20, -30, -40, -50],
                [-30, -20, -10,   0,   0, -10, -20, -30],
                [-30, -10,  20,  30,  30,  20, -10, -30],
                [-30, -10,  30,  40,  40,  30, -10, -30],
                [-30, -10,  30,  40,  40,  30, -10, -30],
                [-30, -10,  20,  30,  30,  20, -10, -30],
                [-30, -30,   0,   0,   0,   0, -30, -30],
                [-50, -30, -30, -30, -30, -30, -30, -50]
            ]
        }

        # Precomputed sets of piece combinations that are insufficient to force checkmate.
        # Used by has_insufficient_material() for automatic draw detection.
        self.insufficient = [
            {("king", "black"), ("king", "white")},
            {("king", "black"), ("king", "white"), ("bishop", "black"), ("knight", "white")},
            {("king", "black"), ("king", "white"), ("bishop", "white"), ("knight", "black")},
            {("king", "black"), ("king", "white"), ("bishop", "white"), ("bishop", "black")},
            {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "black")},
            {("king", "black"), ("king", "white"), ("knight", "black"), ("knight", "black")},
            {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "white")}
        ]

    # =========================================================================
    # MOVE GENERATION (PSEUDO-LEGAL)
    # =========================================================================
    # These methods generate candidate moves for each piece type without
    # checking whether the resulting position leaves the king in check.
    # That legality filter is applied in legal_moves() below.

    def get_moves(self, where):
        """Dispatch to the correct piece move generator based on piece type."""
        if where is None or self.board[where[0]][where[1]] is None:
            return []
        piece = self.board[where[0]][where[1]]
        dispatch = {
            "rook": self.rook_move,
            "bishop": self.bishop_move,
            "queen": self.queen_move,
            "pawn": self.pawn_move,
            "knight": self.knight_move,
            "king": self.king_move,
        }
        return dispatch.get(piece.name, lambda _: [])(where)

    def bishop_move(self, square):
        """
        Generate diagonal sliding moves. Extends in each of four diagonal
        directions until blocked by another piece or the board edge.
        Captures an enemy piece but cannot pass through it.
        """
        moves = []
        directions = [(1, 1), (-1, -1), (-1, 1), (1, -1)]
        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            while 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]] is None:
                moves.append(current)
                current = (current[0] + i[0], current[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]].color != self.board[square[0]][square[1]].color:
                moves.append(current)
        return moves

    def rook_move(self, square):
        """
        Generate orthogonal sliding moves. Same ray-casting pattern as the
        bishop, but along ranks and files instead of diagonals.
        """
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            while 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]] is None:
                moves.append(current)
                current = (current[0] + i[0], current[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]].color != self.board[square[0]][square[1]].color:
                moves.append(current)
        return moves

    def queen_move(self, square):
        """Queen = rook + bishop combined."""
        return self.rook_move(square) + self.bishop_move(square)

    def knight_move(self, square):
        """
        Knights jump in an L-shape. No ray casting — just check the 8
        fixed offsets and filter out-of-bounds and friendly pieces.
        """
        moves = []
        directions = [(2, 1), (2, -1), (-1, 2), (1, 2), (-2, -1), (-1, -2), (-2, 1), (1, -2)]
        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8:
                target = self.board[current[0]][current[1]]
                if target is None or target.color != self.board[square[0]][square[1]].color:
                    moves.append(current)
        return moves

    def king_move(self, square):
        """
        Generate king moves: one step in any direction, plus castling if eligible.
        Castling is checked via can_castle() which verifies rights, empty squares,
        and that the king does not pass through or land on an attacked square.
        Illegal moves (landing in check) are filtered here directly.
        """
        candidates = []
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        color = self.board[square[0]][square[1]].color

        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8:
                target = self.board[current[0]][current[1]]
                if target is None or target.color != color:
                    candidates.append(current)

        # Add castling squares if eligible
        if color == "white":
            if self.can_castle("white", "king"):
                candidates.append((7, 6))
            if self.can_castle("white", "queen"):
                candidates.append((7, 2))
        else:
            if self.can_castle("black", "king"):
                candidates.append((0, 6))
            if self.can_castle("black", "queen"):
                candidates.append((0, 2))

        # Filter out squares attacked by the opponent
        opponent = "black" if color == "white" else "white"
        return [c for c in candidates if not self.is_attacked(c, opponent)]

    def can_castle(self, color, side):
        """
        Check whether castling is currently legal for the given color and side.
        Conditions (all must hold):
          1. The castling right must not have been forfeited (king/rook haven't moved)
          2. The king must not currently be in check
          3. All squares between king and rook must be empty
          4. The king must not pass through a square attacked by the opponent
        """
        if color == "white":
            if side == "king":
                if not self.castling_rights["white_kingside"]:
                    return False
                if self.is_in_check(color):
                    return False
                for i in range(5, 7):  # f1 and g1 must be empty and safe
                    if self.board[7][i] is not None or self.is_attacked((7, i), "black"):
                        return False
                return True
            if side == "queen":
                if not self.castling_rights["white_queenside"]:
                    return False
                if self.is_in_check(color):
                    return False
                for i in range(3, 1, -1):  # d1 and c1 must be empty and safe
                    if self.board[7][i] is not None or self.is_attacked((7, i), "black"):
                        return False
                if self.board[7][1] is not None:  # b1 must also be empty (not attacked check needed)
                    return False
                return True
        if color == "black":
            if side == "king":
                if not self.castling_rights["black_kingside"]:
                    return False
                if self.is_in_check(color):
                    return False
                for i in range(5, 7):
                    if self.board[0][i] is not None or self.is_attacked((0, i), "white"):
                        return False
                return True
            if side == "queen":
                if not self.castling_rights["black_queenside"]:
                    return False
                if self.is_in_check(color):
                    return False
                for i in range(3, 1, -1):
                    if self.board[0][i] is not None or self.is_attacked((0, i), "white"):
                        return False
                if self.board[0][1] is not None:
                    return False
                return True

    def pawn_move(self, square):
        """
        Generate pawn moves. Pawns are the most complex piece to handle because
        they move and capture in different directions, and have three special rules:
          - Double push from starting rank (rows 6/1 for white/black)
          - En passant capture (target is self.en_passant_square)
          - Promotion is handled later in make_move(), not here
        """
        moves = []
        color = self.board[square[0]][square[1]].color
        # directions[0] = forward step; directions[1:] = diagonal captures
        directions = [-1, (-1, 1), (-1, -1)] if color == "white" else [1, (1, 1), (1, -1)]

        # Single step forward (only if square is empty)
        if 0 <= square[0] + directions[0] < 8 and self.board[square[0] + directions[0]][square[1]] is None:
            moves.append((square[0] + directions[0], square[1]))

        # Double push from starting rank
        start_row = 6 if color == "white" else 1
        if square[0] == start_row:
            if (self.board[square[0] + directions[0]][square[1]] is None and
                    self.board[square[0] + directions[0] * 2][square[1]] is None):
                moves.append((square[0] + directions[0] * 2, square[1]))

        # Diagonal captures and en passant
        for i in directions[1:]:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8:
                target = self.board[current[0]][current[1]]
                if target is not None and target.color != color:
                    moves.append(current)
                if self.en_passant_square is not None and current == self.en_passant_square:
                    moves.append(current)
        return moves

    # =========================================================================
    # ATTACK AND CHECK DETECTION
    # =========================================================================

    def is_attacked(self, square, color):
        """
        Determine whether a given square is attacked by any piece of 'color'.
        Uses ray-casting for sliding pieces (rook/bishop/queen) and fixed
        offsets for knights, pawns, and kings.

        This is the core of check detection and is called frequently — it
        iterates the whole board, which is acceptable at this scale but would
        be the first target for optimization in a faster engine (e.g. bitboards).
        """
        def path_clear(start, end, step):
            """Check that no piece blocks the line between start and end."""
            current = (start[0] + step[0], start[1] + step[1])
            while current != end:
                if self.board[current[0]][current[1]] is not None:
                    return False
                current = (current[0] + step[0], current[1] + step[1])
            return True

        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is None or a.color != color:
                    continue
                dr = square[0] - i
                dc = square[1] - j

                if a.name == "rook" or a.name == "queen":
                    if dr == 0 and dc != 0:
                        step = (0, 1 if dc > 0 else -1)
                        if path_clear((i, j), square, step):
                            return True
                    if dc == 0 and dr != 0:
                        step = (1 if dr > 0 else -1, 0)
                        if path_clear((i, j), square, step):
                            return True

                if a.name == "bishop" or a.name == "queen":
                    if abs(dr) == abs(dc) and dr != 0:
                        step = (1 if dr > 0 else -1, 1 if dc > 0 else -1)
                        if path_clear((i, j), square, step):
                            return True

                if a.name == "pawn":
                    pawn_attacks = (
                        [(i - 1, j - 1), (i - 1, j + 1)] if a.color == "white"
                        else [(i + 1, j - 1), (i + 1, j + 1)]
                    )
                    if square in pawn_attacks:
                        return True

                if a.name == "knight":
                    if (abs(dr), abs(dc)) in [(1, 2), (2, 1)]:
                        return True

                if a.name == "king":
                    if max(abs(dr), abs(dc)) == 1:
                        return True
        return False

    def is_in_check(self, color):
        """
        Find the king of the given color and check if it's under attack.
        Short-circuits the loop once the king is found to avoid redundant scanning.
        """
        opponent = "black" if color == "white" else "white"
        king_pos = None
        for i in range(8):
            for j, piece in enumerate(self.board[i]):
                if piece is not None and piece.name == "king" and piece.color == color:
                    king_pos = (i, j)
                    break
            if king_pos:
                break
        if king_pos is None:
            return False
        return self.is_attacked(king_pos, opponent)

    # =========================================================================
    # LEGAL MOVE FILTERING
    # =========================================================================

    def legal_moves(self, square):
        """
        Filter pseudo-legal moves to only those that leave the king safe.

        For each candidate move: make it temporarily on the board, check if
        the king is in check, then undo it. En passant captures require special
        handling because the captured pawn is not on the destination square.

        This make-and-undo approach is simple but slower than more advanced
        techniques (e.g. pin detection). For this engine's depth it's fine.
        """
        moves = []
        pseudo_moves = self.get_moves(square)
        if not pseudo_moves:
            return []

        piece_color = self.board[square[0]][square[1]].color

        for target in pseudo_moves:
            captured = self.board[target[0]][target[1]]

            # Temporarily make the move
            self.board[target[0]][target[1]] = self.board[square[0]][square[1]]
            self.board[square[0]][square[1]] = None

            # Handle en passant: captured pawn is on an adjacent row
            en_passant_capture = None
            if (self.board[target[0]][target[1]].name == "pawn" and
                    target == self.en_passant_square):
                capture_sq = (
                    (target[0] + 1, target[1]) if piece_color == "white"
                    else (target[0] - 1, target[1])
                )
                en_passant_capture = self.board[capture_sq[0]][capture_sq[1]]
                self.board[capture_sq[0]][capture_sq[1]] = None

            if not self.is_in_check(piece_color):
                moves.append(target)

            # Undo the move
            self.board[square[0]][square[1]] = self.board[target[0]][target[1]]
            self.board[target[0]][target[1]] = captured
            if en_passant_capture is not None:
                capture_sq = (
                    (target[0] + 1, target[1]) if piece_color == "white"
                    else (target[0] - 1, target[1])
                )
                self.board[capture_sq[0]][capture_sq[1]] = en_passant_capture

        return moves

    # =========================================================================
    # MOVE EXECUTION AND STATE MANAGEMENT
    # =========================================================================

    def save_move_state(self):
        """
        Snapshot the full mutable game state before a move. Used by
        the search (minimax) to undo moves cleanly after evaluating them.
        Copying only what changes keeps this efficient.
        """
        return {
            "board": [row[:] for row in self.board],
            "turn": self.turn,
            "castling_rights": self.castling_rights.copy(),
            "en_passant_square": self.en_passant_square,
            "halfmove_clock": self.halfmove_clock,
            "move_clock": self.move_clock,
            "current_hash": self.current_hash,
            "hash_history": list(self.hash_history),
            "hash_count": dict(self.hash_count),
        }

    def undo_move(self, state):
        """Restore all mutable state from a saved snapshot."""
        self.board = [row[:] for row in state["board"]]
        self.turn = state["turn"]
        self.castling_rights = state["castling_rights"]
        self.en_passant_square = state["en_passant_square"]
        self.halfmove_clock = state["halfmove_clock"]
        self.move_clock = state["move_clock"]
        self.current_hash = state["current_hash"]
        self.hash_history = list(state["hash_history"])
        self.hash_count = dict(state["hash_count"])

    def make_move(self, from_square, to_square):
        """
        Execute a move on the board, handling all special cases:
          - Castling (king moves two squares → rook teleports to other side)
          - En passant (pawn captures a ghost square → remove captured pawn manually)
          - Promotion (pawn reaches back rank → auto-promotes to queen)
          - Castling rights updates (king or rook move forfeits relevant rights)
          - Halfmove clock (reset on pawn move or capture, increment otherwise)
          - Zobrist hash update

        Returns True if the move was made, False if it was illegal.
        """
        from_square = tuple(from_square)
        to_square = tuple(to_square)
        place_1 = self.board[from_square[0]][from_square[1]]
        if place_1 is None:
            return False
        if to_square not in self.legal_moves(from_square):
            return False

        place_2 = self.board[to_square[0]][to_square[1]]

        # ── Update castling rights ─────────────────────────────────────────
        if place_1.name == "king":
            # King moving forfeits both castling rights for that color
            self.castling_rights[f"{place_1.color}_kingside"] = False
            self.castling_rights[f"{place_1.color}_queenside"] = False
        elif place_1.name == "rook":
            # Rook moving from its starting square forfeits one right
            if from_square == (7, 7): self.castling_rights["white_kingside"] = False
            elif from_square == (7, 0): self.castling_rights["white_queenside"] = False
            elif from_square == (0, 7): self.castling_rights["black_kingside"] = False
            elif from_square == (0, 0): self.castling_rights["black_queenside"] = False

        if place_2 is not None and place_2.name == "rook":
            # Capturing the opponent's rook also forfeits their castling right
            if to_square == (7, 7): self.castling_rights["white_kingside"] = False
            elif to_square == (7, 0): self.castling_rights["white_queenside"] = False
            elif to_square == (0, 7): self.castling_rights["black_kingside"] = False
            elif to_square == (0, 0): self.castling_rights["black_queenside"] = False

        # ── Handle castling ────────────────────────────────────────────────
        if place_1.name == "king" and abs(from_square[1] - to_square[1]) == 2:
            self.board[to_square[0]][to_square[1]] = place_1
            self.board[from_square[0]][from_square[1]] = None
            if from_square[1] > to_square[1]:
                # Queenside: rook jumps from col 0 to col 3
                self.board[from_square[0]][to_square[1] + 1] = self.board[from_square[0]][0]
                self.board[from_square[0]][0] = None
            else:
                # Kingside: rook jumps from col 7 to col 5
                self.board[from_square[0]][to_square[1] - 1] = self.board[from_square[0]][7]
                self.board[from_square[0]][7] = None
            self.halfmove_clock += 1
            self.en_passant_square = None
        else:
            # ── Set en passant square if pawn double-pushed ────────────────
            if place_1.name == "pawn" and abs(to_square[0] - from_square[0]) == 2:
                self.en_passant_square = ((from_square[0] + to_square[0]) // 2, to_square[1])
            else:
                # ── Handle en passant capture ──────────────────────────────
                if place_1.name == "pawn" and to_square == self.en_passant_square:
                    capture_sq = (
                        (to_square[0] + 1, to_square[1]) if place_1.color == "white"
                        else (to_square[0] - 1, to_square[1])
                    )
                    self.board[capture_sq[0]][capture_sq[1]] = None
                self.en_passant_square = None

            # ── Handle promotion (auto-promotes to queen) ──────────────────
            if place_1.name == "pawn" and to_square[0] in (0, 7):
                self.board[to_square[0]][to_square[1]] = Piece("queen", place_1.color)
                self.board[from_square[0]][from_square[1]] = None
            else:
                self.board[to_square[0]][to_square[1]] = place_1
                self.board[from_square[0]][from_square[1]] = None

            # ── Update halfmove clock ──────────────────────────────────────
            if place_2 is None and place_1.name != "pawn":
                self.halfmove_clock += 1
            else:
                self.halfmove_clock = 0

        self.move_clock += 1
        self.turn = "black" if self.turn == "white" else "white"

        # Recompute hash from scratch (simpler than incremental update here)
        self.current_hash = self.hash_table.make_hash(
            self.board, self.turn, self.castling_rights, self.en_passant_square
        )
        self.hash_history.append(self.current_hash)
        self.hash_count[self.current_hash] = self.hash_count.get(self.current_hash, 0) + 1
        return True

    # =========================================================================
    # GAME-OVER DETECTION
    # =========================================================================

    def is_game_over(self):
        """
        Check all terminal conditions:
          - Checkmate or stalemate (no legal moves)
          - 50-move rule (halfmove_clock >= 100, since we count half-moves)
          - Threefold repetition (same position hash appears 3+ times)
          - Insufficient material
        """
        moves = []
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    moves += self.legal_moves((i, j))
        if not moves:
            return True  # Checkmate or stalemate
        if self.halfmove_clock >= 100:
            return True
        if any(count >= 3 for count in self.hash_count.values()):
            return True
        if self.has_insufficient_material():
            return True
        return False

    def has_insufficient_material(self):
        """
        Check for drawn positions where neither side can force checkmate.
        Covers: KvK, KBvK, KNvK, KBvKB, KNvKN, KvKNN, KNNvK.
        """
        white = []
        black = []
        for row in self.board:
            for piece in row:
                if piece is None or piece.name == "king":
                    continue
                if piece.color == "white":
                    white.append(piece.name)
                else:
                    black.append(piece.name)
        if not white and not black:
            return True
        if not white and black in (["bishop"], ["knight"]):
            return True
        if not black and white in (["bishop"], ["knight"]):
            return True
        if white == ["bishop"] and black == ["bishop"]:
            return True
        return False

    def is_checkmate(self):
        """True if the current player has no legal moves AND is in check."""
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    if self.legal_moves((i, j)):
                        return False
        return self.is_in_check(self.turn)

    def is_stalemate(self):
        """True if the current player has no legal moves and is NOT in check."""
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    if self.legal_moves((i, j)):
                        return False
        return not self.is_in_check(self.turn)

    # =========================================================================
    # EVALUATION
    # =========================================================================

    def game_phase(self):
        """
        Switch from middlegame to endgame evaluation tables once fewer than
        7 non-king pieces remain. This changes the king's PST from defensive
        (hide in corner) to active (centralize).
        """
        if self.phase == "Mid":
            piece_count = sum(
                1 for row in self.board for p in row
                if p is not None and p.name != "king"
            )
            if piece_count <= 6:
                self.phase = "End"

    def evaluate(self):
        """
        Static evaluation of the current position in centipawns from White's perspective.
        Positive scores favor White; negative favor Black.

        The evaluation combines:
          1. Material count — sum of piece values
          2. Piece-square bonuses — positional incentives per piece type

        Black pieces use the same PSTs as White but mirrored vertically (7-row, 7-col),
        so that e.g. a pawn on row 6 for black gets the same central bonus as a white
        pawn on row 1.

        This is a purely static evaluation — it doesn't look ahead. The engine's
        strategic strength comes entirely from the minimax search.
        """
        self.game_phase()
        score = 0
        for a in range(8):
            for p, i in enumerate(self.board[a]):
                if i is None:
                    continue
                if i.color == "white":
                    score += self.points[i.name]
                    score += (
                        self.piece_square_values["king" + self.phase][a][p]
                        if i.name == "king"
                        else self.piece_square_values[i.name][a][p]
                    )
                else:
                    score -= self.points[i.name]
                    score -= (
                        self.piece_square_values["king" + self.phase][7 - a][7 - p]
                        if i.name == "king"
                        else self.piece_square_values[i.name][7 - a][7 - p]
                    )
        return score

    # =========================================================================
    # SEARCH: MINIMAX WITH ALPHA-BETA PRUNING
    # =========================================================================

    def sort_moves(self, moves, from_square):
        """
        Order moves to improve alpha-beta pruning efficiency.
        Captures are placed before quiet moves, since they're more likely to
        produce cutoffs early and reduce the effective branching factor.
        A full MVV-LVA (Most Valuable Victim, Least Valuable Attacker) ordering
        would improve this further but wasn't implemented.
        """
        captures = []
        quiets = []
        for move in moves:
            if self.board[move[0]][move[1]] is not None:
                captures.append(move)
            else:
                quiets.append(move)
        return captures + quiets

    def minimax(self, depth, alpha=-10**10, beta=10**10):
        """
        Minimax search with alpha-beta pruning and a transposition table.

        Minimax: White maximizes the evaluation score; Black minimizes it.
        Alpha-beta pruning: tracks the best score each side can guarantee and
        cuts off branches that can't influence the final decision. In the best
        case (perfect move ordering) this halves the effective search depth,
        allowing twice as deep a search for the same computation.

        Transposition table: stores (hash, depth) → score to avoid re-searching
        positions we've already evaluated at the same or greater depth.

        Terminal conditions:
          - depth == 0: return static evaluation
          - game over: return evaluation ± large checkmate bonus/penalty
            (adjusted by depth so the engine prefers faster mates)
        """
        tt_key = (self.current_hash, depth)
        if tt_key in self.tsp:
            return self.tsp[tt_key]

        if depth == 0:
            score = self.evaluate()
            self.tsp[tt_key] = score
            return score

        if self.is_game_over():
            if self.is_checkmate():
                score = (
                    self.evaluate() - 10**4 + depth if self.turn == "white"
                    else self.evaluate() + 10**4 - depth
                )
            else:
                score = self.evaluate()  # Stalemate or draw
            self.tsp[tt_key] = score
            return score

        for a in range(8):
            for j, i in enumerate(self.board[a]):
                if i is None or i.color != self.turn:
                    continue
                moves = self.sort_moves(self.legal_moves((a, j)), (a, j))
                for q in moves:
                    state = self.save_move_state()
                    self.make_move((a, j), q)
                    score = self.minimax(depth - 1, alpha, beta)
                    self.undo_move(state)

                    if self.turn == "white":
                        if score > alpha:
                            alpha = score
                        if beta <= alpha:
                            break  # Beta cutoff: Black would avoid this line
                    else:
                        if score < beta:
                            beta = score
                        if beta <= alpha:
                            break  # Alpha cutoff: White would avoid this line

        score = alpha if self.turn == "white" else beta
        self.tsp[tt_key] = score
        return score

    def best_move(self, depth, alpha=-10**10, beta=10**10):
        """
        Root-level search: find the best move for the current player.
        Unlike minimax() which returns a score, this returns the actual move pair.

        Collects all legal moves, sorts by capture priority, evaluates each
        via minimax at depth-1, and returns the move with the best score.

        The transposition table is cleared at the start of each new search
        to avoid using stale entries from a different game state.
        """
        self.tsp = {}
        scores = {}

        # Collect all legal moves for the current player
        all_moves = []
        for a in range(8):
            for j, i in enumerate(self.board[a]):
                if i is not None and i.color == self.turn:
                    for q in self.legal_moves((a, j)):
                        all_moves.append(((a, j), q))

        # Prioritize captures of high-value pieces at the root level
        def move_priority(move):
            target = self.board[move[1][0]][move[1][1]]
            return self.points[target.name] * 10 if target is not None else 0

        all_moves.sort(key=move_priority, reverse=True)

        for move_pair in all_moves:
            state = self.save_move_state()
            self.make_move(move_pair[0], move_pair[1])
            scores[move_pair] = self.minimax(depth - 1, alpha, beta)
            self.undo_move(state)

        if not scores:
            return None

        return max(scores, key=scores.get) if self.turn == "white" else min(scores, key=scores.get)

    # =========================================================================
    # UTILITY
    # =========================================================================

    def display(self):
        """Print the board to stdout using standard piece letter notation."""
        for a in range(8):
            row = []
            for i in self.board[a]:
                if i is None:
                    row.append(".")
                elif i.color == "white":
                    row.append("N" if i.name == "knight" else i.name[0].upper())
                else:
                    row.append("n" if i.name == "knight" else i.name[0])
            print(" ".join(row))

    def to_json(self):
        """Serialize board state for the Flask API response."""
        return {
            "turn": self.turn,
            "game_over": self.is_game_over(),
            "board": [
                [
                    {"name": piece.name, "color": piece.color} if piece else None
                    for piece in row
                ]
                for row in self.board
            ]
        }

    def play_alone(self):
        """Two-player local mode (terminal)."""
        while not self.is_game_over():
            self.display()
            from_square = tuple(int(x) for x in input("From (row col): ").split())
            to_square = tuple(int(x) for x in input("To (row col): ").split())
            self.make_move(from_square, to_square)

    def play_engine(self, depth):
        """Human (white) vs engine (black) terminal mode."""
        while not self.is_game_over():
            self.display()
            if self.turn == "white":
                from_square = tuple(int(x) for x in input("From (row col): ").split())
                to_square = tuple(int(x) for x in input("To (row col): ").split())
                self.make_move(from_square, to_square)
            else:
                move = self.best_move(depth)
                self.make_move(move[0], move[1])


# =============================================================================
# FLASK API
# =============================================================================
# A thin REST API layer over the Board class. The frontend communicates with
# these endpoints to display the board and submit moves.
# A single global Board instance represents the active game.

board = Board()
app = Flask(__name__)

@app.route('/state', methods=['GET'])
def get_state():
    """Return the current board state as JSON."""
    return jsonify(board.to_json())

@app.route('/move', methods=['POST'])
def moving():
    """
    Accept a player move and apply it to the board.
    Request body: { "from_square": [row, col], "to_square": [row, col] }
    """
    data = request.get_json()
    board.make_move(data['from_square'], data['to_square'])
    return jsonify(board.to_json())

@app.route('/engine-move', methods=['POST'])
def engine_move():
    """
    Trigger the engine to compute and play its best move at depth 3.
    Depth 3 provides a reasonable balance between move quality and response time
    (~1–3 seconds on most hardware depending on position complexity).
    """
    if board.is_game_over():
        return jsonify(board.to_json())
    move = board.best_move(depth=3)
    if move is not None:
        board.make_move(move[0], move[1])
    return jsonify(board.to_json())

@app.route("/options", methods=["POST"])
def get_moves():
    """Return legal moves for a given square (used to highlight valid destinations in the UI)."""
    from_square = request.get_json()
    moves = board.legal_moves(from_square)
    return jsonify(moves)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route("/reset", methods=["POST"])
def reset():
    """Reset the board to the starting position."""
    global board
    board = Board()
    return jsonify(board.to_json())

if __name__ == '__main__':
    app.run(debug=True)