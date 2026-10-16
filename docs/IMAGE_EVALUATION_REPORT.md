# Image-analysis integration status

## Implemented integration

The integrated API provides `POST /api/v1/image-analyses`, which sends uploaded bytes to the Task C image-analysis service and passes explicit image-quality/surface observations to the Task A RSQI scorer. The dashboard can upload an image to the local backend and can still import a saved Task C CLI JSON report and annotation.

The integration does not infer asphalt when surface type is unknown, derive defect/aggregate components from generic pixel edges, invent normalization references, or calculate travel-mode scores. It does not send Task C's inline annotation data URI over HTTP.

## Current behavior and limits

The current Task C service reports unknown surface type, no supported RSQI component observations, and no adequate pavement-region decision. The default Task A scoring configuration also has no fixed normalization profiles. Therefore, a valid image upload currently returns an `unrated` RSQI with a null value and null mode-suitability fields.

The visible-defect score caps are implemented in Task A. They apply when the scorer receives complete, supported, normalized component evidence; they cannot produce a numeric score from the current Task C texture-candidate baseline. Do not interpret an unrated result as good or poor.

The API and dashboard changes are merged into `main` but are not yet part of a rebuilt packaged release. A Windows `.exe` build and runtime test have not been run for this integration.

## Verification

- `PYTHONPATH=backend PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/roadiq-latest-main-venv/bin/python -m pytest -q backend/tests/test_image_analysis.py backend/tests/test_scoring.py` — 59 passed; two dependency deprecation warnings.
- From `frontend/`, `npm run build` — TypeScript and Vite production build passed.

These checks verify the route and scorer boundary, including that a valid normalized visible-defect component at 25.0 returns a capped score of 30.0 through the route. The test uses an injected test-only normalization profile; it does not demonstrate a rated score from a real road image.

## Work needed for a rated image result

1. Agree and implement Task C outputs for all required RSQI components, surface classification, and usable-region adequacy.
2. Obtain reviewed fixed normalization references and evaluate them on a grouped, held-out RoadIQ dataset.
3. Agree and implement mode-suitability evidence/formulas separately from RSQI.
4. Review the API response and dashboard changes with affected Task A/B/C owners.
5. Rebuild and smoke-test the Windows package on Windows with the merged integration.
