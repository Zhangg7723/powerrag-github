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
VLLM解析器结果转换器
"""

from typing import List, Dict, Any, Optional
from PIL import Image
from .vlm_intermediate_model import (
    VLMResultConverter, PageInfo, ContentBlock, ImageBlock, TableBlock, 
    FormulaBlock, BlockType, BoundingBox
)


class DotsOcrResultConverter(VLMResultConverter):
    """VLLM解析器结果转换器
    
    将VLLM模型的输出格式转换为中间结构
    VLLM输出格式: [{"bbox": [x1, y1, x2, y2], "category": "...", "text": "..."}, ...]
    """
    
    # VLLM类别到BlockType的映射
    CATEGORY_MAPPING = {
        "Text": BlockType.TEXT,
        "Title": BlockType.TITLE,
        "Section-header": BlockType.SECTION_HEADER,
        "Picture": BlockType.IMAGE,
        "Table": BlockType.TABLE,
        "Formula": BlockType.FORMULA,
        "List-item": BlockType.LIST,
        "Page-header": BlockType.PAGE_HEADER,
        "Page-footer": BlockType.PAGE_FOOTER,
        "Caption": BlockType.CAPTION,
        "Footnote": BlockType.FOOTNOTE,
    }
    
    def convert_to_intermediate(
        self,
        model_output: List[Dict[str, Any]],
        page_index: int,
        page_size: List[int],
        page_image: Optional[Image.Image] = None,
        **kwargs
    ) -> PageInfo:
        """
        将VLLM模型输出转换为中间结构
        
        Args:
            model_output: VLLM模型输出，格式为 [{"bbox": [...], "category": "...", "text": "..."}, ...]
            page_index: 页面索引
            page_size: 页面尺寸 [width, height]
            page_image: 页面图像（PIL Image）
            **kwargs: 其他参数
                - text_key: 文本字段的键名（默认"text"）
                - output_dir: 输出目录（用于图片存储）
                - skip_page_header_footer: 是否跳过页眉页脚
            
        Returns:
            PageInfo: 转换后的页面信息
        """
        text_key = kwargs.get("text_key", "text")
        skip_page_header_footer = kwargs.get("skip_page_header_footer", False)
        
        blocks = []
        discarded_blocks = []
        
        for idx, cell in enumerate(model_output):
            category = cell.get("category", "Text")
            
            # 跳过页眉页脚（如果配置）
            if skip_page_header_footer and category in ["Page-header", "Page-footer"]:
                continue
            
            # 获取边界框
            bbox_coords = cell.get("bbox", [0, 0, 0, 0])
            if len(bbox_coords) != 4:
                continue
            
            bbox = BoundingBox.from_list(bbox_coords)
            text = cell.get(text_key, "")
            
            # 根据类别创建对应的块
            block_type = self.CATEGORY_MAPPING.get(category, BlockType.TEXT)
            
            if block_type == BlockType.IMAGE:
                # 图片块
                block = ImageBlock(
                    block_type=BlockType.IMAGE,
                    bbox=bbox,
                    content=text,
                    index=idx,
                    metadata={"category": category}
                )
                # 如果提供了页面图像，可以在这里裁剪并存储
                if page_image:
                    self._process_image_block(block, page_image, page_index, idx, **kwargs)
            elif block_type == BlockType.TABLE:
                # 表格块
                block = TableBlock(
                    block_type=BlockType.TABLE,
                    bbox=bbox,
                    content=text,
                    index=idx,
                    table_html=text if category == "Table" else None,
                    metadata={"category": category}
                )
            elif block_type == BlockType.FORMULA:
                # 公式块
                block = FormulaBlock(
                    block_type=BlockType.FORMULA,
                    bbox=bbox,
                    content=text,
                    index=idx,
                    latex=text,
                    is_inline=False,
                    metadata={"category": category}
                )
            else:
                # 其他类型的块
                block = ContentBlock(
                    block_type=block_type,
                    bbox=bbox,
                    content=text,
                    index=idx,
                    metadata={"category": category}
                )
            
            blocks.append(block)
        
        return PageInfo(
            page_index=page_index,
            page_size=page_size,
            blocks=blocks,
            discarded_blocks=discarded_blocks,
            metadata={"source": "vllm"}
        )
    
    def _process_image_block(
        self,
        block: ImageBlock,
        page_image: Image.Image,
        page_index: int,
        block_index: int,
        **kwargs
    ):
        """处理图片块，裁剪并存储图片"""
        output_dir = kwargs.get("output_dir")
        if not output_dir:
            return
        
        try:
            from io import BytesIO
            import base64
            from rag.utils.storage_factory import STORAGE_IMPL
            from api.utils.configs import get_base_config
            import os
            
            # 裁剪图片
            x1, y1, x2, y2 = int(block.bbox.x1), int(block.bbox.y1), int(block.bbox.x2), int(block.bbox.y2)
            image_crop = page_image.crop((x1, y1, x2, y2))
            
            # 生成文件名
            img_filename = f"page_{page_index}_img_{block_index}.png"
            
            # 转换为字节
            buffered = BytesIO()
            image_crop.save(buffered, format='PNG')
            img_bytes = buffered.getvalue()
            
            # 存储图片
            STORAGE_IMPL.put(output_dir, img_filename, img_bytes)
            
            # 生成URL
            api_url = os.environ.get("PUBLIC_SERVER_URL", "http://localhost:6000")
            if not api_url.startswith("http://") and not api_url.startswith("https://"):
                api_url = f"http://{api_url}"
            
            image_url = f"{api_url}/api/v1/powerrag/chunk/image/{output_dir}/{img_filename}"
            
            # 更新块信息
            block.image_url = image_url
            block.image_filename = img_filename
            
        except Exception as e:
            import logging
            logging.error(f"Failed to process image block: {str(e)}")

