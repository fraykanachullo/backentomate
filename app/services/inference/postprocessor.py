from app.services.inference.class_names import CLASS_NAMES, get_metadata

def severity_from_confidence(conf: float) -> str:
    if conf < 0.55:
        return "MILD"
    elif conf <= 0.75:
        return "MODERATE"
    else:
        return "SEVERE"

def build_detections(results, width: int, height: int, conf_thres: float = 0.40):
    """
    Convierte results de Ultralytics a lista de dicts normalizados.
    results: ultralytics YOLO results (uno por imagen)
    width, height: dimensiones originales
    """
    detections = []
    for r in results:
        boxes = r.boxes
        if boxes is None:
            continue
        for box in boxes:
            conf = float(box.conf[0])
            if conf < conf_thres:
                continue
            class_id = int(box.cls[0])
            label = CLASS_NAMES.get(class_id, f"class_{class_id}")
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            # Normalizar a [0,1] respecto a imagen original (no 640)
            x_min = round(x1 / width, 4)
            y_min = round(y1 / height, 4)
            x_max = round(x2 / width, 4)
            y_max = round(y2 / height, 4)
            # Clamp
            x_min, y_min, x_max, y_max = max(0, x_min), max(0, y_min), min(1, x_max), min(1, y_max)
            meta = get_metadata(label)
            detections.append({
                "disease_label": label,
                "disease_name_scientific": meta.get("scientific"),
                "disease_name_spanish": meta.get("spanish"),
                "confidence_score": round(conf, 4),
                "severity_level": severity_from_confidence(conf),
                "bounding_box": {
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max,
                    "coordinate_space": "normalized_0_to_1",
                    "reference": "original_image_dimensions",
                },
            })
    # Ordenar por confianza desc
    detections.sort(key=lambda d: d["confidence_score"], reverse=True)
    return detections
