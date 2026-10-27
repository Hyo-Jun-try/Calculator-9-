import ast
import math
import operator
import re
import tkinter as tk
from tkinter import messagebox

MAX_FACTORIAL = 170


# ---------------------------------------------------------------
# 안전한 수식 계산기 (eval() 대신 사용)
# 허용: 사칙연산, 거듭제곱(^), 나머지(%), 괄호, 수학 함수, 상수(pi, e, ans)
# ---------------------------------------------------------------
def _safe_pow(a, b):
    # 너무 큰 거듭제곱으로 프로그램이 멈추는 것을 방지
    if a != 0 and b > 0 and b * math.log10(abs(a)) > 300:
        raise OverflowError("결과가 너무 큽니다")
    result = operator.pow(a, b)
    if isinstance(result, complex):
        raise ValueError("복소수 결과")
    return result


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: _safe_pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def build_functions(use_degrees):
    """각도 모드(DEG/RAD)에 맞는 함수 테이블 생성"""
    to_rad = math.radians if use_degrees else (lambda x: x)
    from_rad = math.degrees if use_degrees else (lambda x: x)

    def tan(x):
        r = to_rad(x)
        if abs(math.cos(r)) < 1e-12:
            raise ValueError("tan 값이 정의되지 않습니다")
        return math.tan(r)

    def factorial(n):
        if n != int(n) or n < 0 or n > MAX_FACTORIAL:
            raise ValueError("팩토리얼 범위 오류")
        return math.factorial(int(n))

    return {
        "sin": lambda x: math.sin(to_rad(x)),
        "cos": lambda x: math.cos(to_rad(x)),
        "tan": tan,
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        "ln": math.log,
        "log": math.log10,
        "sqrt": math.sqrt,
        "exp": math.exp,
        "abs": abs,
        "fact": factorial,
    }


def safe_eval(expression, use_degrees=True, ans=0):
    functions = build_functions(use_degrees)
    constants = {"pi": math.pi, "e": math.e, "ans": ans}

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and node.id in constants:
            return constants[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in functions
                and len(node.args) == 1 and not node.keywords):
            return functions[node.func.id](_eval(node.args[0]))
        raise ValueError("허용되지 않는 수식")

    result = _eval(ast.parse(expression, mode="eval"))
    if isinstance(result, complex):
        raise ValueError("복소수 결과")
    return result


# 2pi, 3(4), 2sin(30), (1+2)(3+4) 처럼 곱셈 기호가 생략된 입력을 처리
# (1e5 같은 지수 표기는 건드리지 않음)
_IMPLICIT_MUL = re.compile(r'(?<=[\d.)])\s*(?=\(|[a-df-zA-DF-Z]|[eE](?![+\-]?\d))')


def preprocess(expression):
    expression = (expression.replace('π', 'pi').replace('√', 'sqrt')
                  .replace('×', '*').replace('÷', '/').replace('^', '**'))
    return _IMPLICIT_MUL.sub('*', expression)


def format_number(value):
    """3.0 -> 3, 0.30000000000000004 -> 0.3, 아주 큰 수는 지수 표기"""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise OverflowError("결과가 너무 큽니다")
        value = round(value, 10)
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.12g}"
    if abs(value) >= 10 ** 15:
        return f"{value:.12g}"
    return str(value)


# ---------------------------------------------------------------
# GUI
# ---------------------------------------------------------------
class Calculator:
    # 버튼 배치 (5열 x 8행)
    BUTTON_ROWS = [
        ['DEG', 'Ans', '(', ')', 'C'],
        ['sin', 'cos', 'tan', 'π', '⌫'],
        ['asin', 'acos', 'atan', 'e', 'n!'],
        ['ln', 'log', '√', 'x²', '^'],
        ['7', '8', '9', '/', 'mod'],
        ['4', '5', '6', '*', '1/x'],
        ['1', '2', '3', '-', 'abs'],
        ['0', '.', '=', '+', 'eˣ'],
    ]

    # 버튼 라벨 -> 입력창에 들어갈 텍스트
    INSERT_MAP = {
        'sin': 'sin(', 'cos': 'cos(', 'tan': 'tan(',
        'asin': 'asin(', 'acos': 'acos(', 'atan': 'atan(',
        'ln': 'ln(', 'log': 'log(', '√': 'sqrt(', 'abs': 'abs(',
        'eˣ': 'exp(', 'n!': 'fact(',
        'π': 'pi', 'Ans': 'ans', 'x²': '^2', 'mod': '%',
    }

    # 계산 직후 눌러도 결과에 이어서 계산되는 입력
    CONTINUE_TOKENS = {'+', '-', '*', '/', '^', '%', '^2'}

    FUNCTION_BUTTONS = {'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'ln', 'log',
                        '√', 'x²', '^', 'mod', '1/x', 'abs', 'eˣ', 'n!',
                        'π', 'e', 'Ans', '(', ')', 'DEG'}

    # 백스페이스 시 함수명("sin(")이나 상수("pi", "ans")를 한 번에 지우기 위한 패턴
    _BACKSPACE = re.compile(
        r'(?:asin|acos|atan|sin|cos|tan|ln|log|sqrt|exp|abs|fact)\($|(?:pi|ans)$|.$')

    def __init__(self, root):
        self.root = root
        self.root.title("공학용 계산기")
        self.root.geometry("480x780")
        self.root.minsize(400, 680)

        self.result_var = tk.StringVar()
        self.just_evaluated = False   # 직전에 '='를 눌렀는지 여부
        self.use_degrees = True       # True: DEG, False: RAD
        self.last_answer = 0          # Ans 버튼용 직전 계산 결과

        # 세로 배치: 기록(위) / 입력창 / 버튼 / 기록 지우기
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=2)   # 기록 영역
        self.root.grid_rowconfigure(2, weight=7)   # 버튼 영역

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
        # readonly: 키보드 입력이 중복 처리되지 않도록 직접 편집은 막음
        entry = tk.Entry(self.root, textvariable=self.result_var, font=("Arial", 24),
                         bd=4, justify="right", relief="sunken",
                         state="readonly", readonlybackground="white")
        entry.grid(row=1, column=0, sticky="ew", padx=6, pady=6, ipady=8)

    def _build_buttons(self):
        frame = tk.Frame(self.root)
        frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 4))

        for r, row in enumerate(self.BUTTON_ROWS):
            frame.grid_rowconfigure(r, weight=1)
            for c, text in enumerate(row):
                if text == '=':
                    bg = "#bfe0ff"
                elif text in ('C', '⌫'):
                    bg = "#f8d7da"
                elif text in self.FUNCTION_BUTTONS:
                    bg = "#e6edf7"
                else:
                    bg = "#ffffff"
                btn = tk.Button(frame, text=text, font=("Arial", 13), bg=bg,
                                command=lambda x=text: self.click_event(x))
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                if text == 'DEG':
                    self.angle_button = btn
        for c in range(5):
            frame.grid_columnconfigure(c, weight=1)

    def _build_footer(self):
        tk.Button(self.root, text="기록 지우기", font=("Arial", 10),
                  command=self.clear_history
                  ).grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 6))

    def _bind_keys(self):
        self.root.bind("<Return>", lambda e: self.click_event('='))
        self.root.bind("<KP_Enter>", lambda e: self.click_event('='))
        self.root.bind("<BackSpace>", lambda e: self.click_event('⌫'))
        self.root.bind("<Escape>", lambda e: self.click_event('C'))
        for ch in "0123456789.+-*/()^%":
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
            self.result_var.set(self._BACKSPACE.sub('', self.result_var.get(), count=1))
            self.just_evaluated = False
        elif key == 'DEG':
            self.toggle_angle_mode()
        elif key == '1/x':
            self.reciprocal()
        else:
            self.insert_text(self.INSERT_MAP.get(key, key))

    def insert_text(self, text):
        # 계산 직후 숫자/함수를 누르면 새 계산 시작, 연산자를 누르면 결과에 이어서 계산
        if self.just_evaluated and text not in self.CONTINUE_TOKENS:
            self.result_var.set("")
        self.just_evaluated = False
        self.result_var.set(self.result_var.get() + text)

    def toggle_angle_mode(self):
        self.use_degrees = not self.use_degrees
        self.angle_button.config(text="DEG" if self.use_degrees else "RAD")

    def reciprocal(self):
        text = self.result_var.get().strip()
        if text:
            self.result_var.set(f"1/({text})")
            self.just_evaluated = False
            self.calculate()
        else:
            self.result_var.set("1/(")

    def calculate(self):
        expression = self.result_var.get().strip()
        if not expression:
            return
        try:
            value = safe_eval(preprocess(expression), self.use_degrees, self.last_answer)
            result = format_number(value)
        except ZeroDivisionError:
            messagebox.showerror("오류", "0으로 나눌 수 없습니다.")
            self.result_var.set("")
            return
        except OverflowError:
            messagebox.showerror("오류", "결과가 너무 크거나 계산 범위를 벗어났습니다.")
            self.result_var.set("")
            return
        except Exception:
            messagebox.showerror("오류", "잘못된 입력입니다.\n(정의되지 않는 값이거나 수식 형식 오류)")
            self.result_var.set("")
            return

        self.last_answer = value
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
