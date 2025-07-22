import os
import json
import logging
from typing import Dict, Optional, Union
import google.generativeai as genai
import google.api_core.exceptions
from pydantic import BaseModel
from PIL import Image


class ClassificationResult(BaseModel):
    """Pydantic model for classification result"""
    category: str
    confidence: float
    explanation: str

class GeminiClassifier:
    """
    Handles document classification using Gemini API
    """
    
    def __init__(self):
        # Configure the Gemini client using the environment variable
        # This should be set in your environment before running the app
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.categories = [
            "Invoice",
            "Receipt", 
            "Bill",
            "Check",
            "Bank Statement",
            "Purchase Order",
            "Delivery Challan",
            "Others"
        ]
    
    def classify_document(self, content: Union[str, Image.Image]) -> Optional[Dict]:
        """
        Classify document content (text or image) into one of the financial document categories.
        """
        if isinstance(content, str):
            return self._classify_text(content)
        elif isinstance(content, Image.Image):
            return self._classify_image(content)
        else:
            raise TypeError("Unsupported content type. Must be str or PIL Image.")

    def _classify_text(self, text: str) -> Optional[Dict]:
        """
        Classify document text into one of the financial document categories
        """
        try:
            system_prompt = self._create_classification_prompt()
            prompt = f"{system_prompt}\n\nDocument text to classify:\n\n{text}"
            
            response = self.model.generate_content(prompt)

            # Check for safety blocks from the API
            if response.prompt_feedback.block_reason:
                raise ValueError(f"Classification failed due to safety settings. Reason: {response.prompt_feedback.block_reason.name}")

            if hasattr(response, "text"):
                # Clean the response to remove markdown wrappers like ```json ... ```
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                result_data = json.loads(response_text)
                classification_result = ClassificationResult(**result_data)
                
                # Validate that category is in our expected list
                if classification_result.category not in self.categories:
                    classification_result.category = "Others"
                
                # Ensure confidence is between 0 and 1
                confidence = max(0.0, min(1.0, classification_result.confidence))
                
                return {
                    'category': classification_result.category,
                    'confidence': confidence,
                    'explanation': classification_result.explanation
                }
            else:
                # This case might happen if the response is empty for other reasons
                raise ValueError("Classification failed: The AI returned an empty response.")
                
        except json.JSONDecodeError as e:
            raw_response = getattr(response, 'text', 'N/A')
            logging.error(f"JSON decode error: {e}. AI response was: {raw_response}")
            raise ValueError(f"Classification failed: The AI returned improperly formatted data. Full AI response: {raw_response}")
        except google.api_core.exceptions.PermissionDenied as e:
            logging.error(f"Permission Denied error: {e}")
            raise ValueError("Classification failed: Permission denied. Please check if your GEMINI_API_KEY is correct and has the necessary permissions.")
        except Exception as e:
            logging.error(f"An unexpected classification error occurred: {e}")
            raise ValueError(f"An unexpected error occurred during classification: {e}")

    def _classify_image(self, image: Image.Image) -> Optional[Dict]:
        """
        Classify an image using multimodal analysis.
        """
        try:
            system_prompt = self._create_classification_prompt()
            
            # The model can take a list of parts, mixing text and images
            response = self.model.generate_content([system_prompt, image])

            # Check for safety blocks from the API
            if response.prompt_feedback.block_reason:
                raise ValueError(f"Classification failed due to safety settings. Reason: {response.prompt_feedback.block_reason.name}")

            if hasattr(response, "text"):
                # Clean the response to remove markdown wrappers like ```json ... ```
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                result_data = json.loads(response_text)
                classification_result = ClassificationResult(**result_data)
                
                # Validate that category is in our expected list
                if classification_result.category not in self.categories:
                    classification_result.category = "Others"
                
                # Ensure confidence is between 0 and 1
                confidence = max(0.0, min(1.0, classification_result.confidence))
                
                return {
                    'category': classification_result.category,
                    'confidence': confidence,
                    'explanation': classification_result.explanation
                }
            else:
                # This case might happen if the response is empty for other reasons
                raise ValueError("Classification failed: The AI returned an empty response.")
                
        except json.JSONDecodeError as e:
            raw_response = getattr(response, 'text', 'N/A')
            logging.error(f"JSON decode error: {e}. AI response was: {raw_response}")
            raise ValueError(f"Classification failed: The AI returned improperly formatted data. Full AI response: {raw_response}")
        except google.api_core.exceptions.PermissionDenied as e:
            logging.error(f"Permission Denied error: {e}")
            raise ValueError("Classification failed: Permission denied. Please check if your GEMINI_API_KEY is correct and has the necessary permissions.")
        except Exception as e:
            logging.error(f"An unexpected classification error occurred: {e}")
            raise ValueError(f"An unexpected error occurred during classification: {e}")

    def _create_classification_prompt(self) -> str:
        """
        Create a detailed prompt for document classification
        """
        prompt = f"""You are an expert financial document classifier. Your task is to analyze the provided document text and classify it into one of these categories:

**Categories and Definitions:**

1. **Invoice** - A bill sent to a customer requesting payment for goods or services provided. Usually contains seller details, buyer details, itemized list of goods/services, amounts, tax information, and payment terms.

2. **Receipt** - A document acknowledging that payment has been received for goods or services. Contains proof of purchase, amount paid, date of transaction, and method of payment.

3. **Bill** - A statement requesting payment for goods or services received. Similar to invoice but may be less formal, often from utilities, services, or suppliers.

4. **Check** - A written order directing a bank to pay money from the drawer's account. Contains bank details, account number, payee information, amount, date, and signature.

5. **Bank Statement** - A summary of financial transactions in a bank account over a specific period. Shows opening balance, deposits, withdrawals, fees, and closing balance.

6. **Purchase Order** - A document issued by a buyer to authorize a purchase transaction with a seller. Contains item descriptions, quantities, agreed prices, and delivery terms.

7. **Delivery Challan** - A document that accompanies goods during transport, showing details of goods being delivered. Often used in logistics and supply chain management.

8. **Others** - Any financial document that doesn't fit the above categories, such as contracts, agreements, financial reports, etc.

**Instructions:**
- Analyze the document content carefully
- Look for key indicators like document titles, formatting, specific terminology, and data patterns
- Consider the purpose and context of the document
- Provide your classification with a confidence score between 0.0 and 1.0
- Give a brief explanation of why you classified it this way
- Be conservative with confidence scores - only use high confidence (>0.9) when you're very certain

**Response Format:**
Respond with JSON in this exact format:
{{
    "category": "one of the 8 categories exactly as listed above",
    "confidence": "decimal between 0.0 and 1.0",
    "explanation": "brief explanation of classification reasoning"
}}
"""
        return prompt
