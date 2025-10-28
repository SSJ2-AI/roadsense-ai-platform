import 'package:flutter/material.dart';
import '../models/detection.dart';
import '../widgets/detection_card.dart';

class ResultsScreen extends StatelessWidget {
  final Detection result;
  const ResultsScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detection Results')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DetectionCard(result: result),
        ],
      ),
    );
  }
}
