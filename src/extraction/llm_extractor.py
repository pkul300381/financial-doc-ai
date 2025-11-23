"""
LLM-based extraction engine using LangChain and OpenAI.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

from src.models.schemas import (
    DocumentType, InvoiceExtraction, BankStatementExtraction,
    MonetaryAmount, Currency, ExtractedEntity
)
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMExtractor:
    """LLM-based structured data extraction."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize LLM extractor."""
        self.model_name = model_name or settings.openai_model
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.0,
            openai_api_key=settings.openai_api_key
        )
    
    def extract_invoice(self, text: str, tables: List[Dict] = None) -> InvoiceExtraction:
        """Extract structured invoice data from text."""
        prompt_template = """You are an expert at extracting structured data from invoices.
        
        Extract the following information from the invoice text below:
        - Invoice number
        - Invoice date (ISO 8601 format)
        - Due date (ISO 8601 format)
        - Vendor name and address
        - Vendor tax ID
        - Customer name and address
        - Line items (description, quantity, unit price, total)
        - Subtotal, tax amount, and total amount with currency
        - Payment terms
        
        Invoice text:
        {text}
        
        {tables_section}
        
        Return the data in this JSON format:
        {{
            "invoice_number": "string or null",
            "invoice_date": "YYYY-MM-DD or null",
            "due_date": "YYYY-MM-DD or null",
            "vendor_name": "string or null",
            "vendor_address": "string or null",
            "vendor_tax_id": "string or null",
            "customer_name": "string or null",
            "customer_address": "string or null",
            "line_items": [
                {{"description": "string", "quantity": number, "unit_price": number, "total": number}}
            ],
            "subtotal": {{"amount": number, "currency": "USD", "original_text": "string"}},
            "tax_amount": {{"amount": number, "currency": "USD", "original_text": "string"}},
            "total_amount": {{"amount": number, "currency": "USD", "original_text": "string"}},
            "payment_terms": "string or null"
        }}
        
        If any field is not found, set it to null. Ensure all monetary amounts are normalized to numeric values.
        """
        
        tables_section = ""
        if tables:
            tables_section = f"Tables found in document:\n{json.dumps(tables, indent=2)}"
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"text": text[:4000], "tables_section": tables_section})
            result_text = response.content
            
            # Parse JSON response
            result_json = json.loads(result_text)
            
            # Convert to Pydantic model
            extraction = InvoiceExtraction(**result_json)
            return extraction
        except Exception as e:
            logger.error(f"Invoice extraction failed: {e}")
            return InvoiceExtraction()
    
    def extract_bank_statement(self, text: str, tables: List[Dict] = None) -> BankStatementExtraction:
        """Extract structured bank statement data from text."""
        prompt_template = """You are an expert at extracting structured data from bank statements.
        
        Extract the following information from the bank statement text below:
        - Account number
        - Account holder name
        - Statement period (start and end dates in ISO 8601 format)
        - Opening balance with currency
        - Closing balance with currency
        - Individual transactions (date, description, amount, balance)
        - Bank name
        
        Bank statement text:
        {text}
        
        {tables_section}
        
        Return the data in this JSON format:
        {{
            "account_number": "string or null",
            "account_holder": "string or null",
            "statement_period_start": "YYYY-MM-DD or null",
            "statement_period_end": "YYYY-MM-DD or null",
            "opening_balance": {{"amount": number, "currency": "USD", "original_text": "string"}},
            "closing_balance": {{"amount": number, "currency": "USD", "original_text": "string"}},
            "transactions": [
                {{"date": "YYYY-MM-DD", "description": "string", "amount": number, "balance": number}}
            ],
            "bank_name": "string or null"
        }}
        
        If any field is not found, set it to null. Ensure all monetary amounts are normalized to numeric values.
        """
        
        tables_section = ""
        if tables:
            tables_section = f"Tables found in document:\n{json.dumps(tables, indent=2)}"
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"text": text[:4000], "tables_section": tables_section})
            result_text = response.content
            
            # Parse JSON response
            result_json = json.loads(result_text)
            
            # Convert to Pydantic model
            extraction = BankStatementExtraction(**result_json)
            return extraction
        except Exception as e:
            logger.error(f"Bank statement extraction failed: {e}")
            return BankStatementExtraction()
    
    def extract_generic_entities(self, text: str, doc_type: DocumentType) -> List[ExtractedEntity]:
        """Extract generic entities based on document type."""
        prompt_template = """Extract key financial entities from this {doc_type} document.
        
        Look for:
        - Dates (transaction dates, due dates, period dates)
        - Monetary amounts
        - Names (people, companies, vendors)
        - Identifiers (invoice numbers, account numbers, tax IDs)
        - Addresses
        
        Text:
        {text}
        
        Return a JSON array of entities:
        [
            {{"field_name": "string", "value": "string", "confidence": 0.0-1.0, "source_text": "string"}}
        ]
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"text": text[:3000], "doc_type": doc_type.value})
            result_text = response.content
            
            # Parse JSON response
            entities_data = json.loads(result_text)
            
            entities = [ExtractedEntity(**ent) for ent in entities_data]
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def classify_document(self, text: str) -> DocumentType:
        """Classify document type using LLM."""
        prompt_template = """Classify the following financial document into one of these categories:
        - invoice
        - bank_statement
        - receipt
        - contract
        - tax_form
        - financial_report
        - other
        
        Document text (first 1000 chars):
        {text}
        
        Return only the category name, nothing else.
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"text": text[:1000]})
            doc_type_str = response.content.strip().lower()
            
            # Map to enum
            type_mapping = {
                "invoice": DocumentType.INVOICE,
                "bank_statement": DocumentType.BANK_STATEMENT,
                "receipt": DocumentType.RECEIPT,
                "contract": DocumentType.CONTRACT,
                "tax_form": DocumentType.TAX_FORM,
                "financial_report": DocumentType.FINANCIAL_REPORT,
            }
            
            return type_mapping.get(doc_type_str, DocumentType.OTHER)
        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return DocumentType.OTHER
    
    def extract_structured_data(
        self, 
        text: str, 
        doc_type: DocumentType,
        tables: Optional[List[Dict]] = None
    ) -> Any:
        """Extract structured data based on document type."""
        if doc_type == DocumentType.INVOICE:
            return self.extract_invoice(text, tables)
        elif doc_type == DocumentType.BANK_STATEMENT:
            return self.extract_bank_statement(text, tables)
        else:
            # For other types, return generic entities
            return self.extract_generic_entities(text, doc_type)
