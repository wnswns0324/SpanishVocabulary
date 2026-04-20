import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

class SpanishAppGUI:
    def __init__(self, root, llm_handler, notion_client):
        self.root = root
        self.llm = llm_handler      # LLM 모듈 의존성 주입
        self.notion = notion_client # Notion 모듈 의존성 주입
        self.processed_data = []    # 가공된 데이터 저장소

        self.root.title("🇪🇸 Español Vocabulary Manager")
        self.root.geometry("1100x750")

        self._setup_ui()

    def _setup_ui(self):
        # 1. [상단] 설정 영역 (유닛 입력)
        config_frame = ttk.LabelFrame(self.root, text="업로드 설정", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="Unit 태그:").pack(side="left", padx=5)
        self.unit_entry = ttk.Entry(config_frame, width=20)
        self.unit_entry.insert(0, "Basics") # 기본값
        self.unit_entry.pack(side="left", padx=5)

        # 2. [중단] 메인 작업 영역 (좌:입력 / 우:결과표)
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        # 2-1. 좌측: 원시 텍스트 입력
        left_frame = ttk.LabelFrame(paned, text="Step 1. 단어 입력 (단어, 뜻)", padding=5)
        paned.add(left_frame, weight=1)
        
        self.input_text = scrolledtext.ScrolledText(left_frame, width=30, height=20)
        self.input_text.pack(fill="both", expand=True)
        # 힌트 텍스트
        self.input_text.insert("1.0", "")

        # 2-2. 우측: 가공 결과 확인 (Treeview)
        right_frame = ttk.LabelFrame(paned, text="Step 2. 데이터 검수 (LLM 가공 결과)", padding=5)
        paned.add(right_frame, weight=3)

        # 표 컬럼 정의 (JSON 스키마 반영)
        cols = ("word", "meaning", "pos", "gender", "plural", "reflexive", "conj_preview")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings")
        
        # 헤더 설정
        self.tree.heading("word", text="단어")
        self.tree.heading("meaning", text="뜻")
        self.tree.heading("pos", text="품사")
        self.tree.heading("gender", text="성별")
        self.tree.heading("plural", text="명사 복수형")
        self.tree.heading("reflexive", text="재귀")
        self.tree.heading("conj_preview", text="동사 변형 (미리보기)")

        # 컬럼 너비 최적화
        self.tree.column("word", width=100)
        self.tree.column("meaning", width=150)
        self.tree.column("pos", width=60, anchor="center")
        self.tree.column("gender", width=50, anchor="center")
        self.tree.column("plural", width=100, anchor="center")
        self.tree.column("reflexive", width=50, anchor="center")
        self.tree.column("conj_preview", width=250)

        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # 3. [하단] 액션 버튼 & 로그
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x")

        self.btn_process = ttk.Button(action_frame, text="⚡️ 가공 시작 (LLM)", command=self.on_process_click)
        self.btn_process.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_upload = ttk.Button(action_frame, text="🚀 노션 업로드 (DB)", command=self.on_upload_click, state="disabled")
        self.btn_upload.pack(side="left", padx=5, expand=True, fill="x")

        # 로그창
        self.log_text = scrolledtext.ScrolledText(self.root, height=5, state="disabled", bg="#f5f5f5", font=("Consolas", 10))
        self.log_text.pack(fill="x", padx=10, pady=(0, 10))

    # --- 유틸리티 메서드 ---
    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"> {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def toggle_buttons(self, state):
        """버튼 활성화/비활성화 상태 토글"""
        self.btn_process.config(state=state)
        # 업로드 버튼은 데이터가 있을 때만 활성화되어야 함
        if state == "normal" and self.processed_data:
            self.btn_upload.config(state="normal")
        else:
            self.btn_upload.config(state="disabled")

    # --- 이벤트 핸들러 ---
    def on_process_click(self):
        raw_text = self.input_text.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showwarning("경고", "입력된 단어가 없습니다.")
            return

        self.toggle_buttons("disabled")
        self.log("LLM 가공 요청 중... 잠시만 기다려주세요.")
        
        # 쓰레드 시작
        threading.Thread(target=self._run_llm_logic, args=(raw_text,), daemon=True).start()

    def _run_llm_logic(self, raw_text):
        try:
            # LLM 모듈 호출
            results = self.llm.process_words(raw_text)
            self.processed_data = results
            
            # 메인 쓰레드에서 UI 업데이트
            self.root.after(0, self._update_treeview_success)
        except Exception as e:
            print(e)

    def _update_treeview_success(self):
        # 표 비우기
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 데이터 채우기
        for item in self.processed_data:
            # 1. 재귀동사 표시 (T/F -> O/X)
            is_refl = "O" if item.get('is_reflexive') else "-"
            
            # 2. 동사 변형 미리보기 문자열 생성
            conj_str = "-"
            if item.get('conjugation') and isinstance(item['conjugation'], dict):
                # 안전하게 데이터 가져오기 (present 키가 없을 수도 있음)
                pres = item['conjugation'].get('present', {})
                past = item['conjugation'].get('past', {})
                
                # 대표값(1인칭)만 보여주거나 간략화
                p_yo = pres.get('yo', '-')
                pt_yo = past.get('yo', '-')
                conj_str = f"[Pres] {p_yo}.. / [Past] {pt_yo}.."

            self.tree.insert("", "end", values=(
                item.get('word'),
                item.get('meaning'),
                item.get('pos'),
                item.get('gender', 'N'),
                item.get('plural'),
                is_refl,
                conj_str
            ))
        
        self.log(f"✅ 가공 완료: 총 {len(self.processed_data)}개 단어 식별됨.")
        self.toggle_buttons("normal")

    def on_upload_click(self):
        if not self.processed_data:
            return
        
        self.toggle_buttons("disabled")
        unit_val = self.unit_entry.get()
        self.log(f"노션 업로드 시작 (Unit: {unit_val})...")

        threading.Thread(target=self._run_upload_logic, args=(unit_val,), daemon=True).start()

    # modules/gui.py 내부

    def _run_upload_logic(self, unit):
        success_count = 0
        skip_count = 0    # 스킵 카운트 추가
        total = len(self.processed_data)

        for idx, item in enumerate(self.processed_data):
            try:
                # upload_word가 이제 True(성공), False(중복스킵)를 반환함
                result = self.notion.upload_word(item, unit)
                
                if result:
                    success_count += 1
                    # 성공 로그
                    self.root.after(0, lambda i=item['word']: self.log(f"  ✅ 업로드: {i}"))
                else:
                    skip_count += 1
                    # 스킵 로그
                    self.root.after(0, lambda i=item['word']: self.log(f"  ⏭️ 중복 생략: {i}"))
                    
            except Exception as e:
                self.root.after(0, lambda i=item['word'], err=e: self.log(f"  ❌ 에러({i}): {err}"))
            
        self.root.after(0, lambda: self._upload_finished(success_count, skip_count, total))

    def _upload_finished(self, success, skip, total):
        # 메시지 박스 내용 수정
        msg = f"작업 완료!\n\n- 성공: {success}개\n- 중복(생략): {skip}개\n- 전체: {total}개"
        self.log(f"🏁 {msg}")
        messagebox.showinfo("완료", msg)
        self.processed_data = [] # 데이터 초기화
        for item in self.tree.get_children(): # 표 비우기
            self.tree.delete(item)
        self.toggle_buttons("normal") # 초기 상태로 복귀
        # ... (초기화 로직 등) ...
        