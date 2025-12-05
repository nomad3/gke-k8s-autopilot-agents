"""
PDF Data Extractor for Dental Practice Reports
Uses AI (GPT-4o with vision) to extract structured data from PDFs

Supports:
- Day Sheets (production reports)
- Deposit Slips (collections)
- Pay Reconciliation Reports (payroll)
- Operations Reports (multi-metric)
"""

import io
import json
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    logger.warning("PyPDF2 not installed. PDF text extraction will be limited.")
    PDF_SUPPORT = False

try:
    from pdf2image import convert_from_bytes
    IMAGE_SUPPORT = True
except ImportError:
    logger.warning("pdf2image not installed. PDF image extraction will be limited.")
    IMAGE_SUPPORT = False

try:
    import openai
    AI_SUPPORT = True
except ImportError:
    logger.warning("openai not installed. AI extraction will not be available.")
    AI_SUPPORT = False


class PDFExtractor:
    """Extract structured data from dental practice PDF reports using AI"""

    # Report type detection patterns
    REPORT_TYPES = {
        "day_sheet": ["day sheet", "daily production", "production report"],
        "deposit_slip": ["deposit slip", "deposit report", "collections"],
        "pay_reconciliation": ["pay reconciliation", "payroll reconciliation", "pay report"],
        "operations_report": ["operations report", "operational metrics"],
    }

    # Expected data structures for each report type
    EXTRACTION_SCHEMAS = {
        "day_sheet": {
            "description": "Daily production report showing procedures, charges, and provider performance",
            "fields": [
                "report_date",
                "practice_location",
                "total_production",
                "total_adjustments",
                "net_production",
                "provider_breakdown",  # List of {provider_name, production_amount}
                "procedure_codes",  # List of {code, description, count, amount}
                "patient_visits",
            ]
        },
        "deposit_slip": {
            "description": "Daily collections and deposit reconciliation",
            "fields": [
                "deposit_date",
                "practice_location",
                "cash_amount",
                "check_amount",
                "credit_card_amount",
                "total_deposit",
                "payment_breakdown",  # List of {payment_type, amount}
                "check_numbers",
            ]
        },
        "pay_reconciliation": {
            "description": "Payroll reconciliation and employee compensation",
            "fields": [
                "pay_period_start",
                "pay_period_end",
                "practice_location",
                "total_gross_pay",
                "total_net_pay",
                "total_taxes",
                "employee_breakdown",  # List of {employee_name, role, hours, gross, net}
                "department_totals",
            ]
        },
        "operations_report": {
            "description": "Comprehensive operational metrics",
            "fields": [
                "report_period",
                "practice_location",
                "total_patients",
                "new_patients",
                "appointments_scheduled",
                "appointments_completed",
                "cancellation_rate",
                "no_show_rate",
                "provider_utilization",
            ]
        }
    }

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize PDF extractor with optional OpenAI API key"""
        self.openai_api_key = openai_api_key
        if openai_api_key and AI_SUPPORT:
            openai.api_key = openai_api_key

    def extract_from_file(
        self,
        file_path: str,
        report_type: Optional[str] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Extract structured data from a PDF file

        Args:
            file_path: Path to PDF file
            report_type: Optional report type hint (day_sheet, deposit_slip, etc.)
            use_ai: Whether to use AI extraction (requires OpenAI API key)

        Returns:
            Dictionary with extracted data and metadata
        """
        logger.info(f"Extracting data from PDF: {file_path}")

        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()

        return self.extract_from_bytes(pdf_bytes, report_type, use_ai)

    def extract_from_bytes(
        self,
        pdf_bytes: bytes,
        report_type: Optional[str] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Extract structured data from PDF bytes

        Args:
            pdf_bytes: PDF file as bytes
            report_type: Optional report type hint
            use_ai: Whether to use AI extraction

        Returns:
            Dictionary with extracted data and metadata
        """
        # Step 1: Extract text (for metadata and report type detection)
        text_content = self._extract_text(pdf_bytes)

        # Step 2: Detect report type if not provided
        if not report_type:
            report_type = self._detect_report_type(text_content)

        logger.info(f"Detected report type: {report_type}")

        # Step 3: Extract data
        if use_ai and AI_SUPPORT and self.openai_api_key:
            extracted_data = self._extract_with_ai(pdf_bytes, report_type)
        else:
            extracted_data = self._extract_with_rules(text_content, report_type)

        # Step 4: Add metadata
        result = {
            "report_type": report_type,
            "extraction_method": "ai" if (use_ai and AI_SUPPORT) else "rules",
            "extracted_at": datetime.utcnow().isoformat(),
            "data": extracted_data,
            "raw_text_preview": text_content[:500] if text_content else None,
        }

        return result

    def _extract_text(self, pdf_bytes: bytes) -> str:
        """Extract text content from PDF"""
        if not PDF_SUPPORT:
            logger.warning("PyPDF2 not available, skipping text extraction")
            return ""

        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []

            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _detect_report_type(self, text: str) -> str:
        """Detect report type from text content"""
        text_lower = text.lower()

        for report_type, patterns in self.REPORT_TYPES.items():
            if any(pattern in text_lower for pattern in patterns):
                return report_type

        return "unknown"

    def _extract_with_ai(self, pdf_bytes: bytes, report_type: str) -> Dict[str, Any]:
        """
        Extract data using OpenAI GPT-4 Vision
        Converts PDF to images and uses multimodal LLM
        """
        logger.info(f"Using AI extraction for {report_type}")

        try:
            # Convert PDF first page to image (for small PDFs) or use text
            if IMAGE_SUPPORT:
                images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=150)
                # Convert to base64
                buffered = io.BytesIO()
                images[0].save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                # Use GPT-4 Vision
                response = self._call_gpt4_vision(img_base64, report_type)
            else:
                # Fallback to text-only GPT-4
                text = self._extract_text(pdf_bytes)
                response = self._call_gpt4_text(text, report_type)

            return response

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            # Fallback to rules-based extraction
            text = self._extract_text(pdf_bytes)
            return self._extract_with_rules(text, report_type)

    def _call_gpt4_vision(self, image_base64: str, report_type: str) -> Dict[str, Any]:
        """Call GPT-4 Vision API with PDF image"""
        schema = self.EXTRACTION_SCHEMAS.get(report_type, {})

        prompt = f"""
Extract structured data from this {schema.get('description', 'dental practice report')}.

Please extract the following fields:
{json.dumps(schema.get('fields', []), indent=2)}

Return ONLY a valid JSON object with the extracted data. Use null for missing fields.
For amounts, use decimal numbers without currency symbols.
For dates, use YYYY-MM-DD format.
For lists, return arrays of objects with relevant fields.

Example structure:
{{
    "report_date": "2025-07-15",
    "practice_location": "Eastlake",
    "total_production": 15234.50,
    ...
}}
"""

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",  # GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent extraction
            )

            content = response.choices[0].message.content

            # Parse JSON response
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

        except Exception as e:
            logger.error(f"GPT-4 Vision API error: {e}")
            return {"error": str(e)}

    def _call_gpt4_text(self, text: str, report_type: str) -> Dict[str, Any]:
        """Call GPT-4 API with extracted text"""
        schema = self.EXTRACTION_SCHEMAS.get(report_type, {})

        prompt = f"""
Extract structured data from this {schema.get('description', 'dental practice report')}.

Report text:
{text[:4000]}  # Limit text to avoid token limits

Please extract the following fields:
{json.dumps(schema.get('fields', []), indent=2)}

Return ONLY a valid JSON object with the extracted data. Use null for missing fields.
For amounts, use decimal numbers without currency symbols.
For dates, use YYYY-MM-DD format.
"""

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract structured data from documents and return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"GPT-4 API error: {e}")
            return {"error": str(e)}

    def _extract_with_rules(self, text: str, report_type: str) -> Dict[str, Any]:
        """
        Fallback extraction using regex patterns
        Less accurate but doesn't require API calls
        """
        logger.info(f"Using rules-based extraction for {report_type}")

        import re

        result = {
            "extraction_note": "Rules-based extraction (less accurate than AI)",
            "raw_text_length": len(text),
        }

        # Common patterns
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        money_pattern = r'\$?\s*([\d,]+\.\d{2})'

        # Extract dates
        dates = re.findall(date_pattern, text)
        if dates:
            result["dates_found"] = dates[:5]  # First 5 dates

        # Extract monetary amounts
        amounts = re.findall(money_pattern, text)
        if amounts:
            # Convert to floats
            amounts_float = [float(amt.replace(',', '')) for amt in amounts[:20]]
            result["amounts_found"] = amounts_float
            result["total_amount_sum"] = sum(amounts_float)

        # Extract location (common patterns)
        location_patterns = ["Eastlake", "Torrey Pines", "Downtown", "Westside", "ADS", "Aesthetic"]
        for pattern in location_patterns:
            if pattern.lower() in text.lower():
                result["practice_location"] = pattern
                break

        return result

    def batch_extract(
        self,
        pdf_files: List[str],
        report_type: Optional[str] = None,
        use_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract data from multiple PDF files

        Args:
            pdf_files: List of PDF file paths
            report_type: Optional report type hint
            use_ai: Whether to use AI extraction

        Returns:
            List of extraction results
        """
        results = []

        for pdf_file in pdf_files:
            try:
                result = self.extract_from_file(pdf_file, report_type, use_ai)
                result["source_file"] = str(pdf_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                results.append({
                    "source_file": str(pdf_file),
                    "error": str(e),
                    "extracted_at": datetime.utcnow().isoformat()
                })

        return results


# Convenience functions
def extract_day_sheet(pdf_path: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Extract data from a Day Sheet PDF"""
    extractor = PDFExtractor(openai_api_key)
    return extractor.extract_from_file(pdf_path, report_type="day_sheet")


def extract_deposit_slip(pdf_path: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Extract data from a Deposit Slip PDF"""
    extractor = PDFExtractor(openai_api_key)
    return extractor.extract_from_file(pdf_path, report_type="deposit_slip")


def extract_pay_reconciliation(pdf_path: str, openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Extract data from a Pay Reconciliation PDF"""
    extractor = PDFExtractor(openai_api_key)
    return extractor.extract_from_file(pdf_path, report_type="pay_reconciliation")
