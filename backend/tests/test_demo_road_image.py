import json

from scripts.demo_road_image import run_demo


def test_one_command_synthetic_demo_writes_annotation_and_structured_report(tmp_path) -> None:
    summary = run_demo(output_dir=tmp_path / "demo", seed=42)

    assert summary["analysis_status"] == "unrated"
    assert summary["synthetic_input"] is True
    assert summary["training_status"] == "untrained_baseline"
    assert summary["aggregate_count"] is None
    assert summary["candidate_area_ratio"] is not None
    assert (tmp_path / "demo" / "synthetic-road-demo.png").is_file()
    assert (tmp_path / "demo" / "annotated-preview.jpg").is_file()
    report = json.loads((tmp_path / "demo" / "analysis-report.json").read_text(encoding="utf-8"))
    assert report["annotated_image"]["value"].endswith("annotated-preview.jpg")
    assert report["aggregate_analysis"]["individual_particles_segmented"] is False


def test_one_command_demo_accepts_a_local_image(tmp_path) -> None:
    image_path = tmp_path / "owner-road-photo.png"
    run_demo(output_dir=tmp_path / "generated")
    image_path.write_bytes((tmp_path / "generated" / "synthetic-road-demo.png").read_bytes())

    summary = run_demo(output_dir=tmp_path / "photo-analysis", image_path=image_path)

    assert summary["synthetic_input"] is False
    assert summary["source_name"] == "owner-road-photo.png"
    assert summary["input_image"] == str(image_path)
    assert summary["annotated_image"] is not None
    assert summary["report"] is not None
