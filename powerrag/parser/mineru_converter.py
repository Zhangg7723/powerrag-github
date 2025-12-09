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
MinerU解析器结果转换器
"""

from typing import List, Dict, Any, Optional
from PIL import Image
from .vlm_intermediate_model import (
    VLMResultConverter, PageInfo, ContentBlock, ImageBlock, TableBlock, 
    FormulaBlock, BlockType, BoundingBox
)


class MinerUResultConverter(VLMResultConverter):
    """MinerU解析器结果转换器
    
    将MinerU模型的输出格式转换为中间结构
    MinerU输出格式: {"para_blocks": [...], "discarded_blocks": [...], "page_size": [...], "page_idx": ...}
    """
    
    def convert_to_intermediate(
        self,
        model_output: Dict[str, Any],
        page_index: int,
        page_size: List[int],
        page_image: Optional[Image.Image] = None,
        **kwargs
    ) -> PageInfo:
        """
        将MinerU模型输出转换为中间结构
        
        Args:
            model_output: MinerU模型输出，格式为 {"para_blocks": [...], "discarded_blocks": [...], ...}
            page_index: 页面索引
            page_size: 页面尺寸 [width, height]（如果model_output中有则优先使用）
            page_image: 页面图像（PIL Image）
            **kwargs: 其他参数
            
        Returns:
            PageInfo: 转换后的页面信息
        """
        # 优先使用model_output中的page_size
        if "page_size" in model_output:
            page_size = model_output["page_size"]
        
        # 获取页面索引（优先使用model_output中的）
        if "page_idx" in model_output:
            page_index = model_output["page_idx"]
        
        para_blocks = model_output.get("para_blocks", [])
        discarded_blocks_data = model_output.get("discarded_blocks", [])
        
        blocks = []
        discarded_blocks = []
        
        # 转换para_blocks
        for block_data in para_blocks:
            block = self._convert_block(block_data)
            if block:
                blocks.append(block)
        
        # 转换discarded_blocks
        for block_data in discarded_blocks_data:
            block = self._convert_block(block_data)
            if block:
                discarded_blocks.append(block)
        
        return PageInfo(
            page_index=page_index,
            page_size=page_size,
            blocks=blocks,
            discarded_blocks=discarded_blocks,
            metadata={"source": "mineru"}
        )
    
    def _convert_block(self, block_data: Dict[str, Any]) -> Optional[ContentBlock]:
        """将单个block数据转换为ContentBlock"""
        if not isinstance(block_data, dict):
            return None
        
        # 获取块类型
        block_type_str = block_data.get("type", "")
        block_type = self._parse_block_type(block_type_str, block_data)
        
        # 获取边界框
        bbox = self._extract_bbox(block_data)
        if not bbox:
            return None
        
        # 获取内容
        content = block_data.get("text", block_data.get("content", ""))
        
        # 获取索引
        index = block_data.get("index", 0)
        
        # 获取元数据
        metadata = {k: v for k, v in block_data.items() 
                   if k not in ["type", "bbox", "text", "content", "index", "spans"]}
        
        # 根据类型创建对应的块
        if block_type == BlockType.IMAGE:
            block = ImageBlock(
                block_type=BlockType.IMAGE,
                bbox=bbox,
                content=content,
                index=index,
                metadata=metadata
            )
            # 处理图片URL或base64
            if "image_url" in block_data:
                block.image_url = block_data["image_url"]
            if "image_base64" in block_data:
                block.image_base64 = block_data["image_base64"]
            if "image_filename" in block_data:
                block.image_filename = block_data["image_filename"]
            return block
        
        elif block_type == BlockType.TABLE:
            block = TableBlock(
                block_type=BlockType.TABLE,
                bbox=bbox,
                content=content,
                index=index,
                table_html=block_data.get("table_html"),
                table_markdown=block_data.get("table_markdown"),
                metadata=metadata
            )
            return block
        
        elif block_type in [BlockType.FORMULA, BlockType.INTERLINE_EQUATION]:
            is_inline = block_type == BlockType.FORMULA
            block = FormulaBlock(
                block_type=block_type,
                bbox=bbox,
                content=content,
                index=index,
                latex=block_data.get("latex", content),
                is_inline=is_inline,
                metadata=metadata
            )
            return block
        
        else:
            return ContentBlock(
                block_type=block_type,
                bbox=bbox,
                content=content,
                index=index,
                metadata=metadata
            )
    
    def _parse_block_type(self, type_str: str, block_data: Dict[str, Any]) -> BlockType:
        """解析块类型"""
        type_str = type_str.lower() if type_str else ""
        
        # 根据type字符串或block_data中的其他字段判断类型
        if "image" in type_str or block_data.get("image_url") or block_data.get("image_base64"):
            return BlockType.IMAGE
        elif "table" in type_str or block_data.get("table_html") or block_data.get("table_markdown"):
            return BlockType.TABLE
        elif "formula" in type_str or "equation" in type_str or block_data.get("latex"):
            # 判断是行内还是行间公式
            if "inline" in type_str or block_data.get("is_inline", False):
                return BlockType.FORMULA
            else:
                return BlockType.INTERLINE_EQUATION
        elif "title" in type_str or "heading" in type_str:
            return BlockType.TITLE
        elif "code" in type_str:
            return BlockType.CODE
        elif "list" in type_str:
            return BlockType.LIST
        elif "ref" in type_str or "reference" in type_str:
            return BlockType.REF_TEXT
        elif "phonetic" in type_str:
            return BlockType.PHONETIC
        else:
            return BlockType.TEXT
    
    def _extract_bbox(self, block_data: Dict[str, Any]) -> Optional[BoundingBox]:
        """提取边界框"""
        # 尝试多种可能的字段名
        bbox_data = block_data.get("bbox")
        if bbox_data:
            if isinstance(bbox_data, list) and len(bbox_data) == 4:
                return BoundingBox.from_list(bbox_data)
            elif isinstance(bbox_data, dict):
                return BoundingBox(
                    x1=bbox_data.get("x1", 0),
                    y1=bbox_data.get("y1", 0),
                    x2=bbox_data.get("x2", 0),
                    y2=bbox_data.get("y2", 0)
                )
        
        # 尝试单独的坐标字段
        if all(k in block_data for k in ["x1", "y1", "x2", "y2"]):
            return BoundingBox(
                x1=block_data["x1"],
                y1=block_data["y1"],
                x2=block_data["x2"],
                y2=block_data["y2"]
            )
        
        # 尝试spans中的bbox
        spans = block_data.get("spans", [])
        if spans and isinstance(spans, list) and len(spans) > 0:
            first_span = spans[0]
            if isinstance(first_span, dict):
                span_bbox = self._extract_bbox(first_span)
                if span_bbox:
                    return span_bbox
        
        return None

