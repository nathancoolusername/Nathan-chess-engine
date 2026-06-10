from flask import Flask, jsonify, request
import random 

class Zoobrist:
    def __init__(self):
        self.table = {}
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        for square in range(8):
            for j in range(8):
                for piece in pieces:
                    self.table[((square, j), piece)] = random.getrandbits(64)
        self.table["turn"] = random.getrandbits(64)
        self.table["wK"] = random.getrandbits(64)
        self.table["bK"] = random.getrandbits(64)
        self.table["wQ"] = random.getrandbits(64)
        self.table["bQ"]= random.getrandbits(64)
        self.table[(5, 0)] = random.getrandbits(64)
        self.table[(5, 1)] = random.getrandbits(64)
        self.table[(5, 2)] = random.getrandbits(64)
        self.table[(5, 3)] = random.getrandbits(64)
        self.table[(5, 4)] = random.getrandbits(64)
        self.table[(5, 5)] = random.getrandbits(64)
        self.table[(5, 6)] = random.getrandbits(64)
        self.table[(5, 7)] = random.getrandbits(64)
        self.table[(2, 0)] = random.getrandbits(64)
        self.table[(2, 1)] = random.getrandbits(64)
        self.table[(2, 2)] = random.getrandbits(64)
        self.table[(2, 3)] = random.getrandbits(64)
        self.table[(2, 4)] = random.getrandbits(64)
        self.table[(2, 5)] = random.getrandbits(64)
        self.table[(2, 6)] = random.getrandbits(64)
        self.table[(2, 7)] = random.getrandbits(64)
    
    def make_hash(self, board, turn, castling, en_passant, board_hash = 0):
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
        if castling["white_kingside"]:
            board_hash ^= self.table["wK"]
        if castling["black_kingside"]:
            board_hash ^= self.table["bK"]
        if castling["white_queenside"]:
            board_hash ^= self.table["wQ"]
        if castling["black_queenside"]:
            board_hash ^= self.table["bQ"]
        if turn == "white":
            board_hash ^= self.table["turn"]
        if en_passant is not None:
            board_hash ^= self.table[en_passant]
        return board_hash
    
    def update_hash(self, current_hash, where1, where2, piece1, piece2, en_passant, piece3 = False):
        if piece1.color == "white":
            if piece1.name == "knight":
                current_hash ^= self.table[(where1, "n")]
                current_hash ^= self.table[(where2, "n")]
            else:
                current_hash ^= self.table[(where1, piece1.name[0])]
                if not piece3:
                    current_hash ^= self.table[(where2, piece1.name[0])]
                else:
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
        if piece2 and piece2.color == "white":
            if piece2.name == "knight":
                current_hash ^= self.table[(where2, "n")]
            elif piece1.name == "pawn" and where2 == en_passant:
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
        if (piece1.name == "king" and abs(where1[1] - where2[1]) == 2) or (piece1.name == "rook" or (piece2 and piece2.name == "rook")):
            if piece1.color == "white":
                current_hash ^= self.table["wK"]
                current_hash ^= self.table["wQ"]
            else:
                current_hash ^= self.table["bK"]
                current_hash ^= self.table["bQ"]
        current_hash ^= self.table["turn"]
        if en_passant:
            current_hash ^= self.table[(en_passant)]
        return current_hash


class Piece:
    # Basic piece information class
    def __init__(self, name, color):
        self.color = color
        self.name = name

class Board:

    # Initiates the board (2D array), adds pieces, and declares default information like the starting turn

    def __init__(self):
        self.hash_table = Zoobrist()
        back_rank = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        self.board = [[], [], [], [], [], [], [], []]
        a = 0
        for a in range(8):
            if a == 0:
                for i in back_rank:
                    self.board[a].append(Piece(i, "black"))
            elif a == 1:
                for _ in range(8):
                    self.board[a].append(Piece("pawn", "black"))
            elif a == 6:
                for _ in range(8):
                    self.board[a].append(Piece("pawn", "white"))
            elif a == 7:
                for i in back_rank:
                    self.board[a].append(Piece(i, "white"))
            else:
                for _ in range(8):
                    self.board[a].append(None)
        self.points = {
            "king" : 0,
            "queen" : 900,
            "bishop" : 300,
            "knight" : 300,
            "rook" : 500,
            "pawn" : 100
            }
        self.phase = "Mid"
        self.turn = "white"
        self.castling_rights = {
            "white_kingside" :True,
            "white_queenside" : True,
            "black_kingside" : True,
            "black_queenside" : True
        }
        self.en_passant_square = None
        self.move_clock = 0
        self.halfmove_clock = 0
        self.current_hash = self.hash_table.make_hash(self.board, self.turn, self.castling_rights, self.en_passant_square)
        self.hash_history = [self.current_hash]
        self.hash_count = {self.current_hash : 1}
        self.tsp = {}
        self.piece_square_values = {"pawn" : [[0, 0, 0, 0, 0, 0, 0, 0], 
                                              [50, 50, 50, 50, 50, 50, 50, 50], 
                                              [10, 10, 20, 30, 30, 20, 10, 10], 
                                              [5,  5, 10, 25, 25, 10,  5,  5], 
                                              [0,  0,  0, 20, 20,  0,  0,  0], 
                                              [5, -5,-10,  0,  0,-10, -5,  5], 
                                              [5, 10, 10,-20,-20, 10, 10,  5], 
                                              [0,  0,  0,  0,  0,  0,  0,  0]],
                                    "knight": [[-50,-40,-30,-30,-30,-30,-40,-50], 
                                              [-40,-20,  0,  0,  0,  0,-20,-40], 
                                              [-30,  0, 10, 15, 15, 10,  0,-30], 
                                              [-30,  5, 15, 20, 20, 15,  5,-30], 
                                              [-30,  0, 15, 20, 20, 15,  0,-30], 
                                              [-30,  5, 10, 15, 15, 10,  5,-30], 
                                              [-40,-20,  0,  5,  5,  0,-20,-40], 
                                              [-50,-40,-30,-30,-30,-30,-40,-50]],
                                    "bishop": [[-20,-10,-10,-10,-10,-10,-10,-20], 
                                              [-10,  0,  0,  0,  0,  0,  0,-10], 
                                              [-10,  0,  5, 10, 10,  5,  0,-10], 
                                              [-10,  5,  5, 10, 10,  5,  5,-10], 
                                              [-10,  0, 10, 10, 10, 10,  0,-10], 
                                              [-10, 10, 10, 10, 10, 10, 10,-10], 
                                              [-10,  5,  0,  0,  0,  0,  5,-10], 
                                              [-20,-10,-10,-10,-10,-10,-10,-20]], 
                                    "rook": [[  0,  0,  0,  0,  0,  0,  0,  0], 
                                              [ 5, 10, 10, 10, 10, 10, 10,  5], 
                                              [ -5,  0,  0,  0,  0,  0,  0, -5], 
                                              [ -5,  0,  0,  0,  0,  0,  0, -5], 
                                              [ -5,  0,  0,  0,  0,  0,  0, -5], 
                                              [ -5,  0,  0,  0,  0,  0,  0, -5], 
                                              [ -5,  0,  0,  0,  0,  0,  0, -5], 
                                              [  0,  0,  0,  5,  5,  0,  0,  0]],
                                    "queen":[[-20,-10,-10, -5, -5,-10,-10,-20], 
                                              [-10,  0,  0,  0,  0,  0,  0,-10], 
                                              [ -10,  0,  5,  5,  5,  5,  0,-10], 
                                              [ -5,  0,  5,  5,  5,  5,  0, -5], 
                                              [  0,  0,  5,  5,  5,  5,  0, -5], 
                                              [-10,  5,  5,  5,  5,  5,  0,-10], 
                                              [-10,  0,  5,  0,  0,  0,  0,-10], 
                                              [-20,-10,-10, -5, -5,-10,-10,-20]],
                                    "kingMid":[[-30,-40,-40,-50,-50,-40,-40,-30], 
                                              [-30,-40,-40,-50,-50,-40,-40,-30], 
                                              [-30,-40,-40,-50,-50,-40,-40,-30], 
                                              [-30,-40,-40,-50,-50,-40,-40,-30], 
                                              [-20,-30,-30,-40,-40,-30,-30,-20], 
                                              [-10,-20,-20,-20,-20,-20,-20,-10], 
                                              [ 20, 20,  0,  0,  0,  0, 20, 20], 
                                              [20, 30, 10,  0,  0, 10, 30, 20]], 
                                    "kingEnd":[[-50,-40,-30,-20,-20,-30,-40,-50], 
                                              [-30,-20,-10,  0,  0,-10,-20,-30], 
                                              [-30,-10, 20, 30, 30, 20,-10,-30], 
                                              [-30,-10, 30, 40, 40, 30,-10,-30], 
                                              [-30,-10, 30, 40, 40, 30,-10,-30], 
                                              [-30,-10, 20, 30, 30, 20,-10,-30], 
                                              [-30,-30,  0,  0,  0,  0,-30,-30], 
                                              [-50,-30,-30,-30,-30,-30,-30,-50]]
                                              }
        self.insufficient = [{("king", "black"), ("king", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "black"), ("knight", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("bishop", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "black"), ("knight", "black")},
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "white")}]
    
    # Collects all the possible moves (legal and illegal) for the piece on the selected square

    def get_moves(self, where):
        if where is None or self.board[where[0]][where[1]] is None:
            return []
        elif self.board[where[0]][where[1]].name == "rook":
            return self.rook_move(where)
        elif self.board[where[0]][where[1]].name == "bishop":
            return self.bishop_move(where)
        elif self.board[where[0]][where[1]].name == "queen":
            return self.queen_move(where)
        elif self.board[where[0]][where[1]].name == "pawn":
            return self.pawn_move(where)
        elif self.board[where[0]][where[1]].name == "knight":
            return self.knight_move(where)
        elif self.board[where[0]][where[1]].name == "king":
            return self.king_move(where)
        return []
    def bishop_move(self, square):
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
        return self.rook_move(square) + self.bishop_move(square)
     
    def knight_move(self, square):
        moves = []
        directions = [(2, 1), (2, -1), (-1, 2), (1, 2), (-2, -1), (-1, -2), (-2, 1), (1, -2)]
        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]] is None:
                moves.append(current)
            elif 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]].color !=  self.board[square[0]][square[1]].color:
                moves.append(current)
        return moves

    def king_move(self, square):
        candidates = []
        directions = [(1,0), (0, 1), (-1, 0), (0, -1), (1,1), (-1, -1), (1, -1), (-1, 1)]
        for i in directions:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8 and ( self.board[current[0]][current[1]] is None or self.board[current[0]][current[1]].color !=  self.board[square[0]][square[1]].color ):
                candidates.append(current)
        if self.board[square[0]][square[1]].color == "white":
            if self.can_castle(self.board[square[0]][square[1]].color, "king"):
                candidates.append((7, 6))
            if self.can_castle(self.board[square[0]][square[1]].color, "queen"):
                candidates.append((7, 2))
        if self.board[square[0]][square[1]].color == "black":
            if self.can_castle(self.board[square[0]][square[1]].color, "king"):
                candidates.append((0, 6))
            if self.can_castle(self.board[square[0]][square[1]].color, "queen"):
                candidates.append((0, 2))
        if self.board[square[0]][square[1]].color == "white":
            return [c for c in candidates if not self.is_attacked(c, "black")]
        else:
            return [c for c in candidates if not self.is_attacked(c, "white")]
        
    def can_castle(self, color, side):
        if color == "white":
            if side == "king":
                if not self.castling_rights["white_kingside"]:
                    return False
                elif self.is_in_check(color):
                    return False
                else:
                    for i in range(5, 7):
                        if self.board[7][i] is not None or self.is_attacked((7, i), "black") :
                            return False
                return True
            if side == "queen":
                if not self.castling_rights["white_queenside"]:
                    return False
                elif self.is_in_check(color):
                    return False
                else:
                    for i in range(3, 1, -1):
                        if self.board[7][i] is not None or self.is_attacked((7, i), "black") :
                            return False
                    if self.board[7][1] is not None:
                        return False
                return True
        if color == "black":
            if side == "king":
                if not self.castling_rights["black_kingside"]:
                    return False
                elif self.is_in_check(color):
                    return False
                else:
                    for i in range(5, 7):
                        if self.board[0][i] is not None or self.is_attacked((0, i), "white") :
                            return False
                return True
            if side == "queen":
                if not self.castling_rights["black_queenside"]:
                    return False
                elif self.is_in_check(color):
                    return False
                else:
                    for i in range(3, 1, -1):
                        if self.board[0][i] is not None or self.is_attacked((0, i), "white") :
                            return False
                    if self.board[0][1] is not None:
                        return False
                return True
            
    def pawn_move(self, square):
        moves = []
        directions = [-1, (-1, 1), (-1, -1)] if self.board[square[0]][square[1]].color == "white" else [1, (1,1), (1, -1)]
        if 0 <= square[0] + directions[0] < 8 and self.board[square[0] + directions[0]][square[1]] is None:
            current = (square[0] + directions[0], square[1])
            moves.append(current)
        if (square[0] == 6 and self.board[square[0]][square[1]].color == "white") or (square[0] == 1 and self.board[square[0]][square[1]].color == "black"):
                if self.board[square[0] + directions[0]][square[1]] is None and self.board[square[0] + directions[0]*2][square[1]] is None:
                    current = (square[0] + directions[0]*2, square[1]) 
                    moves.append(current)
        for i in directions[1:]:
            current = (square[0] + i[0], square[1] + i[1])
            if 0 <= current[0] < 8 and 0 <= current[1] < 8 and self.board[current[0]][current[1]] is not None and self.board[current[0]][current[1]].color != self.board[square[0]][square[1]].color:
                moves.append(current)
            if self.en_passant_square is not None and current == self.en_passant_square:
                current = (self.en_passant_square[0], self.en_passant_square[1])
                moves.append(current)
        return moves
    
    def is_attacked(self, square, color):
        def path_clear(start, end, step):
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
                    if a.color == "white":
                        pawn_attacks = [(i-1, j-1), (i-1, j+1)]
                    else:
                        pawn_attacks = [(i+1, j-1), (i+1, j+1)]
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
        opponent = "black" if color == "white" else "white"
        # Find king first instead of iterating all pieces
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
    
    def legal_moves(self, square):
        moves = []
        pseudo_moves = self.get_moves(square)
        if pseudo_moves == []:
            return []
        
        # Cache check results to avoid redundant is_in_check calls
        piece_color = self.board[square[0]][square[1]].color
        
        for target in pseudo_moves:
            # Quick capture of target piece
            captured = self.board[target[0]][target[1]]
            
            # Make the move
            self.board[target[0]][target[1]] = self.board[square[0]][square[1]]
            self.board[square[0]][square[1]] = None
            
            # Handle en passant capture
            en_passant_capture = None
            if (self.board[target[0]][target[1]].name == "pawn" and 
                target == self.en_passant_square):
                capture_sq = (target[0] + 1, target[1]) if piece_color == "white" else (target[0] - 1, target[1])
                en_passant_capture = self.board[capture_sq[0]][capture_sq[1]]
                self.board[capture_sq[0]][capture_sq[1]] = None
            
            # Check if king is in check (illegal move)
            if not self.is_in_check(piece_color):
                moves.append(target)
            
            # Undo the move
            self.board[square[0]][square[1]] = self.board[target[0]][target[1]]
            self.board[target[0]][target[1]] = captured
            
            # Restore en passant capture
            if en_passant_capture is not None:
                capture_sq = (target[0] + 1, target[1]) if piece_color == "white" else (target[0] - 1, target[1])
                self.board[capture_sq[0]][capture_sq[1]] = en_passant_capture
        
        return moves
    
    def save_move_state(self):
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
        from_square = tuple(from_square)
        to_square = tuple(to_square)
        place_1 = self.board[from_square[0]][from_square[1]]
        if place_1 is None:
            return False
        moves = self.legal_moves(from_square)
        if to_square not in moves:
            print("Illegal move")
            return False

        place_2 = self.board[to_square[0]][to_square[1]]

        if place_1.name == "king":
            self.castling_rights[f"{place_1.color}_kingside"] = False
            self.castling_rights[f"{place_1.color}_queenside"] = False
        elif place_1.name == "rook":
            if from_square == (7, 7):
                self.castling_rights["white_kingside"] = False
            elif from_square == (7, 0):
                self.castling_rights["white_queenside"] = False
            elif from_square == (0, 7):
                self.castling_rights["black_kingside"] = False
            elif from_square == (0, 0):
                self.castling_rights["black_queenside"] = False

        if place_2 is not None and place_2.name == "rook":
            if to_square == (7, 7):
                self.castling_rights["white_kingside"] = False
            elif to_square == (7, 0):
                self.castling_rights["white_queenside"] = False
            elif to_square == (0, 7):
                self.castling_rights["black_kingside"] = False
            elif to_square == (0, 0):
                self.castling_rights["black_queenside"] = False

        if place_1.name == "king" and abs(from_square[1] - to_square[1]) == 2:
            self.board[to_square[0]][to_square[1]] = place_1
            self.board[from_square[0]][from_square[1]] = None
            if from_square[1] > to_square[1]:
                self.board[from_square[0]][to_square[1] + 1] = self.board[from_square[0]][0]
                self.board[from_square[0]][0] = None
            else:
                self.board[from_square[0]][to_square[1] - 1] = self.board[from_square[0]][7]
                self.board[from_square[0]][7] = None
            self.halfmove_clock += 1
            self.en_passant_square = None
        else:
            if place_1.name == "pawn" and abs(to_square[0] - from_square[0]) == 2:
                self.en_passant_square = ((from_square[0] + to_square[0]) // 2, to_square[1])
            else:
                if place_1.name == "pawn" and to_square == self.en_passant_square:
                    capture_sq = (
                        (to_square[0] + 1, to_square[1])
                        if place_1.color == "white"
                        else (to_square[0] - 1, to_square[1])
                    )
                    self.board[capture_sq[0]][capture_sq[1]] = None
                self.en_passant_square = None

            if place_1.name == "pawn" and to_square[0] in (0, 7):
                self.board[to_square[0]][to_square[1]] = Piece("queen", place_1.color)
                self.board[from_square[0]][from_square[1]] = None
            else:
                self.board[to_square[0]][to_square[1]] = place_1
                self.board[from_square[0]][from_square[1]] = None

            if place_2 is None and place_1.name != "pawn":
                self.halfmove_clock += 1
            else:
                self.halfmove_clock = 0

        self.move_clock += 1
        self.turn = "black" if self.turn == "white" else "white"
        self.current_hash = self.hash_table.make_hash(self.board, self.turn, self.castling_rights, self.en_passant_square)
        self.hash_history.append(self.current_hash)
        self.hash_count[self.current_hash] = self.hash_count.get(self.current_hash, 0) + 1
        return True
 
    def check(self):
        moves = []
        pieces = []
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    moves += self.legal_moves((i, j))
                if a is not None:
                    pieces.append((a.name, a.color))
        if not moves and self.is_in_check(self.turn):
            print("You got checkmated bro")
            return True
        elif not moves:
            print("Stalemate bro")
            return True
    def is_game_over(self):
        moves = []
        pieces = []
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    moves += self.legal_moves((i, j))
                if a is not None:
                    pieces.append((a.name, a.color))
        if not moves and self.is_in_check(self.turn):
            return True
        elif not moves:
            return True
        if self.halfmove_clock >= 100:
            return True
        for a in self.hash_count.values():
            if a >= 3:
                return True
        if self.has_insufficient_material():
            return True
        return False

    def has_insufficient_material(self):
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
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    if self.legal_moves((i, j)):
                        return False
        return self.is_in_check(self.turn)

    def is_stalemate(self):
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is not None and a.color == self.turn:
                    if self.legal_moves((i, j)):
                        return False
        return not self.is_in_check(self.turn)

    def play_alone(self):
        while not self.is_game_over():
            self.display()
            from_square = tuple(int(x) for x in input("From (row col): ").split())
            to_square = tuple(int(x) for x in input("To (row col): ").split())
            self.make_move(from_square, to_square)

    def play_engine(self, depth):
        while not self.is_game_over():
            self.display()
            if self.turn == "white":
                from_square = tuple(int(x) for x in input("From (row col): ").split())
                to_square = tuple(int(x) for x in input("To (row col): ").split())
                self.make_move(from_square, to_square)
            else:
                move = self.best_move(depth)
                self.make_move(move[0], move[1])

    def display(self):
        for a in range(8):
            row = []
            for i in self.board[a]:
                if i is None:
                    row.append(".")
                else:
                    if i.color == "white":
                        if i.name == "knight":
                            row.append("N")
                        else:
                            row.append(i.name[0].capitalize())
                    else:
                        if i.name == "knight":
                            row.append("n")
                        else:
                            row.append(i.name[0])
            print(" ".join(row))

    def to_json(self):
        state = {}
        state["board"] = []
        state["turn"] =  self.turn
        state["game_over"] = self.is_game_over()
        for a in range(8):
            temp = []
            for i in self.board[a]:
                if i is None:
                    temp.append(None)
                else:
                    temp.append({"name" : i.name, "color" : i.color})
            state["board"].append(temp)
        return state
    
    def game_phase(self):
        piece_count = 0
        if self.phase == "Mid":
            for a in range(8):
                for i in self.board[a]:
                    if i is not None and i.name != "king":
                        piece_count += 1
        if piece_count <= 6: 
            self.phase = "End"
                       
    def evaluate(self):
        self.game_phase()
        score = 0
        for a in range(8):
            for p, i in enumerate(self.board[a]):
                if i is None:
                    continue
                elif i.color == "white":
                    score += self.points[i.name]
                    if i.name != "king":
                        score += self.piece_square_values[i.name][a][p]
                    else:
                        score += self.piece_square_values["king" + self.phase][a][p]
                else:
                    score -= self.points[i.name]
                    if i.name != "king":
                        score -= self.piece_square_values[i.name][7-a][7-p]
                    else:
                        score -= self.piece_square_values["king" + self.phase][7-a][7-p]
        return score
    
    def sort_moves(self, moves, from_square):
        """Sort moves with captures first (better alpha-beta pruning)"""
        to_square = from_square
        captures = []
        quiets = []
        for move in moves:
            if self.board[move[0]][move[1]] is not None:
                captures.append(move)
            else:
                quiets.append(move)
        return captures + quiets

    def minimax(self, depth, alpha = -10**10, beta = 10**10):
        tt_key = (self.current_hash, depth)
        if tt_key in self.tsp:
            return self.tsp[tt_key]

        if depth == 0:
            score = self.evaluate()
            self.tsp[tt_key] = score
            return score
        
        if self.is_game_over():
            if self.is_checkmate():
                if self.turn == "white":
                    score = self.evaluate() - 10**4 + depth
                else:
                    score = self.evaluate() + 10**4 - depth
            else:
                score = self.evaluate()
            self.tsp[tt_key] = score
            return score

        for a in range(8):
            for j, i in enumerate(self.board[a]):
                if i is None:
                    continue
                moves = self.legal_moves((a, j))
                if i.color == self.turn:
                    moves = self.sort_moves(moves, (a, j))
                    for q in moves:
                        state = self.save_move_state()
                        self.make_move((a, j), q)
                        score = self.minimax(depth-1, alpha, beta)
                        self.undo_move(state)
                        if self.turn == "white":
                            if score > alpha:
                                alpha = score
                            if beta <= alpha:
                                break
                        else:
                            if score < beta:
                                beta = score
                            if beta <= alpha:
                                break
        score = alpha if self.turn == "white" else beta
        self.tsp[tt_key] = score
        return score

    def best_move(self, depth, alpha = -10**10, beta = 10**10):
        self.tsp = {}  # Clear transposition table for each new search
        scores = {}
        best_moves = []
        
        # Collect all legal moves for current player
        for a in range(8):
                for j, i in enumerate(self.board[a]):
                    if i is None:
                        continue
                    else:
                        if i.color == self.turn:
                            for q in self.legal_moves((a, j)):
                                best_moves.append(((a, j), q))
        
        # Sort by capture priority and piece value
        def move_priority(move):
            from_sq, to_sq = move
            target = self.board[to_sq[0]][to_sq[1]]
            if target is not None:
                return self.points[target.name] * 10  # Prioritize valuable captures
            return 0
        
        best_moves.sort(key=move_priority, reverse=True)
        
        for move_pair in best_moves:
            state = self.save_move_state()
            self.make_move(move_pair[0], move_pair[1])
            scores[move_pair] = self.minimax(depth-1, alpha, beta)
            self.undo_move(state)
        
        if not scores:
            return None
        if self.turn == "white":
            return max(scores, key = scores.get)
        else:
            return min(scores, key = scores.get)
board = Board()
app = Flask(__name__)

@app.route('/state', methods=['GET'])

def get_state():
    return jsonify(board.to_json())

@app.route('/move', methods=['POST'])
def moving():
    data = request.get_json()
    from_square = data['from_square']
    to_square = data['to_square']
    board.make_move(from_square, to_square)
    return jsonify(board.to_json())

@app.route('/engine-move', methods=['POST'])
def engine_move():
    if board.is_game_over():
        return jsonify(board.to_json())
    move = board.best_move(depth=3)
    if move is not None:
        board.make_move(move[0], move[1])
    return jsonify(board.to_json())

@app.route("/options", methods=["POST"])
def get_moves():
    data = request.get_json()
    from_square = data
    moves = board.legal_moves(from_square)
    return jsonify(moves)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route("/reset", methods=["POST"])
def reset():
    global board
    board = Board()
    return jsonify(board.to_json())

if __name__ == '__main__':
    app.run(debug=True)