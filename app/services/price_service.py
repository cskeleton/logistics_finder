from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import SessionLocal, Shipment, ShipmentItem

def normalize_location(location: str) -> str:
    """标准化地址格式"""
    # 移除空格
    location = location.strip()
    # 移除常见的后缀
    suffixes = ['省', '市', '区', '县', '自治州', '地区']
    for suffix in suffixes:
        location = location.replace(suffix, '')
    return location

def normalize_goods_type(goods_type: str) -> str:
    """标准化货物类型"""
    if not goods_type:
        return ''
    
    # 移除空格
    goods_type = goods_type.strip()
    
    # 标准化货物类型
    if any(keyword in goods_type for keyword in ['全电动', '电动']):
        return '全电动'
    elif '配重' in goods_type:
        return '配重'
    elif '前移' in goods_type:
        return '前移'
    elif '大金刚' in goods_type:
        return '大金刚'
    elif '小金刚' in goods_type:
        return '小金刚'
    elif '半电动' in goods_type:
        return '半电动'
    
    return goods_type

async def search_prices(location: str, goods_type: str = None) -> Dict[str, Any]:
    """查询物流价格"""
    db = SessionLocal()
    try:
        # 标准化地址和货物类型
        normalized_location = normalize_location(location)
        normalized_goods_type = normalize_goods_type(goods_type)
        
        # 构建查询条件
        location_conditions = [
            or_(
                Shipment.province.like(f'%{normalized_location}%'),
                Shipment.city.like(f'%{normalized_location}%'),
                Shipment.area.like(f'%{normalized_location}%')
            )
        ]
        
        # 构建基础查询
        base_query = db.query(Shipment)
        if normalized_goods_type:
            base_query = base_query.join(ShipmentItem).filter(
                and_(
                    *location_conditions,
                    or_(
                        ShipmentItem.goods_type.like(f'%{normalized_goods_type}%'),
                        Shipment.raw_goods.like(f'%{normalized_goods_type}%')
                    )
                )
            ).distinct()
        else:
            base_query = base_query.filter(*location_conditions)
        
        # 获取总记录数
        total_count = base_query.count()
        
        # 获取最近10条记录
        shipments = base_query.order_by(Shipment.shipping_date.desc()).limit(10).all()
        
        # 处理结果
        items = []
        total_price = 0
        min_price = float('inf')
        max_price = 0
        
        for shipment in shipments:
            # 计算单价
            unit_price = shipment.total_price / shipment.quantity
            
            # 更新统计信息
            total_price += unit_price
            min_price = min(min_price, unit_price)
            max_price = max(max_price, unit_price)
            
            # 添加明细
            items.append({
                'goods': shipment.raw_goods,
                'quantity': f"{shipment.quantity}{shipment.unit}",
                'price': unit_price,
                'destination': shipment.raw_address
            })
        
        # 计算统计信息
        count = total_count  # 使用总记录数
        average_price = total_price / len(items) if items else 0  # 均价只基于显示的记录计算
        
        return {
            'stats': {
                'average': average_price,
                'min': min_price if min_price != float('inf') else 0,
                'max': max_price,
                'count': count
            },
            'items': items
        }
    finally:
        db.close() 