import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.vector_store import VectorStoreService


async def upload_file_to_knowledge(file_path: str):
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    if not file_path.is_file():
        print(f"❌ 不是有效文件: {file_path}")
        return False
    
    supported_extensions = {'.txt', '.pdf', '.md', '.docx', '.pptx'}
    ext = file_path.suffix.lower()
    
    if ext not in supported_extensions:
        print(f"❌ 不支持的文件格式: {ext}")
        print(f"   支持的格式: {', '.join(supported_extensions)}")
        return False
    
    print(f"📄 正在处理文件: {file_path.name}")
    
    vector_store = VectorStoreService()
    
    try:
        result = await vector_store.add_document(file_path)
        
        if result.get("success"):
            print(f"✅ 文件 {file_path.name} 已成功上传到知识库")
            chunks = result.get("chunks", 0)
            print(f"   切分为 {chunks} 个文档片段")
            return True
        else:
            print(f"❌ 文件上传失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 文件上传异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def upload_directory_to_knowledge(directory_path: str):
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        print(f"❌ 目录不存在: {directory_path}")
        return False
    
    if not directory_path.is_dir():
        print(f"❌ 不是有效目录: {directory_path}")
        return False
    
    supported_extensions = {'.txt', '.pdf', '.md', '.docx', '.pptx'}
    files_to_upload = []
    
    for file in directory_path.rglob('*'):
        if file.is_file() and file.suffix.lower() in supported_extensions:
            files_to_upload.append(file)
    
    if not files_to_upload:
        print(f"❌ 目录中没有找到支持的文件")
        return False
    
    print(f"📁 找到 {len(files_to_upload)} 个文件待上传:")
    for file in files_to_upload:
        print(f"   - {file.name}")
    
    success_count = 0
    fail_count = 0
    
    for file in files_to_upload:
        success = await upload_file_to_knowledge(str(file))
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n📊 上传完成:")
    print(f"   成功: {success_count} 个")
    print(f"   失败: {fail_count} 个")
    
    return success_count > 0


async def main():
    if len(sys.argv) < 2:
        print("""
用法: python upload_knowledge.py <文件路径或目录路径>

示例:
  # 上传单个文件
  python upload_knowledge.py ./docs/pet_guide.pdf
  
  # 上传整个目录
  python upload_knowledge.py ./docs/
  
注意:
  - 支持的文件格式: .txt, .pdf, .md, .docx, .pptx
  - 如果是目录，会自动递归扫描所有支持的文件
  - 文件会被切分后存储到向量数据库中
        """)
        return
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        await upload_file_to_knowledge(path)
    elif os.path.isdir(path):
        await upload_directory_to_knowledge(path)
    else:
        print(f"❌ 无效路径: {path}")


if __name__ == '__main__':
    asyncio.run(main())
