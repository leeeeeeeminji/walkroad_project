# 건물 데이터 사용 x
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, MultiPolygon
import math

class WalkRoad :
    def __init__(self) : 
        return 
    
    def get_shp_file(self) :
        path = 'C:/Users/Admin/Desktop/프로세스 고도화/인도 자르기/rd/src_11.shp'
        walks = gpd.read_file(path)
        
        return walks

    def action(self) :
        walks = self.get_shp_file()
        walks = walks.to_crs(epsg=5179)
        
        new_lines = []
        
        # 기존 데이터의 geometry를 변환하고 새로운 라인을 리스트에 저장
        for index, row in walks.iterrows():
            new_line = self.extract_road_side(row.geometry)
            new_lines.append(new_line)
        
        # 새로운 GeoDataFrame 생성
        new_gdf = gpd.GeoDataFrame(geometry=new_lines, crs=walks.crs)
        
        # 결과를 새로운 shapefile로 저장
        new_gdf.to_file('testtt.shp')
        
    def extract_road_side(self, geom):
        if isinstance(geom, (MultiLineString, MultiPolygon)):
            return
        
        coords = list(geom.coords)
        del coords[-1]
        
        angles = []
        for i in range(len(coords)) :
            a_point = coords[i-1]
            b_point = coords[i]
            c_point = coords[(i+1) % len(coords)]
            
            angle = self.calculate_angle(a_point, b_point, c_point)
            angles.append(angle)
            
        line1, line2 = self.split_lines_by_angle(coords, angles)
        len_line1 = line1.length
        len_line2 = line2.length
        
        if len_line1 < len_line2 :
            line = line1
        else :
            line = line2
        
        try:
            trimmed_geom = geom.difference(line)
        except NotImplementedError as e:
            print(f"Error: {e}")
            return geom 
        
        return trimmed_geom
        
    def split_lines_by_angle(self, coords, angles):
        line1 = []
        line2 = []
        current_line = line1
        cnt = 0
        
        for i in range(len(angles)):
            if i != 0 and angles[i] >= 30 and angles[i] <= 90 and cnt <= 2 :
                if current_line == line1:
                    current_line = line2
                else:
                    current_line = line1 
                
                line1.append(coords[i])
                line2.append(coords[i])
            
            else :
                current_line.append(coords[i])
                
            if i == len(coords) - 1 :
                current_line.append(coords[0])
                
        return LineString(line1), LineString(line2)
        
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
    
if __name__ == '__main__':
    walkRoad = WalkRoad()
    walkRoad.action()