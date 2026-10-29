''' 
    도로 데이터 활용 O
    도로 데이터 : 191 gdata.rd_11
    인도 데이터 : 191 gdata.wk_rd_11
'''
import geopandas as gpd
import math
from sqlalchemy import create_engine
from shapely.ops import unary_union
from shapely.geometry import MultiLineString, LineString
from psycopg2.pool import SimpleConnectionPool

class WalkRoad:
    def __init__(self):
        self.db_params = {
            'dbname': 'devdb',
            'host': '192.168.100.191',
            'port': '15432',
            'user': 'dawul',
            'password': 'dawul1234'
        }
        self.pool = SimpleConnectionPool(1, 10, **self.db_params)
        self.engine = create_engine(f"postgresql+psycopg2://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['dbname']}")

    def get_data(self, table_name):
        query = f"SELECT * FROM {table_name};"
        return gpd.read_postgis(query, self.engine, geom_col='geom')

    def action(self, rd_name, wk_name):
        # 1. 도로 데이터, 인도 데이터 가져오기
        rd_data = self.get_data(rd_name)
        wk_data = self.get_data(wk_name)
        
        sample_wk_data = wk_data.head(20)
        
        # 2. 인도 데이터가 속한 도로 데이터 찾기
        gggeom = []
        for idx, row in sample_wk_data.iterrows() :
            intersect_roads = rd_data[rd_data.intersects(row['geom'])]
            cutted_geom = self.cut_boundary_road_data(row['geom'], intersect_roads)
            gggeom.append(cutted_geom)
            
        new_f = gpd.GeoDataFrame(geometry=gggeom)
        new_f.to_file('test11__.shp')

    def cut_boundary_road_data(self, wk_road, roads) :
        road_boundary = unary_union(roads.geometry.boundary)
        bf_road_boundary = road_boundary.buffer(1)
        
        # 도로와 교차하는 인도 데이터 추출
        intersection = wk_road.intersection(bf_road_boundary)
        
        if isinstance(intersection, MultiLineString):
            # 여러개 추출됐을 경우
            line = self.extract_single_line(intersection)
            
        elif isinstance(intersection, LineString) :
            # 라인 하나 -> 각도 확 꺾이는 부분 제외하기
            line = self.trim_line_edges(intersection)

        return line
        
        
    def trim_line_edges(self, line) :
        # 라인 다듬기 -> 다시
        ln_coords_obj = line.coords
        ln_coords = [coord for coord in ln_coords_obj]
        print(f'coords : {ln_coords}')
        line = []
        
        for i in range(1, len(ln_coords)-1) :
            a_point = ln_coords[i-1]
            b_point = ln_coords[i]
            c_point = ln_coords[i+1]
            
            angle = self.calculate_angle(a_point, b_point, c_point)
            
            if angle > 90:
                if not line:  # 최초로 유효한 점이 포함될 때
                    line.append(a_point)
                line.append(b_point)
        
        if line and self.calculate_angle(ln_coords[-3], ln_coords[-2], ln_coords[-1]) > 90:
            line.append(ln_coords[-1])
        
        # print(f'single : {LineString(line)}')
        return LineString(line)
    
    def extract_single_line(self, line) :
        # 라인 추출하기(한개만)
        lines = [ln for ln in line.geoms]
        ln_length = [ln.length for ln in lines]
        
        line_length = {}
        for i in range(len(lines)) :
            line_length[lines[i]] = ln_length[i]
        
        max_line = max(line_length, key=line_length.get)
        
        # print(f'max_line : {max_line}')
        
        return max_line


    # 각도 계산
    def calculate_angle(self, a_point, b_point, c_point) :
        vector_ab = self.calculate_vector(a_point, b_point)
        vector_bc = self.calculate_vector(b_point, c_point)
        
        inner_prod = vector_ab[0] * vector_bc[0] + vector_ab[1] * vector_bc[1]
        
        mag_ab = math.sqrt(vector_ab[0]**2 + vector_ab[1]**2)
        mag_bc = math.sqrt(vector_bc[0]**2 + vector_bc[1]**2)
        
        cos = inner_prod / (mag_ab * mag_bc)
        cos = max(min(cos, 1), -1)
        
        angle_radians = math.acos(cos)
        angle_degrees = math.degrees(angle_radians)
        
        # 내각 계산
        if self.is_clockwise(a_point, b_point, c_point):
            return angle_degrees
        else:
            return 180 - angle_degrees
        
    # 두 점 사이의 백터 계산
    def calculate_vector(self, p1, p2) :
        return (p2[0] - p1[0], p2[1] - p1[1])
    
    def is_clockwise(self, a_point, b_point, c_point):
        return (b_point[0] - a_point[0]) * (c_point[1] - b_point[1]) - (b_point[1] - a_point[1]) * (c_point[0] - b_point[0]) > 0

    def __del__(self):
        self.pool.closeall()

if __name__ == '__main__':
    walkRoad = WalkRoad()
    road = input('도로 데이터(스키마.테이블) : ')
    wkroad = input('인도 데이터(스키마.테이블) : ')
    walkRoad.action(road, wkroad)
