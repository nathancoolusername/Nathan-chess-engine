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
        self.position_history = []
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
    
    def get_moves(self, where):
        if where is None:
            return []
        if self.board[where[0]][where[1]].name == "rook":
            return self.rook_move(where)
        if self.board[where[0]][where[1]].name == "bishop":
            return self.bishop_move(where)
        if self.board[where[0]][where[1]].name == "queen":
            return self.queen_move(where)
        if self.board[where[0]][where[1]].name == "pawn":
            return self.pawn_move(where)
        if self.board[where[0]][where[1]].name == "knight":
            return self.knight_move(where)
        if self.board[where[0]][where[1]].name == "king":
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
        saved_board = copy.deepcopy(self.board)
        saved_castling = copy.deepcopy(self.castling_rights)
        saved_ep = self.en_passant_square
        saved_halfmove = self.halfmove_clock
        saved_clock = self.move_clock
        saved_turn = self.turn
        moves = []
        everything = self.get_moves(square)
        if everything == []:
            return []
        for i in everything:
            self.board[i[0]][i[1]] = self.board[square[0]][square[1]]
            self.board[square[0]][square[1]] = None
            if not self.is_in_check(self.board[i[0]][i[1]].color):
                moves.append(i)
            saved_halfmove = self.halfmove_clock
            self.board = copy.deepcopy(saved_board)
            self.castling_rights = saved_castling
            self.en_passant_square = saved_ep
            self.halfmove_clock = saved_halfmove
            self.move_clock = saved_clock
            self.turn = saved_turn
        return moves
    
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
            print("Repeat! Repeat! Draw")
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

    def play(self):
        while not self.is_game_over():
            self.display()
            from_square = tuple(int(x) for x in input("From (row col): ").split())
            to_square = tuple(int(x) for x in input("To (row col): ").split())
            self.make_move(from_square, to_square)

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


man = Board()
man.play()