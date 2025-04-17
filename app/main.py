from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from typing import List, Optional
import os
from io import BytesIO
from . import database
from .services import excel_service, price_service

# 初始化数据库
database.init_db()

app = FastAPI(title="物流价格查询系统")

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=STATIC_DIR)

# 存储待处理的DataFrame
pending_dfs = {}

@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """上传Excel文件并处理数据"""
    try:
        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持 .xlsx 或 .xls 格式的文件")
        
        # 读取Excel文件
        try:
            contents = await file.read()
            df = pd.read_excel(BytesIO(contents))
            print(f"Excel文件读取成功，列名: {df.columns.tolist()}")
        except Exception as e:
            print(f"Excel文件读取失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Excel文件读取失败: {str(e)}")
        finally:
            # 确保文件被关闭
            await file.close()
        
        # 检查必要的列是否存在
        required_columns = ['日期', '品名', '件数', '地址', '价格']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"缺少必要的列: {missing_columns}")
            print(f"实际的列: {df.columns.tolist()}")
            raise HTTPException(status_code=400, detail=f"Excel文件格式不正确，缺少以下列：{', '.join(missing_columns)}")
        
        # 生成一个唯一的任务ID
        task_id = str(len(pending_dfs))
        # 存储DataFrame
        pending_dfs[task_id] = df
        
        return {"message": "文件已接收，开始解析数据", "task_id": task_id}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"服务器错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@app.post("/parse/{task_id}")
async def parse_excel(task_id: str):
    """解析Excel数据"""
    try:
        if task_id not in pending_dfs:
            raise HTTPException(status_code=404, detail="未找到待处理的数据")
        
        df = pending_dfs[task_id]
        
        # 处理Excel数据
        try:
            await excel_service.process_excel(df)
            # 处理完成后删除数据
            del pending_dfs[task_id]
            return {"message": "数据添加成功"}
        except Exception as e:
            print(f"数据处理失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"数据处理失败: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"服务器错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@app.get("/search")
async def search(location: str, goods_type: Optional[str] = None):
    """查询物流价格"""
    try:
        return await price_service.search_prices(location, goods_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """返回主页"""
    return templates.TemplateResponse("index.html", {"request": request}) 