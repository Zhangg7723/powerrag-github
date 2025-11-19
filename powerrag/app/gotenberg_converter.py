#
#  Copyright 2025 The OceanBase Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
Gotenberg document converter utilities.

This module provides functions to convert various document formats to PDF
using Gotenberg service. Reference: https://gotenberg.dev/docs/routes
"""

import os
import logging
import io
import requests
from typing import Optional, Callable, Tuple
from api.utils.configs import get_base_config

logger = logging.getLogger(__name__)


def _get_gotenberg_url() -> str:
    """Get Gotenberg service URL from configuration."""
    gotenberg_config = get_base_config("gotenberg", {}) or {}
    return gotenberg_config.get("url", "http://localhost:3000")


def convert_office_to_pdf(
    filename: str,
    binary: Optional[bytes] = None,
    callback: Optional[Callable] = None,
    trace_id: Optional[str] = None,
    timeout: int = 120
) -> Tuple[bytes, str]:
    """
    Convert Office documents (Word, Excel, PowerPoint) to PDF using Gotenberg LibreOffice route.
    
    Reference: https://gotenberg.dev/docs/routes#office-documents-into-pdfs-route
    
    Args:
        filename: Path to the Office document file
        binary: Optional binary content of the file. If None, file will be read from disk.
        callback: Optional callback function for progress updates (progress, message)
        trace_id: Optional trace ID for request tracking
        timeout: Request timeout in seconds (default: 120)
    
    Returns:
        Tuple of (pdf_binary, pdf_filename)
    
    Raises:
        Exception: If conversion fails
    """
    if callback:
        callback(0.15, "Converting Office document to PDF...")
    
    file_handle = None
    try:
        gotenberg_url = _get_gotenberg_url()
        url = f"{gotenberg_url}/forms/libreoffice/convert"
        
        # Prepare file content
        if binary:
            files = {'files': (os.path.basename(filename), io.BytesIO(binary))}
        else:
            file_handle = open(filename, 'rb')
            files = {'files': (os.path.basename(filename), file_handle)}
        
        # Optional: Add trace header for request tracking
        headers = {}
        if trace_id:
            headers['Gotenberg-Trace'] = str(trace_id)
        
        logger.info(f"Converting Office document to PDF via Gotenberg: {filename}")
        response = requests.post(url, files=files, headers=headers, timeout=timeout)
        
        # Ensure file handle is closed
        if file_handle:
            file_handle.close()
            file_handle = None
        
        # Handle different response status codes according to Gotenberg docs
        if response.status_code == 200:
            pdf_binary = response.content
            pdf_filename = os.path.splitext(filename)[0] + ".pdf"
            logger.info(f"Successfully converted {filename} to PDF ({len(pdf_binary)} bytes)")
            
            if callback:
                callback(0.2, "Office document converted to PDF successfully")
            
            return pdf_binary, pdf_filename
        elif response.status_code == 400:
            error_msg = f"Gotenberg conversion failed: Bad Request - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        elif response.status_code == 503:
            error_msg = f"Gotenberg conversion failed: Service Unavailable - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        else:
            error_msg = f"Gotenberg conversion failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        if file_handle:
            file_handle.close()
        error_msg = f"Failed to convert Office document to PDF (network error): {str(e)}"
        logger.error(error_msg)
        if callback:
            callback(-1, error_msg)
        raise Exception(error_msg)
    except Exception as e:
        if file_handle:
            file_handle.close()
        error_msg = f"Failed to convert Office document to PDF: {str(e)}"
        logger.error(error_msg)
        if callback:
            callback(-1, error_msg)
        raise Exception(error_msg)


def convert_html_to_pdf(
    filename: str,
    binary: Optional[bytes] = None,
    callback: Optional[Callable] = None,
    trace_id: Optional[str] = None,
    timeout: int = 120
) -> Tuple[bytes, str]:
    """
    Convert HTML documents to PDF using Gotenberg Chromium route.
    
    Reference: https://gotenberg.dev/docs/routes#html-file-into-pdf-route
    
    Note: According to Gotenberg docs, the filename must be 'index.html' for HTML route.
    
    Args:
        filename: Path to the HTML file (original filename for logging)
        binary: Optional binary content of the file. If None, file will be read from disk.
        callback: Optional callback function for progress updates (progress, message)
        trace_id: Optional trace ID for request tracking
        timeout: Request timeout in seconds (default: 120)
    
    Returns:
        Tuple of (pdf_binary, pdf_filename)
    
    Raises:
        Exception: If conversion fails
    """
    if callback:
        callback(0.15, "Converting HTML document to PDF...")
    
    file_handle = None
    try:
        gotenberg_url = _get_gotenberg_url()
        url = f"{gotenberg_url}/forms/chromium/convert/html"
        
        # Prepare file content - Gotenberg requires filename to be 'index.html' for HTML route
        if binary:
            html_content = binary if isinstance(binary, bytes) else binary.encode('utf-8')
            files = {'files': ('index.html', io.BytesIO(html_content))}
        else:
            file_handle = open(filename, 'rb')
            files = {'files': ('index.html', file_handle)}
        
        # Optional: Add trace header for request tracking
        headers = {}
        if trace_id:
            headers['Gotenberg-Trace'] = str(trace_id)
        
        logger.info(f"Converting HTML document to PDF via Gotenberg: {filename}")
        response = requests.post(url, files=files, headers=headers, timeout=timeout)
        
        # Ensure file handle is closed
        if file_handle:
            file_handle.close()
            file_handle = None
        
        # Handle different response status codes according to Gotenberg docs
        if response.status_code == 200:
            pdf_binary = response.content
            pdf_filename = os.path.splitext(filename)[0] + ".pdf"
            logger.info(f"Successfully converted {filename} to PDF ({len(pdf_binary)} bytes)")
            
            if callback:
                callback(0.2, "HTML document converted to PDF successfully")
            
            return pdf_binary, pdf_filename
        elif response.status_code == 400:
            error_msg = f"Gotenberg conversion failed: Bad Request - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        elif response.status_code == 503:
            error_msg = f"Gotenberg conversion failed: Service Unavailable - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        else:
            error_msg = f"Gotenberg conversion failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        if file_handle:
            file_handle.close()
        error_msg = f"Failed to convert HTML document to PDF (network error): {str(e)}"
        logger.error(error_msg)
        if callback:
            callback(-1, error_msg)
        raise Exception(error_msg)
    except Exception as e:
        if file_handle:
            file_handle.close()
        error_msg = f"Failed to convert HTML document to PDF: {str(e)}"
        logger.error(error_msg)
        if callback:
            callback(-1, error_msg)
        raise Exception(error_msg)

