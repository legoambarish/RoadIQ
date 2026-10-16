from backend.scripts.demo_trained_pipeline import match_report, summarize_counts


def prediction(label, score, box):
    return {"model_label": label, "confidence": score,
            "bbox_xyxy_px": dict(zip(("x_min", "y_min", "x_max", "y_max"), box))}


def test_duplicate_predictions_cannot_double_count_one_ground_truth():
    row = {"boxes_xyxy_px": [[3, 10, 20, 30, 40]]}
    report = {"defects": [{"detections": [prediction("pothole", .9, [10, 20, 30, 40]),
                                          prediction("pothole", .7, [10, 20, 30, 40])]}]}
    assert match_report(row, report)["pothole"] == {"tp": 1, "fp": 1, "fn": 0}


def test_wrong_class_is_a_false_positive_and_missed_ground_truth():
    row = {"boxes_xyxy_px": [[3, 10, 20, 30, 40]]}
    result = match_report(row, {"defects": [{"detections": [prediction("alligator_crack", .9, [10, 20, 30, 40])]}]})
    assert result["pothole"] == {"tp": 0, "fp": 0, "fn": 1}
    assert result["alligator_crack"] == {"tp": 0, "fp": 1, "fn": 0}


def test_no_candidate_remains_a_miss_and_undefined_precision():
    result = match_report({"boxes_xyxy_px": [[3, 10, 20, 30, 40]]}, {"defects": []})
    assert summarize_counts([result["pothole"]]) == {"tp": 0, "fp": 0, "fn": 1, "precision": None, "recall": 0}
