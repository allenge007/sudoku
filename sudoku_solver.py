import tkinter as tk
from tkinter import ttk
import copy

def possible_number_inference(grid):
    """
    根据当前棋盘排除同行、列和宫格中的确定值，
    计算每个未确定单元格的候选值(集)
    
    @param grid: 9x9 数独棋盘，数字 0 表示未填写
    @return: 9x9x9 三维列表，每个内部列表保存候选值状态（索引0表示数字1是否可填）
    """
    candidates = [[[True for _ in range(9)] for _ in range(9)] for _ in range(9)]
    def in_row(row, num):
        for j in range(9):
            if grid[row][j] == num:
                return True
        return False
    def in_col(col, num):
        for i in range(9):
            if grid[i][col] == num:
                return True
        return False
    def in_block(row, col, num):
        br = (row // 3) * 3
        bc = (col // 3) * 3
        for i in range(br, br+3):
            for j in range(bc, bc+3):
                if grid[i][j] == num:
                    return True
        return False
    for i in range(9):
        for j in range(9):
            if grid[i][j] != 0:
                # 已确定的数字：候选数组只保留该数字
                for k in range(9):
                    candidates[i][j][k] = (k == grid[i][j] - 1)
            else:
                for num in range(1, 10):
                    if in_row(i, num) or in_col(j, num) or in_block(i, j, num):
                        candidates[i][j][num-1] = False
    return candidates

def process_unique_candidate(get_cells, grid, candidates, num, update_peers):
    """
    检查在由 get_cells() 返回的一系列 (i, j) 坐标中，
    是否只有唯一一个空位可填入数字 num。
    
    @param get_cells: 一个迭代器，返回待检查区域内所有 (i, j) 坐标。
    @param grid: 当前 9x9 数独棋盘（0 表示空位）。
    @param candidates: 当前候选数组，一般为 9x9x9 三维列表。
    @param num: 待确定的数字（1~9）。
    @param update_peers: 当确定了某格数字时，用于更新该格同行、列和宫的函数。
    @return: 如果唯一候选成立，则在该位置填入数字 num，更新候选数组，并返回 True；否则返回 False。
    """
    count = 0
    pos = None
    for i, j in get_cells():
        if grid[i][j] == 0 and candidates[i][j][num-1]:
            count += 1
            pos = (i, j)
    if count == 1 and pos is not None:
        i, j = pos
        grid[i][j] = num
        for k in range(9):
            candidates[i][j][k] = (k == num - 1)
        update_peers(i, j, num)
        return True
    return False

def last_remaining_cell_inference(grid):
    """
    利用“唯一候选”原则，从当前已知棋盘及候选值中推断确定值：
    如果在某个区域（行、列、宫格）中，只有唯一的空位可以填入某个候选值，
    则将该候选值确定在该单元格，并更新邻近单元格的候选值。
    
    @param grid: 9x9 数独棋盘，数字 0 表示未填写
    @return: 返回推理使用的候选数组（同时 grid 内的 0 被替换为确定数字）
    """
    candidates = possible_number_inference(grid)
    progress = True
    def update_peers(row, col, num):
        idx = num - 1
        for k in range(9):
            if k != col and grid[row][k] == 0:
                candidates[row][k][idx] = False
            if k != row and grid[k][col] == 0:
                candidates[k][col][idx] = False
        br = (row // 3) * 3
        bc = (col // 3) * 3
        for i in range(br, br+3):
            for j in range(bc, bc+3):
                if (i != row or j != col) and grid[i][j] == 0:
                    candidates[i][j][idx] = False
    
    while progress:
        progress = False
        # 检查每一行的唯一候选
        for row in range(9):
            for num in range(1, 10):
                if process_unique_candidate(lambda: ((row, col) for col in range(9)),
                                            grid, candidates, num, update_peers):
                    progress = True
        # 检查每一列的唯一候选
        for col in range(9):
            for num in range(1, 10):
                if process_unique_candidate(lambda: ((row, col) for row in range(9)),
                                            grid, candidates, num, update_peers):
                    progress = True
        # 检查每个 3x3 宫格内的唯一候选
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                for num in range(1, 10):
                    if process_unique_candidate(lambda: ((i, j) for i in range(br, br+3)
                                                        for j in range(bc, bc+3)),
                                                grid, candidates, num, update_peers):
                        progress = True
    return candidates

def board_from_candidates(candidates):
    """
    根据候选值（三维列表），如果候选数字唯一，则返回该数字，否则返回 0
    """
    board = [[0 for _ in range(9)] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if candidates[i][j].count(True) == 1:
                board[i][j] = candidates[i][j].index(True) + 1
    return board

def draw_possible_board(parent, board, candidates, initial_grid):
    """
    绘制 Possible Number Inference 界面：
    若空白格候选不唯一，则按 3×3 格式显示所有可能数字（调整字号和居中），
    若候选唯一，则显示确定数字（大字号）。
    对于初始时已有的数字（initial_grid 非 0），用特殊颜色标明（例如红色）。
    每个单元格采用固定大小的像素值显示。
    """
    cell_width = 50   # 每个单元格宽 50 像素
    cell_height = 50  # 每个单元格高 50 像素

    for block_row in range(3):
        for block_col in range(3):
            block_frame = tk.Frame(parent, borderwidth=2, relief="solid",
                                   width=cell_width*3, height=cell_height*3)
            block_frame.grid(row=block_row, column=block_col, padx=0, pady=0, sticky="nsew")
            # 防止框架自动调整尺寸
            block_frame.grid_propagate(False)
            for i in range(3):
                for j in range(3):
                    r = block_row * 3 + i
                    c = block_col * 3 + j
                    if initial_grid[r][c] != 0:
                        text = str(initial_grid[r][c])
                        font = ("Helvetica", 18)
                        fg = "red"
                    elif board[r][c] != 0:
                        text = str(board[r][c])
                        font = ("Helvetica", 18)
                        fg = "blue"
                    else:
                        nums = candidates[r][c]
                        line1 = " ".join(str(n+1) if nums[n] else " " for n in range(0,3))
                        line2 = " ".join(str(n+1) if nums[n] else " " for n in range(3,6))
                        line3 = " ".join(str(n+1) if nums[n] else " " for n in range(6,9))
                        text = line1 + "\n" + line2 + "\n" + line3
                        # 使用等宽字体 Courier 保证字符宽度一致
                        font = ("Courier", 10)
                        fg = "black"
                    lbl = tk.Label(block_frame, text=text, font=font, fg=fg,
                                   borderwidth=1, relief="ridge", justify="center", anchor="center")
                    # 使用 place 布局以固定单元格尺寸
                    lbl.place(x=j*cell_width, y=i*cell_height, width=cell_width, height=cell_height)
            for j in range(3):
                block_frame.grid_columnconfigure(j, weight=1)
            for i in range(3):
                block_frame.grid_rowconfigure(i, weight=1)
    for i in range(3):
        parent.grid_rowconfigure(i, minsize=cell_height)
    for j in range(3):
        parent.grid_columnconfigure(j, minsize=cell_width)

def draw_last_board(parent, board, initial_grid):
    """
    绘制 Last Remaining Cell Inference 结果：
    若 cell 中有数字，则以大字号显示；
    对于初始给出的数字，用特殊颜色显示（例如红色），而推理得到的新数字则用蓝色标识。
    每个单元格采用固定像素大小显示（如 50×50）。
    """
    cell_width = 50
    cell_height = 50

    for block_row in range(3):
        for block_col in range(3):
            block_frame = tk.Frame(parent, borderwidth=2, relief="solid",
                                   width=cell_width*3, height=cell_height*3)
            block_frame.grid(row=block_row, column=block_col, padx=0, pady=0, sticky="nsew")
            block_frame.grid_propagate(False)
            for i in range(3):
                for j in range(3):
                    r = block_row * 3 + i
                    c = block_col * 3 + j
                    num = board[r][c]
                    if num != 0:
                        text = str(num)
                        font = ("Helvetica", 18)
                        # 若为原始预设数字则显示红色，否则蓝色（即推理得到的数字）
                        fg = "red" if initial_grid[r][c] != 0 else "blue"
                    else:
                        text = ""
                        font = ("Helvetica", 18)
                        fg = "black"
                    lbl = tk.Label(block_frame, text=text, font=font, fg=fg, borderwidth=1,
                                   relief="ridge", justify="center", anchor="center")
                    lbl.place(x=j*cell_width, y=i*cell_height, width=cell_width, height=cell_height)
            for j in range(3):
                block_frame.grid_columnconfigure(j, weight=1)
            for i in range(3):
                block_frame.grid_rowconfigure(i, weight=1)
    for i in range(3):
        parent.grid_rowconfigure(i, minsize=cell_height)
    for j in range(3):
        parent.grid_columnconfigure(j, minsize=cell_width)

def create_gui():
    # 构造 example_grid 数据，这里选择部分填数字的棋盘作为初始数据
    # 使用 example_grid[2] 作为测试棋盘，同时保存原始数据
    num = int(input("请输入要使用的棋盘编号："))
    if num not in range(len(example_grid)):
        print("输入错误，使用默认棋盘编号 0")
        num = 0
    num = int(num)
    test_grid = example_grid[num]
    print(f"使用棋盘编号 {num} 进行推理：")

    board_for_last = copy.deepcopy(test_grid)
    # last_remaining_cell_inference 会在 board_for_last 上直接填入确定数字
    last_remaining_cell_inference(board_for_last)
    board_last = board_for_last

    initial_grid = copy.deepcopy(test_grid)
    board_input = copy.deepcopy(board_for_last)
    possible_candidates = possible_number_inference(board_input)
    board_possible = board_from_candidates(possible_candidates)
    print("Possible Number Inference 结果：")

    root = tk.Tk()
    root.title("数独推理结果")
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Tab1: 显示 Possible Number Inference 结果
    frame1 = ttk.Frame(notebook)
    notebook.add(frame1, text="Possible Number Inference")
    board_frame1 = tk.Frame(frame1)
    board_frame1.pack(expand=True, fill="both", padx=10, pady=10)
    draw_possible_board(board_frame1, board_possible, possible_candidates, initial_grid)

    # Tab2: 显示 Last Remaining Cell Inference 结果
    frame2 = ttk.Frame(notebook)
    notebook.add(frame2, text="Last Remaining Cell Inference")
    board_frame2 = tk.Frame(frame2)
    board_frame2.pack(expand=True, fill="both", padx=10, pady=10)
    draw_last_board(board_frame2, board_last, initial_grid)

    root.mainloop()

def is_valid_sudoku(board):
    """
    检查 board 是否符合数独规则。
    board 为 9x9 数独棋盘，0 表示空位，仅检查非 0 数字是否重复。
    """
    # 检查行
    for row in board:
        seen = set()
        for num in row:
            if num != 0:
                if num in seen:
                    return False
                seen.add(num)
    # 检查列
    for col in range(9):
        seen = set()
        for row in range(9):
            num = board[row][col]
            if num != 0:
                if num in seen:
                    return False
                seen.add(num)
    # 检查九宫格
    for block_row in range(3):
        for block_col in range(3):
            seen = set()
            for i in range(block_row*3, block_row*3+3):
                for j in range(block_col*3, block_col*3+3):
                    num = board[i][j]
                    if num != 0:
                        if num in seen:
                            return False
                        seen.add(num)
    return True

import random

def run_checker():
    """
    使用示例棋盘运行推理，并检查推理后（last remaining cell inference）棋盘是否符合数独规则。
    检查时仅判断所有已确定数字是否冲突，不要求解完全。
    """
    import copy
    # 使用 example_grid 中的所有测试棋盘 
    for idx, grid in enumerate(example_grid):
        print(f"\nChecker: 测试棋盘编号 {idx}")
        # 复制测试棋盘，保留原始数据
        test_grid = copy.deepcopy(grid)
        initial = copy.deepcopy(test_grid)
        board_for_last = copy.deepcopy(test_grid)
        # 运行推理
        last_remaining_cell_inference(board_for_last)
        # 打印推理后的棋盘
        print("推理后棋盘:")
        for row in board_for_last:
            print(row)
        # 检查数独规则是否成立
        if is_valid_sudoku(board_for_last):
            print("Checker: 棋盘满足数独规则")
        else:
            print("Checker: 棋盘违规！")

def valid_option(board, row, col, num):
    """
    检查在棋盘 board 的 (row, col) 位置填入 num 是否符合数独规则。
    """
    # 检查行
    if any(board[row][j] == num for j in range(9)):
        return False
    # 检查列
    if any(board[i][col] == num for i in range(9)):
        return False
    # 检查九宫格
    br = (row // 3) * 3
    bc = (col // 3) * 3
    for i in range(br, br+3):
        for j in range(bc, bc+3):
            if board[i][j] == num:
                return False
    return True

def generate_random_board(fill_rate=0.3):
    """
    随机生成一个部分填数字的 9x9 数独棋盘。
    fill_rate 决定每个格子有多大概率填充数字（保证生成时不冲突）。
    如果某格随机决定填数字，则从其可能的候选中随机选择一个（若候选为空，则置 0）。
    """
    board = [[0 for _ in range(9)] for _ in range(9)]
    for i in range(9):
        for j in range(9):
            if random.random() < fill_rate:
                options = [num for num in range(1, 10) if valid_option(board, i, j, num)]
                if options:
                    board[i][j] = random.choice(options)
                else:
                    board[i][j] = 0
    return board

def run_random_checker(num_boards=5, fill_rate=0.3):
    """
    生成 num_boards 个随机棋盘，并分别运行 last_remaining_cell_inference
    与 possible_board（由 board_from_candidates 得到）推理，
    最后用 is_valid_sudoku 检查推理后棋盘是否合法。
    """
    import copy
    for idx in range(num_boards):
        print(f"\n【随机测试】 棋盘编号 {idx}")
        board = generate_random_board(fill_rate)
        print("生成随机棋盘:")
        for row in board:
            print(row)
            
        # 1. 使用 last_remaining_cell_inference 进行推理
        board_for_last = copy.deepcopy(board)
        last_remaining_cell_inference(board_for_last)
        print("\n推理后棋盘 (Last Remaining Cell Inference):")
        for row in board_for_last:
            print(row)
        if is_valid_sudoku(board_for_last):
            print("随机测试结果 (Last Inference): 棋盘满足数独规则")
        else:
            print("随机测试结果 (Last Inference): 棋盘违规！")
            
        # 2. 通过 possible_number_inference 得到 tablero (possible_board)
        board_for_possible = copy.deepcopy(board_for_last)
        possible_candidates = possible_number_inference(board_for_possible)
        board_possible = board_from_candidates(possible_candidates)
        print("\n推理后棋盘 (Possible Number Inference):")
        for row in possible_candidates:
            for cell in row:
                row_num = possible_candidates.index(row)
                col_num = row.index(cell)
                if board_for_last[row_num][col_num] != 0:
                    continue
                for num in cell:
                    if num == False:
                        continue
                    num_num = cell.index(num) + 1
                    
                    if valid_option(board_for_possible, row_num, col_num, num_num) == 0:
                        print("候选数字不符合数独规则！")
                        print(f"行：{row_num} 列：{col_num} 候选数字：{num_num}")
                        for num in cell:
                            if num == False:
                                continue
                            num_num = cell.index(num) + 1
                            print(f"候选数字：{num_num}")
                        exit(1)
        if is_valid_sudoku(board_possible):
            print("随机测试结果 (Possible Inference): 棋盘满足数独规则")
        else:
            print("随机测试结果 (Possible Inference): 棋盘违规！")

if __name__ == '__main__':
    # 运行 GUI 前可以运行 checker 验证推理结果
    example_grid = [
        # 空棋盘备用
        [[0 for _ in range(9)] for _ in range(9)],
        # 部分填数字的棋盘
        [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9]
        ],
        # 测试棋盘：大多数空位候选数字较多
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 5, 0, 0, 0, 0],
            [0, 7, 0, 0, 0, 0, 0, 2, 0],
            [0, 0, 0, 1, 0, 2, 0, 0, 0],
            [0, 4, 0, 0, 0, 0, 0, 6, 0],
            [0, 0, 0, 0, 8, 0, 0, 0, 0],
            [9, 0, 0, 0, 0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
        [
            [2, 0, 0, 0, 7, 0, 0, 3, 8],
            [0, 0, 0, 0, 0, 6, 0, 7, 0],
            [3, 0, 0, 0, 4, 0, 6, 0, 0],
            [0, 0, 8, 0, 2, 0, 7, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 6],
            [0, 0, 7, 0, 3, 0, 4, 0, 0],
            [0, 0, 4, 0, 8, 0, 0, 0, 9],
            [0, 6, 0, 4, 0, 0, 0, 0, 0],
            [9, 1, 0, 0, 6, 0, 0, 0, 2],
        ],
        [
            [0, 7, 0, 0, 0, 8, 0, 2, 9],
            [0, 0, 2, 0, 0, 0, 0, 0, 4],
            [8, 5, 4, 0, 2, 0, 0, 0, 0],
            [0, 0, 8, 3, 7, 4, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 2, 6, 1, 7, 0, 0],
            [0, 0, 0, 0, 9, 0, 6, 1, 2],
            [2, 0, 0, 0, 0, 0, 4, 0, 0],
            [1, 3, 0, 6, 0, 0, 0, 7, 0],
        ],
        [
            # Medium
            [0, 0, 0, 0, 7, 2, 0, 0, 0],
            [6, 0, 0, 0, 3, 0, 0, 0, 0],
            [0, 2, 7, 5, 0, 9, 6, 1, 0],
            [1, 0, 5, 0, 6, 0, 4, 2, 0],
            [9, 0, 2, 0, 1, 5, 3, 0, 0],
            [0, 0, 0, 9, 0, 0, 0, 6, 1],
            [4, 0, 6, 1, 0, 0, 8, 3, 0],
            [7, 0, 0, 0, 8, 0, 1, 9, 0],
            [0, 1, 8, 0, 9, 6, 0, 4, 5],
        ],
        [
            # Hard
            [0, 0, 2, 3, 7, 0, 0, 5, 0],
            [1, 0, 0, 0, 2, 9, 0, 0, 0],
            [0, 0, 4, 0, 6, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 4, 0, 0, 6],
            [6, 0, 0, 2, 5, 0, 0, 1, 8],
            [0, 2, 7, 0, 0, 0, 0, 0, 5],
            [4, 0, 0, 8, 3, 0, 5, 0, 1],
            [0, 0, 0, 0, 0, 0, 9, 0, 0],
            [7, 5, 0, 0, 0, 0, 0, 4, 2],
        ],
        [
            # Expert
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 3, 0, 2, 1, 0, 0, 4, 0],
            [1, 0, 0, 7, 0, 0, 0, 8, 9],
            [0, 4, 5, 9, 0, 0, 0, 1, 7],
            [7, 2, 6, 0, 0, 0, 3, 0, 4],
            [0, 0, 1, 4, 7, 0, 2, 0, 0],
            [0, 1, 3, 0, 6, 8, 0, 0, 0],
            [6, 0, 0, 0, 4, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 7, 0, 0, 0],
        ],
        [
            [0, 0, 8, 9, 0, 0, 0, 2, 5],
            [0, 5, 0, 0, 7, 0, 0, 0, 8],
            [0, 0, 9, 5, 0, 8, 0, 3, 6],
            [0, 0, 0, 8, 3, 5, 2, 7, 1],
            [0, 0, 0, 7, 6, 4, 3, 5, 9],
            [5, 3, 7, 2, 1, 9, 6, 8, 4],
            [0, 6, 5, 3, 0, 0, 0, 0, 7],
            [0, 0, 0, 1, 9, 0, 0, 0, 3],
            [0, 0, 0, 0, 8, 0, 5, 0, 2],
        ]
    ]
    run_random_checker(num_boards=100, fill_rate=0.3)
    info = input("是否运行 GUI 界面？(y/n): ")
    if info.lower() == 'y':
        create_gui()
    else:
        print("退出程序。")
    # run_checker()
    # create_gui()