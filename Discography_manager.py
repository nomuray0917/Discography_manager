import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import re
import calendar
import json
from datetime import datetime

# --- ユーティリティ関数 ---

def get_ordinal(n):
    """数字を英語の序数形式 (1st, 2nd...) に変換"""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def sanitize_filename(filename):
    """ファイル名に使えない文字を除去"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# --- アプリケーションクラス ---

class DiscographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discography Manager")
        self.root.geometry("650x850") # 幅を少し広げる
        
        # カラーパレットとフォント定義
        self.colors = {
            "bg": "#f4f7f6",        # 全体の背景色
            "card_bg": "#ffffff",   # 入力エリアの背景色
            "primary": "#4a90e2",   # メインボタン色（青）
            "secondary": "#ffffff", # サブボタン色
            "text": "#333333",      # 文字色
            "accent": "#50c878",    # アクセント
            "danger": "#ff6b6b"     # 削除ボタンなど
        }
        self.fonts = {
            "header": ("Helvetica", 14, "bold"),
            "label": ("Helvetica", 10),
            "entry": ("Helvetica", 10),
            "button": ("Helvetica", 10, "bold"),
            "small_btn": ("Helvetica", 8)
        }

        self.root.configure(bg=self.colors["bg"])
        
        # スタイル設定
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=self.fonts["label"])
        self.style.configure("Card.TLabel", background=self.colors["card_bg"], foreground=self.colors["text"], font=self.fonts["label"])
        self.style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=self.fonts["header"])
        self.style.configure("TButton", font=self.fonts["button"], padding=6)
        
        # メインコンテナ
        main_container = ttk.Frame(root, padding=20)
        main_container.pack(fill="both", expand=True)

        # --- ヘッダーエリア ---
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(header_frame, text="Discography Manager", style="Header.TLabel").pack(side="left")
        
        btn_load = tk.Button(
            header_frame, 
            text="📂 プロジェクトを開く", 
            command=self.load_file,
            bg="white", fg="#555", 
            relief="flat", bd=1,
            font=("Helvetica", 9),
            padx=10, pady=4
        )
        btn_load.pack(side="right")

        # --- 保存先設定 ---
        self._create_path_section(main_container)

        # --- 基本情報カード ---
        self._create_basic_info_card(main_container)

        # --- 曲目リストカード ---
        self._create_tracklist_card(main_container)

        # --- アクションボタンエリア ---
        self._create_action_area(main_container)


    def _create_path_section(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(frame, text="保存先フォルダ:").pack(anchor="w", pady=(0, 2))
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x")
        
        self.path_var = tk.StringVar(value=os.getcwd())
        
        entry = ttk.Entry(input_frame, textvariable=self.path_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)
        
        btn = tk.Button(input_frame, text="参照", command=self.select_folder, bg="#e0e0e0", relief="flat", padx=10)
        btn.pack(side="right")

    def _create_basic_info_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill="x", pady=(0, 15))
        
        # --- 1行目: 日付 ---
        date_row = ttk.Frame(card, style="Card.TFrame")
        date_row.pack(fill="x", pady=(0, 10))
        
        ttk.Label(date_row, text="リリース日", style="Card.TLabel").pack(anchor="w")
        
        date_inputs = ttk.Frame(date_row, style="Card.TFrame")
        date_inputs.pack(fill="x", pady=(5, 0))

        # 年
        current_year = datetime.now().year
        self.year_var = tk.StringVar(value=str(current_year))
        self.year_var.trace_add("write", self.update_days_options)
        ttk.Entry(date_inputs, textvariable=self.year_var, width=8).pack(side="left")
        ttk.Label(date_inputs, text="年", style="Card.TLabel").pack(side="left", padx=(2, 10))

        # 月
        current_month = f"{datetime.now().month:02d}"
        months = [f"{m:02d}" for m in range(1, 13)]
        self.month_var = tk.StringVar(value=current_month)
        self.month_combo = ttk.Combobox(date_inputs, textvariable=self.month_var, values=months, width=4, state="readonly")
        self.month_combo.pack(side="left")
        self.month_combo.bind("<<ComboboxSelected>>", self.update_days_options)
        ttk.Label(date_inputs, text="月", style="Card.TLabel").pack(side="left", padx=(2, 10))

        # 日
        current_day = f"{datetime.now().day:02d}"
        self.day_var = tk.StringVar(value=current_day)
        self.day_combo = ttk.Combobox(date_inputs, textvariable=self.day_var, width=4, state="readonly")
        self.day_combo.pack(side="left")
        ttk.Label(date_inputs, text="日", style="Card.TLabel").pack(side="left", padx=(2, 0))

        self.update_days_options()

        # --- 2行目: 何作目 & 種別 ---
        meta_row = ttk.Frame(card, style="Card.TFrame")
        meta_row.pack(fill="x", pady=(0, 10))
        
        col1 = ttk.Frame(meta_row, style="Card.TFrame")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(col1, text="何作目 (数字)", style="Card.TLabel").pack(anchor="w")
        self.order_entry = ttk.Entry(col1)
        self.order_entry.pack(fill="x", pady=(2, 0), ipady=3)
        
        col2 = ttk.Frame(meta_row, style="Card.TFrame")
        col2.pack(side="left", fill="x", expand=True)
        ttk.Label(col2, text="種別", style="Card.TLabel").pack(anchor="w")
        
        disc_types = ["Single", "Album", "EP", "Demo", "Mini Album", "Digital Single", "Best Album", "Live Album", "Compilation", "Remix Album", "Soundtrack"]
        self.type_entry = ttk.Combobox(col2, values=disc_types)
        self.type_entry.pack(fill="x", pady=(2, 0), ipady=3)

        # --- 3行目: タイトル ---
        title_row = ttk.Frame(card, style="Card.TFrame")
        title_row.pack(fill="x")
        ttk.Label(title_row, text="タイトル (ファイル名)", style="Card.TLabel").pack(anchor="w")
        self.title_entry = ttk.Entry(title_row)
        self.title_entry.pack(fill="x", pady=(2, 0), ipady=3)

    def _create_tracklist_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill="both", expand=True, pady=(0, 15))
        
        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 5))
        ttk.Label(header, text="トラックリスト", style="Card.TLabel", font=("Helvetica", 11, "bold")).pack(side="left")
        
        tk.Button(
            header, text="+ 曲を追加", 
            command=lambda: self.add_track(),
            bg="#f0f0f0", relief="flat", font=("Helvetica", 9), padx=8
        ).pack(side="right")
        
        self.tracks_frame = ttk.Frame(card, style="Card.TFrame")
        self.tracks_frame.pack(fill="both", expand=True)
        
        self.track_entries = []
        self.add_track() 

    def _create_action_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="x")
        
        btn_json = tk.Button(
            frame, 
            text="プロジェクト保存 (.json)", 
            command=self.save_project_json,
            bg="white", fg="#555",
            relief="flat", bd=0,
            font=("Helvetica", 10, "bold"),
            pady=10, cursor="hand2"
        )
        btn_json.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_txt = tk.Button(
            frame, 
            text="テキスト書き出し (.txt)", 
            command=self.save_text_file,
            bg=self.colors["primary"], fg="white",
            relief="flat", bd=0,
            font=("Helvetica", 10, "bold"),
            pady=10, cursor="hand2"
        )
        btn_txt.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # --- ロジック部分 ---

    def update_days_options(self, *args):
        try:
            year_str = self.year_var.get()
            month_str = self.month_var.get()
            if not year_str.isdigit() or not month_str: return

            year = int(year_str)
            month = int(month_str)
            _, max_days = calendar.monthrange(year, month)
            
            days = [f"{d:02d}" for d in range(1, max_days + 1)]
            self.day_combo['values'] = days
            
            current_selection = self.day_var.get()
            if current_selection and current_selection.isdigit():
                if int(current_selection) > max_days:
                    self.day_var.set(f"{max_days:02d}")
        except ValueError:
            pass

    def add_track(self, initial_name="", initial_inst=False, refresh=True):
        """トラック行を追加。refresh=Falseにすると追加後の再描画をスキップ（大量追加時の高速化用）"""
        
        # 行コンテナ
        row = ttk.Frame(self.tracks_frame, style="Card.TFrame")
        
        # 1. 番号ラベル
        lbl = ttk.Label(row, text=".", width=3, anchor="e", style="Card.TLabel", foreground="#888")
        lbl.pack(side="left")
        
        # 2. 入力欄
        entry = ttk.Entry(row)
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        entry.insert(0, initial_name)
        
        # 3. Instチェック
        is_inst_var = tk.BooleanVar(value=initial_inst)
        chk = tk.Checkbutton(
            row, text="Inst", variable=is_inst_var,
            bg=self.colors["card_bg"], fg="#666", 
            activebackground=self.colors["card_bg"],
            selectcolor="white", relief="flat"
        )
        chk.pack(side="left", padx=5)

        # 4. 操作ボタン (上へ、下へ、削除)
        btn_frame = ttk.Frame(row, style="Card.TFrame")
        btn_frame.pack(side="left", padx=(5, 0))
        
        # 上へ
        tk.Button(btn_frame, text="▲", command=lambda r=row: self.move_track(r, -1),
                  bg="#f0f0f0", relief="flat", font=self.fonts["small_btn"], width=2).pack(side="left", padx=1)
        # 下へ
        tk.Button(btn_frame, text="▼", command=lambda r=row: self.move_track(r, 1),
                  bg="#f0f0f0", relief="flat", font=self.fonts["small_btn"], width=2).pack(side="left", padx=1)
        # 削除
        tk.Button(btn_frame, text="✕", command=lambda r=row: self.delete_track(r),
                  bg="#fff0f0", fg=self.colors["danger"], relief="flat", font=self.fonts["small_btn"], width=2).pack(side="left", padx=(3, 0))

        # 管理リストに追加
        self.track_entries.append({
            "row": row,
            "label": lbl,
            "entry": entry,
            "var": is_inst_var
        })
        
        # 画面に追加
        row.pack(fill="x", pady=2)
        
        if refresh:
            self.refresh_track_list()

    def move_track(self, row_widget, direction):
        """トラックを移動 (direction: -1=上, 1=下)"""
        # 現在のインデックスを探す
        idx = -1
        for i, item in enumerate(self.track_entries):
            if item["row"] == row_widget:
                idx = i
                break
        
        if idx == -1: return

        new_idx = idx + direction
        if 0 <= new_idx < len(self.track_entries):
            # リスト内で入れ替え
            self.track_entries[idx], self.track_entries[new_idx] = self.track_entries[new_idx], self.track_entries[idx]
            self.refresh_track_list()

    def delete_track(self, row_widget):
        """トラックを削除"""
        # インデックスを探す
        idx = -1
        for i, item in enumerate(self.track_entries):
            if item["row"] == row_widget:
                idx = i
                break
        
        if idx != -1:
            # ウィジェットを破棄
            self.track_entries[idx]["row"].destroy()
            # リストから削除
            self.track_entries.pop(idx)
            self.refresh_track_list()

    def refresh_track_list(self):
        """リストの並び順と番号をUIに反映"""
        for i, item in enumerate(self.track_entries):
            # 番号更新
            item["label"].config(text=f"{i+1}.")
            # 再配置 (pack順序をリスト順にするため、一度forgetしてからpackし直すのが確実だが、
            # ちらつき防止のため、順番が違っている場合のみ再packする方法もある。
            # ここではシンプルに一度forgetして再描画する)
            item["row"].pack_forget()
            item["row"].pack(fill="x", pady=2)

    def clear_tracks(self):
        for widget in self.tracks_frame.winfo_children():
            widget.destroy()
        self.track_entries = []

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_var.set(folder_selected)

    def get_current_data(self):
        tracks = []
        for item in self.track_entries:
            val = item["entry"].get().strip()
            is_inst = item["var"].get()
            if val:
                tracks.append({"name": val, "is_inst": is_inst})
                
        return {
            "year": self.year_var.get().strip(),
            "month": self.month_var.get().strip(),
            "day": self.day_var.get().strip(),
            "order": self.order_entry.get().strip(),
            "type": self.type_entry.get().strip(),
            "title": self.title_entry.get().strip(),
            "tracks": tracks
        }

    # --- ファイル読み書き ---

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All Supported", "*.txt *.json"), ("Text Files", "*.txt"), ("JSON Files", "*.json")])
        if not file_path: return
            
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".json": self.load_from_json(file_path)
            else: self.load_from_txt(file_path)
            self.path_var.set(os.path.dirname(file_path))
            messagebox.showinfo("成功", "ファイルを読み込みました。")
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"失敗しました: {e}")

    def load_from_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.year_var.set(data.get('year', ''))
        self.month_var.set(data.get('month', ''))
        self.update_days_options()
        self.day_var.set(data.get('day', ''))
        self.order_entry.delete(0, tk.END)
        self.order_entry.insert(0, data.get('order', ''))
        self.type_entry.set(data.get('type', ''))
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, data.get('title', ''))
        self.clear_tracks()
        
        raw_tracks = data.get('tracks', [])
        for i, t in enumerate(raw_tracks):
            # 最後の要素以外はrefresh=Falseで高速化、最後だけTrue
            is_last = (i == len(raw_tracks) - 1)
            self.add_track(t['name'], t['is_inst'], refresh=is_last)
        if not raw_tracks: # 空の場合念のため
            self.add_track()

    def load_from_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines()]
        if len(lines) < 3: raise ValueError("形式が不正です")

        date_match = re.match(r'(\d{4})\.(\d{2})\.(\d{2})', lines[0])
        if not date_match: raise ValueError("日付形式エラー")
        y, m, d = date_match.groups()
        
        type_line = lines[1]
        type_match = re.match(r'^(\d+)(?:st|nd|rd|th)\s+(.*)$', type_line)
        if type_match:
            order_num, disc_type = type_match.groups()
        else:
            parts = type_line.split(' ', 1)
            order_num = re.sub(r'\D', '', parts[0])
            disc_type = parts[1] if len(parts) > 1 else ""

        title_str = lines[2]
        
        tracks_data = []
        for line in lines[3:]:
            if not line or line.startswith("<div"): break
            track_match = re.match(r'^\d+\.(.*)$', line)
            if track_match:
                raw_name = track_match.group(1)
                is_inst = False
                if raw_name.endswith("(Inst)"):
                    raw_name = raw_name[:-6]
                    is_inst = True
                tracks_data.append((raw_name, is_inst))

        self.year_var.set(y)
        self.month_var.set(m)
        self.update_days_options()
        self.day_var.set(d)
        self.order_entry.delete(0, tk.END)
        self.order_entry.insert(0, order_num)
        self.type_entry.set(disc_type)
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title_str)
        self.clear_tracks()
        
        for i, (name, inst) in enumerate(tracks_data):
            is_last = (i == len(tracks_data) - 1)
            self.add_track(name, inst, refresh=is_last)
        if not tracks_data:
            self.add_track()

    def save_project_json(self):
        data = self.get_current_data()
        if not self._validate(data): return
        
        safe_title = sanitize_filename(data['title']) or "project"
        path = os.path.join(self.path_var.get().strip(), f"{safe_title}.json")
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", f"保存しました: {path}")
        except Exception as e:
            messagebox.showerror("エラー", f"保存失敗: {e}")

    def save_text_file(self):
        data = self.get_current_data()
        if not self._validate(data, check_tracks=True): return

        try:
            order_num = int(data['order'])
        except ValueError:
            messagebox.showerror("エラー", "何作目は数字で入力してください")
            return

        date_str = f"{data['year']}.{data['month']}.{data['day']}"
        ordinal_prefix = get_ordinal(order_num)
        
        formatted_tracks = []
        for i, t in enumerate(data['tracks'], 1):
            name = t['name']
            if t['is_inst']: name += "(Inst)"
            formatted_tracks.append(f"{i}.{name}")

        text_output = "\n".join([
            f"{date_str}",
            f"{ordinal_prefix} {data['type']}",
            f"{data['title']}"
        ] + formatted_tracks)

        header_title = f"{ordinal_prefix} {data['type']}<br>{data['title']}"
        tracks_html = "<br>".join(formatted_tracks)
        html_output = f"""<div class="details-text">
    <h3>{header_title}</h3>
    <p>{date_str}</p>
    <p>{tracks_html}</p>
</div>"""

        final_content = text_output + "\n\n" + html_output
        
        safe_title = sanitize_filename(data['title']) or "output"
        path = os.path.join(self.path_var.get().strip(), f"{safe_title}.txt")

        try:
            if os.path.exists(path):
                if not messagebox.askyesno("確認", "同名ファイルが存在します。上書きしますか？"): return
            with open(path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            messagebox.showinfo("成功", f"書き出しました: {path}")
        except Exception as e:
            messagebox.showerror("エラー", f"書き出し失敗: {e}")

    def _validate(self, data, check_tracks=False):
        if not all([data['year'], data['month'], data['day'], data['order'], data['type'], data['title']]):
            messagebox.showwarning("入力エラー", "すべての基本情報を入力してください")
            return False
        if check_tracks and not data['tracks']:
            messagebox.showwarning("入力エラー", "曲目を入力してください")
            return False
        if not os.path.isdir(self.path_var.get().strip()):
            messagebox.showerror("エラー", "保存先フォルダが存在しません")
            return False
        return True

if __name__ == "__main__":
    root = tk.Tk()
    app = DiscographyApp(root)
    root.mainloop()