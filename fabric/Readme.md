# TRACE — Fabric Workspace Artifacts

This folder is the **Git integration root** for the Microsoft Fabric workspace. It contains all the definitions for Lakehouses, Data Warehouses, Semantic Models, Dashboards, and Notebooks.

## Folder Structure

- **`Dashboards.Report`**: Power BI report definition containing 5 stakeholder dashboards.
- **`NB01 - NB09... Notebook`**: PySpark notebooks covering ingestion (Bronze), cleaning and modeling (Silver), and data-quality checks (NB09).
- **`Pipeline_Realtime_Ingestion.DataPipeline`**: Scheduled Data Factory pipeline: every 10 minutes runs NB02, then `usp_load_vehicle_positions` in the warehouse.
- **`trace_env.Environment`**: Custom Python environment specifying `gtfs-realtime-bindings` and other pip packages.
- **`trace_lakehouse.Lakehouse`**: Bronze and Silver medallion delta tables.
- **`Trace_model.SemanticModel`**: Direct Lake semantic model with relationships and Row-Level Security (RLS) rules.
- **`trace_warehouse.Warehouse`**: Star schema tables, Gold views, and the load stored procedures.

## Deployment Instructions

To deploy these items to a new Fabric workspace:
1. Go to Workspace Settings -> **Git integration**.
2. Connect to the Azure DevOps or GitHub repository.
3. Set the **Git folder** to `/fabric`.
4. Click **Sync** to pull all artifacts into the workspace.