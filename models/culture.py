# models/culture.py
from enum import Enum

# 학년 정의
class YearEnum(Enum):
    FRESHMAN = 1
    SOPHOMORE = 2
    JUNIOR = 3
    SENIOR = 4

# 성적 등급 정의
class GradeValue(Enum):
    APLUS = "A+"
    A = "A0"
    BPLUS = "B+"
    B = "B0"
    CPLUS = "C+"
    C = "C0"
    DPLUS = "D+"
    D = "D0"
    F = "F"
    P = "P"
    NP = "NP"

    def get_points(self) -> float:
        grade_map = {
            self.APLUS: 4.5, self.A: 4.0,
            self.BPLUS: 3.5, self.B: 3.0,
            self.CPLUS: 2.5, self.C: 2.0,
            self.DPLUS: 1.5, self.D: 1.0,
            self.F: 0.0,
            self.P: 0.0,
            self.NP: 0.0
        }
        return grade_map.get(self, 0.0)