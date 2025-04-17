import pandas as pd
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..database import SessionLocal, Shipment, ShipmentItem
from datetime import datetime
from .region_service import RegionService

# 创建地址解析服务实例
region_service = RegionService()

def extract_numbers(text: str) -> int:
    """从文本中提取数字"""
    if pd.isna(text):
        return 1
    numbers = re.findall(r'\d+', str(text))
    return int(numbers[0]) if numbers else 1

def parse_goods(goods_name: str) -> List[str]:
    """解析货物名称，返回所有货物类型"""
    if pd.isna(goods_name):
        return ['其他']
    
    goods_name = str(goods_name)
    # 分割复合货物（使用+号分割）
    goods_list = goods_name.split('+')
    
    # 处理每个货物
    result = []
    for good in goods_list:
        good = good.strip()
        # 检查是否包含特定货物类型
        if any(keyword in good for keyword in ['全电动', '电动']):
            result.append('全电动')
        elif '配重' in good:
            result.append('配重')
        elif '前移' in good:
            result.append('前移')
        elif '大金刚' in good:
            result.append('大金刚')
        elif '小金刚' in good:
            result.append('小金刚')
        elif '半电动' in good:
            result.append('半电动')
        else:
            # 保留原始货物名称，方便后续模糊匹配
            result.append(good)
    
    return result

async def process_excel(df: pd.DataFrame):
    """处理Excel数据并存入数据库"""
    session = SessionLocal()
    try:
        # 跳过前两行（第一行是合并单元格，第二行是表头）
        df = df.iloc[2:]

        # 处理每一行数据
        for _, row in df.iterrows():
            try:
                # 检查是否为空行
                if row.isna().all():
                    continue  # 跳过完全为空的行

                # 处理日期（使用'日期'列）
                shipping_date = row['日期']
                if pd.isna(shipping_date):
                    shipping_date = datetime.now().date()
                elif isinstance(shipping_date, str):
                    try:
                        shipping_date = datetime.strptime(shipping_date, "%Y-%m-%d").date()
                    except ValueError:
                        shipping_date = datetime.now().date()
                elif isinstance(shipping_date, datetime):
                    shipping_date = shipping_date.date()

                # 处理地址（使用'地址'列）
                raw_address = str(row['地址']).strip()
                if pd.isna(raw_address):
                    continue  # 跳过没有地址的行

                # 解析地址
                address_info = region_service.parse_address(raw_address)
                province = address_info['province']
                city = address_info['city']
                area = address_info['area']

                # 处理货物信息（使用'品名'列）
                goods_info = str(row['品名']).strip()
                if pd.isna(goods_info):
                    continue  # 跳过没有货物信息的行

                # 处理数量（使用'件数'列）
                quantity = row['件数']
                if pd.isna(quantity):
                    quantity = 1  # 默认数量为1
                else:
                    try:
                        # 处理 "1台" 这样的格式
                        if isinstance(quantity, str):
                            quantity = int(''.join(filter(str.isdigit, quantity)))
                        else:
                            quantity = int(float(quantity))
                    except (ValueError, TypeError):
                        quantity = 1

                # 处理价格（使用'价格'列）
                total_price = row['价格']
                if pd.isna(total_price):
                    print(f"警告：发现没有价格的行，跳过处理。行数据：{row.to_dict()}")
                    continue  # 跳过没有价格的行
                try:
                    total_price = float(total_price)
                except (ValueError, TypeError):
                    print(f"警告：价格格式不正确，跳过处理。行数据：{row.to_dict()}")
                    continue  # 跳过无法转换为价格的行

                # 解析货物
                goods_types = parse_goods(goods_info)
                if not goods_types:  # 如果没有识别出货物类型，使用原始货物名称
                    goods_types = [goods_info]

                # 创建发货记录
                shipment = Shipment(
                    shipping_date=shipping_date,
                    raw_address=raw_address,  # 保存原始地址
                    province=province,
                    city=city,
                    area=area,
                    total_price=total_price,
                    quantity=quantity,
                    unit="件",
                    raw_goods=goods_info,  # 使用原始货物名称
                )
                session.add(shipment)
                session.flush()

                # 为每个货物类型创建发货项目记录
                for goods_type in goods_types:
                    item = ShipmentItem(
                        shipment_id=shipment.id,
                        goods_type=goods_type,
                        quantity=quantity // len(goods_types),  # 平均分配数量
                    )
                    session.add(item)

            except Exception as e:
                print(f"处理行数据时出错: {str(e)}")
                print(f"问题行数据: {row.to_dict()}")
                continue  # 跳过出错的行，继续处理下一行

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        raise Exception(f"数据处理失败: {str(e)}")

    finally:
        session.close()

async def test_excel_processing(file_path: str) -> None:
    """测试Excel处理功能"""
    df = pd.read_excel(file_path)
    await process_excel(df) 