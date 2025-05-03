"""RegionService 模块：提供行政区划相关服务。"""
import sqlite3
import os
from typing import Dict, Optional, Tuple

class RegionService:
    """行政区划服务类。"""
    def __init__(self):
        # 获取当前文件所在目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 行政区划数据库路径
        self.db_path = os.path.join(base_dir, "data", "china.db")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # 初始化缓存
        self._init_cache()

    def _init_cache(self):
        """初始化缓存，加载所有省份和直辖市"""
        # 加载所有省份
        self.cursor.execute("SELECT code, name FROM province")
        self.provinces = {row['name']: row['code'] for row in self.cursor.fetchall()}

        # 加载所有直辖市（假设直辖市在province表中）
        self.municipalities = {}
        for name, code in self.provinces.items():
            if name in ['北京市', '上海市', '天津市', '重庆市']:
                self.municipalities[name] = code

        # 加载江苏省的城市（包括地级市和县级市）
        self.cursor.execute("""
            SELECT c.code, c.name 
            FROM city c
            JOIN province p ON c.provinceCode = p.code
            WHERE p.name = '江苏省'
        """)
        self.jiangsu_cities = {row['name']: row['code'] for row in self.cursor.fetchall()}

        # 加载江苏省的县级市
        self.cursor.execute("""
            SELECT a.code, a.name 
            FROM area a
            JOIN city c ON a.cityCode = c.code
            JOIN province p ON c.provinceCode = p.code
            WHERE p.name = '江苏省' AND a.name LIKE '%市'
        """)
        self.jiangsu_county_cities = {row['name']: row['code'] for row in self.cursor.fetchall()}

    def find_province(self, address: str) -> Optional[Tuple[str, str]]:
        """查找省份或直辖市
        
        Args:
            address: 地址字符串
            
        Returns:
            如果找到，返回 (省份名称, 省份代码)，否则返回 None
        """
        # 检查前两个字是否匹配省份
        if len(address) >= 2:
            prefix = address[:2]
            for province_name, province_code in self.provinces.items():
                if province_name.startswith(prefix):
                    return (province_name, province_code)

        # 检查是否匹配直辖市
        for city_name, city_code in self.municipalities.items():
            if address.startswith(city_name):
                return (city_name, city_code)

        # 检查是否是江苏省的城市（地级市）
        if len(address) >= 2:
            prefix = address[:2]
            for city_name, city_code in self.jiangsu_cities.items():
                if city_name.startswith(prefix):
                    return ("江苏省", self.provinces["江苏省"])

        # 检查是否是江苏省的县级市
        if len(address) >= 2:
            prefix = address[:2]
            for city_name, city_code in self.jiangsu_county_cities.items():
                if city_name.startswith(prefix):
                    return ("江苏省", self.provinces["江苏省"])

        return None

    def find_city(self, address: str, province_code: str) -> Optional[Tuple[str, str]]:
        """查找城市
        
        Args:
            address: 地址字符串
            province_code: 省份代码
            
        Returns:
            如果找到，返回 (城市名称, 城市代码)，否则返回 None
        """
        # 获取该省份下的所有城市
        self.cursor.execute("""
            SELECT code, name FROM city 
            WHERE provinceCode = ?
        """, (province_code,))
        cities = {row['name']: row['code'] for row in self.cursor.fetchall()}
        
        # 检查地址中是否包含城市名
        for city_name, city_code in cities.items():
            if city_name in address:
                return (city_name, city_code)
        
        return None
    
    def find_district(self, address: str, city_code: str) -> Optional[Tuple[str, str]]:
        """查找区县
        
        Args:
            address: 地址字符串
            city_code: 城市代码
            
        Returns:
            如果找到，返回 (区县名称, 区县代码)，否则返回 None
        """
        # 获取该城市下的所有区县
        self.cursor.execute("""
            SELECT code, name FROM area 
            WHERE cityCode = ?
        """, (city_code,))
        districts = {row['name']: row['code'] for row in self.cursor.fetchall()}
        
        # 检查地址中是否包含区县名
        for district_name, district_code in districts.items():
            if district_name in address:
                return (district_name, district_code)
        
        return None
    
    def parse_address(self, address: str) -> Dict[str, str]:
        """解析地址，返回省市区信息
        
        Args:
            address: 地址字符串
            
        Returns:
            包含 province, city, area 的字典
        """
        result = {
            'province': '',
            'city': '',
            'area': ''
        }
        
        # 查找省份
        province_info = self.find_province(address)
        if province_info:
            province_name, province_code = province_info
            result['province'] = province_name
            
            # 如果是直辖市，特殊处理
            if province_name in ['北京市', '上海市', '天津市', '重庆市']:
                # 获取该直辖市下的所有区
                self.cursor.execute("""
                    SELECT code, name FROM area 
                    WHERE provinceCode = ?
                """, (province_code,))
                districts = {row['name']: row['code'] for row in self.cursor.fetchall()}
                
                # 检查地址中是否包含区名（考虑带后缀和不带后缀的情况）
                for district_name, district_code in districts.items():
                    # 去掉后缀后的名称
                    base_name = district_name.rstrip('区县')
                    if district_name in address or base_name in address:
                        result['city'] = district_name
                        break
            # 如果是江苏省，使用特殊逻辑
            elif province_name == "江苏省":
                # 先检查是否是地级市
                city_found = False
                if len(address) >= 2:
                    prefix = address[:2]
                    for city_name, city_code in self.jiangsu_cities.items():
                        # 去掉后缀后的名称
                        base_name = city_name.rstrip('市')
                        if city_name.startswith(prefix) or base_name.startswith(prefix):
                            result['city'] = city_name
                            city_found = True
                            break

                # 如果不是地级市，检查是否是县级市
                if not city_found and len(address) >= 2:
                    prefix = address[:2]
                    for city_name, city_code in self.jiangsu_county_cities.items():
                        # 去掉后缀后的名称
                        base_name = city_name.rstrip('市')
                        if city_name.startswith(prefix) or base_name.startswith(prefix):
                            result['city'] = city_name
                            city_found = True
                            break

                # 如果找到了城市，查找区县
                if city_found:
                    # 获取城市代码
                    city_code = None
                    for name, code in self.jiangsu_cities.items():
                        if name == result['city']:
                            city_code = code
                            break

                    if not city_code:
                        for name, code in self.jiangsu_county_cities.items():
                            if name == result['city']:
                                city_code = code
                                break

                    if city_code:
                        # 查找区县
                        area_info = self.find_area(address, city_code)
                        if area_info:
                            area_name, _ = area_info
                            result['area'] = area_name
            # 对于其他省份
            else:
                # 获取该省份下的所有城市（地级市）
                self.cursor.execute("""
                    SELECT code, name FROM city 
                    WHERE provinceCode = ?
                """, (province_code,))
                cities = {row['name']: row['code'] for row in self.cursor.fetchall()}

                # 获取该省份下的所有区县
                self.cursor.execute("""
                    SELECT a.code, a.name, a.cityCode 
                    FROM area a
                    JOIN city c ON a.cityCode = c.code
                    WHERE c.provinceCode = ?
                """, (province_code,))
                areas = {row['name']: (row['code'], row['cityCode']) for row in self.cursor.fetchall()}

                # 先尝试匹配地级市
                city_found = False
                for city_name, city_code in cities.items():
                    # 去掉后缀后的名称
                    base_name = city_name.rstrip('市')
                    if city_name in address or base_name in address:
                        result['city'] = city_name
                        city_found = True
                        # 查找该地级市下的区县
                        area_info = self.find_area(address, city_code)
                        if area_info:
                            area_name, _ = area_info
                            result['area'] = area_name
                        break

                # 如果没有找到地级市，检查是否是县级市
                if not city_found:
                    for area_name, (area_code, city_code) in areas.items():
                        # 去掉后缀后的名称
                        base_name = area_name.rstrip('市')
                        if (area_name.endswith('市') and (area_name in address or base_name in address)):
                            # 获取该县级市所属的地级市
                            self.cursor.execute("""
                                SELECT name FROM city WHERE code = ?
                            """, (city_code,))
                            city_row = self.cursor.fetchone()
                            if city_row:
                                result['city'] = city_row['name']
                                result['area'] = area_name
                            break

        return result

    def find_area(self, address: str, city_code: str) -> Optional[Tuple[str, str]]:
        """查找区县
        
        Args:
            address: 地址字符串
            city_code: 城市代码
            
        Returns:
            如果找到，返回 (区县名称, 区县代码)，否则返回 None
        """
        # 获取该城市下的所有区县
        self.cursor.execute("""
            SELECT code, name FROM area 
            WHERE cityCode = ?
        """, (city_code,))
        areas = {row['name']: row['code'] for row in self.cursor.fetchall()}

        # 检查地址中是否包含区县名
        for area_name, area_code in areas.items():
            if area_name in address:
                return (area_name, area_code)

        return None

    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close() 