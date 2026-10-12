"""무전원 자동 배수 수조 계산기 (단위: cm, L, gf)
수조 안쪽 35x35x50cm, 아래 두 변을 R만큼 둥글게(트로프형), 배수구/마개는 평평한 바닥 구간에 둠.
python3 tank_calc.py  → 수위, 마개에 걸리는 수압, 플로트/자석 조건을 한 번에 출력
"""
import math

W = 35.0          # 안쪽 가로, 세로 (cm)
H = 50.0          # 안쪽 높이 (cm)
R = 10.0          # 바닥 둥글림 반지름 (cm); 8~10 권장
V_FULL = 50.0     # 열리는 물의 양 (L)
V_KEEP = 7.5      # 남기는 물의 양 (L) = 15%
PLUG_D = 5.0      # 마개 지름 (cm); 3.2 로 줄이면 필요한 힘이 줄어듦
RHO_G = 1.0       # 물 1 gf/cm^3 (높이 cm x 면적 cm^2 = gf)

# 두 자석 사이 간격(cm) → 당기는 힘(gf). 예시값이므로 실제 자석으로 재서 바꾸기
MAG_TABLE = [(0.3, 900), (0.5, 520), (0.8, 260), (1.0, 170), (1.5, 70), (2.0, 32), (3.0, 9), (4.0, 3)]
GAP_OPEN = 0.8    # 열렸을 때 간격 (멈춤 고리가 정함, 0이면 자석끼리 닿음)
GAP_CLOSED = 3.0  # 닫혔을 때 간격


def mag_force(gap):
    """MAG_TABLE 사이를 직선으로 이어 간격에 따른 자석 힘(gf)을 구함."""
    t = MAG_TABLE
    if gap <= t[0][0]:
        return t[0][1]
    for (g1, f1), (g2, f2) in zip(t, t[1:]):
        if gap <= g2:
            return f1 + (f2 - f1) * (gap - g1) / (g2 - g1)
    return t[-1][1]


def section_area(h, r=R, w=W):
    """높이 h까지 찬 물의 단면적 (cm^2). 한쪽 방향만 둥글고 반대쪽 두 변이 둥근 트로프형."""
    if h <= 0:
        return 0.0
    if h >= r:
        return w * h - 2 * (1 - math.pi / 4) * r * r
    # 둥근 모서리 구간: 원의 일부만큼 빠짐
    def corner_lost(hh):
        # 모서리 밖(비는 부분)의 면적, 높이 0~hh
        # 원 중심 (r, r), 바닥에서 높이 y 일 때 안쪽 경계 x(y) = r - sqrt(r^2-(r-y)^2)
        n = 400
        s = 0.0
        for i in range(n):
            y = (i + 0.5) * hh / n
            s += (r - math.sqrt(max(r * r - (r - y) ** 2, 0.0))) * (hh / n)
        return s
    return w * h - 2 * corner_lost(h)


def volume(h, depth=W):
    return section_area(h) * depth / 1000.0   # L


def level_for(liters):
    lo, hi = 0.0, H
    for _ in range(60):
        mid = (lo + hi) / 2
        if volume(mid) < liters:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def plug_force(h, d=PLUG_D):
    """마개를 들어 올릴 때 이겨야 하는 수압 (gf). 마개 윗면 면적 x 수심."""
    return RHO_G * h * math.pi * (d / 2) ** 2


def report():
    h50, h75 = level_for(V_FULL), level_for(V_KEEP)
    print(f"[수위] 50L = {h50:.1f} cm, 7.5L = {h75:.1f} cm (평평한 바닥이면 {V_FULL*1000/W/W:.1f} / {V_KEEP*1000/W/W:.1f} cm)")
    print(f"[수압] Ø{PLUG_D*10:.0f}mm 마개: 50L 수위에서 {plug_force(h50):.0f} gf "
          f"(Ø32mm 는 {plug_force(h50, 3.2):.0f} gf)")
    # 플로트가 위 턱을 밀 때: 더 차오른 높이 dh 당 추가 부력 = 물 닿는 단면적 x dh
    A_float = 400.0  # 플로트 수면 단면적 (cm^2) 예시
    print(f"[플로트] 수면 단면적 {A_float:.0f} cm^2 면 위 턱에 닿은 뒤 물이 1cm 오를 때마다 +{A_float:.0f} gf")
    # 자석 조건 (위 자석 고정 + 막대 꼭대기 자석, 비접촉):
    #   F(닫힘 간격) < W_조립 < F(열림 간격) < W_조립 + W_플로트
    W_asm, W_float = 150.0, 500.0   # 예시 무게(gf)
    f_open, f_closed = mag_force(GAP_OPEN), mag_force(GAP_CLOSED)
    print(f"[자석] 열림 간격 {GAP_OPEN:.1f} cm 에서 {f_open:.0f} gf, 닫힘 간격 {GAP_CLOSED:.1f} cm 에서 {f_closed:.0f} gf "
          f"(행정 {GAP_CLOSED-GAP_OPEN:.1f} cm)")
    checks = [
        ("닫혀 있을 때 거의 안 당김: F(닫힘) < 조립 무게", f_closed < W_asm),
        ("열린 채 붙잡음: F(열림) > 조립 무게", f_open > W_asm),
        ("플로트 무게로 닫힘: F(열림) < 조립 + 플로트", f_open < W_asm + W_float),
    ]
    for name, ok in checks:
        print(f"  {'OK ' if ok else '안 맞음'} {name}")
    print(f"[열림 조건] 부력 증가분이 (마개 수압 + 조립 무게 + F(닫힘) ) 보다 커야 열림: "
          f"마개 {plug_force(h50):.0f} gf 기준")


if __name__ == "__main__":
    report()
