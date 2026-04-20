import requests

def create_table_block(conjugation_data, is_reflexive=False):
    def make_row_from_list(cell_texts):
        cells = []
        for text in cell_texts:
            cells.append([{"type": "text", "text": {"content": str(text)}}])
            
        return {
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": cells}
        }

    present = conjugation_data.get('present', {})
    past = conjugation_data.get('past', {})

    keys = ["yo", "tu", "el", "nosotros", "ellos"]

    pronoun_map = {
        "yo": "me", 
        "tu": "te", 
        "el": "se", 
        "nosotros": "nos", 
        "ellos": "se"
    }

    def format_verb(key, verb):
        if verb == "-" or not verb:
            return "-"

        if is_reflexive:
            return f"{pronoun_map[key]} {verb}"
        else:
            return verb


    header_vals = ["시제", "Yo", "Tú", "Él/Ella", "Nosotros", "Ellos"]
    
    present_vals = ["현재 (Pres)"]
    for k in keys:
        raw_verb = present.get(k, "-")
        present_vals.append(format_verb(k, raw_verb))
        
    past_vals = ["과거 (Past)"]
    for k in keys:
        raw_verb = past.get(k, "-")
        past_vals.append(format_verb(k, raw_verb))

    table_block = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 6,
            "has_column_header": True,
            "has_row_header": True,
            "children": [
                make_row_from_list(header_vals),
                make_row_from_list(present_vals),
                make_row_from_list(past_vals)
            ]
        }
    }
    
    return table_block

class NotionClient:
    def __init__(self, token, db_id):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.db_id = db_id

    def check_exists(self, word):
        """
        해당 단어가 이미 DB에 있는지 확인하는 메서드
        Returns: True(중복됨) / False(새로운 단어)
        """
        query_url = f"https://api.notion.com/v1/databases/{self.db_id}/query"
        
        payload = {
            "filter": {
                "property": "단어",
                "title": {
                    "equals": word
                }
            }
        }
        
        response = requests.post(query_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            # 결과 리스트가 비어있지 않으면(len > 0) 이미 존재하는 것
            return len(results) > 0
        else:
            # 에러 발생 시 안전을 위해 False(없음) 처리하거나 로그 출력
            print(f"⚠️ 중복 검사 에러: {response.text}")
            return False

    def upload_word(self, data, unit_tag):
        """
        data: LLM에서 받은 Dict 하나 (word, meaning, pos...)
        """

        if self.check_exists(data['word']):
            print(f"⏭️ 중복된 단어 Skip: {data['word']}")
            return False

        url = "https://api.notion.com/v1/pages"
        
        properties = {
            "단어": {"title": [{"text": {"content": data['word']}}]},
            "뜻": {"rich_text": [{"text": {"content": data['meaning']}}]},
            "품사": {"select": {"name": data['pos']}},
            "유닛": {"multi_select": [{"name": unit_tag}]}
        }

        if data.get('gender') and data['gender'] != 'N':
            if data['gender'] == "M":
                properties["성별"] = {"select": {"name": "남성형"}}
            else:
                properties["성별"] = {"select": {"name": "여성형"}}
        if data['pos'] == "명사":
            properties["복수형"] = {"rich_text": [{"text": {"content": data['plural']}}]}
        
        children = []
        if data['pos'] == "동사":
            children.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"text": {"content": "동사 변형표"}}]
                }
            })

            is_refl = data.get('is_reflexive', False)
            table_block = create_table_block(data['conjugation'], is_reflexive=is_refl)
            children.append(table_block)
            pass

        payload = {
            "parent": {"database_id": self.db_id},
            "properties": properties,
            "children": children
        }

        response = requests.post(url, headers=self.headers, json=payload)
        return response.status_code == 200