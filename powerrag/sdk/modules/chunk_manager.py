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

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from .chunk import ChunkInfo


class ChunkManager:
    """切片管理模块"""
    
    def __init__(self, client):
        """
        初始化切片管理模块
        
        Args:
            client: PowerRAG客户端实例
        """
        self.client = client
    
    def list(
        self,
        kb_id: str,
        doc_id: str,
        id: Optional[str] = None,
        keywords: Optional[str] = None,
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[List[ChunkInfo], int, Dict[str, Any]]:
        """
        列出文档的切片
        
        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            id: 切片ID（可选，用于精确查询）
            keywords: 关键词搜索（可选）
            page: 页码，默认1
            page_size: 每页数量，默认30
        
        Returns:
            (切片列表, 总数, 文档信息)
        
        Raises:
            Exception: API调用失败
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        
        if id:
            params["id"] = id
        if keywords:
            params["keywords"] = keywords
        
        url = f"/datasets/{kb_id}/documents/{doc_id}/chunks"
        res = self.client.get(url, params=params)
        res_json = res.json()
        
        if res_json.get("code") == 0:
            data = res_json.get("data", {})
            return data.get("chunks", []), data.get("total", 0), data.get("doc", {})
        
        raise Exception(res_json.get("message", "List chunks failed"))
    
    def get(self, kb_id: str, doc_id: str, chunk_id: str) -> ChunkInfo:
        """
        获取切片信息
        
        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            chunk_id: 切片ID
        
        Returns:
            切片信息
        
        Raises:
            Exception: API调用失败或切片不存在
        """
        chunks, total, _ = self.list(kb_id, doc_id, id=chunk_id, page_size=1)
        if not chunks:
            raise Exception(f"Chunk '{chunk_id}' not found")
        return chunks[0]
    
    def create(
        self,
        kb_id: str,
        doc_id: str,
        content: str,
        important_keywords: Optional[List[str]] = None,
        questions: Optional[List[str]] = None,
    ) -> ChunkInfo:
        """
        创建切片
        
        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            content: 切片内容
            important_keywords: 重要关键词列表（可选）
            questions: 问题列表（可选）
        
        Returns:
            创建的切片信息
        
        Raises:
            Exception: API调用失败
        """
        payload = {
            "content": content,
        }
        
        if important_keywords is not None:
            payload["important_keywords"] = important_keywords
        if questions is not None:
            payload["questions"] = questions
        
        url = f"/datasets/{kb_id}/documents/{doc_id}/chunks"
        res = self.client.post(url, json=payload)
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Create chunk failed"))
        
        return res_json.get("data", {}).get("chunk", {})
    
    def update(
        self,
        kb_id: str,
        doc_id: str,
        chunk_id: str,
        content: Optional[str] = None,
        important_keywords: Optional[List[str]] = None,
        questions: Optional[List[str]] = None,
        available: Optional[bool] = None,
        positions: Optional[List[List[int]]] = None,
    ) -> ChunkInfo:
        """
        更新切片
        
        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            chunk_id: 切片ID
            content: 切片内容（可选）
            important_keywords: 重要关键词列表（可选）
            questions: 问题列表（可选）
            available: 是否可用（可选）
            positions: 位置信息（可选）
        
        Returns:
            更新后的切片信息
        
        Raises:
            Exception: API调用失败
        """
        update_data = {}
        
        if content is not None:
            update_data["content"] = content
        if important_keywords is not None:
            update_data["important_keywords"] = important_keywords
        if questions is not None:
            update_data["questions"] = questions
        if available is not None:
            update_data["available"] = available
        if positions is not None:
            update_data["positions"] = positions
        
        if not update_data:
            raise Exception("No fields to update")
        
        url = f"/datasets/{kb_id}/documents/{doc_id}/chunks/{chunk_id}"
        res = self.client.put(url, json=update_data)
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Update chunk failed"))
        
        # API返回成功但不包含chunk数据，需要重新获取
        return self.get(kb_id, doc_id, chunk_id)
    
    def delete(
        self,
        kb_id: str,
        doc_id: str,
        chunk_ids: Optional[List[str]] = None,
    ) -> None:
        """
        删除切片
        
        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            chunk_ids: 切片ID列表，如果为None则删除文档的所有切片
        
        Raises:
            Exception: API调用失败
        """
        payload = {}
        if chunk_ids is not None:
            payload["chunk_ids"] = chunk_ids
        
        url = f"/datasets/{kb_id}/documents/{doc_id}/chunks"
        res = self.client.delete(url, json=payload)
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Delete chunks failed"))
    
    def split_text(
        self,
        text: str,
        parser_id: str = "title",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        文本切片（无需上传文档）
        
        Args:
            text: 要切片的文本（Markdown格式）
            parser_id: 解析器ID（默认"title"）
            config: 解析配置（可选）
        
        Returns:
            切片结果，包含chunks列表和total_chunks数量
        
        Raises:
            Exception: API调用失败
        """
        payload = {
            "text": text,
            "parser_id": parser_id,
        }
        
        if config:
            payload["config"] = config
        
        url = "/powerrag/split"
        res = self.client.post(url, json=payload)
        
        # 检查响应状态码
        if res.status_code != 200:
            try:
                error_json = res.json()
                error_msg = error_json.get("message", f"HTTP {res.status_code}")
            except Exception:
                error_msg = f"HTTP {res.status_code}: {res.text[:200]}"
            raise Exception(error_msg)
        
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Split text failed"))
        
        return res_json.get("data", {})
    
    def split_file(
        self,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        parser_id: str = "naive",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        文件切片（支持所有ParserType方法）
        
        支持三种方式：
        1. 本地文件路径：file_path
        2. 文件URL：file_url
        3. 文件上传：使用 split_file_upload 方法
        
        Args:
            file_path: 本地文件路径（可选，与file_url二选一）
            file_url: 文件URL（可选，与file_path二选一）
            parser_id: 解析器ID，支持所有ParserType：
                - naive, qa, book, laws, paper, manual, presentation
                - table, resume, picture, one, audio, email, tag
                - knowledge_graph, title, regex, smart
                默认"naive"
            config: 解析配置（可选）
                - chunk_token_num: 目标分块大小（tokens），默认512
                - delimiter: 分隔符字符串，默认"\n。.；;！!？？"
                - lang: 语言，默认"Chinese"
                - from_page: 起始页码，默认0
                - to_page: 结束页码，默认100000
                - max_file_size: URL下载的最大文件大小（字节）
                - download_timeout: 下载超时时间（秒）
                - head_request_timeout: HEAD请求超时时间（秒）
        
        Returns:
            切片结果，包含chunks列表、total_chunks数量和filename
        
        Raises:
            Exception: API调用失败
            ValueError: file_path和file_url都未提供
        
        Example:
            ```python
            # 使用本地文件路径
            result = client.chunk.split_file(
                file_path="/path/to/document.pdf",
                parser_id="book",
                config={"chunk_token_num": 512}
            )
            
            # 使用文件URL
            result = client.chunk.split_file(
                file_url="https://example.com/doc.pdf",
                parser_id="naive",
                config={"chunk_token_num": 256}
            )
            ```
        """
        if not file_path and not file_url:
            raise ValueError("Either file_path or file_url must be provided")
        
        payload = {
            "parser_id": parser_id,
        }
        
        if file_path:
            payload["file_path"] = file_path
        if file_url:
            payload["file_url"] = file_url
        
        if config:
            payload["config"] = config
        
        url = "/powerrag/split/file"
        res = self.client.post(url, json=payload)
        
        # 检查响应状态码
        if res.status_code != 200:
            try:
                error_json = res.json()
                error_msg = error_json.get("message", f"HTTP {res.status_code}")
            except Exception:
                error_msg = f"HTTP {res.status_code}: {res.text[:200]}"
            raise Exception(error_msg)
        
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Split file failed"))
        
        return res_json.get("data", {})
    
    def split_file_upload(
        self,
        file_path: Union[str, Path],
        parser_id: str = "naive",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        上传文件并切片（支持所有ParserType方法）
        
        Args:
            file_path: 本地文件路径
            parser_id: 解析器ID，支持所有ParserType，默认"naive"
            config: 解析配置（可选）
                - chunk_token_num: 目标分块大小（tokens），默认512
                - delimiter: 分隔符字符串，默认"\n。.；;！!？？"
                - lang: 语言，默认"Chinese"
                - from_page: 起始页码，默认0
                - to_page: 结束页码，默认100000
        
        Returns:
            切片结果，包含chunks列表、total_chunks数量和filename
        
        Raises:
            Exception: API调用失败
            FileNotFoundError: 文件不存在
        
        Example:
            ```python
            result = client.chunk.split_file_upload(
                file_path="/path/to/document.pdf",
                parser_id="book",
                config={"chunk_token_num": 512}
            )
            print(f"Total chunks: {result['total_chunks']}")
            for chunk in result['chunks']:
                print(chunk)
            ```
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 准备文件
        with open(path, "rb") as f:
            files = [("file", (path.name, f.read()))]
        
        # 准备表单数据
        form_data = {
            "parser_id": parser_id,
        }
        
        if config:
            form_data["config"] = json.dumps(config)
        
        url = "/powerrag/split/file/upload"
        res = self.client.post(url, json=None, files=files, data=form_data)
        
        # 检查响应状态码
        if res.status_code != 200:
            try:
                error_json = res.json()
                error_msg = error_json.get("message", f"HTTP {res.status_code}")
            except Exception:
                error_msg = f"HTTP {res.status_code}: {res.text[:200]}"
            raise Exception(error_msg)
        
        res_json = res.json()
        
        if res_json.get("code") != 0:
            raise Exception(res_json.get("message", "Split file upload failed"))
        
        return res_json.get("data", {})

