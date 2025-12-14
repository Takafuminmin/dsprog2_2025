import flet as ft
import math


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK


class ScientificButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_300
        self.color = ft.Colors.WHITE


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()
        self.scientific_mode = False

        # 式の表示用テキスト
        self.expression = ft.Text(value="", color=ft.Colors.WHITE60, size=16)
        # 結果表示用テキスト
        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        
        # 標準モードの行を作成
        self.standard_rows = [
            ft.Row(
                controls=[
                    ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                    ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                    ExtraActionButton(text="%", button_clicked=self.button_clicked),
                    ActionButton(text="/", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    DigitButton(text="7", button_clicked=self.button_clicked),
                    DigitButton(text="8", button_clicked=self.button_clicked),
                    DigitButton(text="9", button_clicked=self.button_clicked),
                    ActionButton(text="*", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    DigitButton(text="4", button_clicked=self.button_clicked),
                    DigitButton(text="5", button_clicked=self.button_clicked),
                    DigitButton(text="6", button_clicked=self.button_clicked),
                    ActionButton(text="-", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    DigitButton(text="1", button_clicked=self.button_clicked),
                    DigitButton(text="2", button_clicked=self.button_clicked),
                    DigitButton(text="3", button_clicked=self.button_clicked),
                    ActionButton(text="+", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                    DigitButton(text=".", button_clicked=self.button_clicked),
                    ActionButton(text="=", button_clicked=self.button_clicked),
                ]
            ),
        ]
        
        # 科学計算モードの行を作成
        self.scientific_rows = [
            ft.Row(
                controls=[
                    ScientificButton(text="sin", button_clicked=self.button_clicked),
                    ScientificButton(text="cos", button_clicked=self.button_clicked),
                    ScientificButton(text="tan", button_clicked=self.button_clicked),
                    ScientificButton(text="π", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    ScientificButton(text="log", button_clicked=self.button_clicked),
                    ScientificButton(text="ln", button_clicked=self.button_clicked),
                    ScientificButton(text="√", button_clicked=self.button_clicked),
                    ScientificButton(text="e", button_clicked=self.button_clicked),
                ]
            ),
            ft.Row(
                controls=[
                    ScientificButton(text="x²", button_clicked=self.button_clicked),
                    ScientificButton(text="x^y", button_clicked=self.button_clicked),
                    ScientificButton(text="(", button_clicked=self.button_clicked),
                    ScientificButton(text=")", button_clicked=self.button_clicked),
                ]
            ),
        ]
        
        # モード切替ボタン
        self.mode_button = ft.ElevatedButton(
            text="Scientific Mode: OFF", 
            on_click=self.toggle_mode,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        # 初期表示は標準モード
        self.all_rows = [
            ft.Column(
                controls=[
                    self.expression,
                    self.result
                ],
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=5
            ), 
            ft.Row(controls=[self.mode_button])
        ]
        self.all_rows.extend(self.standard_rows)
        
        self.content = ft.Column(controls=self.all_rows)

    def toggle_mode(self, e):
        self.scientific_mode = not self.scientific_mode
        
        # ボタンのテキストを更新
        self.mode_button.text = f"Scientific Mode: {'ON' if self.scientific_mode else 'OFF'}"
        
        # 行を再構築
        self.all_rows = [
            ft.Column(
                controls=[
                    self.expression,
                    self.result
                ],
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=5
            ), 
            ft.Row(controls=[self.mode_button])
        ]
        
        if self.scientific_mode:
            self.all_rows.extend(self.scientific_rows)
        
        self.all_rows.extend(self.standard_rows)
        
        self.content.controls = self.all_rows
        self.update()

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.expression.value = ""
            self.reset()
        
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = self.result.value + data
        
        elif data in ("+", "-", "*", "/"):
            # 式を更新
            if self.expression.value == "":
                self.expression.value = f"{self.result.value} {data} "
            else:
                # 前の演算子を含む式に現在の値と新しい演算子を追加
                self.expression.value = f"{self.expression.value}{self.result.value} {data} "
            
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
                self.expression.value = ""
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True
        
        elif data == "=":
            # 式を完成させる
            if self.expression.value != "":
                self.expression.value = f"{self.expression.value}{self.result.value} = "
            
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            # 計算の履歴を保持
            previous_expression = self.expression.value
            self.reset()
            # 計算後も式を表示
            self.expression.value = previous_expression
        
        elif data == "%":
            self.result.value = float(self.result.value) / 100
            self.expression.value = f"{self.expression.value}{self.result.value}% = "
            self.reset()
        
        elif data == "+/-":
            if float(self.result.value) > 0:
                self.result.value = "-" + str(self.result.value)
            elif float(self.result.value) < 0:
                self.result.value = str(self.format_number(abs(float(self.result.value))))
        
        # 科学計算ボタンの処理
        elif data == "sin":
            try:
                value = float(self.result.value)
                result = math.sin(value)
                self.expression.value = f"sin({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "cos":
            try:
                value = float(self.result.value)
                result = math.cos(value)
                self.expression.value = f"cos({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "tan":
            try:
                value = float(self.result.value)
                result = math.tan(value)
                self.expression.value = f"tan({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "log":
            try:
                value = float(self.result.value)
                result = math.log10(value)
                self.expression.value = f"log({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "ln":
            try:
                value = float(self.result.value)
                result = math.log(value)
                self.expression.value = f"ln({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "√":
            try:
                value = float(self.result.value)
                result = math.sqrt(value)
                self.expression.value = f"√({value}) = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "x²":
            try:
                value = float(self.result.value)
                result = value ** 2
                self.expression.value = f"({value})² = "
                self.result.value = str(self.format_number(result))
            except:
                self.result.value = "Error"
                self.expression.value = ""
            self.reset()
        
        elif data == "x^y":
            self.operator = "^"
            self.operand1 = float(self.result.value)
            self.expression.value = f"{self.operand1} ^ "
            self.new_operand = True
        
        elif data == "π":
            self.result.value = str(self.format_number(math.pi))
            self.reset()
        
        elif data == "e":
            self.result.value = str(self.format_number(math.e))
            self.reset()
        
        elif data in ("(", ")"):
            # 括弧は今回は実装していません（複雑な式の解析が必要なため）
            pass

        self.update()

    def format_number(self, num):
        if num % 1 == 0:
            return int(num)
        else:
            # 小数点以下が多すぎる場合は丸める
            if abs(num) < 1e-10:
                return 0
            return round(num, 10)

    def calculate(self, operand1, operand2, operator):
        try:
            if operator == "+":
                return self.format_number(operand1 + operand2)
            elif operator == "-":
                return self.format_number(operand1 - operand2)
            elif operator == "*":
                return self.format_number(operand1 * operand2)
            elif operator == "/":
                if operand2 == 0:
                    return "Error"
                else:
                    return self.format_number(operand1 / operand2)
            elif operator == "^":
                return self.format_number(operand1 ** operand2)
            else:
                return operand2
        except:
            return "Error"

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator"
    calc = CalculatorApp()
    page.add(calc)


ft.app(main)