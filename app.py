import streamlit as st
import os
from document_processor import DocumentProcessor
from gemini_classifier import GeminiClassifier
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Financial Document Classifier",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("📄 Financial Document Classifier")
    st.markdown("Upload your financial documents to classify them using AI-powered analysis. This app can now analyze images directly!")
    
    # Initialize processors
    doc_processor = DocumentProcessor()
    classifier = GeminiClassifier()
    
    # Check if Gemini API key is available
    if not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
        st.stop()
    
    # File upload section
    st.subheader("📁 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'png', 'jpg', 'jpeg', 'txt', 'docx'],
        help="Supported formats: PDF, PNG, JPG, JPEG, TXT, DOCX"
    )
    
    if uploaded_file is not None:
        # Display file information
        st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        # Create columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Document Preview")
            
            # Show file preview based on type
            if uploaded_file.type.startswith('image/'):
                st.image(uploaded_file, caption="Document Image", use_column_width=True)
            elif uploaded_file.type == 'application/pdf':
                st.info("📄 PDF file uploaded - text will be extracted for analysis")
            elif uploaded_file.type == 'text/plain':
                st.info("📝 Text file uploaded")
            elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                st.info("📄 Word document uploaded - text will be extracted for analysis")
        
        with col2:
            st.subheader("🔍 Classification Results")
            
            if st.button("🚀 Classify Document", type="primary"):
                try:
                    # Reset file pointer before any processing
                    uploaded_file.seek(0)
                    
                    with st.spinner("Processing document..."):
                        # Process the document (extracts text or gets image object)
                        processed_content = doc_processor.extract_text(uploaded_file)
                        
                        if processed_content is None:
                            st.error("❌ Could not process the document. It might be corrupted or in an unsupported format.")
                            return

                    # For text documents, check if we have enough content
                    if isinstance(processed_content, str) and len(processed_content.strip()) < 10:
                        st.error("❌ Could not extract sufficient text from the document. Please ensure the document contains readable text.")
                        return
                    
                    with st.spinner("Analyzing document with AI..."):
                        # Classify the document (works for both text and images)
                        classification_result = classifier.classify_document(processed_content)
                        
                        if classification_result:
                            # Display results
                            st.success(f"✅ Classification Complete!")
                            
                            st.metric(
                                "📊 Document Type", 
                                classification_result['category']
                            )
                            
                            # Show confidence bar
                            confidence_percentage = classification_result['confidence']
                            st.progress(confidence_percentage, f"Confidence Level: {confidence_percentage:.1%}")
                            
                            # Classification explanation
                            if 'explanation' in classification_result:
                                st.subheader("💡 Analysis Details")
                                st.write(classification_result['explanation'])
                            
                            # For non-image files, show extracted text preview
                            if not isinstance(processed_content, Image.Image):
                                if st.checkbox("👁️ Show extracted text preview"):
                                    st.subheader("📝 Extracted Text Preview")
                                    text_preview = processed_content[:500]
                                    if len(processed_content) > 500:
                                        text_preview += "..."
                                    st.text_area("Document Content", text_preview, height=200, disabled=True)
                        else:
                            st.error("❌ Classification failed. Please try again.")
                            
                except Exception as e:
                    st.error(f"❌ Error processing document: {str(e)}")
    
    # Information section
    st.markdown("---")
    st.subheader("ℹ️ Classification Categories")
    
    categories = [
        "📧 Invoice - Bills sent to customers for goods/services",
        "🧾 Receipt - Proof of payment for goods/services", 
        "📄 Bill - Request for payment from suppliers",
        "💳 Check - Written order to pay money from bank account",
        "🏦 Bank Statement - Record of bank account transactions",
        "📋 Purchase Order - Authorization to buy goods/services",
        "🚚 Delivery Challan - Document accompanying goods delivery",
        "📁 Others - Documents that don't fit above categories"
    ]
    
    for category in categories:
        st.write(f"• {category}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Powered by Google Gemini AI for accurate document classification*")

if __name__ == "__main__":
    main()
