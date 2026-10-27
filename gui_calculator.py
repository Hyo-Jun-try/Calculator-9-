import ast
import operator
import tkinter as tk
from tkinter import messagebox

# eval() 대신 사용할 안전한 수식 계산기 (사칙연산, 괄호, 단항 +/- 만 허용)
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval(expression):
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("허용되지 않는 수식")

    return _eval(ast.parse(expression, mode="eval"))


def format_number(value):
    """3.0 -> 3, 0.30000000000000004 -> 0.3 처럼 보기 좋게 변환"""
    if isinstance(value, float):
        value = round(value, 10)
        if value == int(value):
            return str(int(value))
    return str(value)


class Calculator:
    OPERATORS = "+-*/"

    def __init__(self, root):
        self.root = root
        self.root.title("간단한 계산기")
        self.root.geometry("380x600")
        self.root.minsize(320, 520)

        self.result_var = tk.StringVar()
        self.just_evaluated = False  # 직전에 '='를 눌렀는지 여부

        # 세로 배치: 기록(위) / 입력창 / 버튼 / 기록 지우기
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=2)   # 기록 영역
        self.root.grid_rowconfigure(2, weight=5)   # 버튼 영역

        self._build_history()
        self._build_display()
        self._build_buttons()
        self._build_footer()
        self._bind_keys()

    # ---------- UI 구성 ----------
    def _build_history(self):
        frame = tk.Frame(self.root, bd=1, relief="sunken")
        frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.history_text = tk.Text(frame, height=6, font=("Consolas", 12),
                                    state="disabled", wrap="none", cursor="arrow",
                                    bd=0, bg="white")
        self.history_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(frame, command=self.history_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_text.config(yscrollcommand=scrollbar.set)

        # 기록 줄을 더블클릭하면 그 결과값을 입력창으로 불러옴
        self.history_text.bind("<Double-Button-1>", self.load_from_history)

    def _build_display(self):
        entry = tk.Entry(self.root, textvariable=self.result_var, font=("Arial", 26),
                         bd=4, justify="right", relief="sunken")
        entry.grid(row=1, column=0, sticky="ew", padx=6, pady=6, ipady=8)

    def _build_buttons(self):
        frame = tk.Frame(self.root)
        frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 4))

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+',
        ]

        for i, text in enumerate(buttons):
            row, col = divmod(i, 4)
            tk.Button(frame, text=text, font=("Arial", 16),
                      command=lambda x=text: self.click_event(x)
                      ).grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        for i in range(4):
            frame.grid_columnconfigure(i, weight=1)
            frame.grid_rowconfigure(i, weight=1)

    def _build_footer(self):
        tk.Button(self.root, text="기록 지우기", font=("Arial", 10),
                  command=self.clear_history
                  ).grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 6))

    def _bind_keys(self):
        self.root.bind("<Return>", lambda e: self.click_event('='))
        self.root.bind("<KP_Enter>", lambda e: self.click_event('='))
        self.root.bind("<BackSpace>", lambda e: self.click_event('⌫'))
        self.root.bind("<Escape>", lambda e: self.click_event('C'))
        for ch in "0123456789.+-*/()":
            self.root.bind(ch, lambda e, c=ch: self._on_keypress(c))

    def _on_keypress(self, char):
        self.click_event(char)
        return "break"

    # ---------- 동작 ----------
    def click_event(self, key):
        if key == '=':
            self.calculate()
        elif key == 'C':
            self.result_var.set("")
            self.just_evaluated = False
        elif key == '⌫':
            self.result_var.set(self.result_var.get()[:-1])
            self.just_evaluated = False
        else:
            # 계산 직후 숫자를 누르면 새 계산 시작, 연산자를 누르면 결과에 이어서 계산
            if self.just_evaluated and key not in self.OPERATORS:
                self.result_var.set("")
            self.just_evaluated = False
            self.result_var.set(self.result_var.get() + key)

    def calculate(self):
        expression = self.result_var.get().strip()
        if not expression:
            return
        try:
            result = format_number(safe_eval(expression))
        except ZeroDivisionError:
            messagebox.showerror("오류", "0으로 나눌 수 없습니다.")
            self.result_var.set("")
            return
        except Exception:
            messagebox.showerror("오류", "잘못된 입력입니다.")
            self.result_var.set("")
            return

        self.result_var.set(result)
        self.just_evaluated = True
        self.add_history(expression, result)

    def add_history(self, expression, result):
        self.history_text.config(state="normal")
        self.history_text.insert(tk.END, f"{expression} = {result}\n")
        self.history_text.config(state="disabled")
        self.history_text.see(tk.END)

    def load_from_history(self, event):
        index = self.history_text.index(f"@{event.x},{event.y} linestart")
        line = self.history_text.get(index, f"{index} lineend").strip()
        if " = " in line:
            self.result_var.set(line.split(" = ")[-1])
            self.just_evaluated = True
        return "break"

    def clear_history(self):
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)
        self.history_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    Calculator(root)
    root.mainloop()
