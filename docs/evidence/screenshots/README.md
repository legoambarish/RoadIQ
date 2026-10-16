# Actual browser checks

Unedited screenshots from the local evaluated-model application, normal Chromium viewport 1280x720. These show actual backend observations, not a rendered mock. Detailed checks and scope are recorded in `../browser-verification.json`.

Road photographs India_006160 and India_001993 are from **RDD2022 India**, by Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal and Yoshihide Sekimoto. Source: https://figshare.com/articles/dataset/21431547 ; licence: https://creativecommons.org/licenses/by/4.0/ . The screenshots add RoadIQ's interface, predicted boxes and optional predicted masks. Predictions are modifications, not source ground truth or an endorsement by the dataset authors. The black input is a generated plumbing control.

The damaged example has one source-matched alligator box **and one missed source pothole**. Experimental masks visibly fail on parts of this image, including sky/vegetation; their quality warning is retained. The no-supported-source-box example is not a certified healthy road. The surrounding map records remain explicitly labelled fixtures.

- `everyday-genuine-detection.jpg`: actual candidate and localized inspection prompts.
- `engineer-genuine-masks.jpg`: optional diagnostic masks; visible failure is not hidden.
- `engineer-reliability-limits.jpg`: failed-mask warning, known detector AP, source coordinates and null physical/ranking evidence.
- `no-supported-source-boxes-challenge.jpg`: no detection is distinct from healthy.
- `unsuitable-synthetic-control.jpg`: unusable input receives no condition grade.
