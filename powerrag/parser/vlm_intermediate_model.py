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
中间JSON结构和数据模型，用于统一不同VLM解析器的输出格式
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod


class BlockType(str, Enum):
    """内容块类型枚举"""
    TEXT = "text"                    # 普通文本
    TITLE = "title"                  # 标题
    IMAGE = "image"                  # 图片
    TABLE = "table"                  # 表格
    FORMULA = "formula"              # 公式（行内）
    INTERLINE_EQUATION = "interline_equation"  # 行间公式
    CODE = "code"                    # 代码块
    LIST = "list"                    # 列表
    REF_TEXT = "ref_text"            # 参考文献
    PHONETIC = "phonetic"            # 拼音/音标
    PAGE_HEADER = "page_header"      # 页眉
    PAGE_FOOTER = "page_footer"      # 页脚
    CAPTION = "caption"              # 图/表标题
    FOOTNOTE = "footnote"            # 脚注
    SECTION_HEADER = "section_header"  # 章节标题


@dataclass
class BoundingBox:
    """边界框坐标"""
    x1: float  # 左上角x坐标
    y1: float  # 左上角y坐标
    x2: float  # 右下角x坐标
    y2: float  # 右下角y坐标
    
    def to_list(self) -> List[float]:
        """转换为列表格式 [x1, y1, x2, y2]"""
        return [self.x1, self.y1, self.x2, self.y2]
    
    @classmethod
    def from_list(cls, coords: List[float]) -> 'BoundingBox':
        """从列表格式创建"""
        if len(coords) != 4:
            raise ValueError(f"BoundingBox requires 4 coordinates, got {len(coords)}")
        return cls(x1=coords[0], y1=coords[1], x2=coords[2], y2=coords[3])


@dataclass
class ContentBlock:
    """内容块基类 - 统一的中间结构"""
    block_type: BlockType           # 块类型
    bbox: BoundingBox               # 边界框
    content: str                    # 内容文本
    index: int = 0                   # 在页面中的顺序索引
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.block_type.value,
            "bbox": self.bbox.to_list(),
            "content": self.content,
            "index": self.index,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentBlock':
        """从字典创建"""
        return cls(
            block_type=BlockType(data["type"]),
            bbox=BoundingBox.from_list(data["bbox"]),
            content=data["content"],
            index=data.get("index", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class ImageBlock(ContentBlock):
    """图片块"""
    image_url: Optional[str] = None      # 图片URL（如果已存储）
    image_base64: Optional[str] = None   # 图片base64（如果未存储）
    image_filename: Optional[str] = None  # 图片文件名
    
    def __post_init__(self):
        self.block_type = BlockType.IMAGE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "image_url": self.image_url,
            "image_base64": self.image_base64,
            "image_filename": self.image_filename
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageBlock':
        """从字典创建"""
        return cls(
            block_type=BlockType.IMAGE,
            bbox=BoundingBox.from_list(data["bbox"]),
            content=data.get("content", ""),
            index=data.get("index", 0),
            metadata=data.get("metadata", {}),
            image_url=data.get("image_url"),
            image_base64=data.get("image_base64"),
            image_filename=data.get("image_filename")
        )


@dataclass
class TableBlock(ContentBlock):
    """表格块"""
    table_html: Optional[str] = None     # HTML格式的表格
    table_markdown: Optional[str] = None # Markdown格式的表格
    
    def __post_init__(self):
        self.block_type = BlockType.TABLE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "table_html": self.table_html,
            "table_markdown": self.table_markdown
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableBlock':
        """从字典创建"""
        return cls(
            block_type=BlockType.TABLE,
            bbox=BoundingBox.from_list(data["bbox"]),
            content=data.get("content", ""),
            index=data.get("index", 0),
            metadata=data.get("metadata", {}),
            table_html=data.get("table_html"),
            table_markdown=data.get("table_markdown")
        )


@dataclass
class FormulaBlock(ContentBlock):
    """公式块"""
    latex: Optional[str] = None          # LaTeX格式
    is_inline: bool = False               # 是否为行内公式
    
    def __post_init__(self):
        self.block_type = BlockType.FORMULA if self.is_inline else BlockType.INTERLINE_EQUATION
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "latex": self.latex,
            "is_inline": self.is_inline
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormulaBlock':
        """从字典创建"""
        is_inline = data.get("is_inline", False)
        return cls(
            block_type=BlockType.FORMULA if is_inline else BlockType.INTERLINE_EQUATION,
            bbox=BoundingBox.from_list(data["bbox"]),
            content=data.get("content", ""),
            index=data.get("index", 0),
            metadata=data.get("metadata", {}),
            latex=data.get("latex"),
            is_inline=is_inline
        )


@dataclass
class PageInfo:
    """页面信息 - 统一的中间结构"""
    page_index: int                       # 页面索引（从0开始）
    page_size: List[int]                 # 页面尺寸 [width, height]
    blocks: List[ContentBlock] = field(default_factory=list)  # 内容块列表
    discarded_blocks: List[ContentBlock] = field(default_factory=list)  # 丢弃的块
    metadata: Dict[str, Any] = field(default_factory=dict)  # 页面元数据
    
    def to_dict(self, legacy_format: bool = False) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            legacy_format: 如果为True，使用旧格式 {"para_blocks": ..., "page_idx": ...}
                          如果为False，使用新格式 {"blocks": ..., "page_index": ...}
        """
        if legacy_format:
            # 旧格式：保持向后兼容
            return {
                "para_blocks": [block.to_dict() for block in self.blocks],
                "discarded_blocks": [block.to_dict() for block in self.discarded_blocks],
                "page_size": self.page_size,
                "page_idx": self.page_index
            }
        else:
            # 新格式
            return {
                "page_index": self.page_index,
                "page_size": self.page_size,
                "blocks": [block.to_dict() for block in self.blocks],
                "discarded_blocks": [block.to_dict() for block in self.discarded_blocks],
                "metadata": self.metadata
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PageInfo':
        """
        从字典创建
        
        支持两种格式：
        1. 新格式: {"blocks": [...], "page_index": ..., "page_size": ...}
        2. 旧格式: {"para_blocks": [...], "page_idx": ..., "page_size": ...}
        """
        # 检测格式类型
        if "para_blocks" in data:
            # 旧格式
            blocks_data = data.get("para_blocks", [])
            page_index = data.get("page_idx", 0)
        else:
            # 新格式
            blocks_data = data.get("blocks", [])
            page_index = data.get("page_index", 0)
        
        blocks = []
        for block_data in blocks_data:
            # 尝试解析块类型
            if isinstance(block_data, dict):
                block_type_str = block_data.get("type", "")
                try:
                    block_type = BlockType(block_type_str)
                except ValueError:
                    # 如果无法识别类型，尝试从其他字段推断
                    block_type = BlockType.TEXT
                
                if block_type == BlockType.IMAGE:
                    try:
                        blocks.append(ImageBlock.from_dict(block_data))
                    except Exception:
                        blocks.append(ContentBlock.from_dict(block_data))
                elif block_type == BlockType.TABLE:
                    try:
                        blocks.append(TableBlock.from_dict(block_data))
                    except Exception:
                        blocks.append(ContentBlock.from_dict(block_data))
                elif block_type in [BlockType.FORMULA, BlockType.INTERLINE_EQUATION]:
                    try:
                        blocks.append(FormulaBlock.from_dict(block_data))
                    except Exception:
                        blocks.append(ContentBlock.from_dict(block_data))
                else:
                    blocks.append(ContentBlock.from_dict(block_data))
        
        discarded_blocks = []
        for block_data in data.get("discarded_blocks", []):
            if isinstance(block_data, dict):
                discarded_blocks.append(ContentBlock.from_dict(block_data))
        
        return cls(
            page_index=page_index,
            page_size=data.get("page_size", [0, 0]),
            blocks=blocks,
            discarded_blocks=discarded_blocks,
            metadata=data.get("metadata", {})
        )


@dataclass
class IntermediateJSON:
    """中间JSON结构 - 整个文档的统一表示"""
    pages: List[PageInfo] = field(default_factory=list)  # 页面列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 文档元数据
    backend: str = "vlm"                 # 后端类型
    version: str = "1.0"                  # 版本号
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "pages": [page.to_dict() for page in self.pages],
            "metadata": self.metadata,
            "_backend": self.backend,
            "_version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntermediateJSON':
        """从字典创建"""
        pages = [PageInfo.from_dict(page_data) for page_data in data.get("pages", [])]
        return cls(
            pages=pages,
            metadata=data.get("metadata", {}),
            backend=data.get("_backend", "vlm"),
            version=data.get("_version", "1.0")
        )


class VLMResultConverter(ABC):
    """VLM解析结果转换器基类
    
    不同模型的解析器需要继承此类并实现convert_to_intermediate方法
    """
    
    @abstractmethod
    def convert_to_intermediate(
        self,
        model_output: Any,
        page_index: int,
        page_size: List[int],
        page_image: Any = None,
        **kwargs
    ) -> PageInfo:
        """
        将模型输出转换为中间结构
        
        Args:
            model_output: 模型原始输出（格式因模型而异）
            page_index: 页面索引
            page_size: 页面尺寸 [width, height]
            page_image: 页面图像（PIL Image或类似对象）
            **kwargs: 其他参数
            
        Returns:
            PageInfo: 转换后的页面信息
        """
        pass
    
    def convert_to_markdown(self, page_info: PageInfo, **kwargs) -> str:
        """
        将PageInfo转换为Markdown格式
        
        Args:
            page_info: 页面信息
            **kwargs: 其他参数（如output_dir用于图片存储）
            
        Returns:
            str: Markdown格式的文本
        """
        markdown_items = []
        
        # 按index排序
        sorted_blocks = sorted(page_info.blocks, key=lambda x: x.index)
        
        for block in sorted_blocks:
            if block.block_type == BlockType.IMAGE:
                markdown_items.append(self._image_to_markdown(block, **kwargs))
            elif block.block_type == BlockType.TABLE:
                markdown_items.append(self._table_to_markdown(block, **kwargs))
            elif block.block_type == BlockType.FORMULA:
                markdown_items.append(self._formula_to_markdown(block, inline=True))
            elif block.block_type == BlockType.INTERLINE_EQUATION:
                markdown_items.append(self._formula_to_markdown(block, inline=False))
            elif block.block_type == BlockType.TITLE:
                markdown_items.append(self._title_to_markdown(block))
            elif block.block_type == BlockType.CODE:
                markdown_items.append(self._code_to_markdown(block))
            else:
                markdown_items.append(block.content)
        
        return "\n\n".join(markdown_items)
    
    def _image_to_markdown(self, block: ImageBlock, **kwargs) -> str:
        """将图片块转换为Markdown"""
        if block.image_url:
            return f'<img src="{block.image_url}" alt="{block.content or ""}" style="max-width: 60%; height: auto;">'
        elif block.image_base64:
            return f"![{block.content or ''}]({block.image_base64})"
        else:
            return f"![{block.content or ''}]"
    
    def _table_to_markdown(self, block: TableBlock, **kwargs) -> str:
        """将表格块转换为Markdown"""
        if block.table_markdown:
            return block.table_markdown
        elif block.table_html:
            # 如果只有HTML，可以尝试转换或直接返回
            return block.table_html
        else:
            return block.content
    
    def _formula_to_markdown(self, block: FormulaBlock, inline: bool = False) -> str:
        """将公式块转换为Markdown"""
        latex = block.latex or block.content
        if inline:
            return f"${latex}$"
        else:
            return f"$$\n{latex}\n$$"
    
    def _title_to_markdown(self, block: ContentBlock) -> str:
        """将标题块转换为Markdown"""
        level = block.metadata.get("level", 1)
        prefix = "#" * min(level, 6)
        return f"{prefix} {block.content}"
    
    def _code_to_markdown(self, block: ContentBlock) -> str:
        """将代码块转换为Markdown"""
        language = block.metadata.get("language", "")
        return f"```{language}\n{block.content}\n```"

