"""Built-in AIOps Skills."""
from app.modules.module8_ai.capabilities.alert_triage import ALERT_TRIAGE_SKILL
from app.modules.module8_ai.capabilities.config_risk import CONFIG_RISK_SKILL
from app.modules.module8_ai.capabilities.inspection import INSPECTION_SKILL

BUILTIN_SKILLS = [ALERT_TRIAGE_SKILL, CONFIG_RISK_SKILL, INSPECTION_SKILL]
