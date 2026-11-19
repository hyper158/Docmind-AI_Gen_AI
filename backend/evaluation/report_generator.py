import csv
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure Matplotlib writable cache before importing matplotlib
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "docmind_mpl_cache"))
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt

from evaluation.config import RESULTS_DIR, CHARTS_DIR


class ReportGenerator:
    """Generates evaluation artifacts: JSON, CSV, Matplotlib charts, and HTML."""

    def __init__(self, eval_data: Dict[str, Any], results_dir: Path = RESULTS_DIR) -> None:
        self.data = eval_data
        self.results_dir = results_dir
        self.charts_dir = results_dir / "charts"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> Dict[str, str]:
        """Generates all 4 artifact formats and returns their file paths."""
        json_path = self.generate_json()
        csv_path = self.generate_csv()
        chart_paths = self.generate_charts()
        html_path = self.generate_html(chart_paths)

        return {
            "json": str(json_path),
            "csv": str(csv_path),
            "html": str(html_path),
            "charts": [str(p) for p in chart_paths],
        }

    def generate_json(self) -> Path:
        json_file = self.results_dir / "metrics.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        return json_file

    def generate_csv(self) -> Path:
        csv_file = self.results_dir / "test_results.csv"
        results = self.data.get("results", [])
        if not results:
            return csv_file

        headers = [
            "id", "category", "question", "answer_status",
            "context_precision", "context_recall", "faithfulness",
            "answer_relevance", "answer_correctness", "citation_accuracy",
            "retrieval_latency_sec", "generation_latency_sec", "total_latency_sec",
            "citation_count", "ground_truth_answer", "generated_answer"
        ]

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)

        return csv_file

    def generate_charts(self) -> List[Path]:
        generated = []
        plt.style.use("dark_background")

        overall = self.data.get("overall_metrics", {})
        thresholds = self.data.get("target_thresholds", {})
        cat_breakdown = self.data.get("category_breakdown", {})
        latency = self.data.get("latency_summary", {})

        # Chart 1: Overall Metrics vs Threshold
        c1_path = self.charts_dir / "overall_metrics.png"
        metrics_keys = [
            ("faithfulness", "Faithfulness"),
            ("context_precision", "Context Precision"),
            ("context_recall", "Context Recall"),
            ("answer_relevance", "Answer Relevance"),
            ("answer_correctness", "Answer Correctness"),
            ("citation_accuracy", "Citation Accuracy"),
        ]

        labels = [m[1] for m in metrics_keys]
        values = [overall.get(m[0], 0.0) * 100 for m in metrics_keys]
        targets = [thresholds.get(m[0], 0.8) * 100 for m in metrics_keys]

        fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#111827")

        y_pos = range(len(labels))
        bars = ax.barh(y_pos, values, color="#6366f1", alpha=0.85, height=0.55, label="Achieved Score")
        ax.scatter(targets, y_pos, color="#22c55e", s=90, zorder=5, marker="|", label="Target Threshold")

        for bar in bars:
            w = bar.get_width()
            ax.text(w + 1.5, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%",
                    va="center", ha="left", color="#e2e8f0", fontsize=9, fontweight="bold")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color="#cbd5e1", fontsize=9.5)
        ax.set_xlim(0, 115)
        ax.set_xlabel("Percentage (%)", color="#94a3b8", fontsize=10)
        ax.set_title("DocMind AI - Core RAG Quality Metrics", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
        ax.grid(axis="x", color="#334155", linestyle="--", alpha=0.5)
        ax.legend(loc="lower right", framealpha=0.3, facecolor="#1e293b", edgecolor="#475569")
        plt.tight_layout()
        plt.savefig(c1_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close()
        generated.append(c1_path)

        # Chart 2: Category Breakdown
        if cat_breakdown:
            c2_path = self.charts_dir / "category_performance.png"
            fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
            fig.patch.set_facecolor("#0b0f19")
            ax.set_facecolor("#111827")

            cats = list(cat_breakdown.keys())
            clean_cats = [c.replace("_", " ").title() for c in cats]
            cat_faith = [cat_breakdown[c].get("faithfulness", 0) * 100 for c in cats]
            cat_prec = [cat_breakdown[c].get("context_precision", 0) * 100 for c in cats]
            cat_corr = [cat_breakdown[c].get("answer_correctness", 0) * 100 for c in cats]

            import numpy as np
            x = np.arange(len(cats))
            width = 0.26

            ax.bar(x - width, cat_faith, width, label="Faithfulness", color="#818cf8")
            ax.bar(x, cat_prec, width, label="Context Precision", color="#38bdf8")
            ax.bar(x + width, cat_corr, width, label="Correctness", color="#a855f7")

            ax.set_ylabel("Score (%)", color="#94a3b8", fontsize=10)
            ax.set_title("Performance by Question Category", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
            ax.set_xticks(x)
            ax.set_xticklabels(clean_cats, rotation=28, ha="right", color="#cbd5e1", fontsize=8.5)
            ax.set_ylim(0, 110)
            ax.grid(axis="y", color="#334155", linestyle="--", alpha=0.5)
            ax.legend(loc="upper right", framealpha=0.3, facecolor="#1e293b", edgecolor="#475569")
            plt.tight_layout()
            plt.savefig(c2_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
            plt.close()
            generated.append(c2_path)

        # Chart 3: Latency Breakdown
        if latency:
            c3_path = self.charts_dir / "latency_breakdown.png"
            fig, ax = plt.subplots(figsize=(7, 3.8), dpi=150)
            fig.patch.set_facecolor("#0b0f19")
            ax.set_facecolor("#111827")

            stages = ["FAISS Retrieval", "LLM Inference", "Total E2E"]
            lat_vals = [
                latency.get("retrieval_mean_sec", 0.05),
                latency.get("generation_mean_sec", 1.2),
                latency.get("total_mean_sec", 1.25),
            ]
            colors = ["#38bdf8", "#818cf8", "#c084fc"]

            bars = ax.bar(stages, lat_vals, color=colors, width=0.45, alpha=0.9)
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05, f"{h:.2f}s",
                        ha="center", va="bottom", color="#e2e8f0", fontsize=9, fontweight="bold")

            ax.set_ylabel("Latency (Seconds)", color="#94a3b8", fontsize=10)
            ax.set_title("Mean Latency by Pipeline Stage", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
            ax.set_ylim(0, max(lat_vals) * 1.35 if lat_vals else 5)
            ax.grid(axis="y", color="#334155", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(c3_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
            plt.close()
            generated.append(c3_path)

        return generated

    def generate_html(self, chart_paths: List[Path]) -> Path:
        html_file = self.results_dir / "evaluation_report.html"
        overall = self.data.get("overall_metrics", {})
        latency = self.data.get("latency_summary", {})
        cat_breakdown = self.data.get("category_breakdown", {})
        results = self.data.get("results", [])
        model_name = self.data.get("model_name", "nvidia/nemotron-3.5-lightning:free")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build Category Rows
        cat_rows_html = ""
        for cat, scores in cat_breakdown.items():
            cat_name = cat.replace("_", " ").title()
            cat_rows_html += f"""
            <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
                <td class="py-3 px-4 font-medium text-slate-200">{cat_name}</td>
                <td class="py-3 px-4 text-center text-slate-400">{scores.get('count', 0)}</td>
                <td class="py-3 px-4 text-center font-semibold text-emerald-400">{(scores.get('faithfulness', 0)*100):.1f}%</td>
                <td class="py-3 px-4 text-center font-semibold text-indigo-400">{(scores.get('context_precision', 0)*100):.1f}%</td>
                <td class="py-3 px-4 text-center font-semibold text-sky-400">{(scores.get('context_recall', 0)*100):.1f}%</td>
                <td class="py-3 px-4 text-center font-semibold text-purple-400">{(scores.get('answer_relevance', 0)*100):.1f}%</td>
                <td class="py-3 px-4 text-center font-semibold text-amber-400">{(scores.get('citation_accuracy', 0)*100):.1f}%</td>
                <td class="py-3 px-4 text-center text-slate-300">{scores.get('total_mean_latency_sec', 0):.2f}s</td>
            </tr>
            """

        # Build Sample Rows
        sample_rows_html = ""
        for r in results[:40]:  # Up to 40 sample rows
            cat_badge = r.get("category", "").replace("_", " ").title()
            status_color = "text-emerald-400" if r.get("answer_status") == "grounded" else "text-amber-400"
            sample_rows_html += f"""
            <details class="group bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden mb-3">
                <summary class="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-800/50 transition-colors">
                    <div class="flex items-center gap-3 min-w-0 pr-4">
                        <span class="px-2 py-0.5 text-[11px] rounded bg-indigo-500/20 text-indigo-300 font-mono">{r.get('id')}</span>
                        <span class="px-2 py-0.5 text-[11px] rounded bg-slate-800 text-slate-300">{cat_badge}</span>
                        <span class="text-sm font-medium text-slate-200 truncate">{r.get('question')}</span>
                    </div>
                    <div class="flex items-center gap-4 flex-shrink-0 text-xs">
                        <span class="font-mono {status_color}">{r.get('answer_status')}</span>
                        <span class="font-semibold text-emerald-400">Faith: {(r.get('faithfulness', 0)*100):.0f}%</span>
                        <span class="text-slate-400">{r.get('total_latency_sec')}s</span>
                    </div>
                </summary>
                <div class="p-4 border-t border-slate-800 bg-slate-950/80 space-y-3 text-xs leading-relaxed font-sans">
                    <div>
                        <div class="text-[11px] uppercase tracking-wider font-bold text-slate-400 mb-1">Generated Answer:</div>
                        <div class="text-slate-200 bg-slate-900/90 p-3 rounded-lg whitespace-pre-wrap">{r.get('generated_answer')}</div>
                    </div>
                    <div>
                        <div class="text-[11px] uppercase tracking-wider font-bold text-slate-400 mb-1">Ground Truth:</div>
                        <div class="text-slate-300 bg-slate-900/50 p-2.5 rounded-lg">{r.get('ground_truth_answer')}</div>
                    </div>
                    <div class="flex flex-wrap gap-4 pt-2 text-[11px] text-slate-400">
                        <span>Context Precision: <strong class="text-indigo-300">{(r.get('context_precision', 0)*100):.1f}%</strong></span>
                        <span>Context Recall: <strong class="text-sky-300">{(r.get('context_recall', 0)*100):.1f}%</strong></span>
                        <span>Relevance: <strong class="text-purple-300">{(r.get('answer_relevance', 0)*100):.1f}%</strong></span>
                        <span>Citation Accuracy: <strong class="text-amber-300">{(r.get('citation_accuracy', 0)*100):.1f}%</strong></span>
                        <span>Citations: <strong class="text-slate-200">{r.get('citation_count')} verified</strong></span>
                    </div>
                </div>
            </details>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocMind AI - Model Evaluation Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0b0f19; }}
        code, pre, .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
</head>
<body class="text-slate-100 min-h-screen p-6 sm:p-10">
    <div class="max-w-6xl mx-auto space-y-8">
        
        <!-- Header -->
        <header class="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-cyan-400 p-0.5">
                        <div class="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center font-bold text-indigo-400">DM</div>
                    </div>
                    <div>
                        <h1 class="text-2xl font-extrabold text-white">DocMind AI – RAG Evaluation Report</h1>
                        <p class="text-xs text-slate-400">Independent Quality Assessment & Performance Benchmarks</p>
                    </div>
                </div>
            </div>
            <div class="text-right text-xs text-slate-400 space-y-1">
                <div>Model: <span class="font-mono text-indigo-300 font-semibold">{model_name}</span></div>
                <div>Evaluated: <span class="font-mono text-slate-300">{timestamp}</span></div>
                <div>Test Samples: <span class="font-mono text-slate-200 font-bold">{overall.get('total_evaluated', 0)} questions</span></div>
            </div>
        </header>

        <!-- KPI Scorecards -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Faithfulness</div>
                <div class="text-3xl font-extrabold text-emerald-400 mt-1">{(overall.get('faithfulness', 0)*100):.1f}%</div>
                <div class="text-[11px] text-slate-500 mt-1">Zero Hallucination Grounding</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Context Precision</div>
                <div class="text-3xl font-extrabold text-indigo-400 mt-1">{(overall.get('context_precision', 0)*100):.1f}%</div>
                <div class="text-[11px] text-slate-500 mt-1">FAISS Semantic Retrieval</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Context Recall</div>
                <div class="text-3xl font-extrabold text-sky-400 mt-1">{(overall.get('context_recall', 0)*100):.1f}%</div>
                <div class="text-[11px] text-slate-500 mt-1">Syllabus Information Coverage</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Citation Accuracy</div>
                <div class="text-3xl font-extrabold text-amber-400 mt-1">{(overall.get('citation_accuracy', 0)*100):.1f}%</div>
                <div class="text-[11px] text-slate-500 mt-1">Verifiable Page References</div>
            </div>
        </section>

        <!-- Visual Analytics Charts -->
        <section class="space-y-4">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
                <span>Visual Analytics & Benchmark Charts</span>
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md">
                    <img src="charts/overall_metrics.png" alt="Overall Metrics" class="rounded-xl w-full">
                </div>
                <div class="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md">
                    <img src="charts/category_performance.png" alt="Category Breakdown" class="rounded-xl w-full">
                </div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md max-w-xl mx-auto">
                <img src="charts/latency_breakdown.png" alt="Latency Breakdown" class="rounded-xl w-full">
            </div>
        </section>

        <!-- Category Performance Table -->
        <section class="space-y-4">
            <h2 class="text-lg font-bold text-white">Performance by Question Category</h2>
            <div class="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-950/80 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                        <tr>
                            <th class="py-3 px-4">Category</th>
                            <th class="py-3 px-4 text-center">Tests</th>
                            <th class="py-3 px-4 text-center">Faithfulness</th>
                            <th class="py-3 px-4 text-center">Context Prec</th>
                            <th class="py-3 px-4 text-center">Context Rec</th>
                            <th class="py-3 px-4 text-center">Relevance</th>
                            <th class="py-3 px-4 text-center">Citation Acc</th>
                            <th class="py-3 px-4 text-center">Mean Latency</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cat_rows_html}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Test Case Explorer -->
        <section class="space-y-4">
            <div class="flex items-center justify-between">
                <h2 class="text-lg font-bold text-white">Detailed Evaluation Cases</h2>
                <span class="text-xs text-slate-400">Click any card to inspect generated answer and citations</span>
            </div>
            <div>
                {sample_rows_html}
            </div>
        </section>

        <!-- Footer -->
        <footer class="pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
            DocMind AI Evaluation Engine &bull; Automated RAG Assessment System &bull; FastEmbed + FAISS + LangChain
        </footer>
    </div>
</body>
</html>
"""
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_file
