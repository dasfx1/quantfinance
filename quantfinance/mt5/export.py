from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from quantfinance.strategies.mean_reversion import MeanReversionParams

PROJECT_ROOT = Path(__file__).resolve().parents[2]


EA_TEMPLATE = """
//+------------------------------------------------------------------+\n"""

EA_TEMPLATE += """//| Mean Reversion (Auto-generated)                              |\n"""
EA_TEMPLATE += """//+------------------------------------------------------------------+\n"""
EA_TEMPLATE += """#property strict\n\n"""
EA_TEMPLATE += """input int    Period         = {period};\n"""
EA_TEMPLATE += """input double ZEntry         = {z_entry};\n"""
EA_TEMPLATE += """input double ZExit          = {z_exit};\n"""
EA_TEMPLATE += """input double StopLossPoints = {sl_distance};\n"""
EA_TEMPLATE += """input double TakeProfitPts  = {tp_distance};\n"""
EA_TEMPLATE += """input double Lots           = 0.1;\n"""
EA_TEMPLATE += """
// The EA uses a simple z-score mean reversion trigger. Replace the
// placeholder logic in OnTick() with your broker's symbol rules.\n\n"""
EA_TEMPLATE += """
int OnInit() {{
   Print("EA geladen: Mean Reversion, ZEntry=", ZEntry, " SL=", StopLossPoints, " TP=", TakeProfitPts);
   return(INIT_SUCCEEDED);
}}

void OnTick()
{{
   // TODO: Implement production-grade signal handling.
   // This template simply illustrates where to place the strategy rules.
}}
"""


def load_best_params_from_csv(path: Path) -> Optional[MeanReversionParams]:
    if not path.exists():
        return None

    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        return None

    try:
        sorted_rows = sorted(rows, key=lambda row: float(row.get("end_capital", 0)), reverse=True)
        best = sorted_rows[0]
        return MeanReversionParams(
            period=int(float(best.get("period", 20))),
            z_entry=float(best.get("z_entry", 1.5)),
            z_exit=float(best.get("z_exit", 0.5)),
            sl_distance=float(best.get("sl_distance", 2.0)),
            tp_distance=float(best.get("tp_distance", 4.0)),
            stake=int(float(best.get("stake", 10))),
            initial_cash=float(best.get("initial_cash", 10_000)),
        )
    except Exception:
        return None


def export_mean_reversion_ea(
    params: MeanReversionParams, output_dir: Path | None = None, name: str = "mean_reversion_auto"
) -> Path:
    output_dir = output_dir or (PROJECT_ROOT / "dist")
    output_dir.mkdir(parents=True, exist_ok=True)

    content = EA_TEMPLATE.format(
        period=params.period,
        z_entry=params.z_entry,
        z_exit=params.z_exit,
        sl_distance=params.sl_distance,
        tp_distance=params.tp_distance,
    )

    output_path = output_dir / f"{name}.mq5"
    output_path.write_text(content)
    return output_path


__all__ = ["export_mean_reversion_ea", "load_best_params_from_csv"]
