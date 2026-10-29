import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import LineString
from shapely.ops import unary_union
import os
import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np

os.environ["SHAPE_RESTORE_SHX"] = "YES"

class WalkRoad:
    def __init__(self) -> None:
        self.cd = '11'
        self.cnt1 = 0
        self.cnt2 = 0
        self.cnt3 = 0
        self.srcfile = f'C:\\Users\\Admin\\Desktop\\프로세스 고도화\\인도 자르기\\rd\\src_{self.cd}.shp'
        self.retfile = f'C:\\Users\\Admin\\Desktop\\프로세스 고도화\\인도 자르기\\result_{self.cd}_len1.shp'
        self.errfile = f'C:\\Users\\Admin\\Desktop\\프로세스 고도화\\인도 자르기\\err_{self.cd}_len1.shp'
        self.rdfile = f'C:\\Users\\Admin\\Desktop\\프로세스 고도화\\인도 자르기\\road_{self.cd}.shp'

    def step1(self):
        gdf: GeoDataFrame = gpd.read_file(self.srcfile)
        self.rd_gdf: GeoDataFrame = gpd.read_file(self.rdfile)
        gdf = gdf.set_crs(epsg=5186, allow_override=True)
        gdf = gdf.to_crs(epsg=5179)
        new_lines = []
        err_lines = []
        
        cnt =0
        for line in gdf.geometry:       
            if isinstance(line, LineString):
                segments = self.split_line_at_sharp_angles(line)
                
                if segments :
                    ret = self.check_result(segments, line)
                    if ret is None:
                        err_lines.append(self.merge_linestrings(segments))
                        continue
                    
                    new_lines.extend(ret)
            
                if cnt %10 ==0:
                    print('-')
                
                cnt +=1

        # 새로운 GeoDataFrame 생성
        new_gdf = gpd.GeoDataFrame(geometry=new_lines, crs=gdf.crs)
        err_gdf = gpd.GeoDataFrame(geometry=err_lines, crs=gdf.crs)

        # 처리된 결과를 SHP 파일로 저장
        new_gdf.to_file(self.retfile)
        err_gdf.to_file(self.errfile)
    
    # 도로 boundary와 떨어진 거리에 따라 판단
    def check_result(self, segments, wk_line) :
        if len(segments) == 2:
            l1, l2 = segments
            
            intersect_roads = self.rd_gdf[self.rd_gdf['geometry'].intersects(wk_line)]
            union_road = unary_union(intersect_roads.geometry)
            road_boundary = union_road.boundary
            
            mid_point_l1 = Point(l1.interpolate(0.5, normalized=True))
            mid_point_l2 = Point(l2.interpolate(0.5, normalized=True))
            
            distance_l1 = mid_point_l1.distance(road_boundary)
            distance_l2 = mid_point_l2.distance(road_boundary)
            
            if distance_l1 > distance_l2 : 
                return [l1]
            else :
                return [l2]
        
        return None


    # 두 벡터 사이의 각도 계산
    def angle_between_vectors(self, v1, v2):
        dot_product = np.dot(v1, v2)
        norms = np.linalg.norm(v1) * np.linalg.norm(v2)
        cos_theta = dot_product / norms
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        angle = np.arccos(cos_theta)
        return np.degrees(angle)

    # 라인의 버텍스가 갖는 각도 전부 가져오기
    def get_vertex_angles(self, line_coords) :
        sharp_angles = []
        all_angles = []

        for i in range(1, len(line_coords) - 1):
            angle = self.calculate_angle(line_coords[i - 1], line_coords[i], line_coords[i + 1])
            all_angles.append(angle)
            if angle <= 95:
                sharp_angles.append(i)

        # 첫 번째 좌표의 각도도 포함
        first_coord_angle = self.calculate_angle(line_coords[-2], line_coords[-1], line_coords[1])
        all_angles.append(first_coord_angle)
        if first_coord_angle <= 95 :
            sharp_angles.append(0)
            
        return sharp_angles, all_angles
        
    # 각이 90도 이하인 지점 기준으로 라인 분리 --> 95도로 수정
    def split_line_at_sharp_angles(self, line):
        # line의 coords 값 가져오기
        if isinstance(line, LineString):
            line_coords = list(line.coords)
        else:
            line_coords = line
        
        if line_coords[0] != line_coords[-1]:
            line_coords.append(line_coords[0])

        # 버텍스의 모든 각도값 가져오기
        sharp_angles, all_angles = self.get_vertex_angles(line_coords)
        sharp_angles.sort()
        if not sharp_angles:
            return [LineString(line_coords)]
        
        segments = []
        # 각도가 95도 이하인 버텍스가 두 개일 경우
        if len(sharp_angles) == 1 :
            temp_idx = sharp_angles[0] - 1
            all_angles[temp_idx] = 999.99999
            min_val = min(all_angles)
            idx = all_angles.index(min_val) + 1
            sharp_angles.append(idx)
            sharp_angles.sort()
            
            start_idx, end_idx = sharp_angles
            ln1 = LineString(line_coords[start_idx:end_idx + 1])
            ln2 = LineString(line_coords[end_idx:] + line_coords[:start_idx + 1])
            segments.append(ln1)
            segments.append(ln2)
            return None
            
        elif len(sharp_angles) == 2:
            start_idx, end_idx = sharp_angles
            ln1 = LineString(line_coords[start_idx:end_idx + 1])
            ln2 = LineString(line_coords[end_idx:] + line_coords[:start_idx + 1])
            segments.append(ln1)
            segments.append(ln2)
            return None
        
        elif len(sharp_angles) >= 3:
            start_idx, end_idx = sharp_angles[0], sharp_angles[-1]
            ln1 = LineString(line_coords[start_idx:end_idx + 1])
            ln2 = LineString(line_coords[end_idx:] + line_coords[:start_idx + 1])
            segments.append(ln1)
            segments.append(ln2)
            return None
            
        else:
            return [LineString(line_coords)]
        

    # 세 점 사이의 각도 계산
    def calculate_angle(self, pointA, pointB, pointC):
        # 벡터 BA, BC 계산
        BA = np.array(pointA) - np.array(pointB)
        BC = np.array(pointC) - np.array(pointB)
        
        # 벡터 간의 내적 계산
        dot_product = np.dot(BA, BC)
        
        if dot_product  == 0:
            return 180
        
        # 벡터의 크기 계산
        norm_BA = np.linalg.norm(BA)
        norm_BC = np.linalg.norm(BC)
        
        # 각도 계산 (라디안)
        cos_theta = dot_product / (norm_BA * norm_BC)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)  # 오차 방지를 위해 값 클리핑
        angle_radians = np.arccos(cos_theta)
        
        # 라디안을 도(degree)로 변환
        angle_degrees = np.degrees(angle_radians)
        
        return angle_degrees

    # 라인 객체 병합
    def merge_linestrings(self, line_strings):
        if not line_strings:
            return None  # 빈 리스트 처리

        merged_coords = []

        for line in line_strings:
            merged_coords.extend(list(line.coords))  # 모든 좌표를 추가

        return LineString(merged_coords)
        
        
if __name__== '__main__':
    wk = WalkRoad()
    wk.step1()