class BoundingBox {
  final double x;
  final double y;
  final double width;
  final double height;
  final double confidence;
  final String className;

  BoundingBox({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.confidence,
    required this.className,
  });

  factory BoundingBox.fromJson(Map<String, dynamic> json) {
    return BoundingBox(
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      width: (json['width'] as num).toDouble(),
      height: (json['height'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      className: json['class_name'] ?? 'pothole',
    );
  }
}

class Detection {
  final List<BoundingBox> boxes;
  final int numDetections;
  final String modelVersion;
  final int inferenceMs;

  Detection({
    required this.boxes,
    required this.numDetections,
    required this.modelVersion,
    required this.inferenceMs,
  });

  factory Detection.fromJson(Map<String, dynamic> json) {
    final bxs = (json['detection']?['boundingBoxes'] ?? json['boundingBoxes'] ?? []) as List<dynamic>;
    return Detection(
      boxes: bxs.map((e) => BoundingBox.fromJson(e as Map<String, dynamic>)).toList(),
      numDetections: json['detection']?['numDetections'] ?? json['numDetections'] ?? 0,
      modelVersion: json['detection']?['modelVersion'] ?? json['modelVersion'] ?? 'unknown',
      inferenceMs: json['detection']?['inferenceMs'] ?? json['inferenceMs'] ?? 0,
    );
  }
}
