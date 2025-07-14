"""
Question Generator Module
Generates challenge questions from document content
"""

import os
import openai
from typing import List, Dict, Tuple
import json
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuestionGenerator:
    """Generates logic-based and comprehension questions from documents"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.3  # Slightly higher for more diverse questions
    
    def generate_challenge_questions(self, document_text: str, num_questions: int = 3) -> List[Dict]:
        """
        Generate challenge questions from document content
        
        Args:
            document_text: Full document text
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries with question, answer, and difficulty
        """
        try:
            # Truncate document if too long
            from backend.ai_assistant import AIAssistant
            ai_assistant = AIAssistant()
            truncated_text = ai_assistant.truncate_text(document_text, 2500)
            
            prompt = f"""
            Based on the following document, generate exactly {num_questions} challenging questions that test:
            1. Reading comprehension
            2. Critical thinking
            3. Analysis and inference
            4. Understanding of key concepts
            
            Document:
            {truncated_text}
            
            For each question, provide:
            - The question text
            - The expected answer or key points
            - Difficulty level (Easy/Medium/Hard)
            
            Generate questions that require understanding the document content, not just memorization.
            Avoid simple factual questions. Focus on analysis, comparison, inference, and application.
            
            Format your response as a JSON array with this structure:
            [
                {{
                    "question": "Your question here",
                    "expected_answer": "Key points for the answer",
                    "difficulty": "Easy/Medium/Hard",
                    "type": "comprehension/analysis/inference"
                }}
            ]
            
            Questions:
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=self.temperature
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it's wrapped in text
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                json_text = response_text[start:end]
                
                questions = json.loads(json_text)
                
                # Validate and clean questions
                valid_questions = []
                for q in questions:
                    if all(key in q for key in ['question', 'expected_answer', 'difficulty']):
                        valid_questions.append({
                            'question': q['question'].strip(),
                            'expected_answer': q['expected_answer'].strip(),
                            'difficulty': q.get('difficulty', 'Medium'),
                            'type': q.get('type', 'comprehension')
                        })
                
                return valid_questions[:num_questions]
                
            except json.JSONDecodeError:
                # Fallback: parse manually
                return self._parse_questions_manually(response_text, num_questions)
                
        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
            return self._generate_fallback_questions(document_text, num_questions)
    
    def _parse_questions_manually(self, response_text: str, num_questions: int) -> List[Dict]:
        """Manually parse questions if JSON parsing fails"""
        questions = []
        lines = response_text.split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', 'Question:', 'Q:')):
                if current_question:
                    questions.append(current_question)
                    current_question = {}
                current_question['question'] = line
                current_question['expected_answer'] = "Based on document content"
                current_question['difficulty'] = "Medium"
                current_question['type'] = "comprehension"
        
        if current_question:
            questions.append(current_question)
        
        return questions[:num_questions]
    
    def _generate_fallback_questions(self, document_text: str, num_questions: int) -> List[Dict]:
        """Generate simple fallback questions if main generation fails"""
        fallback_questions = [
            {
                'question': "What is the main topic or theme discussed in this document?",
                'expected_answer': "The main topic should be identified from the document content",
                'difficulty': "Easy",
                'type': "comprehension"
            },
            {
                'question': "What are the key findings or conclusions presented in the document?",
                'expected_answer': "Key findings should be summarized from the document",
                'difficulty': "Medium",
                'type': "analysis"
            },
            {
                'question': "Based on the information provided, what implications or applications can be drawn?",
                'expected_answer': "Implications should be inferred from the document content",
                'difficulty': "Hard",
                'type': "inference"
            }
        ]
        
        return fallback_questions[:num_questions]
    
    def generate_specific_question_types(self, document_text: str, question_type: str) -> Dict:
        """
        Generate a specific type of question
        
        Args:
            document_text: Full document text
            question_type: Type of question (comprehension, analysis, inference, application)
            
        Returns:
            Single question dictionary
        """
        try:
            from backend.ai_assistant import AIAssistant
            ai_assistant = AIAssistant()
            truncated_text = ai_assistant.truncate_text(document_text, 2000)
            
            question_prompts = {
                'comprehension': "Generate a question that tests understanding of the main concepts in the document.",
                'analysis': "Generate a question that requires analyzing relationships or patterns in the document.",
                'inference': "Generate a question that requires making logical inferences from the document content.",
                'application': "Generate a question that asks how the information could be applied or used."
            }
            
            prompt = f"""
            Based on the following document, {question_prompts.get(question_type, question_prompts['comprehension'])}
            
            Document:
            {truncated_text}
            
            Provide:
            1. A challenging question
            2. Key points for the expected answer
            3. Difficulty level
            
            Question:
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=self.temperature
            )
            
            response_text = response.choices[0].message.content.strip()
            
            return {
                'question': response_text,
                'expected_answer': f"Answer should be based on {question_type} of the document content",
                'difficulty': "Medium",
                'type': question_type
            }
            
        except Exception as e:
            return {
                'question': f"What insights can you gain from this document regarding {question_type}?",
                'expected_answer': "Answer should be based on document content",
                'difficulty': "Medium",
                'type': question_type
            }
    
    def validate_questions(self, questions: List[Dict], document_text: str) -> List[Dict]:
        """
        Validate generated questions against document content
        
        Args:
            questions: List of generated questions
            document_text: Original document text
            
        Returns:
            List of validated questions
        """
        validated_questions = []
        
        for question in questions:
            # Basic validation
            if (question.get('question') and 
                len(question['question'].strip()) > 10 and
                question.get('expected_answer') and
                len(question['expected_answer'].strip()) > 5):
                
                validated_questions.append(question)
        
        return validated_questions