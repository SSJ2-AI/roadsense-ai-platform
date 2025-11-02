import 'package:flutter/material.dart';
import '../models/detection.dart';

class DetectionCard extends StatelessWidget {
  final Detection result;
  const DetectionCard({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Detections: ${result.numDetections}', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text('Model: ${result.modelVersion}'),
            Text('Inference: ${result.inferenceMs} ms'),
          ],
        ),
      ),
    );
  }
}
