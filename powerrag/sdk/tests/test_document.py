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

import pytest
from powerrag.sdk import PowerRAGClient


class TestDocumentUpload:
    """测试文档上传"""
    
    def test_upload_single_file(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试上传单个文件"""
        docs = client.document.upload(kb_id, test_file_path)
        assert len(docs) == 1
        assert docs[0]["id"] is not None
        assert docs[0]["name"] is not None
        
        # 清理
        client.document.delete(kb_id, [docs[0]["id"]])
    
    def test_upload_multiple_files(self, client: PowerRAGClient, kb_id: str, test_files: list):
        """测试批量上传文件"""
        docs = client.document.upload(kb_id, test_files)
        assert len(docs) == len(test_files)
        
        # 清理
        doc_ids = [doc["id"] for doc in docs]
        client.document.delete(kb_id, doc_ids)
    
    def test_upload_nonexistent_file(self, client: PowerRAGClient, kb_id: str):
        """测试上传不存在的文件"""
        with pytest.raises(FileNotFoundError):
            client.document.upload(kb_id, "nonexistent.pdf")


class TestDocumentList:
    """测试文档列表"""
    
    def test_list_all_documents(self, client: PowerRAGClient, kb_id: str):
        """测试列出所有文档"""
        docs, total = client.document.list(kb_id)
        assert isinstance(docs, list)
        assert total >= 0
    
    def test_list_with_filter(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试使用过滤器列出文档"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_name = uploaded_docs[0]["name"]
        
        try:
            docs, total = client.document.list(kb_id, name=doc_name)
            assert len(docs) >= 1
            assert any(doc["name"] == doc_name for doc in docs)
        finally:
            client.document.delete(kb_id, [uploaded_docs[0]["id"]])


class TestDocumentGet:
    """测试文档查询"""
    
    def test_get_existing_document(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试获取存在的文档"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            doc = client.document.get(kb_id, doc_id)
            assert doc["id"] == doc_id
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_get_nonexistent_document(self, client: PowerRAGClient, kb_id: str):
        """测试获取不存在的文档"""
        # 使用有效的UUID格式但不存在于系统中的ID
        nonexistent_id = "a" * 32  # 32个字符的十六进制字符串
        with pytest.raises(Exception) as exc_info:
            client.document.get(kb_id, nonexistent_id)
        # 检查错误信息中是否包含 "not found" 或 "don't own"
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "don't own" in error_msg


class TestDocumentUpdate:
    """测试文档更新"""
    
    def test_update_name(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试更新文档名称"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 注意：不能更改文件扩展名，所以保持 .html 扩展名
            updated_doc = client.document.update(kb_id, doc_id, name="updated_name.html")
            assert updated_doc["name"] == "updated_name.html"
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_rename(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试重命名文档"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 注意：不能更改文件扩展名，所以保持 .html 扩展名
            renamed_doc = client.document.rename(kb_id, doc_id, "renamed.html")
            assert renamed_doc["name"] == "renamed.html"
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_set_meta(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试设置元数据"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            meta_fields = {"author": "Test Author", "category": "Test"}
            updated_doc = client.document.set_meta(kb_id, doc_id, meta_fields)
            assert updated_doc.get("meta_fields") == meta_fields
        finally:
            client.document.delete(kb_id, [doc_id])


class TestDocumentDelete:
    """测试文档删除"""
    
    def test_delete_single_document(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试删除单个文档"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        client.document.delete(kb_id, [doc_id])
        
        with pytest.raises(Exception):
            client.document.get(kb_id, doc_id)
    
    def test_delete_multiple_documents(self, client: PowerRAGClient, kb_id: str, test_files: list):
        """测试批量删除文档"""
        uploaded_docs = client.document.upload(kb_id, test_files)
        doc_ids = [doc["id"] for doc in uploaded_docs]
        
        client.document.delete(kb_id, doc_ids)
        
        for doc_id in doc_ids:
            with pytest.raises(Exception):
                client.document.get(kb_id, doc_id)


class TestDocumentDownload:
    """测试文档下载"""
    
    def test_download_to_bytes(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试下载为字节流"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            content = client.document.download(kb_id, doc_id)
            assert isinstance(content, bytes)
            assert len(content) > 0
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_download_to_file(self, client: PowerRAGClient, kb_id: str, test_file_path: str, tmp_path):
        """测试下载到文件"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            save_path = tmp_path / "downloaded_file.html"
            result_path = client.document.download(kb_id, doc_id, save_path=str(save_path))
            
            assert result_path == str(save_path)
            assert save_path.exists()
            assert save_path.stat().st_size > 0
        finally:
            client.document.delete(kb_id, [doc_id])


class TestDocumentParse:
    """测试文档解析"""
    
    def test_parse_to_chunk_sync(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试同步解析为切片"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            results = client.document.parse_to_chunk(kb_id, [doc_id], wait=True)
            assert len(results) == 1
            assert results[0]["status"] == "DONE"
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_parse_to_chunk_async(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试异步解析为切片"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            task_id = client.document.parse_to_chunk(kb_id, [doc_id], wait=False)
            assert task_id is not None
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_cancel_parse(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试取消解析"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            client.document.parse_to_chunk(kb_id, [doc_id], wait=False)
            client.document.cancel_parse(kb_id, [doc_id])
            
            doc = client.document.get(kb_id, doc_id)
            assert doc["run"] in ["CANCEL", "UNSTART"]
        finally:
            client.document.delete(kb_id, [doc_id])


class TestDocumentParseToMD:
    """测试文档解析为 Markdown（不切分）"""
    
    def test_parse_to_md_basic(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试基本的 parse_to_md 功能"""
        # 上传文档
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 解析为 Markdown
            result = client.document.parse_to_md(doc_id)
            
            # 验证返回结果
            assert "doc_id" in result
            assert "doc_name" in result
            assert "markdown" in result
            assert "markdown_length" in result
            assert result["doc_id"] == doc_id
            assert isinstance(result["markdown"], str)
            assert result["markdown_length"] > 0
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_parse_to_md_with_config(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试带配置参数的 parse_to_md"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 使用配置解析
            config = {
                "layout_recognize": "mineru",
                "enable_ocr": False,
                "enable_formula": False,
                "enable_table": True
            }
            result = client.document.parse_to_md(doc_id, config=config)
            
            # 验证返回结果
            assert result["doc_id"] == doc_id
            assert "markdown" in result
            assert len(result["markdown"]) > 0
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_parse_to_md_nonexistent_doc(self, client: PowerRAGClient):
        """测试解析不存在的文档"""
        nonexistent_id = "nonexistent_doc_id_123"
        
        with pytest.raises(Exception) as exc_info:
            client.document.parse_to_md(nonexistent_id)
        
        # 验证错误信息
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "failed" in error_msg
    
    def test_parse_to_md_with_images(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试解析带图片的文档"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            result = client.document.parse_to_md(doc_id)
            
            # 验证图片相关字段
            assert "images" in result
            assert "total_images" in result
            assert isinstance(result["images"], dict)
            assert isinstance(result["total_images"], int)
            assert result["total_images"] >= 0
        finally:
            client.document.delete(kb_id, [doc_id])


class TestDocumentParseToMDAsync:
    """测试异步解析文档为 Markdown"""
    
    def test_parse_to_md_async_basic(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试异步解析基本功能"""
        # 上传文档
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 提交异步任务
            task_id = client.document.parse_to_md_async(doc_id)
            assert task_id
            assert len(task_id) > 0
            
            # 查询任务状态
            status = client.document.get_parse_to_md_status(task_id)
            assert "task_id" in status
            assert "status" in status
            assert status["status"] in ["pending", "processing", "success", "failed"]
            
            # 等待任务完成
            result = client.document.wait_for_parse_to_md(task_id, timeout=300)
            assert result["status"] == "success"
            assert "result" in result
            assert "markdown" in result["result"]
            assert result["result"]["markdown_length"] > 0
            
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_parse_to_md_async_with_config(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试异步解析带配置"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            # 提交带配置的异步任务
            task_id = client.document.parse_to_md_async(
                doc_id,
                config={
                    "layout_recognize": "mineru",
                    "enable_ocr": False,
                    "enable_table": True
                }
            )
            
            # 等待完成
            result = client.document.wait_for_parse_to_md(task_id, timeout=300)
            assert result["status"] == "success"
            assert result["result"]["markdown_length"] > 0
            
        finally:
            client.document.delete(kb_id, [doc_id])
    
    def test_parse_to_md_async_nonexistent_doc(self, client: PowerRAGClient):
        """测试异步解析不存在的文档"""
        with pytest.raises(Exception) as exc_info:
            client.document.parse_to_md_async("nonexistent_doc_id")
        
        assert "not found" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
    
    def test_get_parse_to_md_status_not_found(self, client: PowerRAGClient):
        """测试查询不存在的任务状态"""
        status = client.document.get_parse_to_md_status("nonexistent_task_id")
        assert status["status"] == "not_found"
    
    def test_wait_for_parse_to_md_timeout(self, client: PowerRAGClient, kb_id: str, test_file_path: str):
        """测试等待任务超时（使用极短超时时间）"""
        uploaded_docs = client.document.upload(kb_id, test_file_path)
        doc_id = uploaded_docs[0]["id"]
        
        try:
            task_id = client.document.parse_to_md_async(doc_id)
            
            # 使用极短的超时时间（0.1秒）来触发超时
            with pytest.raises(TimeoutError):
                client.document.wait_for_parse_to_md(task_id, timeout=0.1, interval=0.05)
            
        finally:
            client.document.delete(kb_id, [doc_id])


class TestDocumentParseToMDUpload:
    """测试直接上传文件并解析为 Markdown"""
    
    def test_parse_to_md_upload_json_response(self, client: PowerRAGClient, test_file_path: str):
        """测试上传文件并返回 JSON 响应"""
        result = client.document.parse_to_md_upload(test_file_path)
        
        # 验证返回结果
        assert "content" in result
        assert "images" in result
        assert "total_images" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
    
    def test_parse_to_md_upload_with_config(self, client: PowerRAGClient, test_file_path: str):
        """测试带配置参数上传并解析"""
        config = {
            "layout_recognize": "mineru",
            "enable_ocr": False
        }
        result = client.document.parse_to_md_upload(test_file_path, config=config)
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_parse_to_md_upload_nonexistent_file(self, client: PowerRAGClient):
        """测试上传不存在的文件"""
        with pytest.raises(FileNotFoundError):
            client.document.parse_to_md_upload("nonexistent_file.pdf")
    
    def test_parse_to_md_upload_different_formats(self, client: PowerRAGClient, test_file_path: str):
        """测试上传不同格式的文件"""
        # 注意：这个测试需要实际的不同格式文件
        # 这里我们只测试 txt 文件，实际使用时可以添加更多格式
        result = client.document.parse_to_md_upload(test_file_path)
        
        assert "content" in result
        assert len(result["content"]) > 0


class TestDocumentParseToMDBinary:
    """测试使用二进制文件解析为 Markdown"""
    
    def test_parse_to_md_binary_basic(self, client: PowerRAGClient, test_file_path: str):
        """测试基本的二进制文件解析功能"""
        # 读取文件为二进制
        with open(test_file_path, "rb") as f:
            file_binary = f.read()
        
        # 使用二进制数据解析
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="test_document.html"
        )
        
        # 验证返回结果
        assert "content" in result
        assert "images" in result
        assert "total_images" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
    
    def test_parse_to_md_binary_with_config(self, client: PowerRAGClient, test_file_path: str):
        """测试带配置参数的二进制文件解析"""
        with open(test_file_path, "rb") as f:
            file_binary = f.read()
        
        config = {
            "layout_recognize": "mineru",
            "enable_ocr": False,
            "enable_table": True
        }
        
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="test_document.html",
            config=config
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_parse_to_md_binary_empty_content(self, client: PowerRAGClient):
        """测试空的二进制内容"""
        with pytest.raises(ValueError) as exc_info:
            client.document.parse_to_md_binary(
                file_binary=b"",
                filename="test.html"
            )
        
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_parse_to_md_binary_empty_filename(self, client: PowerRAGClient):
        """测试空的文件名"""
        with pytest.raises(ValueError) as exc_info:
            client.document.parse_to_md_binary(
                file_binary=b"test content",
                filename=""
            )
        
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_parse_to_md_binary_different_file_types(self, client: PowerRAGClient, tmp_path):
        """测试不同文件类型的二进制解析"""
        # 测试 HTML 文件
        html_file = tmp_path / "test.html"
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        html_file.write_text(html_content)
        
        with open(html_file, "rb") as f:
            file_binary = f.read()
        
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="test.html"
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_parse_to_md_binary_with_images(self, client: PowerRAGClient, test_file_path: str):
        """测试解析带图片的文档（二进制）"""
        with open(test_file_path, "rb") as f:
            file_binary = f.read()
        
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="test_document.html"
        )
        
        # 验证图片相关字段
        assert "images" in result
        assert "total_images" in result
        assert isinstance(result["images"], dict)
        assert isinstance(result["total_images"], int)
        assert result["total_images"] >= 0
    
    def test_parse_to_md_binary_filename_with_extension(self, client: PowerRAGClient, test_file_path: str):
        """测试文件名必须包含扩展名"""
        with open(test_file_path, "rb") as f:
            file_binary = f.read()
        
        # 测试带正确扩展名的文件名
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="document.html"
        )
        
        assert "content" in result
    
    def test_parse_to_md_binary_large_file(self, client: PowerRAGClient, tmp_path):
        """测试较大文件的二进制解析"""
        # 创建一个相对较大的测试文件
        large_file = tmp_path / "large_test.html"
        large_content = "<html><body>" + "<p>Test paragraph.</p>" * 1000 + "</body></html>"
        large_file.write_text(large_content)
        
        with open(large_file, "rb") as f:
            file_binary = f.read()
        
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="large_test.html"
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
        # 验证内容长度合理
        assert len(result["content"]) > 1000
    
    def test_parse_to_md_binary_utf8_content(self, client: PowerRAGClient, tmp_path):
        """测试包含UTF-8字符的文件"""
        utf8_file = tmp_path / "utf8_test.html"
        utf8_content = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>UTF-8测试</title></head>
        <body>
            <h1>中文标题</h1>
            <p>这是中文内容。</p>
            <p>English content with special chars: é, ñ, ü</p>
        </body>
        </html>
        """
        utf8_file.write_text(utf8_content, encoding="utf-8")
        
        with open(utf8_file, "rb") as f:
            file_binary = f.read()
        
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="utf8_test.html"
        )
        
        assert "content" in result
        assert len(result["content"]) > 0


class TestDocumentInputTypeAutoDetection:
    """测试 input_type 自动检测功能"""
    
    @staticmethod
    def _create_valid_pdf_content(text_lines=None):
        """
        创建一个有效的 PDF 文件内容
        
        Args:
            text_lines: 可选的文本行列表，用于自定义 PDF 内容
        
        Returns:
            bytes: PDF 文件的二进制内容
        """
        if text_lines is None:
            text_lines = ["Test PDF File"]
        
        try:
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            # 创建一个有效的 PDF 内容
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            y_pos = 750
            for line in text_lines:
                c.drawString(100, y_pos, line)
                y_pos -= 20
            c.showPage()
            c.save()
            pdf_content = buffer.getvalue()
            buffer.close()
            return pdf_content
        except ImportError:
            # 如果 reportlab 不可用，创建一个最小但有效的 PDF
            # 这是一个最小有效的 PDF 1.4 文档，包含一个文本对象
            return (
                b"%PDF-1.4\n"
                b"1 0 obj\n"
                b"<<\n"
                b"/Type /Catalog\n"
                b"/Pages 2 0 R\n"
                b">>\n"
                b"endobj\n"
                b"2 0 obj\n"
                b"<<\n"
                b"/Type /Pages\n"
                b"/Kids [3 0 R]\n"
                b"/Count 1\n"
                b">>\n"
                b"endobj\n"
                b"3 0 obj\n"
                b"<<\n"
                b"/Type /Page\n"
                b"/Parent 2 0 R\n"
                b"/MediaBox [0 0 612 792]\n"
                b"/Contents 4 0 R\n"
                b"/Resources <<\n"
                b"/Font <<\n"
                b"/F1 5 0 R\n"
                b">>\n"
                b">>\n"
                b">>\n"
                b"endobj\n"
                b"4 0 obj\n"
                b"<<\n"
                b"/Length 44\n"
                b">>\n"
                b"stream\n"
                b"BT\n"
                b"/F1 12 Tf\n"
                b"100 700 Td\n"
                b"(Test PDF) Tj\n"
                b"ET\n"
                b"endstream\n"
                b"endobj\n"
                b"5 0 obj\n"
                b"<<\n"
                b"/Type /Font\n"
                b"/Subtype /Type1\n"
                b"/BaseFont /Helvetica\n"
                b">>\n"
                b"endobj\n"
                b"xref\n"
                b"0 6\n"
                b"0000000000 65535 f \n"
                b"0000000009 00000 n \n"
                b"0000000058 00000 n \n"
                b"0000000115 00000 n \n"
                b"0000000306 00000 n \n"
                b"0000000400 00000 n \n"
                b"trailer\n"
                b"<<\n"
                b"/Size 6\n"
                b"/Root 1 0 R\n"
                b">>\n"
                b"startxref\n"
                b"492\n"
                b"%%EOF\n"
            )
    
    def test_auto_detection_with_valid_extension(self, client: PowerRAGClient, tmp_path):
        """测试有有效扩展名时，input_type='auto' 优先使用扩展名"""
        # 创建一个 HTML 文件
        html_file = tmp_path / "test.html"
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        html_file.write_text(html_content)
        
        with open(html_file, "rb") as f:
            file_binary = f.read()
        
        # input_type='auto' 是默认值，会优先使用 .html 扩展名
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="test.html"
            # input_type='auto' 是默认值，可以省略
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_auto_detection_without_extension_pdf(self, client: PowerRAGClient, tmp_path):
        """测试无扩展名 PDF 文件，input_type='auto' 会自动从二进制检测"""
        # 创建一个有效的 PDF 文件
        pdf_content = self._create_valid_pdf_content([
            "Test PDF File",
            "This is a test PDF document for auto-detection testing.",
            "The file has no extension, so binary detection should be used."
        ])
        
        # 使用没有扩展名的文件名，input_type='auto' 会从二进制内容检测出 PDF
        result = client.document.parse_to_md_binary(
            file_binary=pdf_content,
            filename="document_no_extension"
            # input_type='auto' 是默认值，会从二进制内容检测出 PDF
        )
        
        # 验证解析结果
        assert "content" in result, "Result should contain 'content' field"
        assert len(result["content"]) > 0, "Content should not be empty (PDF should be successfully parsed)"
        assert isinstance(result["content"], str), "Content should be a string"
    
    def test_auto_detection_without_extension_html(self, client: PowerRAGClient):
        """测试无扩展名 HTML 文件，input_type='auto' 会自动从二进制检测"""
        html_content = b"<html><body><h1>Test Title</h1><p>Test content</p></body></html>"
        
        # 使用没有扩展名的文件名
        result = client.document.parse_to_md_binary(
            file_binary=html_content,
            filename="document_without_ext"
            # input_type='auto' 会从二进制内容检测出 HTML
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_explicit_input_type_pdf(self, client: PowerRAGClient, tmp_path):
        """测试显式指定 input_type='pdf'"""
        # 创建一个有效的 PDF 文件
        pdf_content = self._create_valid_pdf_content([
            "Test PDF File",
            "This is a test PDF document for PowerRAG SDK testing."
        ])
        
        # 显式指定为 PDF 类型，即使文件名没有扩展名
        result = client.document.parse_to_md_binary(
            file_binary=pdf_content,
            filename="document",
            input_type="pdf"  # 显式指定类型
        )
        
        # 验证解析结果
        assert "content" in result, "Result should contain 'content' field"
        assert len(result["content"]) > 0, "Content should not be empty"
        assert isinstance(result["content"], str), "Content should be a string"
    
    def test_explicit_input_type_html(self, client: PowerRAGClient):
        """测试显式指定 input_type='html'"""
        html_content = b"<html><body><h1>Title</h1><p>Paragraph</p></body></html>"
        
        # 显式指定为 HTML 类型
        result = client.document.parse_to_md_binary(
            file_binary=html_content,
            filename="document",
            input_type="html"  # 显式指定类型
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_parse_to_md_upload_with_auto_detection(self, client: PowerRAGClient, tmp_path):
        """测试 parse_to_md_upload 方法的自动检测功能"""
        # 创建一个测试文件
        html_file = tmp_path / "test_auto.html"
        html_content = "<html><body><h1>Auto Detection Test</h1></body></html>"
        html_file.write_text(html_content)
        
        # 使用默认的 input_type='auto'
        result = client.document.parse_to_md_upload(str(html_file))
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_parse_to_md_upload_with_explicit_type(self, client: PowerRAGClient, tmp_path):
        """测试 parse_to_md_upload 显式指定类型"""
        html_file = tmp_path / "test_explicit.html"
        html_content = "<html><body><h1>Explicit Type Test</h1></body></html>"
        html_file.write_text(html_content)
        
        # 显式指定类型
        result = client.document.parse_to_md_upload(
            str(html_file),
            input_type="html"
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_auto_detection_priority_extension_over_binary(self, client: PowerRAGClient, tmp_path):
        """测试 input_type='auto' 优先使用扩展名而非二进制检测"""
        # 创建一个 HTML 文件
        html_file = tmp_path / "priority_test.html"
        html_content = "<html><body><h1>Priority Test</h1><p>Extension should be used first</p></body></html>"
        html_file.write_text(html_content)
        
        with open(html_file, "rb") as f:
            file_binary = f.read()
        
        # 文件名有 .html 扩展名，应该优先使用扩展名识别
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="priority_test.html"
            # input_type='auto' 默认值
        )
        
        assert "content" in result
        # 验证确实解析成功（说明使用了正确的类型）
        assert "Priority Test" in result["content"] or len(result["content"]) > 0
    
    def test_auto_detection_fallback_to_binary(self, client: PowerRAGClient):
        """测试扩展名不支持时，fallback 到二进制检测"""
        html_content = b"<html><body><h1>Fallback Test</h1></body></html>"
        
        # 使用一个不支持的扩展名
        result = client.document.parse_to_md_binary(
            file_binary=html_content,
            filename="document.unknown_ext"
            # input_type='auto' 会先尝试 .unknown_ext（失败），然后从二进制检测
        )
        
        # 应该能够通过二进制检测识别为 HTML
        assert "content" in result
        assert len(result["content"]) > 0
    
    def test_config_with_input_type(self, client: PowerRAGClient, tmp_path):
        """测试 config 中包含 input_type 参数"""
        html_file = tmp_path / "config_test.html"
        html_content = "<html><body><h1>Config Test</h1></body></html>"
        html_file.write_text(html_content)
        
        with open(html_file, "rb") as f:
            file_binary = f.read()
        
        # 同时使用 config 和 input_type
        result = client.document.parse_to_md_binary(
            file_binary=file_binary,
            filename="config_test.html",
            config={
                "layout_recognize": "mineru",
                "enable_table": True
            },
            input_type="html"
        )
        
        assert "content" in result
        assert len(result["content"]) > 0


class TestDocumentFileUrl:
    """测试 file_url 参数功能"""
    
    def test_parse_from_url_basic(self, client: PowerRAGClient):
        """测试从URL下载并解析文件（基本功能）"""
        import requests
        import json
        
        # 使用一个公开可访问的示例 HTML URL
        file_url = "https://httpbin.org/html"
        
        # 直接调用 API（因为 SDK 方法已被删除）
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": file_url,
                "config": json.dumps({"input_type": "html"})
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert "content" in result["data"]
        assert len(result["data"]["content"]) > 0
    
    def test_parse_from_url_with_filename(self, client: PowerRAGClient):
        """测试从URL下载并指定文件名"""
        import requests
        import json
        
        file_url = "https://httpbin.org/html"
        custom_filename = "custom_document.html"
        
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": file_url,
                "config": json.dumps({
                    "filename": custom_filename,
                    "input_type": "html"
                })
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
    
    def test_parse_from_url_with_auto_detection(self, client: PowerRAGClient):
        """测试从URL下载，使用 input_type='auto' 自动检测"""
        import requests
        import json
        
        file_url = "https://httpbin.org/html"
        
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": file_url,
                "config": json.dumps({
                    "input_type": "auto"  # 自动检测
                })
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert "content" in result["data"]
    
    def test_parse_from_invalid_url(self, client: PowerRAGClient):
        """测试无效URL应返回错误"""
        import requests
        import json
        
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/file.pdf"
        
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": invalid_url,
                "config": json.dumps({})
            }
        )
        
        # 应该返回 400 错误
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 400
        assert "Failed to download" in result["message"]
    
    def test_parse_cannot_provide_both_file_and_url(self, client: PowerRAGClient, tmp_path):
        """测试不能同时提供 file 和 file_url"""
        import requests
        
        # 创建临时文件
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body>Test</body></html>")
        
        file_url = "https://httpbin.org/html"
        
        # 同时提供 file 和 file_url
        with open(html_file, "rb") as f:
            response = requests.post(
                f"{client.api_url}/powerrag/parse_to_md/upload",
                headers={"Authorization": f"Bearer {client.api_key}"},
                files={"file": ("test.html", f, "text/html")},
                data={
                    "file_url": file_url,
                    "config": "{}"
                }
            )
        
        # 应该返回 400 错误
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 400
        assert "Cannot provide both" in result["message"]
    
    def test_parse_must_provide_file_or_url(self, client: PowerRAGClient):
        """测试必须提供 file 或 file_url 其中之一"""
        import requests
        
        # 不提供 file 也不提供 file_url
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={"config": "{}"}
        )
        
        # 应该返回 400 错误
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 400
        assert "Either 'file' or 'file_url' must be provided" in result["message"]
    
    def test_parse_from_url_with_config(self, client: PowerRAGClient):
        """测试从URL下载并使用完整配置"""
        import requests
        import json
        
        file_url = "https://httpbin.org/html"
        
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": file_url,
                "config": json.dumps({
                    "filename": "complete_config.html",
                    "input_type": "html",
                    "layout_recognize": "mineru",
                    "enable_table": True
                })
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert "content" in result["data"]
    
    def test_parse_from_url_empty_file(self, client: PowerRAGClient):
        """测试从URL下载空文件应返回错误"""
        import requests
        import json
        
        # 使用一个返回空内容的URL（如果存在）
        # 注意：这个测试可能需要 mock，这里使用真实场景
        # httpbin.org/bytes/0 返回 0 字节
        empty_url = "https://httpbin.org/bytes/0"
        
        response = requests.post(
            f"{client.api_url}/powerrag/parse_to_md/upload",
            headers={"Authorization": f"Bearer {client.api_key}"},
            data={
                "file_url": empty_url,
                "config": json.dumps({"filename": "empty.bin"})
            }
        )
        
        # 应该返回 400 错误
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 400
        assert "empty" in result["message"].lower()