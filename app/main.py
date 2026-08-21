from fastapi import FastAPI, HTTPException
from database.database import engine, Base, SessionLocal, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from statistics import median
import re
import time

app = FastAPI()

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

# Create database tables



# =========================
# PYDANTIC MODEL
# =========================

class QueryCreate(BaseModel):
    query_text: str = Field(..., min_length=3, max_length=5000)
    execution_time: float | None = None
class RegressionCheck(BaseModel):
    query_name: str = "Q1"
    historical_query_text: str = ""
    current_query_text: str = ""
    execution_failed: bool = False
    permission_denied: bool = False
    data_size_changed: bool = False
    planner_setting_changed: bool = False
    statistics_refreshed: bool = False
    index_recreated: bool = False
    index_created_during_observation: bool = False
    multiple_indexes_added: bool = False
    index_dropped_during_observation: bool = False
    schema_changed: bool = False
    plan_parse_error: bool = False
    no_identifiable_cause: bool = False
    runtime_resource_issue: bool = False
    cache_conditions_changed: bool = False
    concurrent_workload_changed: bool = False
    plan_change_count: int = Field(default=0, ge=0)
    improvement_threshold: float = Field(default=0.10, ge=0, lt=1)
    old_planning_time: float = 0
    new_planning_time: float = 0
    old_query_plan: str = ""
    new_query_plan: str = "" 
    old_estimated_cost: float = 0
    new_estimated_cost: float = 0 
    old_estimated_rows: int = 0
    new_estimated_rows: int = 0  
    old_actual_rows: int = 0
    new_actual_rows: int = 0
    old_join_method: str = ""
    new_join_method: str = ""
    old_join_order: str = ""
    new_join_order: str = ""
    old_has_sort: bool = False
    new_has_sort: bool = False
    old_filter: str = ""
    new_filter: str = ""
    old_scan_method: str = ""
    new_scan_method: str = ""
    old_plan_nodes: list[str] = Field(default_factory=list)
    new_plan_nodes: list[str] = Field(default_factory=list)
    old_execution_time: float | None = Field(default=None, ge=0)
    new_execution_time: float | None = Field(default=None, ge=0)
    regression_threshold: float = Field(
        default=2.0,
        gt=0,
    )
class RegressionHistoryCheck(BaseModel):
    old_execution_times: list[float]
    new_execution_times: list[float]
    regression_threshold: float = Field(
        default=2.0,
        gt=0,
    )  
    baseline_age_days: int = 0
    baseline_max_age_days: int | None = None  
@app.post("/regression-check")
def regression_check(data: RegressionCheck):

    old_time = data.old_execution_time
    new_time = data.new_execution_time
    threshold = data.regression_threshold 
    if old_time is None:
        return {
            "query_name": data.query_name,
            "comparison_available": False,
            "improvement_detected": None,
            "regression_detected": None,
            "result": "Cannot calculate improvement - before execution missing"
        }
    if new_time is None:
        return {
            "query_name": data.query_name,
            "comparison_available": False,
            "improvement_detected": None,
            "regression_detected": None,
            "result": "Cannot validate optimization - after execution missing"
        }    
    if data.permission_denied:
        return {
        "query_name": data.query_name,
        "plan_comparison_available": False,
        "plan_changed": None,
        "result": "Permission denied while obtaining execution plan"
    }
    if data.plan_parse_error:
        return {
            "query_name": data.query_name,
            "plan_comparison_available": False,
            "plan_changed": None,
            "regression_detected": None,
            "result": "Plan parsing error"
        }    
    if not data.old_query_plan.strip() and not data.new_query_plan.strip():
        return {
            "query_name": data.query_name,
            "plan_comparison_available": False,
            "plan_changed": None,
            "result": "Invalid or missing plan"
        } 
    if not data.old_query_plan.strip() and data.new_query_plan.strip():
        return {
            "query_name": data.query_name,
            "plan_comparison_available": False,
            "plan_changed": None,
            "result": "No baseline plan"
        } 
    if data.old_query_plan.strip() and not data.new_query_plan.strip():
        return {
            "query_name": data.query_name,
            "plan_comparison_available": False,
            "plan_changed": None,
            "result": "Current plan unavailable"
        } 
          
    if data.execution_failed:
        return {
        "query_name": data.query_name,
        "execution_failed": True,
        "regression_detected": None,
        "result": "Execution failed - not classified as performance regression"
    }
    historical_fingerprint = re.sub(r"'[^']*'|\b\d+(?:\.\d+)?\b", "?", data.historical_query_text.strip().lower())
    current_fingerprint = re.sub(r"'[^']*'|\b\d+(?:\.\d+)?\b", "?", data.current_query_text.strip().lower()) 
     
    if (
       data.historical_query_text
       and data.current_query_text
       and historical_fingerprint != current_fingerprint
):
     return {
        "query_name": data.query_name,
        "query_changed": True,
        "regression_detected": None,
        "result": "Different query/version - regression comparison not applied"
    }

    performance_ratio = (
        new_time / old_time
        if old_time > 0
        else 1.0
    )

    regression_detected = (
        performance_ratio >= threshold
    )

    improvement_detected = (
    old_time > 0
    and new_time <= old_time * (1 - data.improvement_threshold)
    )
    comparison_fair = not (
    data.cache_conditions_changed
    or data.data_size_changed
    or data.concurrent_workload_changed
)
    if not comparison_fair:
     improvement_detected = False
    slowdown_percent = (
      ((new_time - old_time) / old_time) * 100
    if old_time > 0
    else 0
)
    improvement_percent = (
    ((old_time - new_time) / old_time) * 100
    if old_time > 0 and new_time < old_time
    else 0
)
    improvement_level = (
    "high"
    if improvement_percent >= 50
    else "significant"
    if improvement_detected
    else "insignificant"
)
    planning_improvement_percent = (
    ((data.old_planning_time - data.new_planning_time) / data.old_planning_time) * 100
    if data.old_planning_time > 0 and data.new_planning_time < data.old_planning_time
    else 0
)

    planning_improvement_detected = (
    data.old_planning_time > 0
    and data.new_planning_time
    <= data.old_planning_time * (1 - data.improvement_threshold)
)
    recommendation_status = (
    "successful"
    if data.index_created_during_observation and improvement_detected
    else "unsuccessful"
    if data.index_created_during_observation and not improvement_detected
    else "not_applicable"
)
    individual_index_benefit_isolated = not data.multiple_indexes_added

    index_attribution_note = (
    "Cannot isolate individual index benefit"
    if data.multiple_indexes_added
    else None
)
    recommendation_action = (
    "Rollback recommendation or investigate further"
    if recommendation_status == "unsuccessful"
    else None
)
    plan_changed = data.old_query_plan != data.new_query_plan
    cost_difference = (
    data.new_estimated_cost - data.old_estimated_cost
)
    rows_difference = (
    data.new_estimated_rows - data.old_estimated_rows
)
    actual_rows_difference = (
    data.new_actual_rows - data.old_actual_rows
)  
    join_method_changed = (
    data.old_join_method != data.new_join_method
) 
    join_order_changed = (
    data.old_join_order != data.new_join_order
)
    sort_added = (
    not data.old_has_sort
    and data.new_has_sort
)
    sort_removed = (
    data.old_has_sort
    and not data.new_has_sort
)
    filter_changed = (
    data.old_filter != data.new_filter
)
    scan_method_changed = (
    data.old_scan_method != data.new_scan_method
)
    added_plan_nodes = [
    node
    for node in data.new_plan_nodes
    if node not in data.old_plan_nodes
]
    removed_plan_nodes = [
    node
    for node in data.old_plan_nodes
    if node not in data.new_plan_nodes
]
    regression_causes = []

    if data.data_size_changed:
        regression_causes.append("Data size changed")
    if data.planner_setting_changed:
        regression_causes.append("Query planner configuration changed")
    if data.statistics_refreshed:
        regression_causes.append("Statistics refreshed / ANALYZE event")
    if data.index_recreated:
        regression_causes.append("Index recreated / lifecycle event")
    if data.index_created_during_observation:
        regression_causes.append("Index created during observation")
    if data.index_dropped_during_observation:
        regression_causes.append("Index dropped during observation")
    if data.schema_changed:
        regression_causes.append("Schema change detected")
    if data.runtime_resource_issue:
        regression_causes.append("Runtime/resource issue")    
    if (
        data.new_estimated_rows > 0
        and (
            data.new_actual_rows >= data.new_estimated_rows * 10
            or data.new_estimated_rows >= data.new_actual_rows * 10
        )
    ):
        regression_causes.append("Statistics/cardinality estimation issue")
    if (
        data.old_scan_method.lower() == "index scan"
        and data.new_scan_method.lower() == "seq scan"
    ):
        regression_causes.append("Index removed / sequential scan introduced")  
    if (
        data.old_join_method != data.new_join_method
        and data.new_join_method.lower() == "nested loop"
    ):
        regression_causes.append("Expensive join introduced") 
    if not data.old_has_sort and data.new_has_sort:
        regression_causes.append("Expensive sort introduced") 
    if data.no_identifiable_cause and len(regression_causes) == 0:
        regression_cause = "Root cause undetermined"
    elif len(regression_causes) > 1:
        regression_cause = "Multiple possible causes: " + "; ".join(regression_causes)
    elif len(regression_causes) == 1:
        regression_cause = regression_causes[0]
    else:
        regression_cause = "Insufficient / uncertain evidence"                
    return {
        "query_name": data.query_name,
        "old_query_plan": data.old_query_plan,
        "new_query_plan": data.new_query_plan,
        "plan_changed": plan_changed,
        "plan_instability": data.plan_change_count >= 3,
        "old_estimated_cost": data.old_estimated_cost,
        "new_estimated_cost": data.new_estimated_cost,
        "cost_difference": cost_difference,
        "old_estimated_rows": data.old_estimated_rows,
        "new_estimated_rows": data.new_estimated_rows,
        "rows_difference": rows_difference,
        "old_actual_rows": data.old_actual_rows,
        "new_actual_rows": data.new_actual_rows,
        "actual_rows_difference": actual_rows_difference,
        "old_join_method": data.old_join_method,
        "new_join_method": data.new_join_method,
        "join_method_changed": join_method_changed,
        "old_join_order": data.old_join_order,
        "new_join_order": data.new_join_order,
        "join_order_changed": join_order_changed,
        "old_has_sort": data.old_has_sort,
        "new_has_sort": data.new_has_sort,
        "sort_added": sort_added,
        "sort_removed": sort_removed, 
        "old_filter": data.old_filter,
        "new_filter": data.new_filter,
        "filter_changed": filter_changed, 
        "old_scan_method": data.old_scan_method,
        "new_scan_method": data.new_scan_method,
        "scan_method_changed": scan_method_changed, 
        "added_plan_nodes": added_plan_nodes,
        "removed_plan_nodes": removed_plan_nodes,
        "regression_cause": regression_cause,
        "root_cause_confidence": (
            "high"
            if regression_detected and len(regression_causes) == 1
            else "medium"
            if regression_detected and len(regression_causes) > 1
            else "low"
        ),
        "old_execution_time": old_time,
        "new_execution_time": new_time,
        "slowdown_percent": slowdown_percent,
        "improvement_percent": improvement_percent,
        "improvement_level": improvement_level,
        "recommendation_status": recommendation_status,
        "individual_index_benefit_isolated": individual_index_benefit_isolated,
        "index_attribution_note": index_attribution_note,
        "comparison_fair": comparison_fair,
        "cache_conditions_changed": data.cache_conditions_changed,
        "recommendation_action": recommendation_action,
        "old_planning_time": data.old_planning_time,
        "new_planning_time": data.new_planning_time,
        "planning_improvement_percent": planning_improvement_percent,
        "planning_improvement_detected": planning_improvement_detected,
        "regression_threshold": threshold,
        "performance_ratio": performance_ratio,
        "regression_detected": regression_detected,
        "improvement_detected": improvement_detected,
        "result": (
            "Regression detected"
            if regression_detected
            else "No regression"
        )
    }
class QueryRegressionInput(BaseModel):
    query_name: str
    old_execution_time: float = Field(..., ge=0)
    new_execution_time: float | None = Field(default=None, ge=0)


class MultipleQueryRegressionCheck(BaseModel):
    queries: list[QueryRegressionInput]
    regression_threshold: float = Field(
        default=2.0,
        gt=0,
    )   
@app.post("/regression-history-check")
def regression_history_check(data: RegressionHistoryCheck):

    if not data.old_execution_times:
        baseline = (
            sum(data.new_execution_times) / len(data.new_execution_times)
        )

        return {
            "baseline_created": True,
            "baseline": baseline,
            "regression_detected": False,
            "result": "No regression - baseline created"
        }
    if not data.new_execution_times:
       return {
        "current_measurement_available": False,
        "regression_detected": None,
        "result": "No regression decision - current measurement unavailable"
    }
    new_average_for_variance = (
    sum(data.new_execution_times) / len(data.new_execution_times)
)
    new_variance_ratio = (
    (max(data.new_execution_times) - min(data.new_execution_times))
    / new_average_for_variance
    if new_average_for_variance > 0
    else 0
)
    unstable_measurement = (
    len(data.new_execution_times) >= 3
    and new_variance_ratio >= 1.0
)
    if (
        data.baseline_max_age_days is not None
        and data.baseline_age_days > data.baseline_max_age_days
    ):
        new_baseline = (
            sum(data.new_execution_times)
            / len(data.new_execution_times)
        )

        return {
            "baseline_stale": True,
            "baseline_created": True,
            "baseline": new_baseline,
            "regression_detected": False,
            "result": "No regression decision - stale baseline replaced"
        }   
    old_avg = (
        sum(data.old_execution_times)
        / len(data.old_execution_times)
    )

    new_avg = (
        sum(data.new_execution_times)
        / len(data.new_execution_times)
    )
    old_median = median(data.old_execution_times)
    new_median = median(data.new_execution_times)

    median_ratio = (
    new_median / old_median
    if old_median > 0
    else 1.0
)
    performance_ratio = median_ratio
    
    regression_detected = (
        performance_ratio >= data.regression_threshold
    )

    return {
        "old_average": old_avg,
        "new_average": new_avg,
        "new_variance_ratio": new_variance_ratio,
        "unstable_measurement": unstable_measurement,
        "regression_threshold": data.regression_threshold,
        "performance_ratio": performance_ratio,
        "regression_detected": regression_detected,
        "result": (
            "Regression detected"
            if regression_detected
            else "No regression"
        )
    }
@app.post("/multiple-regression-check")
def multiple_regression_check(data: MultipleQueryRegressionCheck):

    results = []

    for query in data.queries:

        ratio = (
            query.new_execution_time / query.old_execution_time
            if query.old_execution_time > 0
            else 1.0
        )

        detected = (
            ratio >= data.regression_threshold
        )

        results.append({
            "query_name": query.query_name,
            "performance_ratio": ratio,
            "regression_detected": detected
        })

    return {
    "results": results,
    "workload_wide_improvement": sum(
    1 for item in results if item["performance_ratio"] < 1.0
) >= 2,
"workload_improvement_reason": (
    "Multiple queries improved together - broader workload improvement"
    if sum(1 for item in results if item["performance_ratio"] < 1.0) >= 2
    else None
),
    "shared_cause_investigation_required": sum(
        1 for item in results if item["regression_detected"]
    ) >= 2,
    "shared_cause_reason": (
        "Multiple queries regressed together - investigate shared/environmental cause"
        if sum(1 for item in results if item["regression_detected"]) >= 2
        else None
    )
}  
# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {
        "message": "API is working!"
    }


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================
# DATABASE TEST
# =========================

@app.get("/database-test")
def database_test(username: str, password: str):

    if username != "admin" or password != "admin123":
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    try:
        with engine.connect():
            return {
                "status": "success",
                "message": "Database connected successfully!"
            }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

# =========================
# CREATE QUERY
# =========================

@app.post("/queries")
def create_query(data: QueryCreate):

    query_text = data.query_text.strip()

    if not query_text:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    allowed = (
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "WITH"
    )

    normalized_query = query_text.lstrip().upper()

    if not normalized_query.startswith(allowed):
        raise HTTPException(
            status_code=400,
            detail="Only SQL queries are allowed"
        )

    db = SessionLocal()

    try:
        new_query = Query(
            query_text=query_text,
            execution_time=data.execution_time
        )

        db.add(new_query)
        db.commit()
        db.refresh(new_query)

        return {
            "id": new_query.id,
            "query_text": new_query.query_text,
            "execution_time": new_query.execution_time
        }

    except Exception:
        db.rollback()

        raise HTTPException(
        status_code=503,
        detail="Database unavailable"
    )
    finally:
        db.close()


# =========================
# GET ALL QUERIES
# =========================

@app.get("/queries")
def get_queries():

    db = SessionLocal()

    try:
        queries = (
            db.query(Query)
            .order_by(Query.id.desc())
            .all()
        )

        return [
            {
                "id": query.id,
                "query_text": query.query_text,
                "execution_time": query.execution_time
            }
            for query in queries
        ]
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
    finally:
        db.close()


# =========================
# QUERY STATS
# =========================

@app.get("/queries/stats")
def query_stats():

    db = SessionLocal()

    try:
        total_queries = (
            db.query(func.count(Query.id))
            .scalar()
            or 0
        )

        if total_queries == 0:
            return {
                "total_queries": 0,
                "average_execution_time": 0,
                "fastest_query": None,
                "slowest_query": None
            }

        average_time = (
            db.query(func.avg(Query.execution_time))
            .filter(
                Query.execution_time.isnot(None)
            )
            .scalar()
        )

        fastest = (
            db.query(Query)
            .filter(
                Query.execution_time.isnot(None)
            )
            .order_by(
                Query.execution_time.asc()
            )
            .first()
        )

        slowest = (
            db.query(Query)
            .filter(
                Query.execution_time.isnot(None)
            )
            .order_by(
                Query.execution_time.desc()
            )
            .first()
        )

        return {
            "total_queries": total_queries,

            "average_execution_time": round(
                float(average_time or 0),
                6
            ),

            "fastest_query": (
                {
                    "id": fastest.id,
                    "query_text": fastest.query_text,
                    "execution_time": fastest.execution_time
                }
                if fastest else None
            ),

            "slowest_query": (
                {
                    "id": slowest.id,
                    "query_text": slowest.query_text,
                    "execution_time": slowest.execution_time
                }
                if slowest else None
            )
        }

    finally:
        db.close()


# =========================
# GET QUERY BY ID
# =========================

@app.get("/queries/{query_id}")
def get_query(query_id: int):

    db = SessionLocal()

    try:
        query = (
            db.query(Query)
            .filter(Query.id == query_id)
            .first()
        )

        if query is None:
            raise HTTPException(
                status_code=404,
                detail="Query not found"
            )

        return {
            "id": query.id,
            "query_text": query.query_text,
            "execution_time": query.execution_time
        }

    finally:
        db.close()


# =========================
# UPDATE QUERY
# =========================

@app.put("/queries/{query_id}")
def update_query(
    query_id: int,
    data: QueryCreate
):

    db = SessionLocal()

    try:
        query_text = data.query_text.strip()

        if not query_text:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        allowed = (
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "WITH"
        )

        if not query_text.upper().startswith(allowed):
            raise HTTPException(
                status_code=400,
                detail="Only SQL queries are allowed"
            )

        query = (
            db.query(Query)
            .filter(Query.id == query_id)
            .first()
        )

        if query is None:
            raise HTTPException(
                status_code=404,
                detail="Query not found"
            )

        query.query_text = query_text

        if data.execution_time is not None:
            query.execution_time = data.execution_time

        db.commit()
        db.refresh(query)

        return {
            "id": query.id,
            "query_text": query.query_text,
            "execution_time": query.execution_time
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


# =========================
# DELETE QUERY
# =========================

@app.delete("/queries/{query_id}")
def delete_query(query_id: int):

    db = SessionLocal()

    try:
        query = (
            db.query(Query)
            .filter(Query.id == query_id)
            .first()
        )

        if query is None:
            raise HTTPException(
                status_code=404,
                detail="Query not found"
            )

        db.delete(query)
        db.commit()

        return {
            "status": "success",
            "message": "Query deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()
        
class IndexAnalysisInput(BaseModel):
    table_name: str
    indexes: list[str] = Field(default_factory=list)
    used_indexes: list[str] = Field(default_factory=list) 
    usage_count: int = Field(default=0, ge=0)
    usage_stats_available: bool = True
    observation_days: int = Field(default=30, ge=0)
    minimum_observation_days: int = Field(default=7, ge=0)
    duplicate_indexes: list[str] = Field(default_factory=list)
    similar_indexes: list[str] = Field(default_factory=list)
    index_columns: list[str] = Field(default_factory=list)
    previous_index_columns: list[str] = Field(default_factory=list)
    query_columns: list[str] = Field(default_factory=list)
    filter_columns: list[str] = Field(default_factory=list)
    join_columns: list[str] = Field(default_factory=list)
    order_by_columns: list[str] = Field(default_factory=list)
    execution_plan: str = ""
    index_created: bool = False
    index_deleted: bool = False
    table_dropped: bool = False
    metadata_error: bool = False
    metadata_permission_denied: bool = False
    before_used_indexes: list[str] = Field(default_factory=list)
    after_used_indexes: list[str] = Field(default_factory=list)
    table_row_count: int = Field(default=0, ge=0)
    result_row_count: int = Field(default=0, ge=0)
    query_execution_count: int = Field(default=0, ge=0)
    query_slow: bool = False
    supporting_queries: list[str] = Field(default_factory=list)
    stable_predicate: str = ""
    column_exists: bool = True
    table_column_count: int = Field(default=0, ge=0)
    expression_index_candidate: str = ""
    expression_index_supported: bool = False
    unique_constraint_covers_access: bool = False
    query_template: str = ""
    query_fingerprint: str = ""
    stale_recommendation: bool = False
    excessive_write_overhead: bool = False
    negative_workload_impact: bool = False
    recommendation_score: float = Field(default=0, ge=0)
    recommendation_threshold: float = Field(default=0, ge=0)
    index_size_mb: float = Field(default=0, ge=0)
    bloat_measurement_available: bool = False
    index_bloat_percent: float = Field(default=0, ge=0)
    regression_detected: bool = False
    index_details: list[dict] = Field(default_factory=list)
        
@app.post("/index-analysis")
def index_analysis(data: IndexAnalysisInput):
    identifiers_safe = data.table_name.replace("_", "").isalnum() and all(col.replace("_", "").isalnum() for col in data.filter_columns + data.join_columns + data.order_by_columns)
    return {
    "table_name": data.table_name,
    "index_count": len(data.indexes),
    "indexes": data.indexes,
    "used_indexes": data.used_indexes,
    "index_used": len(data.used_indexes) > 0,
    "usage_level": "unknown" if not data.usage_stats_available else ("high" if data.usage_count >= 10 else "low"),
    "observation_days": data.observation_days,
    "insufficient_observation_period": data.observation_days < data.minimum_observation_days,
    "duplicate_indexes": data.duplicate_indexes,
    "has_duplicate_indexes": len(data.duplicate_indexes) > 0,
    "similar_indexes": data.similar_indexes,
    "has_similar_indexes": len(data.similar_indexes) > 0,
    "index_columns": data.index_columns,
    "previous_index_columns": data.previous_index_columns,
    "metadata_refreshed": data.previous_index_columns != data.index_columns,
    "index_type": "single-column" if len(data.index_columns) == 1 else "composite",
    "query_columns": data.query_columns,
    "leading_column_match": bool(data.index_columns and data.query_columns and data.query_columns[0] == data.index_columns[0]),
    "filter_columns": data.filter_columns,
    "filter_index_relevant": any(col in data.index_columns for col in data.filter_columns),
    "join_columns": data.join_columns,
    "join_index_relevant": any(col in data.index_columns for col in data.join_columns),
    "order_by_columns": data.order_by_columns,
    "order_by_index_relevant": any(col in data.index_columns for col in data.order_by_columns),
    "execution_plan": data.execution_plan,
    "index_created": data.index_created,
    "index_deleted": data.index_deleted,
    "table_dropped": data.table_dropped,
    "table_status": "missing" if data.table_dropped else "available",
    "metadata_error": data.metadata_error,
    "metadata_status": "collection error" if data.metadata_error else "available",
    "metadata_permission_denied": data.metadata_permission_denied,
    "permission_status": "permission denied" if data.metadata_permission_denied else "allowed",
    "before_used_indexes": data.before_used_indexes,
    "after_used_indexes": data.after_used_indexes,
    "index_usage_changed": data.before_used_indexes != data.after_used_indexes,
    "table_row_count": data.table_row_count,
    "result_row_count": data.result_row_count,
    "selective_filter": data.table_row_count > 0 and data.result_row_count * 10 <= data.table_row_count,
    "large_table": data.table_row_count >= 100000,
    "wide_table": data.table_column_count >= 100,
    "analysis_scope": "reduced" if data.table_column_count >= 100 else "normal",
    "index_size_mb": data.index_size_mb,
    "large_index": data.index_size_mb >= 1024,
    "index_bloat_percent": data.index_bloat_percent,
    "index_bloat_flagged": data.bloat_measurement_available and data.index_bloat_percent >= 30,
    "index_usage_investigation_required": len(data.indexes) > 0 and "SEQ SCAN" in data.execution_plan.upper() and len(data.used_indexes) == 0,
    "index_details": data.index_details,
    "multiple_indexes": len(data.indexes) > 1,
    "unused_indexes": [] if (not data.usage_stats_available or data.observation_days < data.minimum_observation_days) else [idx for idx in data.indexes if idx not in data.used_indexes],
    "report_generated": True,
    "index_regression_relevant": data.regression_detected and data.index_deleted,
    "candidate_missing_index": not data.stale_recommendation and identifiers_safe and not data.metadata_error and not data.table_dropped and data.column_exists and not data.unique_constraint_covers_access and (not data.expression_index_candidate or data.expression_index_supported) and data.recommendation_score >= data.recommendation_threshold and (data.table_row_count == 0 or data.result_row_count * 10 <= data.table_row_count) and len(data.indexes) == 0 and bool(data.filter_columns or data.join_columns or data.order_by_columns),
    "recommended_index_columns": [] if (data.stale_recommendation or not identifiers_safe or (data.expression_index_candidate and not data.expression_index_supported) or data.unique_constraint_covers_access or data.metadata_error or not data.column_exists or data.table_dropped or data.recommendation_score < data.recommendation_threshold or (data.table_row_count > 0 and data.result_row_count * 10 > data.table_row_count) or (data.indexes and data.index_columns and list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)) == data.index_columns[:len(list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)))])) else list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)),
    "ranked_recommendation_columns": [] if not data.column_exists else sorted(
    set(data.filter_columns + data.join_columns + data.order_by_columns),
    key=lambda col: -(
        (3 if col in data.filter_columns else 0)
        + (2 if col in data.join_columns else 0)
        + (1 if col in data.order_by_columns else 0)
    )
),
    "recommendation_scores": {
    col: (3 if col in data.filter_columns else 0)
       + (2 if col in data.join_columns else 0)
       + (1 if col in data.order_by_columns else 0)
    for col in set(data.filter_columns + data.join_columns + data.order_by_columns)
},
    "recommendation_priority": "high" if data.query_slow and data.query_execution_count >= 10 else ("low" if data.query_slow and data.query_execution_count > 0 else "normal"),
    "supporting_queries": data.supporting_queries,
    "supporting_query_count": len(data.supporting_queries),
    "query_template": data.query_template,
    "query_fingerprint": data.query_fingerprint,
    "query_identity": data.query_fingerprint if data.query_fingerprint else data.query_template,
    "recommendation_revalidation_required": data.stale_recommendation,
    "write_overhead_tradeoff": data.excessive_write_overhead,
    "workload_impact_tradeoff": data.negative_workload_impact,
    "recommendation_reason": "Index candidate supported by query filter/join/order-by evidence" if (data.filter_columns or data.join_columns or data.order_by_columns) else "No index recommendation evidence",
    "recommendation_evidence": list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)),
    "recommendation_sql": f"CREATE INDEX idx_{data.table_name}_{'_'.join(list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)))} ON {data.table_name} ({', '.join(list(dict.fromkeys(data.filter_columns + data.join_columns + data.order_by_columns)))});" if not data.stale_recommendation and identifiers_safe and (not data.expression_index_candidate or data.expression_index_supported) and not data.unique_constraint_covers_access and not data.metadata_error and not data.table_dropped and data.column_exists and data.recommendation_score >= data.recommendation_threshold and (data.table_row_count == 0 or data.result_row_count * 10 <= data.table_row_count) and len(data.indexes) == 0 and bool(data.filter_columns or data.join_columns or data.order_by_columns) else None,
    "partial_index_candidate": bool(data.stable_predicate and data.query_execution_count >= 10),
    "partial_index_predicate": data.stable_predicate,
    "expression_index_candidate": bool(data.expression_index_candidate and data.expression_index_supported),
    "expression_index_expression": data.expression_index_candidate if data.expression_index_supported else "",
    "index_scan_detected": "INDEX SCAN" in data.execution_plan.upper(),
    "bitmap_index_scan_detected": "BITMAP INDEX SCAN" in data.execution_plan.upper(),
    "index_only_scan_detected": "INDEX ONLY SCAN" in data.execution_plan.upper(),
    "sequential_scan_detected": "SEQ SCAN" in data.execution_plan.upper() or "SEQUENTIAL SCAN" in data.execution_plan.upper(),
    "index_not_chosen": data.usage_stats_available and data.observation_days >= data.minimum_observation_days and len(data.indexes) > 0 and len(data.used_indexes) == 0,
    "index_exists": len(data.indexes) > 0
}     
