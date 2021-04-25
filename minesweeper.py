import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """
    def __init__(self, height=8, width=8, mines=8):
        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """
        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells,)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        return self.cells.intersection(MinesweeperAI.mines)

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        return self.cells.intersection(MinesweeperAI.safes)

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        # should first check to see if cell is one of the cells included in the sentence.
        # If cell is not in the sentence, then no action is necessary.
        if cell not in self.cells:
            return

        # update the sentence so that cell is no longer in the sentence
        self.cells.remove(cell)
        self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """

        # should first check to see if cell is one of the cells included in the sentence.
        # If cell is not in the sentence, then no action is necessary.
        if cell not in self.cells:
            return

        # update the sentence so that cell is no longer in the sentence
        self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called after we know the cell is safe
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        cell (represented as a tuple (i, j))
        """
        # This function should:
        #     1) mark the cell as a move that has been made
        self.moves_made.add(cell)

        #     2) mark the cell as safe
        self.mark_safe(cell)

        #     3) add a new sentence to the AI's knowledge base
        #        based on the value of `cell` and `count`
        #        self.knowledge.append(Sentence(cell, count))

        surrounding_cells = self.surrounding_cells(cell)

        # if amount = len(surrounding_cells), loop through and self.mark_mine
        if len(surrounding_cells) == count:
            for surrounding_cell in surrounding_cells:
                self.mark_mine(surrounding_cell)

        # if count = 0, surrounding cells are safe
        if count == 0:
            for surrounding_cell in surrounding_cells:
                self.mark_safe(surrounding_cell)

        # How many surrounding cells are discovered and safe
        discovered_surrounding_safe_cells = self.safes.intersection(surrounding_cells)

        # How many cells do we know are mines
        discovered_surrounding_mine_cells = self.mines.intersection(surrounding_cells)

        # How many cells do we not know
        undiscovered_surrounding_cells = surrounding_cells - discovered_surrounding_safe_cells - discovered_surrounding_mine_cells
        undiscovered_surrounding_mines_count = count - len(discovered_surrounding_mine_cells)

        #     4) mark any additional cells as safe or as mines
        #        if it can be concluded based on the AI's knowledge base
        if (len(undiscovered_surrounding_cells) > 0 and undiscovered_surrounding_mines_count > 0):
            if len(undiscovered_surrounding_cells) == undiscovered_surrounding_mines_count:
                # all are mines
                for undiscovered_surrounding_cell in undiscovered_surrounding_cells:
                    self.mark_mine(undiscovered_surrounding_cell)
            else:
                self.knowledge.append(Sentence(undiscovered_surrounding_cells, undiscovered_surrounding_mines_count))

        #     5) add any new sentences to the AI's knowledge base
        #        if they can be inferred from existing knowledge
        self.consolidate_cells()

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        # known safe cells not in moves_made
        safe_unmade_moves = self.safes.difference(self.moves_made)
        if len(safe_unmade_moves):
            safe_unmade_move = safe_unmade_moves.pop()
            return safe_unmade_move
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
          * 3) not already picked
        """
        undiscovered_cells = list(self.get_undiscovered_cells())
        undiscovered_cells = list(filter(lambda x: x not in self.mines, undiscovered_cells))
        if len(undiscovered_cells) == 0:
            return None
        randomCell = undiscovered_cells[random.randint(0, len(undiscovered_cells) - 1)]
        return randomCell

    def surrounding_cells(self, cell):
        """
        returns set of surrounding cells
        """
        row, col = cell
        surrounding_cells = {(row - 1, col - 1), (row, col - 1), (row + 1, col - 1), (row - 1, col), (row + 1, col),
                             (row - 1, col + 1), (row, col + 1), (row + 1, col + 1)}

        surrounding_cells = set(filter(lambda x: x[0] >= 0, surrounding_cells))
        surrounding_cells = set(filter(lambda x: x[0] < self.height, surrounding_cells))
        surrounding_cells = set(filter(lambda x: x[1] >= 0, surrounding_cells))
        surrounding_cells = set(filter(lambda x: x[1] < self.width, surrounding_cells))
        return surrounding_cells

    def get_undiscovered_cells(self):
        """
        Returns set of unclicked boxes
        """
        undiscovered_cells = set()

        for i in range(self.height):
            for j in range(self.width):
                if (i, j) not in self.moves_made:
                    undiscovered_cells.add((i, j),)
        return undiscovered_cells

    def consolidate_cells(self):
        popping_indexes = []
        for idx, sentence in enumerate(self.knowledge):
            if len(sentence.cells) == 0:
                self.knowledge.remove(sentence)
            elif not sentence.count:
                sentence_cells = sentence.cells.copy()
                for cell in sentence_cells:
                    self.mark_safe(cell)
                self.knowledge.remove(sentence)
            elif (sentence.count == len(sentence.cells)):
                sentence_cells = sentence.cells.copy()
                for this_cell in sentence_cells:
                    self.mark_mine(this_cell)
                self.knowledge.remove(sentence)

        for idx1, sentence1 in enumerate(self.knowledge):
            for idx2, sentence2 in enumerate(self.knowledge):
                if idx1 is not idx2:
                    # if sentence1 is a subset of sentence2 and they have the same count, then the mine is in sentence1
                    if sentence1.cells.issubset(sentence2.cells):
                        if sentence1.cells == sentence2.cells:
                            self.knowledge.remove(sentence1)
                            continue
                        elif sentence1.count == sentence2.count:
                            # # make safe the difference of the cells
                            sentence_cells = sentence2.cells - sentence1.cells
                            for cell in sentence_cells:
                                self.mark_safe(cell)
                            self.knowledge.remove(sentence1)
                        elif len(sentence2.cells - sentence1.cells) == sentence2.count - sentence1.count and len(sentence2.cells - sentence1.cells) > 0:
                            # if a is subset of b, a's count is b's count - the difference of cells between a and b,
                            # then those extra cells are mines
                            sentence_cells = sentence2.cells - sentence1.cells
                            for cell in sentence_cells:
                                self.mark_mine(cell)

        if(len(popping_indexes)):
            popping_indexes.reverse()
            for idx in popping_indexes:
                self.knowledge.pop(idx)