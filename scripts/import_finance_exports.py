#!/usr/bin/env python3
"""Import Nomad Pocket finance exports from iCloud into normalized expenses."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from time_utils import local_timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()
ICLOUD_FINANCE_DIR = Path("/Users/jongiljeong/Library/Mobile Documents/com~apple~CloudDocs/Nomad_life/Finance")
LOCAL_INBOX_DIR = PROJECT_ROOT / "data/expenses/imports/inbox"
NORMALIZED_EXPENSES_PATH = PROJECT_ROOT / "data/expenses/normalized-expenses.json"
DASHBOARD_FINANCE_REVIEW_PATH = PROJECT_ROOT / "dashboard/finance-review.json"
ACTION_LOG_DIR = PROJECT_ROOT / "data/action_logs"


CATEGORY_MAP = {
    "주거비": "lodging",
    "식비": "food",
    "쇼핑": "shopping",
    "교통비": "transport",
    "의료비": "health",
    "자동차": "transport",
    "문화생활비": "activity",
    "자기계발비": "education",
    "통신/구독료": "tools",
    "꾸밈비": "shopping",
    "보험료": "insurance",
    "세금": "tax",
    "인간관리비": "social",
    "단기여행": "travel",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Nomad Life finance JSON exports.")
    parser.add_argument("--source", default=str(ICLOUD_FINANCE_DIR), help="Source iCloud finance export folder.")
    parser.add_argument("--target", default=str(LOCAL_INBOX_DIR), help="Local finance import inbox folder.")
    parser.add_argument("--latest-only", action=argparse.BooleanOptionalAction, default=True, help="Normalize only the latest export file.")
    return parser.parse_args()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_hash(record: dict) -> str:
    raw = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def import_exports(source_dir: Path, target_dir: Path) -> dict:
    now = datetime.now(TIMEZONE)
    result = {
        "schema_version": "0.1.0",
        "imported_at": now.isoformat(),
        "source_dir": str(source_dir),
        "target_dir": str(target_dir.relative_to(PROJECT_ROOT) if target_dir.is_relative_to(PROJECT_ROOT) else target_dir),
        "scanned_count": 0,
        "scanned_files": [],
        "imported": [],
        "updated": [],
        "skipped": [],
        "errors": [],
    }
    if not source_dir.exists():
        result["errors"].append({"file": str(source_dir), "error": "source_dir_not_found"})
        return result

    target_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(path for path in source_dir.rglob("*.json") if path.is_file())
    for source_path in source_paths:
        result["scanned_count"] += 1
        result["scanned_files"].append(str(source_path.relative_to(source_dir)))
        target_path = target_dir / source_path.name
        try:
            if target_path.exists():
                if file_hash(source_path) == file_hash(target_path):
                    result["skipped"].append(source_path.name)
                    continue
                shutil.copy2(source_path, target_path)
                result["updated"].append(source_path.name)
                continue
            shutil.copy2(source_path, target_path)
            result["imported"].append(source_path.name)
        except OSError as exc:
            result["errors"].append({"file": source_path.name, "error": str(exc)})
    return result


def parse_exported_at(payload: dict, fallback: datetime) -> datetime:
    raw = payload.get("exportedAt")
    if not raw:
        return fallback
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return fallback


def load_exports(inbox_dir: Path) -> list[dict]:
    exports = []
    for path in sorted(inbox_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            exports.append({"path": path, "error": f"json_decode_error:{exc}"})
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            exports.append({"path": path, "error": "unsupported_export_shape"})
            continue
        exports.append(
            {
                "path": path,
                "payload": payload,
                "exported_at": parse_exported_at(payload, datetime.fromtimestamp(path.stat().st_mtime, tz=TIMEZONE)),
            }
        )
    return exports


def lookup_by_id(records: list[dict]) -> dict:
    return {record.get("id"): record for record in records if record.get("id")}


def expense_category(expense: dict) -> str:
    return expense.get("metadata", {}).get("source_category_name") or expense.get("category") or "미분류"


def expense_subcategory(expense: dict) -> str:
    return expense.get("metadata", {}).get("source_subcategory_name") or expense.get("subcategory") or "미분류"


def sum_by(items: list[dict], key: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    for item in items:
        totals[key] = totals.get(key, 0) + float(item.get("amount") or 0)
    return totals


def month_key_from_expenses(expenses: list[dict], normalized: dict, now: datetime) -> str:
    dates = sorted(expense.get("date") for expense in expenses if expense.get("date"))
    if dates:
        return dates[-1][:7]
    source_files = normalized.get("source", {}).get("files") or []
    exported_at = source_files[0].get("exported_at") if source_files else None
    if exported_at:
        try:
            return datetime.fromisoformat(exported_at.replace("Z", "+00:00")).strftime("%Y-%m")
        except ValueError:
            pass
    return now.strftime("%Y-%m")


def date_diff_days(start_date: str | None, end_date: str | None) -> int:
    if not start_date or not end_date:
        return 0
    try:
        start = datetime.fromisoformat(f"{start_date}T00:00:00")
        end = datetime.fromisoformat(f"{end_date}T00:00:00")
    except ValueError:
        return 0
    return max(1, (end - start).days + 1)


def compact_expense(expense: dict) -> dict:
    return {
        "date": expense.get("date"),
        "amount": expense.get("amount"),
        "currency": expense.get("currency"),
        "merchant": expense.get("merchant"),
        "category": expense_category(expense),
        "subcategory": expense_subcategory(expense),
        "place": expense.get("place"),
    }


def build_region_reviews(expenses: list[dict], latest_trade_date: str | None) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for expense in expenses:
        grouped.setdefault(expense.get("place") or "지역 미지정", []).append(expense)

    reviews = []
    for region, region_expenses in grouped.items():
        total = sum(float(expense.get("amount") or 0) for expense in region_expenses)
        dates = sorted(expense.get("date") for expense in region_expenses if expense.get("date"))
        start_date = dates[0] if dates else None
        end_date = dates[-1] if dates else None
        is_active_region = any(expense.get("metadata", {}).get("source_region_is_active") for expense in region_expenses)
        projection_end_date = latest_trade_date if is_active_region and latest_trade_date and end_date and latest_trade_date > end_date else end_date
        observed_days = date_diff_days(start_date, end_date)
        total_days = date_diff_days(start_date, projection_end_date) or observed_days
        daily_average = round(total / observed_days) if observed_days else 0
        projected_total = round((total / observed_days) * total_days) if observed_days and total_days else round(total)

        by_category: dict[str, float] = {}
        for expense in region_expenses:
            category = expense_category(expense)
            by_category[category] = by_category.get(category, 0) + float(expense.get("amount") or 0)
        top_categories = sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:4]
        top_category_names = {category for category, _ in top_categories}
        category_total = sum(amount for _, amount in top_categories)
        category_rows = []
        for category, amount in top_categories:
            details = sorted(
                [expense for expense in region_expenses if expense_category(expense) == category],
                key=lambda expense: float(expense.get("amount") or 0),
                reverse=True,
            )[:8]
            category_rows.append(
                {
                    "category": category,
                    "amount": round(amount),
                    "ratio": round((amount / total) * 100) if total else 0,
                    "details": [compact_expense(expense) for expense in details],
                }
            )
        other_details = sorted(
            [expense for expense in region_expenses if expense_category(expense) not in top_category_names],
            key=lambda expense: float(expense.get("amount") or 0),
            reverse=True,
        )[:8]
        reviews.append(
            {
                "region": region,
                "total": round(total),
                "count": len(region_expenses),
                "startDate": start_date,
                "endDate": projection_end_date,
                "lastExpenseDate": end_date,
                "isActiveRegion": is_active_region,
                "totalDays": total_days,
                "observedDays": observed_days,
                "dailyAverage": daily_average,
                "projectedTotal": projected_total,
                "categoryRows": category_rows,
                "otherTotal": max(0, round(total - category_total)),
                "otherDetails": [compact_expense(expense) for expense in other_details],
            }
        )
    return sorted(reviews, key=lambda review: review["total"], reverse=True)


def normalize_expense(transaction: dict, *, export_file: str, category_by_id: dict, subcategory_by_id: dict, payment_by_id: dict, region_by_id: dict) -> dict:
    category = category_by_id.get(transaction.get("category_id"), {})
    subcategory = subcategory_by_id.get(transaction.get("subcategory_id"), {})
    payment_method = payment_by_id.get(transaction.get("payment_method_id"), {})
    region = region_by_id.get(transaction.get("region_id"), {})
    category_name = category.get("name")
    subcategory_name = subcategory.get("name")

    return {
        "id": f"expense_{transaction.get('id')}",
        "date": transaction.get("date"),
        "posted_at": transaction.get("created_at"),
        "amount": transaction.get("amount"),
        "currency": transaction.get("currency"),
        "original_amount": transaction.get("original_amount"),
        "exchange_rate": transaction.get("exchange_rate"),
        "category": CATEGORY_MAP.get(category_name, "other"),
        "subcategory": subcategory_name,
        "merchant": transaction.get("description"),
        "place": region.get("name"),
        "country": None,
        "payment_method": payment_method.get("name"),
        "satisfaction": None,
        "required_or_optional": "unknown",
        "note": transaction.get("memo"),
        "source": f"finance_export:{export_file}:{transaction.get('id')}",
        "source_app": "nomad_pocket",
        "raw_hash": record_hash(transaction),
        "metadata": {
            "source_type": transaction.get("type"),
            "source_category_id": transaction.get("category_id"),
            "source_category_name": category_name,
            "source_subcategory_id": transaction.get("subcategory_id"),
            "source_subcategory_name": subcategory_name,
            "source_payment_method_id": transaction.get("payment_method_id"),
            "source_region_id": transaction.get("region_id"),
            "source_region_is_active": region.get("is_active"),
            "is_fixed": transaction.get("is_fixed"),
            "fixed_item_id": transaction.get("fixed_item_id"),
            "tag_ids": transaction.get("tag_ids") or [],
            "import_source": transaction.get("import_source"),
            "import_status": transaction.get("import_status"),
            "import_confidence": transaction.get("import_confidence"),
        },
    }


def normalize_exports(inbox_dir: Path, latest_only: bool = True, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    loaded = load_exports(inbox_dir)
    errors = [{"file": item["path"].name, "error": item["error"]} for item in loaded if item.get("error")]
    valid_exports = [item for item in loaded if item.get("payload")]
    if latest_only and valid_exports:
        valid_exports = [
            max(
                valid_exports,
                key=lambda item: (
                    item["exported_at"],
                    item["path"].stat().st_mtime,
                    item["path"].name,
                ),
            )
        ]

    expenses = []
    budgets = []
    income_count = 0
    transaction_count = 0
    for item in valid_exports:
        payload = item["payload"]
        data = payload["data"]
        category_by_id = lookup_by_id(data.get("categories", []))
        subcategory_by_id = lookup_by_id(data.get("subcategories", []))
        payment_by_id = lookup_by_id(data.get("payment_methods", []))
        region_by_id = lookup_by_id(data.get("regions", []))
        budgets.extend(
            {
                "id": budget.get("id"),
                "name": budget.get("name"),
                "target_amount": budget.get("target_amount"),
                "period_type": budget.get("period_type"),
                "year": budget.get("year"),
                "month": budget.get("month"),
                "filter_type": budget.get("filter_type"),
                "filter_id": budget.get("filter_id"),
                "is_active": budget.get("is_active"),
                "is_system": budget.get("is_system"),
                "source": f"finance_export:{item['path'].name}:{budget.get('id')}",
            }
            for budget in data.get("budgets", [])
        )
        for transaction in data.get("transactions", []):
            transaction_count += 1
            if transaction.get("type") == "income":
                income_count += 1
                continue
            if transaction.get("type") != "expense":
                continue
            expenses.append(
                normalize_expense(
                    transaction,
                    export_file=item["path"].name,
                    category_by_id=category_by_id,
                    subcategory_by_id=subcategory_by_id,
                    payment_by_id=payment_by_id,
                    region_by_id=region_by_id,
                )
            )

    expenses.sort(key=lambda expense: (expense.get("date") or "", expense.get("posted_at") or "", expense.get("id") or ""))
    payload = {
        "schema_version": "0.2.0",
        "updated_at": now.isoformat(),
        "source": {
            "type": "finance_json_export",
            "source_app": "nomad_pocket",
            "source_dir": str(ICLOUD_FINANCE_DIR),
            "local_inbox": str(inbox_dir.relative_to(PROJECT_ROOT) if inbox_dir.is_relative_to(PROJECT_ROOT) else inbox_dir),
            "latest_only": latest_only,
            "files": [
                {
                    "name": item["path"].name,
                    "exported_at": item["exported_at"].isoformat(),
                    "modified_at": datetime.fromtimestamp(item["path"].stat().st_mtime, tz=TIMEZONE).isoformat(),
                    "version": item["payload"].get("version"),
                }
                for item in valid_exports
            ],
            "selected_file": valid_exports[0]["path"].name if latest_only and valid_exports else None,
        },
        "data_quality": {
            "status": "partial" if expenses else "empty",
            "notes": [
                "Imported from read-only Nomad Pocket JSON export.",
                "Only expense transactions are normalized here; income records are counted but excluded.",
                "Source export files are copied locally and never written back.",
            ],
            "errors": errors,
        },
        "summary": {
            "export_file_count": len(valid_exports),
            "transaction_count": transaction_count,
            "expense_count": len(expenses),
            "income_count_excluded": income_count,
            "budget_count": len(budgets),
        },
        "budgets": budgets,
        "expenses": expenses,
    }
    write_json(NORMALIZED_EXPENSES_PATH, payload)
    return payload


def find_monthly_budget(normalized: dict, month_key: str) -> dict | None:
    try:
        year, month = (int(part) for part in month_key.split("-", 1))
    except ValueError:
        return None
    for budget in normalized.get("budgets") or []:
        if budget.get("is_active") is False:
            continue
        if budget.get("period_type") != "monthly" or budget.get("filter_type") != "total":
            continue
        if int(budget.get("year") or 0) == year and int(budget.get("month") or 0) == month:
            return budget
    return None


def build_finance_review_snapshot(normalized: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    expenses = normalized.get("expenses") or []
    month_key = month_key_from_expenses(expenses, normalized, now)
    month_expenses = [expense for expense in expenses if str(expense.get("date") or "").startswith(month_key)]
    month_total = round(sum(float(expense.get("amount") or 0) for expense in month_expenses))
    latest_trade_date = sorted(expense.get("date") for expense in expenses if expense.get("date"))[-1] if expenses else None
    budget = find_monthly_budget(normalized, month_key)
    budget_amount = round(float(budget.get("target_amount") or 0)) if budget else 0
    budget_gap = budget_amount - month_total if budget_amount else None
    budget_ratio = round((month_total / budget_amount) * 100) if budget_amount else None
    elapsed_day = max(1, int((latest_trade_date or f"{month_key}-01")[8:10]))
    daily_average = round(month_total / elapsed_day) if month_expenses else 0
    month_end_forecast = daily_average * 30

    category_totals: dict[str, float] = {}
    for expense in month_expenses:
        category = expense_category(expense)
        category_totals[category] = category_totals.get(category, 0) + float(expense.get("amount") or 0)
    category_rows = [
        {
            "category": category,
            "total": round(total),
            "ratio": round((total / month_total) * 100) if month_total else 0,
        }
        for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:6]
    ]

    adjustable = [
        expense
        for expense in month_expenses
        if expense_category(expense) not in {"주거비", "보험료", "세금"}
    ]
    adjustable_total = round(sum(float(expense.get("amount") or 0) for expense in adjustable))
    food_total = round(sum(float(expense.get("amount") or 0) for expense in month_expenses if expense_category(expense) == "식비"))
    missing_region_count = len([expense for expense in expenses if not expense.get("place")])
    top_transactions = [
        compact_expense(expense)
        for expense in sorted(month_expenses, key=lambda expense: float(expense.get("amount") or 0), reverse=True)[:5]
    ]
    source_file = (normalized.get("source", {}).get("files") or [{}])[0]
    status_text = (
        "월 예산 없음"
        if budget_gap is None
        else f"{abs(budget_gap):,} KRW 초과"
        if budget_gap < 0
        else f"{budget_gap:,} KRW 남음"
    )
    top_category = category_rows[0] if category_rows else None
    finance_action = (
        f"{top_category['category']}가 이번 달 지출의 {top_category['ratio']}%입니다. 오늘 조정은 {round(adjustable_total / max(1, 7)):,} KRW 단위로 가볍게 봅니다."
        if top_category
        else "아직 카테고리별 조정 후보가 충분하지 않습니다."
    )
    notes = [
        f"이번 달은 예산을 {abs(budget_gap):,} KRW 초과했습니다." if budget_gap is not None and budget_gap < 0 else f"이번 달 예산 대비 {status_text} 상태입니다.",
        f"조정 가능한 생활비 후보는 {adjustable_total:,} KRW이고, 식비 계열은 {food_total:,} KRW입니다.",
        f"전체 기간 기준 지역 미지정 거래가 {missing_region_count}건이라 체류지별 리뷰 정확도를 높이려면 region 입력 보강이 필요합니다."
        if missing_region_count
        else "전체 거래에 지역 정보가 연결되어 있습니다.",
    ]
    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": now.date().isoformat(),
        "snapshot_kind": "finance-review",
        "source": {
            "source_app": normalized.get("source", {}).get("source_app"),
            "selected_file": normalized.get("source", {}).get("selected_file"),
            "source_file": source_file,
            "normalized_updated_at": normalized.get("updated_at"),
            "expense_count": normalized.get("summary", {}).get("expense_count", len(expenses)),
            "data_quality": normalized.get("data_quality", {}),
        },
        "analysis": {
            "month_key": month_key,
            "latest_trade_date": latest_trade_date,
            "month_total": month_total,
            "budget_amount": budget_amount,
            "budget_gap": budget_gap,
            "budget_ratio": budget_ratio,
            "daily_average": daily_average,
            "month_end_forecast": month_end_forecast,
            "adjustable_total": adjustable_total,
            "food_total": food_total,
            "missing_region_count": missing_region_count,
            "status_text": status_text,
            "status_tone": "over" if budget_gap is not None and budget_gap < 0 else "ok",
            "finance_action": finance_action,
            "category_rows": category_rows,
            "region_reviews": build_region_reviews(expenses, latest_trade_date)[:4],
            "top_transactions": top_transactions,
            "notes": notes,
        },
    }


def write_finance_review_snapshot(normalized: dict, now: datetime | None = None) -> dict:
    snapshot = build_finance_review_snapshot(normalized, now=now)
    write_json(DASHBOARD_FINANCE_REVIEW_PATH, snapshot)
    return snapshot


def append_action_log(import_result: dict, normalized: dict) -> None:
    now = datetime.now(TIMEZONE)
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_finance_import",
        "created_at": now.isoformat(),
        "agent_name": "nomad-finance",
        "action_type": "import_finance_exports_from_icloud",
        "target_tool": "local_files",
        "reason": "Normalize read-only finance export data for spend pattern analysis.",
        "input": {"source_dir": import_result.get("source_dir"), "target_dir": import_result.get("target_dir")},
        "output": {
            "scanned_count": import_result.get("scanned_count", 0),
            "imported_count": len(import_result.get("imported", [])),
            "updated_count": len(import_result.get("updated", [])),
            "skipped_count": len(import_result.get("skipped", [])),
            "error_count": len(import_result.get("errors", [])) + len(normalized.get("data_quality", {}).get("errors", [])),
            "expense_count": normalized.get("summary", {}).get("expense_count", 0),
            "output_path": "data/expenses/normalized-expenses.json",
            "dashboard_path": "dashboard/finance-review.json",
        },
        "status": "warning" if import_result.get("errors") or normalized.get("data_quality", {}).get("errors") else "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": import_result.get("errors") or normalized.get("data_quality", {}).get("errors") or None,
    }
    append_jsonl(ACTION_LOG_DIR / f"{now.date().isoformat()}.jsonl", record)


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source).expanduser()
    target_dir = Path(args.target).expanduser()
    import_result = import_exports(source_dir, target_dir)
    normalized = normalize_exports(target_dir, latest_only=args.latest_only)
    finance_review = write_finance_review_snapshot(normalized)
    append_action_log(import_result, normalized)
    print(
        json.dumps(
            {
                "import": import_result,
                "normalized": {
                    "output": "data/expenses/normalized-expenses.json",
                    "summary": normalized["summary"],
                    "data_quality": normalized["data_quality"],
                    "dashboard": {
                        "output": "dashboard/finance-review.json",
                        "analysis": finance_review["analysis"],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
