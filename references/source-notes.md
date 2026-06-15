# Source Notes

This skill is an original lightweight orchestration skill. It does not vendor code from the researched repositories.

## Learned Patterns

- `6tail/lunar-python`: use a deterministic calendar library for Bazi, solar/lunar conversion, jieqi-aware ganzhi, ten gods, nayin, and luck cycles.
- `SylarLong/iztro` / `spyfree/iztro-py`: use a dedicated Ziwei engine instead of asking the model to place stars.
- `gaoxin492/bazi-skill`: useful agent-skill pattern: collect naturally, repair dependencies, calculate in Python, then archive/interpret.
- `Sudo-Biao/suangua`: useful product pattern: separate calculation layer, schema validation, API/LLM interpretation, and classical reference retrieval.
- `jinchenma94/bazi-skill`: useful prompt workflow, but avoid its weakness: do not let the LLM hand-calculate pillars.

## Dependency Policy

- Prefer runtime dependencies from package managers over copied code.
- `lunar-python` is the preferred Bazi backend.
- `iztro-py` is the preferred Ziwei Python backend for this first version.
- Keep Liuyao and Xiao Liuren scripts transparent. Liuyao includes hexagram body, moving lines, changed hexagram, na-jia, six kin, and six spirits; full yongshen, shi/ying, fu-shen, and school-specific palace rules still need human/LLM interpretation.

## Accuracy Boundary

- Bazi and Ziwei results are only as reliable as the installed calculation libraries and input precision.
- Bazi supports approximate true solar time with `--longitude --true-solar`; it uses longitude correction plus an equation-of-time approximation. For high-stakes or boundary cases, verify with a specialist ephemeris.
- Jieqi and zi-hour boundary warnings are emitted when detectable.
- Ziwei current decadal palace is auto-located by nominal age and should be treated as a coarse stage marker.
- Liuyao and Xiao Liuren are framework outputs, not full traditional judgments.
