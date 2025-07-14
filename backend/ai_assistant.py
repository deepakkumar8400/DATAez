"""
AI Assistant Module
Handles question answering and document analysis using OpenAI
"""

import os
import openai
from typing import Dict, List, Optional, Tuple
import streamlit as st
from dotenv import load_dotenv
import tiktoken

# Load environment variables
load_dotenv()

class AIAssistant:
    """Main AI assistant for document analysis and question answering"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for more consistent responses
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Session state for conversation history
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def truncate_text(self, text: str, max_tokens: int = 3000) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        # Keep the first part of the document
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def generate_summary(self, document_text: str) -> str:
        """
        Generate a concise summary of the document (≤150 words)
        
        Args:
            document_text: Full text of the document
            
        Returns:
            Summary text
        """
        try:
            # Truncate document if too long
            truncated_text = self.truncate_text(document_text, 2500)
            
            prompt = f"""
            Please provide a concise summary of the following document in exactly 150 words or less. 
            Focus on the main topics, key findings, and important conclusions.
            
            Document:
            {truncated_text}
            
            Summary (≤150 words):
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=self.temperature
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def answer_question(self, question: str, document_text: str, context_history: List[Dict] = None) -> Tuple[str, str]:
        """
        Answer a question based on the document content
        
        Args:
            question: User's question
            document_text: Full document text
            context_history: Previous conversation context
            
        Returns:
            Tuple of (answer, justification)
        """
        try:
            # Truncate document if too long
            truncated_text = self.truncate_text(document_text, 2500)
            
            # Build context from history
            context = ""
            if context_history:
                context = "\n\nPrevious conversation:\n"
                for entry in context_history[-3:]:  # Keep last 3 exchanges
                    context += f"Q: {entry['question']}\nA: {entry['answer']}\n"
            
            prompt = f"""
            You are an AI assistant analyzing a document. Answer the user's question based ONLY on the information provided in the document.
            
            Rules:
            1. Base your answer strictly on the document content
            2. If information is not in the document, say "This information is not available in the document"
            3. Provide a clear justification referencing specific parts of the document
            4. Be concise but comprehensive
            5. Do not make assumptions or add external knowledge
            
            Document:
            {truncated_text}
            
            {context}
            
            Question: {question}
            
            Please provide your answer followed by a justification that references specific parts of the document.
            
            Answer:
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=self.temperature
            )
            
            full_response = response.choices[0].message.content.strip()
            
            # Try to separate answer and justification
            if "justification:" in full_response.lower():
                parts = full_response.split("Justification:", 1)
                if len(parts) == 2:
                    answer = parts[0].strip()
                    justification = parts[1].strip()
                else:
                    answer = full_response
                    justification = "Based on the document content provided."
            else:
                answer = full_response
                justification = "Response is grounded in the document content."
            
            return answer, justification
            
        except Exception as e:
            return f"Error answering question: {str(e)}", ""
    
    def evaluate_user_answer(self, question: str, user_answer: str, correct_info: str, document_text: str) -> Tuple[str, str, int]:
        """
        Evaluate user's answer to a challenge question
        
        Args:
            question: The challenge question
            user_answer: User's response
            correct_info: Expected answer information
            document_text: Full document text
            
        Returns:
            Tuple of (evaluation, feedback, score_out_of_10)
        """
        try:
            truncated_text = self.truncate_text(document_text, 2000)
            
            prompt = f"""
            You are evaluating a user's answer to a comprehension question about a document.
            
            Document excerpt:
            {truncated_text}
            
            Question: {question}
            
            Expected information: {correct_info}
            
            User's answer: {user_answer}
            
            Please evaluate the user's answer and provide:
            1. A brief evaluation (Correct/Partially Correct/Incorrect)
            2. Constructive feedback with reference to the document
            3. A score from 1-10
            
            Format your response as:
            Evaluation: [Correct/Partially Correct/Incorrect]
            Feedback: [Your feedback with document references]
            Score: [1-10]
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=self.temperature
            )
            
            full_response = response.choices[0].message.content.strip()
            
            # Parse response
            lines = full_response.split('\n')
            evaluation = "Partially Correct"
            feedback = full_response
            score = 5
            
            for line in lines:
                if line.startswith("Evaluation:"):
                    evaluation = line.replace("Evaluation:", "").strip()
                elif line.startswith("Feedback:"):
                    feedback = line.replace("Feedback:", "").strip()
                elif line.startswith("Score:"):
                    try:
                        score = int(line.replace("Score:", "").strip())
                    except:
                        score = 5
            
            return evaluation, feedback, score
            
        except Exception as e:
            return "Error", f"Error evaluating answer: {str(e)}", 0
    
    def add_to_conversation_history(self, question: str, answer: str):
        """Add Q&A pair to conversation history"""
        st.session_state.conversation_history.append({
            'question': question,
            'answer': answer
        })
        
        # Keep only last 10 exchanges
        if len(st.session_state.conversation_history) > 10:
            st.session_state.conversation_history.pop(0)
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        st.session_state.conversation_history = []