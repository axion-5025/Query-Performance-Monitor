# Query Performance Monitor

A database performance monitoring and analysis application built using **FastAPI, Streamlit, and SQLite**.

The project is designed to help developers monitor SQL query performance, detect performance regressions, compare execution plans, investigate possible root causes, analyze indexes, recommend optimizations, and validate whether an optimization actually improved performance.

---

## Project Objective

A slow database query alone does not provide enough information.

When query performance changes, developers normally need to answer questions such as:

- Which query is slow?
- How much slower is it compared with the previous execution?
- Is the slowdown temporary or a real regression?
- Did the execution plan change?
- Was an index removed or ignored?
- Did the data size or statistics change?
- Can an index improve the query?
- Did the applied optimization actually improve performance?

The **Query Performance Monitor** brings these checks into one application.

---

## Main Workflow

The project follows this performance-analysis lifecycle:

**Monitor → Detect → Compare → Diagnose → Recommend → Validate**

### 1. Monitor
Record and display query-performance information.

### 2. Detect
Identify significant performance regressions using historical or before/after measurements.

### 3. Compare
Compare execution plans and performance metrics.

### 4. Diagnose
Identify possible reasons for a slowdown.

### 5. Recommend
Analyze indexes and identify possible optimization opportunities.

### 6. Validate
Check whether the applied optimization actually improved performance.

---

## Main Features

### Query Performance Monitoring

The system can monitor and record different SQL query scenarios including:

- Normal SELECT queries
- WHERE conditions
- JOIN queries
- ORDER BY queries
- GROUP BY queries
- Fast queries
- Slow queries
- Repeated executions
- Large-processing queries
- Query history

The dashboard displays information such as:

- Total Queries
- Average Execution Time
- Fastest Query
- Slowest Query
- Query Execution Trend
- Query Status
- Top Time-Consuming Queries

---

## Performance Regression Detection

The system compares old and current query performance and determines whether the change represents a meaningful regression.

It supports:

- No performance change
- Small performance variations
- Significant slowdown
- Threshold-based regression detection
- Sudden slowdown
- Gradual slowdown
- Performance improvement
- Multiple executions
- Historical baseline comparison
- Multiple-query comparison
- Temporary performance spikes

Example:

```text
Old execution time: 100 ms
New execution time: 350 ms
Performance ratio: 3.5
Result: Regression detected