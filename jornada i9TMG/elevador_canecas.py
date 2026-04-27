"""
Cálculo de Elevador de Canecas — Mistura 90
Baseado na planilha 110-EL-001

Uso:
    python elevador_canecas.py
    python elevador_canecas.py --V 11.99 --H 10 --v 5.0 --gamma 1.11
"""

import math
import argparse
from dataclasses import dataclass, field


@dataclass
class EntradaElevador:
    # Caneca
    V: float = 11.99       # Volume da caneca a 75% (L)
    n: int = 1             # Número de fileiras de canecas
    e: float = 310.0       # Passo das canecas (mm)
    p: float = 16.13556    # Peso de uma caneca (kg)

    # Geometria
    H: float = 10.0        # Altura centro a centro (m)
    D: float = 0.62        # Diâmetro do tambor motriz (m)

    # Material
    gamma: float = 1.11    # Peso específico (t/m³)
    CF1: float = 0.754     # Coeficiente de enchimento (adm)
    CF2: float = 1.0       # Coeficiente de homogeneidade (adm)

    # Correia
    Tu: float = 33.0       # Tensão admissível por lona (kgf/cm·lona)
    B: float = 55.88       # Largura da correia (cm)
    pc: float = 11.5939824 # Peso da correia (kg/m)
    k: float = 0.85        # Fator de acionamento (esticador manual emborrachado)
    mu: float = 0.35       # Coeficiente de atrito (tambor emborrachado)
    phi: float = 180.0     # Ângulo de abraçamento (graus)

    # Motor / redutor
    eta: float = 0.95      # Rendimento do grupo motor
    Rm: float = 1750.0     # Rotação do motor (rpm)

    # Eixos
    sigma_adm: float = 560.0  # Tensão admissível aço SAE 1045 com chaveta (kgf/cm²)
    Fsf: float = 1.5          # Fator de segurança fletor
    Fst: float = 2.0          # Fator de segurança torsor
    Pt: float = 120.0         # Peso do tambor motriz (kgf)
    a2: float = 16.0          # Dist. centro mancal ao disco lateral (cm)

    # Rolamentos
    L10h: float = 50000.0  # Vida nominal (horas)


@dataclass
class ResultadoElevador:
    # Capacidade
    Q_m3h: float = 0.0
    Q_th: float = 0.0
    V_100: float = 0.0    # Volume caneca a 100% (L)
    p1: float = 0.0       # Peso material na caneca a 100% (kg)

    # Geometria correia
    Ca: float = 0.0       # Comprimento correia aberta (m)
    N1: float = 0.0       # Número de canecas
    Pm: float = 0.0       # Peso por metro de material (kg/m)

    # Tensões
    Tp: float = 0.0       # Tensão estática (kgf)
    Te_a: float = 0.0     # Tensão efetiva fórmula (a)
    Te_b: float = 0.0     # Tensão efetiva fórmula (b)
    Te: float = 0.0       # Tensão efetiva adotada (maior)
    Tm: float = 0.0       # Tensão máxima (kgf)
    K_abraç: float = 0.0  # Fator de abraçamento
    Pe: float = 0.0       # Peso do esticador por gravidade (kgf)

    # Seleção correia
    Ut: float = 0.0       # Unidade de tensão (kgf/cm)
    Nm: float = 0.0       # Lonas mínimas
    NL: int = 0           # Lonas selecionadas
    pct_Tad: float = 0.0  # % da tensão admissível

    # Eixo motriz
    Mf_motriz: float = 0.0
    Mt_motriz: float = 0.0
    Mi_motriz: float = 0.0
    d_motriz_calc: float = 0.0   # mm

    # Eixo movido (retorno)
    Mf_movido: float = 0.0
    d_movido_calc: float = 0.0   # mm

    # Potência
    N_cv: float = 0.0
    N_kw: float = 0.0

    # Redução
    rs: float = 0.0
    R: float = 0.0

    # Acoplamento alta
    Meq_alta: float = 0.0

    # Rolamentos
    C_motriz_N: float = 0.0
    C_movido_N: float = 0.0


def calcular(e: EntradaElevador) -> ResultadoElevador:
    r = ResultadoElevador()
    PI = math.pi

    # ── 1. CAPACIDADE ────────────────────────────────────────────────────────
    r.Q_m3h = 3600 * e.V * e.n * e.v_correia * e.CF1 * e.CF2 / e.e
    r.Q_th  = r.Q_m3h * e.gamma
    r.V_100 = e.V / 0.75
    r.p1    = r.V_100 * e.gamma  # kg, pois V em L e γ em t/m³ → ×1000/1000 = 1

    # ── 2. PESO POR METRO ────────────────────────────────────────────────────
    r.Pm = 1000 * e.n * e.gamma * r.V_100 / e.e

    # ── 3. COMPRIMENTO E NÚMERO DE CANECAS ───────────────────────────────────
    r.Ca = PI * e.D + 2 * e.H
    r.N1 = 1000 * r.Ca * e.n / e.e

    # ── 4. TENSÕES ───────────────────────────────────────────────────────────
    r.Tp = (e.p * r.N1 / 2.0) + (e.pc * r.Ca / 4.0) + (r.p1 * r.N1 / 2.0)

    # Te(a) — em função da carga
    r.Te_a = (e.H + 12 * e.D ** 2) * r.p1 * 1000 / e.e

    # Te(b) — em função do número de canecas (centrífugo Ho = 7 m)
    Ho = 7.0
    r.Te_b = 0.8 * r.p1 * r.N1 * (e.H + Ho) / e.H

    r.Te = max(r.Te_a, r.Te_b)

    # Tensão máxima
    r.Tm = (1 + e.k) * r.Te

    # Fator de abraçamento
    exp_val = math.exp(0.0174 * e.phi * e.mu)
    r.K_abraç = 1 / (exp_val - 1)

    # Esticador por gravidade
    r.Pe = r.K_abraç * r.Te

    # ── 5. SELEÇÃO DA CORREIA ────────────────────────────────────────────────
    r.Ut     = r.Tm / e.B
    r.Nm     = r.Ut / e.Tu
    r.NL     = max(4, math.ceil(r.Nm))
    r.pct_Tad = (r.Tm / (e.Tu * e.B * r.NL)) * 100

    # ── 6. EIXO MOTRIZ ───────────────────────────────────────────────────────
    P_mot = r.Tm + e.Pt
    r.Mf_motriz = P_mot * e.a2 / 2.0                              # kgf·cm
    r.Mt_motriz = r.N_cv * 38 * (e.D * 100) / e.v_correia if False else 0  # calculado após
    # Provisório: potência antecipada para calcular Mt
    N_cv_prev = e.v_correia * r.Pm * e.n * (e.H + 7 * e.D) / (75 * e.eta)
    r.Mt_motriz = N_cv_prev * 38 * (e.D * 100) / e.v_correia
    r.Mi_motriz = math.sqrt((e.Fsf * r.Mf_motriz) ** 2 + (e.Fst * r.Mt_motriz) ** 2)
    r.d_motriz_calc = ((16 * r.Mi_motriz / (PI * e.sigma_adm)) ** (1/3)) * 10  # mm

    # ── 7. EIXO MOVIDO ───────────────────────────────────────────────────────
    P_mov = r.Tp / 2
    r.Mf_movido = P_mov * e.a2 / 2.0
    r.d_movido_calc = ((32 * r.Mf_movido * e.Fsf / (PI * e.sigma_adm)) ** (1/3)) * 10  # mm

    # ── 8. POTÊNCIA ──────────────────────────────────────────────────────────
    r.N_cv = N_cv_prev
    r.N_kw = r.N_cv * 0.7355

    # ── 9. REDUÇÃO ───────────────────────────────────────────────────────────
    r.rs = e.v_correia * 60 / (e.D * PI)
    r.R  = e.Rm / r.rs

    # ── 10. ACOPLAMENTO DE ALTA ──────────────────────────────────────────────
    N_sel = math.ceil(r.N_cv / 2.5) * 2.5
    r.Meq_alta = 7030 * N_sel * 1.5 / e.Rm

    # ── 11. ROLAMENTOS ───────────────────────────────────────────────────────
    P_rol_mot = (r.Tm + e.Pt) / 2 * 9.81  # N
    P_rol_mov = r.Pe / 2 * 9.81            # N
    r.C_motriz_N = P_rol_mot * ((60 * r.rs * e.L10h) / 1e6) ** (1/3)
    r.C_movido_N = P_rol_mov * ((60 * r.rs * e.L10h) / 1e6) ** (1/3)

    return r


# ── PATCH: adicionar v_correia ao dataclass ────────────────────────────────
EntradaElevador.__annotations__['v_correia'] = float
EntradaElevador.__dataclass_fields__['v_correia'] = field(default=5.0)
EntradaElevador.v_correia = 5.0


def imprimir_relatorio(e: EntradaElevador, r: ResultadoElevador):
    sep  = "─" * 68
    sep2 = "═" * 68

    def linha(nome, valor, unidade="", comentario=""):
        v = f"{valor:.4f}" if isinstance(valor, float) else str(valor)
        linha_str = f"  {nome:<36} {v:>12}  {unidade:<10}"
        if comentario:
            linha_str += f"  ← {comentario}"
        return linha_str

    print()
    print(sep2)
    print("  CÁLCULO DE ELEVADOR DE CANECAS — MISTURA 90")
    print("  Baseado na planilha 110-EL-001")
    print(sep2)

    print(f"\n{'─'*28} ENTRADA {'─'*31}")
    print(linha("V — Volume caneca 75%",     e.V,          "L"))
    print(linha("n — Fileiras",              e.n,          "und"))
    print(linha("e — Passo",                 e.e,          "mm"))
    print(linha("v — Velocidade correia",    e.v_correia,  "m/s"))
    print(linha("D — Diâmetro tambor",       e.D,          "m"))
    print(linha("H — Altura CC",             e.H,          "m"))
    print(linha("γ — Peso específico",       e.gamma,      "t/m³"))
    print(linha("CF1 — Coef. enchimento",    e.CF1,        "adm"))
    print(linha("CF2 — Coef. homog.",        e.CF2,        "adm"))

    print(f"\n{sep}")
    print("  1. CAPACIDADE")
    print(sep)
    print(linha("Q — Capacidade",           r.Q_m3h,  "m³/h"))
    print(linha("Q — Capacidade",           r.Q_th,   "t/h"))

    print(f"\n{sep}")
    print("  2. GEOMETRIA DA CORREIA")
    print(sep)
    print(linha("Ca — Correia aberta",       r.Ca,     "m"))
    print(linha("N1 — Nº de canecas (calc)", r.N1,     "und"))
    print(linha("N1 — Nº de canecas (adot)", math.ceil(r.N1), "und"))
    print(linha("Pm — Peso/m material",      r.Pm,     "kg/m"))
    print(linha("p1 — Peso mat./caneca 100%",r.p1,     "kg"))

    print(f"\n{sep}")
    print("  3. TENSÕES")
    print(sep)
    print(linha("Tp — Tensão estática",      r.Tp,     "kgf"))
    print(linha("Te(a) — Tensão efetiva",    r.Te_a,   "kgf",  "em função da carga"))
    print(linha("Te(b) — Tensão efetiva",    r.Te_b,   "kgf",  "em função das canecas"))
    print(linha("Te — Adotado (maior)",       r.Te,     "kgf"))
    print(linha("Tm — Tensão máxima",        r.Tm,     "kgf"))
    print(linha("K — Fator abraçamento",     r.K_abraç, ""))
    print(linha("Pe — Peso esticador grav.", r.Pe,     "kgf"))

    print(f"\n{sep}")
    print("  4. SELEÇÃO DA CORREIA")
    print(sep)
    print(linha("Ut — Unidade de tensão",    r.Ut,     "kgf/cm"))
    print(linha("Nm — Lonas mínimas",        r.Nm,     "lonas"))
    print(linha("NL — Lonas selecionadas",   r.NL,     "lonas"))
    pct_status = "✓ OK" if r.pct_Tad <= 75 else "⚠ ACIMA DE 75%"
    print(linha("%%Tad — %% admissível",     r.pct_Tad, "%",   pct_status))

    print(f"\n{sep}")
    print("  5. DIMENSIONAMENTO DOS EIXOS")
    print(sep)
    print("  Eixo Motriz:")
    print(linha("  Mf — Momento fletor",     r.Mf_motriz, "kgf·cm"))
    print(linha("  Mt — Momento torsor",     r.Mt_motriz, "kgf·cm"))
    print(linha("  Mi — Momento ideal",      r.Mi_motriz, "kgf·cm"))
    print(linha("  d ≥ (calculado)",         r.d_motriz_calc, "mm"))
    print("  Eixo Movido (Retorno):")
    print(linha("  Mf — Momento fletor",     r.Mf_movido, "kgf·cm"))
    print(linha("  d ≥ (calculado)",         r.d_movido_calc, "mm"))

    print(f"\n{sep}")
    print("  6. POTÊNCIA E REDUTOR")
    print(sep)
    print(linha("N — Potência calculada",    r.N_cv,   "cv"))
    print(linha("N — Potência calculada",    r.N_kw,   "kW"))
    print(linha("rs — Rotação de saída",     r.rs,     "rpm"))
    print(linha("R — Redução",               r.R,      "",    f"1 : {r.R:.1f}"))

    print(f"\n{sep}")
    print("  7. ACOPLAMENTO")
    print(sep)
    print(linha("Meq alta — Mom. equiv.",    r.Meq_alta, "N·m"))

    print(f"\n{sep}")
    print("  8. ROLAMENTOS  (L10h = 50.000 h)")
    print(sep)
    print(linha("C — Cap. dinâmica motriz",  r.C_motriz_N / 1000, "kN"))
    print(linha("C — Cap. dinâmica movido",  r.C_movido_N / 1000, "kN"))

    print(f"\n{sep2}\n")


def parse_args():
    ap = argparse.ArgumentParser(description="Cálculo de Elevador de Canecas")
    ap.add_argument("--V",     type=float, default=11.99,    help="Volume caneca 75%% (L)")
    ap.add_argument("--n",     type=int,   default=1,        help="Fileiras de canecas")
    ap.add_argument("--e",     type=float, default=310.0,    help="Passo das canecas (mm)")
    ap.add_argument("--v",     type=float, default=5.0,      help="Velocidade correia (m/s)")
    ap.add_argument("--D",     type=float, default=0.62,     help="Diâmetro tambor motriz (m)")
    ap.add_argument("--H",     type=float, default=10.0,     help="Altura CC (m)")
    ap.add_argument("--gamma", type=float, default=1.11,     help="Peso específico material (t/m³)")
    ap.add_argument("--CF1",   type=float, default=0.754,    help="Coef. enchimento (adm)")
    ap.add_argument("--CF2",   type=float, default=1.0,      help="Coef. homogeneidade (adm)")
    ap.add_argument("--Tu",    type=float, default=33.0,     help="Tensão admissível lona (kgf/cm·lona)")
    ap.add_argument("--B",     type=float, default=55.88,    help="Largura correia (cm)")
    ap.add_argument("--pc",    type=float, default=11.5939824, help="Peso correia (kg/m)")
    ap.add_argument("--p",     type=float, default=16.13556, help="Peso caneca (kg)")
    ap.add_argument("--eta",   type=float, default=0.95,     help="Rendimento grupo motor")
    ap.add_argument("--Rm",    type=float, default=1750.0,   help="Rotação motor (rpm)")
    ap.add_argument("--k",     type=float, default=0.85,     help="Fator acionamento")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()

    entrada = EntradaElevador(
        V=args.V, n=args.n, e=args.e,
        D=args.D, H=args.H, gamma=args.gamma,
        CF1=args.CF1, CF2=args.CF2,
        Tu=args.Tu, B=args.B, pc=args.pc, p=args.p,
        eta=args.eta, Rm=args.Rm, k=args.k,
    )
    entrada.v_correia = args.v

    resultado = calcular(entrada)
    imprimir_relatorio(entrada, resultado)
