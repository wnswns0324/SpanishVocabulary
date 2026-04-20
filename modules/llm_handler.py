import google.generativeai as genai
import json
import typing_extensions as typing

from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

class LLMHandler:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def process_words(self, raw_text):
        """
        raw_text: "papa, 감자\nbeber, 마시다"
        return: List[Dict] (가공된 데이터)
        """

        prompt = f"""
        You are a Spanish linguistics expert. 
        Input format: "Word(no accent), Rough Meaning and extra information if needed" per line.
        
        Your Task:
        1. Restore accents based on the meaning (Disambiguation).
           - Ex: "papa, dad" -> "Papá" (Masculine)
           - Ex: "papa, potato" -> "Papa" (Feminine)
           - the Word part should be in lowercase alphabets.
        2. Identify Part of Speech (POS), Gender (m/f/nm), and Conjugation info.
            - You must determine the POS in KOREAN, such as 형용사, 부사, 동사, 명사 etc.
        3. If it is a Verb:
            - The Word part should be in -r or -rse form, not the form user provided.
            - Provide conjugation for BOTH "Present Indicative" AND "Preterite Indefinite" (Simple Past).
            - do not omit json data even if the word isn't verb, leave the part like "yo":"-".
            - Check if it is reflexive.
            - if the word is reflexive, you may leave out the pronouns such as me, te, se, etc.
        3. Output MUST be a raw JSON list of objects. Do not use Markdown blocks.
        
        JSON Structure per word:
        {{
            "word": "Restored Spanish Word",
            "meaning": "Refined English Meaning(Ex: comer->to eat, papá->dad)",
            "pos": "명사/동사/형용사...",
            "is_reflexive": true / false,
            "gender": "남성(M)/여성(F)/-(N), use only single alphabet such as M/F/N",
            "plural": "if the word is noun, fill this space with plural of the word(Ex:lapiz->lapices)",
            "conjugation": {{
                "present": {{
                    "yo": "yo form or -",
                    "tu": "tu form or -",
                    "el": "el form or -",
                    "nosotros": "nosotros form or -",
                    "ellos": "ellos form or -"
                }},
                "past": {{
                    "yo": "yo form or -",
                    "tu": "tu form or -",
                    "el": "el form or -",
                    "nosotros": "nosotros form or -",
                    "ellos": "ellos form or -"
                }}
            }}
        }}

        Input Data:
        {raw_text}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )

            return json.loads(response.text)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return []
