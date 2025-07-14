"""
Smart Assistant for Research Summarization
Main Streamlit Application
"""

import streamlit as st
import os
from backend.document_processor import DocumentProcessor
from backend.ai_assistant import AIAssistant
from backend.question_generator import QuestionGenerator

# Configure Streamlit page
st.set_page_config(
    page_title="Smart Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'document_text' not in st.session_state:
    st.session_state.document_text = ""
if 'document_name' not in st.session_state:
    st.session_state.document_name = ""
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'challenge_questions' not in st.session_state:
    st.session_state.challenge_questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'challenge_mode' not in st.session_state:
    st.session_state.challenge_mode = False
if 'question_answered' not in st.session_state:
    st.session_state.question_answered = False

# Initialize components

def get_components():
    return DocumentProcessor(), AIAssistant(), QuestionGenerator()

doc_processor, ai_assistant, question_generator = get_components()

def main():
    st.title("📚 Smart Research Assistant")
    st.markdown("Upload a document and interact with it using AI-powered analysis!")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set your OPENAI_API_KEY environment variable.")
        st.stop()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("📄 Document Upload")
        uploaded_file = st.file_uploader(
            "Choose a PDF or TXT file",
            type=['pdf', 'txt'],
            help="Upload a structured document (research paper, report, etc.)"
        )
        
        if uploaded_file is not None:
            if st.button("Process Document", type="primary"):
                process_document(uploaded_file)
        
        # Document info
        if st.session_state.document_name:
            st.success(f"📄 Document: {st.session_state.document_name}")
            st.info(f"📊 Text length: {len(st.session_state.document_text):,} characters")
            
            if st.button("Clear Document"):
                clear_document()
                st.rerun()
    
    # Main content area
    if st.session_state.document_text:
        # Display summary
        st.header("📋 Document Summary")
        if st.session_state.summary:
            st.markdown(f"**Summary:** {st.session_state.summary}")
        else:
            st.warning("Summary not available. Please reprocess the document.")
        
        st.divider()
        
        # Mode selection
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🤔 Ask Anything", type="secondary", use_container_width=True):
                st.session_state.challenge_mode = False
                st.rerun()
        
        with col2:
            if st.button("🎯 Challenge Me", type="secondary", use_container_width=True):
                st.session_state.challenge_mode = True
                generate_challenge_questions()
                st.rerun()
        
        st.divider()
        
        # Display appropriate mode
        if st.session_state.challenge_mode:
            display_challenge_mode()
        else:
            display_ask_anything_mode()
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to Smart Research Assistant! 🚀
        
        This AI-powered tool helps you:
        - **📄 Process Documents**: Upload PDF or TXT files
        - **📝 Get Summaries**: Receive concise summaries (≤150 words)
        - **❓ Ask Questions**: Get detailed answers with document-based justifications
        - **🎯 Take Challenges**: Test your understanding with AI-generated questions
        
        ### How to Start:
        1. Upload a document using the sidebar
        2. Click "Process Document" to analyze it
        3. Choose between "Ask Anything" or "Challenge Me" modes
        
        ### Features:
        - **Smart Q&A**: Context-aware responses with document references
        - **Challenge Questions**: Logic-based questions to test comprehension
        - **Memory**: Maintains conversation context for follow-up questions
        - **Justifications**: Every answer includes document-based reasoning
        """)

def process_document(uploaded_file):
    """Process uploaded document"""
    with st.spinner("Processing document..."):
        # Process document
        success, text_content, error_msg = doc_processor.process_document(uploaded_file)
        
        if success:
            st.session_state.document_text = text_content
            st.session_state.document_name = uploaded_file.name
            
            # Generate summary
            with st.spinner("Generating summary..."):
                summary = ai_assistant.generate_summary(text_content)
                st.session_state.summary = summary
            
            # Clear previous session data
            st.session_state.challenge_questions = []
            st.session_state.current_question_index = 0
            st.session_state.challenge_mode = False
            ai_assistant.clear_conversation_history()
            
            st.success("✅ Document processed successfully!")
            
        else:
            st.error(f"❌ Error processing document: {error_msg}")

def clear_document():
    """Clear current document and reset session"""
    st.session_state.document_text = ""
    st.session_state.document_name = ""
    st.session_state.summary = ""
    st.session_state.challenge_questions = []
    st.session_state.current_question_index = 0
    st.session_state.challenge_mode = False
    st.session_state.question_answered = False
    ai_assistant.clear_conversation_history()

def display_ask_anything_mode():
    """Display the Ask Anything interface"""
    st.header("🤔 Ask Anything Mode")
    st.markdown("Ask any question about your document. The AI will provide answers with document-based justifications.")
    
    # Question input
    question = st.text_input(
        "What would you like to know about this document?",
        placeholder="e.g., What are the main conclusions? How does this relate to...?"
    )
    
    if st.button("Get Answer", type="primary") and question:
        with st.spinner("Analyzing document and generating answer..."):
            answer, justification = ai_assistant.answer_question(
                question, 
                st.session_state.document_text,
                st.session_state.get('conversation_history', [])
            )
            
            # Display answer
            st.markdown("### 💡 Answer:")
            st.markdown(answer)
            
            st.markdown("### 📝 Justification:")
            st.markdown(justification)
            
            # Add to conversation history
            ai_assistant.add_to_conversation_history(question, answer)
    
    # Display conversation history
    if st.session_state.get('conversation_history'):
        st.markdown("---")
        st.markdown("### 📚 Conversation History")
        
        for i, entry in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(f"Q{len(st.session_state.conversation_history)-i}: {entry['question'][:50]}..."):
                st.markdown(f"**Question:** {entry['question']}")
                st.markdown(f"**Answer:** {entry['answer']}")

def generate_challenge_questions():
    """Generate challenge questions"""
    if not st.session_state.challenge_questions:
        with st.spinner("Generating challenge questions..."):
            questions = question_generator.generate_challenge_questions(
                st.session_state.document_text, 
                num_questions=3
            )
            st.session_state.challenge_questions = questions
            st.session_state.current_question_index = 0
            st.session_state.question_answered = False

def display_challenge_mode():
    """Display the Challenge Mode interface"""
    st.header("🎯 Challenge Me Mode")
    st.markdown("Test your understanding with AI-generated questions based on the document.")
    
    if not st.session_state.challenge_questions:
        st.info("Click 'Challenge Me' to generate questions based on your document.")
        return
    
    # Display current question
    current_idx = st.session_state.current_question_index
    total_questions = len(st.session_state.challenge_questions)
    
    if current_idx < total_questions:
        current_question = st.session_state.challenge_questions[current_idx]
        
        st.markdown(f"### Question {current_idx + 1} of {total_questions}")
        st.markdown(f"**Difficulty:** {current_question.get('difficulty', 'Medium')}")
        st.markdown(f"**Type:** {current_question.get('type', 'Comprehension')}")
        
        st.markdown("---")
        st.markdown(f"**{current_question['question']}**")
        
        # Answer input
        user_answer = st.text_area(
            "Your answer:",
            placeholder="Provide your answer based on the document...",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Submit Answer", type="primary") and user_answer:
                evaluate_answer(current_question, user_answer)
        
        with col2:
            if st.button("Skip Question") and current_idx < total_questions - 1:
                st.session_state.current_question_index += 1
                st.session_state.question_answered = False
                st.rerun()
        
        with col3:
            if st.button("New Questions"):
                st.session_state.challenge_questions = []
                generate_challenge_questions()
                st.rerun()
    
    else:
        st.success("🎉 You've completed all challenge questions!")
        if st.button("Generate New Questions"):
            st.session_state.challenge_questions = []
            generate_challenge_questions()
            st.rerun()

def evaluate_answer(question, user_answer):
    """Evaluate user's answer to challenge question"""
    with st.spinner("Evaluating your answer..."):
        evaluation, feedback, score = ai_assistant.evaluate_user_answer(
            question['question'],
            user_answer,
            question['expected_answer'],
            st.session_state.document_text
        )
        
        st.session_state.question_answered = True
        
        # Display evaluation
        st.markdown("---")
        st.markdown("### 📊 Evaluation Results")
        
        # Score display with color coding
        if score >= 8:
            st.success(f"🎉 **{evaluation}** - Score: {score}/10")
        elif score >= 6:
            st.warning(f"⚠️ **{evaluation}** - Score: {score}/10")
        else:
            st.error(f"❌ **{evaluation}** - Score: {score}/10")
        
        st.markdown("### 💭 Feedback:")
        st.markdown(feedback)
        
        # Expected answer
        st.markdown("### 📚 Expected Answer Points:")
        st.markdown(question['expected_answer'])
        
        # Navigation
        col1, col2 = st.columns(2)
        
        with col1:
            if (st.session_state.current_question_index < len(st.session_state.challenge_questions) - 1 and
                st.button("Next Question", type="primary")):
                st.session_state.current_question_index += 1
                st.session_state.question_answered = False
                st.rerun()
        
        with col2:
            if st.button("Back to Ask Anything"):
                st.session_state.challenge_mode = False
                st.rerun()

if __name__ == "__main__":
    main()