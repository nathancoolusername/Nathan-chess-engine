import chess
import math
import copy
from collections import Counter

class Piece:
    def __init__(self, name, color):
        self.color = color
        self.name = name

class Board:
    def __init__(self):
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
        self.position_history = [self.board_string()]
    
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
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is None:
                    continue
                if a.color != color:
                    continue
                if a.name == "rook":
                    if square in self.rook_move((i, j)):
                        return True
                if a.name == "bishop":
                    if square in self.bishop_move((i, j)):
                        return True
                if a.name == "queen":
                    if square in self.queen_move((i, j)):
                        return True
                if a.name == "pawn":
                    if square in self.pawn_move((i, j)):
                        return True
                if a.name == "knight":
                    if square in self.knight_move((i, j)):
                        return True
                if a.name == "king":
                    directions = [(1,0), (0, 1), (-1, 0), (0, -1), (1,1), (-1, -1), (1, -1), (-1, 1)]
                    for p in directions:
                        current = (i + p[0], j + p[1])
                        if 0 <= current[0] < 8 and 0 <= current[1] < 8 and current == square:
                            return True      
                            
    def is_in_check(self, color):
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a == None:
                    continue 
                if a.name == "king" and a.color == color:
                    return self.is_attacked((i, j), color)
    
    def legal_moves(self, square):
        moves = []
        everything = self.get_moves(square)
        if everything == []:
            return []
        for i in everything:
            state = self.save_move_state(square, i)
            self.board[i[0]][i[1]] = self.board[square[0]][square[1]]
            self.board[square[0]][square[1]] = None
            if not self.is_in_check(self.board[i[0]][i[1]].color):
                moves.append(i)
            self.undo_move(state)
        return moves
    
    def save_move_state(self, from_square, to_square):
        piece = self.board[from_square[0]][from_square[1]]
        state = {
            "from_square": from_square,
            "to_square": to_square,
            "moved_piece": piece,
            "captured_piece": self.board[to_square[0]][to_square[1]],
            "prev_en_passant": self.en_passant_square,
            "prev_castling_rights": self.castling_rights.copy(),
            "prev_halfmove_clock": self.halfmove_clock,
            "prev_move_clock": self.move_clock,
            "prev_turn": self.turn,
            "history_len": len(self.position_history),
            "is_castle": piece.name == "king" and abs(from_square[1] - to_square[1]) == 2,
            "is_en_passant": piece.name == "pawn" and to_square == self.en_passant_square,
            "is_promotion": piece.name == "pawn" and to_square[0] in (0, 7),
        }

        if state["is_castle"]:
            rook_from = (from_square[0], 7 if to_square[1] > from_square[1] else 0)
            rook_to = (from_square[0], 5 if to_square[1] > from_square[1] else 3)
            state["rook_from"] = rook_from
            state["rook_to"] = rook_to
            state["rook_piece"] = self.board[rook_from[0]][rook_from[1]]

        if state["is_en_passant"]:
            capture_sq = (
                (to_square[0] + 1, to_square[1])
                if piece.color == "white"
                else (to_square[0] - 1, to_square[1])
            )
            state["ep_capture_sq"] = capture_sq
            state["captured_piece"] = self.board[capture_sq[0]][capture_sq[1]]

        return state
    
    def undo_move(self, state):
        if state["is_castle"]:
            self.board[state["from_square"][0]][state["from_square"][1]] = state["moved_piece"]
            self.board[state["to_square"][0]][state["to_square"][1]] = None
            self.board[state["rook_from"][0]][state["rook_from"][1]] = state["rook_piece"]
            self.board[state["rook_to"][0]][state["rook_to"][1]] = None
        elif state["is_en_passant"]:
            self.board[state["from_square"][0]][state["from_square"][1]] = state["moved_piece"]
            self.board[state["to_square"][0]][state["to_square"][1]] = None
            self.board[state["ep_capture_sq"][0]][state["ep_capture_sq"][1]] = state["captured_piece"]
        else:
            self.board[state["from_square"][0]][state["from_square"][1]] = state["moved_piece"]
            self.board[state["to_square"][0]][state["to_square"][1]] = state["captured_piece"]

        self.en_passant_square = state["prev_en_passant"]
        self.castling_rights = state["prev_castling_rights"]
        self.halfmove_clock = state["prev_halfmove_clock"]
        self.move_clock = state["prev_move_clock"]
        self.turn = state["prev_turn"]
        self.position_history = self.position_history[:state["history_len"]]

    def make_move(self, from_square, to_square):
        place_1 = self.board[from_square[0]][from_square[1]] 
        place_2 = self.board[to_square[0]][to_square[1]]
        moves = self.legal_moves(from_square)
        turn = self.turn
        if to_square in moves:
            if place_1.name == "king" and abs(from_square[1] - to_square[1]) == 2:
                self.board[to_square[0]][to_square[1]] = self.board[from_square[0]][from_square[1]]
                self.board[from_square[0]][from_square[1]] = None
                if from_square[1] > to_square[1]:
                    self.board[from_square[0]][to_square[1]+1] = self.board[from_square[0]][0]
                    self.board[from_square[0]][0] = None
                else: 
                    self.board[from_square[0]][to_square[1]-1] = self.board[from_square[0]][7]
                    self.board[from_square[0]][7] = None
                self.castling_rights[f"{place_1.color}_queenside"] = False
                self.castling_rights[f"{place_1.color}_kingside"] = False
            else:
                if place_1.name == "rook" and from_square[1] == 7:
                    self.castling_rights[f"{place_1.color}_kingside"] = False
                if place_1.name == "rook" and from_square[1] == 0:
                    self.castling_rights[f"{place_1.color}_queenside"] = False
                if place_1.name == "pawn" and abs(to_square[0]-from_square[0]) == 2:
                    self.en_passant_square = (to_square[0]-1, to_square[1]) if place_1.color == "black" else (to_square[0]+1, to_square[1])
                else:
                    if to_square == self.en_passant_square:
                        if place_1.color == "white":
                            self.board[to_square[0]+1][to_square[1]] = None
                        else:
                            self.board[to_square[0]-1][to_square[1]] = None
                    self.en_passant_square = None
                if place_1.name == "pawn" and (to_square[0] == 0 or to_square[0] == 7):
                    self.board[to_square[0]][to_square[1]] = Piece("queen", place_1.color)
                    self.board[from_square[0]][from_square[1]] = None
                else:
                    self.board[to_square[0]][to_square[1]] = self.board[from_square[0]][from_square[1]]
                    self.board[from_square[0]][from_square[1]] = None
                if place_2 == None and place_1.name != "pawn":
                    self.halfmove_clock += 1
                else:
                    self.halfmove_clock = 0
            self.move_clock += 1
            self.turn = "black" if turn == "white" else "white"
            self.position_history.append(self.board_string())
        else: 
            print("Illegal move")
 
    def check(self):
        moves = []
        pieces = []
        insufficient = [{("king", "black"), ("king", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "black"), ("knight", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("bishop", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "black"), ("knight", "black")},
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "white")}]
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
        insufficient = [{("king", "black"), ("king", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "black"), ("knight", "white")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("bishop", "white"), ("bishop", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "black")}, 
                        {("king", "black"), ("king", "white"), ("knight", "black"), ("knight", "black")},
                        {("king", "black"), ("king", "white"), ("knight", "white"), ("knight", "white")}]
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
        if self.halfmove_clock == 100:
            print("Too passive --> Draw")
            return True
        counts = Counter(self.position_history)
        if any(c >= 3 for c in counts.values()):
            print("Repeat Draw")
            return True
        if set(pieces) in insufficient :
            print("not enough to win bro --> Draw")
            return True
        return False
        
    def board_string(self):
        string = ""
        for i in range(8):
            for j, a in enumerate(self.board[i]):
                if a is None:
                    string += "."
                    continue
                if a.color == "white":
                    if a.name == "knight":
                        string += "N"
                    else:
                        string += a.name[0].capitalize()
                else:
                    if a.name == "knight":
                        string += "n"
                    else:
                        string += a.name[0]
        string += "-" if self.en_passant_square is None else f"{self.en_passant_square}"
        string += "+" if self.turn == "black" else ";"
        string += "1" if self.castling_rights["white_kingside"] else "2"
        string += "3" if self.castling_rights["white_queenside"] else "4"
        string += "5" if self.castling_rights["black_kingside"] else "6"
        string += "7" if self.castling_rights["black_queenside"] else "8"
        return string

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

    def evaluate(self):
        score = 0
        points = {
            "king" : 0,
            "queen" : 9,
            "bishop" : 3,
            "knight" : 3,
            "rook" : 5,
            "pawn" : 1
        }
        for a in range(8):
            for i in self.board[a]:
                if i is None:
                    continue
                elif i.color == "white":
                    score += points[i.name]
                else:
                    score -= points[i.name]
        return score
    
    def minimax(self, depth, alpha = -10**10, beta = 10**10):
        moves = []
        if depth == 0 or self.check():
            return self.evaluate()
        else: 
            for a in range(8):
                for j, i in enumerate(self.board[a]):
                    if i is None:
                        continue
                    else:
                        if i.color == self.turn:
                            for q in self.legal_moves((a, j)):
                                state = self.save_move_state((a, j), q)
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
        if self.turn == "white":
            return alpha
        else:
            return beta

    def best_move(self, depth, alpha = -10**10, beta = 10**10):
        scores = {}
        for a in range(8):
                for j, i in enumerate(self.board[a]):
                    if i is None:
                        continue
                    else:
                        if i.color == self.turn:
                            for q in self.legal_moves((a, j)):
                                state = self.save_move_state((a, j), q)
                                self.make_move((a, j), q)
                                scores[((a,j), q)] = self.minimax(depth-1, alpha, beta)
                                self.undo_move(state)
        if self.turn == "white":
            return max(scores, key = scores.get)
        else:
            return min(scores, key = scores.get)

man = Board()
man.play_engine(3)