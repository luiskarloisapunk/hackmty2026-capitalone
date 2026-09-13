---
name: project-treasury-model
description: Módulo matemático de tesorería predictiva implementado para HackMTY 2026 Capital One
metadata:
  type: project
---

Motor predictivo AR(p) + interés compuesto implementado en `backend/app/modelo/`.

**Why:** El equipo necesitaba el modelo matemático para la categoría SMB Cash-Flow & Working Capital Intelligence (B2B). Luis es el responsable del modelo en Python.

**Archivos creados:**
- `backend/app/modelo/simulator.py` — Generador de transacciones sintéticas tipo Nessie (coseno + ruido gaussiano)
- `backend/app/modelo/engine.py` — `CashFlowEngine` AR(p): matriz de Hankel via as_strided, lstsq/SVD, predicción sliding window
- `backend/app/modelo/advisor.py` — `WorkingCapitalAdvisor`: fórmula de interés compuesto P = D / (1+r/n)^(nt)
- `backend/app/routers/treasury.py` — Router FastAPI: `GET /api/treasury/simulate` + `POST /api/treasury/analyze`

**How to apply:** Al añadir funcionalidad al modelo, mantener la separación simulator/engine/advisor. El router es la capa de integración con FastAPI.
